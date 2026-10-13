# FIRMS MCP server: Streamable HTTP on port 8000 with the MAP_KEY connect flow.
#
#   docker build -t firms-mcp .
#   docker run -p 8000:8000 \
#     -e FIRMS_MCP_PUBLIC_URL=https://firms-mcp.example.org \
#     -e FIRMS_MCP_TOKEN_KEYS="$(docker run --rm firms-mcp keygen)" firms-mcp
#
# Configuration: docs/developers/CONFIGURATION.md; deployment: docs/design/AUTHENTICATION.md.

FROM python:3.13-slim-bookworm AS build
COPY --from=ghcr.io/astral-sh/uv:0.13.0 /uv /bin/uv
ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PYTHON_DOWNLOADS=never
WORKDIR /app
# Dependencies first, so source changes do not invalidate the dependency layer.
COPY pyproject.toml uv.lock README.md ./
RUN uv sync --locked --no-install-project --no-editable
COPY src ./src
COPY knowledge ./knowledge
# Install the project as a wheel: the knowledge base ships inside the package (ADR-0005).
RUN uv sync --locked --no-editable

FROM python:3.13-slim-bookworm
RUN useradd --create-home --uid 10001 --shell /usr/sbin/nologin firms
COPY --from=build --chown=firms:firms /app/.venv /app/.venv
ENV PATH="/app/.venv/bin:${PATH}" \
    PYTHONUNBUFFERED=1 \
    FIRMS_MCP_HOST=0.0.0.0 \
    FIRMS_MCP_PORT=8000
USER firms
WORKDIR /home/firms
EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD ["python", "-c", "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health', timeout=4)"]
ENTRYPOINT ["firms-mcp"]
CMD ["http"]
