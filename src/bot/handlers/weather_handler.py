"""
Weather command handler with OpenWeatherMap integration.
Systematic weather data retrieval with comprehensive error handling.
"""

import logging
from telegram import Update
from telegram.ext import ContextTypes

from .base_handler import BaseHandler
from src.bot.services import weather_service, WeatherServiceError
from src.bot.utils import MessageFormatter, InputValidator

logger = logging.getLogger(__name__)


class WeatherHandler(BaseHandler):
    """
    Handler for /weather command.
    Implements robust weather data retrieval with user-friendly error handling.
    """
    
    def __init__(self):
        super().__init__("weather")
    
    async def _process_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """
        Process weather command with city parameter validation.
        
        Args:
            update: Telegram update object
            context: Telegram context object
        """
        try:
            # Extract and validate arguments
            args = self._extract_command_args(context)
            
            if not args:
                usage_message = MessageFormatter.format_usage_message(
                    "weather",
                    "/weather <city>",
                    "Get current weather data for specified city"
                )
                await self._send_message(update, usage_message)
                return
            
            # Join arguments to form city name (handles "New York" etc.)
            city = ' '.join(args)
            
            # Additional validation
            is_valid, error = InputValidator.validate_city_name(city)
            if not is_valid:
                await self._send_error_message(update, "invalid_input", error)
                return
            
            # Check service availability
            if not weather_service.is_service_available():
                await self._send_error_message(
                    update, 
                    "api_unavailable", 
                    "Weather service not configured"
                )
                return
            
            # Retrieve weather data
            logger.info(f"Processing weather request for: {city}")
            weather_data = await weather_service.get_current_weather(city)
            
            # Format and send response
            weather_report = MessageFormatter.format_weather_report(weather_data.raw_data)
            success = await self._send_message(update, weather_report)
            
            if success:
                logger.info(f"Weather data sent for {weather_data.city_name}")
            
        except WeatherServiceError as e:
            logger.warning(f"Weather service error: {e.message}")
            
            # Map service errors to user-friendly messages
            error_type_mapping = {
                "city_not_found": "city_not_found",
                "service_unavailable": "api_unavailable", 
                "validation_error": "invalid_input",
                "configuration_error": "api_unavailable",
                "auth_error": "api_unavailable"
            }
            
            error_type = error_type_mapping.get(e.error_type, "general")
            await self._send_error_message(update, error_type, e.message if error_type == "invalid_input" else None)
        
        except Exception as e:
            logger.error(f"Unexpected error in weather handler: {e}")
            await self._send_error_message(update, "general")
    
    async def _pre_process(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """
        Pre-processing for weather command.
        Validate service availability and log request initiation.
        """
        user_info = self.get_user_info(update)
        args = self._extract_command_args(context)
        
        city_query = ' '.join(args) if args else "no_city"
        logger.info(f"Weather request from user {user_info['id']} for: {city_query}")
        
        # Early service availability check
        if not weather_service.is_service_available():
            logger.warning("Weather service unavailable - API key not configured")
    
    async def _post_process(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """
        Post-processing for weather command.
        Log completion and update usage metrics.
        """
        user_info = self.get_user_info(update)
        logger.info(f"Weather command completed for user {user_info['id']}")


class WeatherLocationHandler(BaseHandler):
    """
    Future expansion: Handler for location-based weather requests.
    Handles weather requests with GPS coordinates.
    """
    
    def __init__(self):
        super().__init__("weather_location")
    
    async def _process_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """
        Process weather command with location coordinates.
        Future implementation for location-based weather queries.
        """
        # Implementation placeholder for future location-based weather
        await self._send_error_message(
            update,
            "general", 
            "Location-based weather not yet implemented"
        )