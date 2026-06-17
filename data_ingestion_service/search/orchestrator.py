"""Search orchestrator – runs all platform adapters concurrently.

Active adapters (returns real data when credentials are set):
  - SerpAPI    → Reddit + Google Shopping (SERPAPI_KEY)
  - Google CSE → Google web search        (GOOGLE_API_KEY + GOOGLE_CSE_ID)
  - eBay       → product listings          (EBAY_APP_ID)
  - Discord    → server messages           (DISCORD_BOT_TOKEN)
  - Twitter    → tweets                    (TWITTER_BEARER_TOKEN)

Placeholder adapters (wired but return [] until credentials added):
  - Instagram, Facebook, Amazon
"""
import asyncio
from typing import List, Dict, Any

from .adapters.serpapi import search as serpapi_search
from .adapters.google_shopping import search as google_search
from .adapters.ebay import search as ebay_search
from .adapters.discord import search as discord_search
from .adapters.twitter import search as twitter_search
from .adapters.instagram import search as instagram_search
from .adapters.facebook import search as facebook_search
from .adapters.amazon import search as amazon_search
from .insights import compute_insights


async def aggregate_search(query: str) -> Dict[str, Any]:
    """Run all adapters concurrently, aggregate results and compute insights."""

    tasks = [
        serpapi_search(query),    # Reddit + Google Shopping via SerpAPI
        google_search(query),     # Google Custom Search (web)
        ebay_search(query),       # eBay product listings
        discord_search(query),    # Discord messages
        twitter_search(query),    # Twitter/X posts
        instagram_search(query),  # Instagram (placeholder)
        facebook_search(query),   # Facebook (placeholder)
        amazon_search(query),     # Amazon (placeholder)
    ]

    results_lists: List[List[Dict[str, Any]]] = await asyncio.gather(
        *tasks, return_exceptions=True
    )

    # Flatten, skip any adapter that threw an exception
    all_results: List[Dict[str, Any]] = []
    for r in results_lists:
        if isinstance(r, list):
            all_results.extend(r)

    insights = compute_insights(all_results)

    return {"results": all_results, "insights": insights}
