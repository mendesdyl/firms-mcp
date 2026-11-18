/**
 * The knowledge base contains the FIRMS FAQ in full (FR-KB-001, ADR-0005). The reference is
 * the FAQ text the project owner provided on 2026-10-09; every non-empty line of it must
 * appear in the knowledge base after markup and whitespace normalization.
 */
import { readFileSync } from "node:fs";
import { join } from "node:path";
import { describe, expect, it } from "vitest";
import {
  defaultKnowledgeDir,
  fold,
  type KnowledgeEntry,
  markdownToPlain,
  missingLines,
} from "../../src/knowledge/index.js";
import { repoKb } from "../unit/knowledge/fixtures.js";

const SNAPSHOT = readFileSync(
  join(defaultKnowledgeDir(), "snapshots", "firms-faq_2026-10-09_owner-provided.txt"),
  "utf8",
);
const faqEntries = (): KnowledgeEntry[] => repoKb.ordered().filter((e) => e.source === "firms-faq");

describe("FAQ completeness", () => {
  it("[REQ-FR-KB-001] contains every line of the owner-provided FAQ", () => {
    expect(missingLines(SNAPSHOT, faqEntries())).toEqual([]);
  });

  it("[REQ-FR-KB-001] keeps all 137 questions as separate entries", () => {
    const questions = repoKb.ordered().filter((e) => e.kind === "faq");
    expect(questions).toHaveLength(137);
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
    const sentence = "It is a worldwide scientific standard of timekeeping.";
    const entries = faqEntries().map((e) =>
      e.id === "faq.getting-started.what-is-utc" ? { ...e, body: e.body.replace(sentence, "") } : e,
    );
    expect(missingLines(SNAPSHOT, entries).join("\n")).toContain(fold(sentence));
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

  it("uses the unmodified reference snapshot", () => {
    expect(
      SNAPSHOT.startsWith("NASA's Fire Information for Resource Management System (FIRMS)"),
    ).toBe(true);
    expect(SNAPSHOT.trimEnd().endsWith("VIIRS\tVisible Infrared Imaging Radiometer Suite")).toBe(
      true,
    );
  });
});
