"""Google Custom Search adapter.
Uses Google's Custom Search JSON API to search the entire web,
including Reddit, shopping sites, social media etc.

Free tier: 100 queries/day (no credit card needed).
Setup: https://console.cloud.google.com → enable "Custom Search API" → create API key
       https://programmablesearchengine.google.com → create engine → copy Search Engine ID

Required env vars:
  GOOGLE_API_KEY  – your API key from Google Cloud Console
  GOOGLE_CSE_ID   – your Search Engine ID (cx parameter)
"""
import os
from typing import List, Dict, Any

try:
    import aiohttp
except ImportError:
    aiohttp = None

GOOGLE_CSE_URL = "https://www.googleapis.com/customsearch/v1"


async def search(query: str) -> List[Dict[str, Any]]:
    """Search Google Custom Search and return unified result dicts."""
    api_key = os.getenv("GOOGLE_API_KEY")
    cse_id = os.getenv("GOOGLE_CSE_ID")

    if not api_key or not cse_id or api_key.startswith("YOUR_"):
        return []

    if aiohttp is None:
        return []

    results: List[Dict[str, Any]] = []

    try:
        async with aiohttp.ClientSession() as session:
            params = {
                "key": api_key,
                "cx": cse_id,
                "q": query,
                "num": 10,           # max 10 per request on free tier
                "safe": "active",
            }

            async with session.get(
                GOOGLE_CSE_URL,
                params=params,
                timeout=aiohttp.ClientTimeout(total=10),
            ) as resp:
                if resp.status != 200:
                    error = await resp.text()
                    print(f"[google_shopping] API error {resp.status}: {error[:200]}")
                    return []

                data = await resp.json()
                items = data.get("items", [])

                for item in items:
                    title = item.get("title", "")
                    url = item.get("link", "")
                    snippet = item.get("snippet", "")

                    # Try to extract price from snippet or pagemap
                    price = None
                    pagemap = item.get("pagemap", {})
                    offers = pagemap.get("offer", [{}])
                    if offers:
                        price = offers[0].get("price")
                    if not price:
                        product = pagemap.get("product", [{}])
                        if product:
                            price = product[0].get("price")

                    results.append({
                        "source": "google",
                        "title": title,
                        "snippet": snippet,
                        "url": url,
                        "metrics": {
                            "price": price,
                            "domain": item.get("displayLink", ""),
                        },
                        "timestamp": "",
                    })

    except Exception as e:
        print(f"[google_shopping] Exception: {e}")

    return results
