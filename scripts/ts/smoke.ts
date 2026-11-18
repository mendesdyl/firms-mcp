/**
 * Self-check: starts the built server over stdio, checks the handshake and the tool list,
 * and exits non-zero on any failure. Run with: npm run build && npm run smoke
 */
import { strict as assert } from "node:assert";
import { Client } from "@modelcontextprotocol/client";
import { getDefaultEnvironment, StdioClientTransport } from "@modelcontextprotocol/client/stdio";
import { TOOLS } from "../../src/tools/index.js";
import { SERVER_NAME, VERSION } from "../../src/version.js";

const client = new Client({ name: "firms-mcp-smoke", version: "1.0.0" });
await client.connect(
  new StdioClientTransport({
    command: "node",
    args: ["dist/index.js"],
    env: getDefaultEnvironment(),
  }),
);

const info = client.getServerVersion();
assert.equal(info?.name, SERVER_NAME);
assert.equal(info?.version, VERSION);
assert.ok(client.getInstructions()?.includes("not an official NASA product"));

const { tools } = await client.listTools();
assert.deepEqual(
  tools.map((tool) => tool.name),
  TOOLS.map((tool) => tool.name),
);

await client.close();
console.error(`smoke test passed: ${SERVER_NAME} ${VERSION}, ${tools.length} tools`);
