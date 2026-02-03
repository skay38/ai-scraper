"""Extraction service for company data using Anthropic."""

from src.clients.anthropic_client import AnthropicClient
from src.llm_prompts import (
    build_company_extraction_prompt,
    build_pricing_extraction_prompt,
)
from src.mappers import clean_html, parse_company_response
from src.models import CompanyExtractionData
from src.utils import (
    HTML_TRUNCATE_MAIN,
    HTML_TRUNCATE_PRICING,
    ApiResponseError,
    JsonParseError,
    RateLimitExceededError,
    logger,
)


class ExtractionService:
    """Service for extracting company data using Anthropic.

    This service orchestrates the extraction flow:
    1. Clean and truncate HTML
    2. Build prompts
    3. Call Anthropic API
    4. Parse responses
    """

    def __init__(self, anthropic_client: AnthropicClient) -> None:
        """Initialize extraction service.

        Args:
            anthropic_client: Anthropic API client
        """
        self.client = anthropic_client

    async def extract_company_data(
        self, html: str, url: str
    ) -> tuple[bool, CompanyExtractionData | None, str | None]:
        """Extract company data and pricing URLs from main page HTML.

        Args:
            html: HTML content
            url: Source URL

        Returns:
            Tuple of (success, data, error_message)
        """
        cleaned = clean_html(html)
        truncated = cleaned[:HTML_TRUNCATE_MAIN]

        logger.debug(
            "Truncated HTML content",
            extra={
                "original_length": len(cleaned),
                "truncated_length": len(truncated),
            },
        )

        prompt = build_company_extraction_prompt(
            url=url, content=truncated, max_chars=HTML_TRUNCATE_MAIN
        )

        try:
            response = await self.client.send_message(prompt)
            data = parse_company_response(response, url)
            return (True, data, None)

        except (RateLimitExceededError, ApiResponseError, JsonParseError) as e:
            return (False, None, str(e))

    async def extract_pricing(self, html: str) -> tuple[bool, str, str | None]:
        """Extract pricing details from a pricing page.

        Args:
            html: HTML content

        Returns:
            Tuple of (success, pricing_summary, error_message)
        """
        cleaned = clean_html(html)
        truncated = cleaned[:HTML_TRUNCATE_PRICING]

        prompt = build_pricing_extraction_prompt(
            content=truncated, max_chars=HTML_TRUNCATE_PRICING
        )

        try:
            response = await self.client.send_message(prompt)
            return (True, response.strip(), None)

        except (RateLimitExceededError, ApiResponseError) as e:
            return (False, "Failed to extract pricing", str(e))
