"""The knowledge base contains the FIRMS FAQ in full (FR-KB-001, ADR-0005).

The reference is the FAQ text provided by the project owner on 2026-10-09
(knowledge/snapshots/firms-faq_2026-10-09_owner-provided.txt). Every non-empty line of
it must appear in the knowledge base after markup and whitespace normalization.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from firms_mcp.knowledge import default_knowledge_dir, load_knowledge_base
from firms_mcp.knowledge.completeness import fold, markdown_to_plain, missing_lines

SNAPSHOT = default_knowledge_dir() / "snapshots" / "firms-faq_2026-10-09_owner-provided.txt"


@pytest.fixture(scope="module")
def kb():
    return load_knowledge_base([default_knowledge_dir()])


@pytest.mark.req("FR-KB-001")
def test_every_line_of_the_owner_provided_faq_is_present(kb) -> None:
    faq_entries = [e for e in kb.ordered() if e.source == "firms-faq"]
    missing = missing_lines(SNAPSHOT.read_text(encoding="utf-8"), faq_entries)
    assert missing == [], "FAQ content missing from the knowledge base:\n" + "\n".join(missing)


@pytest.mark.req("FR-KB-001")
def test_all_137_questions_are_separate_entries(kb) -> None:
    questions = [e for e in kb.ordered() if e.kind == "faq"]
    assert len(questions) == 137
    assert all(e.body.strip() for e in questions)
    titles = {e.title for e in questions}
    for expected in (
        "What does a fire detection mean on the ground?",
        "What is the detection confidence?",
        "Can I estimate burned area from active fire data?",
        "What are the status categories in the Steel Plants layer?",
    ):
        assert expected in titles


@pytest.mark.req("FR-KB-001")
def test_the_check_detects_a_dropped_sentence(kb) -> None:
    """Guard against a vacuous check: removing one sentence must be detected."""
    entries = [e for e in kb.ordered() if e.source == "firms-faq"]
    target = next(e for e in entries if e.id == "faq.getting-started.what-is-utc")
    sentence = "It is a worldwide scientific standard of timekeeping."
    damaged = target.model_copy(update={"body": target.body.replace(sentence, "")})
    others = [e for e in entries if e.id != target.id] + [damaged]
    assert fold(sentence) in "\n".join(missing_lines(SNAPSHOT.read_text(encoding="utf-8"), others))


def test_markdown_to_plain_strips_only_markup() -> None:
    markdown = "| A | [B](https://x) |\n|---|---|\n| <sup>1</sup>C | D \\| E |\n- item\\\n![alt](u)"
    assert markdown_to_plain(markdown).split("\n") == ["  A   B  ", "  1C   D | E  ", "item", "alt"]


def test_snapshot_is_unmodified_reference() -> None:
    text = Path(SNAPSHOT).read_text(encoding="utf-8")
    assert text.startswith("NASA's Fire Information for Resource Management System (FIRMS)")
    assert text.rstrip().endswith("VIIRS\tVisible Infrared Imaging Radiometer Suite")
