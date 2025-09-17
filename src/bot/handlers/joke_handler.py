"""
Joke command handler with icanhazdadjoke integration.
Simple handler for humor content delivery with error resilience.
"""

import logging
from telegram import Update
from telegram.ext import ContextTypes

from .base_handler import BaseHandler
from src.bot.services import joke_service, JokeServiceError
from src.bot.utils import MessageFormatter

logger = logging.getLogger(__name__)


class JokeHandler(BaseHandler):
    """
    Handler for /joke command.
    Implements straightforward joke retrieval with graceful error handling.
    """
    
    def __init__(self):
        super().__init__("joke")
    
    async def _process_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """
        Process joke command with simple error handling.
        
        Args:
            update: Telegram update object
            context: Telegram context object
        """
        try:
            # Check service availability
            if not joke_service.is_service_available():
                await self._send_error_message(
                    update,
                    "api_unavailable",
                    "Joke service not available"
                )
                return
            
            # Retrieve random joke
            logger.info("Processing joke request")
            joke_data = await joke_service.get_random_joke()
            
            # Format and send joke
            joke_message = MessageFormatter.format_joke_message(joke_data.joke)
            success = await self._send_message(update, joke_message)
            
            if success:
                logger.info(f"Joke delivered successfully: ID {joke_data.id}")
            
        except JokeServiceError as e:
            logger.warning(f"Joke service error: {e.message}")
            
            # Map service errors to user-friendly messages
            error_type_mapping = {
                "service_unavailable": "api_unavailable",
                "api_error": "api_unavailable", 
                "empty_joke": "api_unavailable",
                "internal_error": "general"
            }
            
            error_type = error_type_mapping.get(e.error_type, "general")
            await self._send_error_message(update, error_type)
        
        except Exception as e:
            logger.error(f"Unexpected error in joke handler: {e}")
            await self._send_error_message(update, "general")
    
    async def _pre_process(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """
        Pre-processing for joke command.
        Log request initiation and validate service status.
        """
        user_info = self.get_user_info(update)
        logger.info(f"Joke request from user {user_info['id']}")
        
        # Service status check for logging
        if not joke_service.is_service_available():
            logger.warning("Joke service reported as unavailable")
    
    async def _post_process(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """
        Post-processing for joke command.
        Log completion and update humor delivery metrics.
        """
        user_info = self.get_user_info(update)
        logger.info(f"Joke command completed for user {user_info['id']}")


class JokeSearchHandler(BaseHandler):
    """
    Future expansion: Handler for joke search functionality.
    Allows users to search for jokes by keyword.
    """
    
    def __init__(self):
        super().__init__("joke_search")
    
    async def _process_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """
        Process joke search command with keyword validation.
        Future implementation for targeted joke searches.
        
        Args:
            update: Telegram update object
            context: Telegram context object
        """
        try:
            args = self._extract_command_args(context)
            
            if not args:
                usage_message = MessageFormatter.format_usage_message(
                    "joke_search",
                    "/joke_search <keyword>",
                    "Search for jokes containing specific keyword"
                )
                await self._send_message(update, usage_message)
                return
            
            search_term = ' '.join(args)
            
            # Perform joke search
            joke_results = await joke_service.search_jokes(search_term, limit=5)
            
            if not joke_results:
                await self._send_error_message(
                    update,
                    "general", 
                    f"No jokes found for '{search_term}'"
                )
                return
            
            # Format search results
            response_parts = [f"🔍 *Joke Search Results for '{search_term}'*\n"]
            
            for i, joke in enumerate(joke_results, 1):
                joke_message = MessageFormatter.format_joke_message(joke.joke)
                response_parts.append(f"{i}\\. {joke_message}")
            
            search_response = "\n\n".join(response_parts)
            await self._send_message(update, search_response)
            
        except JokeServiceError as e:
            logger.warning(f"Joke search error: {e.message}")
            await self._send_error_message(update, "api_unavailable")
        
        except Exception as e:
            logger.error(f"Unexpected error in joke search: {e}")
            await self._send_error_message(update, "general")