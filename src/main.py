"""
Main application entry point.
"""

import asyncio
import logging
import sys
import signal
from typing import NoReturn

from config import settings
from bot import bot_app

# Configure logging
logging.basicConfig(**settings.get_log_config())
logger = logging.getLogger(__name__)


class BotRunner:
    """
    Bot execution manager with proper lifecycle control.
    Implements systematic startup, operation, and shutdown procedures.
    """
    
    def __init__(self):
        self.shutdown_requested = False
    
    def setup_signal_handlers(self) -> None:
        """Setup signal handlers for graceful shutdown."""
        def signal_handler(sig, frame):
            logger.info(f"Received signal {sig}, initiating shutdown")
            self.shutdown_requested = True
        
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
    
    async def run_bot(self) -> None:
        """
        Main bot execution logic with mode detection.
        Automatically selects webhook or polling based on environment.
        """
        try:
            # Initialize bot application
            await bot_app.initialize()
            
            # Get bot information for logging
            bot_info = await bot_app.get_bot_info()
            logger.info(f"Bot initialized: @{bot_info.get('username', 'unknown')}")
            logger.info(f"Mode: {bot_info.get('mode', 'unknown')}")
            logger.info(f"Handlers: {bot_info.get('handlers_count', 0)}")
            
            # Determine execution mode
            if settings.is_production:
                logger.info("Production mode detected - starting webhook")
                await bot_app.start_webhook()
            else:
                logger.info("Development mode detected - starting polling")
                await self._run_polling()
            
        except KeyboardInterrupt:
            logger.info("Keyboard interrupt received")
        except Exception as e:
            logger.error(f"Bot execution failed: {e}")
            raise
        finally:
            await self._cleanup()
    
    async def _run_polling(self) -> None:
        """
        Run bot in polling mode with shutdown detection.
        Implements proper async polling with signal handling.
        """
        try:
            # Start polling in background task
            polling_task = asyncio.create_task(bot_app.start_polling())
            
            # Wait for shutdown signal
            while not self.shutdown_requested and bot_app.is_running():
                await asyncio.sleep(1)
            
            # Cancel polling if shutdown requested
            if not polling_task.done():
                polling_task.cancel()
                try:
                    await polling_task
                except asyncio.CancelledError:
                    logger.info("Polling task cancelled")
            
        except Exception as e:
            logger.error(f"Polling execution error: {e}")
            raise
    
    async def _cleanup(self) -> None:
        """Cleanup resources and shutdown bot gracefully."""
        try:
            logger.info("Initiating bot shutdown")
            await bot_app.stop()
            logger.info("Bot shutdown completed")
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")


def main() -> NoReturn:
    """
    Application entry point with systematic error handling.
    Implements fail-fast initialization with clear error messaging.
    """
    logger.info("Starting Telegram Bot Application")
    
    try:
        # Validate environment and configuration
        settings.validate()
        logger.info("Configuration validated successfully")
        
        # Create bot runner
        runner = BotRunner()
        runner.setup_signal_handlers()
        
        # Run bot application
        asyncio.run(runner.run_bot())
        
    except ValueError as e:
        logger.error(f"Configuration error: {e}")
        print(f"Configuration Error: {e}")
        print("Please check your environment variables and try again.")
        sys.exit(1)
    
    except KeyboardInterrupt:
        logger.info("Application interrupted by user")
        sys.exit(0)
    
    except Exception as e:
        logger.critical(f"Critical application error: {e}")
        print(f"Critical Error: {e}")
        sys.exit(1)
    
    finally:
        logger.info("Application shutdown complete")


if __name__ == "__main__":
    main()