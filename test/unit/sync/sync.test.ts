import { createHash } from "node:crypto";
import { existsSync, mkdtempSync, readdirSync, readFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { gunzipSync } from "node:zlib";
import { describe, expect, it } from "vitest";
import { FAQ_URL, parseFaqHtml, slugify } from "../../../scripts/ts/faq-sync/faq.js";
import { checkParsed } from "../../../scripts/ts/faq-sync/guard.js";
import { extractPageMarkdown } from "../../../scripts/ts/faq-sync/page.js";
import { currentIds, reportMarkdown, writeEntries } from "../../../scripts/ts/faq-sync/write.js";
import { PAGE_SNAPSHOT, readSaved } from "../../../scripts/ts/knowledge.js";
import { defaultKnowledgeDir, split } from "../../../src/knowledge/index.js";

const PAGE = "https://example.org/faq";
const minimal = readFileSync("test/fixtures/faq_minimal.html", "utf8");
const parsed = new Map(parseFaqHtml(minimal, PAGE).map((e) => [e.id, e]));
const entry = (id: string) => {
  const found = parsed.get(id);
  if (!found) throw new Error(`no entry ${id}`);
  return found;
};
const tempDir = () => mkdtempSync(join(tmpdir(), "firms-sync-"));

describe("FAQ page conversion", () => {
  it("[REQ-FR-KB-008] produces entries in document order", () => {
    expect([...parsed.keys()]).toEqual([
      "faq.preamble",
      "faq.getting-started.what-is-a-detection",
      "faq.second-section.overview",
      "faq.second-section.second-section-question",
    ]);
    expect([...parsed.values()].map((e) => e.order)).toEqual([0, 1, 2, 3]);
  });

  it("[REQ-FR-KB-008] uses known section IDs and slugs for new sections", () => {
    const detection = entry("faq.getting-started.what-is-a-detection");
    expect(detection.section).toBe("getting-started");
    expect(detection.section_title).toBe("Getting Started");
    expect(entry("faq.second-section.overview").section).toBe("second-section");
  });

  it("[REQ-FR-KB-002] links each entry to its anchor on the page", () => {
    expect(entry("faq.getting-started.what-is-a-detection").source_url).toBe(
      `${PAGE}#heading-accordion-1-1`,
    );
    expect(entry("faq.second-section.overview").source_url).toBe(`${PAGE}#second`);
  });

  it("[REQ-FR-KB-008] keeps answer text verbatim", () => {
    const body = entry("faq.getting-started.what-is-a-detection").body;
    expect(body).toContain(
      "A detection is the center of a pixel. It has **bold** and *italic* text.\\\nSecond line.",
    );
    expect(body).not.toContain("\u200b");
  });

  it("[REQ-FR-KB-008] converts tables, lists, and figures", () => {
    const body = entry("faq.getting-started.what-is-a-detection").body;
    expect(body).toContain("| Product | Latency<sup>4</sup> |");
    expect(body).toContain("| MODIS \\| Aqua | <3 hours<br>(Global) |");
    expect(body).toContain("- First item\n- Second item\n  - Nested item");
    expect(body).toContain("![A figure](https://example.org/full.png)");
    expect(body).toContain("*Image caption:* Figure caption text.");
    expect(body.replace("Image caption", "")).not.toContain("Image Caption");
  });

  it("[REQ-FR-KB-008] makes links absolute and resolves related entries", () => {
    const preamble = entry("faq.preamble");
    expect(preamble.body).toContain("[relative link](https://example.org/data/tools/firms)");
    expect(preamble.body).toContain("#### Contact heading");
    expect(preamble.related).toEqual(["faq.second-section.second-section-question"]);
    const second = entry("faq.second-section.second-section-question");
    expect(second.body).toContain("[email](mailto:help@example.org)");
    expect(second.related).toEqual(["faq.getting-started.what-is-a-detection"]);
    expect(second.body).toContain("1. One\n2. Two");
    expect(second.body).toContain("### Sub heading");
  });

  it("[REQ-FR-KB-008] leaves out navigation and footer", () => {
    const text = [...parsed.values()].map((e) => e.body).join(" ");
    expect(text).not.toContain("Site navigation");
    expect(text).not.toContain("Footer");
  });

  it("slugifies on word boundaries", () => {
    expect(slugify("What is UTC?")).toBe("what-is-utc");
    const long = slugify("word ".repeat(40), 20);
    expect(long.length).toBeLessThanOrEqual(20);
    expect(long.endsWith("-")).toBe(false);
  });
});

describe("parity with iteration 1", () => {
  it("[REQ-FR-KB-008] writes the same files as the Python sync for the 2026-11-18 page", () => {
    const expected = JSON.parse(readFileSync("test/fixtures/faq-sync-parity.json", "utf8")) as {
      files: Record<string, string>;
      report_sha256: string;
    };
    const html = readSaved("test/fixtures/faq-page_2026-11-18.html.gz");
    const dir = tempDir();
    const report = writeEntries(parseFaqHtml(html, FAQ_URL), dir, "2026-11-18");
    const sha = (text: string | Buffer) => createHash("sha256").update(text).digest("hex");
    const written = Object.fromEntries(
      readdirSync(join(dir, "faq"), { recursive: true, encoding: "utf8" })
        .filter((name) => name.endsWith(".md"))
        .sort()
        .map((name) => [join("faq", name), sha(readFileSync(join(dir, "faq", name)))]),
    );
    expect(written).toEqual(expected.files);
    expect(sha(reportMarkdown(report, "2026-11-18", FAQ_URL))).toBe(expected.report_sha256);
  });

  const snapshot = join(defaultKnowledgeDir(), PAGE_SNAPSHOT);
  it.skipIf(!existsSync(snapshot))(
    "[REQ-FR-KB-008] the committed FAQ entries are exactly what the saved page converts to",
    () => {
      const report = writeEntries(parseFaqHtml(readSaved(snapshot)), defaultKnowledgeDir(), "", {
        dryRun: true,
      });
      expect({ added: report.added, changed: report.changed, retired: report.retired }).toEqual({
        added: [],
        changed: [],
        retired: [],
      });
    },
  );
});

describe("writing and reporting", () => {
  it("[REQ-FR-KB-009] reports added, changed, unchanged, and retired entries", () => {
    const dir = tempDir();
    const first = writeEntries(parseFaqHtml(minimal, PAGE), dir, "2026-10-09");
    expect(first.added).toHaveLength(4);
    expect(first.changed).toEqual([]);
    const again = writeEntries(parseFaqHtml(minimal, PAGE), dir, "2026-10-09");
    expect(again.unchanged).toHaveLength(4);

    let changed = minimal.replace("Section introduction text.", "Section introduction, revised.");
    changed =
      changed.slice(0, changed.indexOf('<div class="accordion-item" id="heading-accordion-2-1">')) +
      "</div></div></div></div></body></html>";
    const report = writeEntries(parseFaqHtml(changed, PAGE), dir, "2026-11-01");
    expect(report.changed).toEqual(["faq.second-section.overview"]);
    expect(report.retired).toEqual(["faq.second-section.second-section-question"]);

    const meta = (path: string) => split(readFileSync(join(dir, "faq", path), "utf8"))[0];
    expect(meta("second-section/second-section-question.md").status).toBe("retired");
    expect(meta("getting-started/what-is-a-detection.md").retrieved).toBe("2026-10-09");
    expect(meta("second-section/overview.md").retrieved).toBe("2026-11-01");
    const markdown = reportMarkdown(report, "2026-11-01", PAGE);
    expect(markdown).toContain("- Retired (no longer on the page): 1");
    expect(currentIds(dir).has("faq.second-section.second-section-question")).toBe(false);
  });

  it("[REQ-FR-KB-008] writes nothing on a dry run", () => {
    const dir = tempDir();
    const report = writeEntries(parseFaqHtml(minimal, PAGE), dir, "2026-10-09", { dryRun: true });
    expect(report.added).toHaveLength(4);
    expect(existsSync(join(dir, "faq"))).toBe(false);
  });
});

describe("refusing a broken parse", () => {
  const ids = new Set([...parsed.keys()]);

  it("[REQ-FR-KB-012] refuses a page with no FAQ questions", () => {
    expect(checkParsed([], ids)).toEqual(
      expect.arrayContaining([expect.stringContaining("no FAQ questions found")]),
    );
  });

  it("[REQ-FR-KB-012] refuses retiring a large share of entries unless allowed", () => {
    const kept = [...parsed.values()].filter((e) => e.kind === "faq").slice(0, 1);
    expect(checkParsed(kept, ids).join()).toContain("would be retired");
    expect(checkParsed(kept, ids, true)).toEqual([]);
  });

  it("[REQ-FR-KB-012] refuses empty titles or bodies", () => {
    const [first] = [...parsed.values()].filter((e) => e.kind === "faq");
    if (!first) throw new Error("fixture has no questions");
    expect(checkParsed([{ ...first, body: " " }], new Set()).join()).toContain("empty body");
  });

  it("accepts the real page", () => {
    const html = readSaved("test/fixtures/faq-page_2026-11-18.html.gz");
    expect(checkParsed(parseFaqHtml(html), currentIds(defaultKnowledgeDir()))).toEqual([]);
  });
});

describe("importing part of another page", () => {
  it("[REQ-FR-KB-003] extracts by selector or by heading", () => {
    expect(
      extractPageMarkdown(minimal, PAGE, { selector: "#heading-accordion-2-1 .panel-collapse" }),
    ).toMatch(/^See \[What is a detection\]/);
    expect(extractPageMarkdown(minimal, PAGE, { heading: "Sub heading" })).toBe(
      "Under the sub heading.",
    );
    expect(() => extractPageMarkdown(minimal, PAGE, { selector: ".does-not-exist" })).toThrow();
    expect(() => extractPageMarkdown(minimal, PAGE, { heading: "No such heading" })).toThrow();
    expect(() => extractPageMarkdown(minimal, PAGE, {})).toThrow();
  });
});

describe("compressed snapshots", () => {
  it("reads gzip files", () => {
    expect(
      gunzipSync(readFileSync("test/fixtures/faq-page_2026-11-18.html.gz")).length,
    ).toBeGreaterThan(500_000);
  });
});
