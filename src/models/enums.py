"""Enums for the AI scraper."""

from enum import StrEnum


class PricingStatus(StrEnum):
    """Status values for pricing extraction."""

    NOT_AVAILABLE = "Pricing information not available"
    NOT_FOUND_ON_MAIN_PAGE = "Not found on main page"
    NO_PRICING_INFO = "No pricing information available"
    UNKNOWN = "Unknown"

    @classmethod
    def empty_statuses(cls) -> list["PricingStatus"]:
        """Return list of statuses that indicate no pricing was found."""
        return [cls.NOT_AVAILABLE, cls.NOT_FOUND_ON_MAIN_PAGE, cls.UNKNOWN]


class BusinessType(StrEnum):
    """Business type classification."""

    B2B = "B2B"
    B2C = "B2C"
    B2B2C = "B2B2C"
    UNKNOWN = "Unknown"
