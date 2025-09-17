"""
Weather service with OpenWeatherMap API integration.
Encapsulates weather data retrieval logic with error handling.
"""

import logging
from typing import Dict, Any, Optional
from dataclasses import dataclass

from src.config import settings
from src.bot.utils import WeatherValidator, ValidationError
from .http_client import http_client, HTTPClientError

logger = logging.getLogger(__name__)


@dataclass
class WeatherData:
    """Structured weather data model."""
    temperature: float
    feels_like: float
    humidity: int
    pressure: Optional[int]
    description: str
    main_condition: str
    city_name: str
    country_code: str
    raw_data: Dict[str, Any]


class WeatherServiceError(Exception):
    """Custom exception for weather service errors."""
    
    def __init__(self, message: str, error_type: str = "general"):
        self.message = message
        self.error_type = error_type
        super().__init__(self.message)


class WeatherService:
    """
    Weather data service with systematic error handling.
    Implements clean architecture principles for external API integration.
    """
    
    def __init__(self):
        self.base_url = settings.api.openweather_base_url
        self.api_key = settings.api.openweather_key
        
        if not self.api_key:
            logger.warning("OpenWeatherMap API key not configured")
    
    async def get_current_weather(self, city: str) -> WeatherData:
        """
        Retrieve current weather data for specified city.
        
        Args:
            city: City name for weather query
            
        Returns:
            WeatherData: Structured weather information
            
        Raises:
            WeatherServiceError: On service or validation errors
        """
        # Input validation
        is_valid, error, sanitized_city = WeatherValidator.validate_weather_query(city)
        if not is_valid:
            logger.warning(f"Invalid weather query: {city} - {error}")
            raise WeatherServiceError(error, "validation_error")
        
        if not self.api_key:
            raise WeatherServiceError("Weather service not configured", "configuration_error")
        
        try:
            # Prepare API request
            url = f"{self.base_url}/weather"
            params = {
                'q': sanitized_city,
                'appid': self.api_key,
                'units': 'metric',
                'lang': 'en'
            }
            
            logger.info(f"Requesting weather data for: {sanitized_city}")
            
            # Make API call
            data, status_code = await http_client.get(
                url=url,
                params=params,
                service_name="openweathermap"
            )
            
            # Parse and validate response
            weather_data = self._parse_weather_response(data)
            
            logger.info(f"Weather data retrieved successfully for {weather_data.city_name}")
            return weather_data
            
        except HTTPClientError as e:
            logger.error(f"HTTP error in weather service: {e.message}")
            
            if e.status_code == 404:
                raise WeatherServiceError(
                    f"City '{sanitized_city}' not found",
                    "city_not_found"
                )
            elif e.status_code == 401:
                raise WeatherServiceError(
                    "Weather service authentication failed",
                    "auth_error"
                )
            elif e.status_code and e.status_code >= 500:
                raise WeatherServiceError(
                    "Weather service temporarily unavailable",
                    "service_unavailable"
                )
            else:
                raise WeatherServiceError(
                    "Weather service error occurred",
                    "api_error"
                )
        
        except Exception as e:
            logger.error(f"Unexpected error in weather service: {e}")
            raise WeatherServiceError(
                "Weather data retrieval failed",
                "internal_error"
            )
    
    def _parse_weather_response(self, data: Dict[str, Any]) -> WeatherData:
        """
        Parse OpenWeatherMap API response into structured data.
        
        Args:
            data: Raw API response data
            
        Returns:
            WeatherData: Parsed weather information
            
        Raises:
            WeatherServiceError: On parsing errors
        """
        try:
            # Extract required fields
            main_data = data['main']
            weather_list = data['weather']
            sys_data = data['sys']
            
            if not weather_list:
                raise KeyError("weather data empty")
            
            weather_info = weather_list[0]
            
            # Create structured weather data
            weather_data = WeatherData(
                temperature=float(main_data['temp']),
                feels_like=float(main_data['feels_like']),
                humidity=int(main_data['humidity']),
                pressure=main_data.get('pressure'),
                description=weather_info['description'],
                main_condition=weather_info['main'],
                city_name=data['name'],
                country_code=sys_data['country'],
                raw_data=data
            )
            
            return weather_data
            
        except KeyError as e:
            logger.error(f"Missing field in weather response: {e}")
            raise WeatherServiceError(
                f"Invalid weather data format: missing {e}",
                "data_format_error"
            )
        
        except (ValueError, TypeError) as e:
            logger.error(f"Data type error in weather response: {e}")
            raise WeatherServiceError(
                "Invalid weather data types",
                "data_type_error"
            )
    
    async def get_weather_by_coordinates(self, lat: float, lon: float) -> WeatherData:
        """
        Get weather data by geographical coordinates.
        Future expansion method for location-based queries.
        
        Args:
            lat: Latitude
            lon: Longitude
            
        Returns:
            WeatherData: Weather information for coordinates
        """
        if not self.api_key:
            raise WeatherServiceError("Weather service not configured", "configuration_error")
        
        try:
            url = f"{self.base_url}/weather"
            params = {
                'lat': lat,
                'lon': lon,
                'appid': self.api_key,
                'units': 'metric',
                'lang': 'en'
            }
            
            data, _ = await http_client.get(
                url=url,
                params=params,
                service_name="openweathermap"
            )
            
            return self._parse_weather_response(data)
            
        except HTTPClientError as e:
            logger.error(f"Coordinate weather lookup failed: {e.message}")
            raise WeatherServiceError("Location weather lookup failed", "api_error")
    
    def is_service_available(self) -> bool:
        """
        Check if weather service is properly configured.
        
        Returns:
            bool: True if service is available
        """
        return bool(self.api_key)


# Global weather service instance
weather_service = WeatherService()