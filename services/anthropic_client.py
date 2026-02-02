"""Anthropic AI client for data extraction."""

import asyncio
import json
import re

from anthropic import APIError, AsyncAnthropic, RateLimitError
from anthropic.types import TextBlock
from bs4 import BeautifulSoup

from models import BusinessType, CompanyExtractionData, PricingStatus
from utils import (
    ANTHROPIC_CONCURRENCY,
    ANTHROPIC_MODEL,
    HTML_TRUNCATE_MAIN,
    HTML_TRUNCATE_PRICING,
    MAX_PRICING_URLS,
    MAX_TOKENS,
    ApiResponseError,
    JsonParseError,
    RateLimitExceededError,
    logger,
)


class AnthropicClient:
    """Client for extracting structured data using Anthropic's Claude API."""

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

    def _clean_html(self, html: str) -> str:
        """Clean HTML by removing scripts, styles, and extra whitespace.

        Args:
            html: Raw HTML content

        Returns:
            Cleaned text content
        """
        soup = BeautifulSoup(html, "html.parser")

        for script in soup(["script", "style", "noscript"]):
            script.decompose()

        return soup.prettify()

    async def _call_api(
        self, prompt: str, max_retries: int = 3
    ) -> tuple[bool, str, str | None]:
        """Call Anthropic API with retry logic.

        Args:
            prompt: Prompt to send to API
            max_retries: Maximum number of retries

        Returns:
            Tuple of (success, response_or_error, error_type)
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
                        return (False, "Unexpected response type", "invalid_response")
                    return (True, first_block.text, None)

                except RateLimitError as e:
                    if attempt < max_retries - 1:
                        await asyncio.sleep(2 ** (attempt + 1))
                    else:
                        raise RateLimitExceededError("Rate limit exceeded") from e

                except APIError as e:
                    raise ApiResponseError("Anthropic API error") from e

            return (False, "Max retries exceeded", "max_retries")

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
        cleaned = self._clean_html(html)
        truncated = cleaned[:HTML_TRUNCATE_MAIN]

        logger.debug(
            "Truncated HTML content",
            extra={"original_length": len(cleaned), "truncated_length": len(truncated)},
        )

        prompt = f"""You are a data extraction assistant. Analyze the following text content from {url} and extract structured company information.

Extract the following information:
1. company_name: The official name of the company
2. company_description: A 1-2 sentence description of what the company does
3. business_type: Classify as "B2B", "B2C", or "B2B2C" (use "Unknown" if unclear)
4. pricing: Extract pricing information if available on this page. If not found, return "Not found on main page"
5. pricing_urls: List of URLs (absolute URLs, not relative paths) that likely contain pricing information. Look for links with text like "Pricing", "Plans", "Get Started", etc. Return empty array if none found.

Content (first {HTML_TRUNCATE_MAIN} characters):
{truncated}

Return ONLY a JSON object with this exact structure (no markdown, no explanation):
{{
  "company_name": "string",
  "company_description": "string",
  "business_type": "string",
  "pricing": "string",
  "pricing_urls": ["string"]
}}

Be concise and accurate. If information is not available, use "Unknown".
"""

        try:
            success, response, error_type = await self._call_api(prompt)

            if not success:
                return (False, None, response)

            return self._parse_company_response(response, url)

        except (RateLimitExceededError, ApiResponseError, JsonParseError) as e:
            return (False, None, str(e))

    def _parse_company_response(
        self, response: str, url: str
    ) -> tuple[bool, CompanyExtractionData | None, str | None]:
        """Parse JSON response from company data extraction.

        Args:
            response: Raw response string
            url: Source URL for resolving relative URLs

        Returns:
            Tuple of (success, data, error_message)
        """
        try:
            json_match = re.search(r"\{[\s\S]*\}", response)
            if not json_match:
                raise JsonParseError("No JSON found in response")

            json_str = json_match.group(0)
            raw_data = json.loads(json_str)

            pricing_urls = self._normalize_pricing_urls(
                raw_data.get("pricing_urls", []), url
            )

            data = CompanyExtractionData(
                company_name=raw_data.get("company_name", BusinessType.UNKNOWN.value),
                company_description=raw_data.get(
                    "company_description", BusinessType.UNKNOWN.value
                ),
                business_type=raw_data.get("business_type", BusinessType.UNKNOWN.value),
                pricing=raw_data.get(
                    "pricing", PricingStatus.NOT_FOUND_ON_MAIN_PAGE.value
                ),
                pricing_urls=pricing_urls,
            )

            return (True, data, None)

        except json.JSONDecodeError as e:
            raise JsonParseError("Failed to parse JSON") from e

    def _normalize_pricing_urls(
        self, pricing_urls: list | None, base_url: str
    ) -> list[str]:
        """Normalize pricing URLs to absolute URLs.

        Args:
            pricing_urls: Raw pricing URLs from extraction
            base_url: Base URL for resolving relative paths

        Returns:
            List of normalized absolute URLs
        """
        if not pricing_urls or not isinstance(pricing_urls, list):
            return []

        normalized: list[str] = []
        for pricing_url in pricing_urls:
            if pricing_url.startswith("/"):
                normalized.append(f"{base_url.rstrip('/')}{pricing_url}")
            elif pricing_url.startswith(("http://", "https://")):
                normalized.append(pricing_url)

        return normalized[:MAX_PRICING_URLS]

    async def extract_pricing(self, html: str) -> tuple[bool, str, str | None]:
        """Extract pricing details from a pricing page.

        Args:
            html: HTML content

        Returns:
            Tuple of (success, pricing_summary, error_message)
        """
        cleaned = self._clean_html(html)
        truncated = cleaned[:HTML_TRUNCATE_PRICING]

        prompt = f"""You are analyzing a pricing page. Extract detailed pricing information from this text content.

Focus on:
- Pricing tiers/plans and their costs
- Billing frequency (monthly, annual)
- Key features or limits per tier
- Any special pricing notes

Content (first {HTML_TRUNCATE_PRICING} characters):
{truncated}

Return a concise summary of the pricing structure (2-3 sentences max).
If no pricing information is found, return "No pricing information available".

Provide ONLY the pricing summary, no other text or explanation.
"""

        try:
            success, response, error_type = await self._call_api(prompt)

            if not success:
                return (False, "Failed to extract pricing", response)

            return (True, response.strip(), None)

        except (RateLimitExceededError, ApiResponseError) as e:
            return (False, "Failed to extract pricing", str(e))
