import asyncio
import os
from pathlib import Path

from dotenv import load_dotenv

from config import DEFAULT_IMPORT_LIMIT, OUTPUT_FILE
from logger import logger
from services.batch_scraper import BatchScraperService
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

    batch_scraper = BatchScraperService(api_key=api_key)
    batch_result = await batch_scraper.scrape_domains(domains)

    for result in batch_result.results:
        display_result(result)

    batch_scraper.save_results(batch_result.results, Path(OUTPUT_FILE))


if __name__ == "__main__":
    asyncio.run(main())
