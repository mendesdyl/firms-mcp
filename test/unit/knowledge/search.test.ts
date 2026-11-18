import { readFileSync } from "node:fs";
import { describe, expect, it } from "vitest";
import { makeSnippet, tokenize } from "../../../src/knowledge/index.js";
import { repoKb } from "./fixtures.js";

interface ParityCase {
  query: string;
  section?: string;
  hits: { id: string; score: number; snippet: string }[];
}
const parity = JSON.parse(readFileSync("test/fixtures/search-parity.json", "utf8")) as {
  cases: ParityCase[];
};

describe("search", () => {
  it("[REQ-FR-KB-005] ranks exactly as iteration 1 did", () => {
    for (const c of parity.cases) {
      const hits = repoKb.search(c.query, {
        limit: c.hits.length || 10,
        section: c.section,
      });
      expect(
        hits.map((h) => ({ id: h.entry.id, score: h.score, snippet: h.snippet })),
        c.query,
      ).toEqual(c.hits);
    }
  });

  it("[REQ-FR-KB-005] is deterministic and returns the full verbatim body", () => {
    const first = repoKb
      .search("VIIRS confidence", { limit: 10 })
      .map((h) => [h.entry.id, h.score]);
    expect(
      repoKb.search("VIIRS confidence", { limit: 10 }).map((h) => [h.entry.id, h.score]),
    ).toEqual(first);
    const scores = first.map(([, score]) => score as number);
    expect(scores).toEqual([...scores].sort((a, b) => b - a));
    const [hit] = repoKb.search("What is UTC?", { limit: 1 });
    expect(hit?.entry).toBe(repoKb.get("faq.getting-started.what-is-utc"));
    expect(hit?.entry.body.startsWith('UTC is known as "Universal Coordinated Time”')).toBe(true);
    expect(hit?.snippet.length).toBeLessThanOrEqual(242);
  });

  const caveats: [string, string][] = [
    [
      "what does a fire detection mean on the ground",
      "faq.getting-started.what-does-a-fire-detection-mean-on-the-ground",
    ],
    [
      "isolated pixels South Atlantic ocean",
      "faq.viirs.are-those-few-isolated-fire-pixels-in-the-middle-of-the-south",
    ],
    [
      "estimate burned area from detections",
      "faq.caveats.can-i-estimate-burned-area-from-active-fire-data",
    ],
    ["MAP_KEY transaction limit", "supplement.api.map-key"],
    ["time zone UTC", "faq.getting-started.what-is-utc"],
    ["smoke plume parallax", "faq.caveats.are-there-ever-false-fire-detections-or-data-artifacts"],
    [
      "detection confidence low nominal high",
      "faq.getting-started.what-is-the-detection-confidence",
    ],
    ["preservation of life or property", "supplement.disclaimers.fire-map-disclaimer"],
    [
      "standard processing NRT difference",
      "faq.getting-started.what-are-the-key-differences-between-urt-rt-nrt-and-standard",
    ],
  ];
  for (const [query, expected] of caveats) {
    it(`[REQ-FR-KB-005] finds the right entry for "${query}"`, () => {
      expect(repoKb.search(query, { limit: 3 }).map((h) => h.entry.id)).toContain(expected);
    });
  }

  it("[REQ-FR-KB-005] expands lay terms", () => {
    expect(
      repoKb.search("how fast is the data available", { limit: 5 }).map((h) => h.entry.id),
    ).toContain("faq.getting-started.how-often-is-firms-updated");
  });

  it("filters by section and kind and ignores stopword-only queries", () => {
    expect(repoKb.search("the of and")).toEqual([]);
    const viirs = repoKb.search("pixels", { section: "viirs", limit: 5 });
    expect(viirs.every((h) => h.entry.section === "viirs")).toBe(true);
    const supplements = repoKb.search("API", { kinds: ["supplement"], limit: 5 });
    expect(supplements.every((h) => h.entry.kind === "supplement")).toBe(true);
  });

  it("tokenizes and builds snippets", () => {
    expect(tokenize("The detections, of VIIRS 375m!")).toEqual(["detection", "viirs", "375m"]);
    expect(tokenize("[link text](https://x.org/a)")).toEqual(["link", "text"]);
    const snippet = makeSnippet(
      `${"Alpha. ".repeat(50)}The South Atlantic Magnetic Anomaly causes it.`,
      ["atlantic"],
    );
    expect(snippet.startsWith("…")).toBe(true);
    expect(snippet).toContain("Atlantic");
  });
});
