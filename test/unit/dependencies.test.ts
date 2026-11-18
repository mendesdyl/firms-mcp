import { readdirSync, readFileSync } from "node:fs";
import { join } from "node:path";
import { describe, expect, it } from "vitest";

const pkg = JSON.parse(readFileSync("package.json", "utf8")) as {
  dependencies: Record<string, string>;
};

function sourceFiles(dir: string): string[] {
  return readdirSync(dir, { withFileTypes: true }).flatMap((entry) =>
    entry.isDirectory()
      ? sourceFiles(join(dir, entry.name))
      : entry.name.endsWith(".ts")
        ? [join(dir, entry.name)]
        : [],
  );
}

/** `zod/v4` → `zod`, `@scope/name/sub` → `@scope/name`. */
function packageName(specifier: string): string {
  const parts = specifier.split("/");
  return specifier.startsWith("@") ? parts.slice(0, 2).join("/") : (parts[0] ?? specifier);
}

describe("runtime dependencies", () => {
  it("declares every package the server imports as a runtime dependency", () => {
    const imported = new Set<string>();
    for (const file of sourceFiles("src")) {
      for (const match of readFileSync(file, "utf8").matchAll(/from "([^".][^"]*)"/g)) {
        const specifier = match[1] ?? "";
        if (!specifier.startsWith("node:")) imported.add(packageName(specifier));
      }
    }
    expect([...imported].filter((name) => !(name in pkg.dependencies)).sort()).toEqual([]);
  });
});
