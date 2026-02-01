"""HTTP client with retry logic and error handling."""

import asyncio
import random

import httpx

from config import (
    HTTP_CONCURRENCY,
    HTTP_MAX_RETRIES,
    HTTP_RETRY_BACKOFF,
    HTTP_TIMEOUT_CONNECT,
    HTTP_TIMEOUT_READ,
    USER_AGENTS,
)
from exceptions import (
    ConnectionTimeoutError,
    ContentTypeError,
    HttpClientError,
    NetworkError,
    ReadTimeoutError,
    TooManyRedirectsError,
)


class HttpClient:
    """Async HTTP client with retry logic and comprehensive error handling."""

    def __init__(self, semaphore: asyncio.Semaphore | None = None) -> None:
        """Initialize HTTP client.

        Args:
            semaphore: Optional semaphore for concurrency control
        """
        self.semaphore = semaphore or asyncio.Semaphore(HTTP_CONCURRENCY)
        self.timeout = httpx.Timeout(
            connect=HTTP_TIMEOUT_CONNECT,
            read=HTTP_TIMEOUT_READ,
            write=HTTP_TIMEOUT_READ,
            pool=None,
        )

    def _get_headers(self) -> dict[str, str]:
        """Get random User-Agent header."""
        return {"User-Agent": random.choice(USER_AGENTS)}

    async def get(self, url: str) -> tuple[bool, str, str | None]:
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
                        if not url.startswith(("http://", "https://")):
                            url = f"https://{url}"

                        response = await client.get(
                            url, headers=self._get_headers(), follow_redirects=True
                        )
                        response.raise_for_status()

                        content_type = response.headers.get("content-type", "")
                        if "text/html" not in content_type.lower():
                            raise ContentTypeError(
                                f"Invalid content type: {content_type}"
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
                    if (
                        400 <= e.response.status_code < 500
                        and e.response.status_code != 429
                    ):
                        return (False, error_msg, error_type)
                except httpx.NetworkError:
                    error_msg = "Network error"
                    error_type = "network_error"
                except httpx.TooManyRedirects:
                    error_msg = "Too many redirects"
                    error_type = "too_many_redirects"
                    return (False, error_msg, error_type)
                except ContentTypeError as e:
                    return (False, str(e), "invalid_content_type")
                except (
                    ConnectionTimeoutError,
                    ReadTimeoutError,
                    NetworkError,
                    TooManyRedirectsError,
                    HttpClientError,
                ) as e:
                    error_msg = str(e)
                    error_type = type(e).__name__
                    return (False, error_msg, error_type)

                if attempt < HTTP_MAX_RETRIES - 1:
                    await asyncio.sleep(HTTP_RETRY_BACKOFF * (2**attempt))

            return (False, error_msg, error_type)
