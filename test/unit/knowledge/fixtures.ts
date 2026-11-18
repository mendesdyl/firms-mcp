import { mkdtempSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join as joinPath } from "node:path";
import { contentHash, join, loadKnowledgeBase } from "../../../src/knowledge/index.js";

export const SOURCES = `sources:
  - id: local
    title: Local notes
    publisher: Test
    url: https://example.org
    retrieved: 2026-10-09
    license_note: test
`;

/** The repository's knowledge base, loaded once per test file. */
export const repoKb = loadKnowledgeBase();

/** A valid entry document; `raw` overrides front-matter fields without validation. */
export function makeEntry(
  options: {
    id?: string;
    body?: string;
    order?: number;
    status?: string;
    source?: string;
    related?: string[];
    raw?: Record<string, unknown>;
  } = {},
): string {
  const body = options.body ?? "Some text.";
  const meta = {
    id: options.id ?? "supplement.local.note",
    title: "A note",
    kind: "supplement",
    section: "local",
    section_title: "Local",
    source: options.source ?? "local",
    source_url: "https://example.org/note",
    retrieved: "2026-10-09",
    content_sha256: contentHash(body),
    order: options.order ?? 0,
    tags: [],
    related: options.related ?? [],
    status: options.status ?? "current",
    ...options.raw,
  };
  return join(meta, body);
}

/** A fresh knowledge directory with a sources.yaml and the given files. */
export function kbDir(files: Record<string, string> = {}, sources = SOURCES): string {
  const dir = mkdtempSync(joinPath(tmpdir(), "firms-kb-"));
  writeFileSync(joinPath(dir, "sources.yaml"), sources);
  for (const [name, text] of Object.entries(files)) writeFileSync(joinPath(dir, name), text);
  return dir;
}
