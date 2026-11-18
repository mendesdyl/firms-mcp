/**
 * The FIRMS FAQ page → verbatim knowledge entries (ADR-0005). A port of iteration 1's
 * `parse_faq_html`: section headings (`<h2>`) and accordion items (question button + answer
 * body) are walked in document order, producing one entry per question plus entries for the
 * page preamble and for text directly under a section heading.
 */
import { collapse, MarkdownConverter } from "./convert.js";
import {
  type AnyNode,
  attr,
  children,
  classes,
  type Element,
  findAll,
  findParent,
  getText,
  isTag,
  parseHtml,
  select,
  selectFirst,
} from "./dom.js";

export const FAQ_URL = "https://www.earthdata.nasa.gov/data/tools/firms/faq";
export const SOURCE_ID = "firms-faq";

/**
 * Stable, short section IDs for the sections present on 2026-10-09. Sections added to the page
 * later fall back to a slug of their title.
 */
export const SECTION_IDS: Record<string, string> = {
  "Getting Started": "getting-started",
  "Support and Mailing Lists": "support",
  "Caveats to Consider When Using Active Fire Data from FIRMS": "caveats",
  "Questions About VIIRS Active Fire Data": "viirs",
  "Questions About MODIS Active Fire Data": "modis",
  "Questions About Real-Time (RT) and Ultra Real-Time (URT) Active Fire Data": "rt-urt",
  "Geostationary Active Fire Data": "geostationary",
  "Landsat Fire Data": "landsat",
  "Harmonized Landsat Sentinel-2 (HLS) imagery in FIRMS": "hls",
  "FIRMS Fire Map": "fire-map",
  "Satellite Swaths and Coverage": "swaths",
  "Email Alerts": "email-alerts",
  "FIRMS US/Canada": "us-canada",
  "Experimental Mode": "experimental",
  "Static Thermal Anomalies": "static-thermal-anomalies",
  Acronyms: "acronyms",
};

/** Keyword → tag, matched against the question and section title (helps search only). */
const TAG_KEYWORDS: [string, string[]][] = [
  ["modis", ["modis", "terra", "aqua"]],
  ["viirs", ["viirs", "suomi", "noaa-20", "noaa-21"]],
  ["landsat", ["landsat", "oli"]],
  ["geostationary", ["geostationary", "goes", "meteosat", "himawari", "seviri", "abi", "ahi"]],
  ["hls", ["hls", "harmonized"]],
  ["confidence", ["confidence"]],
  ["latency", ["latency", "real-time", "urt", "nrt", "updated", "how often"]],
  ["resolution", ["resolution", "pixel", "scan and track", "size"]],
  ["caveats", ["caveat", "false", "artifact", "missed", "not detected", "canopy", "plume"]],
  ["frp", ["frp", "radiative"]],
  ["burned-area", ["burned area", "burn"]],
  ["perimeter", ["perimeter"]],
  ["alerts", ["alert"]],
  ["fire-map", ["fire map", "map viewer"]],
  ["citation", ["citation", "cite", "restrictions"]],
  ["attributes", ["attribute", "fields"]],
  ["smoke", ["smoke", "aerosol", "omps"]],
];

export interface ParsedEntry {
  id: string;
  title: string;
  kind: "faq" | "faq-section-intro" | "faq-preamble";
  section: string;
  section_title: string;
  source_url: string;
  order: number;
  body: string;
  anchor: string | undefined;
  tags: string[];
  related: string[];
}

export function slugify(text: string, maxLength = 64): string {
  const slug = text
    .toLowerCase()
    .replaceAll("&", " and ")
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-+|-+$/g, "");
  if (slug.length <= maxLength) return slug;
  const cut = slug.slice(0, maxLength);
  return cut.includes("-") ? cut.slice(0, cut.lastIndexOf("-")) : cut;
}

function tagsFor(...texts: string[]): string[] {
  const haystack = texts.join(" ").toLowerCase();
  return TAG_KEYWORDS.filter(([, words]) => words.some((w) => haystack.includes(w))).map(
    ([tag]) => tag,
  );
}

function paragraphType(node: Element): string {
  const cls = classes(node).find((c) => c.startsWith("paragraph--type--"));
  return cls ? cls.slice("paragraph--type--".length) : "";
}

function* topLevelParagraphs(content: AnyNode): Generator<[string, Element]> {
  for (const div of findAll(content, ["div"], { cls: "paragraph" })) {
    const kind = paragraphType(div);
    if (kind === "layout-paragraph") continue;
    let parent = findParent(div, "div", "paragraph");
    while (parent && paragraphType(parent) === "layout-paragraph") {
      parent = findParent(parent, "div", "paragraph");
    }
    if (!parent) yield [kind, div];
  }
}

/** Parse the FAQ page into entries in document order. */
export function parseFaqHtml(html: string, pageUrl = FAQ_URL): ParsedEntry[] {
  const doc = parseHtml(html);
  const content =
    selectFirst(doc, ".block-field-blocknodepagefield-content") ?? findAll(doc, ["body"])[0] ?? doc;
  const converter = new MarkdownConverter(pageUrl);

  const entries: ParsedEntry[] = [];
  const usedIds = new Set<string>();
  const anchors = new Map<string, string>();
  let sectionId = "preamble";
  let sectionTitle = "FIRMS FAQ";
  let sectionAnchor: string | undefined;
  const pending: AnyNode[] = [];
  const freeTextCount = new Map<string, number>();

  const unique = (candidate: string) => {
    let result = candidate;
    for (let n = 2; usedIds.has(result); n++) result = `${candidate}-${n}`;
    usedIds.add(result);
    return result;
  };
  const urlFor = (anchor: string | undefined) => pageUrl + (anchor ? `#${anchor}` : "");

  const flushPending = () => {
    if (!pending.length) return;
    const body = pending
      .flatMap((node) => converter.blocksFor(node))
      .filter((block) => block.trim())
      .join("\n\n");
    pending.length = 0;
    if (!body.trim()) return;
    const count = freeTextCount.get(sectionId) ?? 0;
    freeTextCount.set(sectionId, count + 1);
    const preamble = sectionId === "preamble";
    const suffix = count === 0 ? "overview" : `overview-${count + 1}`;
    const entry: ParsedEntry = {
      id: unique(preamble ? "faq.preamble" : `faq.${sectionId}.${suffix}`),
      title: sectionTitle,
      kind: preamble ? "faq-preamble" : "faq-section-intro",
      section: sectionId,
      section_title: sectionTitle,
      source_url: urlFor(sectionAnchor),
      order: entries.length,
      body,
      anchor: sectionAnchor,
      tags: tagsFor(sectionTitle),
      related: [],
    };
    entries.push(entry);
    if (sectionAnchor && !anchors.has(sectionAnchor)) anchors.set(sectionAnchor, entry.id);
  };

  for (const [kind, paragraph] of topLevelParagraphs(content)) {
    if (kind === "bp-accordion") {
      flushPending();
      for (const item of select(paragraph, ".accordion-item")) {
        const button = selectFirst(item, "button");
        const question = button ? collapse(getText(button, " ")).trim() : "";
        const panel = selectFirst(item, ".panel-collapse") ?? item;
        const anchor = attr(item, "id");
        const id = unique(`faq.${sectionId}.${slugify(question)}`);
        entries.push({
          id,
          title: question,
          kind: "faq",
          section: sectionId,
          section_title: sectionTitle,
          source_url: urlFor(anchor),
          order: entries.length,
          body: converter.convert(panel),
          anchor,
          tags: tagsFor(question, sectionTitle),
          related: [],
        });
        if (anchor) anchors.set(anchor, id);
      }
      continue;
    }
    if (kind === "image-full-width") {
      pending.push(paragraph);
      continue;
    }
    // Text paragraph: split on section headings.
    const container = selectFirst(paragraph, ".tex2jax_process") ?? paragraph;
    for (const child of children(container)) {
      if (isTag(child) && child.name === "h2") {
        const title = collapse(getText(child, " ")).trim();
        if (!title) continue; // empty headings exist on the page
        flushPending();
        sectionTitle = title;
        sectionId = SECTION_IDS[title] ?? slugify(title);
        sectionAnchor = attr(child, "id");
        continue;
      }
      pending.push(child);
    }
  }
  flushPending();
  resolveRelated(entries, anchors, pageUrl);
  return entries;
}

function resolveRelated(entries: ParsedEntry[], anchors: Map<string, string>, pageUrl: string) {
  const escaped = pageUrl.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
  const link = new RegExp(`\\]\\(${escaped}#([^)\\s]+)\\)`, "g");
  for (const entry of entries) {
    for (const [, anchor] of entry.body.matchAll(link)) {
      const target = anchors.get(anchor ?? "");
      if (target && target !== entry.id && !entry.related.includes(target)) {
        entry.related.push(target);
      }
    }
  }
}
