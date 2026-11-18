import { defineConfig } from "vitest/config";

export default defineConfig({
  test: {
    include: ["test/**/*.test.ts"],
    // Tests never reach the network (NFR-001); see test/setup/no-network.ts.
    setupFiles: ["test/setup/no-network.ts"],
  },
});
