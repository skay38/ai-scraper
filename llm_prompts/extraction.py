"""Extraction prompts for company and pricing data."""

COMPANY_EXTRACTION_PROMPT = """You are a data extraction assistant. Analyze the provided text content and extract structured company information.

Extract the following information:
1. company_name: The official name of the company
2. company_description: A 1-2 sentence description of what the company does
3. business_type: Classify as "B2B", "B2C", or "B2B2C" (use "Unknown" if unclear)
4. pricing: Extract pricing information if available on this page. If not found, return "Not found on main page"
5. pricing_urls: List of URLs (absolute URLs, not relative paths) that likely contain pricing information. Look for links with text like "Pricing", "Plans", "Get Started", etc. Return empty array if none found.

<source_url>
{url}
</source_url>

<content max_chars="{max_chars}">
{content}
</content>

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

PRICING_EXTRACTION_PROMPT = """You are analyzing a pricing page. Extract detailed pricing information from this text content.

Focus on:
- Pricing tiers/plans and their costs
- Billing frequency (monthly, annual)
- Key features or limits per tier
- Any special pricing notes

<content max_chars="{max_chars}">
{content}
</content>

Return a concise summary of the pricing structure (2-3 sentences max).
If no pricing information is found, return "No pricing information available".

Provide ONLY the pricing summary, no other text or explanation.
"""


def build_company_extraction_prompt(url: str, content: str, max_chars: int) -> str:
    """Build prompt for company data extraction.

    Args:
        url: Source URL of the content
        content: Cleaned and truncated HTML content
        max_chars: Maximum character limit used for truncation

    Returns:
        Formatted prompt string
    """
    return COMPANY_EXTRACTION_PROMPT.format(
        url=url, content=content, max_chars=max_chars
    )


def build_pricing_extraction_prompt(content: str, max_chars: int) -> str:
    """Build prompt for pricing extraction.

    Args:
        content: Cleaned and truncated HTML content
        max_chars: Maximum character limit used for truncation

    Returns:
        Formatted prompt string
    """
    return PRICING_EXTRACTION_PROMPT.format(content=content, max_chars=max_chars)
