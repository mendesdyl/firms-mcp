"""Verify that knowledge entries contain a reference text in full (requirement FR-KB-001).

The reference is plain text (for example the FAQ as provided by the project owner). The
knowledge base is Markdown. Both are reduced to comparable plain text — markup, link
targets, table pipes, list markers, and whitespace differences removed; typographic
quotes and dashes folded — and every non-empty reference line must then occur in the
knowledge-base text. Nothing is compared approximately: a missing sentence fails.
"""

from __future__ import annotations

import re
import unicodedata
from collections.abc import Iterable

from firms_mcp.knowledge.models import KnowledgeEntry

# Lines that are artifacts of copying a web page (screen-reader labels for figures).
IGNORED_REFERENCE_LINES = frozenset({"Image", "Image Caption"})

_FOLD = str.maketrans(
    {
        "\u201c": '"',  # left double quotation mark
        "\u201d": '"',  # right double quotation mark
        "\u2018": "'",  # left single quotation mark
        "\u2019": "'",  # right single quotation mark
        "\u2013": "-",  # en dash
        "\u2014": "-",  # em dash
        "\u00a0": " ",  # no-break space
        "\u2026": "...",  # horizontal ellipsis
        "\u200b": None,  # zero-width space
        "\u200c": None,  # zero-width non-joiner
        "\u200d": None,  # zero-width joiner
        "\u2060": None,  # word joiner
        "\ufeff": None,  # zero-width no-break space
    }
)
_IMAGE = re.compile(r"!\[([^\]]*)\]\([^)]*\)")
_LINK = re.compile(r"\[((?:[^\[\]]|\[[^\]]*\])*)\]\((?:[^()]|\([^)]*\))*\)")
_TABLE_RULE = re.compile(r"^\|(?:-+\|)+$")


def fold(text: str) -> str:
    """Unicode-normalize, fold quotes/dashes, drop emphasis markers, collapse whitespace."""
    text = unicodedata.normalize("NFKC", text).translate(_FOLD)
    text = text.replace("*", "")
    return re.sub(r"\s+", " ", text).strip()


def markdown_to_plain(markdown: str) -> str:
    """Plain text of an entry body, preserving reading order."""
    lines = []
    for line in markdown.split("\n"):
        stripped = line.strip()
        if _TABLE_RULE.match(stripped):
            continue
        stripped = re.sub(r"^#{1,6}\s+", "", stripped)
        stripped = re.sub(r"^(?:[-+]|\d+\.)\s+", "", stripped)
        stripped = _IMAGE.sub(r"\1", stripped)
        for _ in range(3):  # links may contain images or brackets
            stripped = _LINK.sub(r"\1", stripped)
        stripped = re.sub(r"</?(?:sup|sub)>", "", stripped)
        stripped = stripped.replace("<br>", " ").replace("\\|", "\x00")
        stripped = stripped.replace("|", " ").replace("\x00", "|")
        stripped = stripped.rstrip("\\")
        lines.append(stripped)
    return "\n".join(lines)


def corpus(entries: Iterable[KnowledgeEntry]) -> str:
    """Folded plain text of the given entries (section titles, titles, and bodies)."""
    parts: list[str] = []
    seen_sections: set[str] = set()
    for entry in entries:
        if entry.section not in seen_sections:
            parts.append(entry.section_title)
            seen_sections.add(entry.section)
        parts.append(entry.title)
        parts.append(markdown_to_plain(entry.body))
    return fold(" ".join(parts))


def missing_lines(reference_text: str, entries: Iterable[KnowledgeEntry]) -> list[str]:
    """Reference lines (folded) that do not occur in the knowledge-base text."""
    haystack = corpus(entries)
    missing = []
    for raw in reference_text.split("\n"):
        line = raw.strip()
        if not line or line in IGNORED_REFERENCE_LINES:
            continue
        folded = fold(line)
        if folded and folded not in haystack:
            missing.append(folded)
    return missing
