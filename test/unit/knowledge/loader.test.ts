import { mkdirSync, mkdtempSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join as joinPath } from "node:path";
import { describe, expect, it } from "vitest";
import {
  configuredKnowledgeDirs,
  contentHash,
  defaultKnowledgeDir,
  FrontMatterError,
  join,
  KnowledgeBaseError,
  loadKnowledgeBase,
  split,
} from "../../../src/knowledge/index.js";
import { kbDir, makeEntry, repoKb, SOURCES } from "./fixtures.js";

function problemsOf(dir: string): string {
  try {
    loadKnowledgeBase([dir]);
  } catch (error) {
    expect(error).toBeInstanceOf(KnowledgeBaseError);
    return (error as Error).message;
  }
  throw new Error("expected the knowledge base to be rejected");
}

describe("the repository's knowledge base", () => {
  it("[REQ-FR-KB-002] gives every entry its source, URL, retrieval date, section, and hash", () => {
    expect(repoKb.size).toBeGreaterThanOrEqual(150);
    for (const entry of repoKb.ordered({ includeRetired: true })) {
      expect(repoKb.sources.has(entry.source)).toBe(true);
      expect(entry.source_url.startsWith("https://")).toBe(true);
      expect(entry.retrieved >= "2026-10-09").toBe(true);
      expect(entry.content_sha256).toBe(contentHash(entry.body));
      expect(entry.section && entry.section_title).toBeTruthy();
    }
  });

  it("[REQ-FR-KB-007] lists sections in page order with their entries", () => {
    const sections = repoKb.sections();
    const ids = sections.map((s) => s.id);
    expect(ids.slice(0, 4)).toEqual(["preamble", "getting-started", "support", "caveats"]);
    expect(ids).toContain("disclaimers");
    expect(ids).toContain("api");
    expect(sections.find((s) => s.id === "caveats")?.entry_ids[0]).toBe(
      "faq.caveats.are-there-ever-false-fire-detections-or-data-artifacts",
    );
  });

  it("[REQ-FR-KB-006] gets entries by ID and suggests IDs for unknown ones", () => {
    expect(repoKb.get("faq.getting-started.what-is-utc")?.title).toBe("What is UTC?");
    expect(repoKb.get("faq.getting-started.what-is-gmt")).toBeUndefined();
    expect(repoKb.suggestions("faq.getting-started.what-is-gmt")).toContain(
      "faq.getting-started.what-is-utc",
    );
  });
});

describe("extension", () => {
  it("[REQ-FR-KB-003] adds entries and sources from extra directories", () => {
    const dir = kbDir({ "README.md": "not an entry" });
    mkdirSync(joinPath(dir, "notes"));
    writeFileSync(joinPath(dir, "notes", "note.md"), makeEntry());
    const kb = loadKnowledgeBase([defaultKnowledgeDir(), dir]);
    expect(kb.get("supplement.local.note")?.body).toBe("Some text.\n");
    expect(kb.sources.get("local")?.publisher).toBe("Test");
  });

  it("[REQ-FR-KB-003] reads extra directories from FIRMS_MCP_KNOWLEDGE_DIRS", () => {
    const dirs = configuredKnowledgeDirs({ FIRMS_MCP_KNOWLEDGE_DIRS: "/a:/b" });
    expect(dirs).toEqual([defaultKnowledgeDir(), "/a", "/b"]);
  });
});

describe("validation", () => {
  const cases: [string, string, string][] = [
    ["no front matter", "no front matter", "must start with"],
    ["unclosed front matter", "---\nid: x\n", "not closed"],
    ["invalid YAML", "---\nid: [unclosed\n---\nbody\n", "invalid YAML"],
    ["empty title", makeEntry({ raw: { title: "" } }), "title"],
    [
      "wrong hash",
      makeEntry({ raw: { content_sha256: "0".repeat(64) } }),
      "content_sha256 does not match",
    ],
    ["unknown source", makeEntry({ source: "unknown" }), "unknown source"],
    ["missing related entry", makeEntry({ related: ["faq.does-not-exist"] }), "related id"],
    ["unknown kind", makeEntry({ raw: { kind: "essay" } }), "kind"],
    ["bad id", makeEntry({ id: "Bad ID" }), "id"],
    ["unknown field", makeEntry({ raw: { author: "me" } }), "author"],
  ];
  for (const [name, content, problem] of cases) {
    it(`[REQ-FR-KB-004] rejects ${name}`, () => {
      expect(problemsOf(kbDir({ "bad.md": content }))).toContain(problem);
    });
  }

  it("[REQ-FR-KB-004] rejects duplicate IDs", () => {
    expect(problemsOf(kbDir({ "a.md": makeEntry(), "b.md": makeEntry() }))).toContain(
      "duplicate id",
    );
  });

  it("[REQ-FR-KB-004] rejects missing and empty directories", () => {
    const empty = mkdtempSync(joinPath(tmpdir(), "firms-kb-"));
    expect(problemsOf(joinPath(empty, "missing"))).toContain("not found");
    expect(problemsOf(empty)).toContain("no knowledge entries");
  });

  it("[REQ-FR-KB-004] rejects duplicate and invalid sources, reporting every problem", () => {
    const sources = `${SOURCES}${SOURCES.replace("sources:\n", "")}  - id: broken\n`;
    const message = problemsOf(kbDir({ "a.md": makeEntry() }, sources));
    expect(message).toContain("duplicate source id 'local'");
    expect(message).toContain("invalid source 'broken'");
  });
});

describe("retired content", () => {
  it("[REQ-FR-KB-009] hides retired entries from search but returns them by ID", () => {
    const kb = loadKnowledgeBase([
      kbDir({
        "old.md": makeEntry({
          id: "supplement.local.old",
          body: "Retired wildfire guidance.",
          status: "retired",
        }),
        "new.md": makeEntry({
          id: "supplement.local.new",
          body: "Current wildfire guidance.",
          order: 1,
        }),
      }),
    ]);
    expect(kb.search("wildfire guidance").map((h) => h.entry.id)).toEqual(["supplement.local.new"]);
    expect(
      new Set(kb.search("wildfire guidance", { includeRetired: true }).map((h) => h.entry.id)),
    ).toEqual(new Set(["supplement.local.old", "supplement.local.new"]));
    expect(kb.get("supplement.local.old")?.status).toBe("retired");
    expect(kb.ordered().map((e) => e.id)).toEqual(["supplement.local.new"]);
  });
});

describe("front matter and hashing", () => {
  it("round-trips a document", () => {
    const text = makeEntry({ body: "Line one.\n\nLine two." });
    const [meta, body] = split(text);
    expect(meta.id).toBe("supplement.local.note");
    expect(body).toBe("Line one.\n\nLine two.\n");
    expect(split(join(meta, body))).toEqual([meta, body]);
    expect(() => split("---\n- a list\n---\nbody\n")).toThrow(FrontMatterError);
  });

  it("ignores trailing whitespace and CRLF when hashing", () => {
    expect(contentHash("a  \r\nb\n\n")).toBe(contentHash("a\nb"));
    expect(contentHash("a")).not.toBe(contentHash("b"));
  });
});

describe("maintenance commands", () => {
  it("rehash updates only the content_sha256 line", async () => {
    const { rehash } = await import("../../../scripts/ts/knowledge.js");
    const original = makeEntry({ body: "Edited text." });
    const stale = original.replace(contentHash("Edited text."), "0".repeat(64));
    expect(rehash(stale)).toBe(original);
  });
});
