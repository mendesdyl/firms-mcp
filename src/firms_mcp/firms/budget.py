"""Client-side guard for the FIRMS transaction limit (FR-DATA-013).

FIRMS allows 5,000 transactions per MAP_KEY per 10-minute interval, and "larger
transactions may count as multiple requests". The weight estimate below is the formula
FIRMS's own area-API page uses to display the "Mapkey transaction amount" for a request
(page script ``computeWeight``, observed 2026-10-09):

    ceil(ceil((east - west) / 60) * ceil((north - south) / 60) * s * DAY_RANGE)
    s = 2 for VIIRS sources, 0.5 otherwise

The guard keeps a rolling 10-minute window per key (keys are hashed, never stored) and
refuses a request that would push the estimate over the configured budget, with the time
to wait. It is per-process: multiple server replicas each keep their own window.
"""

from __future__ import annotations

import hashlib
import math
import threading
import time
from collections import deque
from collections.abc import Callable

from firms_mcp.config import FIRMS_TRANSACTION_WINDOW_SECONDS
from firms_mcp.firms.errors import RateLimited
from firms_mcp.firms.geo import BoundingBox


def transaction_weight(source_id: str, area: BoundingBox, day_range: int) -> int:
    factor = 2.0 if "VIIRS" in source_id.upper() else 0.5
    columns = math.ceil(area.width_degrees / 60.0)
    rows = math.ceil(area.height_degrees / 60.0)
    return max(1, math.ceil(columns * rows * factor * day_range))


def key_fingerprint(map_key: str) -> str:
    return hashlib.sha256(map_key.encode("utf-8")).hexdigest()[:16]


class TransactionBudget:
    def __init__(
        self,
        budget: int,
        window_seconds: float = FIRMS_TRANSACTION_WINDOW_SECONDS,
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        self.budget = budget
        self.window = window_seconds
        self._clock = clock
        self._events: dict[str, deque[tuple[float, int]]] = {}
        self._lock = threading.Lock()

    def _prune(self, events: deque[tuple[float, int]], now: float) -> None:
        while events and events[0][0] <= now - self.window:
            events.popleft()

    def used(self, map_key: str) -> int:
        with self._lock:
            events = self._events.get(key_fingerprint(map_key), deque())
            self._prune(events, self._clock())
            return sum(weight for _, weight in events)

    def charge(self, map_key: str, weight: int) -> None:
        """Record ``weight`` or raise RateLimited (with retry-after) if over budget."""
        fingerprint = key_fingerprint(map_key)
        with self._lock:
            now = self._clock()
            events = self._events.setdefault(fingerprint, deque())
            self._prune(events, now)
            used = sum(w for _, w in events)
            if weight > self.budget:
                raise RateLimited(
                    f"This request is estimated at {weight} FIRMS transactions, more than the "
                    f"{self.budget} allowed per 10 minutes. Use a smaller area or fewer days."
                )
            if used + weight > self.budget:
                excess = used + weight - self.budget
                released = 0
                wait = 0.0
                for timestamp, w in events:
                    released += w
                    wait = timestamp + self.window - now
                    if released >= excess:
                        break
                raise RateLimited(
                    f"Estimated FIRMS usage for this MAP_KEY would reach {used + weight} of the "
                    f"{self.budget} transactions allowed per 10 minutes.",
                    retry_after_seconds=round(max(wait, 1.0), 1),
                )
            events.append((now, weight))
