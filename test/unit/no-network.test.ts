import net from "node:net";
import { describe, expect, it } from "vitest";
import { NetworkAccessBlocked } from "../setup/no-network.js";

describe("network guard", () => {
  it("[REQ-NFR-001] blocks connections that leave this machine", async () => {
    expect(() => net.connect(443, "192.0.2.1")).toThrow(NetworkAccessBlocked);
    await expect(fetch("https://firms.modaps.eosdis.nasa.gov/")).rejects.toThrow(
      NetworkAccessBlocked,
    );
  });
});
