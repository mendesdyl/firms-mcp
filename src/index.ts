#!/usr/bin/env node
/**
 * Entry point. `firms-mcp-server` serves stdio (local hosts such as Claude Desktop and Claude
 * Code); `firms-mcp-server http` serves stateless Streamable HTTP. Never write to stdout here:
 * on stdio it carries the protocol, so logs go to stderr.
 */
import { serveStdio } from "@modelcontextprotocol/server/stdio";
import { createServer } from "./server/create.js";
import { createHttpApp, readHttpOptions } from "./server/http.js";
import { SERVER_NAME, VERSION } from "./version.js";

const mode = process.argv[2] ?? "stdio";

if (mode === "http") {
  const options = readHttpOptions();
  createHttpApp(options).listen(options.port, options.host, () => {
    console.error(
      `${SERVER_NAME} ${VERSION} listening on http://${options.host}:${options.port}/mcp`,
    );
  });
} else if (mode === "stdio") {
  serveStdio(createServer);
  console.error(`${SERVER_NAME} ${VERSION} running on stdio`);
} else {
  console.error(`Unknown mode "${mode}". Use "stdio" (default) or "http".`);
  process.exit(2);
}
