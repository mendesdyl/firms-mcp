/**
 * The knowledge base contains the FIRMS FAQ in full (FR-KB-001, ADR-0005).
 *
 * Until the first automated sync, the reference is the FAQ text the project owner provided on
 * 2026-10-09. NASA rewords answers over time, so from the first sync on, the reference is the
 * FAQ page the sync last parsed (knowledge/snapshots/firms-faq-page.html.gz): its text is read
 * straight from the DOM, without the Markdown converter, and every line must appear in the
 * knowledge base after markup and whitespace normalization.
 */
import { cpSync, existsSync, mkdtempSync, readFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { describe, expect, it } from "vitest";
import { FAQ_URL, parseFaqHtml } from "../../scripts/ts/faq-sync/faq.js";
import { pageReferenceLines } from "../../scripts/ts/faq-sync/reference.js";
import { writeEntries } from "../../scripts/ts/faq-sync/write.js";
import { PAGE_SNAPSHOT, readSaved } from "../../scripts/ts/knowledge.js";
import {
  defaultKnowledgeDir,
  fold,
  type KnowledgeEntry,
  loadKnowledgeBase,
  markdownToPlain,
  missingLines,
} from "../../src/knowledge/index.js";
import { repoKb } from "../unit/knowledge/fixtures.js";

const OWNER_COPY = readFileSync(
  join(defaultKnowledgeDir(), "snapshots", "firms-faq_2026-10-09_owner-provided.txt"),
  "utf8",
);
const SAVED_PAGE = join(defaultKnowledgeDir(), PAGE_SNAPSHOT);
const faqEntries = (kb = repoKb): KnowledgeEntry[] =>
  kb.ordered().filter((e) => e.source === "firms-faq");
const syncedSinceOwnerCopy = faqEntries().some((e) => e.retrieved > "2026-10-09");

describe("FAQ completeness", () => {
  it.skipIf(syncedSinceOwnerCopy)(
    "[REQ-FR-KB-001] contains every line of the owner-provided FAQ (until the first sync)",
    () => {
      expect(missingLines(OWNER_COPY, faqEntries())).toEqual([]);
    },
  );

  it.skipIf(!existsSync(SAVED_PAGE))(
    "[REQ-FR-KB-001] contains every line of the FAQ page as last synced",
    () => {
      const reference = pageReferenceLines(readSaved(SAVED_PAGE)).join("\n");
      expect(missingLines(reference, faqEntries())).toEqual([]);
    },
  );

  it("[REQ-FR-KB-001] a sync of the 2026-11-18 page contains every line of that page", () => {
    const dir = mkdtempSync(join(tmpdir(), "firms-kb-"));
    cpSync(defaultKnowledgeDir(), dir, { recursive: true });
    const html = readSaved("test/fixtures/faq-page_2026-11-18.html.gz");
    writeEntries(parseFaqHtml(html, FAQ_URL), dir, "2026-11-18");
    const kb = loadKnowledgeBase([dir]);
    const reference = pageReferenceLines(html);
    expect(reference.length).toBeGreaterThan(900);
    expect(missingLines(reference.join("\n"), faqEntries(kb))).toEqual([]);
  });

  it("[REQ-FR-KB-001] keeps every question as a separate entry", () => {
    const questions = repoKb.ordered().filter((e) => e.kind === "faq");
    expect(questions.length).toBeGreaterThanOrEqual(137);
    expect(questions.every((e) => e.body.trim())).toBe(true);
    const titles = new Set(questions.map((e) => e.title));
    for (const title of [
      "What does a fire detection mean on the ground?",
      "What is the detection confidence?",
      "Can I estimate burned area from active fire data?",
      "What are the status categories in the Steel Plants layer?",
    ]) {
      expect(titles).toContain(title);
    }
  });

  it("[REQ-FR-KB-001] detects a dropped sentence (the check is not vacuous)", () => {
    const html = readSaved("test/fixtures/faq-page_2026-11-18.html.gz");
    const sentence = "It is a worldwide scientific standard of timekeeping.";
    expect(pageReferenceLines(html).join("\n")).toContain(sentence);
    const entries = faqEntries().map((e) =>
      e.id === "faq.getting-started.what-is-utc" ? { ...e, body: e.body.replace(sentence, "") } : e,
    );
    expect(missingLines(OWNER_COPY, entries).join("\n")).toContain(fold(sentence));
  });

  it("strips only markup when reducing Markdown to plain text", () => {
    const markdown =
      "| A | [B](https://x) |\n|---|---|\n| <sup>1</sup>C | D \\| E |\n- item\\\n![alt](u)";
    expect(markdownToPlain(markdown).split("\n")).toEqual([
      "  A   B  ",
      "  1C   D | E  ",
      "item",
      "alt",
    ]);
  });

  it("keeps the owner-provided copy unmodified", () => {
    expect(
      OWNER_COPY.startsWith("NASA's Fire Information for Resource Management System (FIRMS)"),
    ).toBe(true);
    expect(OWNER_COPY.trimEnd().endsWith("VIIRS\tVisible Infrared Imaging Radiometer Suite")).toBe(
      true,
    );
  });
});
