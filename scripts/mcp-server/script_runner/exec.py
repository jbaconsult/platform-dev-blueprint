"""argv build + subprocess run with cwd, timeout, capture (DESIGN §2.4, §2.5, §3.3)."""

from __future__ import annotations

import os
import subprocess
from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from pathlib import Path

from .discovery import ArgSpec


@dataclass(frozen=True)
class RunResult:
    stdout: str
    stderr: str
    returncode: int
    timed_out: bool = False


def build_argv(specs: Iterable[ArgSpec], arguments: Mapping[str, object]) -> list[str]:
    """Turn declared args + provided values into script argv tokens (DESIGN §2.4).

    Each declared arg present in ``arguments`` → a ``name=value`` token; a boolean
    that is present-and-true → the bare ``name``; a boolean that is false (or any
    absent arg) is omitted.
    """
    argv: list[str] = []
    for spec in specs:
        if spec.name not in arguments:
            continue
        value = arguments[spec.name]
        if spec.type == "boolean":
            if _as_bool(value):
                argv.append(spec.name)
            # false → omitted
        else:
            argv.append(f"{spec.name}={value}")
    return argv


def _as_bool(value: object) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.strip().lower() in {"true", "1", "yes"}
    return bool(value)


def run(
    script_path: str | Path,
    argv: list[str],
    root: str | Path,
    timeout: float,
) -> RunResult:
    """Run ``script_path`` from ``root`` with ``argv``, capturing output.

    Uses ``bash <script>`` unless the file is executable, in which case it is run
    directly (so a missing executable bit is not a failure). A timeout yields a
    synthetic non-zero result with a clear message rather than an exception.
    """
    script = Path(script_path)
    if os.access(script, os.X_OK):
        cmd = [str(script), *argv]
    else:
        cmd = ["bash", str(script), *argv]

    try:
        proc = subprocess.run(
            cmd,
            cwd=str(root),
            capture_output=True,
            text=True,
            timeout=timeout,
        )
    except subprocess.TimeoutExpired as exc:
        partial = exc.stdout or ""
        partial_err = exc.stderr or ""
        if isinstance(partial, bytes):
            partial = partial.decode("utf-8", "replace")
        if isinstance(partial_err, bytes):
            partial_err = partial_err.decode("utf-8", "replace")
        return RunResult(
            stdout=partial,
            stderr=(partial_err + f"\nscript-runner: timed out after {timeout}s").strip(),
            returncode=124,
            timed_out=True,
        )

    return RunResult(stdout=proc.stdout, stderr=proc.stderr, returncode=proc.returncode)
