"""
Main bot application with systematic architecture.
"""

import asyncio
import logging
from typing import Optional
from telegram.ext import Application, CommandHandler
from telegram import BotCommand

from src.config import settings
from src.bot.handlers import StartHandler, WeatherHandler, JokeHandler
from src.bot.services import http_client
from src.bot.utils import BotCommands

logger = logging.getLogger(__name__)


class TelegramBotApplication:
    """
    Main bot application class with comprehensive lifecycle management.
    Implements clean architecture with proper resource management.
    """
    
    def __init__(self):
        self.application: Optional[Application] = None
        self.handlers = {}
        self._is_running = False
    
    async def initialize(self) -> None:
        """
        Initialize bot application with all components.
        Systematic initialization following dependency order.
        """
        try:
            logger.info("Initializing Telegram bot application")
            
            # Validate configuration
            settings.validate()
            
            # Create application instance
            self.application = Application.builder().token(settings.telegram.token).build()
            
            # Initialize handlers
            await self._initialize_handlers()
            
            # Register handlers with application
            await self._register_handlers()
            
            # Setup bot commands
            await self._setup_bot_commands()
            
            # Register error handler
            self.application.add_error_handler(self._global_error_handler)
            
            # Setup shutdown hooks
            self._setup_shutdown_hooks()
            
            logger.info("Bot application initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize bot application: {e}")
            raise
    
    async def _initialize_handlers(self) -> None:
        """Initialize all command handlers."""
        self.handlers = {
            BotCommands.START.value: StartHandler(),
            BotCommands.WEATHER.value: WeatherHandler(), 
            BotCommands.JOKE.value: JokeHandler()
        }
        
        logger.info(f"Initialized {len(self.handlers)} command handlers")
    
    async def _register_handlers(self) -> None:
        """Register handlers with the Telegram application."""
        for command, handler in self.handlers.items():
            command_handler = CommandHandler(command, handler.handle)
            self.application.add_handler(command_handler)
            logger.debug(f"Registered handler for /{command}")
        
        logger.info("All handlers registered successfully")
    
    async def _setup_bot_commands(self) -> None:
        """Setup bot command menu for Telegram UI."""
        try:
            commands = [
                BotCommand("start", "Initialize bot and show welcome message"),
                BotCommand("weather", "Get current weather for a city"),
                BotCommand("joke", "Get a random dad joke")
            ]
            
            await self.application.bot.set_my_commands(commands)
            logger.info("Bot command menu configured")
            
        except Exception as e:
            logger.warning(f"Failed to set bot commands: {e}")
    
    def _setup_shutdown_hooks(self) -> None:
        """Setup cleanup hooks for graceful shutdown."""
        async def cleanup_resources():
            """Cleanup function for shutdown."""
            try:
                logger.info("Cleaning up bot resources")
                await http_client.close()
                logger.info("HTTP client closed")
            except Exception as e:
                logger.error(f"Error during cleanup: {e}")
        
        self.application.post_shutdown.append(
            lambda app: asyncio.create_task(cleanup_resources())
        )
    
    async def _global_error_handler(self, update: object, context) -> None:
        """
        Global error handler for unhandled exceptions.
        Implements systematic error logging and user notification.
        """
        try:
            # Log the error with context
            logger.error(f"Global error handler triggered: {context.error}")
            logger.error(f"Update object: {update}")
            
            # Send user-friendly error message if update has message capability
            from telegram import Update
            if isinstance(update, Update) and update.message:
                try:
                    await update.message.reply_text(
                        "⚠️ System error occurred - operation failed",
                        parse_mode=None
                    )
                except Exception as send_error:
                    logger.error(f"Failed to send error message: {send_error}")
            
        except Exception as handler_error:
            logger.critical(f"Error in global error handler: {handler_error}")
    
    async def start_polling(self) -> None:
        """
        Start bot in polling mode for development.
        Non-blocking polling with proper error handling.
        """
        try:
            if not self.application:
                await self.initialize()
            
            logger.info("Starting bot in polling mode")
            self._is_running = True
            
            # Configure polling parameters
            await self.application.initialize()
            await self.application.start()
            await self.application.updater.start_polling(
                poll_interval=1.0,
                timeout=10,
                read_timeout=6,
                write_timeout=6,
                connect_timeout=7,
                pool_timeout=1,
                drop_pending_updates=True
            )
            
            logger.info("Bot polling started successfully")
            
        except Exception as e:
            logger.error(f"Failed to start polling: {e}")
            self._is_running = False
            raise
    
    async def start_webhook(self) -> None:
        """
        Start bot in webhook mode for production.
        Configured for Heroku and similar platforms.
        """
        try:
            if not self.application:
                await self.initialize()
            
            logger.info("Starting bot in webhook mode")
            self._is_running = True
            
            # Validate webhook configuration
            if not settings.telegram.webhook_url or not settings.telegram.webhook_path:
                raise ValueError("Webhook URL and path must be configured for webhook mode")
            
            # Start webhook
            await self.application.initialize()
            await self.application.start()
            
            self.application.run_webhook(
                listen=settings.server.host,
                port=settings.server.port,
                url_path=settings.telegram.webhook_path,
                webhook_url=settings.telegram.webhook_url,
                drop_pending_updates=True
            )
            
            logger.info(f"Bot webhook started on {settings.server.host}:{settings.server.port}")
            
        except Exception as e:
            logger.error(f"Failed to start webhook: {e}")
            self._is_running = False
            raise
    
    async def stop(self) -> None:
        """
        Stop bot application gracefully.
        Ensures proper cleanup of all resources.
        """
        try:
            if not self.application or not self._is_running:
                logger.warning("Bot application not running")
                return
            
            logger.info("Stopping bot application")
            
            # Stop the application
            if self.application.updater.running:
                await self.application.updater.stop()
            
            await self.application.stop()
            await self.application.shutdown()
            
            self._is_running = False
            logger.info("Bot application stopped successfully")
            
        except Exception as e:
            logger.error(f"Error during bot shutdown: {e}")
            raise
    
    def is_running(self) -> bool:
        """
        Check if bot application is currently running.
        
        Returns:
            bool: True if bot is running
        """
        return self._is_running
    
    async def get_bot_info(self) -> dict:
        """
        Get basic bot information for diagnostics.
        
        Returns:
            dict: Bot information and status
        """
        if not self.application:
            return {"status": "not_initialized"}
        
        try:
            bot = self.application.bot
            me = await bot.get_me()
            
            return {
                "status": "running" if self._is_running else "stopped",
                "bot_id": me.id,
                "username": me.username,
                "first_name": me.first_name,
                "handlers_count": len(self.handlers),
                "mode": "production" if settings.is_production else "development"
            }
            
        except Exception as e:
            logger.error(f"Error getting bot info: {e}")
            return {"status": "error", "error": str(e)}


# Global bot application instance
bot_app = TelegramBotApplication()