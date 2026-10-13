"""The "Connect your FIRMS MAP_KEY" page (ADR-0004 §2; FR-AUTH-006, SEC-003).

A single self-contained page: no scripts, no third-party resources, inline styles pinned
by hash in the Content-Security-Policy, framing forbidden. Every dynamic value is
HTML-escaped. The page says who is asking, where the user will be returned, where the key
goes, and that the service is not NASA's.
"""

from __future__ import annotations

import base64
import hashlib
import re
from html import escape
from urllib.parse import urlsplit

from starlette.responses import HTMLResponse

MAP_KEY_REQUEST_URL = "https://firms.modaps.eosdis.nasa.gov/api/map_key/"

STYLE = """
body{font-family:system-ui,-apple-system,"Segoe UI",sans-serif;margin:0;background:#f6f7f9;color:#1d232b}
main{max-width:34rem;margin:3rem auto;padding:2rem;background:#fff;border:1px solid #d9dde3;border-radius:10px}
h1{font-size:1.4rem;margin:0 0 .25rem}
.label{font-size:.8rem;color:#5b6573;margin:0 0 1.5rem}
.who{background:#f0f3f7;border-radius:6px;padding:.75rem 1rem;margin:1rem 0}
.who strong{word-break:break-all}
.note{font-size:.9rem;color:#3a4350}
.error{background:#fdecec;border:1px solid #f2b8b8;color:#8a1c1c;border-radius:6px;padding:.75rem 1rem}
label{display:block;font-weight:600;margin:1.25rem 0 .4rem}
input[type=password]{width:100%;box-sizing:border-box;font:inherit;font-family:ui-monospace,monospace;padding:.6rem;border:1px solid #9aa4b2;border-radius:6px}
.actions{display:flex;gap:.75rem;margin-top:1.25rem}
button{font:inherit;padding:.6rem 1.2rem;border-radius:6px;border:1px solid #1d4ed8;background:#1d4ed8;color:#fff;cursor:pointer}
button.secondary{background:#fff;color:#1d4ed8}
footer{font-size:.8rem;color:#5b6573;margin-top:2rem;border-top:1px solid #e3e6ea;padding-top:1rem}
"""
STYLE_HASH = base64.b64encode(hashlib.sha256(STYLE.encode("utf-8")).digest()).decode("ascii")
_SAFE_SOURCE = re.compile(r"^[a-z][a-z0-9+.-]*:(//[A-Za-z0-9.\-\[\]:]+)?$")


def content_security_policy(form_target: str | None = None) -> str:
    """CSP for the page. Browsers apply ``form-action`` to the redirect that follows the
    form, so the client's redirect origin is allowed alongside the page's own origin."""
    form_action = "'self'"
    if form_target and _SAFE_SOURCE.match(form_target):
        form_action += f" {form_target}"
    return (
        f"default-src 'none'; style-src 'sha256-{STYLE_HASH}'; form-action {form_action}; "
        "frame-ancestors 'none'; base-uri 'none'"
    )


def security_headers(form_target: str | None = None) -> dict[str, str]:
    return {
        "Content-Security-Policy": content_security_policy(form_target),
        "X-Frame-Options": "DENY",
        "X-Content-Type-Options": "nosniff",
        "Referrer-Policy": "no-referrer",
        "Cache-Control": "no-store",
    }


def redirect_source(redirect_uri: str) -> str | None:
    """The CSP source for a redirect URI: ``scheme://host[:port]`` or ``scheme:``."""
    parts = urlsplit(redirect_uri)
    if not parts.scheme:
        return None
    if parts.netloc:
        return f"{parts.scheme}://{parts.netloc}"
    return f"{parts.scheme}:"


def _page(title: str, body: str, status_code: int, form_target: str | None = None) -> HTMLResponse:
    html = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="referrer" content="no-referrer">
<title>{escape(title)}</title>
<style>{STYLE}</style>
</head>
<body>
<main>
<h1>{escape(title)}</h1>
<p class="label">FIRMS MCP — an independent service that uses NASA FIRMS. It is not operated or endorsed by NASA.</p>
{body}
<footer>Data from NASA FIRMS. FIRMS states: "Do not use for the preservation of life or property."</footer>
</main>
</body>
</html>"""
    return HTMLResponse(html, status_code=status_code, headers=security_headers(form_target))


def render_connect_form(
    *,
    txn: str,
    csrf: str,
    client_name: str,
    client_verified: bool,
    redirect_host: str,
    redirect_uri: str,
    error: str | None = None,
    status_code: int = 200,
) -> HTMLResponse:
    name_note = (
        "verified: the app's identity is its web address"
        if client_verified
        else "name supplied by the app itself"
    )
    error_html = f'<p class="error" role="alert">{escape(error)}</p>' if error else ""
    body = f"""
{error_html}
<div class="who">
<p><strong>{escape(client_name)}</strong> ({escape(name_note)}) wants to get NASA FIRMS fire data for you through this server.</p>
<p class="note">After you connect, you will be returned to <strong>{escape(redirect_host)}</strong>. If you did not start this from that app, close this page.</p>
</div>
<p class="note">Your MAP_KEY is sent only to FIRMS, to check it now and to request the data you ask for. The AI model never sees it, and it is never written into the conversation.</p>
<p class="note">No key yet? <a href="{MAP_KEY_REQUEST_URL}" target="_blank" rel="noopener noreferrer">Request a free FIRMS MAP_KEY</a> (it arrives by email), then come back to this page.</p>
<form method="post" action="/connect" autocomplete="off">
<input type="hidden" name="txn" value="{escape(txn)}">
<input type="hidden" name="csrf" value="{escape(csrf)}">
<label for="map_key">FIRMS MAP_KEY</label>
<input type="password" id="map_key" name="map_key" required maxlength="64" spellcheck="false" autocomplete="off">
<div class="actions">
<button type="submit" name="action" value="connect">Connect</button>
<button type="submit" name="action" value="deny" class="secondary" formnovalidate>Cancel</button>
</div>
</form>
"""
    return _page("Connect your FIRMS MAP_KEY", body, status_code, redirect_source(redirect_uri))


def render_problem(message: str, status_code: int = 400) -> HTMLResponse:
    body = f'<p class="error" role="alert">{escape(message)}</p>'
    return _page("This connection request cannot continue", body, status_code)
