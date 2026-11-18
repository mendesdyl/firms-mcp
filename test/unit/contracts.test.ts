import { readFileSync } from "node:fs";
import { describe, expect, it } from "vitest";
import { renderContracts } from "../../scripts/ts/contracts.js";

describe("tool contracts", () => {
  it("[REQ-FR-MCP-001] contracts/tools.json matches the tool definitions", () => {
    expect(readFileSync("contracts/tools.json", "utf8")).toBe(renderContracts());
  });
});
