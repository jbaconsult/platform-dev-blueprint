"""Low-level Server wiring: list_tools / call_tool / stdio (DESIGN §2.7, §3.1, §3.3)."""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import mcp.types as types
from mcp.server.lowlevel import Server
from mcp.server.stdio import stdio_server

from . import exec as runner
from .discovery import ToolSpec, scan
from .schema import input_schema


def _default_scripts_dir() -> Path:
    # The package lives at scripts/mcp-server/script_runner/; the scripts dir is
    # two levels up (scripts/). DESIGN §2.6.
    return Path(__file__).resolve().parents[2]


def _resolve_root(scripts_dir: Path) -> Path:
    override = os.environ.get("SCRIPT_RUNNER_ROOT")
    if override:
        return Path(override)
    try:
        out = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            cwd=str(scripts_dir),
            capture_output=True,
            text=True,
            timeout=10,
        )
        if out.returncode == 0 and out.stdout.strip():
            return Path(out.stdout.strip())
    except (OSError, subprocess.SubprocessError):
        pass
    return scripts_dir.parent  # fallback: parent of scripts/ (DESIGN §2.4)


class Config:
    def __init__(self) -> None:
        env_dir = os.environ.get("SCRIPT_RUNNER_DIR")
        self.scripts_dir = Path(env_dir) if env_dir else _default_scripts_dir()
        self.root = _resolve_root(self.scripts_dir)
        try:
            self.timeout = float(os.environ.get("SCRIPT_RUNNER_TIMEOUT", "120"))
        except ValueError:
            self.timeout = 120.0


def _to_mcp_tool(spec: ToolSpec) -> types.Tool:
    return types.Tool(
        name=spec.name,
        description=spec.description,
        inputSchema=input_schema(spec.args),
    )


def build_server(config: Config | None = None) -> Server:
    cfg = config or Config()
    server: Server = Server("script-runner")
    # Last reported signature set, for list_changed diffing (DESIGN §2.7).
    last_signatures: set[tuple] = set()

    async def _maybe_notify_changed(specs: list[ToolSpec]) -> None:
        nonlocal last_signatures
        current = {s.signature() for s in specs}
        if current != last_signatures:
            last_signatures = current
            try:
                session = server.request_context.session
                await session.send_tool_list_changed()
            except (LookupError, AttributeError):
                # No active request/session context (e.g. unit tests) — nothing to notify.
                pass

    @server.list_tools()
    async def list_tools() -> list[types.Tool]:
        specs = scan(cfg.scripts_dir)
        await _maybe_notify_changed(specs)
        return [_to_mcp_tool(s) for s in specs]

    @server.call_tool()
    async def call_tool(name: str, arguments: dict) -> types.CallToolResult:
        specs = scan(cfg.scripts_dir)
        spec = next((s for s in specs if s.name == name), None)
        if spec is None:
            return types.CallToolResult(
                content=[types.TextContent(type="text", text=f"unknown tool: {name}")],
                isError=True,
            )

        argv = runner.build_argv(spec.args, arguments or {})
        result = runner.run(spec.path, argv, cfg.root, cfg.timeout)

        blocks: list[types.ContentBlock] = [types.TextContent(type="text", text=result.stdout or "")]
        is_error = result.returncode != 0
        if is_error:
            detail = f"\n[exit code: {result.returncode}]"
            if result.stderr:
                detail += f"\n[stderr]\n{result.stderr}"
            blocks.append(types.TextContent(type="text", text=detail))

        # Re-scan after the call so a script that mutates scripts/ surfaces (DESIGN §2.7).
        await _maybe_notify_changed(scan(cfg.scripts_dir))

        return types.CallToolResult(content=blocks, isError=is_error)

    return server


async def main() -> None:
    cfg = Config()
    print(
        f"script-runner: scripts={cfg.scripts_dir} root={cfg.root} timeout={cfg.timeout}s",
        file=sys.stderr,
    )
    server = build_server(cfg)
    async with stdio_server() as (read_stream, write_stream):
        await server.run(read_stream, write_stream, server.create_initialization_options())
