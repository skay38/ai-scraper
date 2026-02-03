"""URL transformation functions."""

from urllib.parse import urljoin

from src.utils import MAX_PRICING_URLS


def normalize_pricing_urls(
    pricing_urls: list[str] | None, base_url: str, max_urls: int = MAX_PRICING_URLS
) -> list[str]:
    """Normalize pricing URLs to absolute URLs.

    Args:
        pricing_urls: Raw pricing URLs from extraction
        base_url: Base URL for resolving relative paths
        max_urls: Maximum number of URLs to return

    Returns:
        List of normalized absolute URLs
    """
    if not pricing_urls or not isinstance(pricing_urls, list):
        return []

    normalized: list[str] = []
    for url in pricing_urls:
        if url.startswith(("http://", "https://")):
            normalized.append(url)
        elif url.startswith("/"):
            normalized.append(urljoin(base_url, url))

    return normalized[:max_urls]
