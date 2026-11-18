import { createMcpExpressApp } from "@modelcontextprotocol/express";
import { toNodeHandler } from "@modelcontextprotocol/node";
import { createMcpHandler } from "@modelcontextprotocol/server";
import { TOOLS } from "../tools/index.js";
import { SERVER_NAME, VERSION } from "../version.js";
import { createServer } from "./create.js";

export interface HttpOptions {
  host: string;
  port: number;
  /** Host names accepted in the Host header; required when binding beyond localhost. */
  allowedHosts: string[];
}

export function readHttpOptions(env: NodeJS.ProcessEnv = process.env): HttpOptions {
  const host = env.FIRMS_MCP_HOST ?? "127.0.0.1";
  const port = Number(env.FIRMS_MCP_PORT ?? 8000);
  if (!Number.isInteger(port) || port < 1 || port > 65535) {
    throw new Error(`FIRMS_MCP_PORT must be a port number, got "${env.FIRMS_MCP_PORT}"`);
  }
  const allowedHosts = (env.FIRMS_MCP_ALLOWED_HOSTS ?? "")
    .split(",")
    .map((name) => name.trim())
    .filter(Boolean);
  const local = ["127.0.0.1", "localhost", "::1"].includes(host);
  if (!local && allowedHosts.length === 0) {
    throw new Error(
      `Binding to ${host} needs FIRMS_MCP_ALLOWED_HOSTS (comma-separated host names) so DNS-rebinding protection stays on.`,
    );
  }
  return { host, port, allowedHosts };
}

/** Express app serving stateless Streamable HTTP at /mcp and a health check at /health. */
export function createHttpApp(options: HttpOptions) {
  const app = createMcpExpressApp(
    options.allowedHosts.length > 0
      ? { host: options.host, allowedHosts: options.allowedHosts }
      : { host: options.host },
  );
  const handler = toNodeHandler(createMcpHandler(createServer));
  app.get("/health", (_req, res) => {
    res.json({ status: "ok", name: SERVER_NAME, version: VERSION, tools: TOOLS.length });
  });
  app.all("/mcp", (req, res) => void handler(req, res, req.body));
  return app;
}
