"""Clearing the cache forces the next read to fetch fresh data."""
from app.web.cache import TTLCache

calls = []


def fetch():
    calls.append(1)
    return len(calls)


cache = TTLCache(300)
assert cache.get("k", fetch) == 1 and cache.get("k", fetch) == 1
cache.clear()
assert cache.get("k", fetch) == 2
print("all cache-clear tests passed")
