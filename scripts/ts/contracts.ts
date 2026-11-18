/**
 * Writes contracts/tools.json: every tool's name, version, title, description, annotations,
 * and input and output JSON Schemas, generated from the Zod definitions (ADR-0012). It is the
 * language-neutral contract another implementation (for example a PHP port) must satisfy.
 * With `--check`, fails if the file is out of date.
 */
import { readFileSync, writeFileSync } from "node:fs";
import { join } from "node:path";
import * as z from "zod/v4";
import { TOOLS } from "../../src/tools/index.js";
import { SERVER_NAME, VERSION } from "../../src/version.js";

const FILE = join(import.meta.dirname, "..", "..", "contracts", "tools.json");

export function renderContracts(): string {
  const contract = {
    server: SERVER_NAME,
    version: VERSION,
    tools: TOOLS.map((tool) => ({
      name: tool.name,
      version: tool.version,
      title: tool.title,
      description: tool.description,
      annotations: tool.annotations,
      inputSchema: z.toJSONSchema(tool.inputSchema),
      outputSchema: z.toJSONSchema(tool.outputSchema),
    })),
  };
  return `${JSON.stringify(contract, null, 2)}\n`;
}

if (process.argv[1] === import.meta.filename) {
  const text = renderContracts();
  if (process.argv.includes("--check")) {
    if (readFileSync(FILE, "utf8") !== text) {
      console.error("contracts/tools.json is out of date: run `npm run contracts`");
      process.exit(1);
    }
  } else {
    writeFileSync(FILE, text);
  }
}
