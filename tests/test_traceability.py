"""Requirements traceability meta-tests (ADR-0008).

* requirements.yaml is well formed.
* Every ``req`` marker names a known requirement.
* Every requirement verified by ``test`` whose status is ``implemented`` or
  ``verified`` has at least one test.
"""

from __future__ import annotations

import re

import pytest
import yaml

from tests.conftest import FULL_COLLECTION, REPO_ROOT, REQUIREMENT_TESTS

REQUIREMENTS_FILE = REPO_ROOT / "docs" / "project" / "requirements.yaml"
ID_PATTERN = re.compile(r"^(FR-[A-Z]+|SEC|NFR|DOC|PRJ)(-[0-9]{3}|-[A-Z]+-[0-9]{3})$")
REQUIRED_FIELDS = {"id", "title", "source", "rationale", "priority", "verification", "status"}
PRIORITIES = {"must", "should", "could"}
VERIFICATIONS = {"test", "inspection", "demonstration", "analysis"}
STATUSES = {"planned", "implemented", "verified"}


def _load() -> list[dict]:
    data = yaml.safe_load(REQUIREMENTS_FILE.read_text(encoding="utf-8"))
    return data["requirements"]


def test_requirements_file_is_well_formed() -> None:
    reqs = _load()
    ids = [r["id"] for r in reqs]
    assert len(ids) == len(set(ids)), "duplicate requirement IDs"
    for r in reqs:
        missing = REQUIRED_FIELDS - r.keys()
        assert not missing, f"{r.get('id')}: missing fields {missing}"
        assert ID_PATTERN.match(r["id"]), f"bad requirement ID {r['id']}"
        assert r["priority"] in PRIORITIES, r["id"]
        assert r["verification"] in VERIFICATIONS, r["id"]
        assert r["status"] in STATUSES, r["id"]


def test_markers_reference_known_requirements() -> None:
    known = {r["id"] for r in _load()}
    unknown = sorted(set(REQUIREMENT_TESTS) - known)
    assert not unknown, f"tests reference unknown requirement IDs: {unknown}"


def test_implemented_requirements_have_tests() -> None:
    if not FULL_COLLECTION["value"]:
        pytest.skip("traceability is only checked when the full suite is collected")
    untested = [
        r["id"]
        for r in _load()
        if r["verification"] == "test"
        and r["status"] in {"implemented", "verified"}
        and not REQUIREMENT_TESTS.get(r["id"])
    ]
    assert not untested, f"implemented requirements without tests: {untested}"


@pytest.mark.req("NFR-001")
def test_network_is_blocked_for_non_live_tests() -> None:
    import socket

    from tests.conftest import NetworkAccessBlocked

    with (
        pytest.raises(NetworkAccessBlocked),
        socket.create_connection(("192.0.2.1", 443), timeout=1),
    ):
        pass
