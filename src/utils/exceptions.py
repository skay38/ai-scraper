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


class ValidationError(ScraperError):
    """Data validation error."""

    pass
