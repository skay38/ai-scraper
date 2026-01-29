"""Anthropic AI client for data extraction."""

import asyncio
import json
import os
import re
from typing import Optional

from anthropic import Anthropic, AsyncAnthropic, RateLimitError, APIError
from bs4 import BeautifulSoup

from config import (
    ANTHROPIC_CONCURRENCY,
    ANTHROPIC_MODEL,
    HTML_TRUNCATE_MAIN,
    HTML_TRUNCATE_PRICING,
    MAX_TOKENS,
)


class AnthropicClient:
    """Client for extracting structured data using Anthropic's Claude API."""

    def __init__(self, api_key: str, semaphore: Optional[asyncio.Semaphore] = None):
        """Initialize Anthropic client.

        Args:
            api_key: Anthropic API key
            semaphore: Optional semaphore for rate limiting
        """
        self.client = AsyncAnthropic(api_key=api_key)
        self.semaphore = semaphore or asyncio.Semaphore(ANTHROPIC_CONCURRENCY)

    def _clean_html(self, html: str) -> str:
        """Clean HTML by removing scripts, styles, and extra whitespace.

        Args:
            html: Raw HTML content

        Returns:
            Cleaned text content
        """
        soup = BeautifulSoup(html, "html.parser")

        # Remove script and style elements
        for script in soup(["script", "style", "noscript"]):
            script.decompose()

        # # Get text and clean whitespace
        # text = soup.get_text()
        # lines = (line.strip() for line in text.splitlines())
        # chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        # text = " ".join(chunk for chunk in chunks if chunk)

        # return html content as string
        return soup.prettify()

    async def _call_api(
        self, prompt: str, max_retries: int = 3
    ) -> tuple[bool, str, Optional[str]]:
        """Call Anthropic API with retry logic.

        Args:
            prompt: Prompt to send to API
            max_retries: Maximum number of retries

        Returns:
            Tuple of (success, response_or_error, error_type)
        """
        async with self.semaphore:
            for attempt in range(max_retries):
                try:
                    response = await self.client.messages.create(
                        model=ANTHROPIC_MODEL,
                        max_tokens=MAX_TOKENS,
                        messages=[{"role": "user", "content": prompt}],
                    )

                    # Extract text content
                    content = response.content[0].text
                    return (True, content, None)

                except RateLimitError as e:
                    error_msg = f"Rate limit error: {str(e)}"
                    error_type = "rate_limit"
                    # Exponential backoff for rate limits
                    if attempt < max_retries - 1:
                        await asyncio.sleep(2 ** (attempt + 1))
                    else:
                        return (False, error_msg, error_type)

                except APIError as e:
                    error_msg = f"Anthropic API error: {str(e)}"
                    error_type = "api_error"
                    return (False, error_msg, error_type)

                except Exception as e:
                    error_msg = f"Unexpected error: {str(e)}"
                    error_type = "unexpected_error"
                    return (False, error_msg, error_type)

            return (False, "Max retries exceeded", "max_retries")

    async def extract_company_data(
        self, html: str, url: str
    ) -> tuple[bool, Optional[dict], Optional[str]]:
        """Extract company data and pricing URLs from main page HTML.

        Args:
            html: HTML content
            url: Source URL

        Returns:
            Tuple of (success, data_dict, error_message)
            data_dict contains: company_name, company_description, business_type, pricing, pricing_urls
        """
        # Clean and truncate HTML
        cleaned = self._clean_html(html)
        
        truncated = cleaned[:HTML_TRUNCATE_MAIN]
        print("Truncated from ", len(cleaned), "to", len(truncated))

        prompt = f"""You are a data extraction assistant. Analyze the following text content from {url} and extract structured company information.

Extract the following information:
1. company_name: The official name of the company
2. company_description: A 1-2 sentence description of what the company does
3. business_type: Classify as "B2B", "B2C", or "B2B2C" (use "Unknown" if unclear)
4. pricing: Extract pricing information if available on this page. If not found, return "Not found on main page"
5. pricing_urls: List of URLs (absolute URLs, not relative paths) that likely contain pricing information. Look for links with text like "Pricing", "Plans", "Get Started", etc. Return empty array if none found.

Content (first {HTML_TRUNCATE_MAIN} characters):
{truncated}

Return ONLY a JSON object with this exact structure (no markdown, no explanation):
{{
  "company_name": "string",
  "company_description": "string",
  "business_type": "string",
  "pricing": "string",
  "pricing_urls": ["string"]
}}

Be concise and accurate. If information is not available, use "Unknown".
"""

        success, response, error_type = await self._call_api(prompt)

        if not success:
            return (False, None, response)

        # Parse JSON response
        try:
            # Extract JSON from response (handle markdown code blocks)
            json_match = re.search(r"\{[\s\S]*\}", response)
            if json_match:
                json_str = json_match.group(0)
                data = json.loads(json_str)
            else:
                return (False, None, "No JSON found in response")

            # Validate required fields
            required_fields = [
                "company_name",
                "company_description",
                "business_type",
                "pricing",
            ]
            for field in required_fields:
                if field not in data:
                    data[field] = "Unknown"

            if "pricing_urls" not in data:
                data["pricing_urls"] = []

            # Ensure pricing_urls is a list
            if not isinstance(data["pricing_urls"], list):
                data["pricing_urls"] = []

            # Filter pricing URLs to ensure they're absolute URLs
            if data["pricing_urls"]:
                filtered_urls = []
                for pricing_url in data["pricing_urls"]:
                    # If relative URL, convert to absolute
                    if pricing_url.startswith("/"):
                        base_url = url.rstrip("/")
                        filtered_urls.append(f"{base_url}{pricing_url}")
                    elif pricing_url.startswith(("http://", "https://")):
                        filtered_urls.append(pricing_url)
                data["pricing_urls"] = filtered_urls[:3]  # Limit to 3 pricing URLs

            return (True, data, None)

        except json.JSONDecodeError as e:
            return (False, None, f"Failed to parse JSON: {str(e)}")
        except Exception as e:
            return (False, None, f"Error processing response: {str(e)}")

    async def extract_pricing(self, html: str) -> tuple[bool, str, Optional[str]]:
        """Extract pricing details from a pricing page.

        Args:
            html: HTML content

        Returns:
            Tuple of (success, pricing_summary, error_message)
        """
        # Clean and truncate HTML
        cleaned = self._clean_html(html)
        truncated = cleaned[:HTML_TRUNCATE_PRICING]

        prompt = f"""You are analyzing a pricing page. Extract detailed pricing information from this text content.

Focus on:
- Pricing tiers/plans and their costs
- Billing frequency (monthly, annual)
- Key features or limits per tier
- Any special pricing notes

Content (first {HTML_TRUNCATE_PRICING} characters):
{truncated}

Return a concise summary of the pricing structure (2-3 sentences max).
If no pricing information is found, return "No pricing information available".

Provide ONLY the pricing summary, no other text or explanation.
"""

        success, response, error_type = await self._call_api(prompt)

        if not success:
            return (False, "Failed to extract pricing", response)

        return (True, response.strip(), None)
