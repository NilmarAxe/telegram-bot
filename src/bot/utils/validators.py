"""
Input validation utilities.
Systematic validation approach with clear error messaging.
"""

import re
from typing import Optional, Tuple, List
from .constants import Limits


class ValidationError(Exception):
    """Custom exception for validation failures."""
    
    def __init__(self, message: str, field: str = None):
        self.message = message
        self.field = field
        super().__init__(self.message)


class InputValidator:
    """
    Centralized input validation logic.
    Implements fail-fast validation with descriptive errors.
    """
    
    @staticmethod
    def validate_city_name(city: str) -> Tuple[bool, Optional[str]]:
        """
        Validate city name input for weather queries.
        
        Returns:
            Tuple[bool, Optional[str]]: (is_valid, error_message)
        """
        if not city or not city.strip():
            return False, "City name cannot be empty"
        
        city = city.strip()
        
        if len(city) > Limits.MAX_CITY_NAME_LENGTH:
            return False, f"City name exceeds {Limits.MAX_CITY_NAME_LENGTH} character limit"
        
        # Allow letters, spaces, hyphens, apostrophes, and common accented characters
        if not re.match(r"^[a-zA-ZÀ-ÿĀ-žА-я\s\-'\.]+$", city):
            return False, "City name contains invalid characters"
        
        # Check for suspicious patterns
        if re.search(r'[<>{}[\]|\\]', city):
            return False, "Invalid characters detected"
        
        return True, None
    
    @staticmethod
    def validate_command_args(args: List[str], min_args: int = 1, max_args: int = 10) -> Tuple[bool, Optional[str]]:
        """
        Validate command arguments.
        
        Args:
            args: List of command arguments
            min_args: Minimum required arguments
            max_args: Maximum allowed arguments
            
        Returns:
            Tuple[bool, Optional[str]]: (is_valid, error_message)
        """
        if len(args) < min_args:
            return False, f"Insufficient arguments - minimum {min_args} required"
        
        if len(args) > max_args:
            return False, f"Too many arguments - maximum {max_args} allowed"
        
        # Check for extremely long arguments
        for arg in args:
            if len(arg) > 100:
                return False, "Argument length exceeds limit"
        
        return True, None
    
    @staticmethod
    def sanitize_input(text: str) -> str:
        """
        Sanitize user input by removing potentially harmful content.
        
        Args:
            text: Raw user input
            
        Returns:
            str: Sanitized text
        """
        if not text:
            return ""
        
        # Remove control characters and normalize whitespace
        sanitized = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', text)
        sanitized = re.sub(r'\s+', ' ', sanitized).strip()
        
        return sanitized
    
    @staticmethod
    def validate_user_id(user_id: int) -> bool:
        """
        Validate Telegram user ID format.
        
        Args:
            user_id: Telegram user ID
            
        Returns:
            bool: True if valid
        """
        return isinstance(user_id, int) and user_id > 0
    
    @staticmethod
    def is_rate_limited(user_id: int, current_count: int) -> bool:
        """
        Check if user has exceeded rate limits.
        
        Args:
            user_id: User identifier
            current_count: Current request count in time window
            
        Returns:
            bool: True if rate limited
        """
        return current_count > Limits.RATE_LIMIT_PER_USER_MINUTE


class WeatherValidator(InputValidator):
    """Specialized validator for weather-related inputs."""
    
    @staticmethod
    def validate_weather_query(query: str) -> Tuple[bool, Optional[str], Optional[str]]:
        """
        Comprehensive weather query validation.
        
        Returns:
            Tuple[bool, Optional[str], Optional[str]]: (is_valid, error_message, sanitized_query)
        """
        if not query:
            return False, "Weather query cannot be empty", None
        
        sanitized = InputValidator.sanitize_input(query)
        is_valid, error = InputValidator.validate_city_name(sanitized)
        
        if not is_valid:
            return False, error, None
        
        return True, None, sanitized


class SecurityValidator:
    """Security-focused validation methods."""
    
    @staticmethod
    def detect_injection_attempt(text: str) -> bool:
        """
        Basic injection attempt detection.
        
        Args:
            text: Input text to analyze
            
        Returns:
            bool: True if suspicious patterns detected
        """
        suspicious_patterns = [
            r'<script\b[^<]*(?:(?!<\/script>)<[^<]*)*<\/script>',  # Script tags
            r'javascript:',  # JavaScript protocol
            r'on\w+\s*=',   # Event handlers
            r'<iframe',      # Iframe tags
            r'<object',      # Object tags
            r'<embed',       # Embed tags
        ]
        
        text_lower = text.lower()
        return any(re.search(pattern, text_lower, re.IGNORECASE) for pattern in suspicious_patterns)
    
    @staticmethod
    def validate_message_length(message: str) -> bool:
        """
        Validate message length against Telegram limits.
        
        Args:
            message: Message content
            
        Returns:
            bool: True if within limits
        """
        return len(message) <= Limits.MAX_MESSAGE_LENGTH