/**
 * The tool convention (ADR-0012): each tool lives in `src/tools/<name>/tool.ts` and exports
 * one `defineTool(...)` value. Its Zod schemas are the single source of truth: the SDK derives
 * the JSON Schema clients see, and `npm run contracts` writes the same schemas to
 * `contracts/tools.json`, the language-neutral contract a port to another stack reads.
 */
import type { McpServer, ToolAnnotations } from "@modelcontextprotocol/server";
import type * as z from "zod/v4";

export interface ToolSpec<I extends z.ZodObject, O extends z.ZodObject> {
  /** snake_case with the `firms_` prefix. */
  name: `firms_${string}`;
  /** Semantic version of this tool's contract, bumped when its schemas change. */
  version: string;
  title: string;
  /** What the model reads to decide when and how to call the tool. */
  description: string;
  inputSchema: I;
  outputSchema: O;
  annotations: ToolAnnotations;
  run(input: z.infer<I>, signal: AbortSignal): Promise<z.infer<O>>;
}

/** A tool ready to register, with its schemas kept for contract generation. */
export interface DefinedTool {
  name: string;
  version: string;
  title: string;
  description: string;
  inputSchema: z.ZodObject;
  outputSchema: z.ZodObject;
  annotations: ToolAnnotations;
  register(server: McpServer): void;
}

export function defineTool<I extends z.ZodObject, O extends z.ZodObject>(
  spec: ToolSpec<I, O>,
): DefinedTool {
  return {
    name: spec.name,
    version: spec.version,
    title: spec.title,
    description: spec.description,
    inputSchema: spec.inputSchema,
    outputSchema: spec.outputSchema,
    annotations: spec.annotations,
    register(server) {
      // The SDK validates arguments against `inputSchema` before calling the handler, so the
      // widened schema types below lose no safety; they only stop generic inference failing.
      const inputSchema: z.ZodObject = spec.inputSchema;
      const outputSchema: z.ZodObject = spec.outputSchema;
      server.registerTool(
        spec.name,
        {
          title: spec.title,
          description: spec.description,
          inputSchema,
          outputSchema,
          annotations: spec.annotations,
          _meta: { "io.github.mendesdyl/firms-mcp/tool-version": spec.version },
        },
        async (input, ctx) => {
          // A thrown error becomes an isError result whose text the model reads, so tool
          // code throws errors that say how to recover.
          const output = outputSchema.parse(await spec.run(input as z.infer<I>, ctx.mcpReq.signal));
          return {
            content: [{ type: "text", text: JSON.stringify(output, null, 2) }],
            structuredContent: output,
          };
        },
      );
    },
  };
}

/** Annotations shared by every iteration-2 tool: read-only, repeatable, no side effects. */
export const READ_ONLY: ToolAnnotations = {
  readOnlyHint: true,
  destructiveHint: false,
  idempotentHint: true,
  openWorldHint: false,
};
