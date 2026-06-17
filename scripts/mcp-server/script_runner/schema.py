"""@mcp-arg specs → JSON-Schema inputSchema (DESIGN §2.3, §3.3)."""

from __future__ import annotations

from collections.abc import Iterable

from .discovery import ArgSpec


def input_schema(args: Iterable[ArgSpec]) -> dict:
    """Build a JSON-Schema object from the declared arguments.

    Each arg becomes a typed property; required args are listed in ``required``.
    A tool with no args yields an object with empty ``properties``.
    """
    properties: dict[str, dict] = {}
    required: list[str] = []
    for arg in args:
        prop: dict = {"type": arg.type}
        if arg.description:
            prop["description"] = arg.description
        properties[arg.name] = prop
        if arg.required:
            required.append(arg.name)

    schema: dict = {"type": "object", "properties": properties}
    if required:
        schema["required"] = required
    return schema
