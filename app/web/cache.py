"""Tiny time-based cache. Errors are never cached."""
import time


class TTLCache:
    def __init__(self, ttl, clock=time.monotonic):
        self.ttl, self.clock, self.items = ttl, clock, {}

    def get(self, key, fn):
        now = self.clock()
        hit = self.items.get(key)
        if hit and now - hit[0] < self.ttl:
            return hit[1]
        value = fn()
        self.items[key] = (now, value)
        return value

    def clear(self):
        self.items.clear()
