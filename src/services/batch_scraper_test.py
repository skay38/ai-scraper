"""Tests for batch scraper service."""

import json
from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest

from src.models import BatchScrapingResult, PricingStatus, ScrapingData, ScrapingResult
from src.services.batch_scraper import BatchScraperService


def create_scraping_result(
    url: str = "https://example.com",
    success: bool = True,
    pricing: str = "$10/month",
) -> ScrapingResult:
    """Factory for creating ScrapingResult test data."""
    if success:
        return ScrapingResult(
            url=url,
            success=True,
            data=ScrapingData(
                company_name="Test Company",
                company_description="A test company",
                business_type="B2B",
                pricing=pricing,
                pricing_urls=[],
            ),
        )
    return ScrapingResult(url=url, success=False, error="Scraping failed")


class TestBatchScraperServiceInit:
    """Tests for BatchScraperService initialization."""

    def test_creates_internal_clients(self) -> None:
        """Service creates HTTP and Anthropic clients."""
        # Arrange / Act
        service = BatchScraperService(api_key="test-key")

        # Assert
        assert service._http_client is not None
        assert service._anthropic_client is not None
        assert service._scraper is not None


class TestScrapeDomains:
    """Tests for BatchScraperService.scrape_domains method."""

    @pytest.mark.asyncio
    async def test_returns_batch_result_with_statistics(self) -> None:
        """Returns BatchScrapingResult with correct statistics."""
        # Arrange
        service = BatchScraperService(api_key="test-key")
        domains = ["https://example1.com", "https://example2.com"]
        mock_results = [
            create_scraping_result(url=domains[0], success=True, pricing="$10/month"),
            create_scraping_result(url=domains[1], success=False),
        ]

        service._scraper.scrape_url = AsyncMock(side_effect=mock_results)

        # Act
        result = await service.scrape_domains(domains)

        # Assert
        assert isinstance(result, BatchScrapingResult)
        assert result.total == 2
        assert result.successful == 1
        assert result.failed == 1
        assert result.elapsed_seconds >= 0

    @pytest.mark.asyncio
    async def test_handles_exceptions_from_scraper(self) -> None:
        """Filters out exceptions and continues processing."""
        # Arrange
        service = BatchScraperService(api_key="test-key")
        domains = ["https://example1.com", "https://example2.com"]
        successful_result = create_scraping_result(url=domains[1], success=True)

        async def mock_scrape(url: str) -> ScrapingResult:
            if url == domains[0]:
                raise RuntimeError("Unexpected error")
            return successful_result

        with patch.object(service._scraper, "scrape_url", side_effect=mock_scrape):
            # Act
            result = await service.scrape_domains(domains)

        # Assert
        assert len(result.results) == 1
        assert result.results[0].url == domains[1]
        assert result.failed == 1

    @pytest.mark.asyncio
    async def test_counts_pricing_extracted_correctly(self) -> None:
        """Counts only results with valid pricing."""
        # Arrange
        service = BatchScraperService(api_key="test-key")
        domains = ["https://a.com", "https://b.com", "https://c.com"]
        mock_results = [
            create_scraping_result(url=domains[0], pricing="$10/month"),
            create_scraping_result(url=domains[1], pricing=PricingStatus.NOT_AVAILABLE),
            create_scraping_result(url=domains[2], pricing="Free tier available"),
        ]

        service._scraper.scrape_url = AsyncMock(side_effect=mock_results)

        # Act
        result = await service.scrape_domains(domains)

        # Assert
        assert result.pricing_extracted == 2

    @pytest.mark.asyncio
    async def test_all_failed_results(self) -> None:
        """Handles case where all scrapes fail."""
        # Arrange
        service = BatchScraperService(api_key="test-key")
        domains = ["https://example1.com", "https://example2.com"]
        mock_results = [
            create_scraping_result(url=domains[0], success=False),
            create_scraping_result(url=domains[1], success=False),
        ]

        service._scraper.scrape_url = AsyncMock(side_effect=mock_results)

        # Act
        result = await service.scrape_domains(domains)

        # Assert
        assert result.successful == 0
        assert result.failed == 2
        assert result.pricing_extracted == 0


class TestCountPricingExtracted:
    """Tests for _count_pricing_extracted method."""

    @pytest.mark.parametrize(
        ("pricing", "expected_count"),
        [
            ("$10/month", 1),
            ("Free", 1),
            (PricingStatus.NOT_AVAILABLE, 0),
            (PricingStatus.NOT_FOUND_ON_MAIN_PAGE, 0),
            (PricingStatus.UNKNOWN, 0),
        ],
    )
    def test_counts_by_pricing_status(self, pricing: str, expected_count: int) -> None:
        """Correctly identifies valid vs invalid pricing."""
        # Arrange
        service = BatchScraperService(api_key="test-key")
        results = [create_scraping_result(pricing=pricing)]

        # Act
        count = service._count_pricing_extracted(results)

        # Assert
        assert count == expected_count

    def test_excludes_failed_results(self) -> None:
        """Does not count pricing from failed results."""
        # Arrange
        service = BatchScraperService(api_key="test-key")
        results = [create_scraping_result(success=False)]

        # Act
        count = service._count_pricing_extracted(results)

        # Assert
        assert count == 0

    def test_empty_results(self) -> None:
        """Returns zero for empty results list."""
        # Arrange
        service = BatchScraperService(api_key="test-key")

        # Act
        count = service._count_pricing_extracted([])

        # Assert
        assert count == 0


class TestProcessResults:
    """Tests for _process_results method."""

    def test_filters_out_exceptions(self) -> None:
        """Removes BaseException instances from results."""
        # Arrange
        service = BatchScraperService(api_key="test-key")
        valid_result = create_scraping_result()
        raw_results: list[ScrapingResult | BaseException] = [
            valid_result,
            RuntimeError("Error 1"),
            ValueError("Error 2"),
        ]

        # Act
        results = service._process_results(raw_results)

        # Assert
        assert len(results) == 1
        assert results[0] == valid_result

    def test_preserves_all_valid_results(self) -> None:
        """Keeps all ScrapingResult instances."""
        # Arrange
        service = BatchScraperService(api_key="test-key")
        result1 = create_scraping_result(url="https://a.com")
        result2 = create_scraping_result(url="https://b.com")
        raw_results: list[ScrapingResult | BaseException] = [result1, result2]

        # Act
        results = service._process_results(raw_results)

        # Assert
        assert len(results) == 2
        assert results[0] == result1
        assert results[1] == result2

    def test_empty_input(self) -> None:
        """Returns empty list for empty input."""
        # Arrange
        service = BatchScraperService(api_key="test-key")

        # Act
        results = service._process_results([])

        # Assert
        assert results == []


class TestSaveResults:
    """Tests for save_results method."""

    def test_saves_results_to_json_file(self, tmp_path: Path) -> None:
        """Writes results as JSON to specified path."""
        # Arrange
        service = BatchScraperService(api_key="test-key")
        results = [create_scraping_result(url="https://example.com")]
        output_path = tmp_path / "results.json"

        # Act
        service.save_results(results, output_path)

        # Assert
        assert output_path.exists()
        with open(output_path) as f:
            saved_data = json.load(f)
        assert len(saved_data) == 1
        assert saved_data[0]["url"] == "https://example.com"

    def test_saves_multiple_results(self, tmp_path: Path) -> None:
        """Saves all results to file."""
        # Arrange
        service = BatchScraperService(api_key="test-key")
        results = [
            create_scraping_result(url="https://a.com"),
            create_scraping_result(url="https://b.com"),
        ]
        output_path = tmp_path / "results.json"

        # Act
        service.save_results(results, output_path)

        # Assert
        with open(output_path) as f:
            saved_data = json.load(f)
        assert len(saved_data) == 2

    def test_saves_empty_results(self, tmp_path: Path) -> None:
        """Handles empty results list."""
        # Arrange
        service = BatchScraperService(api_key="test-key")
        output_path = tmp_path / "results.json"

        # Act
        service.save_results([], output_path)

        # Assert
        with open(output_path) as f:
            saved_data = json.load(f)
        assert saved_data == []
