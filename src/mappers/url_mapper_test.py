"""Tests for URL mapper functions."""

from src.mappers.url_mapper import normalize_pricing_urls


class TestNormalizePricingUrls:
    """Tests for normalize_pricing_urls function."""

    def test_absolute_urls_unchanged(self) -> None:
        """Absolute URLs are preserved."""
        # Arrange
        urls = ["https://example.com/pricing", "http://example.com/plans"]
        base_url = "https://other.com"

        # Act
        result = normalize_pricing_urls(urls, base_url)

        # Assert
        assert result == urls

    def test_relative_urls_resolved(self) -> None:
        """Relative URLs are resolved against base URL."""
        # Arrange
        urls = ["/pricing", "/plans"]
        base_url = "https://example.com"

        # Act
        result = normalize_pricing_urls(urls, base_url)

        # Assert
        assert result == ["https://example.com/pricing", "https://example.com/plans"]

    def test_base_url_trailing_slash_handled(self) -> None:
        """Base URL trailing slash is handled correctly."""
        # Arrange
        urls = ["/pricing"]
        base_url = "https://example.com/"

        # Act
        result = normalize_pricing_urls(urls, base_url)

        # Assert
        assert result == ["https://example.com/pricing"]

    def test_none_input_returns_empty(self) -> None:
        """None input returns empty list."""
        # Arrange / Act
        result = normalize_pricing_urls(None, "https://example.com")

        # Assert
        assert result == []

    def test_non_list_input_returns_empty(self) -> None:
        """Non-list input returns empty list."""
        # Arrange / Act
        result = normalize_pricing_urls(
            "not a list",  # type: ignore[arg-type]
            "https://example.com",
        )

        # Assert
        assert result == []

    def test_limits_to_max_urls(self) -> None:
        """Limits output to max_urls parameter."""
        # Arrange
        urls = [f"https://example.com/page{i}" for i in range(10)]

        # Act
        result = normalize_pricing_urls(urls, "https://example.com", max_urls=3)

        # Assert
        assert len(result) == 3

    def test_filters_invalid_urls(self) -> None:
        """Filters out URLs without valid scheme or leading slash."""
        # Arrange
        urls = ["https://valid.com", "/relative", "invalid-url", "ftp://other.com"]
        base_url = "https://example.com"

        # Act
        result = normalize_pricing_urls(urls, base_url)

        # Assert
        assert result == ["https://valid.com", "https://example.com/relative"]

    def test_empty_list_returns_empty(self) -> None:
        """Empty list input returns empty list."""
        # Arrange / Act
        result = normalize_pricing_urls([], "https://example.com")

        # Assert
        assert result == []
