/**
 * An independent reference text for the FAQ completeness check (FR-KB-001). The page's text is
 * read straight from the DOM — every paragraph, list item, table cell, heading, caption, and
 * accordion question, one line each — without the Markdown converter, so a converter that
 * dropped or changed text would be caught.
 */
import { collapse } from "./convert.js";
import {
  type AnyNode,
  children,
  classes,
  type Element,
  findAll,
  isTag,
  isText,
  parseHtml,
  selectFirst,
} from "./dom.js";

const LEAF_BLOCKS = new Set([
  "p",
  "li",
  "td",
  "th",
  "h2",
  "h3",
  "h4",
  "h5",
  "h6",
  "figcaption",
  "button",
  "dt",
  "dd",
]);
const SKIPPED = new Set(["script", "style", "noscript"]);

function textOf(node: AnyNode): string {
  if (isText(node)) return node.data;
  if (!isTag(node) || SKIPPED.has(node.name)) return "";
  if (classes(node).includes("visually-hidden")) return "";
  if (node.name === "br") return "\n";
  // Nested blocks get their own lines.
  if (LEAF_BLOCKS.has(node.name)) return "\n";
  return children(node).map(textOf).join("");
}

export function pageReferenceLines(html: string): string[] {
  const doc = parseHtml(html);
  const content = selectFirst(doc, ".block-field-blocknodepagefield-content") ?? doc;
  const lines: string[] = [];
  for (const block of findAll(content, [...LEAF_BLOCKS]) as Element[]) {
    const text = children(block).map(textOf).join("");
    for (const line of text.split("\n")) {
      const clean = collapse(line).trim();
      if (clean) lines.push(clean);
    }
  }
  return lines;
}
