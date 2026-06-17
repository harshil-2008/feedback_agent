import os
from typing import List, Dict, Any
import asyncio

async def search(query: str) -> List[Dict[str, Any]]:
    """Instagram search placeholder – returns empty list if credentials missing.
    Unified schema: {source, title, url, metrics, timestamp}
    """
    # Instagram Basic Display API requires an access token.
    token = os.getenv('INSTAGRAM_ACCESS_TOKEN')
    if not token or token.startswith('YOUR_'):
        return []
    # Real implementation would hit https://graph.instagram.com/me/media?fields=caption,media_url,permalink&access_token=TOKEN
    return []
