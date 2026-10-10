"""Load, validate, and query the knowledge base (ADR-0005).

Content lives in Markdown files with YAML front matter under one or more directories
(by default the repository's ``knowledge/`` directory, which is also packaged into the
wheel). Sources are registered in ``sources.yaml`` in the first directory. Loading is
strict: any invalid file stops loading with an error that names the file and problem
(requirement FR-KB-004).
"""

from __future__ import annotations

import os
from collections.abc import Iterable, Sequence
from dataclasses import dataclass, field
from importlib import resources
from pathlib import Path

import yaml
from pydantic import ValidationError

from firms_mcp.knowledge.frontmatter import FrontMatterError, split
from firms_mcp.knowledge.models import KnowledgeEntry, KnowledgeSource, content_hash
from firms_mcp.knowledge.search import SearchHit, SearchIndex

KNOWLEDGE_DIRS_ENV = "FIRMS_MCP_KNOWLEDGE_DIRS"
SOURCES_FILE = "sources.yaml"
EXCLUDED_DIRS = {"snapshots", "reports"}
EXCLUDED_FILES = {"README.md"}


class KnowledgeBaseError(ValueError):
    """Raised when knowledge content is invalid. Lists every problem found."""

    def __init__(self, problems: Sequence[str]) -> None:
        self.problems = list(problems)
        super().__init__("invalid knowledge base:\n  - " + "\n  - ".join(self.problems))


def default_knowledge_dir() -> Path:
    """The bundled knowledge directory (wheel) or the repository's ``knowledge/`` (source)."""
    packaged = resources.files("firms_mcp").joinpath("_knowledge")
    if packaged.is_dir():
        return Path(str(packaged))
    return Path(__file__).resolve().parents[3] / "knowledge"


def configured_knowledge_dirs() -> list[Path]:
    """Default directory plus any extra directories from ``FIRMS_MCP_KNOWLEDGE_DIRS``."""
    dirs = [default_knowledge_dir()]
    extra = os.environ.get(KNOWLEDGE_DIRS_ENV, "")
    dirs.extend(Path(p).expanduser() for p in extra.split(os.pathsep) if p.strip())
    return dirs


@dataclass(frozen=True)
class Section:
    id: str
    title: str
    order: int
    entry_ids: list[str] = field(default_factory=list)


@dataclass
class KnowledgeBase:
    entries: dict[str, KnowledgeEntry]
    sources: dict[str, KnowledgeSource]
    _index: SearchIndex = field(init=False, repr=False)

    def __post_init__(self) -> None:
        self._ordered = sorted(self.entries.values(), key=_sort_key)
        self._index = SearchIndex(self._ordered)

    # -- queries ----------------------------------------------------------------
    def __len__(self) -> int:
        return len(self.entries)

    def ordered(self, *, include_retired: bool = False) -> list[KnowledgeEntry]:
        return [e for e in self._ordered if include_retired or e.status == "current"]

    def get(self, entry_id: str) -> KnowledgeEntry | None:
        return self.entries.get(entry_id)

    def search(
        self,
        query: str,
        *,
        limit: int = 3,
        section: str | None = None,
        kinds: Iterable[str] | None = None,
        include_retired: bool = False,
    ) -> list[SearchHit]:
        kind_set = set(kinds) if kinds else None

        def keep(entry: KnowledgeEntry) -> bool:
            if not include_retired and entry.status != "current":
                return False
            if section and entry.section != section:
                return False
            return not (kind_set and entry.kind not in kind_set)

        return self._index.search(query, limit=limit, predicate=keep)

    def suggestions(self, entry_id: str, limit: int = 5) -> list[str]:
        """Closest IDs to an unknown ID (prefix, then token overlap)."""
        wanted = set(entry_id.replace(".", "-").split("-"))
        scored = []
        for candidate in self.entries:
            parts = set(candidate.replace(".", "-").split("-"))
            overlap = len(wanted & parts)
            if candidate.startswith(entry_id) or overlap:
                scored.append((-(overlap + 10 * candidate.startswith(entry_id)), candidate))
        return [c for _, c in sorted(scored)[:limit]]

    def sections(self, *, include_retired: bool = False) -> list[Section]:
        result: dict[str, Section] = {}
        for entry in self.ordered(include_retired=include_retired):
            if entry.section not in result:
                result[entry.section] = Section(
                    id=entry.section, title=entry.section_title, order=len(result)
                )
            result[entry.section].entry_ids.append(entry.id)
        return list(result.values())


def _sort_key(entry: KnowledgeEntry) -> tuple:
    # FAQ content first, in page order; then supplements in their own order.
    family = 0 if entry.kind.startswith("faq") else 1
    return (family, entry.source, entry.order, entry.id)


def _iter_markdown(directory: Path) -> Iterable[Path]:
    for path in sorted(directory.rglob("*.md")):
        relative = path.relative_to(directory)
        if relative.parts[0] in EXCLUDED_DIRS or path.name in EXCLUDED_FILES:
            continue
        yield path


def load_sources(directories: Sequence[Path]) -> tuple[dict[str, KnowledgeSource], list[str]]:
    sources: dict[str, KnowledgeSource] = {}
    problems: list[str] = []
    for directory in directories:
        path = directory / SOURCES_FILE
        if not path.exists():
            continue
        data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        for raw in data.get("sources", []):
            try:
                source = KnowledgeSource.model_validate(raw)
            except ValidationError as exc:
                problems.append(f"{path}: invalid source {raw.get('id')!r}: {exc.errors()}")
                continue
            if source.id in sources:
                problems.append(f"{path}: duplicate source id {source.id!r}")
                continue
            sources[source.id] = source
    return sources, problems


def load_knowledge_base(directories: Sequence[Path] | None = None) -> KnowledgeBase:
    """Load and validate every entry in ``directories``; raise on any problem."""
    directories = list(directories) if directories is not None else configured_knowledge_dirs()
    problems: list[str] = []
    missing = [str(d) for d in directories if not d.is_dir()]
    if missing:
        raise KnowledgeBaseError([f"knowledge directory not found: {d}" for d in missing])

    sources, source_problems = load_sources(directories)
    problems.extend(source_problems)
    entries: dict[str, KnowledgeEntry] = {}
    origins: dict[str, Path] = {}

    for directory in directories:
        for path in _iter_markdown(directory):
            try:
                meta, body = split(path.read_text(encoding="utf-8"))
            except (FrontMatterError, UnicodeDecodeError) as exc:
                problems.append(f"{path}: {exc}")
                continue
            try:
                entry = KnowledgeEntry.model_validate({**meta, "body": body})
            except ValidationError as exc:
                details = "; ".join(
                    f"{'.'.join(str(p) for p in err['loc'])}: {err['msg']}" for err in exc.errors()
                )
                problems.append(f"{path}: {details}")
                continue
            actual = content_hash(entry.body)
            if actual != entry.content_sha256:
                problems.append(
                    f"{path}: content_sha256 does not match the body (expected {actual}); "
                    "if the edit is intentional run `python -m firms_mcp.knowledge rehash`"
                )
            if entry.source not in sources:
                problems.append(f"{path}: unknown source {entry.source!r} (add it to sources.yaml)")
            if entry.id in entries:
                problems.append(f"{path}: duplicate id {entry.id!r} (also in {origins[entry.id]})")
                continue
            entries[entry.id] = entry
            origins[entry.id] = path

    for entry in entries.values():
        for related in entry.related:
            if related not in entries:
                problems.append(f"{origins[entry.id]}: related id {related!r} does not exist")

    if not entries and not problems:
        problems.append("no knowledge entries found")
    if problems:
        raise KnowledgeBaseError(problems)
    return KnowledgeBase(entries=entries, sources=sources)
