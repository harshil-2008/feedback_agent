"""SerpAPI adapter – searches Reddit and Google Shopping via SerpAPI.

One API key gives access to Reddit, Google, Google Shopping, and more.
Free tier: 100 searches/month. No credit card required.

Sign up at https://serpapi.com → Dashboard → Your API Key

Required env var:
  SERPAPI_KEY – your SerpAPI key

This adapter makes 2 calls per search:
  1. Reddit search  → returns Reddit posts about the query
  2. Google Shopping → returns product listings with prices
"""
import os
from typing import List, Dict, Any

try:
    import aiohttp
except ImportError:
    aiohttp = None

SERPAPI_BASE = "https://serpapi.com/search"


async def _serpapi_get(session: "aiohttp.ClientSession", params: dict) -> dict:
    """Make a single SerpAPI call and return the JSON response."""
    try:
        async with session.get(
            SERPAPI_BASE,
            params=params,
            timeout=aiohttp.ClientTimeout(total=15),
        ) as resp:
            if resp.status != 200:
                error = await resp.text()
                print(f"[serpapi] HTTP {resp.status}: {error[:200]}")
                return {}
            return await resp.json()
    except Exception as e:
        print(f"[serpapi] Exception: {e}")
        return {}


async def search(query: str) -> List[Dict[str, Any]]:
    """Search Reddit and Google Shopping via SerpAPI."""
    api_key = os.getenv("SERPAPI_KEY") or "4088e2971b8daf6f5a47bdf3a407a9ad178339ccd2b5d9b1e6ce15efc8de906f"
    if aiohttp is None:
        return []

    results: List[Dict[str, Any]] = []

    async with aiohttp.ClientSession() as session:
        # ── 1. Reddit search ─────────────────────────────────────
        reddit_data = await _serpapi_get(session, {
            "engine": "google",
            "q": f"site:reddit.com {query}",
            "api_key": api_key,
            "num": 10,
        })

        for post in reddit_data.get("organic_results", []):
            results.append({
                "source": "reddit",
                "title": post.get("title", ""),
                "snippet": post.get("snippet", ""),
                "url": post.get("link", ""),
                "metrics": {
                    "upvotes": post.get("upvotes", ""),
                    "comments": post.get("comments", ""),
                    "subreddit": post.get("subreddit", ""),
                },
                "timestamp": post.get("date", ""),
            })

        # ── 2. Google Shopping search ─────────────────────────────
        shopping_data = await _serpapi_get(session, {
            "engine": "google_shopping",
            "q": query,
            "api_key": api_key,
            "num": 10,
            "gl": "us",
            "hl": "en",
        })

        for item in shopping_data.get("shopping_results", []):
            price_str = item.get("price", "")
            # Strip $ and commas to get numeric price
            price_num = None
            try:
                price_num = float(price_str.replace("$", "").replace(",", "").strip())
            except (ValueError, AttributeError):
                pass

            results.append({
                "source": "google_shopping",
                "title": item.get("title", ""),
                "snippet": item.get("source", ""),
                "url": item.get("link", item.get("product_link", "")),
                "metrics": {
                    "price": price_num,
                    "store": item.get("source", ""),
                    "rating": item.get("rating", ""),
                    "reviews": item.get("reviews", ""),
                },
                "timestamp": "",
            })

    return results
