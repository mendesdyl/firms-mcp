"""Deterministic lexical search (BM25) over knowledge entries (ADR-0005)."""

from __future__ import annotations

import math
import re
from collections import Counter
from collections.abc import Callable, Iterable, Sequence
from dataclasses import dataclass

from firms_mcp.knowledge.models import KnowledgeEntry

_TOKEN = re.compile(r"[a-z0-9]+(?:\.[0-9]+)?")
_MARKDOWN_LINK = re.compile(r"!?\[([^\]]*)\]\([^)]*\)")

STOPWORDS = frozenset(
    """a an and are as at be been being but by can do does for from has have how i if in
    into is it its may me my of on or our so such than that the their them then there these
    they this those to too us was we were what when where which who why will with would you
    your""".split()
)

# Domain terms that end in "s" but are not plurals.
UNFOLDED = frozenset({"viirs", "gibs", "omps", "lance", "eosdis"})

# Lay terms an agent may pass through from a user, expanded at half weight. Kept small and
# explicit so ranking stays explainable.
SYNONYMS: dict[str, tuple[str, ...]] = {
    "fast": ("latency", "updated"),
    "quickly": ("latency", "updated"),
    "delay": ("latency", "updated"),
    "latency": ("updated", "real", "time"),
    "dot": ("detection", "pixel", "hotspot"),
    "square": ("pixel", "detection"),
    "point": ("detection", "pixel"),
    "hotspot": ("detection", "pixel"),
    "fake": ("false", "spurious", "artifact"),
    "wrong": ("false", "spurious", "artifact"),
    "timezone": ("utc",),
    "zone": ("utc",),
    "big": ("size", "pixel"),
    "intensity": ("frp", "radiative"),
    "key": ("map_key", "transaction"),
}
EXPANSION_WEIGHT = 0.5

# Field weights: the question/heading matters more than the body (BM25F-style boosting by
# repetition keeps the scorer simple and deterministic).
TITLE_WEIGHT = 3
TAG_WEIGHT = 2
K1 = 1.2
B = 0.75


def tokenize(text: str) -> list[str]:
    """Lower-case alphanumeric tokens without stopwords; plural 's' folded."""
    text = _MARKDOWN_LINK.sub(r"\1", text.lower())
    tokens = []
    for token in _TOKEN.findall(text):
        if token in STOPWORDS:
            continue
        if (
            len(token) > 4
            and token.endswith("s")
            and not token.endswith(("ss", "us", "is"))
            and token not in UNFOLDED
        ):
            token = token[:-1]
        tokens.append(token)
    return tokens


@dataclass(frozen=True)
class SearchHit:
    entry: KnowledgeEntry
    score: float
    snippet: str


class SearchIndex:
    """In-memory BM25 index. Ties are broken by entry order, so results are reproducible."""

    def __init__(self, entries: Sequence[KnowledgeEntry]) -> None:
        self._entries = list(entries)
        self._docs: list[Counter[str]] = []
        self._lengths: list[int] = []
        document_frequency: Counter[str] = Counter()
        for entry in self._entries:
            tokens = (
                tokenize(entry.title) * TITLE_WEIGHT
                + tokenize(" ".join(entry.tags)) * TAG_WEIGHT
                + tokenize(entry.body)
            )
            counts = Counter(tokens)
            self._docs.append(counts)
            self._lengths.append(len(tokens))
            document_frequency.update(counts.keys())
        n = max(len(self._entries), 1)
        self._avg_length = sum(self._lengths) / n if self._lengths else 0.0
        self._idf = {
            term: math.log(1 + (n - df + 0.5) / (df + 0.5))
            for term, df in document_frequency.items()
        }

    def search(
        self,
        query: str,
        *,
        limit: int,
        predicate: Callable[[KnowledgeEntry], bool] | None = None,
    ) -> list[SearchHit]:
        terms = list(dict.fromkeys(tokenize(query)))
        if not terms:
            return []
        weights = dict.fromkeys(terms, 1.0)
        for term in terms:
            for synonym in SYNONYMS.get(term, ()):
                weights.setdefault(synonym, EXPANSION_WEIGHT)
        scored: list[tuple[float, int]] = []
        for index, (entry, counts) in enumerate(zip(self._entries, self._docs, strict=True)):
            if predicate is not None and not predicate(entry):
                continue
            score = 0.0
            length_norm = 1 - B + B * (self._lengths[index] / (self._avg_length or 1))
            for term, weight in weights.items():
                tf = counts.get(term, 0)
                if not tf:
                    continue
                score += weight * self._idf[term] * tf * (K1 + 1) / (tf + K1 * length_norm)
            if score > 0:
                scored.append((score, index))
        scored.sort(key=lambda pair: (-pair[0], self._entries[pair[1]].order, pair[1]))
        return [
            SearchHit(
                entry=self._entries[i],
                score=round(s, 4),
                snippet=make_snippet(self._entries[i].body, terms),
            )
            for s, i in scored[:limit]
        ]


def make_snippet(body: str, terms: Iterable[str], width: int = 240) -> str:
    """First sentence-sized window of the body containing a query term (a navigation aid only)."""
    plain = re.sub(r"\s+", " ", _MARKDOWN_LINK.sub(r"\1", body)).strip()
    lowered = plain.lower()
    positions = [lowered.find(t) for t in terms if lowered.find(t) >= 0]
    start = max(min(positions) - 60, 0) if positions else 0
    snippet = plain[start : start + width].strip()
    prefix = "…" if start > 0 else ""
    suffix = "…" if start + width < len(plain) else ""
    return f"{prefix}{snippet}{suffix}"
