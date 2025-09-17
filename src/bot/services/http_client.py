"""
HTTP client service with connection pooling and error handling.
Systematic approach to external API communication.
"""

import asyncio
import logging
from typing import Optional, Dict, Any, Tuple
from contextlib import asynccontextmanager
import aiohttp
from aiohttp import ClientTimeout, ClientError

from src.config import settings
from src.bot.utils import LogFormatter

logger = logging.getLogger(__name__)


class HTTPClientError(Exception):
    """Custom exception for HTTP client errors."""
    
    def __init__(self, message: str, status_code: Optional[int] = None, service: str = "unknown"):
        self.message = message
        self.status_code = status_code
        self.service = service
        super().__init__(self.message)


class HTTPClient:
    """
    Centralized HTTP client with connection pooling and retry logic.
    Implements circuit breaker pattern for reliability.
    """
    
    def __init__(self):
        self._session: Optional[aiohttp.ClientSession] = None
        self._timeout = ClientTimeout(total=settings.api.request_timeout)
        self._max_retries = settings.api.max_retries
        self._circuit_breaker = {}  # Simple circuit breaker state
    
    async def _create_session(self) -> aiohttp.ClientSession:
        """Create HTTP session with optimized settings."""
        connector = aiohttp.TCPConnector(
            limit=100,  # Total connection pool size
            limit_per_host=30,  # Connections per host
            ttl_dns_cache=300,  # DNS cache TTL
            use_dns_cache=True,
            enable_cleanup_closed=True
        )
        
        return aiohttp.ClientSession(
            connector=connector,
            timeout=self._timeout,
            headers={
                'User-Agent': 'TelegramBot/1.0.0',
                'Accept': 'application/json',
                'Accept-Encoding': 'gzip, deflate',
                'Connection': 'keep-alive'
            }
        )
    
    @asynccontextmanager
    async def session(self):
        """Context manager for HTTP session lifecycle."""
        if not self._session or self._session.closed:
            self._session = await self._create_session()
        
        try:
            yield self._session
        except Exception as e:
            logger.error(f"Session error: {e}")
            raise
    
    async def get(
        self,
        url: str,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        service_name: str = "unknown"
    ) -> Tuple[Dict[str, Any], int]:
        """
        Perform GET request with retry logic and error handling.
        
        Args:
            url: Request URL
            params: Query parameters
            headers: Additional headers
            service_name: Service identifier for logging
            
        Returns:
            Tuple[Dict[str, Any], int]: (response_data, status_code)
            
        Raises:
            HTTPClientError: On request failure
        """
        if self._is_circuit_broken(service_name):
            raise HTTPClientError(f"Circuit breaker open for {service_name}", service=service_name)
        
        start_time = asyncio.get_event_loop().time()
        
        for attempt in range(self._max_retries + 1):
            try:
                async with self.session() as session:
                    async with session.get(url, params=params, headers=headers) as response:
                        duration = asyncio.get_event_loop().time() - start_time
                        
                        # Log API call
                        log_entry = LogFormatter.format_api_call(
                            service_name, url, str(response.status), duration
                        )
                        logger.info(log_entry)
                        
                        # Handle different status codes
                        if response.status == 200:
                            self._reset_circuit_breaker(service_name)
                            data = await response.json()
                            return data, response.status
                        
                        elif response.status == 404:
                            # Don't retry on 404
                            raise HTTPClientError(
                                f"Resource not found: {url}",
                                status_code=response.status,
                                service=service_name
                            )
                        
                        elif response.status >= 500:
                            # Retry on server errors
                            if attempt < self._max_retries:
                                wait_time = 2 ** attempt  # Exponential backoff
                                await asyncio.sleep(wait_time)
                                continue
                        
                        # Other client errors
                        error_text = await response.text()
                        raise HTTPClientError(
                            f"HTTP {response.status}: {error_text}",
                            status_code=response.status,
                            service=service_name
                        )
            
            except asyncio.TimeoutError:
                if attempt < self._max_retries:
                    logger.warning(f"Timeout on attempt {attempt + 1} for {service_name}")
                    await asyncio.sleep(2 ** attempt)
                    continue
                
                self._trip_circuit_breaker(service_name)
                raise HTTPClientError(
                    f"Request timeout after {self._max_retries + 1} attempts",
                    service=service_name
                )
            
            except ClientError as e:
                if attempt < self._max_retries:
                    logger.warning(f"Client error on attempt {attempt + 1}: {e}")
                    await asyncio.sleep(2 ** attempt)
                    continue
                
                self._trip_circuit_breaker(service_name)
                raise HTTPClientError(f"Client error: {str(e)}", service=service_name)
            
            except Exception as e:
                logger.error(f"Unexpected error in HTTP client: {e}")
                raise HTTPClientError(f"Unexpected error: {str(e)}", service=service_name)
        
        # Should not reach here
        raise HTTPClientError("Maximum retries exceeded", service=service_name)
    
    def _is_circuit_broken(self, service: str) -> bool:
        """Check if circuit breaker is open for service."""
        if service not in self._circuit_breaker:
            return False
        
        breaker_state = self._circuit_breaker[service]
        current_time = asyncio.get_event_loop().time()
        
        # Reset after 60 seconds
        if current_time - breaker_state['trip_time'] > 60:
            self._reset_circuit_breaker(service)
            return False
        
        return breaker_state['tripped']
    
    def _trip_circuit_breaker(self, service: str):
        """Trip circuit breaker for service."""
        self._circuit_breaker[service] = {
            'tripped': True,
            'trip_time': asyncio.get_event_loop().time()
        }
        logger.warning(f"Circuit breaker tripped for {service}")
    
    def _reset_circuit_breaker(self, service: str):
        """Reset circuit breaker for service."""
        if service in self._circuit_breaker:
            del self._circuit_breaker[service]
    
    async def close(self):
        """Close HTTP session and cleanup resources."""
        if self._session and not self._session.closed:
            await self._session.close()
            self._session = None
        logger.info("HTTP client session closed")


# Global HTTP client instance
http_client = HTTPClient()