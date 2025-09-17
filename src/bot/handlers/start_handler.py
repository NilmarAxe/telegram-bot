"""
Start command handler for bot initialization and welcome messages.
Implements clean user onboarding with privacy-focused messaging.
"""

import logging
from telegram import Update
from telegram.ext import ContextTypes

from .base_handler import BaseHandler
from src.bot.utils import MessageFormatter

logger = logging.getLogger(__name__)


class StartHandler(BaseHandler):
    """
    Handler for /start command.
    Provides systematic user onboarding with essential information.
    """
    
    def __init__(self):
        super().__init__("start")
    
    async def _process_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """
        Process start command with personalized welcome message.
        
        Args:
            update: Telegram update object
            context: Telegram context object
        """
        try:
            user_info = self.get_user_info(update)
            user_name = user_info.get('first_name', 'User')
            
            # Generate welcome message
            welcome_message = MessageFormatter.format_welcome_message(user_name)
            
            # Send welcome message
            success = await self._send_message(update, welcome_message)
            
            if success:
                logger.info(f"Welcome message sent to user {user_info['id']}")
            else:
                logger.error(f"Failed to send welcome message to user {user_info['id']}")
            
        except Exception as e:
            logger.error(f"Error processing start command: {e}")
            await self._send_error_message(update, "general")
    
    async def _pre_process(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """
        Pre-processing for start command.
        Log new user interactions for analytics (without storing personal data).
        """
        user_info = self.get_user_info(update)
        logger.info(f"Start command initiated by user {user_info['id']}")
        
        # Check if this is a deep link start (with parameters)
        if context.args:
            logger.info(f"Start command with parameters: {len(context.args)} args")
    
    async def _post_process(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """
        Post-processing for start command.
        Track successful onboarding for system metrics.
        """
        user_info = self.get_user_info(update)
        logger.info(f"User {user_info['id']} successfully onboarded")