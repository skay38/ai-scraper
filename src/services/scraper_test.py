"""Tests for scraper service."""

from unittest.mock import AsyncMock, MagicMock

import pytest

from src.models import CompanyExtractionData, PricingStatus
from src.services.scraper import ScraperService


@pytest.fixture
def mock_http_client() -> MagicMock:
    """Create mock HTTP client."""
    return MagicMock()


@pytest.fixture
def mock_extraction_service() -> MagicMock:
    """Create mock extraction service."""
    return MagicMock()


@pytest.fixture
def scraper(
    mock_http_client: MagicMock, mock_extraction_service: MagicMock
) -> ScraperService:
    """Create scraper service with mocked dependencies."""
    return ScraperService(
        http_client=mock_http_client,
        extraction_service=mock_extraction_service,
    )


class TestScraperServiceInit:
    """Tests for ScraperService initialization."""

    def test_stores_clients(
        self, mock_http_client: MagicMock, mock_extraction_service: MagicMock
    ) -> None:
        """Stores provided clients."""
        # Act
        service = ScraperService(
            http_client=mock_http_client,
            extraction_service=mock_extraction_service,
        )

        # Assert
        assert service.http_client is mock_http_client
        assert service.extraction_service is mock_extraction_service


class TestScraperServiceScrapeUrl:
    """Tests for ScraperService.scrape_url method."""

    @pytest.mark.asyncio
    async def test_returns_error_when_http_fails(
        self, scraper: ScraperService, mock_http_client: MagicMock
    ) -> None:
        """Returns error result when HTTP request fails."""
        # Arrange
        mock_http_client.get = AsyncMock(
            return_value=(False, "Connection timeout", "connect_timeout")
        )

        # Act
        result = await scraper.scrape_url("https://example.com")

        # Assert
        assert result.success is False
        assert result.url == "https://example.com"
        assert result.error == "Connection timeout"

    @pytest.mark.asyncio
    async def test_returns_error_when_extraction_fails(
        self,
        scraper: ScraperService,
        mock_http_client: MagicMock,
        mock_extraction_service: MagicMock,
    ) -> None:
        """Returns error result when AI extraction fails."""
        # Arrange
        mock_http_client.get = AsyncMock(
            return_value=(True, "<html>content</html>", None)
        )
        mock_extraction_service.extract_company_data = AsyncMock(
            return_value=(False, None, "API error")
        )

        # Act
        result = await scraper.scrape_url("https://example.com")

        # Assert
        assert result.success is False
        assert result.error is not None
        assert "AI extraction failed" in result.error

    @pytest.mark.asyncio
    async def test_successful_scrape_without_pricing_urls(
        self,
        scraper: ScraperService,
        mock_http_client: MagicMock,
        mock_extraction_service: MagicMock,
    ) -> None:
        """Returns success when scraping completes without pricing URLs."""
        # Arrange
        mock_http_client.get = AsyncMock(
            return_value=(True, "<html>content</html>", None)
        )
        extracted_data = CompanyExtractionData(
            company_name="Test Co",
            company_description="A test company",
            business_type="B2B",
            pricing="$99/month",
            pricing_urls=[],
        )
        mock_extraction_service.extract_company_data = AsyncMock(
            return_value=(True, extracted_data, None)
        )

        # Act
        result = await scraper.scrape_url("https://example.com")

        # Assert
        assert result.success is True
        assert result.data is not None
        assert result.data.company_name == "Test Co"
        assert result.data.pricing == "$99/month"

    @pytest.mark.asyncio
    async def test_fetches_pricing_pages_and_aggregates(
        self,
        scraper: ScraperService,
        mock_http_client: MagicMock,
        mock_extraction_service: MagicMock,
    ) -> None:
        """Fetches pricing pages and aggregates pricing info."""
        # Arrange
        mock_http_client.get = AsyncMock(
            side_effect=[
                (True, "<html>main</html>", None),
                (True, "<html>pricing</html>", None),
            ]
        )
        extracted_data = CompanyExtractionData(
            company_name="Test Co",
            company_description="A test company",
            business_type="B2B",
            pricing=PricingStatus.NOT_FOUND_ON_MAIN_PAGE,
            pricing_urls=["https://example.com/pricing"],
        )
        mock_extraction_service.extract_company_data = AsyncMock(
            return_value=(True, extracted_data, None)
        )
        mock_extraction_service.extract_pricing = AsyncMock(
            return_value=(True, "$49/month", None)
        )

        # Act
        result = await scraper.scrape_url("https://example.com")

        # Assert
        assert result.success is True
        assert result.data is not None
        assert result.data.pricing == "$49/month"


class TestScraperServiceAggregatePricing:
    """Tests for ScraperService._aggregate_pricing method."""

    def test_returns_not_available_when_no_pricing(
        self, scraper: ScraperService
    ) -> None:
        """Returns NOT_AVAILABLE when no pricing found."""
        # Act
        result = scraper._aggregate_pricing(PricingStatus.NOT_FOUND_ON_MAIN_PAGE, [])

        # Assert
        assert result == PricingStatus.NOT_AVAILABLE

    def test_returns_main_pricing_when_no_page_results(
        self, scraper: ScraperService
    ) -> None:
        """Returns main pricing when pricing pages have no results."""
        # Act
        result = scraper._aggregate_pricing("$99/month", [None, None])

        # Assert
        assert result == "$99/month"

    def test_returns_page_pricing_when_main_has_none(
        self, scraper: ScraperService
    ) -> None:
        """Returns pricing page results when main has no pricing."""
        # Act
        result = scraper._aggregate_pricing(
            PricingStatus.NOT_FOUND_ON_MAIN_PAGE, ["$49/month"]
        )

        # Assert
        assert result == "$49/month"

    def test_combines_main_and_page_pricing(self, scraper: ScraperService) -> None:
        """Combines main and page pricing with separator."""
        # Act
        result = scraper._aggregate_pricing("$99/month", ["$49/month"])

        # Assert
        assert result == "$99/month | $49/month"

    def test_joins_multiple_page_results(self, scraper: ScraperService) -> None:
        """Joins multiple pricing page results."""
        # Act
        result = scraper._aggregate_pricing(
            PricingStatus.NOT_AVAILABLE, ["$49/month", "$99/month"]
        )

        # Assert
        assert result == "$49/month | $99/month"

    def test_filters_out_exceptions(self, scraper: ScraperService) -> None:
        """Filters out exception results from pricing pages."""
        # Act
        result = scraper._aggregate_pricing(
            PricingStatus.NOT_AVAILABLE, ["$49/month", ValueError("error"), None]
        )

        # Assert
        assert result == "$49/month"

    def test_filters_out_empty_strings(self, scraper: ScraperService) -> None:
        """Filters out empty string results."""
        # Act
        result = scraper._aggregate_pricing(
            PricingStatus.NOT_AVAILABLE, ["$49/month", "", "  "]
        )

        # Assert
        assert result == "$49/month"


class TestScraperServiceFetchAndExtractPricing:
    """Tests for ScraperService._fetch_and_extract_pricing method."""

    @pytest.mark.asyncio
    async def test_returns_none_when_http_fails(
        self,
        scraper: ScraperService,
        mock_http_client: MagicMock,
    ) -> None:
        """Returns None when HTTP request fails."""
        # Arrange
        mock_http_client.get = AsyncMock(
            return_value=(False, "Connection timeout", "connect_timeout")
        )

        # Act
        result = await scraper._fetch_and_extract_pricing("https://example.com/pricing")

        # Assert
        assert result is None

    @pytest.mark.asyncio
    async def test_returns_none_when_no_pricing_info(
        self,
        scraper: ScraperService,
        mock_http_client: MagicMock,
        mock_extraction_service: MagicMock,
    ) -> None:
        """Returns None when page has no pricing info."""
        # Arrange
        mock_http_client.get = AsyncMock(
            return_value=(True, "<html>content</html>", None)
        )
        mock_extraction_service.extract_pricing = AsyncMock(
            return_value=(True, PricingStatus.NO_PRICING_INFO, None)
        )

        # Act
        result = await scraper._fetch_and_extract_pricing("https://example.com/pricing")

        # Assert
        assert result is None

    @pytest.mark.asyncio
    async def test_returns_pricing_summary(
        self,
        scraper: ScraperService,
        mock_http_client: MagicMock,
        mock_extraction_service: MagicMock,
    ) -> None:
        """Returns pricing summary when extraction succeeds."""
        # Arrange
        mock_http_client.get = AsyncMock(
            return_value=(True, "<html>content</html>", None)
        )
        mock_extraction_service.extract_pricing = AsyncMock(
            return_value=(True, "$99/month", None)
        )

        # Act
        result = await scraper._fetch_and_extract_pricing("https://example.com/pricing")

        # Assert
        assert result == "$99/month"


class TestScraperServiceFetchPricingPages:
    """Tests for ScraperService._fetch_pricing_pages method."""

    @pytest.mark.asyncio
    async def test_returns_empty_list_when_no_urls(
        self, scraper: ScraperService
    ) -> None:
        """Returns empty list when no pricing URLs provided."""
        # Act
        result = await scraper._fetch_pricing_pages([])

        # Assert
        assert result == []

    @pytest.mark.asyncio
    async def test_limits_urls_to_max(
        self,
        scraper: ScraperService,
        mock_http_client: MagicMock,
        mock_extraction_service: MagicMock,
    ) -> None:
        """Limits pricing URLs to MAX_PRICING_URLS."""
        # Arrange
        mock_http_client.get = AsyncMock(
            return_value=(True, "<html>content</html>", None)
        )
        mock_extraction_service.extract_pricing = AsyncMock(
            return_value=(True, "$99/month", None)
        )
        urls = [f"https://example.com/pricing{i}" for i in range(10)]

        # Act
        result = await scraper._fetch_pricing_pages(urls)

        # Assert - MAX_PRICING_URLS is 3
        assert len(result) == 3
