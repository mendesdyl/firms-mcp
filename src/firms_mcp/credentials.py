"""Which FIRMS MAP_KEY a request uses (ADR-0004).

* **Local** (stdio): the user's own key from ``FIRMS_MAP_KEY`` (FR-AUTH-001).
* **Remote** (Streamable HTTP): the key the user connected through the OAuth connect flow
  (WP8). Until that exists, and for anonymous calls afterwards, a remote server uses the
  operator's ``FIRMS_MAP_KEY`` only when ``FIRMS_MCP_ALLOW_OPERATOR_KEY`` is true, which
  it is not by default (FR-AUTH-010, owner decision OD-04).

The key is never a tool parameter (SEC-002) and is registered for redaction as soon as it
is resolved (SEC-001).
"""

from __future__ import annotations

import re
from enum import StrEnum

from firms_mcp.config import Settings
from firms_mcp.firms.errors import AuthRequired, InvalidMapKey
from firms_mcp.redaction import register_secret

MAP_KEY_PATTERN = re.compile(r"^[0-9A-Za-z]{32}$")
"""FIRMS's own pages validate a MAP_KEY as 32 letters and digits (running list LU-16)."""


class CredentialMode(StrEnum):
    LOCAL = "local"
    REMOTE = "remote"


class MapKeyResolver:
    def __init__(self, settings: Settings, mode: CredentialMode) -> None:
        self.settings = settings
        self.mode = mode

    def _configured_key(self) -> str | None:
        if self.settings.map_key is None:
            return None
        key = self.settings.map_key.get_secret_value().strip()
        if not key:
            return None
        register_secret(key)
        if not MAP_KEY_PATTERN.fullmatch(key):
            raise InvalidMapKey(
                "The FIRMS_MAP_KEY configured for this server is not a FIRMS MAP_KEY "
                "(32 letters and digits)."
            )
        return key

    def resolve(self) -> str | None:
        """The key for the current request, or None if there is none."""
        if self.mode is CredentialMode.LOCAL:
            return self._configured_key()
        if self.settings.allow_operator_key:
            return self._configured_key()
        return None

    def require(self) -> str:
        key = self.resolve()
        if key is None:
            raise AuthRequired("This tool needs a FIRMS MAP_KEY and none is connected.")
        return key
