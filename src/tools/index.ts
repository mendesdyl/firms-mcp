/**
 * Every tool the server registers, in the order `tools/list` returns them (FR-MCP-008).
 * The seven `firms_` tools of ADR-0011 are added by the knowledge, URL-builder, and tools
 * steps (running list WK-20 … WK-23).
 */
import type { DefinedTool } from "./definition.js";

export const TOOLS: readonly DefinedTool[] = [];
