/**
 * Minimal, lossless-for-text HTML → Markdown converter for the FIRMS FAQ markup (ADR-0005).
 * A port of iteration 1's `MarkdownConverter`: the form changes (links made absolute, tables,
 * lists, figures with captions), the wording never does.
 */
import {
  type AnyNode,
  attr,
  children,
  classes,
  type Element,
  findAll,
  findParent,
  isTag,
  isText,
  selectFirst,
} from "./dom.js";

const BLOCK_TAGS = new Set([
  "p",
  "div",
  "section",
  "article",
  "figure",
  "ul",
  "ol",
  "table",
  "h1",
  "h2",
  "h3",
  "h4",
  "h5",
  "h6",
  "blockquote",
  "figcaption",
]);
const HEADINGS = new Set(["h1", "h2", "h3", "h4", "h5", "h6"]);
/** Placeholder for <br> until rendering (LINE SEPARATOR). */
const HARD_BREAK = "\u2028";

/** Drop invisible formatting characters, turn no-break spaces into spaces, collapse runs. */
export function collapse(text: string): string {
  return text
    .replace(/\u200b|\u200c|\u200d|\u2060|\ufeff/g, "")
    .replaceAll("\u00a0", " ")
    .replace(/[ \t\r\n\f\v]+/g, " ");
}

const isSpace = (ch: string | undefined) => ch !== undefined && /\s/.test(ch);
const lead = (text: string) => (isSpace(text[0]) ? " " : "");
const trail = (text: string) => (isSpace(text.at(-1)) ? " " : "");

function wrap(inner: string, marker: string): string {
  const text = inner.trim();
  return text ? `${lead(inner)}${marker}${text}${marker}${trail(inner)}` : inner;
}

function finishInline(text: string): string {
  const lines = collapse(text)
    .split(HARD_BREAK)
    .map((line) => line.trim());
  while (lines.length && !lines[0]) lines.shift();
  while (lines.length && !lines.at(-1)) lines.pop();
  return lines.join("\\\n");
}

function isHiddenLabel(node: AnyNode): boolean {
  const cls = classes(node);
  return cls.includes("visually-hidden") && cls.includes("field__label");
}

export function isImageParagraph(node: AnyNode): boolean {
  return classes(node).includes("paragraph--type--image-full-width");
}

/** Python's `urljoin` for the link forms on FIRMS pages (no re-encoding of the href). */
export function urljoin(base: string, href: string): string {
  if (/^[a-zA-Z][a-zA-Z0-9+.-]*:/.test(href)) return href;
  const url = new URL(base);
  if (href.startsWith("//")) return `${url.protocol}${href}`;
  const origin = `${url.protocol}//${url.host}`;
  const basePath = url.pathname;
  if (href.startsWith("#")) return `${origin}${basePath}${url.search}${href}`;
  if (href.startsWith("?")) return `${origin}${basePath}${href}`;
  const [pathPart = "", ...rest] = href.split(/(?=[?#])/);
  const joined = pathPart.startsWith("/")
    ? pathPart
    : `${basePath.slice(0, basePath.lastIndexOf("/") + 1)}${pathPart}`;
  const segments: string[] = [];
  const parts = joined.split("/");
  parts.forEach((segment, index) => {
    const last = index === parts.length - 1;
    if (segment === "..") {
      if (segments.length > 1) segments.pop();
      if (last) segments.push("");
    } else if (segment === ".") {
      if (last) segments.push("");
    } else {
      segments.push(segment);
    }
  });
  return `${origin}${segments.join("/")}${rest.join("")}`;
}

export class MarkdownConverter {
  constructor(readonly pageUrl: string) {}

  /** Resolve a link against the page it appeared on (mailto/tel left unchanged). */
  absolute(href: string): string {
    const trimmed = href.trim();
    if (!trimmed || trimmed.startsWith("mailto:") || trimmed.startsWith("tel:")) return trimmed;
    return urljoin(this.pageUrl, trimmed);
  }

  inline(node: AnyNode): string {
    if (isText(node)) return collapse(node.data);
    if (!isTag(node)) return ""; // comments, processing instructions
    const name = node.name;
    if (name === "br") return HARD_BREAK;
    if (isHiddenLabel(node)) return "";
    if (name === "img") return this.image(node);
    const inner = children(node)
      .map((child) => this.inline(child))
      .join("");
    if (name === "a") {
      const href = this.absolute(attr(node, "href") ?? "");
      const text = inner.trim();
      if (!href) return inner;
      if (!text) return "";
      return `${lead(inner)}[${text}](${href})${trail(inner)}`;
    }
    if (name === "strong" || name === "b") return wrap(inner, "**");
    if (name === "em" || name === "i") return wrap(inner, "*");
    if (name === "sup" || name === "sub") {
      return inner.trim() ? `<${name}>${inner.trim()}</${name}>` : "";
    }
    if (name === "code") return inner.trim() ? `\`${inner}\`` : inner;
    return inner;
  }

  image(img: Element): string {
    const alt = collapse(attr(img, "alt") ?? "").trim();
    const link = findParent(img, "a");
    const url = link && attr(link, "href") ? (attr(link, "href") ?? "") : (attr(img, "src") ?? "");
    return `![${alt}](${this.absolute(url)})`;
  }

  blocks(node: AnyNode, depth = 0): string[] {
    const out: string[] = [];
    let buffer: string[] = [];
    const flush = () => {
      const text = finishInline(buffer.join(""));
      if (text) out.push(text);
      buffer = [];
    };
    for (const child of children(node)) {
      if (!isTag(child)) {
        buffer.push(this.inline(child));
        continue;
      }
      if (isHiddenLabel(child)) continue;
      if (isImageParagraph(child)) {
        flush();
        out.push(...this.imageParagraph(child));
        continue;
      }
      if (BLOCK_TAGS.has(child.name)) {
        flush();
        out.push(...this.block(child, depth));
      } else if (child.name === "img") {
        flush();
        out.push(this.image(child));
      } else if (!["script", "style", "button"].includes(child.name)) {
        buffer.push(this.inline(child));
      }
    }
    flush();
    return out;
  }

  block(node: Element, depth: number): string[] {
    const name = node.name;
    if (HEADINGS.has(name)) {
      const text = finishInline(
        children(node)
          .map((c) => this.inline(c))
          .join(""),
      );
      return text ? [`${"#".repeat(Number(name[1]))} ${text}`] : [];
    }
    if (name === "ul" || name === "ol") return [this.listBlock(node, depth)];
    if (name === "table") {
      const table = this.table(node);
      return table ? [table] : [];
    }
    if (name === "blockquote") {
      const inner = this.blocks(node, depth);
      return [inner.flatMap((b) => b.split("\n").map((line) => `> ${line}`)).join("\n")];
    }
    return this.blocks(node, depth);
  }

  listBlock(node: Element, depth: number): string {
    const ordered = node.name === "ol";
    const lines: string[] = [];
    let number = 1;
    for (const li of findAll(node, ["li"], { recursive: false })) {
      const marker = ordered ? `${number}.` : "-";
      number += 1;
      const parts = this.blocks(li, depth + 1);
      if (!parts.length) continue;
      const indent = " ".repeat(marker.length + 1);
      const [first = "", ...rest] = parts;
      lines.push(`${marker} ${first.replaceAll("\n", `\n${indent}`)}`);
      for (const part of rest) lines.push(indent + part.replaceAll("\n", `\n${indent}`));
    }
    return lines.join("\n");
  }

  table(node: Element): string {
    let rows = findAll(node, ["tr"]).map((tr) =>
      findAll(tr, ["th", "td"], { recursive: false }).map((cell) => this.cell(cell)),
    );
    rows = rows.filter((row) => row.some((cell) => cell.trim()));
    if (!rows.length) return "";
    const width = Math.max(...rows.map((row) => row.length));
    rows = rows.map((row) => [...row, ...Array<string>(width - row.length).fill("")]);
    const [header = [], ...body] = rows;
    const out = [`| ${header.join(" | ")} |`, `|${"---|".repeat(width)}`];
    for (const row of body) out.push(`| ${row.join(" | ")} |`);
    return out.join("\n");
  }

  cell(node: Element): string {
    const text = this.blocks(node)
      .map((part) => part.replaceAll("\\\n", "<br>").replaceAll("\n", "<br>"))
      .join("<br>");
    return text.replaceAll("|", "\\|").trim();
  }

  imageParagraph(node: Element): string[] {
    const out = findAll(node, ["img"]).map((img) => this.image(img));
    const caption = selectFirst(node, ".field--name-field-image-media-entity-caption .field__item");
    if (caption) {
      const text = this.blocks(caption).join(" ").trim();
      if (text) out.push(`*Image caption:* ${text}`);
    }
    return out;
  }

  /** Blocks for one top-level node (text, element, or image paragraph). */
  blocksFor(node: AnyNode): string[] {
    if (!isTag(node)) {
      const text = finishInline(this.inline(node));
      return text ? [text] : [];
    }
    if (isImageParagraph(node)) return this.imageParagraph(node);
    if (BLOCK_TAGS.has(node.name)) return this.block(node, 0);
    const text = finishInline(this.inline(node));
    return text ? [text] : [];
  }

  convert(node: AnyNode): string {
    return this.blocks(node)
      .filter((block) => block.trim())
      .join("\n\n");
  }
}
