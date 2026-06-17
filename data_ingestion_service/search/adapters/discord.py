"""Discord adapter – searches messages across all guilds the bot belongs to.

Uses the Discord HTTP API directly (no discord.py dependency needed).
The bot must have:
  - MESSAGE_CONTENT intent enabled (Developer Portal → Bot → Privileged Intents)
  - Read Message History permission in the channels you want to search

Discord does NOT have a native search API for bots, so we fetch recent
messages from text channels and filter client-side.
"""
import os
import asyncio
from typing import List, Dict, Any

try:
    import aiohttp
except ImportError:
    aiohttp = None

DISCORD_API = "https://discord.com/api/v10"


async def search(query: str) -> List[Dict[str, Any]]:
    """Search Discord messages containing `query` across all guilds the bot is in."""
    token = os.getenv("DISCORD_BOT_TOKEN") or "MTUxNTMxMTE5NDgxNzE3MTQ5Ng.G5hO4X.0BQyaPVKf9JyktXdaaaetCfG416suMTCkzdjqA"
    if aiohttp is None:
        return []

    headers = {
        "Authorization": f"Bot {token}",
        "Content-Type": "application/json",
    }

    results: List[Dict[str, Any]] = []
    query_lower = query.lower()

    try:
        async with aiohttp.ClientSession(headers=headers) as session:
            # 1. Get guilds the bot is in
            async with session.get(f"{DISCORD_API}/users/@me/guilds") as resp:
                if resp.status != 200:
                    return []
                guilds = await resp.json()

            # Limit to first 3 guilds to keep it fast
            for guild in guilds[:3]:
                guild_id = guild["id"]
                guild_name = guild.get("name", "Unknown")

                # 2. Get text channels in this guild
                async with session.get(f"{DISCORD_API}/guilds/{guild_id}/channels") as resp:
                    if resp.status != 200:
                        continue
                    channels = await resp.json()

                text_channels = [c for c in channels if c.get("type") == 0]  # type 0 = text

                # Limit to first 5 text channels per guild
                for channel in text_channels[:5]:
                    channel_id = channel["id"]
                    channel_name = channel.get("name", "unknown")

                    # 3. Fetch last 50 messages from channel
                    async with session.get(
                        f"{DISCORD_API}/channels/{channel_id}/messages",
                        params={"limit": 50},
                    ) as resp:
                        if resp.status != 200:
                            continue
                        messages = await resp.json()

                    # 4. Filter messages that contain the query
                    for msg in messages:
                        content = msg.get("content", "")
                        if query_lower in content.lower():
                            author = msg.get("author", {})
                            results.append({
                                "source": "discord",
                                "title": content[:200],
                                "url": f"https://discord.com/channels/{guild_id}/{channel_id}/{msg['id']}",
                                "metrics": {
                                    "server": guild_name,
                                    "channel": f"#{channel_name}",
                                    "author": f"{author.get('username', '?')}",
                                },
                                "timestamp": msg.get("timestamp", ""),
                            })

                    # Stop early if we have enough results
                    if len(results) >= 10:
                        break
                if len(results) >= 10:
                    break

    except Exception:
        # Silently fail — don't break the aggregator
        pass

    return results[:10]
