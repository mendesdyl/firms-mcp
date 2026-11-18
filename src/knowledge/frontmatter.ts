/** Read and write Markdown documents with YAML front matter. */
import { parse, stringify } from "yaml";

const DELIMITER = "---";

export class FrontMatterError extends Error {}

/** `[frontMatter, body]` for a document that starts with `---`. */
export function split(text: string): [Record<string, unknown>, string] {
  const normalized = text.replaceAll("\r\n", "\n");
  if (!normalized.startsWith(`${DELIMITER}\n`)) {
    throw new FrontMatterError("document must start with a '---' front-matter line");
  }
  const end = normalized.indexOf(`\n${DELIMITER}\n`, DELIMITER.length);
  if (end === -1) throw new FrontMatterError("front matter is not closed with a '---' line");
  const header = normalized.slice(DELIMITER.length + 1, end);
  const body = normalized.slice(end + DELIMITER.length + 2);
  let data: unknown;
  try {
    data = parse(header) ?? {};
  } catch (error) {
    throw new FrontMatterError(`invalid YAML front matter: ${(error as Error).message}`);
  }
  if (typeof data !== "object" || data === null || Array.isArray(data)) {
    throw new FrontMatterError("front matter must be a mapping");
  }
  return [data as Record<string, unknown>, `${body.replace(/^\n+|\n+$/g, "")}\n`];
}

/** Serialize front matter and body into a document. */
export function join(frontMatter: Record<string, unknown>, body: string): string {
  const header = stringify(frontMatter, { lineWidth: 0 });
  return `${DELIMITER}\n${header}${DELIMITER}\n\n${body.replace(/^\n+|\n+$/g, "")}\n`;
}
