/** Write parsed FAQ entries and report what changed (ADR-0005, FR-KB-008, FR-KB-009). */
import {
  existsSync,
  mkdirSync,
  readdirSync,
  readFileSync,
  unlinkSync,
  writeFileSync,
} from "node:fs";
import { dirname, join as joinPath } from "node:path";
import { contentHash, join, split } from "../../../src/knowledge/index.js";
import type { ParsedEntry } from "./faq.js";
import { SOURCE_ID } from "./faq.js";

export interface SyncReport {
  added: string[];
  changed: string[];
  unchanged: string[];
  retired: string[];
}

export function reportMarkdown(report: SyncReport, retrieved: string, pageUrl: string): string {
  const lines = [
    `# FAQ sync report — ${retrieved}`,
    "",
    `Source: <${pageUrl}>`,
    "",
    `- Added: ${report.added.length}`,
    `- Changed: ${report.changed.length}`,
    `- Unchanged: ${report.unchanged.length}`,
    `- Retired (no longer on the page): ${report.retired.length}`,
    "",
  ];
  for (const [title, ids] of [
    ["Added", report.added],
    ["Changed", report.changed],
    ["Retired", report.retired],
  ] as const) {
    if (ids.length) lines.push(`## ${title}`, "", ...ids.map((id) => `- \`${id}\``), "");
  }
  return lines.join("\n");
}

export function entryPath(root: string, entryId: string, section: string): string {
  const parts = entryId.split(".");
  const name = parts.length >= 3 ? parts.slice(2).join(".") : (parts.at(-1) ?? entryId);
  return joinPath(root, "faq", section, `${name}.md`);
}

/** IDs of the current (not retired) entries a previous sync wrote. */
export function currentIds(knowledgeDir: string, sourceId = SOURCE_ID): Set<string> {
  return new Set(
    [...existingEntries(knowledgeDir, sourceId)]
      .filter(([, e]) => e.meta.status !== "retired")
      .map(([id]) => id),
  );
}

function existingEntries(knowledgeDir: string, sourceId: string) {
  const faqRoot = joinPath(knowledgeDir, "faq");
  const existing = new Map<string, { path: string; meta: Record<string, unknown>; body: string }>();
  if (!existsSync(faqRoot)) return existing;
  const files = readdirSync(faqRoot, { recursive: true, encoding: "utf8" })
    .filter((name) => name.endsWith(".md"))
    .sort();
  for (const name of files) {
    const path = joinPath(faqRoot, name);
    const [meta, body] = split(readFileSync(path, "utf8"));
    if (meta.source === sourceId) existing.set(String(meta.id), { path, meta, body });
  }
  return existing;
}

/** Write parsed entries; mark previously synced entries missing from the page as retired. */
export function writeEntries(
  parsed: ParsedEntry[],
  knowledgeDir: string,
  retrieved: string,
  options: { sourceId?: string; dryRun?: boolean } = {},
): SyncReport {
  const { sourceId = SOURCE_ID, dryRun = false } = options;
  const report: SyncReport = { added: [], changed: [], unchanged: [], retired: [] };
  const existing = existingEntries(knowledgeDir, sourceId);
  const seen = new Set<string>();
  for (const item of parsed) {
    seen.add(item.id);
    const hash = contentHash(item.body);
    const previous = existing.get(item.id);
    let date = retrieved;
    if (!previous) report.added.push(item.id);
    else if (previous.meta.content_sha256 !== hash || previous.meta.title !== item.title) {
      report.changed.push(item.id);
    } else {
      report.unchanged.push(item.id);
      date = String(previous.meta.retrieved); // keep the original retrieval date
    }
    const frontMatter = {
      id: item.id,
      title: item.title,
      kind: item.kind,
      section: item.section,
      section_title: item.section_title,
      source: sourceId,
      source_url: item.source_url,
      retrieved: date,
      content_sha256: hash,
      order: item.order,
      tags: [...new Set(item.tags)],
      related: [...new Set(item.related)],
      status: "current",
    };
    if (dryRun) continue;
    const path = entryPath(knowledgeDir, item.id, item.section);
    if (previous && previous.path !== path) unlinkSync(previous.path);
    mkdirSync(dirname(path), { recursive: true });
    writeFileSync(path, join(frontMatter, item.body));
  }
  for (const [id, { path, meta, body }] of existing) {
    if (seen.has(id) || meta.status === "retired") continue;
    if (!dryRun) writeFileSync(path, join({ ...meta, status: "retired" }, body));
    report.retired.push(id);
  }
  return report;
}
