"""Shared pytest configuration.

* Blocks outbound network access in every test that is not marked ``live``
  (requirement NFR-001; mirrors the Earthdata MCP's autouse network block).
* Collects ``@pytest.mark.req(...)`` markers so that tests/test_traceability.py can
  check every implemented requirement against the tests that verify it.
"""

from __future__ import annotations

import ipaddress
import socket
from collections import defaultdict
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent

# requirement ID -> list of test node IDs; filled during collection.
REQUIREMENT_TESTS: dict[str, list[str]] = defaultdict(list)
# True when the whole default suite was collected (not a subset).
FULL_COLLECTION: dict[str, bool] = {"value": False}


class NetworkAccessBlocked(RuntimeError):
    """Raised when a non-live test tries to open a network connection."""


def _is_local(address: object) -> bool:
    if isinstance(address, str):  # AF_UNIX path
        return True
    if isinstance(address, tuple) and address:
        host = address[0]
        if host in ("localhost", ""):
            return True
        try:
            return ipaddress.ip_address(host).is_loopback
        except ValueError:
            return False
    return False


@pytest.fixture(autouse=True)
def _block_network(request: pytest.FixtureRequest, monkeypatch: pytest.MonkeyPatch) -> None:
    if request.node.get_closest_marker("live"):
        return
    real_connect = socket.socket.connect
    real_connect_ex = socket.socket.connect_ex

    def guarded_connect(sock: socket.socket, address: object) -> None:
        if not _is_local(address):
            raise NetworkAccessBlocked(
                f"Test {request.node.nodeid} tried to connect to {address!r}. "
                "Mock the HTTP call (respx) or mark the test 'live'."
            )
        return real_connect(sock, address)

    def guarded_connect_ex(sock: socket.socket, address: object) -> int:
        if not _is_local(address):
            raise NetworkAccessBlocked(
                f"Test {request.node.nodeid} tried to connect to {address!r}."
            )
        return real_connect_ex(sock, address)

    monkeypatch.setattr(socket.socket, "connect", guarded_connect)
    monkeypatch.setattr(socket.socket, "connect_ex", guarded_connect_ex)


def pytest_collection_modifyitems(session: pytest.Session, config: pytest.Config, items) -> None:
    REQUIREMENT_TESTS.clear()
    for item in items:
        for marker in item.iter_markers(name="req"):
            for req_id in marker.args:
                REQUIREMENT_TESTS[str(req_id)].append(item.nodeid)
    # A "full" collection is one started without explicit path or keyword selection.
    args = [a for a in config.args if not a.startswith("-")]
    default_paths = {str(REPO_ROOT / p) for p in config.getini("testpaths")}
    resolved = {str((Path(config.invocation_params.dir) / a).resolve()) for a in args}
    FULL_COLLECTION["value"] = (not args or resolved <= default_paths) and not config.getoption(
        "keyword"
    )
