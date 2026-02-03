"""Tests for response mapper functions."""

import pytest

from src.mappers.response_mapper import parse_company_response
from src.models import BusinessType, PricingStatus
from src.utils import JsonParseError


class TestParseCompanyResponse:
    """Tests for parse_company_response function."""

    def test_valid_json_response(self) -> None:
        """Parses valid JSON response correctly."""
        # Arrange
        response = """{
            "company_name": "Acme Corp",
            "company_description": "A software company",
            "business_type": "B2B",
            "pricing": "$99/month",
            "pricing_urls": ["https://acme.com/pricing"]
        }"""
        url = "https://acme.com"

        # Act
        data = parse_company_response(response, url)

        # Assert
        assert data.company_name == "Acme Corp"
        assert data.company_description == "A software company"
        assert data.business_type == "B2B"
        assert data.pricing == "$99/month"
        assert data.pricing_urls == ["https://acme.com/pricing"]

    def test_json_with_surrounding_text(self) -> None:
        """Extracts JSON from response with surrounding text."""
        # Arrange
        response = """Here is the data:
        {"company_name": "Test Co", "company_description": "Test", "business_type": "B2C", "pricing": "Free", "pricing_urls": []}
        That's all."""
        url = "https://test.com"

        # Act
        data = parse_company_response(response, url)

        # Assert
        assert data.company_name == "Test Co"

    def test_missing_fields_use_defaults(self) -> None:
        """Missing fields use default values."""
        # Arrange
        response = '{"company_name": "Test"}'
        url = "https://test.com"

        # Act
        data = parse_company_response(response, url)

        # Assert
        assert data.company_name == "Test"
        assert data.company_description == BusinessType.UNKNOWN.value
        assert data.pricing == PricingStatus.NOT_FOUND_ON_MAIN_PAGE.value

    def test_no_json_raises_error(self) -> None:
        """Raises JsonParseError when no JSON found."""
        # Arrange
        response = "This response contains no JSON"
        url = "https://test.com"

        # Act / Assert
        with pytest.raises(JsonParseError) as exc_info:
            parse_company_response(response, url)

        assert "No JSON found" in str(exc_info.value)

    def test_invalid_json_raises_error(self) -> None:
        """Raises JsonParseError for invalid JSON."""
        # Arrange
        response = '{"company_name": "Test", invalid}'
        url = "https://test.com"

        # Act / Assert
        with pytest.raises(JsonParseError) as exc_info:
            parse_company_response(response, url)

        assert "Failed to parse JSON" in str(exc_info.value)

    def test_normalizes_relative_pricing_urls(self) -> None:
        """Normalizes relative pricing URLs."""
        # Arrange
        response = '{"company_name": "Test", "pricing_urls": ["/pricing", "/plans"]}'
        url = "https://example.com"

        # Act
        data = parse_company_response(response, url)

        # Assert
        assert data.pricing_urls == [
            "https://example.com/pricing",
            "https://example.com/plans",
        ]

    def test_empty_pricing_urls(self) -> None:
        """Handles empty pricing_urls array."""
        # Arrange
        response = '{"company_name": "Test", "pricing_urls": []}'
        url = "https://test.com"

        # Act
        data = parse_company_response(response, url)

        # Assert
        assert data.pricing_urls == []
