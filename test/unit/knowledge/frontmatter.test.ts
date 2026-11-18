import { readdirSync, readFileSync } from "node:fs";
import { join as joinPath } from "node:path";
import { describe, expect, it } from "vitest";
import { defaultKnowledgeDir, join, split } from "../../../src/knowledge/index.js";

const files = readdirSync(defaultKnowledgeDir(), { recursive: true, encoding: "utf8" })
  .filter((name) => name.endsWith(".md") && !name.startsWith("reports") && name !== "README.md")
  .map((name) => joinPath(defaultKnowledgeDir(), name));

describe("front matter writer", () => {
  it("[REQ-FR-KB-008] rewrites every existing entry byte for byte", () => {
    expect(files.length).toBeGreaterThanOrEqual(150);
    for (const file of files) {
      const text = readFileSync(file, "utf8");
      const [meta, body] = split(text);
      expect(join(meta, body), file).toBe(text);
    }
  });

  it("quotes strings that YAML would read as something else", () => {
    const out = join(
      {
        a: "2026-10-09",
        b: "FIRMS API: area",
        c: "yes",
        d: "it's",
        e: "- item",
        f: "plain text, with commas",
        g: "#tag",
        h: "a #b",
        i: "",
        j: "1.5",
        k: "ends with:",
      },
      "x",
    );
    expect(out).toContain("a: '2026-10-09'\n");
    expect(out).toContain("b: 'FIRMS API: area'\n");
    expect(out).toContain("c: 'yes'\n");
    expect(out).toContain("d: it's\n");
    expect(out).toContain("e: '- item'\n");
    expect(out).toContain("f: plain text, with commas\n");
    expect(out).toContain("g: '#tag'\n");
    expect(out).toContain("h: 'a #b'\n");
    expect(out).toContain("i: ''\n");
    expect(out).toContain("j: '1.5'\n");
    expect(out).toContain("k: 'ends with:'\n");
  });
});
