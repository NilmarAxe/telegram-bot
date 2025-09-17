"""
Base handler class with common functionality.
"""

import logging
from abc import ABC, abstractmethod
from typing import Optional, Dict, Any
from telegram import Update
from telegram.ext import ContextTypes
from telegram.constants import ParseMode

from src.bot.utils import MessageFormatter, LogFormatter, InputValidator, ValidationError

logger = logging.getLogger(__name__)


class BaseHandler(ABC):
    """
    Abstract base handler with common functionality.
    Implements template method pattern for consistent handler behavior.
    """
    
    def __init__(self, command_name: str):
        self.command_name = command_name
        self._rate_limiter: Dict[int, Dict[str, Any]] = {}
    
    async def handle(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """
        Main handler entry point with standardized flow.
        Template method implementing common handler logic.
        """
        try:
            # Extract user information
            user = update.effective_user
            if not user:
                logger.warning("Update received without user information")
                return
            
            # Validate user
            if not InputValidator.validate_user_id(user.id):
                logger.warning(f"Invalid user ID received: {user.id}")
                return
            
            # Rate limiting check
            if self._is_rate_limited(user.id):
                await self._send_rate_limit_message(update)
                return
            
            # Log user action
            log_message = LogFormatter.format_user_action(
                user.id, user.username, f"/{self.command_name}"
            )
            logger.info(log_message)
            
            # Pre-processing hook
            await self._pre_process(update, context)
            
            # Main command processing
            await self._process_command(update, context)
            
            # Post-processing hook
            await self._post_process(update, context)
            
            # Update rate limiter
            self._update_rate_limit(user.id)
            
        except ValidationError as e:
            logger.warning(f"Validation error in {self.command_name}: {e.message}")
            await self._send_error_message(update, "invalid_input", e.message)
        
        except Exception as e:
            logger.error(f"Unexpected error in {self.command_name} handler: {e}")
            await self._send_error_message(update, "general")
    
    @abstractmethod
    async def _process_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """
        Abstract method for command-specific processing.
        Must be implemented by concrete handlers.
        """
        pass
    
    async def _pre_process(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """
        Pre-processing hook for common setup logic.
        Override in subclasses for specific pre-processing needs.
        """
        pass
    
    async def _post_process(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """
        Post-processing hook for cleanup and analytics.
        Override in subclasses for specific post-processing needs.
        """
        pass
    
    async def _send_message(
        self,
        update: Update,
        message: str,
        parse_mode: ParseMode = ParseMode.MARKDOWN_V2
    ) -> bool:
        """
        Send message with error handling and length validation.
        
        Args:
            update: Telegram update object
            message: Message to send
            parse_mode: Message parsing mode
            
        Returns:
            bool: True if message sent successfully
        """
        try:
            # Validate message length
            if not MessageFormatter.truncate_message(message):
                logger.error("Message too long after truncation")
                return False
            
            # Truncate if necessary
            safe_message = MessageFormatter.truncate_message(message)
            
            await update.message.reply_text(
                text=safe_message,
                parse_mode=parse_mode
            )
            return True
            
        except Exception as e:
            logger.error(f"Failed to send message: {e}")
            
            # Fallback: send plain text without formatting
            try:
                await update.message.reply_text(
                    text="⚠️ Response formatting error - message sent in plain text",
                    parse_mode=None
                )
            except Exception as fallback_error:
                logger.error(f"Fallback message also failed: {fallback_error}")
            
            return False
    
    async def _send_error_message(
        self,
        update: Update,
        error_type: str,
        details: Optional[str] = None
    ) -> None:
        """
        Send formatted error message to user.
        
        Args:
            update: Telegram update object
            error_type: Type of error (timeout, api_error, etc.)
            details: Optional error details
        """
        error_message = MessageFormatter.format_error_message(error_type, details)
        await self._send_message(update, error_message)
    
    async def _send_rate_limit_message(self, update: Update) -> None:
        """Send rate limit exceeded message."""
        message = MessageFormatter.format_error_message(
            "general", 
            "Rate limit exceeded - please wait before sending more commands"
        )
        await self._send_message(update, message)
    
    def _is_rate_limited(self, user_id: int) -> bool:
        """
        Check if user has exceeded rate limits.
        Simple sliding window rate limiting implementation.
        
        Args:
            user_id: User identifier
            
        Returns:
            bool: True if rate limited
        """
        import time
        
        current_time = time.time()
        
        if user_id not in self._rate_limiter:
            self._rate_limiter[user_id] = {
                'requests': [],
                'window_start': current_time
            }
        
        user_data = self._rate_limiter[user_id]
        
        # Clean old requests (older than 1 minute)
        user_data['requests'] = [
            req_time for req_time in user_data['requests']
            if current_time - req_time < 60
        ]
        
        # Check rate limit (20 requests per minute)
        if len(user_data['requests']) >= 20:
            logger.warning(f"Rate limit exceeded for user {user_id}")
            return True
        
        return False
    
    def _update_rate_limit(self, user_id: int) -> None:
        """Update rate limiting data for user."""
        import time
        
        if user_id not in self._rate_limiter:
            self._rate_limiter[user_id] = {'requests': []}
        
        self._rate_limiter[user_id]['requests'].append(time.time())
    
    def _extract_command_args(self, context: ContextTypes.DEFAULT_TYPE) -> list[str]:
        """
        Extract and validate command arguments.
        
        Args:
            context: Telegram context object
            
        Returns:
            List[str]: Cleaned command arguments
        """
        if not context.args:
            return []
        
        # Sanitize arguments
        clean_args = []
        for arg in context.args:
            sanitized = InputValidator.sanitize_input(arg)
            if sanitized:  # Only include non-empty arguments
                clean_args.append(sanitized)
        
        return clean_args
    
    def get_user_info(self, update: Update) -> Dict[str, Any]:
        """
        Extract user information from update.
        
        Args:
            update: Telegram update object
            
        Returns:
            Dict[str, Any]: User information dictionary
        """
        user = update.effective_user
        if not user:
            return {}
        
        return {
            'id': user.id,
            'username': user.username,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'language_code': user.language_code,
            'is_bot': user.is_bot
        }