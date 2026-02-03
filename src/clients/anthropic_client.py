"""Anthropic AI client for API interactions."""

import asyncio

from anthropic import APIError, AsyncAnthropic, RateLimitError
from anthropic.types import TextBlock

from src.utils import (
    ANTHROPIC_CONCURRENCY,
    ANTHROPIC_MODEL,
    MAX_TOKENS,
    ApiResponseError,
    RateLimitExceededError,
)


class AnthropicClient:
    """Pure API client for Anthropic's Claude API.

    This client handles only API communication with retry/rate-limit logic.
    Business logic and data transformation are handled by ExtractionService.
    """

    def __init__(
        self, api_key: str, semaphore: asyncio.Semaphore | None = None
    ) -> None:
        """Initialize Anthropic client.

        Args:
            api_key: Anthropic API key
            semaphore: Optional semaphore for rate limiting
        """
        self.client = AsyncAnthropic(api_key=api_key)
        self.semaphore = semaphore or asyncio.Semaphore(ANTHROPIC_CONCURRENCY)

    async def send_message(self, prompt: str, max_retries: int = 3) -> str:
        """Send a prompt to Anthropic and return the response text.

        Args:
            prompt: Prompt to send to API
            max_retries: Maximum number of retries

        Returns:
            Response text from the API

        Raises:
            RateLimitExceededError: When rate limit exceeded after retries
            ApiResponseError: On API errors or unexpected response types
        """
        async with self.semaphore:
            for attempt in range(max_retries):
                try:
                    response = await self.client.messages.create(
                        model=ANTHROPIC_MODEL,
                        max_tokens=MAX_TOKENS,
                        messages=[{"role": "user", "content": prompt}],
                    )

                    first_block = response.content[0]
                    if not isinstance(first_block, TextBlock):
                        raise ApiResponseError("Unexpected response type from API")

                    return first_block.text

                except RateLimitError as e:
                    if attempt < max_retries - 1:
                        await asyncio.sleep(2 ** (attempt + 1))
                    else:
                        raise RateLimitExceededError("Rate limit exceeded") from e

                except APIError as e:
                    raise ApiResponseError("Anthropic API error") from e

            raise ApiResponseError("Max retries exceeded")
