"""TTL cache with request coalescing for FIRMS responses (FR-DATA-012).

FIRMS data are public, so a cached response for a query can serve any user; caching
saves each user's transaction quota and FIRMS's servers. Concurrent identical requests
share one upstream call ("single flight"). Entries expire by TTL and the cache is bounded
(least recently used entries are evicted).
"""

from __future__ import annotations

import asyncio
import time
from collections import OrderedDict
from collections.abc import Awaitable, Callable, Hashable
from typing import Any


class ResponseCache:
    def __init__(self, max_entries: int, clock: Callable[[], float] = time.monotonic) -> None:
        self.max_entries = max_entries
        self._clock = clock
        self._data: OrderedDict[Hashable, tuple[float, Any]] = OrderedDict()
        self._inflight: dict[Hashable, asyncio.Future] = {}
        self.hits = 0
        self.misses = 0

    def get(self, key: Hashable) -> tuple[bool, Any]:
        item = self._data.get(key)
        if item is None:
            return False, None
        expires, value = item
        if expires <= self._clock():
            del self._data[key]
            return False, None
        self._data.move_to_end(key)
        return True, value

    def put(self, key: Hashable, value: Any, ttl_seconds: float) -> None:
        if self.max_entries <= 0 or ttl_seconds <= 0:
            return
        self._data[key] = (self._clock() + ttl_seconds, value)
        self._data.move_to_end(key)
        while len(self._data) > self.max_entries:
            self._data.popitem(last=False)

    async def get_or_fetch(
        self, key: Hashable, ttl_seconds: float, fetch: Callable[[], Awaitable[Any]]
    ) -> tuple[Any, bool]:
        """Return ``(value, from_cache)``; at most one fetch runs per key at a time."""
        found, value = self.get(key)
        if found:
            self.hits += 1
            return value, True
        pending = self._inflight.get(key)
        if pending is not None:
            self.hits += 1
            return await asyncio.shield(pending), True
        self.misses += 1
        future: asyncio.Future = asyncio.get_running_loop().create_future()
        self._inflight[key] = future
        try:
            value = await fetch()
        except BaseException as exc:
            future.set_exception(exc)
            future.exception()  # mark retrieved so un-awaited futures do not warn
            raise
        else:
            self.put(key, value, ttl_seconds)
            future.set_result(value)
            return value, False
        finally:
            self._inflight.pop(key, None)

    def clear(self) -> None:
        self._data.clear()
