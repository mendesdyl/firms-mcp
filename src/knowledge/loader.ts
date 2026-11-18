/**
 * Load, validate, and query the knowledge base (ADR-0005).
 *
 * Content lives in Markdown files with YAML front matter under one or more directories: the
 * repository's `knowledge/` directory, plus any listed in `FIRMS_MCP_KNOWLEDGE_DIRS`. Sources
 * are registered in `sources.yaml`. Loading is strict: any invalid file stops loading with an
 * error that lists every problem found (FR-KB-004).
 */
import { existsSync, readdirSync, readFileSync, statSync } from "node:fs";
import { delimiter, join, relative, resolve, sep } from "node:path";
import { parse } from "yaml";
import { FrontMatterError, split } from "./frontmatter.js";
import {
  contentHash,
  type KnowledgeEntry,
  KnowledgeEntrySchema,
  type KnowledgeSource,
  KnowledgeSourceSchema,
} from "./models.js";
import { type SearchHit, SearchIndex } from "./search.js";

export const KNOWLEDGE_DIRS_ENV = "FIRMS_MCP_KNOWLEDGE_DIRS";
const SOURCES_FILE = "sources.yaml";
const EXCLUDED_DIRS = new Set(["snapshots", "reports", "reference"]);
const EXCLUDED_FILES = new Set(["README.md"]);

export class KnowledgeBaseError extends Error {
  constructor(readonly problems: string[]) {
    super(`invalid knowledge base:\n  - ${problems.join("\n  - ")}`);
  }
}

/** The repository's `knowledge/` directory (the same path from `src/` and from `dist/`). */
export function defaultKnowledgeDir(): string {
  return resolve(import.meta.dirname, "..", "..", "knowledge");
}

/** The default directory plus any extra directories from `FIRMS_MCP_KNOWLEDGE_DIRS`. */
export function configuredKnowledgeDirs(env: NodeJS.ProcessEnv = process.env): string[] {
  const extra = (env[KNOWLEDGE_DIRS_ENV] ?? "")
    .split(delimiter)
    .map((part) => part.trim())
    .filter(Boolean)
    .map((part) => resolve(part.replace(/^~(?=$|\/)/, env.HOME ?? "~")));
  return [defaultKnowledgeDir(), ...extra];
}

export interface Section {
  id: string;
  title: string;
  order: number;
  entry_ids: string[];
}

export interface SearchOptions {
  limit?: number;
  section?: string | undefined;
  kinds?: readonly string[] | undefined;
  includeRetired?: boolean;
}

// FAQ content first, in page order; then supplements in their own order.
function compareEntries(a: KnowledgeEntry, b: KnowledgeEntry): number {
  const family = (e: KnowledgeEntry) => (e.kind.startsWith("faq") ? 0 : 1);
  const text = (x: string, y: string) => (x < y ? -1 : x > y ? 1 : 0);
  return family(a) - family(b) || text(a.source, b.source) || a.order - b.order || text(a.id, b.id);
}

export class KnowledgeBase {
  readonly #ordered: KnowledgeEntry[];
  readonly #index: SearchIndex;

  constructor(
    readonly entries: ReadonlyMap<string, KnowledgeEntry>,
    readonly sources: ReadonlyMap<string, KnowledgeSource>,
  ) {
    this.#ordered = [...entries.values()].sort(compareEntries);
    this.#index = new SearchIndex(this.#ordered);
  }

  get size(): number {
    return this.entries.size;
  }

  ordered({ includeRetired = false } = {}): KnowledgeEntry[] {
    return this.#ordered.filter((entry) => includeRetired || entry.status === "current");
  }

  get(entryId: string): KnowledgeEntry | undefined {
    return this.entries.get(entryId);
  }

  search(query: string, options: SearchOptions = {}): SearchHit[] {
    const { limit = 3, section, kinds, includeRetired = false } = options;
    const kindSet = kinds?.length ? new Set(kinds) : undefined;
    return this.#index.search(query, limit, (entry) => {
      if (!includeRetired && entry.status !== "current") return false;
      if (section && entry.section !== section) return false;
      return !(kindSet && !kindSet.has(entry.kind));
    });
  }

  /** Closest IDs to an unknown ID (prefix first, then token overlap). */
  suggestions(entryId: string, limit = 5): string[] {
    const parts = (id: string) => new Set(id.replaceAll(".", "-").split("-"));
    const wanted = parts(entryId);
    const scored: [number, string][] = [];
    for (const candidate of this.entries.keys()) {
      const overlap = [...parts(candidate)].filter((part) => wanted.has(part)).length;
      const prefix = candidate.startsWith(entryId);
      if (prefix || overlap) scored.push([-(overlap + (prefix ? 10 : 0)), candidate]);
    }
    scored.sort((a, b) => a[0] - b[0] || (a[1] < b[1] ? -1 : a[1] > b[1] ? 1 : 0));
    return scored.slice(0, limit).map(([, candidate]) => candidate);
  }

  sections({ includeRetired = false } = {}): Section[] {
    const result = new Map<string, Section>();
    for (const entry of this.ordered({ includeRetired })) {
      let section = result.get(entry.section);
      if (!section) {
        section = {
          id: entry.section,
          title: entry.section_title,
          order: result.size,
          entry_ids: [],
        };
        result.set(entry.section, section);
      }
      section.entry_ids.push(entry.id);
    }
    return [...result.values()];
  }
}

function markdownFiles(directory: string): string[] {
  return readdirSync(directory, { recursive: true, encoding: "utf8" })
    .filter((name) => name.endsWith(".md"))
    .filter((name) => {
      const [top] = name.split(sep);
      const file = name.split(sep).at(-1) ?? "";
      return !EXCLUDED_DIRS.has(top ?? "") && !EXCLUDED_FILES.has(file);
    })
    .sort()
    .map((name) => join(directory, name));
}

function loadSources(directories: readonly string[], problems: string[]) {
  const sources = new Map<string, KnowledgeSource>();
  for (const directory of directories) {
    const path = join(directory, SOURCES_FILE);
    if (!existsSync(path)) continue;
    const data = (parse(readFileSync(path, "utf8")) ?? {}) as { sources?: unknown[] };
    for (const raw of data.sources ?? []) {
      const id = (raw as { id?: unknown })?.id;
      // YAML 1.2 reads an unquoted date as a string already; normalize Date objects anyway.
      const candidate = { ...(raw as object) } as Record<string, unknown>;
      if (candidate.retrieved instanceof Date) {
        candidate.retrieved = candidate.retrieved.toISOString().slice(0, 10);
      }
      const parsed = KnowledgeSourceSchema.safeParse(candidate);
      if (!parsed.success) {
        problems.push(`${path}: invalid source '${String(id)}': ${parsed.error.message}`);
        continue;
      }
      if (sources.has(parsed.data.id)) {
        problems.push(`${path}: duplicate source id '${parsed.data.id}'`);
        continue;
      }
      sources.set(parsed.data.id, parsed.data);
    }
  }
  return sources;
}

/** Load and validate every entry in `directories`; throw on any problem. */
export function loadKnowledgeBase(
  directories: readonly string[] = configuredKnowledgeDirs(),
): KnowledgeBase {
  const missing = directories.filter((d) => !existsSync(d) || !statSync(d).isDirectory());
  if (missing.length) {
    throw new KnowledgeBaseError(missing.map((d) => `knowledge directory not found: ${d}`));
  }
  const problems: string[] = [];
  const sources = loadSources(directories, problems);
  const entries = new Map<string, KnowledgeEntry>();
  const origins = new Map<string, string>();

  for (const directory of directories) {
    for (const path of markdownFiles(directory)) {
      const shown = relative(process.cwd(), path);
      let meta: Record<string, unknown>;
      let body: string;
      try {
        [meta, body] = split(readFileSync(path, "utf8"));
      } catch (error) {
        if (!(error instanceof FrontMatterError)) throw error;
        problems.push(`${shown}: ${error.message}`);
        continue;
      }
      const parsed = KnowledgeEntrySchema.safeParse({ ...meta, body });
      if (!parsed.success) {
        const details = parsed.error.issues.map((i) => `${i.path.join(".")}: ${i.message}`);
        problems.push(`${shown}: ${details.join("; ")}`);
        continue;
      }
      const entry = parsed.data;
      const actual = contentHash(entry.body);
      if (actual !== entry.content_sha256) {
        problems.push(
          `${shown}: content_sha256 does not match the body (expected ${actual}); if the edit is intentional, update the hash`,
        );
      }
      if (!sources.has(entry.source)) {
        problems.push(`${shown}: unknown source '${entry.source}' (add it to sources.yaml)`);
      }
      const earlier = origins.get(entry.id);
      if (earlier) {
        problems.push(`${shown}: duplicate id '${entry.id}' (also in ${earlier})`);
        continue;
      }
      entries.set(entry.id, entry);
      origins.set(entry.id, shown);
    }
  }

  for (const entry of entries.values()) {
    for (const related of entry.related) {
      if (!entries.has(related)) {
        problems.push(`${origins.get(entry.id)}: related id '${related}' does not exist`);
      }
    }
  }
  if (entries.size === 0 && problems.length === 0) problems.push("no knowledge entries found");
  if (problems.length) throw new KnowledgeBaseError(problems);
  return new KnowledgeBase(entries, sources);
}
