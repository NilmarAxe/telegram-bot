"""
Joke service with icanhazdadjoke API integration.
Simple service for humor content retrieval.
"""

import logging
from typing import Optional
from dataclasses import dataclass

from src.config import settings
from .http_client import http_client, HTTPClientError

logger = logging.getLogger(__name__)


@dataclass
class JokeData:
    """Structured joke data model."""
    id: str
    joke: str
    status: int


class JokeServiceError(Exception):
    """Custom exception for joke service errors."""
    
    def __init__(self, message: str, error_type: str = "general"):
        self.message = message
        self.error_type = error_type
        super().__init__(self.message)


class JokeService:
    """
    Joke retrieval service with error handling.
    Implements clean separation of concerns for humor content.
    """
    
    def __init__(self):
        self.base_url = settings.api.joke_api_url.rstrip('/')
        self.headers = {
            'Accept': 'application/json',
            'User-Agent': 'TelegramBot/1.0.0 (https://github.com/user/telegram-bot)'
        }
    
    async def get_random_joke(self) -> JokeData:
        """
        Retrieve a random dad joke from the API.
        
        Returns:
            JokeData: Structured joke information
            
        Raises:
            JokeServiceError: On service errors
        """
        try:
            logger.info("Requesting random joke")
            
            data, status_code = await http_client.get(
                url=self.base_url,
                headers=self.headers,
                service_name="icanhazdadjoke"
            )
            
            # Parse response
            joke_data = self._parse_joke_response(data, status_code)
            
            logger.info(f"Joke retrieved successfully: ID {joke_data.id}")
            return joke_data
            
        except HTTPClientError as e:
            logger.error(f"HTTP error in joke service: {e.message}")
            
            if e.status_code and e.status_code >= 500:
                raise JokeServiceError(
                    "Joke service temporarily unavailable",
                    "service_unavailable"
                )
            else:
                raise JokeServiceError(
                    "Joke service error occurred",
                    "api_error"
                )
        
        except Exception as e:
            logger.error(f"Unexpected error in joke service: {e}")
            raise JokeServiceError(
                "Joke retrieval failed",
                "internal_error"
            )
    
    async def get_joke_by_id(self, joke_id: str) -> JokeData:
        """
        Retrieve a specific joke by ID.
        Future expansion method for targeted joke requests.
        
        Args:
            joke_id: Specific joke identifier
            
        Returns:
            JokeData: Requested joke information
        """
        if not joke_id or not joke_id.strip():
            raise JokeServiceError("Invalid joke ID", "validation_error")
        
        try:
            url = f"{self.base_url}/j/{joke_id.strip()}"
            
            data, status_code = await http_client.get(
                url=url,
                headers=self.headers,
                service_name="icanhazdadjoke"
            )
            
            return self._parse_joke_response(data, status_code)
            
        except HTTPClientError as e:
            if e.status_code == 404:
                raise JokeServiceError(f"Joke {joke_id} not found", "joke_not_found")
            
            raise JokeServiceError("Specific joke retrieval failed", "api_error")
    
    async def search_jokes(self, term: str, limit: int = 10) -> list[JokeData]:
        """
        Search for jokes containing specific term.
        Future expansion method for joke search functionality.
        
        Args:
            term: Search term
            limit: Maximum results to return
            
        Returns:
            List[JokeData]: List of matching jokes
        """
        if not term or not term.strip():
            raise JokeServiceError("Search term cannot be empty", "validation_error")
        
        if limit < 1 or limit > 30:
            raise JokeServiceError("Limit must be between 1 and 30", "validation_error")
        
        try:
            url = f"{self.base_url}/search"
            params = {
                'term': term.strip(),
                'limit': limit
            }
            
            data, status_code = await http_client.get(
                url=url,
                params=params,
                headers=self.headers,
                service_name="icanhazdadjoke"
            )
            
            return self._parse_search_response(data)
            
        except HTTPClientError as e:
            logger.error(f"Joke search failed: {e.message}")
            raise JokeServiceError("Joke search failed", "search_error")
    
    def _parse_joke_response(self, data: dict, status_code: int) -> JokeData:
        """
        Parse single joke API response.
        
        Args:
            data: API response data
            status_code: HTTP status code
            
        Returns:
            JokeData: Parsed joke information
            
        Raises:
            JokeServiceError: On parsing errors
        """
        try:
            joke_id = data.get('id', 'unknown')
            joke_text = data.get('joke', '').strip()
            
            if not joke_text:
                raise JokeServiceError("Empty joke received", "empty_joke")
            
            # Basic content validation
            if len(joke_text) > 1000:  # Reasonable joke length limit
                joke_text = joke_text[:997] + "..."
            
            return JokeData(
                id=joke_id,
                joke=joke_text,
                status=status_code
            )
            
        except KeyError as e:
            logger.error(f"Missing field in joke response: {e}")
            raise JokeServiceError(
                f"Invalid joke data format: missing {e}",
                "data_format_error"
            )
    
    def _parse_search_response(self, data: dict) -> list[JokeData]:
        """
        Parse joke search API response.
        
        Args:
            data: Search API response data
            
        Returns:
            List[JokeData]: List of parsed jokes
        """
        try:
            results = data.get('results', [])
            jokes = []
            
            for joke_data in results:
                joke = self._parse_joke_response(joke_data, 200)
                jokes.append(joke)
            
            return jokes
            
        except Exception as e:
            logger.error(f"Error parsing search results: {e}")
            raise JokeServiceError("Search results parsing failed", "parse_error")
    
    def is_service_available(self) -> bool:
        """
        Check if joke service is available.
        Basic availability check for service status.
        
        Returns:
            bool: Always True for icanhazdadjoke (no auth required)
        """
        return True


# Global joke service instance
joke_service = JokeService()