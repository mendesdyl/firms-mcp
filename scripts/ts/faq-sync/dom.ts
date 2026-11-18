/**
 * The few DOM operations the converter needs, with BeautifulSoup's semantics (iteration 1
 * parsed with BeautifulSoup and the output must not change).
 */
import { selectAll, selectOne } from "css-select";
import { type AnyNode, type Document, type Element, isTag, isText } from "domhandler";
import { parseDocument } from "htmlparser2";

export type { AnyNode, Document, Element };
export { isTag, isText };

export function parseHtml(html: string): Document {
  return parseDocument(html, { decodeEntities: true });
}

export function classes(node: AnyNode): string[] {
  return isTag(node) ? (node.attribs.class ?? "").split(/\s+/).filter(Boolean) : [];
}

export function attr(node: Element, name: string): string | undefined {
  return node.attribs[name];
}

/** Nearest ancestor with this tag name (and class, if given). */
export function findParent(node: AnyNode, name: string, cls?: string): Element | null {
  for (let p = node.parent; p; p = p.parent) {
    if (isTag(p) && p.name === name && (!cls || classes(p).includes(cls))) return p;
  }
  return null;
}

/** Descendant elements in document order, optionally only direct children. */
export function findAll(
  node: AnyNode,
  names: readonly string[],
  options: { recursive?: boolean; cls?: string } = {},
): Element[] {
  const { recursive = true, cls } = options;
  const out: Element[] = [];
  const visit = (parent: AnyNode) => {
    if (!("children" in parent)) return;
    for (const child of parent.children) {
      if (!isTag(child)) continue;
      if (names.includes(child.name) && (!cls || classes(child).includes(cls))) out.push(child);
      if (recursive) visit(child);
    }
  };
  visit(node);
  return out;
}

export function select(node: AnyNode, selector: string): Element[] {
  return selectAll(selector, node);
}

export function selectFirst(node: AnyNode, selector: string): Element | null {
  return selectOne(selector, node);
}

export function children(node: AnyNode): AnyNode[] {
  return "children" in node ? node.children : [];
}

/** BeautifulSoup `get_text(separator)`: text nodes only (no comments), joined. */
export function getText(node: AnyNode, separator = ""): string {
  const parts: string[] = [];
  const visit = (n: AnyNode) => {
    if (isText(n)) parts.push(n.data);
    else for (const child of children(n)) visit(child);
  };
  visit(node);
  return parts.join(separator);
}

/** Every element after `node` in document order (BeautifulSoup `find_all_next(True)`). */
export function elementsAfter(node: Element, root: Document): Element[] {
  const all: Element[] = [];
  const visit = (n: AnyNode) => {
    for (const child of children(n)) {
      if (isTag(child)) all.push(child);
      visit(child);
    }
  };
  visit(root);
  return all.slice(all.indexOf(node) + 1);
}
