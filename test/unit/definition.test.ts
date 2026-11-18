import { McpServer } from "@modelcontextprotocol/server";
import { describe, expect, it } from "vitest";
import * as z from "zod/v4";
import { type DefinedTool, defineTool, READ_ONLY } from "../../src/tools/definition.js";
import { TOOLS } from "../../src/tools/index.js";
import { connect } from "../helpers.js";

const echo = defineTool({
  name: "firms_echo",
  version: "1.0.0",
  title: "Echo",
  description: "Echoes a word.",
  inputSchema: z.strictObject({ word: z.string().min(2) }),
  outputSchema: z.object({ word: z.string(), length: z.number() }),
  annotations: READ_ONLY,
  async run({ word }) {
    if (word === "fail") throw new Error("Cannot echo 'fail'. Try another word.");
    if (word === "bad")
      return { word, length: "three" } as unknown as { word: string; length: number };
    return { word, length: word.length };
  },
});

async function clientFor(tool: DefinedTool) {
  const server = new McpServer({ name: "t", version: "0" });
  tool.register(server);
  return connect(server);
}

describe("defineTool", () => {
  it("[REQ-FR-MCP-001] advertises the title, annotations, schemas, and tool version", async () => {
    const client = await clientFor(echo);
    const [tool] = (await client.listTools()).tools;
    expect(tool?.name).toBe("firms_echo");
    expect(tool?.title).toBe("Echo");
    expect(tool?.annotations).toMatchObject(READ_ONLY);
    expect(tool?.inputSchema.properties).toHaveProperty("word");
    expect(tool?.outputSchema?.properties).toHaveProperty("length");
    expect(tool?._meta?.["io.github.mendesdyl/firms-mcp/tool-version"]).toBe("1.0.0");
  });

  it("[REQ-NFR-002] returns structured content and the same data as JSON text", async () => {
    const client = await clientFor(echo);
    const result = await client.callTool({ name: "firms_echo", arguments: { word: "fire" } });
    expect(result.isError).toBeFalsy();
    expect(result.structuredContent).toEqual({ word: "fire", length: 4 });
    const [text] = result.content as { type: string; text: string }[];
    expect(JSON.parse(text?.text ?? "")).toEqual({ word: "fire", length: 4 });
  });

  it("turns invalid arguments, thrown errors, and invalid output into tool errors", async () => {
    const client = await clientFor(echo);
    const invalid = await client.callTool({ name: "firms_echo", arguments: { word: "x" } });
    expect(invalid.isError).toBe(true);
    const unknownArg = await client.callTool({
      name: "firms_echo",
      arguments: { word: "fire", extra: 1 },
    });
    expect(unknownArg.isError).toBe(true);
    const thrown = await client.callTool({ name: "firms_echo", arguments: { word: "fail" } });
    expect(thrown.isError).toBe(true);
    expect(JSON.stringify(thrown.content)).toContain("Try another word");
    const badOutput = await client.callTool({ name: "firms_echo", arguments: { word: "bad" } });
    expect(badOutput.isError).toBe(true);
  });

  it("[REQ-NFR-003] every registered tool has a firms_ name, title, annotations, and schemas", () => {
    for (const tool of TOOLS) {
      expect(tool.name).toMatch(/^firms_[a-z_]+$/);
      expect(tool.title.length).toBeGreaterThan(0);
      expect(tool.annotations.readOnlyHint).toBe(true);
      expect(tool.outputSchema).toBeDefined();
    }
  });
});
