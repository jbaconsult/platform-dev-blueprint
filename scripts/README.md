# scripts/ — tools the AI can run for you

This directory holds the scripts a platform developer needs while working with
the AI. Each script with a valid `@mcp-tool` header is exposed by the
**script-runner** MCP server (in `mcp-server/`) as its own MCP tool, so the AI
can call it directly during a session.

Scripts are not limited to any one purpose. Status reporting (QS — "where do we
stand", "does it still build") is one kind; any repeatable command the AI should
be able to run for you belongs here.

---

## How it works

The **script-runner** server (`mcp-server/`, Python) scans this directory on
startup, reads each tool script's header, and registers one MCP tool per script.
It runs each script with the working directory set to the **superrepo root**
(resolved via `git rev-parse --show-toplevel`), so scripts act on the whole
workspace and its submodules regardless of where they live. The server also
emits `tools/list_changed` when the set of scripts changes, so a newly added
script becomes available without a restart.

See `mcp-server/README.md` for the server's design and configuration.

```
scripts/
├── mcp-server/               the script-runner MCP server (Python)
├── gitstatus.sh              tool: git ground-truth (superrepo + submodules)
├── buildhealth.sh.example    template for an instance-specific build-health tool
├── qs_test.sh                offline test helper (runs all tool scripts locally)
└── README.md                 this file
```

---

## The header convention (tool opt-in)

A script becomes a tool **only** if it carries a valid `@mcp-tool` header. This
is the opt-in: shared helper libraries (meant to be `source`d) and templates
have no header and are never exposed. Filenames carry no meaning beyond
readability — there is no ordering, no numeric prefix; the header is the truth.

```bash
#!/usr/bin/env bash
#
# @mcp-tool: gitstatus
# @mcp-desc: Git ground-truth for the superrepo and every submodule.
# @mcp-arg: verbose | boolean | optional | include the full git status
# @mcp-arg: module  | string  | optional | restrict to a single module
```

Header fields:
- **`@mcp-tool:`** — the tool name (required). Lowercase, no spaces.
- **`@mcp-desc:`** — one-line description shown to the AI (required).
- **`@mcp-arg:`** — one line **per argument** (optional, repeatable), four
  fields separated by `|`:
  `name | type | required|optional | description`.
  `type` is a JSON-Schema scalar (`string`, `boolean`, `integer`, `number`).
  The server builds each tool's `inputSchema` from these lines.

A script with no `@mcp-tool` line is ignored by both the server and `qs_test.sh`.

---

## Argument passing

The server passes a tool's declared arguments to the script as positional
arguments / `name=value` tokens. By convention every script **tolerates unknown
arguments** — it reads what it understands and ignores the rest — so a script is
never broken by an argument meant for a sibling. Keep `set -u` if you like; avoid
`set -e` where you want to report despite a partial failure.

---

## Adding a tool

1. Create `scripts/<name>.sh`.
2. Add the `@mcp-tool` / `@mcp-desc` / `@mcp-arg` header.
3. Write the body. Report clearly; run from the superrepo root (the server sets
   cwd there). Tolerate unknown arguments. Surface errors concisely (e.g. the
   first N error lines on failure, full log only on `verbose`).
4. `chmod +x` is optional — the runner falls back to `bash <file>`.
5. Smoke-test locally with `bash scripts/qs_test.sh` before the server picks it
   up, or just let the server re-scan (`tools/list_changed`).

---

## Bundled scripts

### `gitstatus.sh`
Git ground-truth for the superrepo and every submodule: branch, upstream
ahead/behind, short working-tree status, latest commit, and submodule pointer
alignment. `verbose` switches to the full `git status`. Runs cleanly with or
without submodules. This is the QS boot/closure check (`WORKING_CONCEPT.md` §12).

### `buildhealth.sh.example`
A **template** (not an active tool — the `.example` suffix keeps it out of the
scan) showing how to write an instance-specific build-health check: run the
project's build/verify, report pass/fail, surface the first error lines on
failure, change no committed state. Copy to `buildhealth.sh` and adapt to the
instance's stack (Maven, npm/tsc, gradle, …) when deriving a project.

### `qs_test.sh`
**Offline test helper**, not the production path. Discovers the same
`@mcp-tool` scripts the server would, runs each from the superrepo root, and
prints a labelled report — for smoke-testing a script before the server exposes
it. The server is the authority on what becomes a tool.

---

*This directory is the workspace's toolbox. When a command proves repeatedly
useful in a session, capture it as a script here with an `@mcp-tool` header so
it becomes a standing, one-call tool the AI can reach for.*
