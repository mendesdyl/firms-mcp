"""Knowledge-base maintenance commands.

    python -m firms_mcp.knowledge validate [DIR ...]
    python -m firms_mcp.knowledge rehash FILE [FILE ...]
    python -m firms_mcp.knowledge sync [--html FILE] [--date YYYY-MM-DD] [--dir DIR]
    python -m firms_mcp.knowledge import-page --url URL (--select CSS | --heading TEXT) ...

``validate`` loads the knowledge base exactly as the server does and reports problems.
``rehash`` updates ``content_sha256`` after an intentional edit of a supplement.
``sync`` regenerates FAQ entries from the live FIRMS FAQ (or a saved HTML file) and writes
a change report to ``knowledge/reports/`` for review. ``import-page`` adds part of any web
page as a verbatim supplement (see docs/developers/ADDING_KNOWLEDGE.md).
"""

from __future__ import annotations

import argparse
import datetime as dt
import sys
from pathlib import Path

from firms_mcp.knowledge.frontmatter import join, split
from firms_mcp.knowledge.loader import (
    KnowledgeBaseError,
    configured_knowledge_dirs,
    default_knowledge_dir,
    load_knowledge_base,
)
from firms_mcp.knowledge.models import KnowledgeEntry, content_hash

USER_AGENT = "firms-mcp-knowledge-sync (python-httpx)"


def _validate(args: argparse.Namespace) -> int:
    dirs = [Path(d) for d in args.dirs] or configured_knowledge_dirs()
    try:
        kb = load_knowledge_base(dirs)
    except KnowledgeBaseError as exc:
        print(exc, file=sys.stderr)
        return 1
    print(f"ok: {len(kb)} entries, {len(kb.sources)} sources, {len(kb.sections())} sections")
    return 0


def _rehash(args: argparse.Namespace) -> int:
    for name in args.files:
        path = Path(name)
        meta, body = split(path.read_text(encoding="utf-8"))
        meta["content_sha256"] = content_hash(body)
        path.write_text(join(meta, body), encoding="utf-8")
        print(f"rehashed {path}")
    return 0


def _sync(args: argparse.Namespace) -> int:
    from firms_mcp.knowledge.sync import FAQ_URL, parse_faq_html, write_entries

    if args.html:
        html = Path(args.html).read_text(encoding="utf-8")
    else:
        import httpx

        response = httpx.get(
            FAQ_URL, headers={"User-Agent": USER_AGENT}, timeout=60, follow_redirects=True
        )
        response.raise_for_status()
        html = response.text
    retrieved = dt.date.fromisoformat(args.date) if args.date else dt.datetime.now(dt.UTC).date()
    knowledge_dir = Path(args.dir) if args.dir else default_knowledge_dir()
    parsed = parse_faq_html(html)
    report = write_entries(parsed, knowledge_dir, retrieved=retrieved)
    reports = knowledge_dir / "reports"
    reports.mkdir(parents=True, exist_ok=True)
    report_path = reports / f"faq-sync-{retrieved.isoformat()}.md"
    report_path.write_text(report.to_markdown(retrieved, FAQ_URL), encoding="utf-8")
    print(
        f"parsed {len(parsed)} entries: {len(report.added)} added, {len(report.changed)} "
        f"changed, {len(report.unchanged)} unchanged, {len(report.retired)} retired; "
        f"report: {report_path}"
    )
    return 0


def _import_page(args: argparse.Namespace) -> int:
    from firms_mcp.knowledge.sync import extract_page_markdown

    if args.html:
        html = Path(args.html).read_text(encoding="utf-8")
    else:
        import httpx

        response = httpx.get(
            args.url, headers={"User-Agent": USER_AGENT}, timeout=60, follow_redirects=True
        )
        response.raise_for_status()
        html = response.text
    body = extract_page_markdown(html, args.url, selector=args.select, heading=args.heading)
    retrieved = dt.date.fromisoformat(args.date) if args.date else dt.datetime.now(dt.UTC).date()
    entry = KnowledgeEntry(
        id=args.id,
        title=args.title,
        kind="supplement",
        section=args.section,
        section_title=args.section_title,
        source=args.source,
        source_url=args.url,
        retrieved=retrieved,
        content_sha256=content_hash(body),
        order=args.order,
        tags=[t for t in (args.tags or "").split(",") if t],
        related=[],
        status="current",
        body=body,
    )
    knowledge_dir = Path(args.dir) if args.dir else default_knowledge_dir()
    out = knowledge_dir / "supplements" / args.section / f"{args.id.split('.')[-1]}.md"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(join(entry.front_matter(), entry.body), encoding="utf-8")
    print(f"wrote {out}")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python -m firms_mcp.knowledge")
    commands = parser.add_subparsers(dest="command", required=True)
    validate = commands.add_parser("validate", help="validate knowledge content")
    validate.add_argument("dirs", nargs="*")
    validate.set_defaults(func=_validate)
    rehash = commands.add_parser("rehash", help="recompute content hashes after an edit")
    rehash.add_argument("files", nargs="+")
    rehash.set_defaults(func=_rehash)
    sync = commands.add_parser("sync", help="regenerate FAQ entries from the FIRMS FAQ page")
    sync.add_argument("--html", help="parse a saved HTML file instead of fetching the page")
    sync.add_argument("--date", help="retrieval date to record (default: today, UTC)")
    sync.add_argument("--dir", help="knowledge directory (default: the repository's knowledge/)")
    sync.set_defaults(func=_sync)
    page = commands.add_parser(
        "import-page", help="add part of a web page as a verbatim supplement entry"
    )
    page.add_argument("--url", required=True, help="page URL (recorded as source_url)")
    page.add_argument("--html", help="parse a saved copy of the page instead of fetching it")
    target = page.add_mutually_exclusive_group(required=True)
    target.add_argument("--select", help="CSS selector of the content to import")
    target.add_argument("--heading", help="import the section under this heading text")
    page.add_argument("--id", required=True, help="entry id, e.g. supplement.api.area")
    page.add_argument("--title", required=True)
    page.add_argument("--section", required=True, help="section id, e.g. api")
    page.add_argument("--section-title", required=True)
    page.add_argument("--source", required=True, help="source id registered in sources.yaml")
    page.add_argument("--order", type=int, default=0)
    page.add_argument("--tags", help="comma-separated tags")
    page.add_argument("--date", help="retrieval date (default: today, UTC)")
    page.add_argument("--dir", help="knowledge directory (default: repository knowledge/)")
    page.set_defaults(func=_import_page)
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
