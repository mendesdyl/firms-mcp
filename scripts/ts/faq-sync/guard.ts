/**
 * Refuse a sync whose result looks like a broken parse rather than a changed FAQ (FR-KB-012).
 * Nothing is written when a check fails; the last good entries stay in place and the command
 * exits non-zero, so the scheduled workflow fails visibly.
 */
import type { ParsedEntry } from "./faq.js";

/** Share of current entries a single sync may retire before a person has to confirm it. */
export const MAX_RETIRED_SHARE = 0.2;

export function checkParsed(
  parsed: ParsedEntry[],
  currentIds: ReadonlySet<string>,
  allowLargeChange = false,
): string[] {
  const problems: string[] = [];
  const questions = parsed.filter((e) => e.kind === "faq");
  if (questions.length === 0) {
    problems.push("no FAQ questions found: the page structure may have changed");
  }
  for (const entry of parsed) {
    if (!entry.title.trim()) problems.push(`${entry.id}: empty title`);
    if (!entry.body.trim()) problems.push(`${entry.id}: empty body`);
  }
  const parsedIds = new Set(parsed.map((e) => e.id));
  const retired = [...currentIds].filter((id) => !parsedIds.has(id));
  if (
    !allowLargeChange &&
    currentIds.size > 0 &&
    retired.length / currentIds.size > MAX_RETIRED_SHARE
  ) {
    problems.push(
      `${retired.length} of ${currentIds.size} current entries would be retired (more than ${MAX_RETIRED_SHARE * 100} %); ` +
        "if the FAQ really was reorganized, rerun with --allow-large-change",
    );
  }
  return problems;
}
