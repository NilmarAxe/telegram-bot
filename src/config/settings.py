"""
Configuration management with environment-based settings.
"""

import os
from typing import Optional
from dataclasses import dataclass
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


@dataclass
class DatabaseConfig:
    """Database configuration - extensible for future needs."""
    url: Optional[str] = None
    max_connections: int = 10


@dataclass
class APIConfig:
    """External API configurations."""
    openweather_key: Optional[str] = None
    openweather_base_url: str = "http://api.openweathermap.org/data/2.5"
    joke_api_url: str = "https://icanhazdadjoke.com/"
    request_timeout: int = 10
    max_retries: int = 3


@dataclass
class TelegramConfig:
    """Telegram bot specific configuration."""
    token: Optional[str] = None
    webhook_url: Optional[str] = None
    webhook_path: Optional[str] = None
    max_message_length: int = 4096
    rate_limit_per_user: int = 20  # messages per minute


@dataclass
class ServerConfig:
    """Server deployment configuration."""
    host: str = "0.0.0.0"
    port: int = 8443
    debug: bool = False
    log_level: str = "INFO"
    heroku_app_name: Optional[str] = None


class Settings:
    """
    Centralized settings management.
    Implements singleton pattern for consistent configuration access.
    """
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialize()
        return cls._instance
    
    def _initialize(self):
        """Initialize configuration from environment variables."""
        self.telegram = TelegramConfig(
            token=os.getenv('TELEGRAM_BOT_TOKEN'),
            webhook_url=self._build_webhook_url(),
            webhook_path=f"/{os.getenv('TELEGRAM_BOT_TOKEN')}" if os.getenv('TELEGRAM_BOT_TOKEN') else None
        )
        
        self.api = APIConfig(
            openweather_key=os.getenv('OPENWEATHER_API_KEY'),
            request_timeout=int(os.getenv('API_TIMEOUT', '10')),
            max_retries=int(os.getenv('API_MAX_RETRIES', '3'))
        )
        
        self.server = ServerConfig(
            port=int(os.getenv('PORT', '8443')),
            debug=os.getenv('DEBUG', 'False').lower() == 'true',
            log_level=os.getenv('LOG_LEVEL', 'INFO'),
            heroku_app_name=os.getenv('HEROKU_APP_NAME')
        )
        
        self.database = DatabaseConfig(
            url=os.getenv('DATABASE_URL'),
            max_connections=int(os.getenv('DB_MAX_CONNECTIONS', '10'))
        )
    
    def _build_webhook_url(self) -> Optional[str]:
        """Build webhook URL for production deployment."""
        heroku_app = os.getenv('HEROKU_APP_NAME')
        token = os.getenv('TELEGRAM_BOT_TOKEN')
        
        if heroku_app and token:
            return f"https://{heroku_app}.herokuapp.com/{token}"
        return None
    
    @property
    def is_production(self) -> bool:
        """Determine if running in production environment."""
        return bool(self.server.heroku_app_name)
    
    def validate(self) -> None:
        """
        Validate critical configuration.
        Fails fast if essential settings are missing.
        """
        if not self.telegram.token:
            raise ValueError("TELEGRAM_BOT_TOKEN environment variable is required")
        
        if not self.api.openweather_key:
            raise ValueError("OPENWEATHER_API_KEY environment variable is required")
    
    def get_log_config(self) -> dict:
        """Return logging configuration."""
        return {
            'level': self.server.log_level,
            'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            'datefmt': '%Y-%m-%d %H:%M:%S'
        }


# Global settings instance
settings = Settings()