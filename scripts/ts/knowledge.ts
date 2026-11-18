/**
 * Knowledge-base maintenance (ADR-0005).
 *
 *   npm run knowledge -- validate [dir ...]   load and validate (default: configured dirs)
 *   npm run knowledge -- rehash <file ...>    update content_sha256 after an intentional edit
 *
 * `rehash` changes only the `content_sha256` line, so the rest of the file stays as written.
 * The FAQ sync command arrives with the sync port (WK-21).
 */
import { readFileSync, writeFileSync } from "node:fs";
import { resolve } from "node:path";
import {
  configuredKnowledgeDirs,
  contentHash,
  KnowledgeBaseError,
  loadKnowledgeBase,
  split,
} from "../../src/knowledge/index.js";

export function rehash(text: string): string {
  const [, body] = split(text);
  const updated = text.replace(/^content_sha256: .*$/m, `content_sha256: ${contentHash(body)}`);
  if (updated === text && !text.includes(contentHash(body))) {
    throw new Error("no content_sha256 line in the front matter");
  }
  return updated;
}

function main(args: string[]): number {
  const [command, ...rest] = args;
  if (command === "validate") {
    try {
      const kb = loadKnowledgeBase(
        rest.length ? rest.map((d) => resolve(d)) : configuredKnowledgeDirs(),
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
  if (command === "rehash" && rest.length) {
    for (const file of rest) {
      writeFileSync(file, rehash(readFileSync(file, "utf8")));
      console.error(`rehashed ${file}`);
    }
    return 0;
  }
  console.error("usage: knowledge validate [dir ...] | knowledge rehash <file ...>");
  return 2;
}

if (process.argv[1] === import.meta.filename) process.exit(main(process.argv.slice(2)));
