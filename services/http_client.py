"""HTTP client with retry logic and error handling."""

import asyncio
import random
from typing import Optional

import httpx

from config import (
    HTTP_MAX_RETRIES,
    HTTP_RETRY_BACKOFF,
    HTTP_TIMEOUT_CONNECT,
    HTTP_TIMEOUT_READ,
    USER_AGENTS,
)


class HttpClient:
    """Async HTTP client with retry logic and comprehensive error handling."""

    def __init__(self, semaphore: Optional[asyncio.Semaphore] = None):
        """Initialize HTTP client.

        Args:
            semaphore: Optional semaphore for concurrency control
        """
        self.semaphore = semaphore or asyncio.Semaphore(50)
        self.timeout = httpx.Timeout(
            connect=HTTP_TIMEOUT_CONNECT, read=HTTP_TIMEOUT_READ, write=HTTP_TIMEOUT_READ, pool=None
        )

    def _get_headers(self) -> dict[str, str]:
        """Get random User-Agent header."""
        return {"User-Agent": random.choice(USER_AGENTS)}

    async def get(self, url: str) -> tuple[bool, str, Optional[str]]:
        """Fetch URL with retry logic.

        Args:
            url: URL to fetch

        Returns:
            Tuple of (success, content_or_error, error_type)
            - If success: (True, html_content, None)
            - If failure: (False, error_message, error_type)
        """
        async with self.semaphore:
            error_msg = "Unknown error"
            error_type = "unknown"

            for attempt in range(HTTP_MAX_RETRIES):
                try:
                    async with httpx.AsyncClient(timeout=self.timeout) as client:
                        # Ensure URL has scheme
                        if not url.startswith(("http://", "https://")):
                            url = f"https://{url}"

                        response = await client.get(url, headers=self._get_headers(), follow_redirects=True)
                        response.raise_for_status()

                        # Check content type
                        content_type = response.headers.get("content-type", "")
                        if "text/html" not in content_type.lower():
                            return (
                                False,
                                f"Invalid content type: {content_type}",
                                "invalid_content_type",
                            )

                        return (True, response.text, None)

                except httpx.ConnectTimeout:
                    error_msg = "Connection timeout"
                    error_type = "connect_timeout"
                except httpx.ReadTimeout:
                    error_msg = "Read timeout"
                    error_type = "read_timeout"
                except httpx.HTTPStatusError as e:
                    error_msg = f"HTTP {e.response.status_code}"
                    error_type = f"http_{e.response.status_code}"
                    # Don't retry on 4xx errors (except 429)
                    if 400 <= e.response.status_code < 500 and e.response.status_code != 429:
                        return (False, error_msg, error_type)
                except httpx.NetworkError:
                    error_msg = "Network error"
                    error_type = "network_error"
                except httpx.TooManyRedirects:
                    error_msg = "Too many redirects"
                    error_type = "too_many_redirects"
                    return (False, error_msg, error_type)
                except Exception as e:
                    error_msg = f"Unexpected error: {str(e)}"
                    error_type = "unexpected_error"

                # Retry with exponential backoff
                if attempt < HTTP_MAX_RETRIES - 1:
                    await asyncio.sleep(HTTP_RETRY_BACKOFF * (2**attempt))

            # All retries exhausted
            return (False, error_msg, error_type)
