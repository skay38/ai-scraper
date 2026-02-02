"""Tests for Anthropic client."""

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from anthropic import APIError, RateLimitError
from anthropic.types import TextBlock

from models import BusinessType, PricingStatus
from utils import ApiResponseError, JsonParseError, RateLimitExceededError
from services.anthropic_client import AnthropicClient


@pytest.fixture
def anthropic_client() -> AnthropicClient:
    """Create Anthropic client with test configuration."""
    return AnthropicClient(api_key="test-api-key", semaphore=asyncio.Semaphore(1))


class TestAnthropicClientInit:
    """Tests for AnthropicClient initialization."""

    def test_creates_client_with_api_key(self) -> None:
        """Client initializes with provided API key."""
        # Arrange / Act
        client = AnthropicClient(api_key="test-key")

        # Assert
        assert client.client is not None
        assert client.semaphore is not None

    def test_uses_custom_semaphore(self) -> None:
        """Client uses provided semaphore."""
        # Arrange
        semaphore = asyncio.Semaphore(5)

        # Act
        client = AnthropicClient(api_key="test-key", semaphore=semaphore)

        # Assert
        assert client.semaphore is semaphore


class TestCleanHtml:
    """Tests for HTML cleaning functionality."""

    def test_removes_script_tags(self, anthropic_client: AnthropicClient) -> None:
        """Removes script tags from HTML."""
        # Arrange
        html = "<html><head><script>alert('test')</script></head><body>Content</body></html>"

        # Act
        result = anthropic_client._clean_html(html)

        # Assert
        assert "alert" not in result
        assert "Content" in result

    def test_removes_style_tags(self, anthropic_client: AnthropicClient) -> None:
        """Removes style tags from HTML."""
        # Arrange
        html = "<html><head><style>.test{color:red}</style></head><body>Content</body></html>"

        # Act
        result = anthropic_client._clean_html(html)

        # Assert
        assert "color:red" not in result
        assert "Content" in result

    def test_removes_noscript_tags(self, anthropic_client: AnthropicClient) -> None:
        """Removes noscript tags from HTML."""
        # Arrange
        html = "<html><body><noscript>Enable JS</noscript>Content</body></html>"

        # Act
        result = anthropic_client._clean_html(html)

        # Assert
        assert "Enable JS" not in result
        assert "Content" in result

    def test_preserves_text_content(self, anthropic_client: AnthropicClient) -> None:
        """Preserves regular text content."""
        # Arrange
        html = "<html><body><h1>Title</h1><p>Paragraph text</p></body></html>"

        # Act
        result = anthropic_client._clean_html(html)

        # Assert
        assert "Title" in result
        assert "Paragraph text" in result


class TestNormalizePricingUrls:
    """Tests for URL normalization."""

    def test_absolute_urls_unchanged(self, anthropic_client: AnthropicClient) -> None:
        """Absolute URLs are preserved."""
        # Arrange
        urls = ["https://example.com/pricing", "http://example.com/plans"]
        base_url = "https://other.com"

        # Act
        result = anthropic_client._normalize_pricing_urls(urls, base_url)

        # Assert
        assert result == urls

    def test_relative_urls_resolved(self, anthropic_client: AnthropicClient) -> None:
        """Relative URLs are resolved against base URL."""
        # Arrange
        urls = ["/pricing", "/plans"]
        base_url = "https://example.com"

        # Act
        result = anthropic_client._normalize_pricing_urls(urls, base_url)

        # Assert
        assert result == ["https://example.com/pricing", "https://example.com/plans"]

    def test_base_url_trailing_slash_handled(
        self, anthropic_client: AnthropicClient
    ) -> None:
        """Base URL trailing slash is handled correctly."""
        # Arrange
        urls = ["/pricing"]
        base_url = "https://example.com/"

        # Act
        result = anthropic_client._normalize_pricing_urls(urls, base_url)

        # Assert
        assert result == ["https://example.com/pricing"]

    def test_none_input_returns_empty(self, anthropic_client: AnthropicClient) -> None:
        """None input returns empty list."""
        # Arrange / Act
        result = anthropic_client._normalize_pricing_urls(None, "https://example.com")

        # Assert
        assert result == []

    def test_non_list_input_returns_empty(
        self, anthropic_client: AnthropicClient
    ) -> None:
        """Non-list input returns empty list."""
        # Arrange / Act
        result = anthropic_client._normalize_pricing_urls(
            "not a list",  # type: ignore[arg-type]
            "https://example.com",
        )

        # Assert
        assert result == []

    def test_limits_to_max_pricing_urls(
        self, anthropic_client: AnthropicClient
    ) -> None:
        """Limits output to MAX_PRICING_URLS."""
        # Arrange
        urls = [f"https://example.com/page{i}" for i in range(10)]

        # Act
        with patch("services.anthropic_client.MAX_PRICING_URLS", 3):
            result = anthropic_client._normalize_pricing_urls(
                urls, "https://example.com"
            )

        # Assert
        assert len(result) == 3

    def test_filters_invalid_urls(self, anthropic_client: AnthropicClient) -> None:
        """Filters out URLs without valid scheme or leading slash."""
        # Arrange
        urls = ["https://valid.com", "/relative", "invalid-url", "ftp://other.com"]
        base_url = "https://example.com"

        # Act
        result = anthropic_client._normalize_pricing_urls(urls, base_url)

        # Assert
        assert result == ["https://valid.com", "https://example.com/relative"]


class TestParseCompanyResponse:
    """Tests for company response parsing."""

    def test_valid_json_response(self, anthropic_client: AnthropicClient) -> None:
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
        success, data, error = anthropic_client._parse_company_response(response, url)

        # Assert
        assert success is True
        assert data is not None
        assert data.company_name == "Acme Corp"
        assert data.company_description == "A software company"
        assert data.business_type == "B2B"
        assert data.pricing == "$99/month"
        assert data.pricing_urls == ["https://acme.com/pricing"]
        assert error is None

    def test_json_with_surrounding_text(
        self, anthropic_client: AnthropicClient
    ) -> None:
        """Extracts JSON from response with surrounding text."""
        # Arrange
        response = """Here is the data:
        {"company_name": "Test Co", "company_description": "Test", "business_type": "B2C", "pricing": "Free", "pricing_urls": []}
        That's all."""
        url = "https://test.com"

        # Act
        success, data, error = anthropic_client._parse_company_response(response, url)

        # Assert
        assert success is True
        assert data is not None
        assert data.company_name == "Test Co"

    def test_missing_fields_use_defaults(
        self, anthropic_client: AnthropicClient
    ) -> None:
        """Missing fields use default values."""
        # Arrange
        response = '{"company_name": "Test"}'
        url = "https://test.com"

        # Act
        success, data, error = anthropic_client._parse_company_response(response, url)

        # Assert
        assert success is True
        assert data is not None
        assert data.company_name == "Test"
        assert data.company_description == BusinessType.UNKNOWN.value
        assert data.pricing == PricingStatus.NOT_FOUND_ON_MAIN_PAGE.value

    def test_no_json_raises_error(self, anthropic_client: AnthropicClient) -> None:
        """Raises JsonParseError when no JSON found."""
        # Arrange
        response = "This response contains no JSON"
        url = "https://test.com"

        # Act / Assert
        with pytest.raises(JsonParseError) as exc_info:
            anthropic_client._parse_company_response(response, url)

        assert "No JSON found" in str(exc_info.value)

    def test_invalid_json_raises_error(self, anthropic_client: AnthropicClient) -> None:
        """Raises JsonParseError for invalid JSON."""
        # Arrange
        response = '{"company_name": "Test", invalid}'
        url = "https://test.com"

        # Act / Assert
        with pytest.raises(JsonParseError) as exc_info:
            anthropic_client._parse_company_response(response, url)

        assert "Failed to parse JSON" in str(exc_info.value)


class TestCallApi:
    """Tests for API call functionality."""

    @pytest.mark.asyncio
    async def test_successful_api_call(self, anthropic_client: AnthropicClient) -> None:
        """Returns response text on successful call."""
        # Arrange
        mock_text_block = MagicMock(spec=TextBlock)
        mock_text_block.text = "API response"

        mock_response = MagicMock()
        mock_response.content = [mock_text_block]

        anthropic_client.client.messages.create = AsyncMock(return_value=mock_response)

        # Act
        success, response, error_type = await anthropic_client._call_api("test prompt")

        # Assert
        assert success is True
        assert response == "API response"
        assert error_type is None

    @pytest.mark.asyncio
    async def test_unexpected_response_type(
        self, anthropic_client: AnthropicClient
    ) -> None:
        """Returns error for non-TextBlock response."""
        # Arrange
        mock_response = MagicMock()
        mock_response.content = [MagicMock()]  # Not a TextBlock

        anthropic_client.client.messages.create = AsyncMock(return_value=mock_response)

        # Act
        success, response, error_type = await anthropic_client._call_api("test prompt")

        # Assert
        assert success is False
        assert "Unexpected response type" in response
        assert error_type == "invalid_response"

    @pytest.mark.asyncio
    async def test_rate_limit_retry_then_success(
        self, anthropic_client: AnthropicClient
    ) -> None:
        """Retries on rate limit and succeeds."""
        # Arrange
        mock_text_block = MagicMock(spec=TextBlock)
        mock_text_block.text = "Success after retry"

        mock_success_response = MagicMock()
        mock_success_response.content = [mock_text_block]

        anthropic_client.client.messages.create = AsyncMock(
            side_effect=[
                RateLimitError(
                    "rate limited",
                    response=MagicMock(status_code=429),
                    body=None,
                ),
                mock_success_response,
            ]
        )

        # Act
        with patch("services.anthropic_client.asyncio.sleep", new_callable=AsyncMock):
            success, response, error_type = await anthropic_client._call_api(
                "test prompt"
            )

        # Assert
        assert success is True
        assert response == "Success after retry"

    @pytest.mark.asyncio
    async def test_rate_limit_exhausted_raises(
        self, anthropic_client: AnthropicClient
    ) -> None:
        """Raises RateLimitExceededError after max retries."""
        # Arrange
        anthropic_client.client.messages.create = AsyncMock(
            side_effect=RateLimitError(
                "rate limited",
                response=MagicMock(status_code=429),
                body=None,
            )
        )

        # Act / Assert
        with (
            patch("services.anthropic_client.asyncio.sleep", new_callable=AsyncMock),
            pytest.raises(RateLimitExceededError),
        ):
            await anthropic_client._call_api("test prompt", max_retries=2)

    @pytest.mark.asyncio
    async def test_api_error_raises(self, anthropic_client: AnthropicClient) -> None:
        """Raises ApiResponseError on API error."""
        # Arrange
        anthropic_client.client.messages.create = AsyncMock(
            side_effect=APIError(
                "API error",
                request=MagicMock(),
                body=None,
            )
        )

        # Act / Assert
        with pytest.raises(ApiResponseError):
            await anthropic_client._call_api("test prompt")


class TestExtractCompanyData:
    """Tests for company data extraction."""

    @pytest.mark.asyncio
    async def test_successful_extraction(
        self, anthropic_client: AnthropicClient
    ) -> None:
        """Returns extracted company data on success."""
        # Arrange
        json_response = """{
            "company_name": "Test Corp",
            "company_description": "A test company",
            "business_type": "B2B",
            "pricing": "$50/month",
            "pricing_urls": []
        }"""

        mock_text_block = MagicMock(spec=TextBlock)
        mock_text_block.text = json_response

        mock_response = MagicMock()
        mock_response.content = [mock_text_block]

        anthropic_client.client.messages.create = AsyncMock(return_value=mock_response)

        # Act
        success, data, error = await anthropic_client.extract_company_data(
            "<html><body>Test</body></html>", "https://test.com"
        )

        # Assert
        assert success is True
        assert data is not None
        assert data.company_name == "Test Corp"
        assert error is None

    @pytest.mark.asyncio
    async def test_api_failure_returns_error(
        self, anthropic_client: AnthropicClient
    ) -> None:
        """Returns error tuple on API failure."""
        # Arrange
        anthropic_client.client.messages.create = AsyncMock(
            side_effect=APIError(
                "API error",
                request=MagicMock(),
                body=None,
            )
        )

        # Act
        success, data, error = await anthropic_client.extract_company_data(
            "<html></html>", "https://test.com"
        )

        # Assert
        assert success is False
        assert data is None
        assert error is not None


class TestExtractPricing:
    """Tests for pricing extraction."""

    @pytest.mark.asyncio
    async def test_successful_pricing_extraction(
        self, anthropic_client: AnthropicClient
    ) -> None:
        """Returns pricing summary on success."""
        # Arrange
        mock_text_block = MagicMock(spec=TextBlock)
        mock_text_block.text = "Basic: $10/month, Pro: $25/month"

        mock_response = MagicMock()
        mock_response.content = [mock_text_block]

        anthropic_client.client.messages.create = AsyncMock(return_value=mock_response)

        # Act
        success, pricing, error = await anthropic_client.extract_pricing(
            "<html><body>Pricing page</body></html>"
        )

        # Assert
        assert success is True
        assert pricing == "Basic: $10/month, Pro: $25/month"
        assert error is None

    @pytest.mark.asyncio
    async def test_pricing_extraction_strips_whitespace(
        self, anthropic_client: AnthropicClient
    ) -> None:
        """Strips whitespace from pricing response."""
        # Arrange
        mock_text_block = MagicMock(spec=TextBlock)
        mock_text_block.text = "  Pricing info  \n"

        mock_response = MagicMock()
        mock_response.content = [mock_text_block]

        anthropic_client.client.messages.create = AsyncMock(return_value=mock_response)

        # Act
        success, pricing, error = await anthropic_client.extract_pricing(
            "<html></html>"
        )

        # Assert
        assert success is True
        assert pricing == "Pricing info"

    @pytest.mark.asyncio
    async def test_pricing_api_failure(self, anthropic_client: AnthropicClient) -> None:
        """Returns error on API failure."""
        # Arrange
        anthropic_client.client.messages.create = AsyncMock(
            side_effect=APIError(
                "API error",
                request=MagicMock(),
                body=None,
            )
        )

        # Act
        success, pricing, error = await anthropic_client.extract_pricing(
            "<html></html>"
        )

        # Assert
        assert success is False
        assert pricing == "Failed to extract pricing"
        assert error is not None
