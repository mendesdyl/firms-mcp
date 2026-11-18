import { describe, expect, it } from "vitest";
import { checkTraceability, collectTags, loadRequirements } from "../../scripts/ts/traceability.js";

const yaml = (status: string) => `requirements:
  - id: FR-KB-001
    title: T
    source: S
    rationale: R
    priority: must
    verification: test
    status: ${status}
`;

describe("traceability", () => {
  it("accepts the four statuses and rejects others", () => {
    for (const status of ["planned", "implemented", "verified", "deferred"]) {
      expect(loadRequirements(yaml(status))).toHaveLength(1);
    }
    expect(() => loadRequirements(yaml("done"))).toThrow(/bad status/);
  });

  it("collects tags from test names and reports unknown and untested requirements", () => {
    // Built at run time so the traceability scanner does not read these as real tags.
    const tag = (id: string) => `[${"REQ"}-${id}]`;
    const text = `it("${tag("FR-KB-001")} loads", () => {});\nit("${tag("FR-ZZ-999")} x", () => {});`;
    const tags = collectTags([{ path: "test/a.test.ts", text }]);
    expect(tags.get("FR-KB-001")).toEqual(["test/a.test.ts › loads"]);
    const requirements = loadRequirements(yaml("implemented"));
    expect(checkTraceability(requirements, tags).unknown).toEqual(["FR-ZZ-999"]);
    expect(checkTraceability(requirements, new Map()).untested).toEqual(["FR-KB-001"]);
    expect(checkTraceability(loadRequirements(yaml("deferred")), new Map()).untested).toEqual([]);
  });
});
