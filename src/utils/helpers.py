from pathlib import Path

from src.models import ScrapingResult
from src.utils.logger import logger


def load_domains(path: Path, limit: int) -> list[str]:
    """Load domain list from CSV file.

    Args:
        path: Path to CSV file
        limit: Maximum number of domains to load

    Returns:
        List of domain strings
    """
    domains: list[str] = []
    with path.open() as file:
        for index, line in enumerate(file):
            if index >= limit:
                break
            domain = line.strip()
            if domain:
                domains.append(domain)

    return domains


def display_result(result: ScrapingResult) -> None:
    """Display a scraping result.

    Args:
        result: Scraping result to display
    """
    if result.success and result.data:
        logger.info(
            "Scraping succeeded",
            extra={"url": result.url, "pricing": result.data.pricing},
        )
    else:
        logger.warning(
            "Scraping failed",
            extra={"url": result.url, "error": result.error},
        )
