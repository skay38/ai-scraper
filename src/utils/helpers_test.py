"""Tests for utility functions."""

from pathlib import Path
from unittest.mock import patch

import pytest

from src.models import ScrapingData, ScrapingResult
from src.utils import display_result, load_domains


class TestLoadDomains:
    """Tests for load_domains function."""

    def test_loads_domains_from_file(self, tmp_path: Path) -> None:
        """Loads domains from CSV file."""
        # Arrange
        csv_file = tmp_path / "domains.csv"
        csv_file.write_text("example.com\ntest.com\nfoo.com\n")

        # Act
        domains = load_domains(csv_file, limit=10)

        # Assert
        assert domains == ["example.com", "test.com", "foo.com"]

    def test_respects_limit(self, tmp_path: Path) -> None:
        """Stops loading after reaching limit."""
        # Arrange
        csv_file = tmp_path / "domains.csv"
        csv_file.write_text("a.com\nb.com\nc.com\nd.com\ne.com\n")

        # Act
        domains = load_domains(csv_file, limit=3)

        # Assert
        assert domains == ["a.com", "b.com", "c.com"]

    def test_skips_empty_lines(self, tmp_path: Path) -> None:
        """Skips empty lines in file."""
        # Arrange
        csv_file = tmp_path / "domains.csv"
        csv_file.write_text("a.com\n\nb.com\n  \nc.com\n")

        # Act
        domains = load_domains(csv_file, limit=10)

        # Assert
        assert domains == ["a.com", "b.com", "c.com"]

    def test_strips_whitespace(self, tmp_path: Path) -> None:
        """Strips whitespace from domain names."""
        # Arrange
        csv_file = tmp_path / "domains.csv"
        csv_file.write_text("  example.com  \n  test.com\n")

        # Act
        domains = load_domains(csv_file, limit=10)

        # Assert
        assert domains == ["example.com", "test.com"]

    def test_empty_file_returns_empty_list(self, tmp_path: Path) -> None:
        """Returns empty list for empty file."""
        # Arrange
        csv_file = tmp_path / "domains.csv"
        csv_file.write_text("")

        # Act
        domains = load_domains(csv_file, limit=10)

        # Assert
        assert domains == []

    def test_file_not_found_raises_error(self, tmp_path: Path) -> None:
        """Raises error when file does not exist."""
        # Arrange
        csv_file = tmp_path / "nonexistent.csv"

        # Act / Assert
        with pytest.raises(FileNotFoundError):
            load_domains(csv_file, limit=10)


class TestDisplayResult:
    """Tests for display_result function."""

    def test_logs_success_with_pricing(self) -> None:
        """Logs info for successful result with pricing."""
        # Arrange
        data = ScrapingData(
            company_name="Test Co",
            company_description="A test company",
            business_type="B2B",
            pricing="$99/month",
            pricing_urls=[],
        )
        result = ScrapingResult(url="https://test.com", success=True, data=data)

        # Act / Assert
        with patch("src.utils.helpers.logger") as mock_logger:
            display_result(result)
            mock_logger.info.assert_called_once()
            call_kwargs = mock_logger.info.call_args
            assert call_kwargs[1]["extra"]["url"] == "https://test.com"
            assert call_kwargs[1]["extra"]["pricing"] == "$99/month"

    def test_logs_warning_for_failed_result(self) -> None:
        """Logs warning for failed result."""
        # Arrange
        result = ScrapingResult(
            url="https://fail.com", success=False, error="Connection timeout"
        )

        # Act / Assert
        with patch("src.utils.helpers.logger") as mock_logger:
            display_result(result)
            mock_logger.warning.assert_called_once()
            call_kwargs = mock_logger.warning.call_args
            assert call_kwargs[1]["extra"]["url"] == "https://fail.com"
            assert call_kwargs[1]["extra"]["error"] == "Connection timeout"

    def test_logs_warning_when_success_but_no_data(self) -> None:
        """Logs warning when success is True but data is None."""
        # Arrange
        result = ScrapingResult(url="https://test.com", success=True, data=None)

        # Act / Assert
        with patch("src.utils.helpers.logger") as mock_logger:
            display_result(result)
            mock_logger.warning.assert_called_once()
