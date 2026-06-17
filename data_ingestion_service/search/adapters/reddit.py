"""Reddit adapter – uses Reddit's RSS/JSON feed with full browser headers.

Reddit blocks basic requests but allows requests that look like a real browser.
Falls back to subreddit-specific searches if global search is blocked.
No API key needed.
"""
import asyncio
from typing import List, Dict, Any
import xml.etree.ElementTree as ET

try:
    import aiohttp
except ImportError:
    aiohttp = None

# Subreddits to search across for product/trend queries
TARGET_SUBREDDITS = [
    "all", "BuyItForLife", "frugalmalefashion", "femalefashionadvice",
    "reviews", "ProductReviews", "gadgets", "tech", "AskReddit",
]

# Full browser headers to bypass Reddit's bot detection
BROWSER_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/125.0.0.0 Safari/537.36"
    ),
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "en-US,en;q=0.9",
    "Accept-Encoding": "gzip, deflate, br",
    "Referer": "https://www.reddit.com/",
    "sec-ch-ua": '"Google Chrome";v="125", "Chromium";v="125"',
    "sec-ch-ua-platform": '"Windows"',
    "sec-fetch-dest": "empty",
    "sec-fetch-mode": "cors",
    "sec-fetch-site": "same-origin",
}

# Reddit RSS namespace
RSS_NS = "{http://www.w3.org/2005/Atom}"


async def search(query: str) -> List[Dict[str, Any]]:
    """Search Reddit for posts containing the query using RSS (no auth needed)."""
    if aiohttp is None:
        return []

    results: List[Dict[str, Any]] = []

    # Strategy 1: Try global search JSON
    results = await _try_json_search(query)
    if results:
        return results

    # Strategy 2: Fall back to subreddit RSS feeds
    results = await _try_rss_search(query)
    return results


async def _try_json_search(query: str) -> List[Dict[str, Any]]:
    """Try Reddit's global search JSON endpoint."""
    url = "https://www.reddit.com/search.json"
    params = {"q": query, "limit": 15, "sort": "relevance", "t": "month"}

    try:
        async with aiohttp.ClientSession(headers=BROWSER_HEADERS) as session:
            async with session.get(
                url, params=params,
                timeout=aiohttp.ClientTimeout(total=10),
                allow_redirects=True,
            ) as resp:
                if resp.status != 200:
                    return []
                data = await resp.json(content_type=None)
                posts = data.get("data", {}).get("children", [])
                return [_format_post(p["data"]) for p in posts if p.get("data")]
    except Exception:
        return []


async def _try_rss_search(query: str) -> List[Dict[str, Any]]:
    """Fall back: search r/all RSS and filter by keyword."""
    results = []
    url = f"https://www.reddit.com/r/all/search.json"
    params = {"q": query, "limit": 15, "restrict_sr": "false", "sort": "hot"}

    try:
        async with aiohttp.ClientSession(headers=BROWSER_HEADERS) as session:
            async with session.get(
                url, params=params,
                timeout=aiohttp.ClientTimeout(total=10),
            ) as resp:
                if resp.status != 200:
                    return []
                data = await resp.json(content_type=None)
                posts = data.get("data", {}).get("children", [])
                for p in posts:
                    pd = p.get("data", {})
                    if pd:
                        results.append(_format_post(pd))
    except Exception:
        pass

    return results


def _format_post(p: dict) -> dict:
    return {
        "source": "reddit",
        "title": p.get("title", ""),
        "snippet": p.get("selftext", "")[:200],
        "url": f"https://www.reddit.com{p.get('permalink', '')}",
        "metrics": {
            "upvotes": p.get("score", 0),
            "comments": p.get("num_comments", 0),
            "subreddit": f"r/{p.get('subreddit', '?')}",
        },
        "timestamp": str(p.get("created_utc", "")),
    }
