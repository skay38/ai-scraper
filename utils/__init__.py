"""Utility modules for the AI scraper."""

from utils.config import (
    ANTHROPIC_CONCURRENCY,
    ANTHROPIC_MODEL,
    DEFAULT_IMPORT_LIMIT,
    HTML_TRUNCATE_MAIN,
    HTML_TRUNCATE_PRICING,
    HTTP_CONCURRENCY,
    HTTP_MAX_RETRIES,
    HTTP_RETRY_BACKOFF,
    HTTP_TIMEOUT_CONNECT,
    HTTP_TIMEOUT_READ,
    MAX_PRICING_URLS,
    MAX_TOKENS,
    OUTPUT_FILE,
    USER_AGENTS,
)
from utils.exceptions import (
    AnthropicClientError,
    ApiResponseError,
    ConnectionTimeoutError,
    ContentTypeError,
    DataExtractionError,
    HttpClientError,
    JsonParseError,
    NetworkError,
    RateLimitExceededError,
    ReadTimeoutError,
    ScraperError,
    TooManyRedirectsError,
    ValidationError,
)
from utils.helpers import display_result, load_domains
from utils.logger import logger, setup_logger

__all__ = [
    # Config
    "ANTHROPIC_CONCURRENCY",
    "ANTHROPIC_MODEL",
    "DEFAULT_IMPORT_LIMIT",
    "HTML_TRUNCATE_MAIN",
    "HTML_TRUNCATE_PRICING",
    "HTTP_CONCURRENCY",
    "HTTP_MAX_RETRIES",
    "HTTP_RETRY_BACKOFF",
    "HTTP_TIMEOUT_CONNECT",
    "HTTP_TIMEOUT_READ",
    "MAX_PRICING_URLS",
    "MAX_TOKENS",
    "OUTPUT_FILE",
    "USER_AGENTS",
    # Exceptions
    "AnthropicClientError",
    "ApiResponseError",
    "ConnectionTimeoutError",
    "ContentTypeError",
    "DataExtractionError",
    "HttpClientError",
    "JsonParseError",
    "NetworkError",
    "RateLimitExceededError",
    "ReadTimeoutError",
    "ScraperError",
    "TooManyRedirectsError",
    "ValidationError",
    # Helpers
    "display_result",
    "load_domains",
    # Logger
    "logger",
    "setup_logger",
]
