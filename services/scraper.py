"""Scraper service for extracting company data from URLs."""

import asyncio

from pydantic import ValidationError as PydanticValidationError

from models import PricingStatus, ScrapingData, ScrapingResult
from services.anthropic_client import AnthropicClient
from services.http_client import HttpClient
from utils import MAX_PRICING_URLS, ValidationError


class ScraperService:
    """Service for scraping and extracting company data from URLs."""

    def __init__(
        self,
        http_client: HttpClient,
        anthropic_client: AnthropicClient,
    ) -> None:
        """Initialize scraper service.

        Args:
            http_client: HTTP client for fetching pages
            anthropic_client: Anthropic client for data extraction
        """
        self.http_client = http_client
        self.anthropic_client = anthropic_client

    async def scrape_url(self, url: str) -> ScrapingResult:
        """Scrape a URL and extract company data.

        Multi-step flow:
        1. Fetch main URL
        2. Extract company data + pricing URLs from Anthropic
        3. Fetch pricing URLs (if any)
        4. Extract pricing from pricing pages
        5. Aggregate all data
        6. Return result

        Args:
            url: URL to scrape

        Returns:
            ScrapingResult with extracted data or error
        """
        success, content, error_type = await self.http_client.get(url)
        if not success:
            return ScrapingResult(url=url, success=False, error=content)

        (
            success,
            extracted_data,
            error_msg,
        ) = await self.anthropic_client.extract_company_data(content, url)
        if not success or extracted_data is None:
            return ScrapingResult(
                url=url, success=False, error=f"AI extraction failed: {error_msg}"
            )

        pricing_results = await self._fetch_pricing_pages(extracted_data.pricing_urls)

        final_pricing = self._aggregate_pricing(extracted_data.pricing, pricing_results)

        try:
            data = ScrapingData(
                company_name=extracted_data.company_name,
                company_description=extracted_data.company_description,
                business_type=extracted_data.business_type,
                pricing=final_pricing,
                pricing_urls=extracted_data.pricing_urls,
            )
            return ScrapingResult(url=url, success=True, data=data)

        except PydanticValidationError as e:
            raise ValidationError("Data validation failed") from e

    async def _fetch_pricing_pages(
        self, pricing_urls: list[str]
    ) -> list[str | None | BaseException]:
        """Fetch and extract pricing from pricing pages.

        Args:
            pricing_urls: List of pricing page URLs

        Returns:
            List of pricing summaries (None for failed extractions, BaseException for errors)
        """
        if not pricing_urls:
            return []

        pricing_tasks = [
            self._fetch_and_extract_pricing(pricing_url)
            for pricing_url in pricing_urls[:MAX_PRICING_URLS]
        ]

        return await asyncio.gather(*pricing_tasks, return_exceptions=True)

    async def _fetch_and_extract_pricing(self, pricing_url: str) -> str | None:
        """Fetch a pricing page and extract pricing info.

        Args:
            pricing_url: URL of pricing page

        Returns:
            Pricing summary or None if failed
        """
        success, content, error_type = await self.http_client.get(pricing_url)
        if not success:
            return None

        (
            success,
            pricing_summary,
            error_msg,
        ) = await self.anthropic_client.extract_pricing(content)
        if not success or pricing_summary == PricingStatus.NO_PRICING_INFO:
            return None

        return pricing_summary

    def _aggregate_pricing(
        self, main_pricing: str, pricing_results: list[str | None | BaseException]
    ) -> str:
        """Aggregate pricing from main page and pricing pages.

        Args:
            main_pricing: Pricing from main page
            pricing_results: List of pricing summaries from pricing pages

        Returns:
            Aggregated pricing string
        """
        valid_pricing = [
            p
            for p in pricing_results
            if p is not None and not isinstance(p, BaseException) and p.strip()
        ]

        no_pricing_values = [
            PricingStatus.NOT_FOUND_ON_MAIN_PAGE,
            PricingStatus.NOT_AVAILABLE,
            PricingStatus.UNKNOWN,
        ]

        main_has_pricing = main_pricing and main_pricing not in no_pricing_values

        if not valid_pricing and not main_has_pricing:
            return PricingStatus.NOT_AVAILABLE

        if not valid_pricing:
            return main_pricing if main_has_pricing else PricingStatus.NOT_AVAILABLE

        if main_has_pricing:
            return f"{main_pricing} | {' | '.join(valid_pricing)}"

        return " | ".join(valid_pricing)
