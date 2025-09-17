"""
Test suite for bot handlers.
"""

import pytest
from unittest.mock import AsyncMock, Mock, patch
from telegram import Update, User, Message, Chat
from telegram.ext import ContextTypes

from src.bot.handlers import StartHandler, WeatherHandler, JokeHandler
from src.bot.services import WeatherServiceError, JokeServiceError


class TestBaseHandler:
    """Test base handler functionality."""
    
    def setup_method(self):
        """Setup test fixtures."""
        self.start_handler = StartHandler()
        self.weather_handler = WeatherHandler()
        self.joke_handler = JokeHandler()
    
    def create_mock_update(self, user_id: int = 123456, username: str = "testuser") -> Update:
        """Create mock Telegram update object."""
        user = User(id=user_id, first_name="Test", last_name="User", username=username, is_bot=False)
        chat = Chat(id=user_id, type="private")
        message = Message(
            message_id=1,
            date=None,
            chat=chat,
            from_user=user
        )
        
        update = Mock(spec=Update)
        update.effective_user = user
        update.message = message
        return update
    
    def create_mock_context(self, args: list = None) -> ContextTypes.DEFAULT_TYPE:
        """Create mock Telegram context object."""
        context = Mock(spec=ContextTypes.DEFAULT_TYPE)
        context.args = args or []
        return context
    
    @pytest.mark.asyncio
    async def test_rate_limiting(self):
        """Test rate limiting functionality."""
        handler = self.start_handler
        user_id = 123456
        
        # Simulate rate limit by calling _update_rate_limit multiple times
        for _ in range(25):  # Exceed the 20 requests per minute limit
            handler._update_rate_limit(user_id)
        
        is_limited = handler._is_rate_limited(user_id, 25)
        assert is_limited is True
    
    def test_user_info_extraction(self):
        """Test user information extraction."""
        update = self.create_mock_update()
        handler = self.start_handler
        
        user_info = handler.get_user_info(update)
        
        assert user_info['id'] == 123456
        assert user_info['username'] == "testuser"
        assert user_info['first_name'] == "Test"
        assert user_info['is_bot'] is False


class TestStartHandler:
    """Test start command handler."""
    
    def setup_method(self):
        """Setup test fixtures."""
        self.handler = StartHandler()
    
    def create_mock_update(self) -> Update:
        """Create mock update for testing."""
        user = User(id=123456, first_name="TestUser", username="test", is_bot=False)
        chat = Chat(id=123456, type="private")
        message = Mock(spec=Message)
        message.reply_text = AsyncMock()
        
        update = Mock(spec=Update)
        update.effective_user = user
        update.message = message
        return update
    
    @pytest.mark.asyncio
    async def test_start_command_success(self):
        """Test successful start command execution."""
        update = self.create_mock_update()
        context = Mock(spec=ContextTypes.DEFAULT_TYPE)
        context.args = []
        
        await self.handler.handle(update, context)
        
        # Verify reply_text was called
        update.message.reply_text.assert_called_once()
        
        # Check that the message contains welcome text
        call_args = update.message.reply_text.call_args
        message_text = call_args[1]['text']
        assert "Bot Initialized" in message_text
        assert "TestUser" in message_text
    
    @pytest.mark.asyncio
    async def test_start_command_with_invalid_user(self):
        """Test start command with invalid user."""
        update = Mock(spec=Update)
        update.effective_user = None
        context = Mock(spec=ContextTypes.DEFAULT_TYPE)
        
        # Should handle gracefully without throwing exception
        await self.handler.handle(update, context)


class TestWeatherHandler:
    """Test weather command handler."""
    
    def setup_method(self):
        """Setup test fixtures."""
        self.handler = WeatherHandler()
    
    def create_mock_update_with_message(self, reply_mock: AsyncMock) -> Update:
        """Create mock update with message reply capability."""
        user = User(id=123456, first_name="Test", username="test", is_bot=False)
        chat = Chat(id=123456, type="private")
        message = Mock(spec=Message)
        message.reply_text = reply_mock
        
        update = Mock(spec=Update)
        update.effective_user = user
        update.message = message
        return update
    
    @pytest.mark.asyncio
    async def test_weather_command_no_args(self):
        """Test weather command without city argument."""
        reply_mock = AsyncMock()
        update = self.create_mock_update_with_message(reply_mock)
        context = Mock(spec=ContextTypes.DEFAULT_TYPE)
        context.args = []
        
        await self.handler.handle(update, context)
        
        # Should send usage message
        reply_mock.assert_called_once()
        call_args = reply_mock.call_args
        message_text = call_args[1]['text']
        assert "weather" in message_text.lower()
        assert "usage" in message_text.lower() or "command" in message_text.lower()
    
    @pytest.mark.asyncio
    @patch('src.bot.handlers.weather_handler.weather_service')
    async def test_weather_command_success(self, mock_service):
        """Test successful weather command execution."""
        # Mock service response
        mock_weather_data = Mock()
        mock_weather_data.city_name = "London"
        mock_weather_data.raw_data = {
            'main': {'temp': 20.5, 'feels_like': 19.0, 'humidity': 65, 'pressure': 1013},
            'weather': [{'description': 'clear sky', 'main': 'Clear'}],
            'name': 'London',
            'sys': {'country': 'GB'}
        }
        
        mock_service.is_service_available.return_value = True
        mock_service.get_current_weather.return_value = mock_weather_data
        
        reply_mock = AsyncMock()
        update = self.create_mock_update_with_message(reply_mock)
        context = Mock(spec=ContextTypes.DEFAULT_TYPE)
        context.args = ["London"]
        
        await self.handler.handle(update, context)
        
        # Verify service was called
        mock_service.get_current_weather.assert_called_once_with("London")
        
        # Verify response was sent
        reply_mock.assert_called_once()
    
    @pytest.mark.asyncio
    @patch('src.bot.handlers.weather_handler.weather_service')
    async def test_weather_command_service_error(self, mock_service):
        """Test weather command with service error."""
        mock_service.is_service_available.return_value = True
        mock_service.get_current_weather.side_effect = WeatherServiceError(
            "City not found", "city_not_found"
        )
        
        reply_mock = AsyncMock()
        update = self.create_mock_update_with_message(reply_mock)
        context = Mock(spec=ContextTypes.DEFAULT_TYPE)
        context.args = ["InvalidCity"]
        
        await self.handler.handle(update, context)
        
        # Should send error message
        reply_mock.assert_called_once()
        call_args = reply_mock.call_args
        message_text = call_args[1]['text']
        assert "❌" in message_text


class TestJokeHandler:
    """Test joke command handler."""
    
    def setup_method(self):
        """Setup test fixtures."""
        self.handler = JokeHandler()
    
    def create_mock_update_with_message(self, reply_mock: AsyncMock) -> Update:
        """Create mock update with message reply capability."""
        user = User(id=123456, first_name="Test", username="test", is_bot=False)
        chat = Chat(id=123456, type="private")
        message = Mock(spec=Message)
        message.reply_text = reply_mock
        
        update = Mock(spec=Update)
        update.effective_user = user
        update.message = message
        return update
    
    @pytest.mark.asyncio
    @patch('src.bot.handlers.joke_handler.joke_service')
    async def test_joke_command_success(self, mock_service):
        """Test successful joke command execution."""
        # Mock service response
        mock_joke_data = Mock()
        mock_joke_data.id = "test123"
        mock_joke_data.joke = "Why don't scientists trust atoms? Because they make up everything!"
        
        mock_service.is_service_available.return_value = True
        mock_service.get_random_joke.return_value = mock_joke_data
        
        reply_mock = AsyncMock()
        update = self.create_mock_update_with_message(reply_mock)
        context = Mock(spec=ContextTypes.DEFAULT_TYPE)
        context.args = []
        
        await self.handler.handle(update, context)
        
        # Verify service was called
        mock_service.get_random_joke.assert_called_once()
        
        # Verify response was sent
        reply_mock.assert_called_once()
        call_args = reply_mock.call_args
        message_text = call_args[1]['text']
        assert "😄" in message_text
        assert "atoms" in message_text
    
    @pytest.mark.asyncio
    @patch('src.bot.handlers.joke_handler.joke_service')
    async def test_joke_command_service_error(self, mock_service):
        """Test joke command with service error."""
        mock_service.is_service_available.return_value = True
        mock_service.get_random_joke.side_effect = JokeServiceError(
            "Service unavailable", "service_unavailable"
        )
        
        reply_mock = AsyncMock()
        update = self.create_mock_update_with_message(reply_mock)
        context = Mock(spec=ContextTypes.DEFAULT_TYPE)
        context.args = []
        
        await self.handler.handle(update, context)
        
        # Should send error message
        reply_mock.assert_called_once()
        call_args = reply_mock.call_args
        message_text = call_args[1]['text']
        assert "❌" in message_text or "⚠️" in message_text