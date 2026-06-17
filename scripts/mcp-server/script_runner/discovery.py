"""Directory scan + header parse → ToolSpec list (DESIGN §2.1, §2.2, §3.3).

A file in the top level of the scripts directory is a tool iff it matches
``*.sh`` and carries a valid ``@mcp-tool:`` header. Files without the header are
ignored; files that opt in (``@mcp-tool`` present) but are malformed are skipped
with an error logged to stderr — fail loud, never expose a half-parsed tool.
"""

from __future__ import annotations

import re
import sys
from dataclasses import dataclass, field
from pathlib import Path

_VALID_TYPES = {"string", "boolean", "integer", "number"}
_TOOL_NAME_RE = re.compile(r"^[a-z0-9_-]+$")
_HEADER_RE = re.compile(r"^\s*#\s*@mcp-(tool|desc|arg)\s*:\s*(.*)$")


class HeaderError(Exception):
    """A file opted in via @mcp-tool but its header is malformed."""


@dataclass(frozen=True)
class ArgSpec:
    name: str
    type: str
    required: bool
    description: str


@dataclass(frozen=True)
class ToolSpec:
    name: str
    description: str
    path: Path
    args: list[ArgSpec] = field(default_factory=list)

    def signature(self) -> tuple:
        """Identity tuple for list_changed diffing (DESIGN §2.7)."""
        return (
            self.name,
            self.description,
            tuple((a.name, a.type, a.required) for a in self.args),
        )


def _leading_comment_lines(path: Path) -> list[str]:
    """Lines of the leading comment block (blanks and ``#`` lines, incl. shebang),
    stopping at the first line of actual code."""
    lines: list[str] = []
    with path.open("r", encoding="utf-8", errors="replace") as fh:
        for raw in fh:
            line = raw.rstrip("\n")
            stripped = line.strip()
            if stripped == "" or stripped.startswith("#"):
                lines.append(line)
                continue
            break
    return lines


def _parse_arg(value: str) -> ArgSpec:
    parts = [p.strip() for p in value.split("|")]
    if len(parts) != 4:
        raise HeaderError(
            f"@mcp-arg needs 4 '|'-separated fields (name|type|required|desc), got {len(parts)}: {value!r}"
        )
    name, type_, requiredness, description = parts
    if type_ not in _VALID_TYPES:
        raise HeaderError(f"@mcp-arg '{name}' has unknown type {type_!r} (allowed: {sorted(_VALID_TYPES)})")
    if requiredness not in {"required", "optional"}:
        raise HeaderError(
            f"@mcp-arg '{name}' field 3 must be 'required' or 'optional', got {requiredness!r}"
        )
    if not name:
        raise HeaderError(f"@mcp-arg has an empty name: {value!r}")
    return ArgSpec(name=name, type=type_, required=(requiredness == "required"), description=description)


def parse_tool(path: Path) -> ToolSpec | None:
    """Parse one file. Returns a ToolSpec, or None if the file does not opt in
    (no @mcp-tool header). Raises HeaderError if it opts in but is malformed."""
    tool_name: str | None = None
    description: str | None = None
    args: list[ArgSpec] = []

    for line in _leading_comment_lines(path):
        m = _HEADER_RE.match(line)
        if not m:
            continue
        key, value = m.group(1), m.group(2).strip()
        if key == "tool":
            if tool_name is not None:
                raise HeaderError(f"{path.name}: duplicate @mcp-tool header")
            if not _TOOL_NAME_RE.match(value):
                raise HeaderError(f"{path.name}: invalid @mcp-tool name {value!r} (want [a-z0-9_-]+)")
            tool_name = value
        elif key == "desc":
            if description is not None:
                raise HeaderError(f"{path.name}: duplicate @mcp-desc header")
            description = value
        elif key == "arg":
            args.append(_parse_arg(value))

    if tool_name is None:
        return None  # not a tool — ignored silently (DESIGN §2.1)
    if not description:
        raise HeaderError(f"{path.name}: @mcp-tool present but @mcp-desc missing")

    return ToolSpec(name=tool_name, description=description, path=path, args=args)


def scan(directory: str | Path) -> list[ToolSpec]:
    """Scan the top level of ``directory`` for tool scripts (DESIGN §2.1).

    Non-recursive: subdirectories (incl. ``mcp-server/``) are never entered.
    Malformed opted-in files are logged to stderr and skipped.
    """
    base = Path(directory)
    tools: list[ToolSpec] = []
    if not base.is_dir():
        print(f"script-runner: scripts dir not found: {base}", file=sys.stderr)
        return tools

    for path in sorted(base.glob("*.sh")):
        if not path.is_file():
            continue
        try:
            spec = parse_tool(path)
        except HeaderError as exc:
            print(f"script-runner: skipping {path.name}: {exc}", file=sys.stderr)
            continue
        if spec is not None:
            tools.append(spec)

    return tools
