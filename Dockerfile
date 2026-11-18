# FIRMS MCP server (TypeScript): stateless Streamable HTTP on port 8000, keyless.
#
#   docker build -t firms-mcp .
#   docker run -p 8000:8000 -e FIRMS_MCP_ALLOWED_HOSTS=firms-mcp.example.org,localhost firms-mcp
#
# The server binds 0.0.0.0 inside the container, so Host-header (DNS-rebinding) checks need
# FIRMS_MCP_ALLOWED_HOSTS; the default below allows only local access through a published
# port. Configuration: docs/developers/CONFIGURATION.md.

FROM node:26-bookworm-slim AS build
WORKDIR /app
# Dependencies first, so source changes do not invalidate the dependency layer.
COPY package.json package-lock.json ./
RUN npm ci --ignore-scripts
COPY tsconfig.json tsconfig.build.json ./
COPY src ./src
RUN npm run build && npm prune --omit=dev

FROM node:26-bookworm-slim
ENV NODE_ENV=production \
    FIRMS_MCP_HOST=0.0.0.0 \
    FIRMS_MCP_PORT=8000 \
    FIRMS_MCP_ALLOWED_HOSTS=localhost,127.0.0.1
WORKDIR /app
COPY --from=build --chown=node:node /app/package.json ./
COPY --from=build --chown=node:node /app/node_modules ./node_modules
COPY --from=build --chown=node:node /app/dist ./dist
COPY --chown=node:node contracts ./contracts
COPY --chown=node:node knowledge ./knowledge
USER node
EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD ["node", "-e", "fetch('http://127.0.0.1:8000/health').then(r => process.exit(r.ok ? 0 : 1), () => process.exit(1))"]
ENTRYPOINT ["node", "dist/index.js"]
CMD ["http"]
