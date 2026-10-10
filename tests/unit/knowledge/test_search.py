"""Knowledge search behaviour (FR-KB-005)."""

from __future__ import annotations

import pytest

from firms_mcp.knowledge import default_knowledge_dir, load_knowledge_base
from firms_mcp.knowledge.search import make_snippet, tokenize


@pytest.fixture(scope="module")
def kb():
    return load_knowledge_base([default_knowledge_dir()])


@pytest.mark.req("FR-KB-005")
def test_results_are_deterministic(kb) -> None:
    first = [(h.entry.id, h.score) for h in kb.search("VIIRS confidence", limit=10)]
    second = [(h.entry.id, h.score) for h in kb.search("VIIRS confidence", limit=10)]
    assert first == second
    scores = [score for _, score in first]
    assert scores == sorted(scores, reverse=True)


@pytest.mark.req("FR-KB-005")
def test_hits_carry_the_full_verbatim_body(kb) -> None:
    hit = kb.search("What is UTC?", limit=1)[0]
    entry = kb.get("faq.getting-started.what-is-utc")
    assert hit.entry is entry
    assert hit.entry.body.startswith('UTC is known as "Universal Coordinated Time”')
    assert len(hit.snippet) <= 242


@pytest.mark.req("FR-KB-005")
@pytest.mark.parametrize(
    ("query", "expected"),
    [
        ("what does a fire detection mean on the ground", "faq.getting-started.what-does-a-fire-detection-mean-on-the-ground"),
        ("isolated pixels South Atlantic ocean", "faq.viirs.are-those-few-isolated-fire-pixels-in-the-middle-of-the-south"),
        ("estimate burned area from detections", "faq.caveats.can-i-estimate-burned-area-from-active-fire-data"),
        ("MAP_KEY transaction limit", "supplement.api.map-key"),
        ("time zone UTC", "faq.getting-started.what-is-utc"),
        ("smoke plume parallax", "faq.caveats.are-there-ever-false-fire-detections-or-data-artifacts"),
        ("detection confidence low nominal high", "faq.getting-started.what-is-the-detection-confidence"),
        ("preservation of life or property", "supplement.disclaimers.fire-map-disclaimer"),
    ],
)
def test_caveat_questions_find_the_right_entry(kb, query: str, expected: str) -> None:
    top = [h.entry.id for h in kb.search(query, limit=3)]
    assert expected in top, top


@pytest.mark.req("FR-KB-005")
def test_lay_terms_are_expanded(kb) -> None:
    top = [h.entry.id for h in kb.search("how fast is the data available", limit=5)]
    assert "faq.getting-started.how-often-is-firms-updated" in top


def test_filters_and_empty_queries(kb) -> None:
    assert kb.search("the of and") == []
    assert all(h.entry.section == "viirs" for h in kb.search("pixels", section="viirs", limit=5))
    assert all(h.entry.kind == "supplement" for h in kb.search("API", kinds=["supplement"], limit=5))


def test_tokenizer_and_snippet() -> None:
    assert tokenize("The detections, of VIIRS 375m!") == ["detection", "viirs", "375m"]
    assert tokenize("[link text](https://x.org/a)") == ["link", "text"]
    body = "Alpha. " * 50 + "The South Atlantic Magnetic Anomaly causes it."
    snippet = make_snippet(body, ["atlantic"])
    assert snippet.startswith("…") and "Atlantic" in snippet
