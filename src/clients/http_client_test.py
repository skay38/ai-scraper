"""Tests for HTTP client."""

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from src.clients.http_client import HttpClient


@pytest.fixture
def http_client() -> HttpClient:
    """Create HTTP client with test semaphore."""
    return HttpClient(semaphore=asyncio.Semaphore(1))


class TestHttpClientInit:
    """Tests for HttpClient initialization."""

    def test_default_semaphore(self) -> None:
        """Client creates default semaphore when none provided."""
        # Arrange / Act
        client = HttpClient()

        # Assert
        assert client.semaphore is not None

    def test_custom_semaphore(self) -> None:
        """Client uses provided semaphore."""
        # Arrange
        semaphore = asyncio.Semaphore(5)

        # Act
        client = HttpClient(semaphore=semaphore)

        # Assert
        assert client.semaphore is semaphore

    def test_timeout_configuration(self) -> None:
        """Client configures timeout correctly."""
        # Arrange / Act
        client = HttpClient()

        # Assert
        assert client.timeout.connect is not None
        assert client.timeout.read is not None


class TestHttpClientGet:
    """Tests for HttpClient.get method."""

    @pytest.mark.asyncio
    async def test_successful_html_response(self, http_client: HttpClient) -> None:
        """Returns success for valid HTML response."""
        # Arrange
        mock_response = MagicMock()
        mock_response.text = "<html><body>Test</body></html>"
        mock_response.headers = {"content-type": "text/html; charset=utf-8"}
        mock_response.raise_for_status = MagicMock()

        mock_client = AsyncMock()
        mock_client.get = AsyncMock(return_value=mock_response)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)

        with patch(
            "src.clients.http_client.httpx.AsyncClient", return_value=mock_client
        ):
            # Act
            success, content, error_type = await http_client.get("https://example.com")

        # Assert
        assert success is True
        assert content == "<html><body>Test</body></html>"
        assert error_type is None

    @pytest.mark.asyncio
    async def test_prepends_https_when_missing(self, http_client: HttpClient) -> None:
        """Prepends https:// when URL has no scheme."""
        # Arrange
        mock_response = MagicMock()
        mock_response.text = "<html></html>"
        mock_response.headers = {"content-type": "text/html"}
        mock_response.raise_for_status = MagicMock()

        mock_client = AsyncMock()
        mock_client.get = AsyncMock(return_value=mock_response)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)

        with patch(
            "src.clients.http_client.httpx.AsyncClient", return_value=mock_client
        ):
            # Act
            await http_client.get("example.com")

        # Assert
        call_args = mock_client.get.call_args
        assert call_args[0][0] == "https://example.com"

    @pytest.mark.asyncio
    async def test_invalid_content_type(self, http_client: HttpClient) -> None:
        """Returns error for non-HTML content type."""
        # Arrange
        mock_response = MagicMock()
        mock_response.headers = {"content-type": "application/json"}
        mock_response.raise_for_status = MagicMock()

        mock_client = AsyncMock()
        mock_client.get = AsyncMock(return_value=mock_response)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)

        with patch(
            "src.clients.http_client.httpx.AsyncClient", return_value=mock_client
        ):
            # Act
            success, content, error_type = await http_client.get("https://example.com")

        # Assert
        assert success is False
        assert "Invalid content type" in content
        assert error_type == "invalid_content_type"

    @pytest.mark.asyncio
    async def test_connection_timeout(self, http_client: HttpClient) -> None:
        """Returns error on connection timeout after retries."""
        # Arrange
        mock_client = AsyncMock()
        mock_client.get = AsyncMock(side_effect=httpx.ConnectTimeout("timeout"))
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)

        with (
            patch(
                "src.clients.http_client.httpx.AsyncClient", return_value=mock_client
            ),
            patch("src.clients.http_client.HTTP_MAX_RETRIES", 1),
        ):
            # Act
            success, content, error_type = await http_client.get("https://example.com")

        # Assert
        assert success is False
        assert content == "Connection timeout"
        assert error_type == "connect_timeout"

    @pytest.mark.asyncio
    async def test_read_timeout(self, http_client: HttpClient) -> None:
        """Returns error on read timeout after retries."""
        # Arrange
        mock_client = AsyncMock()
        mock_client.get = AsyncMock(side_effect=httpx.ReadTimeout("timeout"))
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)

        with (
            patch(
                "src.clients.http_client.httpx.AsyncClient", return_value=mock_client
            ),
            patch("src.clients.http_client.HTTP_MAX_RETRIES", 1),
        ):
            # Act
            success, content, error_type = await http_client.get("https://example.com")

        # Assert
        assert success is False
        assert content == "Read timeout"
        assert error_type == "read_timeout"

    @pytest.mark.asyncio
    async def test_http_404_no_retry(self, http_client: HttpClient) -> None:
        """Returns immediately on 4xx errors without retry."""
        # Arrange
        mock_response = MagicMock()
        mock_response.status_code = 404

        mock_client = AsyncMock()
        mock_client.get = AsyncMock(
            side_effect=httpx.HTTPStatusError(
                "Not Found", request=MagicMock(), response=mock_response
            )
        )
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)

        with patch(
            "src.clients.http_client.httpx.AsyncClient", return_value=mock_client
        ):
            # Act
            success, content, error_type = await http_client.get("https://example.com")

        # Assert
        assert success is False
        assert content == "HTTP 404"
        assert error_type == "http_404"
        assert mock_client.get.call_count == 1

    @pytest.mark.asyncio
    async def test_http_429_retries(self, http_client: HttpClient) -> None:
        """Retries on 429 rate limit error."""
        # Arrange
        mock_response_429 = MagicMock()
        mock_response_429.status_code = 429

        mock_response_ok = MagicMock()
        mock_response_ok.text = "<html></html>"
        mock_response_ok.headers = {"content-type": "text/html"}
        mock_response_ok.raise_for_status = MagicMock()

        mock_client = AsyncMock()
        mock_client.get = AsyncMock(
            side_effect=[
                httpx.HTTPStatusError(
                    "Rate Limited", request=MagicMock(), response=mock_response_429
                ),
                mock_response_ok,
            ]
        )
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)

        with (
            patch(
                "src.clients.http_client.httpx.AsyncClient", return_value=mock_client
            ),
            patch("src.clients.http_client.HTTP_RETRY_BACKOFF", 0.001),
        ):
            # Act
            success, content, error_type = await http_client.get("https://example.com")

        # Assert
        assert success is True
        assert mock_client.get.call_count == 2

    @pytest.mark.asyncio
    async def test_network_error(self, http_client: HttpClient) -> None:
        """Returns error on network failure after retries."""
        # Arrange
        mock_client = AsyncMock()
        mock_client.get = AsyncMock(
            side_effect=httpx.NetworkError("Network unreachable")
        )
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)

        with (
            patch(
                "src.clients.http_client.httpx.AsyncClient", return_value=mock_client
            ),
            patch("src.clients.http_client.HTTP_MAX_RETRIES", 1),
        ):
            # Act
            success, content, error_type = await http_client.get("https://example.com")

        # Assert
        assert success is False
        assert content == "Network error"
        assert error_type == "network_error"

    @pytest.mark.asyncio
    async def test_too_many_redirects_no_retry(self, http_client: HttpClient) -> None:
        """Returns immediately on too many redirects without retry."""
        # Arrange
        mock_client = AsyncMock()
        mock_client.get = AsyncMock(
            side_effect=httpx.TooManyRedirects("Too many redirects")
        )
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)

        with patch(
            "src.clients.http_client.httpx.AsyncClient", return_value=mock_client
        ):
            # Act
            success, content, error_type = await http_client.get("https://example.com")

        # Assert
        assert success is False
        assert content == "Too many redirects"
        assert error_type == "too_many_redirects"
        assert mock_client.get.call_count == 1


class TestHttpClientHeaders:
    """Tests for HTTP client headers."""

    def test_get_headers_returns_user_agent(self) -> None:
        """Returns dict with User-Agent header."""
        # Arrange
        client = HttpClient()

        # Act
        headers = client._get_headers()

        # Assert
        assert "User-Agent" in headers
        assert len(headers["User-Agent"]) > 0
