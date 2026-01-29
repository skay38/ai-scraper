import asyncio
import json
import os
from pathlib import Path
from time import time

from dotenv import load_dotenv

from config import ANTHROPIC_CONCURRENCY, HTTP_CONCURRENCY
from services import http_client
from services.anthropic_client import AnthropicClient
from services.http_client import HttpClient
from services.scraper import ScraperService
from utils import display_result, load_domains

# Load environment variables
load_dotenv()

IMPORT_LIMIT = 50  # Start with 5 URLs for testing
DOMAIN_LIST_PATH = Path("data", "domains.csv")


async def main():
    """Main entry point for the scraper."""
    # Verify API key
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        print("❌ Error: ANTHROPIC_API_KEY not found in .env file")
        return

    # Load domains
    domains = await load_domains(DOMAIN_LIST_PATH, IMPORT_LIMIT)
    print(f"Loaded {len(domains)} domains\n")
    print(f"Concurrency: {HTTP_CONCURRENCY} HTTP, {ANTHROPIC_CONCURRENCY} Anthropic\n")

    # http_client = HttpClient()
    # anthropic_client = AnthropicClient(api_key=api_key)
    # scraper = ScraperService(
    #     http_client=http_client,
    #     anthropic_client=anthropic_client,
    # )
    # # Test with a single URL to verify functionality
    # result = await scraper.scrape_url(domains[0])
    # display_result(result)
    
    
    # Create semaphores for concurrency control
    http_semaphore = asyncio.Semaphore(HTTP_CONCURRENCY)
    anthropic_semaphore = asyncio.Semaphore(ANTHROPIC_CONCURRENCY)

    # Initialize clients
    http_client = HttpClient(semaphore=http_semaphore)
    anthropic_client = AnthropicClient(api_key=api_key, semaphore=anthropic_semaphore)
    scraper = ScraperService(
        http_client=http_client,
        anthropic_client=anthropic_client,
    )

    # Process URLs concurrently
    start_time = time()
    tasks = [scraper.scrape_url(domain) for domain in domains]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    elapsed = time() - start_time

    # Display results
    print("\n" + "=" * 80)
    print("RESULTS")
    print("=" * 80 + "\n")

    for result in results:
        if isinstance(result, Exception):
            print(f"❌ Exception: {result}")
        else:
            display_result(result)

    # Display summary
    successful = sum(1 for r in results if not isinstance(r, Exception) and r.success)
    failed = len(results) - successful

    # Count pricing extracted (not "Pricing information not available" or similar)
    pricing_extracted = sum(
        1 for r in results
        if not isinstance(r, Exception)
        and r.success
        and r.data
        and r.data.pricing
        and r.data.pricing not in ["Pricing information not available", "Not available", "Unknown", "Not found on main page"]
    )

    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print(f"Total URLs:        {len(domains)}")
    print(f"Successful:        {successful} ({successful / len(domains) * 100:.1f}%)")
    print(f"Failed:            {failed} ({failed / len(domains) * 100:.1f}%)")
    print(f"Pricing extracted: {pricing_extracted} ({pricing_extracted / len(domains) * 100:.1f}%)")
    print(f"Elapsed time:      {elapsed:.2f}s")
    print(f"Avg per URL:       {elapsed / len(domains):.2f}s")
    print("=" * 80 + "\n")

    # Save results to JSON
    json_results = []
    for result in results:
        if not isinstance(result, Exception):
            json_results.append(result.model_dump())

    with open("res.json", "w") as f:
        json.dump(json_results, f, indent=2)

    print(f"✅ Results saved to res.json")


if __name__ == "__main__":
    asyncio.run(main())
