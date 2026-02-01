import asyncio
import json
import os
from pathlib import Path
from time import time

from dotenv import load_dotenv

from config import ANTHROPIC_CONCURRENCY, DEFAULT_IMPORT_LIMIT, HTTP_CONCURRENCY
from enums import PricingStatus
from logger import logger
from models import ScrapingResult
from services.anthropic_client import AnthropicClient
from services.http_client import HttpClient
from services.scraper import ScraperService
from utils import display_result, load_domains

load_dotenv()

DOMAIN_LIST_PATH = Path("data", "domains.csv")


async def main() -> None:
    """Main entry point for the scraper."""
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        logger.error("ANTHROPIC_API_KEY not found in .env file")
        return

    domains = load_domains(DOMAIN_LIST_PATH, DEFAULT_IMPORT_LIMIT)
    logger.info("Loaded domains", extra={"count": len(domains)})
    logger.info(
        "Concurrency settings",
        extra={"http": HTTP_CONCURRENCY, "anthropic": ANTHROPIC_CONCURRENCY},
    )

    http_semaphore = asyncio.Semaphore(HTTP_CONCURRENCY)
    anthropic_semaphore = asyncio.Semaphore(ANTHROPIC_CONCURRENCY)

    http_client = HttpClient(semaphore=http_semaphore)
    anthropic_client = AnthropicClient(api_key=api_key, semaphore=anthropic_semaphore)
    scraper = ScraperService(
        http_client=http_client,
        anthropic_client=anthropic_client,
    )

    start_time = time()
    tasks = [scraper.scrape_url(domain) for domain in domains]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    elapsed = time() - start_time

    logger.info("Processing complete", extra={"elapsed_seconds": f"{elapsed:.2f}"})

    scraping_results: list[ScrapingResult] = []
    for result in results:
        if isinstance(result, BaseException):
            logger.error("Scraping exception", extra={"error": str(result)})
        else:
            scraping_results.append(result)
            display_result(result)

    successful = sum(1 for r in scraping_results if r.success)
    failed = len(results) - successful

    pricing_extracted = sum(
        1
        for r in scraping_results
        if r.success
        and r.data
        and r.data.pricing
        and r.data.pricing
        not in [
            PricingStatus.NOT_AVAILABLE,
            PricingStatus.NOT_FOUND_ON_MAIN_PAGE,
            PricingStatus.UNKNOWN,
        ]
    )

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

    json_results: list[dict] = []
    for result in results:
        if isinstance(result, ScrapingResult):
            json_results.append(result.model_dump())

    with open("res.json", "w") as f:
        json.dump(json_results, f, indent=2)

    logger.info("Results saved", extra={"file": "res.json"})


if __name__ == "__main__":
    asyncio.run(main())
