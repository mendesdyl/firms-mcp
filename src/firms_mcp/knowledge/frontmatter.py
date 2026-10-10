"""Read and write Markdown documents with YAML front matter."""

from __future__ import annotations

import yaml

DELIMITER = "---"


class FrontMatterError(ValueError):
    """Raised when a document does not start with a valid YAML front-matter block."""


def split(text: str) -> tuple[dict, str]:
    """Return ``(front_matter, body)`` for a document that starts with ``---``."""
    text = text.replace("\r\n", "\n")
    if not text.startswith(DELIMITER + "\n"):
        raise FrontMatterError("document must start with a '---' front-matter line")
    end = text.find("\n" + DELIMITER + "\n", len(DELIMITER))
    if end == -1:
        raise FrontMatterError("front matter is not closed with a '---' line")
    header = text[len(DELIMITER) + 1 : end]
    body = text[end + len(DELIMITER) + 2 :]
    try:
        data = yaml.safe_load(header) or {}
    except yaml.YAMLError as exc:  # pragma: no cover - message passthrough
        raise FrontMatterError(f"invalid YAML front matter: {exc}") from exc
    if not isinstance(data, dict):
        raise FrontMatterError("front matter must be a mapping")
    return data, body.strip("\n") + "\n"


def join(front_matter: dict, body: str) -> str:
    """Serialize front matter and body into a document."""
    header = yaml.safe_dump(
        front_matter, sort_keys=False, allow_unicode=True, width=1000, default_flow_style=False
    )
    return f"{DELIMITER}\n{header}{DELIMITER}\n\n{body.strip(chr(10))}\n"
