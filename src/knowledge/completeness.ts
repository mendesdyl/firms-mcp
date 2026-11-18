/**
 * Verify that knowledge entries contain a reference text in full (FR-KB-001).
 *
 * The reference is plain text (for example the FAQ as provided by the project owner). The
 * knowledge base is Markdown. Both are reduced to comparable plain text — markup, link
 * targets, table pipes, list markers, and whitespace differences removed; typographic quotes
 * and dashes folded — and every non-empty reference line must then occur in the
 * knowledge-base text. Nothing is compared approximately: a missing sentence fails.
 */
import type { KnowledgeEntry } from "./models.js";

/** Lines that are artifacts of copying a web page (screen-reader labels for figures). */
const IGNORED_REFERENCE_LINES = new Set(["Image", "Image Caption"]);

const FOLD: Record<string, string> = {
  "“": '"', // left double quotation mark
  "”": '"', // right double quotation mark
  "‘": "'", // left single quotation mark
  "’": "'", // right single quotation mark
  "–": "-", // en dash
  "—": "-", // em dash
  "\u00a0": " ", // no-break space
  "…": "...", // horizontal ellipsis
  "\u200b": "", // zero-width space
  "\u200c": "", // zero-width non-joiner
  "\u200d": "", // zero-width joiner
  "\u2060": "", // word joiner
  "\ufeff": "", // zero-width no-break space
};
const FOLD_PATTERN = new RegExp(`[${Object.keys(FOLD).join("")}]`, "g");
const IMAGE = /!\[([^\]]*)\]\([^)]*\)/g;
const LINK = /\[((?:[^[\]]|\[[^\]]*\])*)\]\((?:[^()]|\([^)]*\))*\)/g;
const TABLE_RULE = /^\|(?:-+\|)+$/;

/** Unicode-normalize, fold quotes and dashes, drop emphasis markers, collapse whitespace. */
export function fold(text: string): string {
  return text
    .normalize("NFKC")
    .replace(FOLD_PATTERN, (char) => FOLD[char] ?? char)
    .replaceAll("*", "")
    .replace(/\s+/g, " ")
    .trim();
}

/** Plain text of an entry body, preserving reading order. */
export function markdownToPlain(markdown: string): string {
  const lines: string[] = [];
  for (const line of markdown.split("\n")) {
    let text = line.trim();
    if (TABLE_RULE.test(text)) continue;
    text = text.replace(/^#{1,6}\s+/, "").replace(/^(?:[-+]|\d+\.)\s+/, "");
    text = text.replace(IMAGE, "$1");
    for (let pass = 0; pass < 3; pass++) text = text.replace(LINK, "$1"); // links may nest
    text = text.replace(/<\/?(?:sup|sub)>/g, "");
    text = text.replaceAll("<br>", " ").replaceAll("\\|", "\0");
    text = text.replaceAll("|", " ").replaceAll("\0", "|");
    lines.push(text.replace(/\\+$/, ""));
  }
  return lines.join("\n");
}

/** Folded plain text of the given entries (section titles, titles, and bodies). */
export function corpus(entries: Iterable<KnowledgeEntry>): string {
  const parts: string[] = [];
  const seenSections = new Set<string>();
  for (const entry of entries) {
    if (!seenSections.has(entry.section)) {
      parts.push(entry.section_title);
      seenSections.add(entry.section);
    }
    parts.push(entry.title, markdownToPlain(entry.body));
  }
  return fold(parts.join(" "));
}

/** Reference lines (folded) that do not occur in the knowledge-base text. */
export function missingLines(reference: string, entries: Iterable<KnowledgeEntry>): string[] {
  const haystack = corpus(entries);
  const missing: string[] = [];
  for (const raw of reference.split("\n")) {
    const line = raw.trim();
    if (!line || IGNORED_REFERENCE_LINES.has(line)) continue;
    // List numbers and bullets are markup on one side and may be typed text on the other.
    const folded = fold(line.replace(/^(?:[-+]|\d+\.)\s+/, ""));
    if (folded && !haystack.includes(folded)) missing.push(folded);
  }
  return missing;
}
