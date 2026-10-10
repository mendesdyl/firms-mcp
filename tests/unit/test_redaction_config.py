"""Secret redaction and configuration (SEC-001, FR-AUTH-001)."""

from __future__ import annotations

import logging

import pytest

from firms_mcp.config import Settings
from firms_mcp.redaction import (
    PLACEHOLDER,
    RedactingFilter,
    install_log_redaction,
    redact,
    register_secret,
)
from tests.fixtures.firms_csv import MAP_KEY


@pytest.mark.req("SEC-001")
@pytest.mark.parametrize(
    "text",
    [
        f"GET https://firms.modaps.eosdis.nasa.gov/api/area/csv/{MAP_KEY}/MODIS_NRT/world/1",
        f"GET https://firms.modaps.eosdis.nasa.gov/api/data_availability/csv/{MAP_KEY}/ALL",
        f"GET https://firms.modaps.eosdis.nasa.gov/mapserver/mapkey_status/?MAP_KEY={MAP_KEY}",
        f"https://x/?map_key={MAP_KEY}&other=1",
    ],
)
def test_keys_in_firms_urls_are_redacted(text: str) -> None:
    result = redact(text)
    assert MAP_KEY not in result and PLACEHOLDER in result


@pytest.mark.req("SEC-001")
def test_registered_secrets_are_redacted_anywhere() -> None:
    secret = "zzzz9999yyyy8888xxxx7777wwww6666"
    register_secret(secret)
    assert redact(f"the key is {secret}.") == f"the key is {PLACEHOLDER}."
    register_secret("short")  # too short to be a credential; ignored
    assert redact("short") == "short"


@pytest.mark.req("SEC-001")
def test_logging_filter_and_noisy_http_loggers(caplog) -> None:
    record = logging.LogRecord(
        "x", logging.INFO, __file__, 1, "url %s", (f"/api/area/csv/{MAP_KEY}/MODIS_NRT",), None
    )
    assert RedactingFilter().filter(record)
    assert MAP_KEY not in record.getMessage()
    install_log_redaction()
    assert logging.getLogger("httpx").level >= logging.WARNING
    assert logging.getLogger("httpcore").level >= logging.WARNING


@pytest.mark.req("FR-AUTH-001")
def test_map_key_comes_from_the_environment(monkeypatch) -> None:
    monkeypatch.setenv("FIRMS_MAP_KEY", MAP_KEY)
    settings = Settings(_env_file=None)
    assert settings.map_key is not None
    assert settings.map_key.get_secret_value() == MAP_KEY
    assert MAP_KEY not in repr(settings)


def test_defaults() -> None:
    settings = Settings(_env_file=None)
    assert settings.firms_base_url == "https://firms.modaps.eosdis.nasa.gov"
    assert settings.transaction_budget == 4500
    assert settings.allow_operator_key is False
    assert settings.referral_params is True
