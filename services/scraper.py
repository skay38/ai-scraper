import asyncio
from typing import Optional

from pydantic import BaseModel, ValidationError

from services.anthropic_client import AnthropicClient
from services.http_client import HttpClient


class ScrapingData(BaseModel):
    company_name: str
    company_description: str
    business_type: str
    pricing: str
    pricing_urls: list[str] = []


class ScrapingResult(BaseModel):
    url: str
    success: bool
    data: ScrapingData | None = None
    error: str | None = None


class ScraperService:
    """Service for scraping and extracting company data from URLs."""

    def __init__(
        self,
        http_client: HttpClient,
        anthropic_client: AnthropicClient,
    ):
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
        # Step 1: Fetch main URL
        success, content, error_type = await self.http_client.get(url)
        if not success:
            return ScrapingResult(url=url, success=False, error=content)
        
        # Step 2: Extract company data + pricing URLs
        success, extracted_data, error_msg = await self.anthropic_client.extract_company_data(
            content, url
        )
        if not success:
            return ScrapingResult(
                url=url, success=False, error=f"AI extraction failed: {error_msg}"
            )

        # Extract pricing URLs
        pricing_urls = extracted_data.get("pricing_urls", [])
        main_pricing = extracted_data.get("pricing", "Not available")

        # Step 3 & 4: Fetch and extract pricing from pricing pages (if any)
        pricing_results = []
        if pricing_urls:
            pricing_tasks = []
            for pricing_url in pricing_urls[:3]:  # Limit to 3 pricing pages
                pricing_tasks.append(self._fetch_and_extract_pricing(pricing_url))

            pricing_results = await asyncio.gather(*pricing_tasks, return_exceptions=True)

        # Step 5: Aggregate pricing data
        final_pricing = self._aggregate_pricing(main_pricing, pricing_results)

        # Step 6: Create final result
        try:
            data = ScrapingData(
                company_name=extracted_data.get("company_name", "Unknown"),
                company_description=extracted_data.get("company_description", "Not available"),
                business_type=extracted_data.get("business_type", "Unknown"),
                pricing=final_pricing,
                pricing_urls=pricing_urls if isinstance(pricing_urls, list) else [],
            )
            return ScrapingResult(url=url, success=True, data=data)

        except ValidationError as e:
            return ScrapingResult(
                url=url,
                success=False,
                error=f"Data validation failed: {str(e)}",
            )
        except Exception as e:
            return ScrapingResult(
                url=url,
                success=False,
                error=f"Unexpected error: {str(e)}",
            )

    async def _fetch_and_extract_pricing(self, pricing_url: str) -> Optional[str]:
        """Fetch a pricing page and extract pricing info.

        Args:
            pricing_url: URL of pricing page

        Returns:
            Pricing summary or None if failed
        """
        # Fetch pricing page
        success, content, error_type = await self.http_client.get(pricing_url)
        if not success:
            return None

        # Extract pricing
        success, pricing_summary, error_msg = await self.anthropic_client.extract_pricing(
            content
        )
        if not success or pricing_summary == "No pricing information available":
            return None

        return pricing_summary

    def _aggregate_pricing(self, main_pricing: str, pricing_results: list) -> str:
        """Aggregate pricing from main page and pricing pages.

        Args:
            main_pricing: Pricing from main page
            pricing_results: List of pricing summaries from pricing pages

        Returns:
            Aggregated pricing string
        """
        # Filter out None and exceptions from pricing results
        valid_pricing = [
            p for p in pricing_results
            if p is not None and not isinstance(p, Exception) and p.strip()
        ]

        # If no pricing found anywhere
        if not valid_pricing and (
            not main_pricing
            or main_pricing in ["Not found on main page", "Not available", "Unknown"]
        ):
            return "Pricing information not available"

        # If main pricing has good info but no pricing pages
        if not valid_pricing:
            if main_pricing not in ["Not found on main page", "Not available", "Unknown"]:
                return main_pricing
            else:
                return "Pricing information not available"

        # If we have pricing from pricing pages
        if valid_pricing:
            # If main pricing also has good info, combine
            if main_pricing not in ["Not found on main page", "Not available", "Unknown"]:
                return f"{main_pricing} | {' | '.join(valid_pricing)}"
            else:
                return " | ".join(valid_pricing)

        return "Pricing information not available"
