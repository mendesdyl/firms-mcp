"""Keep FIRMS MAP_KEYs out of logs, errors, and tool output (requirement SEC-001).

A MAP_KEY is 32 alphanumeric characters (FIRMS's own pages validate it this way). Keys
appear in FIRMS URLs either as a path segment (``/api/area/csv/<KEY>/…``) or as the
``MAP_KEY`` query parameter. ``redact`` removes both forms and any explicitly registered
secret values; ``RedactingFilter`` applies it to every log record.
"""

from __future__ import annotations

import logging
import re
import threading

PLACEHOLDER = "[MAP_KEY]"
_PATH_KEY = re.compile(
    r"(/api/(?:area|country|data_availability)/(?:csv|html|json)/)[0-9A-Za-z]{32}(?=/|$|\b)"
)
_QUERY_KEY = re.compile(r"(MAP_KEY=)[^&\s\"']+", re.IGNORECASE)
_known: set[str] = set()
_lock = threading.Lock()


def register_secret(value: str | None) -> None:
    """Remember a secret so it is redacted wherever it appears, not only in URLs."""
    if value and len(value) >= 8:
        with _lock:
            _known.add(value)


def redact(text: str) -> str:
    if not text:
        return text
    text = _PATH_KEY.sub(lambda m: m.group(1) + PLACEHOLDER, text)
    text = _QUERY_KEY.sub(lambda m: m.group(1) + PLACEHOLDER, text)
    with _lock:
        secrets = sorted(_known, key=len, reverse=True)
    for secret in secrets:
        text = text.replace(secret, PLACEHOLDER)
    return text


class RedactingFilter(logging.Filter):
    """Redact MAP_KEYs from the message and arguments of every record."""

    def filter(self, record: logging.LogRecord) -> bool:
        try:
            message = record.getMessage()
        except Exception:  # pragma: no cover - malformed record; leave it alone
            return True
        record.msg = redact(message)
        record.args = None
        return True


def install_log_redaction() -> None:
    """Attach the filter to all root handlers and quiet loggers that print full URLs."""
    root = logging.getLogger()
    for handler in root.handlers:
        if not any(isinstance(f, RedactingFilter) for f in handler.filters):
            handler.addFilter(RedactingFilter())
    # httpx/httpcore log every request URL at INFO/DEBUG; FIRMS URLs contain the key.
    for name in ("httpx", "httpcore"):
        logger = logging.getLogger(name)
        logger.setLevel(logging.WARNING)
        if not any(isinstance(f, RedactingFilter) for f in logger.filters):
            logger.addFilter(RedactingFilter())
