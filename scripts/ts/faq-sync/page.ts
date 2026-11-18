/** Verbatim Markdown of part of another web page, for supplement entries (FR-KB-003). */
import { removeElement } from "domutils";
import { collapse, MarkdownConverter } from "./convert.js";
import { type Element, elementsAfter, findAll, getText, parseHtml, select } from "./dom.js";

const HEADINGS = ["h1", "h2", "h3", "h4", "h5", "h6"];
const REMOVED = ["script", "style", "noscript", "form", "select", "input", "button"];
const CONTENT = new Set(["p", "ul", "ol", "table", "figure", "blockquote"]);

/**
 * `selector` (CSS; may match several elements, kept in document order) or `heading` (the text
 * of a heading; content runs until the next heading of the same or a higher level).
 */
export function extractPageMarkdown(
  html: string,
  pageUrl: string,
  target: { selector?: string; heading?: string },
): string {
  if (!target.selector && !target.heading)
    throw new Error("either selector or heading is required");
  const doc = parseHtml(html);
  for (const node of findAll(doc, REMOVED)) removeElement(node);
  const converter = new MarkdownConverter(pageUrl);
  const blocks: string[] = [];
  if (target.selector) {
    const nodes = select(doc, target.selector);
    if (!nodes.length) throw new Error(`selector '${target.selector}' matched nothing`);
    for (const node of nodes) blocks.push(...converter.blocks(node).filter((b) => b.trim()));
  } else {
    const heading = findAll(doc, HEADINGS).find(
      (h) => collapse(getText(h, " ")).trim() === target.heading,
    );
    if (!heading) throw new Error(`heading '${target.heading}' not found`);
    const level = Number(heading.name[1]);
    const collected: Element[] = [];
    for (const node of elementsAfter(heading, doc)) {
      if (HEADINGS.includes(node.name) && Number(node.name[1]) <= level) break;
      const inside = (n: Element) => {
        for (let p = n.parent; p; p = p.parent) if (collected.includes(p as Element)) return true;
        return false;
      };
      if (CONTENT.has(node.name) && !inside(node)) collected.push(node);
    }
    for (const node of collected) blocks.push(...converter.blocksFor(node).filter((b) => b.trim()));
  }
  if (!blocks.length) throw new Error("no content extracted");
  return blocks.join("\n\n");
}
