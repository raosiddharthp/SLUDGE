"""Serialise and coalesce sync requests. No Google imports, so it tests offline."""
import asyncio


class Coalescer:
    """Run fn in a thread, one at a time. A run that starts after a request already covers it."""

    def __init__(self, fn):
        self.fn = fn
        self.lock = asyncio.Lock()
        self.requested = 0
        self.completed = 0
        self.last = None

    async def run(self):
        self.requested += 1
        mine = self.requested
        async with self.lock:
            if self.completed >= mine:
                return self.last
            covers = self.requested
            self.last = await asyncio.to_thread(self.fn)
            self.completed = covers
            return self.last
