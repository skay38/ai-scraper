"""Data models for the AI scraper."""

from pydantic import BaseModel, Field

from enums import BusinessType, PricingStatus


class CompanyExtractionData(BaseModel):
    """Data extracted from company page by LLM."""

    company_name: str = Field(default=BusinessType.UNKNOWN)
    company_description: str = Field(default=PricingStatus.NOT_AVAILABLE)
    business_type: str = Field(default=BusinessType.UNKNOWN)
    pricing: str = Field(default=PricingStatus.NOT_FOUND_ON_MAIN_PAGE)
    pricing_urls: list[str] = Field(default_factory=list)


class ScrapingData(BaseModel):
    """Final scraped data for a company."""

    company_name: str
    company_description: str
    business_type: str
    pricing: str
    pricing_urls: list[str] = Field(default_factory=list)


class ScrapingResult(BaseModel):
    """Result of scraping a single URL."""

    url: str
    success: bool
    data: ScrapingData | None = None
    error: str | None = None
