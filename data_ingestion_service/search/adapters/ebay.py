import os
from typing import List, Dict, Any
import asyncio

async def search(query: str) -> List[Dict[str, Any]]:
    """eBay Finding API placeholder – returns empty list if credentials missing.
    Unified schema: {source, title, url, metrics, timestamp}
    """
    app_id = os.getenv('EBAY_APP_ID')
    if not app_id or app_id.startswith('YOUR_'):
        return []
    # Real implementation would call https://svcs.ebay.com/services/search/FindingService/v1
    return []
