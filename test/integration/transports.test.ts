import type { Server } from "node:http";
import type { AddressInfo } from "node:net";
import { Client, StreamableHTTPClientTransport } from "@modelcontextprotocol/client";
import { getDefaultEnvironment, StdioClientTransport } from "@modelcontextprotocol/client/stdio";
import { afterAll, beforeAll, describe, expect, it } from "vitest";
import { createServer } from "../../src/server/create.js";
import { createHttpApp, readHttpOptions } from "../../src/server/http.js";
import { TOOLS } from "../../src/tools/index.js";
import { SERVER_NAME, VERSION } from "../../src/version.js";
import { connect } from "../helpers.js";

describe("server", () => {
  it("[REQ-FR-MCP-002] identifies itself and sends instructions", async () => {
    const client = await connect(createServer());
    expect(client.getServerVersion()).toMatchObject({ name: SERVER_NAME, version: VERSION });
    expect(client.getInstructions()).toContain("does not answer science questions");
    expect(client.getInstructions()).toContain("not an official NASA product");
  });

  it("[REQ-FR-MCP-008] lists tools in the registry order", async () => {
    const client = await connect(createServer());
    const { tools } = await client.listTools();
    expect(tools.map((t) => t.name)).toEqual(TOOLS.map((t) => t.name));
  });
});

describe("Streamable HTTP", () => {
  let http: Server;
  let base: string;

  beforeAll(async () => {
    const options = readHttpOptions({ FIRMS_MCP_PORT: "1" });
    http = createHttpApp(options).listen(0, "127.0.0.1");
    await new Promise((resolve) => http.once("listening", resolve));
    base = `http://127.0.0.1:${(http.address() as AddressInfo).port}`;
  });
  afterAll(() => new Promise<void>((resolve) => http.close(() => resolve())));

  it("[REQ-FR-MCP-006] serves MCP over stateless Streamable HTTP", async () => {
    const client = new Client({ name: "firms-mcp-test", version: "1.0.0" });
    await client.connect(new StreamableHTTPClientTransport(new URL(`${base}/mcp`)));
    expect(client.getServerVersion()?.name).toBe(SERVER_NAME);
    expect((await client.listTools()).tools).toHaveLength(TOOLS.length);
    await client.close();
  });

  it("[REQ-FR-MCP-007] accepts a handshake-era (2025-06-18) initialize", async () => {
    const response = await fetch(`${base}/mcp`, {
      method: "POST",
      headers: {
        "content-type": "application/json",
        accept: "application/json, text/event-stream",
      },
      body: JSON.stringify({
        jsonrpc: "2.0",
        id: 1,
        method: "initialize",
        params: {
          protocolVersion: "2025-06-18",
          capabilities: {},
          clientInfo: { name: "legacy", version: "1" },
        },
      }),
    });
    expect(response.status).toBe(200);
    const text = await response.text();
    expect(text).toContain(SERVER_NAME);
    expect(text).toContain("2025-06-18");
  });

  it("reports health", async () => {
    const response = await fetch(`${base}/health`);
    expect(await response.json()).toEqual({
      status: "ok",
      name: SERVER_NAME,
      version: VERSION,
      tools: TOOLS.length,
    });
  });
});

describe("stdio", () => {
  it("[REQ-FR-MCP-006] serves MCP over stdio", async () => {
    const client = new Client({ name: "firms-mcp-test", version: "1.0.0" });
    await client.connect(
      new StdioClientTransport({
        command: process.execPath,
        args: ["--import", "tsx", "src/index.ts"],
        env: getDefaultEnvironment(),
      }),
    );
    expect(client.getServerVersion()?.version).toBe(VERSION);
    await client.close();
  }, 20_000);
});

describe("HTTP options", () => {
  it("defaults to localhost and refuses a public bind without allowed host names", () => {
    expect(readHttpOptions({})).toEqual({ host: "127.0.0.1", port: 8000, allowedHosts: [] });
    expect(() => readHttpOptions({ FIRMS_MCP_HOST: "0.0.0.0" })).toThrow(/FIRMS_MCP_ALLOWED_HOSTS/);
    expect(
      readHttpOptions({ FIRMS_MCP_HOST: "0.0.0.0", FIRMS_MCP_ALLOWED_HOSTS: "mcp.example.org" }),
    ).toMatchObject({ allowedHosts: ["mcp.example.org"] });
    expect(() => readHttpOptions({ FIRMS_MCP_PORT: "http" })).toThrow(/port number/);
  });
});
