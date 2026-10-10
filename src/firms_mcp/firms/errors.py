"""Errors raised by the FIRMS client, each with a stable code and a remediation (FR-DATA-007).

Messages never contain a MAP_KEY: upstream text is passed through ``redact()`` first.
"""

from __future__ import annotations

from firms_mcp.redaction import redact


class FirmsError(Exception):
    code = "firms_error"
    retryable = False
    remediation = "Check the request and try again."

    def __init__(self, message: str, *, retry_after_seconds: float | None = None) -> None:
        self.message = redact(message)
        self.retry_after_seconds = retry_after_seconds
        super().__init__(self.message)

    def as_dict(self) -> dict:
        return {
            "error_code": self.code,
            "error_message": self.message,
            "remediation": self.remediation,
            "retryable": self.retryable,
            "retry_after_seconds": self.retry_after_seconds,
        }


class AuthRequired(FirmsError):
    code = "auth_required"
    remediation = (
        "This tool needs the user's FIRMS MAP_KEY. Ask the user to connect their key: remote "
        "servers prompt them through the client's sign-in flow; local servers read "
        "FIRMS_MAP_KEY. A free key can be requested at "
        "https://firms.modaps.eosdis.nasa.gov/api/map_key/. Never ask the user to paste the "
        "key into the conversation."
    )


class InvalidMapKey(FirmsError):
    code = "invalid_map_key"
    remediation = (
        "FIRMS did not accept the MAP_KEY. The user should check the key they connected or "
        "request a new one at https://firms.modaps.eosdis.nasa.gov/api/map_key/."
    )


class MapKeyRejected(FirmsError):
    code = "map_key_rejected"
    retryable = True
    remediation = (
        "FIRMS rejected the MAP_KEY: it is either invalid or has exceeded the limit of 5,000 "
        "transactions per 10 minutes. Wait a few minutes and retry; if it persists, the key "
        "may be invalid."
    )


class RateLimited(FirmsError):
    code = "rate_limited"
    retryable = True
    remediation = (
        "The FIRMS transaction limit for this MAP_KEY (5,000 per 10 minutes) would be "
        "exceeded. Wait before retrying, or narrow the request (smaller area, fewer days, "
        "fewer sources)."
    )


class InvalidRequest(FirmsError):
    code = "invalid_request"
    remediation = "Correct the parameters described in the message and try again."


class UpstreamUnavailable(FirmsError):
    code = "upstream_unavailable"
    retryable = True
    remediation = (
        "FIRMS did not respond successfully. Try again shortly; FIRMS outages are announced "
        "at https://firms.modaps.eosdis.nasa.gov/notifications/firms/outages.html."
    )


class UpstreamFormatError(FirmsError):
    code = "upstream_format"
    remediation = (
        "FIRMS returned a response in an unexpected format. The FIRMS API may have changed; "
        "please report this to the server maintainers."
    )
