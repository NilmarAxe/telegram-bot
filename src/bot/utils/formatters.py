"""
Message formatting utilities.
Systematic approach to consistent bot messaging.
"""

from typing import Dict, Any, Optional
from telegram.constants import ParseMode
from .constants import Emojis, WEATHER_CONDITION_EMOJIS


class MessageFormatter:
    """
    Centralized message formatting logic.
    Ensures consistent formatting and prevents injection attacks.
    """
    
    @staticmethod
    def escape_markdown(text: str) -> str:
        """
        Escape markdown special characters to prevent formatting issues.
        
        Args:
            text: Raw text to escape
            
        Returns:
            str: Escaped text safe for Markdown parsing
        """
        escape_chars = ['_', '*', '[', ']', '(', ')', '~', '`', '>', '#', '+', '-', '=', '|', '{', '}', '.', '!']
        escaped = text
        for char in escape_chars:
            escaped = escaped.replace(char, f'\\{char}')
        return escaped
    
    @staticmethod
    def format_welcome_message(user_name: str) -> str:
        """
        Format welcome message with user personalization.
        
        Args:
            user_name: User's first name
            
        Returns:
            str: Formatted welcome message
        """
        safe_name = MessageFormatter.escape_markdown(user_name)
        return f"""{Emojis.ROBOT} *Bot Initialized* \\- Hello, {safe_name}

*Available Commands:*
• `/weather <city>` \\- Weather data retrieval
• `/joke` \\- Random humor generation
• `/start` \\- System initialization

_Privacy Protocol: Zero data retention_"""
    
    @staticmethod
    def format_weather_report(weather_data: Dict[str, Any]) -> str:
        """
        Format comprehensive weather report from API data.
        
        Args:
            weather_data: Weather API response data
            
        Returns:
            str: Formatted weather report
        """
        try:
            # Extract and validate data
            temp = weather_data['main']['temp']
            feels_like = weather_data['main']['feels_like']
            humidity = weather_data['main']['humidity']
            pressure = weather_data['main'].get('pressure', 'N/A')
            
            weather_desc = weather_data['weather'][0]['description']
            weather_main = weather_data['weather'][0]['main'].lower()
            
            city_name = weather_data['name']
            country = weather_data['sys']['country']
            
            # Get weather emoji
            weather_emoji = WEATHER_CONDITION_EMOJIS.get(weather_main, Emojis.CLOUD)
            
            # Format temperature values
            temp_str = f"{temp:.1f}" if isinstance(temp, float) else str(temp)
            feels_like_str = f"{feels_like:.1f}" if isinstance(feels_like, float) else str(feels_like)
            
            # Escape special characters
            safe_city = MessageFormatter.escape_markdown(city_name)
            safe_country = MessageFormatter.escape_markdown(country)
            safe_description = MessageFormatter.escape_markdown(weather_desc.title())
            
            # Build comprehensive report
            report = f"""{Emojis.THERMOMETER} *Weather Report*

{Emojis.LOCATION} *Location:* {safe_city}, {safe_country}
{weather_emoji} *Conditions:* {safe_description}
{Emojis.THERMOMETER} *Temperature:* {temp_str}°C \\(feels like {feels_like_str}°C\\)
{Emojis.HUMIDITY} *Humidity:* {humidity}%"""
            
            # Add pressure if available
            if pressure != 'N/A':
                report += f"\n📊 *Pressure:* {pressure} hPa"
            
            return report
            
        except KeyError as e:
            return f"{Emojis.ERROR} Weather data format error: missing field {str(e)}"
        except Exception as e:
            return f"{Emojis.ERROR} Weather formatting error occurred"
    
    @staticmethod
    def format_joke_message(joke_text: str) -> str:
        """
        Format joke message with consistent styling.
        
        Args:
            joke_text: Raw joke text from API
            
        Returns:
            str: Formatted joke message
        """
        if not joke_text or not joke_text.strip():
            return f"{Emojis.ERROR} Joke data unavailable"
        
        # Clean and escape joke text
        clean_joke = joke_text.strip()
        safe_joke = MessageFormatter.escape_markdown(clean_joke)
        
        return f"{Emojis.LAUGH} {safe_joke}"
    
    @staticmethod
    def format_error_message(error_type: str, details: Optional[str] = None) -> str:
        """
        Format error messages with consistent styling.
        
        Args:
            error_type: Type of error (timeout, api_error, etc.)
            details: Optional error details
            
        Returns:
            str: Formatted error message
        """
        error_messages = {
            'timeout': f"{Emojis.CLOCK} Request timeout \\- retry recommended",
            'api_unavailable': f"{Emojis.WARNING} External service unavailable",
            'invalid_input': f"{Emojis.ERROR} Invalid input format",
            'city_not_found': f"{Emojis.ERROR} Location not found",
            'general': f"{Emojis.ERROR} System error \\- operation failed"
        }
        
        base_message = error_messages.get(error_type, error_messages['general'])
        
        if details:
            safe_details = MessageFormatter.escape_markdown(details)
            return f"{base_message}\n_{safe_details}_"
        
        return base_message
    
    @staticmethod
    def format_usage_message(command: str, usage: str, description: str) -> str:
        """
        Format command usage help messages.
        
        Args:
            command: Command name
            usage: Usage pattern
            description: Command description
            
        Returns:
            str: Formatted usage message
        """
        safe_command = MessageFormatter.escape_markdown(command)
        safe_usage = MessageFormatter.escape_markdown(usage)
        safe_description = MessageFormatter.escape_markdown(description)
        
        return f"""*Command:* `{safe_command}`
*Usage:* `{safe_usage}`
*Description:* {safe_description}"""
    
    @staticmethod
    def truncate_message(message: str, max_length: int = 4000) -> str:
        """
        Truncate message to fit Telegram limits while preserving formatting.
        
        Args:
            message: Message to truncate
            max_length: Maximum allowed length
            
        Returns:
            str: Truncated message with ellipsis if needed
        """
        if len(message) <= max_length:
            return message
        
        truncated = message[:max_length - 4]  # Reserve space for "..."
        return f"{truncated}\\.\\.\\."


class LogFormatter:
    """Specialized formatting for logging purposes."""
    
    @staticmethod
    def format_user_action(user_id: int, username: Optional[str], action: str) -> str:
        """
        Format user action for logging.
        
        Args:
            user_id: Telegram user ID
            username: Telegram username (if available)
            action: Action performed
            
        Returns:
            str: Formatted log entry
        """
        user_identifier = f"@{username}" if username else f"ID:{user_id}"
        return f"User {user_identifier} - {action}"
    
    @staticmethod
    def format_api_call(service: str, endpoint: str, status: str, duration: float) -> str:
        """
        Format API call logging.
        
        Args:
            service: Service name (weather, joke, etc.)
            endpoint: API endpoint
            status: Response status
            duration: Request duration in seconds
            
        Returns:
            str: Formatted log entry
        """
        return f"API Call - {service}:{endpoint} | Status: {status} | Duration: {duration:.3f}s"