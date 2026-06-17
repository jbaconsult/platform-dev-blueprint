# script-runner

An MCP server that turns the workspace's `scripts/` directory into MCP tools.
Every top-level `*.sh` that opts in with an `@mcp-tool` header becomes its own
tool, runnable by the session and executed from the **superrepo root**.

This is the implementation of [`DESIGN.md`](./DESIGN.md) — read that for the full
behaviour specification and rationale.

## What it exposes

The server scans the top level of `scripts/` on every `list_tools` (no watcher).
A file is a tool **iff** it is `*.sh` **and** carries a valid `@mcp-tool:` header:

```bash
# @mcp-tool: gitstatus
# @mcp-desc: Git ground-truth for the superrepo and every submodule …
# @mcp-arg: verbose | boolean | optional | include the full per-repo git status
```

- Files without the header (shared libs, `qs_test.sh`, `*.sh.example` templates)
  are ignored.
- Subdirectories — including this `mcp-server/` package — are never scanned.
- A file that opts in but has a malformed header is skipped and the error is
  logged to stderr (fail loud), so a half-parsed tool is never exposed.

Add a script with the header → it appears as a tool (a `tools/list_changed`
notification is emitted when the set changes). No restart needed.

## Requirements

- Python ≥ 3.11
- `git` and `bash` on `PATH` (the scripts need them anyway)
- One Python dependency: [`mcp`](https://pypi.org/project/mcp/)

## Install

From this directory (`scripts/mcp-server/`):

```bash
# with uv (recommended)
uv venv
uv pip install -e .

# or with pip
python -m venv .venv && . .venv/bin/activate
pip install -e .
```

This installs the `script_runner` package and a `script-runner` console script.

## Run

```bash
python -m script_runner      # stdio transport; logs config to stderr
```

The server speaks MCP over stdio; it is meant to be launched by an MCP client
rather than run by hand. On start it logs the resolved scripts dir, execution
root, and timeout to stderr.

## Configure

All optional, with sane defaults (DESIGN §2.6):

| Env var | Default | Purpose |
|---|---|---|
| `SCRIPT_RUNNER_DIR` | the `scripts/` dir two levels up from the package | directory to scan for tool scripts |
| `SCRIPT_RUNNER_ROOT` | `git rev-parse --show-toplevel` (from `scripts/`), else the parent of `scripts/` | working directory for every script run |
| `SCRIPT_RUNNER_TIMEOUT` | `120` | per-call wall-clock timeout, in seconds |

## Register with an MCP client

Launch `python -m script_runner` over stdio with the working directory at the
workspace. Example client config (Claude Desktop / Claude Code `mcp` block):

```json
{
  "mcpServers": {
    "script-runner": {
      "command": "/abs/path/to/scripts/mcp-server/.venv/bin/python",
      "args": ["-m", "script_runner"],
      "env": {
        "SCRIPT_RUNNER_DIR": "/abs/path/to/scripts"
      }
    }
  }
}
```

Use absolute paths for the interpreter and `SCRIPT_RUNNER_DIR` so the server
resolves the same scripts regardless of where the client launches it. The tools
the client then sees are exactly the `@mcp-tool` scripts in `scripts/` (today:
`gitstatus`).

> Naming note (DESIGN §4): `PROJECT.md` historically names a single `qs_tool` /
> `run-qs-dev`. With script-runner there is no umbrella QS tool — there are
> per-script tools. When an instance adopts script-runner, update `PROJECT.md`
> to name this server and let `session-start` call the specific tool(s) it needs
> (e.g. `gitstatus`).

## Develop / test

```bash
uv pip install -e . pytest
python -m pytest tests/ -q
```

The smoke tests cover parse, schema, exec, and a full in-memory protocol round
trip (see `tests/test_smoke.py`).

## Layout

```
script_runner/
├── __main__.py    entry point: python -m script_runner
├── server.py      low-level Server wiring (list_tools/call_tool/stdio)
├── discovery.py   directory scan + header parse → ToolSpec list
├── schema.py      @mcp-arg lines → JSON-Schema inputSchema
└── exec.py        argv build + subprocess run (cwd, timeout, capture)
```
