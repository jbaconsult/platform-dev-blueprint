"""script-runner: expose @mcp-tool scripts in scripts/ as MCP tools."""

from .discovery import ArgSpec, ToolSpec, scan
from .schema import input_schema

__all__ = ["ArgSpec", "ToolSpec", "scan", "input_schema"]
