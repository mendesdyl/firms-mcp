/**
 * Tests never reach the network (NFR-001): any connection that is not to this machine
 * throws. Loopback stays open so the HTTP transport can be tested in-process.
 */
import net from "node:net";

export class NetworkAccessBlocked extends Error {}

const LOOPBACK = new Set(["127.0.0.1", "::1", "localhost"]);

const realConnect = net.Socket.prototype.connect;
net.Socket.prototype.connect = function (this: net.Socket, ...args: unknown[]) {
  // net.connect() hands Socket#connect its arguments already normalized into one array.
  const [first, second] = Array.isArray(args[0]) ? (args[0] as unknown[]) : args;
  const options =
    typeof first === "object" && first !== null ? (first as net.TcpNetConnectOpts) : undefined;
  const host = options
    ? (options.host ?? "localhost")
    : typeof second === "string"
      ? second
      : "localhost";
  const isPath = options
    ? "path" in options
    : typeof first === "string" && Number.isNaN(Number(first));
  if (!isPath && !LOOPBACK.has(host)) {
    throw new NetworkAccessBlocked(`tests may not connect to ${host}`);
  }
  return Reflect.apply(realConnect, this, args) as net.Socket;
} as typeof net.Socket.prototype.connect;

const realFetch = globalThis.fetch;
globalThis.fetch = (input: string | URL | Request, init?: RequestInit) => {
  const url = new URL(input instanceof Request ? input.url : input);
  if (!LOOPBACK.has(url.hostname.replace(/^\[|\]$/g, ""))) {
    return Promise.reject(new NetworkAccessBlocked(`tests may not fetch ${url.origin}`));
  }
  return realFetch(input, init);
};
