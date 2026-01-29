"""Configuration constants for the AI scraper."""

# Anthropic API
ANTHROPIC_MODEL = "claude-sonnet-4-20250514"
MAX_TOKENS = 1024

# HTTP Client
HTTP_TIMEOUT_CONNECT = 10.0  # seconds
HTTP_TIMEOUT_READ = 30.0  # seconds
HTTP_MAX_RETRIES = 3
HTTP_RETRY_BACKOFF = 1.0  # initial backoff in seconds

# Concurrency
HTTP_CONCURRENCY = 50  # concurrent HTTP requests
ANTHROPIC_CONCURRENCY = 10  # concurrent Anthropic API calls

# Content Processing
HTML_TRUNCATE_MAIN = 500000  # characters for main page
HTML_TRUNCATE_PRICING = 300000  # characters for pricing pages

# User-Agent
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
]
