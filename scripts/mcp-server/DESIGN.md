# script-runner — DESIGN

> The build document for the **script-runner** MCP server. It is both the
> ratifiable specification (what the server does and why) and the implementation
> brief (how it is built). The subsequent code dispatch implements exactly this.
>
> Status: ratified design, pending implementation.

---

## 1. Purpose

`script-runner` turns the workspace's `scripts/` directory into a set of MCP
tools. Every script that opts in with an `@mcp-tool` header is exposed to the
session as its own tool, runnable by the AI, executed from the **superrepo
root**. It is the mechanism that bundles a project's heterogeneous helper
scripts (git status, build-health, and whatever else the developer needs) behind
one server, consistently across instances (Forgenesis, Kumbuka, …).

It is **not** a QS-specific server. QS (status reporting) is one kind of script;
the server is agnostic to what a script does.

## 2. Behaviour specification

### 2.1 Tool discovery (the opt-in)
- The server scans the **top level** of the `scripts/` directory only — not
  recursively. Its own subdirectory (`scripts/mcp-server/`) and any other
  subdirectory are therefore never scanned.
- A file is a tool **iff** it matches `*.sh` **and** contains a valid
  `@mcp-tool:` header line. Files without the header (shared libraries meant to
  be `source`d, the `qs_test.sh` helper, `*.example` templates) are ignored.
- The scan runs on **every `list_tools` request** (cheap: one directory listing
  plus a header parse of a handful of files). There is no filesystem watcher.

### 2.2 Header format
Header lines are shell comments near the top of the script. Recognized keys:

```
# @mcp-tool: <name>
# @mcp-desc: <one-line description>
# @mcp-arg: <name> | <type> | <required|optional> | <description>
```

- `@mcp-tool:` (required, exactly one) — the MCP tool name. Lowercase,
  `[a-z0-9_-]+`. If absent or malformed, the file is not a tool.
- `@mcp-desc:` (required, exactly one) — the tool description shown to the AI.
- `@mcp-arg:` (optional, zero or more, one per argument) — four `|`-separated
  fields: `name | type | required|optional | description`.
  - `type` ∈ {`string`, `boolean`, `integer`, `number`} (JSON-Schema scalars).
  - whitespace around fields and around `|` is trimmed.

A malformed `@mcp-arg` line (wrong field count, unknown type) is a **load
error** for that tool: the tool is skipped and the error is logged to stderr so
it surfaces — fail-loud, never silently expose a half-parsed tool.

### 2.3 inputSchema derivation
From the `@mcp-arg` lines the server builds the tool's JSON-Schema `inputSchema`:
- each arg → a property of the declared `type`;
- `required` args → listed in the schema's `required` array;
- `description` → the property's `description`;
- a tool with no `@mcp-arg` lines → `inputSchema` with empty `properties`.

### 2.4 Execution
- The server resolves the **superrepo root** once at startup via
  `git rev-parse --show-toplevel` (run from the `scripts/` directory). Fallback:
  the parent of `scripts/`. This is the working directory for every script run.
- On `call_tool(name, arguments)`:
  - locate the script whose `@mcp-tool` name matches `name` (re-scan if needed);
  - build the argv: each declared argument present in `arguments` becomes a
    `name=value` token (booleans present-and-true become the bare `name`; absent
    args are omitted), forwarded after the script path;
  - run the script with `cwd = superrepo_root`, capturing stdout and stderr
    separately;
  - apply a wall-clock **timeout** (default 120 s, see §2.6);
  - return the result (§2.5).
- Execution uses `bash <script>` (so a missing executable bit is not a failure)
  unless the file is executable, in which case it is run directly.

### 2.5 Result shape
`call_tool` returns MCP text content:
- stdout as the primary text block;
- if the script exited non-zero, append a clearly marked block with the exit
  code and the captured stderr;
- the MCP `isError` flag is set when the exit code is non-zero.

Reporting, not gating: a non-zero exit is reported faithfully, not swallowed and
not raised as a server fault.

### 2.6 Configuration
Environment variables (all optional, sane defaults):
- `SCRIPT_RUNNER_DIR` — the scripts directory to scan. Default: the directory
  containing the server package's parent (i.e. `scripts/`). Lets an instance
  point the server at a non-default location.
- `SCRIPT_RUNNER_ROOT` — override the execution root. Default: the
  `git rev-parse` result described in §2.4.
- `SCRIPT_RUNNER_TIMEOUT` — per-call timeout in seconds. Default: `120`.

### 2.7 list_changed
The server tracks the set of `(name, description, arg-signature)` tuples it last
reported. On each `list_tools` (and after each `call_tool`), it re-scans; if the
set changed, it emits a `notifications/tools/list_changed` so the client
refreshes. This gives "add a script → it appears as a tool" without a restart,
without a filesystem watcher.

## 3. Implementation

### 3.1 Foundation
- **Library:** the official `mcp` Python SDK (`modelcontextprotocol/python-sdk`).
- **API level:** the **low-level `mcp.server.Server`**, not `FastMCP` —
  `FastMCP` assumes statically decorated tools, whereas our tool set is dynamic
  (built from a directory scan) and needs `list_changed`. The low-level API is
  built for exactly this: `@server.list_tools()` returns the current scan,
  `@server.call_tool()` dispatches by name.
- **Transport:** stdio (`mcp.server.stdio`), the standard for a local server
  launched by the client. No SSE/HTTP.

### 3.2 Project layout
```
scripts/mcp-server/
├── pyproject.toml            package metadata + dependency on `mcp`
├── README.md                 how to install, configure, register
├── DESIGN.md                 this document
└── script_runner/
    ├── __init__.py
    ├── __main__.py           entry point: `python -m script_runner`
    ├── server.py             low-level Server wiring (list_tools/call_tool/stdio)
    ├── discovery.py          directory scan + header parse → ToolSpec list
    ├── schema.py             @mcp-arg lines → JSON-Schema inputSchema
    └── exec.py               argv build + subprocess run (cwd, timeout, capture)
```

### 3.3 Key modules
- **`discovery.py`** — `scan(dir) -> list[ToolSpec]`. Globs top-level `*.sh`,
  reads each file's leading comment block, parses `@mcp-*` keys. A `ToolSpec`
  holds `name`, `description`, `args: list[ArgSpec]`, and the script `path`.
  Skips files without `@mcp-tool`; logs and skips malformed ones.
- **`schema.py`** — `input_schema(args) -> dict`. Maps `ArgSpec`s to a
  JSON-Schema object (`type: object`, `properties`, `required`).
- **`exec.py`** — `run(script_path, args, root, timeout) -> RunResult`. Builds
  argv (`name=value` / bare-flag for true booleans), runs via `subprocess.run`
  with `cwd=root`, `capture_output=True`, `timeout`, `text=True`. Returns
  stdout, stderr, returncode (timeout → a synthetic non-zero result with a clear
  message).
- **`server.py`** — instantiates `Server("script-runner")`; `list_tools` calls
  `discovery.scan` + `schema.input_schema`, diffs against the last set, emits
  `list_changed` on change; `call_tool` re-locates the script, calls
  `exec.run`, formats the MCP result (§2.5). Runs over stdio in `__main__`.

### 3.4 Dependencies & runtime
- Python ≥ 3.11. Single runtime dependency: `mcp`. `git` and `bash` available on
  PATH (the scripts need them anyway).
- Installed/declared via `pyproject.toml`; runnable as `python -m script_runner`.

## 4. MCP registration
The server is registered with the client as the instance's `qs_tool`-providing
server (the name is historical; it provides *all* script tools, not only QS).
Registration launches `python -m script_runner` over stdio with the working
directory at the workspace, optionally setting the §2.6 environment variables.
The tools the client then sees are exactly the `@mcp-tool` scripts in `scripts/`.

> Naming note: `PROJECT.md` currently calls the QS entry `qs_tool` /
> `run-qs-dev`. With script-runner there is no single "qs" tool — there are
> per-script tools (`gitstatus`, …). When an instance adopts script-runner,
> update `PROJECT.md` to name the server and let `session-start` call the
> specific tool(s) it needs (e.g. `gitstatus`) rather than one umbrella QS tool.

## 5. Out of scope (for the first build)
- No filesystem watcher (scan-on-list is sufficient).
- No collective "run all" tool (ratified: one tool per script).
- No SSE/HTTP transport.
- No per-script sandboxing beyond the timeout (the scripts are the developer's
  own, run locally).
