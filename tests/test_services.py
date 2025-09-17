"""
Test suite for bot services.
Comprehensive service testing with mocked external dependencies.
"""

import pytest
from unittest.mock import AsyncMock, Mock, patch
from aioresponses import aioresponses

from src.bot.services import WeatherService, JokeService, HTTPClient
from src.bot.services import WeatherServiceError, JokeServiceError, HTTPClientError


class TestHTTPClient:
    """Test HTTP client functionality."""
    
    def setup_method(self):
        """Setup test fixtures."""
        self.client = HTTPClient()
    
    @pytest.mark.asyncio
    async def test_get_request_success(self):
        """Test successful GET request."""
        with aioresponses() as mock_aiohttp:
            mock_aiohttp.get(
                'https://api.example.com/test',
                payload={'result': 'success'},
                status=200
            )
            
            data, status = await self.client.get(
                'https://api.example.com/test',
                service_name='test_service'
            )
            
            assert status == 200
            assert data['result'] == 'success'
    
    @pytest.mark.asyncio
    async def test_get_request_404_error(self):
        """Test GET request with 404 error."""
        with aioresponses() as mock_aiohttp:
            mock_aiohttp.get(
                'https://api.example.com/notfound',
                status=404
            )
            
            with pytest.raises(HTTPClientError) as exc_info:
                await self.client.get(
                    'https://api.example.com/notfound',
                    service_name='test_service'
                )
            
            assert exc_info.value.status_code == 404
    
    @pytest.mark.asyncio
    async def test_circuit_breaker(self):
        """Test circuit breaker functionality."""
        # Trip circuit breaker
        self.client._trip_circuit_breaker('test_service')
        
        # Should be tripped
        assert self.client._is_circuit_broken('test_service') is True
        
        # Reset circuit breaker
        self.client._reset_circuit_breaker('test_service')
        
        # Should be reset
        assert self.client._is_circuit_broken('test_service') is False
    
    @pytest.mark.asyncio
    async def test_cleanup(self):
        """Test HTTP client cleanup."""
        # Initialize session
        async with self.client.session():
            pass  # Session created
        
        # Cleanup should work without errors
        await self.client.close()


class TestWeatherService:
    """Test weather service functionality."""
    
    def setup_method(self):
        """Setup test fixtures."""
        with patch('src.bot.services.weather_service.settings') as mock_settings:
            mock_settings.api.openweather_base_url = 'https://api.openweathermap.org/data/2.5'
            mock_settings.api.openweather_key = 'test_api_key'
            self.service = WeatherService()
    
    def create_weather_api_response(self):
        """Create mock weather API response."""
        return {
            'name': 'London',
            'main': {
                'temp': 15.5,
                'feels_like': 14.0,
                'humidity': 72,
                'pressure': 1013
            },
            'weather': [{
                'main': 'Clouds',
                'description': 'overcast clouds'
            }],
            'sys': {
                'country': 'GB'
            }
        }
    
    @pytest.mark.asyncio
    @patch('src.bot.services.weather_service.http_client')
    async def test_get_current_weather_success(self, mock_http_client):
        """Test successful weather data retrieval."""
        # Mock HTTP client response
        weather_data = self.create_weather_api_response()
        mock_http_client.get.return_value = (weather_data, 200)
        
        result = await self.service.get_current_weather('London')
        
        assert result.city_name == 'London'
        assert result.temperature == 15.5
        assert result.feels_like == 14.0
        assert result.humidity == 72
        assert result.description == 'overcast clouds'
        assert result.country_code == 'GB'
    
    @pytest.mark.asyncio
    @patch('src.bot.services.weather_service.http_client')
    async def test_get_current_weather_city_not_found(self, mock_http_client):
        """Test weather request for non-existent city."""
        mock_http_client.get.side_effect = HTTPClientError(
            "Resource not found",
            status_code=404,
            service="openweathermap"
        )
        
        with pytest.raises(WeatherServiceError) as exc_info:
            await self.service.get_current_weather('NonExistentCity')
        
        assert exc_info.value.error_type == 'city_not_found'
        assert 'NonExistentCity' in exc_info.value.message
    
    @pytest.mark.asyncio
    async def test_get_current_weather_invalid_input(self):
        """Test weather request with invalid city name."""
        with pytest.raises(WeatherServiceError) as exc_info:
            await self.service.get_current_weather('')
        
        assert exc_info.value.error_type == 'validation_error'
    
    @pytest.mark.asyncio
    @patch('src.bot.services.weather_service.http_client')
    async def test_get_current_weather_api_error(self, mock_http_client):
        """Test weather request with API error."""
        mock_http_client.get.side_effect = HTTPClientError(
            "Server error",
            status_code=500,
            service="openweathermap"
        )
        
        with pytest.raises(WeatherServiceError) as exc_info:
            await self.service.get_current_weather('London')
        
        assert exc_info.value.error_type == 'service_unavailable'
    
    def test_parse_weather_response_missing_data(self):
        """Test weather response parsing with missing data."""
        incomplete_data = {
            'name': 'London',
            'main': {'temp': 15.5}
            # Missing required fields
        }
        
        with pytest.raises(WeatherServiceError) as exc_info:
            self.service._parse_weather_response(incomplete_data)
        
        assert exc_info.value.error_type == 'data_format_error'
    
    def test_service_availability(self):
        """Test service availability check."""
        assert self.service.is_service_available() is True
        
        # Test with no API key
        with patch('src.bot.services.weather_service.settings') as mock_settings:
            mock_settings.api.openweather_key = None
            service_no_key = WeatherService()
            assert service_no_key.is_service_available() is False


class TestJokeService:
    """Test joke service functionality."""
    
    def setup_method(self):
        """Setup test fixtures."""
        with patch('src.bot.services.joke_service.settings') as mock_settings:
            mock_settings.api.joke_api_url = 'https://icanhazdadjoke.com'
            self.service = JokeService()
    
    def create_joke_api_response(self):
        """Create mock joke API response."""
        return {
            'id': 'test123',
            'joke': 'Why don\'t scientists trust atoms? Because they make up everything!',
            'status': 200
        }
    
    @pytest.mark.asyncio
    @patch('src.bot.services.joke_service.http_client')
    async def test_get_random_joke_success(self, mock_http_client):
        """Test successful joke retrieval."""
        joke_data = self.create_joke_api_response()
        mock_http_client.get.return_value = (joke_data, 200)
        
        result = await self.service.get_random_joke()
        
        assert result.id == 'test123'
        assert 'atoms' in result.joke
        assert result.status == 200
    
    @pytest.mark.asyncio
    @patch('src.bot.services.joke_service.http_client')
    async def test_get_random_joke_api_error(self, mock_http_client):
        """Test joke request with API error."""
        mock_http_client.get.side_effect = HTTPClientError(
            "Service unavailable",
            status_code=503,
            service="icanhazdadjoke"
        )
        
        with pytest.raises(JokeServiceError) as exc_info:
            await self.service.get_random_joke()
        
        assert exc_info.value.error_type == 'service_unavailable'
    
    @pytest.mark.asyncio
    @patch('src.bot.services.joke_service.http_client')
    async def test_get_joke_by_id_success(self, mock_http_client):
        """Test joke retrieval by ID."""
        joke_data = self.create_joke_api_response()
        mock_http_client.get.return_value = (joke_data, 200)
        
        result = await self.service.get_joke_by_id('test123')
        
        assert result.id == 'test123'
        assert result.joke is not None
    
    @pytest.mark.asyncio
    async def test_get_joke_by_id_invalid_input(self):
        """Test joke retrieval with invalid ID."""
        with pytest.raises(JokeServiceError) as exc_info:
            await self.service.get_joke_by_id('')
        
        assert exc_info.value.error_type == 'validation_error'
    
    @pytest.mark.asyncio
    @patch('src.bot.services.joke_service.http_client')
    async def test_search_jokes_success(self, mock_http_client):
        """Test joke search functionality."""
        search_response = {
            'results': [
                {'id': '1', 'joke': 'First joke about cats'},
                {'id': '2', 'joke': 'Second joke about cats'}
            ]
        }
        mock_http_client.get.return_value = (search_response, 200)
        
        results = await self.service.search_jokes('cats', limit=5)
        
        assert len(results) == 2
        assert 'cats' in results[0].joke
        assert 'cats' in results[1].joke
    
    def test_parse_joke_response_empty_joke(self):
        """Test parsing response with empty joke."""
        empty_data = {'id': 'test', 'joke': ''}
        
        with pytest.raises(JokeServiceError) as exc_info:
            self.service._parse_joke_response(empty_data, 200)
        
        assert exc_info.value.error_type == 'empty_joke'
    
    def test_service_availability(self):
        """Test service availability check."""
        # Joke service should always be available (no auth required)
        assert self.service.is_service_available() is True