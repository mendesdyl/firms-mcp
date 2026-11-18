/**
 * Deterministic lexical search (BM25) over knowledge entries (ADR-0005). A line-for-line
 * port of iteration 1's ranking, so the same query gives the same order.
 */
import type { KnowledgeEntry } from "./models.js";

const TOKEN = /[a-z0-9]+(?:\.[0-9]+)?/g;
const MARKDOWN_LINK = /!?\[([^\]]*)\]\([^)]*\)/g;

const STOPWORDS = new Set(
  `a an and are as at be been being but by can do does for from has have how i if in
  into is it its may me my of on or our so such than that the their them then there these
  they this those to too us was we were what when where which who why will with would you
  your`.split(/\s+/),
);

/** Domain terms that end in "s" but are not plurals. */
const UNFOLDED = new Set(["viirs", "gibs", "omps", "lance", "eosdis"]);

/**
 * Lay terms an agent may pass through from a user, expanded at half weight. Kept small and
 * explicit so ranking stays explainable.
 */
const SYNONYMS: Record<string, readonly string[]> = {
  fast: ["latency", "updated"],
  quickly: ["latency", "updated"],
  delay: ["latency", "updated"],
  latency: ["updated", "real", "time"],
  dot: ["detection", "pixel", "hotspot"],
  square: ["pixel", "detection"],
  point: ["detection", "pixel"],
  hotspot: ["detection", "pixel"],
  fake: ["false", "spurious", "artifact"],
  wrong: ["false", "spurious", "artifact"],
  timezone: ["utc"],
  zone: ["utc"],
  big: ["size", "pixel"],
  intensity: ["frp", "radiative"],
  key: ["map_key", "transaction"],
};
const EXPANSION_WEIGHT = 0.5;

// Field weights: the question/heading matters more than the body (BM25F-style boosting by
// repetition keeps the scorer simple and deterministic).
const TITLE_WEIGHT = 3;
const TAG_WEIGHT = 2;
const K1 = 1.2;
const B = 0.75;

/** Lower-case alphanumeric tokens without stopwords; plural "s" folded. */
export function tokenize(text: string): string[] {
  const plain = text.toLowerCase().replace(MARKDOWN_LINK, "$1");
  const tokens: string[] = [];
  for (const [match] of plain.matchAll(TOKEN)) {
    if (STOPWORDS.has(match)) continue;
    const folds =
      match.length > 4 && match.endsWith("s") && !/(ss|us|is)$/.test(match) && !UNFOLDED.has(match);
    tokens.push(folds ? match.slice(0, -1) : match);
  }
  return tokens;
}

function counts(tokens: string[]): Map<string, number> {
  const result = new Map<string, number>();
  for (const token of tokens) result.set(token, (result.get(token) ?? 0) + 1);
  return result;
}

export interface SearchHit {
  entry: KnowledgeEntry;
  score: number;
  /** A navigation aid only; the entry body is the content. */
  snippet: string;
}

/** In-memory BM25 index. Ties are broken by entry order, so results are reproducible. */
export class SearchIndex {
  readonly #entries: readonly KnowledgeEntry[];
  readonly #docs: Map<string, number>[] = [];
  readonly #lengths: number[] = [];
  readonly #idf = new Map<string, number>();
  readonly #avgLength: number;

  constructor(entries: readonly KnowledgeEntry[]) {
    this.#entries = entries;
    const documentFrequency = new Map<string, number>();
    for (const entry of entries) {
      const tokens = [
        ...Array.from({ length: TITLE_WEIGHT }, () => tokenize(entry.title)).flat(),
        ...Array.from({ length: TAG_WEIGHT }, () => tokenize(entry.tags.join(" "))).flat(),
        ...tokenize(entry.body),
      ];
      const doc = counts(tokens);
      this.#docs.push(doc);
      this.#lengths.push(tokens.length);
      for (const term of doc.keys()) {
        documentFrequency.set(term, (documentFrequency.get(term) ?? 0) + 1);
      }
    }
    const n = Math.max(entries.length, 1);
    this.#avgLength = this.#lengths.length
      ? this.#lengths.reduce((sum, length) => sum + length, 0) / n
      : 0;
    for (const [term, df] of documentFrequency) {
      this.#idf.set(term, Math.log(1 + (n - df + 0.5) / (df + 0.5)));
    }
  }

  search(
    query: string,
    limit: number,
    predicate?: (entry: KnowledgeEntry) => boolean,
  ): SearchHit[] {
    const terms = [...new Set(tokenize(query))];
    if (terms.length === 0) return [];
    const weights = new Map(terms.map((term) => [term, 1]));
    for (const term of terms) {
      for (const synonym of SYNONYMS[term] ?? []) {
        if (!weights.has(synonym)) weights.set(synonym, EXPANSION_WEIGHT);
      }
    }
    const scored: [number, number][] = [];
    this.#entries.forEach((entry, index) => {
      if (predicate && !predicate(entry)) return;
      const doc = this.#docs[index] as Map<string, number>;
      const lengthNorm = 1 - B + B * ((this.#lengths[index] ?? 0) / (this.#avgLength || 1));
      let score = 0;
      for (const [term, weight] of weights) {
        const tf = doc.get(term) ?? 0;
        if (!tf) continue;
        score += (weight * (this.#idf.get(term) ?? 0) * tf * (K1 + 1)) / (tf + K1 * lengthNorm);
      }
      if (score > 0) scored.push([score, index]);
    });
    const orderOf = (index: number) => (this.#entries[index] as KnowledgeEntry).order;
    scored.sort((a, b) => b[0] - a[0] || orderOf(a[1]) - orderOf(b[1]) || a[1] - b[1]);
    return scored.slice(0, limit).map(([score, index]) => {
      const entry = this.#entries[index] as KnowledgeEntry;
      return {
        entry,
        score: Math.round(score * 10_000) / 10_000,
        snippet: makeSnippet(entry.body, terms),
      };
    });
  }
}

/** The first window of the body containing a query term (a navigation aid only). */
export function makeSnippet(body: string, terms: Iterable<string>, width = 240): string {
  const plain = body.replace(MARKDOWN_LINK, "$1").replace(/\s+/g, " ").trim();
  const lowered = plain.toLowerCase();
  const positions = [...terms].map((term) => lowered.indexOf(term)).filter((at) => at >= 0);
  const start = positions.length ? Math.max(Math.min(...positions) - 60, 0) : 0;
  const snippet = plain.slice(start, start + width).trim();
  return `${start > 0 ? "…" : ""}${snippet}${start + width < plain.length ? "…" : ""}`;
}
