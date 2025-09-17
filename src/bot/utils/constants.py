"""
Application constants and enumerations.
Centralized constant management for maintainability.
"""

from enum import Enum
from typing import Dict, Any


class BotCommands(Enum):
    """Bot command definitions."""
    START = "start"
    WEATHER = "weather"
    JOKE = "joke"
    HELP = "help"


class ResponseMessages(Enum):
    """Standard response messages."""
    WELCOME = """🤖 *Bot Initialized*

*Available Commands:*
• `/weather <city>` - Weather data retrieval
• `/joke` - Random humor generation  
• `/start` - System initialization

_Privacy Protocol: Zero data retention_"""
    
    ERROR_GENERAL = "❌ System error - operation failed"
    ERROR_TIMEOUT = "⏱️ Request timeout - retry recommended"
    ERROR_API_UNAVAILABLE = "⚠️ External service unavailable"
    ERROR_INVALID_INPUT = "❌ Invalid input format"
    
    WEATHER_USAGE = "❌ Usage: `/weather <city>`"
    WEATHER_NOT_FOUND = "❌ Location '{}' not found"
    WEATHER_SERVICE_DOWN = "❌ Weather service temporarily offline"
    
    JOKE_UNAVAILABLE = "❌ Humor service offline"


class APIEndpoints:
    """External API endpoint definitions."""
    OPENWEATHER_CURRENT = "/weather"
    JOKE_RANDOM = "/"


class Limits:
    """Application limits and constraints."""
    MAX_CITY_NAME_LENGTH = 50
    MAX_MESSAGE_LENGTH = 4096
    REQUEST_TIMEOUT_SECONDS = 10
    MAX_API_RETRIES = 3
    RATE_LIMIT_PER_USER_MINUTE = 20


class Emojis:
    """Emoji constants for consistent UI."""
    ROBOT = "🤖"
    THERMOMETER = "🌡️"
    LOCATION = "📍"
    HUMIDITY = "💧"
    CLOUD = "☁️"
    LAUGH = "😄"
    ERROR = "❌"
    WARNING = "⚠️"
    CLOCK = "⏱️"


HTTP_HEADERS: Dict[str, str] = {
    'User-Agent': 'TelegramBot/1.0.0',
    'Accept': 'application/json',
    'Accept-Encoding': 'gzip, deflate',
    'Connection': 'keep-alive'
}

# Weather condition mappings
WEATHER_CONDITION_EMOJIS: Dict[str, str] = {
    'clear': '☀️',
    'clouds': '☁️',
    'rain': '🌧️',
    'drizzle': '🌦️',
    'thunderstorm': '⛈️',
    'snow': '❄️',
    'mist': '🌫️',
    'fog': '🌫️',
    'haze': '🌫️',
    'dust': '💨',
    'sand': '💨',
    'smoke': '💨',
    'squall': '💨',
    'tornado': '🌪️'
}