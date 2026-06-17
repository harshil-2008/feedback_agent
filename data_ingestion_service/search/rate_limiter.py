import time
from collections import defaultdict

# In‑memory store: {ip: [(timestamp1), (timestamp2), ...]}
_rate_store = defaultdict(list)

def check_rate_limit(client_ip: str, limit: int = 5, period_seconds: int = 3600) -> bool:
    """Return True if request is allowed, otherwise False.
    Keeps up to `limit` requests per `period_seconds` for each IP.
    """
    now = time.time()
    timestamps = _rate_store[client_ip]
    # Drop old timestamps
    timestamps = [t for t in timestamps if now - t < period_seconds]
    _rate_store[client_ip] = timestamps
    if len(timestamps) >= limit:
        return False
    timestamps.append(now)
    return True
