/** Read and write Markdown documents with YAML front matter. */
import { parse } from "yaml";

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

/**
 * Serialize front matter and body into a document. The YAML is written exactly as
 * iteration 1's PyYAML writer wrote it (`safe_dump(sort_keys=False, allow_unicode=True,
 * width=1000)`), so re-syncing an unchanged entry rewrites the same bytes.
 */
export function join(frontMatter: Record<string, unknown>, body: string): string {
  const header = Object.entries(frontMatter)
    .map(([key, value]) => emitField(key, value))
    .join("");
  return `${DELIMITER}\n${header}${DELIMITER}\n\n${body.replace(/^\n+|\n+$/g, "")}\n`;
}

function emitField(key: string, value: unknown): string {
  if (Array.isArray(value)) {
    if (value.length === 0) return `${key}: []\n`;
    return `${key}:\n${value.map((item) => `- ${emitScalar(item)}\n`).join("")}`;
  }
  return `${key}: ${emitScalar(value)}\n`;
}

// YAML 1.1 implicit types (PyYAML's resolver): a string that would read back as one of these
// must be quoted.
const IMPLICIT = [
  /^(?:yes|Yes|YES|no|No|NO|true|True|TRUE|false|False|FALSE|on|On|ON|off|Off|OFF)$/,
  /^(?:[-+]?(?:[0-9][0-9_]*)\.[0-9_]*(?:[eE][-+][0-9]+)?|\.[0-9][0-9_]*(?:[eE][-+][0-9]+)?|[-+]?[0-9][0-9_]*(?::[0-5]?[0-9])+\.[0-9_]*|[-+]?\.(?:inf|Inf|INF)|\.(?:nan|NaN|NAN))$/,
  /^(?:[-+]?0b[0-1_]+|[-+]?0[0-7_]+|[-+]?(?:0|[1-9][0-9_]*)|[-+]?0x[0-9a-fA-F_]+|[-+]?[1-9][0-9_]*(?::[0-5]?[0-9])+)$/,
  /^(?:<<|=|~|null|Null|NULL|)$/,
  /^(?:[0-9]{4}-[0-9]{1,2}-[0-9]{1,2}(?:[Tt]|[ \t]+)[0-9]{1,2}:[0-9]{2}:[0-9]{2}(?:\.[0-9]*)?(?:[ \t]*(?:Z|[-+][0-9]{1,2}(?::[0-9]{2})?))?|[0-9]{4}-[0-9]{2}-[0-9]{2})$/,
];
const BREAKS = "\0 \t\r\n\u0085\u2028\u2029";
const PRINTABLE = /^[\t\n\r\x20-\x7E\u0085\u00A0-\uD7FF\uE000-\uFFFD\u{10000}-\u{10FFFF}]*$/u;

function emitScalar(value: unknown): string {
  if (value === null || value === undefined) return "null";
  if (typeof value === "boolean") return value ? "true" : "false";
  if (typeof value === "number") return String(value);
  const text = String(value);
  if (!PRINTABLE.test(text) || /[\n\r\u0085\u2028\u2029]/.test(text)) {
    throw new Error(`cannot write ${JSON.stringify(text)} in front matter`);
  }
  return plainAllowed(text) ? text : `'${text.replaceAll("'", "''")}'`;
}

/** PyYAML's `analyze_scalar` for a single-line block scalar. */
function plainAllowed(text: string): boolean {
  if (IMPLICIT.some((pattern) => pattern.test(text))) return false;
  if (text.startsWith("---") || text.startsWith("...")) return false;
  if (/^\s|\s$/.test(text.replace(/[^ \t]/g, "x"))) return false;
  const chars = [...text];
  let precededBySpace = true;
  for (const [index, ch] of chars.entries()) {
    const next = chars[index + 1];
    const followedBySpace = next === undefined || BREAKS.includes(next);
    if (index === 0) {
      if ("#,[]{}&*!|>'\"%@`".includes(ch)) return false;
      if ((ch === "?" || ch === ":" || ch === "-") && followedBySpace) return false;
    } else {
      if (ch === ":" && followedBySpace) return false;
      if (ch === "#" && precededBySpace) return false;
    }
    precededBySpace = BREAKS.includes(ch);
  }
  return true;
}
