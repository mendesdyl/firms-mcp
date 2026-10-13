"""FAQ page conversion and refresh (ADR-0005; FR-KB-008, FR-KB-009)."""

from __future__ import annotations

import datetime as dt
from pathlib import Path

import pytest

from firms_mcp.knowledge.frontmatter import split
from firms_mcp.knowledge.sync import (
    extract_page_markdown,
    parse_faq_html,
    slugify,
    write_entries,
)

FIXTURE = Path(__file__).resolve().parents[2] / "fixtures" / "faq_minimal.html"
PAGE = "https://example.org/faq"
DAY = dt.date(2026, 10, 9)


@pytest.fixture
def html() -> str:
    return FIXTURE.read_text(encoding="utf-8")


@pytest.fixture
def parsed(html: str):
    return {e.id: e for e in parse_faq_html(html, page_url=PAGE)}


@pytest.mark.req("FR-KB-008")
def test_entries_follow_document_order(parsed) -> None:
    ids = list(parsed)
    assert ids == [
        "faq.preamble",
        "faq.getting-started.what-is-a-detection",
        "faq.second-section.overview",
        "faq.second-section.second-section-question",
    ]
    assert [parsed[i].order for i in ids] == [0, 1, 2, 3]


@pytest.mark.req("FR-KB-008")
def test_known_and_unknown_section_ids(parsed) -> None:
    detection = parsed["faq.getting-started.what-is-a-detection"]
    assert detection.section == "getting-started"  # mapped by SECTION_IDS
    assert detection.section_title == "Getting Started"
    assert parsed["faq.second-section.overview"].section == "second-section"  # slug fallback


@pytest.mark.req("FR-KB-002", "FR-KB-008")
def test_source_urls_use_page_anchors(parsed) -> None:
    detection = parsed["faq.getting-started.what-is-a-detection"]
    assert detection.source_url == f"{PAGE}#heading-accordion-1-1"
    assert parsed["faq.second-section.overview"].source_url == f"{PAGE}#second"


@pytest.mark.req("FR-KB-008")
def test_answer_text_is_preserved_verbatim(parsed) -> None:
    body = parsed["faq.getting-started.what-is-a-detection"].body
    # nbsp folded to a space, zero-width spaces dropped, emphasis kept, <br> as hard break
    assert (
        "A detection is the center of a pixel. It has **bold** and *italic* text.\\\nSecond line."
        in body
    )
    assert "​" not in body


@pytest.mark.req("FR-KB-008")
def test_tables_lists_and_figures(parsed) -> None:
    body = parsed["faq.getting-started.what-is-a-detection"].body
    assert "| Product | Latency<sup>4</sup> |" in body
    assert "| MODIS \\| Aqua | <3 hours<br>(Global) |" in body
    assert "- First item\n- Second item\n  - Nested item" in body
    assert "![A figure](https://example.org/full.png)" in body
    assert "*Image caption:* Figure caption text." in body
    assert "Image Caption" not in body.replace("Image caption", "")  # hidden labels dropped


@pytest.mark.req("FR-KB-008")
def test_links_are_absolute_and_related_entries_resolved(parsed) -> None:
    preamble = parsed["faq.preamble"]
    assert "[relative link](https://example.org/data/tools/firms)" in preamble.body
    assert "#### Contact heading" in preamble.body
    assert preamble.related == ["faq.second-section.second-section-question"]
    second = parsed["faq.second-section.second-section-question"]
    assert "[email](mailto:help@example.org)" in second.body
    assert second.related == ["faq.getting-started.what-is-a-detection"]
    assert "1. One\n2. Two" in second.body
    assert "### Sub heading" in second.body


@pytest.mark.req("FR-KB-008")
def test_navigation_and_footer_are_excluded(parsed) -> None:
    text = " ".join(e.body for e in parsed.values())
    assert "Site navigation" not in text
    assert "Footer" not in text


@pytest.mark.req("FR-KB-008", "FR-KB-009")
def test_write_entries_reports_added_changed_unchanged_and_retired(html: str, tmp_path) -> None:
    first = write_entries(parse_faq_html(html, page_url=PAGE), tmp_path, retrieved=DAY)
    assert len(first.added) == 4 and not first.changed and not first.retired

    again = write_entries(parse_faq_html(html, page_url=PAGE), tmp_path, retrieved=DAY)
    assert len(again.unchanged) == 4 and not again.added

    changed_html = html.replace("Section introduction text.", "Section introduction, revised.")
    changed_html = changed_html.replace(
        changed_html[
            changed_html.index('<div class="accordion-item" id="heading-accordion-2-1">') :
        ],
        "</div></div></div></div></body></html>",
    )
    later = dt.date(2026, 11, 1)
    report = write_entries(parse_faq_html(changed_html, page_url=PAGE), tmp_path, retrieved=later)
    assert report.changed == ["faq.second-section.overview"]
    assert report.retired == ["faq.second-section.second-section-question"]

    retired_file = tmp_path / "faq" / "second-section" / "second-section-question.md"
    meta, _ = split(retired_file.read_text(encoding="utf-8"))
    assert meta["status"] == "retired"

    unchanged_file = tmp_path / "faq" / "getting-started" / "what-is-a-detection.md"
    meta, _ = split(unchanged_file.read_text(encoding="utf-8"))
    assert meta["retrieved"] == "2026-10-09"  # unchanged content keeps its retrieval date

    changed_file = tmp_path / "faq" / "second-section" / "overview.md"
    meta, _ = split(changed_file.read_text(encoding="utf-8"))
    assert meta["retrieved"] == "2026-11-01"
    assert "## FAQ sync report" not in report.to_markdown(later, PAGE)
    assert "- Retired (no longer on the page): 1" in report.to_markdown(later, PAGE)


@pytest.mark.req("FR-KB-003")
def test_extract_page_markdown_by_selector_and_heading(html: str) -> None:
    by_selector = extract_page_markdown(
        html, PAGE, selector="#heading-accordion-2-1 .panel-collapse"
    )
    assert by_selector.startswith("See [What is a detection]")
    by_heading = extract_page_markdown(html, PAGE, heading="Sub heading")
    assert by_heading == "Under the sub heading."
    with pytest.raises(ValueError):
        extract_page_markdown(html, PAGE, selector=".does-not-exist")
    with pytest.raises(ValueError):
        extract_page_markdown(html, PAGE, heading="No such heading")
    with pytest.raises(ValueError):
        extract_page_markdown(html, PAGE)


def test_slugify_limits_length_on_word_boundaries() -> None:
    assert slugify("What is UTC?") == "what-is-utc"
    long = slugify("word " * 40, max_length=20)
    assert len(long) <= 20 and not long.endswith("-")
