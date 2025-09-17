"""
Test suite for utility functions.
Comprehensive testing of validators, formatters, and constants.
"""

import pytest
from src.bot.utils import (
    InputValidator, WeatherValidator, ValidationError,
    MessageFormatter, LogFormatter,
    BotCommands, ResponseMessages, Emojis
)


class TestInputValidator:
    """Test input validation functionality."""
    
    def test_validate_city_name_valid(self):
        """Test validation with valid city names."""
        valid_cities = [
            "London",
            "New York", 
            "São Paulo",
            "México City",
            "Saint-Petersburg",
            "O'Fallon"
        ]
        
        for city in valid_cities:
            is_valid, error = InputValidator.validate_city_name(city)
            assert is_valid is True
            assert error is None
    
    def test_validate_city_name_invalid(self):
        """Test validation with invalid city names."""
        invalid_cities = [
            "",  # Empty
            "   ",  # Whitespace only
            "A" * 60,  # Too long
            "City<script>",  # Contains script tag
            "City{}",  # Contains braces
            "City|pipe",  # Contains pipe
        ]
        
        for city in invalid_cities:
            is_valid, error = InputValidator.validate_city_name(city)
            assert is_valid is False
            assert error is not None
    
    def test_validate_command_args_valid(self):
        """Test command argument validation with valid inputs."""
        valid_args = [
            ["London"],
            ["New", "York"],
            ["single"],
            ["one", "two", "three"]
        ]
        
        for args in valid_args:
            is_valid, error = InputValidator.validate_command_args(args)
            assert is_valid is True
            assert error is None
    
    def test_validate_command_args_invalid(self):
        """Test command argument validation with invalid inputs."""
        # Too few arguments
        is_valid, error = InputValidator.validate_command_args([], min_args=1)
        assert is_valid is False
        assert "Insufficient arguments" in error
        
        # Too many arguments
        many_args = ["arg"] * 15
        is_valid, error = InputValidator.validate_command_args(many_args, max_args=10)
        assert is_valid is False
        assert "Too many arguments" in error
        
        # Argument too long
        long_args = ["a" * 150]
        is_valid, error = InputValidator.validate_command_args(long_args)
        assert is_valid is False
        assert "exceeds limit" in error
    
    def test_sanitize_input(self):
        """Test input sanitization."""
        # Test control character removal
        dirty_input = "Hello\x00World\x1f"
        clean_output = InputValidator.sanitize_input(dirty_input)
        assert clean_output == "HelloWorld"
        
        # Test whitespace normalization
        messy_spaces = "Hello    \t\n   World"
        clean_spaces = InputValidator.sanitize_input(messy_spaces)
        assert clean_spaces == "Hello World"
        
        # Test empty input
        empty = InputValidator.sanitize_input("")
        assert empty == ""
    
    def test_validate_user_id(self):
        """Test user ID validation."""
        # Valid user IDs
        assert InputValidator.validate_user_id(123456) is True
        assert InputValidator.validate_user_id(1) is True
        
        # Invalid user IDs
        assert InputValidator.validate_user_id(0) is False
        assert InputValidator.validate_user_id(-1) is False
        assert InputValidator.validate_user_id("123") is False
    
    def test_rate_limiting_check(self):
        """Test rate limiting logic."""
        # Under limit
        assert InputValidator.is_rate_limited(123456, 10) is False
        
        # Over limit
        assert InputValidator.is_rate_limited(123456, 25) is True


class TestWeatherValidator:
    """Test weather-specific validation."""
    
    def test_validate_weather_query_valid(self):
        """Test valid weather queries."""
        valid_queries = [
            "London",
            "New York",
            "São Paulo",
            "tokyo"
        ]
        
        for query in valid_queries:
            is_valid, error, sanitized = WeatherValidator.validate_weather_query(query)
            assert is_valid is True
            assert error is None
            assert sanitized == query.strip()
    
    def test_validate_weather_query_invalid(self):
        """Test invalid weather queries."""
        invalid_queries = [
            "",
            "   ",
            "A" * 60,  # Too long
            "<script>alert('xss')</script>"
        ]
        
        for query in invalid_queries:
            is_valid, error, sanitized = WeatherValidator.validate_weather_query(query)
            assert is_valid is False
            assert error is not None
            assert sanitized is None


class TestMessageFormatter:
    """Test message formatting functionality."""
    
    def test_escape_markdown(self):
        """Test markdown escaping."""
        dangerous_text = "Hello *world* [link](url) `code`"
        escaped = MessageFormatter.escape_markdown(dangerous_text)
        
        # Should escape special characters
        assert "\\*" in escaped
        assert "\\[" in escaped
        assert "\\]" in escaped
        assert "\\(" in escaped
        assert "\\)" in escaped
        assert "\\`" in escaped
    
    def test_format_welcome_message(self):
        """Test welcome message formatting."""
        user_name = "TestUser"
        message = MessageFormatter.format_welcome_message(user_name)
        
        assert "TestUser" in message
        assert "Bot Initialized" in message
        assert "/weather" in message
        assert "/joke" in message
        assert "Privacy Protocol" in message
    
    def test_format_weather_report(self):
        """Test weather report formatting."""
        weather_data = {
            'main': {
                'temp': 20.5,
                'feels_like': 19.0,
                'humidity': 65,
                'pressure': 1013
            },
            'weather': [{
                'description': 'clear sky',
                'main': 'Clear'
            }],
            'name': 'London',
            'sys': {'country': 'GB'}
        }
        
        report = MessageFormatter.format_weather_report(weather_data)
        
        assert "Weather Report" in report
        assert "London" in report
        assert "GB" in report
        assert "20.5°C" in report
        assert "19.0°C" in report
        assert "65%" in report
        assert "Clear Sky" in report
    
    def test_format_weather_report_missing_data(self):
        """Test weather report with missing data."""
        incomplete_data = {
            'main': {'temp': 20.5}
            # Missing required fields
        }
        
        report = MessageFormatter.format_weather_report(incomplete_data)
        assert "error" in report.lower()
    
    def test_format_joke_message(self):
        """Test joke message formatting."""
        joke_text = "Why don't scientists trust atoms? Because they make up everything!"
        formatted = MessageFormatter.format_joke_message(joke_text)
        
        assert "😄" in formatted
        assert joke_text in formatted
    
    def test_format_joke_message_empty(self):
        """Test joke formatting with empty text."""
        formatted = MessageFormatter.format_joke_message("")
        assert "❌" in formatted
        assert "unavailable" in formatted.lower()
    
    def test_format_error_message(self):
        """Test error message formatting."""
        # Test different error types
        error_types = ['timeout', 'api_unavailable', 'invalid_input', 'general']
        
        for error_type in error_types:
            message = MessageFormatter.format_error_message(error_type)
            assert len(message) > 0
            assert ("❌" in message or "⚠️" in message or "⏱️" in message)
    
    def test_format_usage_message(self):
        """Test usage message formatting."""
        command = "weather"
        usage = "/weather <city>"
        description = "Get weather data"
        
        message = MessageFormatter.format_usage_message(command, usage, description)
        
        assert "weather" in message
        assert "/weather <city>" in message
        assert "Get weather data" in message
    
    def test_truncate_message(self):
        """Test message truncation."""
        long_message = "A" * 5000
        truncated = MessageFormatter.truncate_message(long_message, max_length=100)
        
        assert len(truncated) <= 104  # 100 + "..."
        assert truncated.endswith("\\.\\.\\.")
        
        # Test message under limit
        short_message = "Short message"
        not_truncated = MessageFormatter.truncate_message(short_message, max_length=100)
        assert not_truncated == short_message


class TestLogFormatter:
    """Test logging formatter functionality."""
    
    def test_format_user_action(self):
        """Test user action log formatting."""
        # With username
        log_entry = LogFormatter.format_user_action(123456, "testuser", "start command")
        assert "123456" in log_entry or "@testuser" in log_entry
        assert "start command" in log_entry
        
        # Without username
        log_entry_no_username = LogFormatter.format_user_action(123456, None, "weather command")
        assert "ID:123456" in log_entry_no_username
        assert "weather command" in log_entry_no_username
    
    def test_format_api_call(self):
        """Test API call log formatting."""
        log_entry = LogFormatter.format_api_call(
            "weather", "/weather", "200", 0.523
        )
        
        assert "weather" in log_entry
        assert "/weather" in log_entry
        assert "200" in log_entry
        assert "0.523" in log_entry
        assert "API Call" in log_entry


class TestConstants:
    """Test constants and enumerations."""
    
    def test_bot_commands_enum(self):
        """Test BotCommands enum values."""
        assert BotCommands.START.value == "start"
        assert BotCommands.WEATHER.value == "weather"
        assert BotCommands.JOKE.value == "joke"
    
    def test_response_messages_enum(self):
        """Test ResponseMessages enum."""
        welcome = ResponseMessages.WELCOME.value
        assert "Bot Initialized" in welcome
        assert "/weather" in welcome
        assert "/joke" in welcome
        assert "Privacy Protocol" in welcome
    
    def test_emojis_constants(self):
        """Test emoji constants."""
        assert Emojis.ROBOT == "🤖"
        assert Emojis.THERMOMETER == "🌡️"
        assert Emojis.ERROR == "❌"
        assert Emojis.LAUGH == "😄"
    
    def test_weather_condition_emojis(self):
        """Test weather condition emoji mapping."""
        from src.bot.utils.constants import WEATHER_CONDITION_EMOJIS
        
        assert 'clear' in WEATHER_CONDITION_EMOJIS
        assert 'rain' in WEATHER_CONDITION_EMOJIS
        assert 'snow' in WEATHER_CONDITION_EMOJIS
        
        # Check that emojis are actual emoji characters
        for condition, emoji in WEATHER_CONDITION_EMOJIS.items():
            assert len(emoji) > 0
            assert isinstance(emoji, str)


class TestValidationError:
    """Test custom validation exception."""
    
    def test_validation_error_creation(self):
        """Test ValidationError exception."""
        error = ValidationError("Test message", "test_field")
        
        assert str(error) == "Test message"
        assert error.message == "Test message"
        assert error.field == "test_field"
    
    def test_validation_error_without_field(self):
        """Test ValidationError without field specification."""
        error = ValidationError("Test message")
        
        assert error.message == "Test message"
        assert error.field is None


class TestSecurityValidator:
    """Test security-related validation."""
    
    def test_detect_injection_attempt(self):
        """Test injection attempt detection."""
        from src.bot.utils.validators import SecurityValidator
        
        # Suspicious inputs
        suspicious_inputs = [
            "<script>alert('xss')</script>",
            "javascript:void(0)",
            "<iframe src='evil.com'>",
            "onclick='malicious()'",
            "<object data='malware'>",
        ]
        
        for suspicious in suspicious_inputs:
            assert SecurityValidator.detect_injection_attempt(suspicious) is True
        
        # Safe inputs
        safe_inputs = [
            "London",
            "New York",
            "Weather is nice today",
            "Tell me a joke"
        ]
        
        for safe in safe_inputs:
            assert SecurityValidator.detect_injection_attempt(safe) is False
    
    def test_validate_message_length(self):
        """Test message length validation."""
        from src.bot.utils.validators import SecurityValidator
        
        # Valid length
        short_message = "Hello world"
        assert SecurityValidator.validate_message_length(short_message) is True
        
        # Invalid length
        long_message = "A" * 5000
        assert SecurityValidator.validate_message_length(long_message) is False