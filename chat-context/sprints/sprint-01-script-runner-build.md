# Sprint 01 — script-runner build record

> Build record for the **script-runner** MCP server. Design ratified in
> `scripts/mcp-server/DESIGN.md`; this sprint implements exactly that. The
> package is self-contained under `scripts/mcp-server/` — this record is the only
> chat-context artifact the build produces.

**Apparatus:** code dispatch. **Branch:** `feature/script-runner` (off `main`).
**Gate:** MET.

## What was built

The full package per DESIGN §3.2, on the low-level `mcp.server.Server` API over
stdio (not FastMCP — the tool set is dynamic, built from a directory scan, and
needs `list_changed`):

| File | Role (DESIGN §) |
|---|---|
| `pyproject.toml` | package metadata, `requires-python >=3.11`, single dep `mcp` (§3.4) |
| `script_runner/discovery.py` | top-level `*.sh` scan + `@mcp-*` header parse → `ToolSpec` list; skip non-opt-in files; log+skip malformed (§2.1, §2.2) |
| `script_runner/schema.py` | `@mcp-arg` specs → JSON-Schema `inputSchema` (§2.3) |
| `script_runner/exec.py` | argv build (`name=value`, bare flag for true booleans) + subprocess run with `cwd=root`, timeout, captured stdout/stderr; timeout → synthetic non-zero (§2.4, §2.5) |
| `script_runner/server.py` | `list_tools` (scan+schema, diff signatures, emit `list_changed`), `call_tool` (locate+run+format, `isError` on non-zero), config via env vars, stdio `main` (§2.6, §2.7, §3.3) |
| `script_runner/__main__.py` | entry point `python -m script_runner` (§3.1) |
| `README.md` | install / configure / register-with-client (§3.2) |
| `tests/test_smoke.py` | the four verification tests below |

Key implementation notes:
- **Opt-in trigger** is `@mcp-tool`. A file with it but missing `@mcp-desc` or
  carrying a malformed `@mcp-arg` (wrong field count / unknown type) is a load
  error: skipped + logged to stderr (fail loud). A file without `@mcp-tool` is
  ignored silently.
- **`isError` without raising:** the low-level `call_tool` handler returns a
  `types.CallToolResult(content=…, isError=…)` directly. A non-zero script exit
  is reported faithfully (stdout block + a marked exit-code/stderr block,
  `isError=True`), never raised as a server fault (DESIGN §2.5).
- **list_changed:** the server diffs the `(name, description, arg-signature)`
  set on every `list_tools` and after every `call_tool`; on change it calls
  `session.send_tool_list_changed()`, guarded for the no-session (unit-test) case.

## Smoke-test results — all pass (`python -m pytest tests/ -q` → 11 passed)

1. **Parse:** `scan(scripts/)` finds exactly `gitstatus`; skips `qs_test.sh`
   (no header), `buildhealth.sh.example` (not `*.sh`), and the `mcp-server/`
   subdir (non-recursive). A malformed-header file is skipped + logged, not
   crashed; the sibling good tool still loads.
2. **Schema:** `gitstatus`'s `verbose` → a boolean property; `required` omitted
   when empty; a no-arg script → empty `properties`; a required arg lands in
   `required`.
3. **Exec:** `build_argv` maps `verbose:true`→`["verbose"]`, `false`/absent→`[]`;
   `gitstatus` runs from the superrepo root and returns its report; a non-zero
   script sets the error path and captures stderr separately.
4. **Protocol:** a full in-memory client/server session lists `gitstatus` with
   its description and correct `inputSchema`, and `call_tool("gitstatus", {})`
   returns the git report with `isError=False`. **Chose the real protocol round
   trip** (SDK in-memory session), not a bare handler unit test.

**Gate verification (literal):** `python -m script_runner` launched over **real
stdio** (subprocess + `stdio_client`/`ClientSession`) — initialized, listed
`gitstatus` with the correct boolean `verbose` schema, and the `call_tool`
returned `[superrepo] branch: main …` with `isError=False`. Package also
installs cleanly (`uv pip install -e .`) and imports.

## DESIGN.md gaps found

None. The design was implementable as written; every §2/§3 clause has a
corresponding module and a passing test. No clause required papering over.

## Pointer

Build complete, gate MET. Code is self-contained in `scripts/mcp-server/`; the
git commit block is prepared on `feature/script-runner` but **not pushed**
(operator-gated). Next: operator reviews + pushes, then an instance adopting
script-runner updates `PROJECT.md` per DESIGN §4 (name this server; let
`session-start` call `gitstatus` rather than an umbrella QS tool).
