/**
 * Knowledge-base maintenance (ADR-0005, ADR-0011 §6).
 *
 *   npm run knowledge -- validate [dir ...]
 *       Load and validate (default: the configured directories).
 *   npm run knowledge -- rehash <file ...>
 *       Update content_sha256 after an intentional edit (only that line changes).
 *   npm run knowledge -- sync [--html file] [--date YYYY-MM-DD] [--dir dir] [--allow-large-change]
 *       Regenerate the FAQ entries from the live page (or a saved copy), write a change report,
 *       and save the page itself to snapshots/firms-faq-page.html.gz. Refuses results that look
 *       like a broken parse; nothing is written then.
 *   npm run knowledge -- missing-data [--json file] [--date YYYY-MM-DD] [--dir dir]
 *       Save FIRMS's missing-data table to reference/missing-data.json.
 *   npm run knowledge -- check [--html file] [--strict]
 *       Compare the committed FAQ entries with the live page without writing anything. Prints
 *       what a sync would change; with --strict, exits 1 if anything would.
 *   npm run knowledge -- import-page --url U (--select CSS | --heading TEXT) --id ID --title T
 *       --section S --section-title T --source SRC [--order N] [--tags a,b] [--html file]
 *       Add part of another page as a verbatim supplement entry.
 */
import { existsSync, mkdirSync, readFileSync, writeFileSync } from "node:fs";
import { dirname, join as joinPath, resolve } from "node:path";
import { parseArgs } from "node:util";
import { gunzipSync, gzipSync } from "node:zlib";
import {
  configuredKnowledgeDirs,
  contentHash,
  defaultKnowledgeDir,
  join,
  KnowledgeBaseError,
  loadKnowledgeBase,
  split,
} from "../../src/knowledge/index.js";
import {
  loadMissingData,
  MISSING_DATA_FILE,
  type MissingData,
} from "../../src/knowledge/missing-data.js";
import { FAQ_URL, parseFaqHtml } from "./faq-sync/faq.js";
import { checkParsed } from "./faq-sync/guard.js";
import { MISSING_DATA_FEED, parseMissingData } from "./faq-sync/missing-data.js";
import { extractPageMarkdown } from "./faq-sync/page.js";
import { currentIds, reportMarkdown, writeEntries } from "./faq-sync/write.js";

const USER_AGENT = "firms-mcp-knowledge-sync (+https://github.com/mendesdyl/firms-mcp)";
export const PAGE_SNAPSHOT = joinPath("snapshots", "firms-faq-page.html.gz");

export function rehash(text: string): string {
  const [, body] = split(text);
  if (!/^content_sha256: .*$/m.test(text))
    throw new Error("no content_sha256 line in the front matter");
  return text.replace(/^content_sha256: .*$/m, `content_sha256: ${contentHash(body)}`);
}

async function fetchText(url: string, timeoutMs: number, headers: Record<string, string> = {}) {
  const response = await fetch(url, {
    headers: { "User-Agent": USER_AGENT, ...headers },
    redirect: "follow",
    signal: AbortSignal.timeout(timeoutMs),
  });
  if (!response.ok) throw new Error(`${url} returned HTTP ${response.status}`);
  return response.text();
}

const today = () => new Date().toISOString().slice(0, 10);

/** Read a saved page; `.gz` files are decompressed. */
export function readSaved(file: string): string {
  const bytes = readFileSync(file);
  return file.endsWith(".gz") ? gunzipSync(bytes).toString("utf8") : bytes.toString("utf8");
}

async function sync(args: string[]): Promise<number> {
  const { values } = parseArgs({
    args,
    options: {
      html: { type: "string" },
      date: { type: "string" },
      dir: { type: "string" },
      "allow-large-change": { type: "boolean", default: false },
    },
  });
  const html = values.html ? readSaved(values.html) : await fetchText(FAQ_URL, 60_000);
  const retrieved = values.date ?? today();
  const dir = resolve(values.dir ?? defaultKnowledgeDir());
  const parsed = parseFaqHtml(html);
  const problems = checkParsed(parsed, currentIds(dir), values["allow-large-change"]);
  if (problems.length) {
    console.error(`FAQ sync refused; nothing was written:\n  - ${problems.join("\n  - ")}`);
    return 1;
  }
  const report = writeEntries(parsed, dir, retrieved);
  const summary =
    `parsed ${parsed.length} entries: ${report.added.length} added, ${report.changed.length} changed, ` +
    `${report.unchanged.length} unchanged, ${report.retired.length} retired`;
  const snapshot = joinPath(dir, PAGE_SNAPSHOT);
  const changed = report.added.length + report.changed.length + report.retired.length > 0;
  // The page's HTML changes every week in ways that do not touch the FAQ (scripts, tokens), so
  // the report and the saved page are written only when entries changed. The saved page always
  // converts to the committed entries.
  if (!changed && existsSync(snapshot)) {
    console.error(`${summary}; no changes`);
    return 0;
  }
  const reportPath = joinPath(dir, "reports", `faq-sync-${retrieved}.md`);
  mkdirSync(dirname(reportPath), { recursive: true });
  writeFileSync(reportPath, reportMarkdown(report, retrieved, FAQ_URL));
  mkdirSync(dirname(snapshot), { recursive: true });
  writeFileSync(snapshot, gzipSync(html, { level: 9 }));
  console.error(`${summary}; report: ${reportPath}`);
  return 0;
}

/** One gap per line, so a weekly change reads as a short diff. */
export function formatMissingData(snapshot: MissingData): string {
  const gaps = (list: MissingData["standard"]) =>
    list.map((gap) => `  ${JSON.stringify(gap)}`).join(",\n");
  return [
    "{",
    `"page_url": ${JSON.stringify(snapshot.page_url)},`,
    `"retrieved": ${JSON.stringify(snapshot.retrieved)},`,
    `"standard": [\n${gaps(snapshot.standard)}\n],`,
    `"nrt": [\n${gaps(snapshot.nrt)}\n]`,
    "}",
    "",
  ].join("\n");
}

async function missingData(args: string[]): Promise<number> {
  const { values } = parseArgs({
    args,
    options: { json: { type: "string" }, date: { type: "string" }, dir: { type: "string" } },
  });
  const text = values.json
    ? readFileSync(values.json, "utf8")
    : await fetchText(MISSING_DATA_FEED, 180_000, { "X-Requested-With": "XMLHttpRequest" });
  const snapshot = parseMissingData(JSON.parse(text), values.date ?? today());
  const dir = resolve(values.dir ?? defaultKnowledgeDir());
  const path = joinPath(dir, MISSING_DATA_FILE);
  // `retrieved` is the date of this copy; an unchanged table keeps the earlier copy and date.
  const previous = loadMissingData(dir);
  if (
    previous &&
    JSON.stringify([previous.standard, previous.nrt]) ===
      JSON.stringify([snapshot.standard, snapshot.nrt])
  ) {
    console.error(`missing data: unchanged since ${previous.retrieved}`);
    return 0;
  }
  mkdirSync(dirname(path), { recursive: true });
  writeFileSync(path, formatMissingData(snapshot));
  console.error(
    `missing data: ${snapshot.standard.length} standard and ${snapshot.nrt.length} NRT days; wrote ${path}`,
  );
  return 0;
}

async function check(args: string[]): Promise<number> {
  const { values } = parseArgs({
    args,
    options: { html: { type: "string" }, strict: { type: "boolean", default: false } },
  });
  const html = values.html ? readSaved(values.html) : await fetchText(FAQ_URL, 60_000);
  const dir = defaultKnowledgeDir();
  const parsed = parseFaqHtml(html);
  const problems = checkParsed(parsed, currentIds(dir));
  const report = writeEntries(parsed, dir, today(), { dryRun: true });
  const differs = report.added.length + report.changed.length + report.retired.length > 0;
  for (const problem of problems) console.error(`warning: ${problem}`);
  if (differs) {
    console.error(
      `warning: the committed FAQ differs from the live page (${report.added.length} added, ` +
        `${report.changed.length} changed, ${report.retired.length} retired); ` +
        "the weekly sync pull request will bring the changes for review",
    );
  } else {
    console.error(
      `ok: the committed FAQ matches the live page (${report.unchanged.length} entries)`,
    );
  }
  return values.strict && (differs || problems.length) ? 1 : 0;
}

async function importPage(args: string[]): Promise<number> {
  const { values: v } = parseArgs({
    args,
    options: {
      url: { type: "string" },
      html: { type: "string" },
      select: { type: "string" },
      heading: { type: "string" },
      id: { type: "string" },
      title: { type: "string" },
      section: { type: "string" },
      "section-title": { type: "string" },
      source: { type: "string" },
      order: { type: "string", default: "0" },
      tags: { type: "string", default: "" },
      date: { type: "string" },
      dir: { type: "string" },
    },
  });
  const required = ["url", "id", "title", "section", "section-title", "source"] as const;
  const missing = required.filter((name) => !v[name]);
  if (missing.length || !(v.select || v.heading)) {
    console.error(
      `import-page needs --${[...missing, ...(v.select || v.heading ? [] : ["select or --heading"])].join(", --")}`,
    );
    return 2;
  }
  const url = v.url as string;
  const html = v.html ? readSaved(v.html) : await fetchText(url, 60_000);
  const body = extractPageMarkdown(html, url, {
    ...(v.select ? { selector: v.select } : {}),
    ...(v.heading ? { heading: v.heading } : {}),
  });
  const id = v.id as string;
  const frontMatter = {
    id,
    title: v.title,
    kind: "supplement",
    section: v.section,
    section_title: v["section-title"],
    source: v.source,
    source_url: url,
    retrieved: v.date ?? today(),
    content_sha256: contentHash(body),
    order: Number(v.order),
    tags: (v.tags ?? "").split(",").filter(Boolean),
    related: [],
    status: "current",
  };
  const out = joinPath(
    resolve(v.dir ?? defaultKnowledgeDir()),
    "supplements",
    v.section as string,
    `${id.split(".").at(-1)}.md`,
  );
  mkdirSync(dirname(out), { recursive: true });
  writeFileSync(out, join(frontMatter, body));
  console.error(`wrote ${out}`);
  return 0;
}

function validate(dirs: string[]): number {
  try {
    const kb = loadKnowledgeBase(
      dirs.length ? dirs.map((d) => resolve(d)) : configuredKnowledgeDirs(),
    );
    console.error(
      `ok: ${kb.size} entries, ${kb.sources.size} sources, ${kb.sections().length} sections`,
    );
    return 0;
  } catch (error) {
    if (!(error instanceof KnowledgeBaseError)) throw error;
    console.error(error.message);
    return 1;
  }
}

async function main([command, ...rest]: string[]): Promise<number> {
  switch (command) {
    case "validate":
      return validate(rest);
    case "rehash":
      if (!rest.length) break;
      for (const file of rest) {
        writeFileSync(file, rehash(readFileSync(file, "utf8")));
        console.error(`rehashed ${file}`);
      }
      return 0;
    case "sync":
      return sync(rest);
    case "missing-data":
      return missingData(rest);
    case "check":
      return check(rest);
    case "import-page":
      return importPage(rest);
  }
  console.error(
    "usage: knowledge validate | rehash | sync | missing-data | check | import-page (see the file header)",
  );
  return 2;
}

if (process.argv[1] === import.meta.filename) {
  void main(process.argv.slice(2)).then((code) => {
    process.exitCode = code;
  });
}
