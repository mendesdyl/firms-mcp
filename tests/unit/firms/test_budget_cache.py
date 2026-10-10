"""Transaction budget and response cache (FR-DATA-012, FR-DATA-013)."""

from __future__ import annotations

import asyncio

import pytest

from firms_mcp.firms.budget import TransactionBudget, key_fingerprint, transaction_weight
from firms_mcp.firms.cache import ResponseCache
from firms_mcp.firms.errors import RateLimited
from firms_mcp.firms.geo import BoundingBox
from tests.fixtures.firms_csv import MAP_KEY, OTHER_KEY


class FakeClock:
    def __init__(self) -> None:
        self.now = 1000.0

    def __call__(self) -> float:
        return self.now


@pytest.mark.req("FR-DATA-013")
@pytest.mark.parametrize(
    ("source", "box", "days", "expected"),
    [
        # FIRMS area page: ceil(ceil(dx/60) * ceil(dy/60) * (2 VIIRS | 0.5 other) * days)
        ("VIIRS_SNPP_NRT", BoundingBox.world(), 1, 36),
        ("MODIS_NRT", BoundingBox.world(), 1, 9),
        ("VIIRS_NOAA20_NRT", BoundingBox(west=-119, south=33, east=-118, north=34), 1, 2),
        ("MODIS_NRT", BoundingBox(west=-119, south=33, east=-118, north=34), 1, 1),
        ("LANDSAT_NRT", BoundingBox(west=-125, south=25, east=-65, north=50), 5, 3),
        ("VIIRS_SNPP_SP", BoundingBox(west=-85, south=-57, east=-32, north=14), 5, 20),
    ],
)
def test_transaction_weight_matches_firms_formula(source, box, days, expected) -> None:
    assert transaction_weight(source, box, days) == expected


@pytest.mark.req("FR-DATA-013")
def test_budget_window_and_retry_after() -> None:
    clock = FakeClock()
    budget = TransactionBudget(100, window_seconds=600, clock=clock)
    budget.charge(MAP_KEY, 60)
    clock.now += 100
    budget.charge(MAP_KEY, 30)
    assert budget.used(MAP_KEY) == 90
    with pytest.raises(RateLimited) as error:
        budget.charge(MAP_KEY, 20)
    assert error.value.retry_after_seconds == pytest.approx(500.0)
    budget.charge(OTHER_KEY, 100)  # keys are independent
    clock.now += 501
    budget.charge(MAP_KEY, 20)  # the first charge has left the window
    assert budget.used(MAP_KEY) == 50


@pytest.mark.req("FR-DATA-013")
def test_requests_larger_than_the_budget_are_refused_outright() -> None:
    with pytest.raises(RateLimited, match="smaller area"):
        TransactionBudget(10).charge(MAP_KEY, 11)


def test_keys_are_fingerprinted_not_stored() -> None:
    budget = TransactionBudget(100)
    budget.charge(MAP_KEY, 1)
    assert MAP_KEY not in repr(budget._events)
    assert key_fingerprint(MAP_KEY) in budget._events


@pytest.mark.req("FR-DATA-012")
async def test_cache_hits_expiry_and_bounds() -> None:
    clock = FakeClock()
    cache = ResponseCache(max_entries=2, clock=clock)
    calls = 0

    async def fetch() -> str:
        nonlocal calls
        calls += 1
        return f"value-{calls}"

    assert await cache.get_or_fetch("a", 10, fetch) == ("value-1", False)
    assert await cache.get_or_fetch("a", 10, fetch) == ("value-1", True)
    clock.now += 11
    assert await cache.get_or_fetch("a", 10, fetch) == ("value-2", False)
    await cache.get_or_fetch("b", 10, fetch)
    await cache.get_or_fetch("c", 10, fetch)  # evicts least recently used ("a")
    assert cache.get("a") == (False, None)
    assert cache.hits == 1 and cache.misses == 4


@pytest.mark.req("FR-DATA-012")
async def test_concurrent_identical_requests_share_one_fetch() -> None:
    cache = ResponseCache(max_entries=10)
    calls = 0
    gate = asyncio.Event()

    async def fetch() -> int:
        nonlocal calls
        calls += 1
        await gate.wait()
        return 42

    tasks = [asyncio.create_task(cache.get_or_fetch("k", 60, fetch)) for _ in range(5)]
    await asyncio.sleep(0)
    gate.set()
    results = await asyncio.gather(*tasks)
    assert calls == 1
    assert [value for value, _ in results] == [42] * 5
    assert sum(from_cache for _, from_cache in results) == 4


@pytest.mark.req("FR-DATA-012")
async def test_failures_are_not_cached() -> None:
    cache = ResponseCache(max_entries=10)
    attempts = 0

    async def flaky() -> str:
        nonlocal attempts
        attempts += 1
        if attempts == 1:
            raise RuntimeError("boom")
        return "ok"

    with pytest.raises(RuntimeError):
        await cache.get_or_fetch("k", 60, flaky)
    assert await cache.get_or_fetch("k", 60, flaky) == ("ok", False)


def test_disabled_cache_stores_nothing() -> None:
    cache = ResponseCache(max_entries=0)
    cache.put("k", 1, 60)
    assert cache.get("k") == (False, None)
