"""Smoke tests for script-runner (DESIGN Verification §1–4).

Run: `python -m pytest tests/ -q` (or `python tests/test_smoke.py` for a plain run).

Test 4 (Protocol) uses the SDK's in-memory client/server session — a full stdio
round trip — not a hand-rolled handler unit test.
"""

from __future__ import annotations

import os
import tempfile
from pathlib import Path

import anyio
import pytest

from script_runner.discovery import HeaderError, parse_tool, scan
from script_runner.exec import build_argv, run
from script_runner.schema import input_schema
from script_runner.server import Config, build_server

SCRIPTS_DIR = Path(__file__).resolve().parents[2]  # repo scripts/
REPO_ROOT = SCRIPTS_DIR.parent


# --- Test 1: Parse (DESIGN §2.1, §2.2) ---------------------------------------

def test_scan_finds_only_tool_scripts():
    specs = scan(SCRIPTS_DIR)
    names = {s.name for s in specs}
    assert "gitstatus" in names
    # qs_test.sh has no @mcp-tool header; buildhealth is *.sh.example (not *.sh);
    # mcp-server/ is a subdir and never scanned.
    assert all(s.path.name != "qs_test.sh" for s in specs)
    assert all(not s.path.name.endswith(".example") for s in specs)
    assert all(s.path.parent == SCRIPTS_DIR for s in specs)


def test_malformed_header_is_skipped_not_crash(capsys):
    with tempfile.TemporaryDirectory() as d:
        good = Path(d) / "good.sh"
        good.write_text("#!/usr/bin/env bash\n# @mcp-tool: good\n# @mcp-desc: ok\n")
        bad = Path(d) / "bad.sh"
        # 3 fields instead of 4 → malformed @mcp-arg → load error for this tool.
        bad.write_text("# @mcp-tool: bad\n# @mcp-desc: nope\n# @mcp-arg: x | string | optional\n")
        specs = scan(d)
        names = {s.name for s in specs}
        assert names == {"good"}  # bad skipped, good survives
        err = capsys.readouterr().err
        assert "bad.sh" in err  # logged to stderr (fail loud)


def test_non_tool_file_is_ignored_silently():
    with tempfile.TemporaryDirectory() as d:
        lib = Path(d) / "lib.sh"
        lib.write_text("#!/usr/bin/env bash\n# just a helper, no header\n")
        assert scan(d) == []


def test_unknown_arg_type_raises_headererror():
    with tempfile.TemporaryDirectory() as d:
        p = Path(d) / "t.sh"
        p.write_text("# @mcp-tool: t\n# @mcp-desc: d\n# @mcp-arg: a | wat | optional | x\n")
        with pytest.raises(HeaderError):
            parse_tool(p)


# --- Test 2: Schema (DESIGN §2.3) --------------------------------------------

def test_gitstatus_verbose_is_boolean_property():
    spec = next(s for s in scan(SCRIPTS_DIR) if s.name == "gitstatus")
    schema = input_schema(spec.args)
    assert schema["type"] == "object"
    assert schema["properties"]["verbose"]["type"] == "boolean"
    # verbose is optional → not in required (and required key omitted when empty)
    assert "required" not in schema


def test_no_arg_script_has_empty_properties():
    with tempfile.TemporaryDirectory() as d:
        p = Path(d) / "noargs.sh"
        p.write_text("# @mcp-tool: noargs\n# @mcp-desc: d\n")
        spec = scan(d)[0]
        schema = input_schema(spec.args)
        assert schema["properties"] == {}


def test_required_arg_listed_in_required():
    with tempfile.TemporaryDirectory() as d:
        p = Path(d) / "r.sh"
        p.write_text("# @mcp-tool: r\n# @mcp-desc: d\n# @mcp-arg: n | string | required | name\n")
        schema = input_schema(scan(d)[0].args)
        assert schema["required"] == ["n"]


# --- Test 3: Exec (DESIGN §2.4, §2.5) ----------------------------------------

def test_build_argv_boolean_and_value():
    spec = next(s for s in scan(SCRIPTS_DIR) if s.name == "gitstatus")
    assert build_argv(spec.args, {"verbose": True}) == ["verbose"]
    assert build_argv(spec.args, {"verbose": False}) == []
    assert build_argv(spec.args, {}) == []


def test_gitstatus_runs_from_root_and_returns_stdout():
    spec = next(s for s in scan(SCRIPTS_DIR) if s.name == "gitstatus")
    result = run(spec.path, [], REPO_ROOT, timeout=60)
    assert result.returncode == 0
    assert "[superrepo] branch:" in result.stdout


def test_nonzero_exit_sets_error_and_includes_stderr():
    with tempfile.TemporaryDirectory() as d:
        p = Path(d) / "fail.sh"
        p.write_text("#!/usr/bin/env bash\necho out\necho boom >&2\nexit 3\n")
        result = run(p, [], d, timeout=60)
        assert result.returncode == 3
        assert "out" in result.stdout
        assert "boom" in result.stderr


# --- Test 4: Protocol (DESIGN §3.1, §3.3) ------------------------------------

def test_protocol_list_and_call():
    from mcp.shared.memory import create_connected_server_and_client_session

    async def scenario():
        cfg = Config()
        cfg.scripts_dir = SCRIPTS_DIR
        cfg.root = REPO_ROOT
        cfg.timeout = 60.0
        server = build_server(cfg)
        async with create_connected_server_and_client_session(server) as client:
            tools = await client.list_tools()
            by_name = {t.name: t for t in tools.tools}
            assert "gitstatus" in by_name
            gs = by_name["gitstatus"]
            assert gs.description
            assert gs.inputSchema["properties"]["verbose"]["type"] == "boolean"

            res = await client.call_tool("gitstatus", {})
            assert res.isError is False
            text = "".join(c.text for c in res.content if c.type == "text")
            assert "[superrepo] branch:" in text

    anyio.run(scenario)


if __name__ == "__main__":
    import sys

    sys.exit(pytest.main([__file__, "-q"]))
