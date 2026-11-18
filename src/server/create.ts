import { McpServer } from "@modelcontextprotocol/server";
import { TOOLS } from "../tools/index.js";
import { SERVER_NAME, SERVER_TITLE, VERSION } from "../version.js";
import { INSTRUCTIONS } from "./instructions.js";
import { registerResources } from "./resources.js";

/**
 * Builds a fresh server. `serveStdio` calls this once; the HTTP handler calls it once per
 * request, so the server keeps no state between requests (ADR-0011 §8). Anything costly to
 * build (the knowledge base, catalogs) is loaded once at module scope and closed over.
 */
export function createServer(): McpServer {
  const server = new McpServer(
    { name: SERVER_NAME, title: SERVER_TITLE, version: VERSION },
    { instructions: INSTRUCTIONS },
  );
  for (const tool of TOOLS) tool.register(server);
  registerResources(server);
  return server;
}
