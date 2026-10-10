"""Convert the live FIRMS FAQ page into verbatim knowledge entries (ADR-0005).

The FAQ page (https://www.earthdata.nasa.gov/data/tools/firms/faq) is a sequence of
section headings (``<h2>``) and accordion items (question button + answer body). This
module walks that structure in document order and produces one entry per question, plus
entries for the page preamble and for any text that sits directly under a section
heading. Answer HTML is converted to Markdown **without editing the text**: links are made
absolute, tables become Markdown tables, and figures keep their alt text and caption.

Requires the optional ``sync`` dependencies (BeautifulSoup): ``uv sync --extra sync``.
"""

from __future__ import annotations

import datetime as dt
import re
from dataclasses import dataclass, field
from pathlib import Path
from urllib.parse import urljoin

from firms_mcp.knowledge.frontmatter import join, split
from firms_mcp.knowledge.models import KnowledgeEntry, content_hash

FAQ_URL = "https://www.earthdata.nasa.gov/data/tools/firms/faq"
SOURCE_ID = "firms-faq"

# Stable, short section IDs for the sections present on 2026-10-09. Sections added to the
# page later fall back to a slug of their title.
SECTION_IDS: dict[str, str] = {
    "Getting Started": "getting-started",
    "Support and Mailing Lists": "support",
    "Caveats to Consider When Using Active Fire Data from FIRMS": "caveats",
    "Questions About VIIRS Active Fire Data": "viirs",
    "Questions About MODIS Active Fire Data": "modis",
    "Questions About Real-Time (RT) and Ultra Real-Time (URT) Active Fire Data": "rt-urt",
    "Geostationary Active Fire Data": "geostationary",
    "Landsat Fire Data": "landsat",
    "Harmonized Landsat Sentinel-2 (HLS) imagery in FIRMS": "hls",
    "FIRMS Fire Map": "fire-map",
    "Satellite Swaths and Coverage": "swaths",
    "Email Alerts": "email-alerts",
    "FIRMS US/Canada": "us-canada",
    "Experimental Mode": "experimental",
    "Static Thermal Anomalies": "static-thermal-anomalies",
    "Acronyms": "acronyms",
}

# Keyword → tag, matched against the question and section title (helps search only).
TAG_KEYWORDS: dict[str, tuple[str, ...]] = {
    "modis": ("modis", "terra", "aqua"),
    "viirs": ("viirs", "suomi", "noaa-20", "noaa-21"),
    "landsat": ("landsat", "oli"),
    "geostationary": ("geostationary", "goes", "meteosat", "himawari", "seviri", "abi", "ahi"),
    "hls": ("hls", "harmonized"),
    "confidence": ("confidence",),
    "latency": ("latency", "real-time", "urt", "nrt", "updated", "how often"),
    "resolution": ("resolution", "pixel", "scan and track", "size"),
    "caveats": ("caveat", "false", "artifact", "missed", "not detected", "canopy", "plume"),
    "frp": ("frp", "radiative"),
    "burned-area": ("burned area", "burn"),
    "perimeter": ("perimeter",),
    "alerts": ("alert",),
    "fire-map": ("fire map", "map viewer"),
    "citation": ("citation", "cite", "restrictions"),
    "attributes": ("attribute", "fields"),
    "smoke": ("smoke", "aerosol", "omps"),
}


class SyncDependencyError(RuntimeError):
    """Raised when the optional HTML parsing dependency is missing."""


def _soup(html: str):
    try:
        from bs4 import BeautifulSoup  # noqa: PLC0415 - optional dependency
    except ImportError as exc:  # pragma: no cover - environment dependent
        raise SyncDependencyError(
            "FAQ sync needs BeautifulSoup: run `uv sync --extra sync`"
        ) from exc
    return BeautifulSoup(html, "html.parser")


def slugify(text: str, max_length: int = 64) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", text.lower().replace("&", " and ")).strip("-")
    if len(slug) <= max_length:
        return slug
    cut = slug[:max_length]
    return cut.rsplit("-", 1)[0] if "-" in cut else cut


# --------------------------------------------------------------------------- HTML → Markdown

BLOCK_TAGS = {
    "p",
    "div",
    "section",
    "article",
    "figure",
    "ul",
    "ol",
    "table",
    "h1",
    "h2",
    "h3",
    "h4",
    "h5",
    "h6",
    "blockquote",
    "figcaption",
}
HARD_BREAK = "\u2028"  # placeholder for <br> until rendering (LINE SEPARATOR)


ZERO_WIDTH = dict.fromkeys(map(ord, "\u200b\u200c\u200d\u2060\ufeff"))


def _collapse(text: str) -> str:
    # Invisible formatting characters (zero-width spaces) carry no content; drop them.
    text = text.translate(ZERO_WIDTH).replace("\u00a0", " ")
    text = re.sub(r"[ \t\r\n\f\v]+", " ", text)
    return text


class MarkdownConverter:
    """Minimal, lossless-for-text HTML → Markdown converter for the FIRMS FAQ markup."""

    def __init__(self, page_url: str) -> None:
        self.page_url = page_url

    # -- links ------------------------------------------------------------------
    def absolute(self, href: str) -> str:
        """Resolve a link against the page it appeared on (mailto/tel left unchanged)."""
        href = href.strip()
        if not href or href.startswith(("mailto:", "tel:")):
            return href
        return urljoin(self.page_url, href)

    # -- inline -----------------------------------------------------------------
    def inline(self, node) -> str:
        from bs4 import Comment, NavigableString  # noqa: PLC0415

        if isinstance(node, Comment):
            return ""
        if isinstance(node, NavigableString):
            return _collapse(str(node))
        name = node.name
        if name == "br":
            return HARD_BREAK
        if _is_hidden_label(node):
            return ""
        if name == "img":
            return self.image(node)
        inner = "".join(self.inline(child) for child in node.children)
        if name == "a":
            href = self.absolute(node.get("href", ""))
            text = inner.strip()
            if not href:
                return inner
            if not text:
                return ""
            return f"{_lead(inner)}[{text}]({href}){_trail(inner)}"
        if name in ("strong", "b"):
            return _wrap(inner, "**")
        if name in ("em", "i"):
            return _wrap(inner, "*")
        if name in ("sup", "sub"):
            return f"<{name}>{inner.strip()}</{name}>" if inner.strip() else ""
        if name == "code":
            return f"`{inner}`" if inner.strip() else inner
        return inner

    def image(self, img) -> str:
        alt = _collapse(img.get("alt", "")).strip()
        parent_link = img.find_parent("a")
        url = (
            parent_link.get("href")
            if parent_link is not None and parent_link.get("href")
            else img.get("src", "")
        )
        return f"![{alt}]({self.absolute(url)})"

    # -- blocks -----------------------------------------------------------------
    def blocks(self, node, depth: int = 0) -> list[str]:
        from bs4 import NavigableString  # noqa: PLC0415

        out: list[str] = []
        buffer: list[str] = []

        def flush() -> None:
            text = _finish_inline("".join(buffer))
            if text:
                out.append(text)
            buffer.clear()

        for child in node.children:
            if isinstance(child, NavigableString):
                buffer.append(self.inline(child))
                continue
            if _is_hidden_label(child):
                continue
            if _is_image_paragraph(child):
                flush()
                out.extend(self.image_paragraph(child))
                continue
            if child.name in BLOCK_TAGS:
                flush()
                out.extend(self.block(child, depth))
            elif child.name == "img":
                flush()
                out.append(self.image(child))
            elif child.name in ("script", "style", "button"):
                continue
            else:
                buffer.append(self.inline(child))
        flush()
        return out

    def block(self, node, depth: int) -> list[str]:
        name = node.name
        if name in ("h1", "h2", "h3", "h4", "h5", "h6"):
            text = _finish_inline("".join(self.inline(c) for c in node.children))
            return [f"{'#' * int(name[1])} {text}"] if text else []
        if name in ("ul", "ol"):
            return [self.list_block(node, depth)]
        if name == "table":
            table = self.table(node)
            return [table] if table else []
        if name == "blockquote":
            inner = self.blocks(node, depth)
            return ["\n".join("> " + line for b in inner for line in b.split("\n"))]
        return self.blocks(node, depth)

    def list_block(self, node, depth: int) -> str:
        ordered = node.name == "ol"
        lines: list[str] = []
        number = 1
        for li in node.find_all("li", recursive=False):
            marker = f"{number}." if ordered else "-"
            number += 1
            parts = self.blocks(li, depth + 1)
            if not parts:
                continue
            indent = " " * (len(marker) + 1)
            first, *rest = parts
            lines.append(f"{marker} " + first.replace("\n", "\n" + indent))
            for part in rest:
                lines.append(indent + part.replace("\n", "\n" + indent))
        return "\n".join(lines)

    def table(self, node) -> str:
        rows = []
        for tr in node.find_all("tr"):
            cells = tr.find_all(["th", "td"], recursive=False)
            rows.append([self.cell(c) for c in cells])
        rows = [r for r in rows if any(c.strip() for c in r)]
        if not rows:
            return ""
        width = max(len(r) for r in rows)
        rows = [r + [""] * (width - len(r)) for r in rows]
        header, *body = rows
        out = ["| " + " | ".join(header) + " |", "|" + "---|" * width]
        out.extend("| " + " | ".join(r) + " |" for r in body)
        return "\n".join(out)

    def cell(self, node) -> str:
        parts = self.blocks(node)
        text = "<br>".join(p.replace("\\\n", "<br>").replace("\n", "<br>") for p in parts)
        return text.replace("|", "\\|").strip()

    def image_paragraph(self, node) -> list[str]:
        out = [self.image(img) for img in node.find_all("img")]
        caption = node.select_one(".field--name-field-image-media-entity-caption .field__item")
        if caption is not None:
            text = " ".join(self.blocks(caption)).strip()
            if text:
                out.append(f"*Image caption:* {text}")
        return out

    def blocks_for(self, node) -> list[str]:
        """Blocks for one top-level node (text, element, or image paragraph)."""
        from bs4 import NavigableString  # noqa: PLC0415

        if isinstance(node, NavigableString):
            text = _finish_inline(self.inline(node))
            return [text] if text else []
        if _is_image_paragraph(node):
            return self.image_paragraph(node)
        if node.name in BLOCK_TAGS:
            return self.block(node, 0)
        text = _finish_inline(self.inline(node))
        return [text] if text else []

    def convert(self, node) -> str:
        return "\n\n".join(b for b in self.blocks(node) if b.strip())


def _lead(text: str) -> str:
    return " " if text[:1].isspace() else ""


def _trail(text: str) -> str:
    return " " if text[-1:].isspace() else ""


def _wrap(inner: str, marker: str) -> str:
    text = inner.strip()
    if not text:
        return inner
    return f"{_lead(inner)}{marker}{text}{marker}{_trail(inner)}"


def _finish_inline(text: str) -> str:
    text = _collapse(text)
    lines = [line.strip() for line in text.split(HARD_BREAK)]
    while lines and not lines[0]:
        lines.pop(0)
    while lines and not lines[-1]:
        lines.pop()
    return "\\\n".join(lines)


def _classes(node) -> list[str]:
    if not hasattr(node, "attrs"):
        return []
    return list(node.get("class") or [])


def _is_hidden_label(node) -> bool:
    classes = _classes(node)
    return "visually-hidden" in classes and "field__label" in classes


def _is_image_paragraph(node) -> bool:
    return "paragraph--type--image-full-width" in _classes(node)


# --------------------------------------------------------------------------- page walk


@dataclass
class ParsedEntry:
    id: str
    title: str
    kind: str
    section: str
    section_title: str
    source_url: str
    order: int
    body: str
    anchor: str | None = None
    tags: list[str] = field(default_factory=list)
    related: list[str] = field(default_factory=list)


def _paragraph_type(node) -> str:
    for cls in node.get("class") or []:
        if cls.startswith("paragraph--type--"):
            return cls.removeprefix("paragraph--type--")
    return ""


def _top_level_paragraphs(content):
    for div in content.find_all("div", class_="paragraph"):
        kind = _paragraph_type(div)
        if kind == "layout-paragraph":
            continue
        parent = div.find_parent("div", class_="paragraph")
        while parent is not None and _paragraph_type(parent) == "layout-paragraph":
            parent = parent.find_parent("div", class_="paragraph")
        if parent is None:
            yield kind, div


def _tags_for(*texts: str) -> list[str]:
    haystack = " ".join(texts).lower()
    return [tag for tag, words in TAG_KEYWORDS.items() if any(w in haystack for w in words)]


def parse_faq_html(html: str, page_url: str = FAQ_URL) -> list[ParsedEntry]:
    """Parse the FAQ page into entries in document order."""
    soup = _soup(html)
    content = soup.select_one(".block-field-blocknodepagefield-content") or soup.body or soup
    converter = MarkdownConverter(page_url)

    entries: list[ParsedEntry] = []
    used_ids: set[str] = set()
    anchors: dict[str, str] = {}
    section_id, section_title, section_anchor = "preamble", "FIRMS FAQ", None
    pending: list = []  # nodes of free text under the current heading
    free_text_count: dict[str, int] = {}

    def unique(candidate: str) -> str:
        result, n = candidate, 2
        while result in used_ids:
            result, n = f"{candidate}-{n}", n + 1
        used_ids.add(result)
        return result

    def flush_pending() -> None:
        if not pending:
            return
        body = "\n\n".join(
            block for node in pending for block in converter.blocks_for(node) if block.strip()
        )
        pending.clear()
        if not body.strip():
            return
        count = free_text_count.get(section_id, 0)
        free_text_count[section_id] = count + 1
        if section_id == "preamble":
            entry_id, kind = "faq.preamble", "faq-preamble"
        else:
            suffix = "overview" if count == 0 else f"overview-{count + 1}"
            entry_id, kind = f"faq.{section_id}.{suffix}", "faq-section-intro"
        url = page_url + (f"#{section_anchor}" if section_anchor else "")
        entries.append(
            ParsedEntry(
                id=unique(entry_id),
                title=section_title,
                kind=kind,
                section=section_id,
                section_title=section_title,
                source_url=url,
                order=len(entries),
                body=body,
                anchor=section_anchor,
                tags=_tags_for(section_title),
            )
        )
        if section_anchor:
            anchors.setdefault(section_anchor, entries[-1].id)

    for kind, paragraph in _top_level_paragraphs(content):
        if kind == "bp-accordion":
            flush_pending()
            for item in paragraph.select(".accordion-item"):
                button = item.select_one("button")
                question = _collapse(button.get_text(" ")).strip() if button else ""
                collapse = item.select_one(".panel-collapse") or item
                body = converter.convert(collapse)
                anchor = item.get("id")
                entry_id = unique(f"faq.{section_id}.{slugify(question)}")
                entries.append(
                    ParsedEntry(
                        id=entry_id,
                        title=question,
                        kind="faq",
                        section=section_id,
                        section_title=section_title,
                        source_url=page_url + (f"#{anchor}" if anchor else ""),
                        order=len(entries),
                        body=body,
                        anchor=anchor,
                        tags=_tags_for(question, section_title),
                    )
                )
                if anchor:
                    anchors[anchor] = entry_id
            continue
        if kind == "image-full-width":
            pending.append(paragraph)
            continue
        # Text paragraph: split on section headings.
        container = paragraph.select_one(".tex2jax_process") or paragraph
        for child in container.children:
            if getattr(child, "name", None) == "h2":
                title = _collapse(child.get_text(" ")).strip()
                if not title:
                    continue  # empty headings exist on the page
                flush_pending()
                section_title = title
                section_id = SECTION_IDS.get(title) or slugify(title)
                section_anchor = child.get("id")
                continue
            pending.append(child)
    flush_pending()

    _resolve_related(entries, anchors, page_url)
    return entries




def _resolve_related(entries: list[ParsedEntry], anchors: dict[str, str], page_url: str) -> None:
    link = re.compile(r"\]\(" + re.escape(page_url) + r"#([^)\s]+)\)")
    for entry in entries:
        for anchor in link.findall(entry.body):
            target = anchors.get(anchor)
            if target and target != entry.id and target not in entry.related:
                entry.related.append(target)


# --------------------------------------------------------------------------- writing


@dataclass
class SyncReport:
    added: list[str] = field(default_factory=list)
    changed: list[str] = field(default_factory=list)
    unchanged: list[str] = field(default_factory=list)
    retired: list[str] = field(default_factory=list)

    def to_markdown(self, retrieved: dt.date, page_url: str) -> str:
        lines = [
            f"# FAQ sync report — {retrieved.isoformat()}",
            "",
            f"Source: <{page_url}>",
            "",
            f"- Added: {len(self.added)}",
            f"- Changed: {len(self.changed)}",
            f"- Unchanged: {len(self.unchanged)}",
            f"- Retired (no longer on the page): {len(self.retired)}",
            "",
        ]
        for title, ids in (
            ("Added", self.added),
            ("Changed", self.changed),
            ("Retired", self.retired),
        ):
            if ids:
                lines += [f"## {title}", ""] + [f"- `{i}`" for i in ids] + [""]
        return "\n".join(lines)


def entry_path(root: Path, entry_id: str, section: str) -> Path:
    name = entry_id.split(".", 2)[-1] if entry_id.count(".") >= 2 else entry_id.split(".")[-1]
    return root / "faq" / section / f"{name}.md"


def write_entries(
    parsed: list[ParsedEntry],
    knowledge_dir: Path,
    *,
    retrieved: dt.date,
    source_id: str = SOURCE_ID,
) -> SyncReport:
    """Write parsed entries; mark previously synced entries missing from the page as retired."""
    report = SyncReport()
    faq_root = knowledge_dir / "faq"
    existing: dict[str, tuple[Path, dict, str]] = {}
    if faq_root.exists():
        for path in sorted(faq_root.rglob("*.md")):
            meta, body = split(path.read_text(encoding="utf-8"))
            if meta.get("source") == source_id:
                existing[meta["id"]] = (path, meta, body)

    seen: set[str] = set()
    for item in parsed:
        seen.add(item.id)
        entry = KnowledgeEntry(
            id=item.id,
            title=item.title,
            kind=item.kind,  # type: ignore[arg-type]
            section=item.section,
            section_title=item.section_title,
            source=source_id,
            source_url=item.source_url,
            retrieved=retrieved,
            content_sha256=content_hash(item.body),
            order=item.order,
            tags=item.tags,
            related=item.related,
            status="current",
            body=item.body,
        )
        previous = existing.get(item.id)
        if previous is None:
            report.added.append(item.id)
        elif previous[1].get("content_sha256") != entry.content_sha256 or previous[1].get(
            "title"
        ) != entry.title:
            report.changed.append(item.id)
        else:
            report.unchanged.append(item.id)
            # Keep the original retrieval date for unchanged content.
            entry = entry.model_copy(
                update={"retrieved": dt.date.fromisoformat(str(previous[1]["retrieved"]))}
            )
        path = entry_path(knowledge_dir, item.id, item.section)
        if previous is not None and previous[0] != path:
            previous[0].unlink()
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(join(entry.front_matter(), entry.body), encoding="utf-8")

    for entry_id, (path, meta, body) in existing.items():
        if entry_id in seen or meta.get("status") == "retired":
            continue
        meta = {**meta, "status": "retired"}
        path.write_text(join(meta, body), encoding="utf-8")
        report.retired.append(entry_id)
    return report


# --------------------------------------------------------------------------- other pages

HEADING_TAGS = ("h1", "h2", "h3", "h4", "h5", "h6")


def extract_page_markdown(
    html: str,
    page_url: str,
    *,
    selector: str | None = None,
    heading: str | None = None,
) -> str:
    """Verbatim Markdown of part of a web page.

    ``selector`` (CSS; may match several elements, kept in document order) or ``heading``
    (the text of a heading; content runs until the next heading of the same or a higher
    level). One of the two is required.
    """
    if not selector and not heading:
        raise ValueError("either selector or heading is required")
    soup = _soup(html)
    for tag in soup(["script", "style", "noscript", "form", "select", "input", "button"]):
        tag.decompose()
    converter = MarkdownConverter(page_url)
    blocks: list[str] = []
    if selector:
        nodes = soup.select(selector)
        if not nodes:
            raise ValueError(f"selector {selector!r} matched nothing")
        for node in nodes:
            blocks.extend(b for b in converter.blocks(node) if b.strip())
    else:
        target = next(
            (
                h
                for h in soup.find_all(HEADING_TAGS)
                if _collapse(h.get_text(" ")).strip() == heading
            ),
            None,
        )
        if target is None:
            raise ValueError(f"heading {heading!r} not found")
        level = int(target.name[1])
        collected: list = []
        for node in target.find_all_next(True):
            if node.name in HEADING_TAGS and int(node.name[1]) <= level:
                break
            if node.name in ("p", "ul", "ol", "table", "figure", "blockquote") and not any(
                parent in collected for parent in node.parents
            ):
                collected.append(node)
        for node in collected:
            blocks.extend(b for b in converter.blocks_for(node) if b.strip())
    if not blocks:
        raise ValueError("no content extracted")
    return "\n\n".join(blocks)
