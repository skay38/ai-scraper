"""Response parsing and transformation functions."""

import json
import re

from src.mappers.url_mapper import normalize_pricing_urls
from src.models import BusinessType, CompanyExtractionData, PricingStatus
from src.utils import JsonParseError


def parse_company_response(response: str, base_url: str) -> CompanyExtractionData:
    """Parse JSON response from company data extraction.

    Args:
        response: Raw response string from LLM
        base_url: Source URL for resolving relative URLs

    Returns:
        Parsed company extraction data

    Raises:
        JsonParseError: When JSON cannot be found or parsed
    """
    json_match = re.search(r"\{[\s\S]*\}", response)
    if not json_match:
        raise JsonParseError("No JSON found in response")

    json_str = json_match.group(0)

    try:
        raw_data = json.loads(json_str)
    except json.JSONDecodeError as e:
        raise JsonParseError("Failed to parse JSON") from e

    pricing_urls = normalize_pricing_urls(raw_data.get("pricing_urls", []), base_url)

    return CompanyExtractionData(
        company_name=raw_data.get("company_name", BusinessType.UNKNOWN.value),
        company_description=raw_data.get(
            "company_description", BusinessType.UNKNOWN.value
        ),
        business_type=raw_data.get("business_type", BusinessType.UNKNOWN.value),
        pricing=raw_data.get("pricing", PricingStatus.NOT_FOUND_ON_MAIN_PAGE.value),
        pricing_urls=pricing_urls,
    )
