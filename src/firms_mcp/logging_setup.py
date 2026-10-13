"""Structured JSON logs on stderr with MAP_KEY redaction (ADR-0002; SEC-001).

stdout is the MCP channel for stdio servers, so logs always go to stderr. Every handler
gets the redacting filter before anything is logged.
"""

from __future__ import annotations

import datetime as dt
import json
import logging
import sys

from firms_mcp.redaction import RedactingFilter, install_log_redaction


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        entry = {
            "time": dt.datetime.fromtimestamp(record.created, dt.UTC).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        if record.exc_info:
            entry["exception"] = self.formatException(record.exc_info)
        return json.dumps(entry, ensure_ascii=False)


def configure_logging(level: str = "INFO") -> None:
    handler = logging.StreamHandler(sys.stderr)
    handler.setFormatter(JsonFormatter())
    handler.addFilter(RedactingFilter())
    root = logging.getLogger()
    root.handlers[:] = [handler]
    root.setLevel(level.upper())
    install_log_redaction()
