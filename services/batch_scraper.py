"""Batch scraper service for processing multiple domains."""

import asyncio
import json
from pathlib import Path
from time import time

from config import ANTHROPIC_CONCURRENCY, HTTP_CONCURRENCY
from enums import PricingStatus
from logger import logger
from models import BatchScrapingResult, ScrapingResult
from services.anthropic_client import AnthropicClient
from services.http_client import HttpClient
from services.scraper import ScraperService


class BatchScraperService:
    """Service for scraping multiple domains in parallel."""

    def __init__(self, api_key: str) -> None:
        """Initialize batch scraper service.

        Args:
            api_key: Anthropic API key
        """
        http_semaphore = asyncio.Semaphore(HTTP_CONCURRENCY)
        anthropic_semaphore = asyncio.Semaphore(ANTHROPIC_CONCURRENCY)

        self._http_client = HttpClient(semaphore=http_semaphore)
        self._anthropic_client = AnthropicClient(
            api_key=api_key, semaphore=anthropic_semaphore
        )
        self._scraper = ScraperService(
            http_client=self._http_client,
            anthropic_client=self._anthropic_client,
        )

    async def scrape_domains(self, domains: list[str]) -> BatchScrapingResult:
        """Scrape a list of domains and return aggregated results.

        Args:
            domains: List of domain URLs to scrape

        Returns:
            BatchScrapingResult with all results and statistics
        """
        logger.info(
            "Concurrency settings",
            extra={"http": HTTP_CONCURRENCY, "anthropic": ANTHROPIC_CONCURRENCY},
        )

        start_time = time()
        tasks = [self._scraper.scrape_url(domain) for domain in domains]
        raw_results = await asyncio.gather(*tasks, return_exceptions=True)
        elapsed = time() - start_time

        logger.info("Processing complete", extra={"elapsed_seconds": f"{elapsed:.2f}"})

        results = self._process_results(raw_results)
        successful = sum(1 for r in results if r.success)
        failed = len(domains) - successful
        pricing_extracted = self._count_pricing_extracted(results)

        logger.info(
            "Summary",
            extra={
                "total": len(domains),
                "successful": successful,
                "successful_pct": f"{successful / len(domains) * 100:.1f}%",
                "failed": failed,
                "failed_pct": f"{failed / len(domains) * 100:.1f}%",
                "pricing_extracted": pricing_extracted,
                "pricing_pct": f"{pricing_extracted / len(domains) * 100:.1f}%",
                "elapsed_seconds": f"{elapsed:.2f}",
                "avg_per_url": f"{elapsed / len(domains):.2f}",
            },
        )

        return BatchScrapingResult(
            results=results,
            total=len(domains),
            successful=successful,
            failed=failed,
            pricing_extracted=pricing_extracted,
            elapsed_seconds=elapsed,
        )

    def _process_results(
        self, raw_results: list[ScrapingResult | BaseException]
    ) -> list[ScrapingResult]:
        """Process raw results, filtering out exceptions.

        Args:
            raw_results: Raw results from asyncio.gather

        Returns:
            List of valid ScrapingResult objects
        """
        results: list[ScrapingResult] = []
        for result in raw_results:
            if isinstance(result, BaseException):
                logger.error("Scraping exception", extra={"error": str(result)})
            else:
                results.append(result)
        return results

    def _count_pricing_extracted(self, results: list[ScrapingResult]) -> int:
        """Count results with valid pricing information.

        Args:
            results: List of scraping results

        Returns:
            Number of results with extracted pricing
        """
        no_pricing_statuses = [
            PricingStatus.NOT_AVAILABLE,
            PricingStatus.NOT_FOUND_ON_MAIN_PAGE,
            PricingStatus.UNKNOWN,
        ]
        return sum(
            1
            for r in results
            if r.success and r.data and r.data.pricing not in no_pricing_statuses
        )

    def save_results(self, results: list[ScrapingResult], output_path: Path) -> None:
        """Save scraping results to a JSON file.

        Args:
            results: List of scraping results
            output_path: Path to output file
        """
        json_results = [result.model_dump() for result in results]
        with open(output_path, "w") as f:
            json.dump(json_results, f, indent=2)
        logger.info("Results saved", extra={"file": str(output_path)})
