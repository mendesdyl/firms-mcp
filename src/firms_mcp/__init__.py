"""FIRMS MCP: a Model Context Protocol server for NASA FIRMS."""

from importlib.metadata import PackageNotFoundError, version

try:
    __version__ = version("firms-mcp")
except PackageNotFoundError:  # pragma: no cover - running from a source tree
    __version__ = "dev"
