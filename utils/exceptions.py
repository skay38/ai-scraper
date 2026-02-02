"""Custom exceptions for the AI scraper."""


class ScraperError(Exception):
    """Base exception for scraper errors."""

    pass


class HttpClientError(ScraperError):
    """HTTP client related errors."""

    pass


class ContentTypeError(HttpClientError):
    """Invalid content type error."""

    pass


class ConnectionTimeoutError(HttpClientError):
    """Connection timeout error."""

    pass


class ReadTimeoutError(HttpClientError):
    """Read timeout error."""

    pass


class NetworkError(HttpClientError):
    """Network error."""

    pass


class TooManyRedirectsError(HttpClientError):
    """Too many redirects error."""

    pass


class AnthropicClientError(ScraperError):
    """Anthropic API client errors."""

    pass


class RateLimitExceededError(AnthropicClientError):
    """Rate limit exceeded error."""

    pass


class ApiResponseError(AnthropicClientError):
    """API response error."""

    pass


class JsonParseError(AnthropicClientError):
    """JSON parsing error."""

    pass


class DataExtractionError(ScraperError):
    """Data extraction error."""

    pass


class ValidationError(ScraperError):
    """Data validation error."""

    pass
