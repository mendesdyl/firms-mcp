"""Knowledge loading, validation, retrieval, and extension (ADR-0005)."""

from __future__ import annotations

import datetime as dt
from pathlib import Path

import pytest

from firms_mcp.knowledge import (
    KnowledgeBaseError,
    KnowledgeEntry,
    content_hash,
    default_knowledge_dir,
    load_knowledge_base,
)
from firms_mcp.knowledge.frontmatter import FrontMatterError, join, split
from firms_mcp.knowledge.loader import KNOWLEDGE_DIRS_ENV, configured_knowledge_dirs

SOURCES = """sources:
  - id: local
    title: Local notes
    publisher: Test
    url: https://example.org
    retrieved: 2026-10-09
    license_note: test
"""


def make_entry(
    entry_id: str = "supplement.local.note",
    body: str = "Some text.",
    *,
    order: int = 0,
    status: str = "current",
    source: str = "local",
    related: list[str] | None = None,
    **raw: object,
) -> str:
    """A valid entry document; ``raw`` overrides front-matter fields without validation."""
    entry = KnowledgeEntry(
        id="supplement.local.note",
        title="A note",
        kind="supplement",
        section="local",
        section_title="Local",
        source=source,
        source_url="https://example.org/note",
        retrieved=dt.date(2026, 10, 9),
        content_sha256=content_hash(body),
        order=order,
        tags=[],
        related=related or [],
        status=status,  # type: ignore[arg-type]
        body=body,
    )
    meta = entry.front_matter()
    meta["id"] = entry_id
    meta.update(raw)
    return join(meta, body)


@pytest.fixture
def kb_dir(tmp_path: Path) -> Path:
    (tmp_path / "sources.yaml").write_text(SOURCES, encoding="utf-8")
    return tmp_path


@pytest.fixture(scope="module")
def repo_kb():
    return load_knowledge_base([default_knowledge_dir()])


# -- the repository's knowledge base ------------------------------------------------


@pytest.mark.req("FR-KB-002")
def test_every_entry_has_provenance(repo_kb) -> None:
    assert len(repo_kb) >= 150
    for entry in repo_kb.ordered(include_retired=True):
        assert entry.source in repo_kb.sources
        assert entry.source_url.startswith("https://")
        assert entry.retrieved >= dt.date(2026, 10, 9)
        assert entry.content_sha256 == content_hash(entry.body)
        assert entry.section and entry.section_title


@pytest.mark.req("FR-KB-007")
def test_table_of_contents_lists_sections_in_page_order(repo_kb) -> None:
    sections = repo_kb.sections()
    ids = [s.id for s in sections]
    assert ids[:4] == ["preamble", "getting-started", "support", "caveats"]
    assert "disclaimers" in ids and "api" in ids
    caveats = next(s for s in sections if s.id == "caveats")
    assert (
        caveats.entry_ids[0] == "faq.caveats.are-there-ever-false-fire-detections-or-data-artifacts"
    )


@pytest.mark.req("FR-KB-006")
def test_get_by_id_and_suggestions(repo_kb) -> None:
    entry = repo_kb.get("faq.getting-started.what-is-utc")
    assert entry is not None and entry.title == "What is UTC?"
    assert repo_kb.get("faq.getting-started.what-is-gmt") is None
    suggestions = repo_kb.suggestions("faq.getting-started.what-is-gmt")
    assert "faq.getting-started.what-is-utc" in suggestions


def test_default_dirs_include_extra_directories(monkeypatch, tmp_path) -> None:
    monkeypatch.setenv(KNOWLEDGE_DIRS_ENV, str(tmp_path))
    assert configured_knowledge_dirs()[-1] == tmp_path


# -- extension mechanism ------------------------------------------------------------


@pytest.mark.req("FR-KB-003")
def test_extra_directory_adds_entries(kb_dir: Path) -> None:
    (kb_dir / "notes").mkdir()
    (kb_dir / "notes" / "note.md").write_text(make_entry(), encoding="utf-8")
    (kb_dir / "README.md").write_text("not an entry", encoding="utf-8")
    kb = load_knowledge_base([default_knowledge_dir(), kb_dir])
    assert kb.get("supplement.local.note").body == "Some text.\n"
    assert kb.sources["local"].publisher == "Test"


@pytest.mark.req("FR-KB-004")
@pytest.mark.parametrize(
    ("content", "problem"),
    [
        ("no front matter", "must start with"),
        ("---\nid: x\n", "not closed"),
        ("---\nid: [unclosed\n---\nbody\n", "invalid YAML"),
        (make_entry(title=""), "title"),
        (make_entry(content_sha256="0" * 64), "content_sha256 does not match"),
        (make_entry(source="unknown"), "unknown source"),
        (make_entry(related=["faq.does-not-exist"]), "related id"),
        (make_entry(kind="essay"), "kind"),
        (make_entry(entry_id="Bad ID"), "id"),
    ],
)
def test_invalid_content_is_rejected(kb_dir: Path, content: str, problem: str) -> None:
    (kb_dir / "bad.md").write_text(content, encoding="utf-8")
    with pytest.raises(KnowledgeBaseError) as error:
        load_knowledge_base([kb_dir])
    assert problem in str(error.value)


@pytest.mark.req("FR-KB-004")
def test_duplicate_ids_are_rejected(kb_dir: Path) -> None:
    (kb_dir / "a.md").write_text(make_entry(), encoding="utf-8")
    (kb_dir / "b.md").write_text(make_entry(), encoding="utf-8")
    with pytest.raises(KnowledgeBaseError, match="duplicate id"):
        load_knowledge_base([kb_dir])


@pytest.mark.req("FR-KB-004")
def test_missing_directory_and_empty_directory(tmp_path: Path) -> None:
    with pytest.raises(KnowledgeBaseError, match="not found"):
        load_knowledge_base([tmp_path / "missing"])
    with pytest.raises(KnowledgeBaseError, match="no knowledge entries"):
        load_knowledge_base([tmp_path])


@pytest.mark.req("FR-KB-004")
def test_duplicate_and_invalid_sources_are_rejected(kb_dir: Path) -> None:
    (kb_dir / "sources.yaml").write_text(
        SOURCES + SOURCES.removeprefix("sources:\n") + "  - id: broken\n", encoding="utf-8"
    )
    (kb_dir / "a.md").write_text(make_entry(), encoding="utf-8")
    with pytest.raises(KnowledgeBaseError) as error:
        load_knowledge_base([kb_dir])
    assert "duplicate source id 'local'" in str(error.value)
    assert "invalid source 'broken'" in str(error.value)


# -- retired content ------------------------------------------------------------------


@pytest.mark.req("FR-KB-009")
def test_retired_entries_are_hidden_from_search_but_retrievable(kb_dir: Path) -> None:
    (kb_dir / "old.md").write_text(
        make_entry("supplement.local.old", "Retired wildfire guidance.", status="retired"),
        encoding="utf-8",
    )
    (kb_dir / "new.md").write_text(
        make_entry("supplement.local.new", "Current wildfire guidance.", order=1), encoding="utf-8"
    )
    kb = load_knowledge_base([kb_dir])
    assert [h.entry.id for h in kb.search("wildfire guidance")] == ["supplement.local.new"]
    assert {h.entry.id for h in kb.search("wildfire guidance", include_retired=True)} == {
        "supplement.local.old",
        "supplement.local.new",
    }
    assert kb.get("supplement.local.old").status == "retired"
    assert [e.id for e in kb.ordered()] == ["supplement.local.new"]


# -- front matter -------------------------------------------------------------------


def test_front_matter_round_trip() -> None:
    text = make_entry(body="Line one.\n\nLine two.")
    meta, body = split(text)
    assert meta["id"] == "supplement.local.note"
    assert body == "Line one.\n\nLine two.\n"
    assert split(join(meta, body)) == (meta, body)
    with pytest.raises(FrontMatterError, match="mapping"):
        split("---\n- a list\n---\nbody\n")


def test_content_hash_ignores_trailing_whitespace_and_crlf() -> None:
    assert content_hash("a  \r\nb\n\n") == content_hash("a\nb")
    assert content_hash("a") != content_hash("b")
