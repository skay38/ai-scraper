"""Tests for data models."""

import pytest
from pydantic import ValidationError

from src.models import (
    BusinessType,
    CompanyExtractionData,
    PricingStatus,
    ScrapingData,
    ScrapingResult,
)


class TestCompanyExtractionData:
    """Tests for CompanyExtractionData model."""

    def test_default_values(self) -> None:
        """Model uses correct defaults when no values provided."""
        # Arrange / Act
        data = CompanyExtractionData()

        # Assert
        assert data.company_name == BusinessType.UNKNOWN.value
        assert data.company_description == ""
        assert data.business_type == BusinessType.UNKNOWN.value
        assert data.pricing == PricingStatus.NOT_FOUND_ON_MAIN_PAGE.value
        assert data.pricing_urls == []

    def test_with_all_fields(self) -> None:
        """Model accepts all fields correctly."""
        # Arrange
        pricing_urls = ["https://example.com/pricing", "https://example.com/plans"]

        # Act
        data = CompanyExtractionData(
            company_name="Acme Corp",
            company_description="A software company",
            business_type="B2B",
            pricing="$99/month",
            pricing_urls=pricing_urls,
        )

        # Assert
        assert data.company_name == "Acme Corp"
        assert data.company_description == "A software company"
        assert data.business_type == "B2B"
        assert data.pricing == "$99/month"
        assert data.pricing_urls == pricing_urls

    def test_partial_fields(self) -> None:
        """Model uses defaults for missing optional fields."""
        # Arrange / Act
        data = CompanyExtractionData(company_name="Test Co")

        # Assert
        assert data.company_name == "Test Co"
        assert data.company_description == ""
        assert data.pricing_urls == []


class TestScrapingData:
    """Tests for ScrapingData model."""

    def test_required_fields(self) -> None:
        """Model requires all mandatory fields."""
        # Arrange / Act
        data = ScrapingData(
            company_name="Test Corp",
            company_description="Testing company",
            business_type="B2C",
            pricing="Free",
        )

        # Assert
        assert data.company_name == "Test Corp"
        assert data.company_description == "Testing company"
        assert data.business_type == "B2C"
        assert data.pricing == "Free"
        assert data.pricing_urls == []

    def test_missing_required_field_raises_error(self) -> None:
        """Model raises ValidationError when required field is missing."""
        # Arrange / Act / Assert
        with pytest.raises(ValidationError):
            ScrapingData(  # type: ignore[call-arg]
                company_name="Test Corp",
                company_description="Testing company",
                # missing business_type and pricing
            )

    def test_with_pricing_urls(self) -> None:
        """Model accepts optional pricing_urls."""
        # Arrange
        urls = ["https://example.com/pricing"]

        # Act
        data = ScrapingData(
            company_name="Test Corp",
            company_description="Testing company",
            business_type="B2B",
            pricing="$50/month",
            pricing_urls=urls,
        )

        # Assert
        assert data.pricing_urls == urls


class TestScrapingResult:
    """Tests for ScrapingResult model."""

    def test_successful_result(self) -> None:
        """Model represents successful scraping result."""
        # Arrange
        scraping_data = ScrapingData(
            company_name="Test Corp",
            company_description="Testing company",
            business_type="B2B",
            pricing="$99/month",
        )

        # Act
        result = ScrapingResult(
            url="https://example.com",
            success=True,
            data=scraping_data,
        )

        # Assert
        assert result.url == "https://example.com"
        assert result.success is True
        assert result.data == scraping_data
        assert result.error is None

    def test_failed_result(self) -> None:
        """Model represents failed scraping result."""
        # Arrange / Act
        result = ScrapingResult(
            url="https://example.com",
            success=False,
            error="Connection timeout",
        )

        # Assert
        assert result.url == "https://example.com"
        assert result.success is False
        assert result.data is None
        assert result.error == "Connection timeout"

    def test_minimal_result(self) -> None:
        """Model works with only required fields."""
        # Arrange / Act
        result = ScrapingResult(url="https://example.com", success=False)

        # Assert
        assert result.url == "https://example.com"
        assert result.success is False
        assert result.data is None
        assert result.error is None

    def test_model_dump(self) -> None:
        """Model serializes to dict correctly."""
        # Arrange
        scraping_data = ScrapingData(
            company_name="Test Corp",
            company_description="Testing company",
            business_type="B2B",
            pricing="Free",
        )
        result = ScrapingResult(
            url="https://example.com",
            success=True,
            data=scraping_data,
        )

        # Act
        dumped = result.model_dump()

        # Assert
        assert dumped["url"] == "https://example.com"
        assert dumped["success"] is True
        assert dumped["data"]["company_name"] == "Test Corp"
        assert dumped["error"] is None
