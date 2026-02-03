"""HTML transformation functions."""

from bs4 import BeautifulSoup


def clean_html(html: str) -> str:
    """Clean HTML by removing scripts, styles, and noscript tags.

    Args:
        html: Raw HTML content

    Returns:
        Cleaned HTML with prettified output
    """
    soup = BeautifulSoup(html, "html.parser")

    for script in soup(["script", "style", "noscript"]):
        script.decompose()

    return soup.prettify()
