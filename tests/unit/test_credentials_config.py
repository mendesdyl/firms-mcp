"""Credential resolution and server configuration (FR-AUTH-001, FR-AUTH-010, FR-KB-003)."""

from __future__ import annotations

from pathlib import Path

import pytest

from firms_mcp.config import Settings
from firms_mcp.credentials import CredentialMode, MapKeyResolver
from firms_mcp.firms.errors import AuthRequired, InvalidMapKey
from firms_mcp.knowledge import configured_knowledge_dirs, default_knowledge_dir
from firms_mcp.redaction import PLACEHOLDER, redact
from tests.fixtures.firms_csv import MAP_KEY


def settings(**values: object) -> Settings:
    return Settings(_env_file=None, **values)


@pytest.mark.req("FR-AUTH-001")
def test_local_mode_uses_the_environment_key() -> None:
    resolver = MapKeyResolver(settings(FIRMS_MAP_KEY=MAP_KEY), CredentialMode.LOCAL)
    assert resolver.require() == MAP_KEY
    assert redact(f"key {MAP_KEY}") == f"key {PLACEHOLDER}"  # registered for redaction
    with pytest.raises(AuthRequired):
        MapKeyResolver(settings(), CredentialMode.LOCAL).require()
    with pytest.raises(AuthRequired):
        MapKeyResolver(settings(FIRMS_MAP_KEY="   "), CredentialMode.LOCAL).require()


def test_a_malformed_configured_key_is_rejected_without_echoing_it() -> None:
    resolver = MapKeyResolver(settings(FIRMS_MAP_KEY="abc123-not-a-key"), CredentialMode.LOCAL)
    with pytest.raises(InvalidMapKey) as error:
        resolver.require()
    assert "abc123-not-a-key" not in str(error.value)


@pytest.mark.req("FR-AUTH-010")
def test_remote_mode_ignores_the_operator_key_unless_allowed() -> None:
    assert MapKeyResolver(settings(FIRMS_MAP_KEY=MAP_KEY), CredentialMode.REMOTE).resolve() is None
    allowed = settings(FIRMS_MAP_KEY=MAP_KEY, FIRMS_MCP_ALLOW_OPERATOR_KEY=True)
    assert MapKeyResolver(allowed, CredentialMode.REMOTE).resolve() == MAP_KEY


@pytest.mark.req("FR-KB-003")
def test_extra_knowledge_dirs_come_from_settings_including_dotenv(tmp_path: Path) -> None:
    extra = tmp_path / "local-knowledge"
    env_file = tmp_path / ".env"
    env_file.write_text(f"FIRMS_MCP_KNOWLEDGE_DIRS={extra}\n", encoding="utf-8")
    configured = Settings(_env_file=env_file)
    assert configured_knowledge_dirs(configured) == [default_knowledge_dir(), extra]


def test_server_settings_defaults(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("FIRMS_MCP_PORT", "9000")
    configured = settings()
    assert (configured.host, configured.port, configured.log_level) == ("127.0.0.1", 9000, "INFO")
