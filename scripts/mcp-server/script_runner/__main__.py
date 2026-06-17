"""Entry point: ``python -m script_runner`` (stdio transport, DESIGN §3.1)."""

from __future__ import annotations

import anyio

from .server import main


def run() -> None:
    anyio.run(main)


if __name__ == "__main__":
    run()
