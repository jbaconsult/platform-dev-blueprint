# TOOLING

> How the apparatus actually behaves — the hard-won operational knowledge for
> the tools this workspace runs on. Stable reference: written from experience,
> referenced often, extended whenever a new quirk is found. The `fs-write`
> skill is the working summary of the write rules below; this file is the
> canonical record and carries the reasoning and the edge cases.

When you hit a new tool behaviour worth remembering, add it here and (if it
changes a write rule) reflect it in the `fs-write` skill. Tool behaviour is part
of the apparatus; documenting it is real work, not overhead.

---

## Filesystem connector — mark3labs `mcp-filesystem-server`

The workspace's filesystem MCP connector is the mark3labs
`mcp-filesystem-server` (https://github.com/mark3labs/mcp-filesystem-server).
Referred to by the `fs_connector` parameter in `PROJECT.md` (typically
`filesystem-work`). Allowed root is set in the server config; absolute paths are
required for every operation.

### Deferred tools
The `list_*` and read tools load by default. The **write, edit, and directory
tools are deferred** — they must be loaded with a `tool_search` before first
use:

```
tool_search(query="<fs_connector> write file modify create directory move copy")
```

The `session-start` skill does this at boot so closure does not stall.

### Two structural quirks (verified)
1. **`write_file` does not auto-create parent directories.** Writing
   `a/b/c.md` when `a/b/` does not exist fails with *"parent directory does not
   exist"*. Create the directory chain first.
2. **`create_directory` is not recursive.** Each level is created individually —
   `chat-context/`, then `chat-context/sprints/`. A deep path in one call fails
   on the missing intermediate.

Reliable pattern for a new nested file: create each directory level top-down,
then `write_file`.

### No sectional-edit tool
The `filesystem-work` connector exposes `write_file` (whole-file write), not a
sectional find/replace edit. Every change to an existing file is a full
overwrite: read the current content, modify it in full, write it back — there is
no anchored in-place edit. Keep large files (e.g. WORKLIST) structured so a
whole-file rewrite stays manageable, and always read the file fresh before
overwriting so no concurrent change is lost. (This differs from earlier
connectors that had a `modify_file`; do not assume one exists. Note: the host
may also offer a generic `str_replace`/`view` pair, but those act on a separate
container filesystem, not on the connector's work area — they will not edit
these files.)

### Read-back discipline
A success message is **not** proof the write landed where intended. After any
`write_file` to a new path, confirm with a targeted `list_directory`; when in
doubt, re-read the file. This is the single most important habit — it catches
silent path mistakes before they compound.

### Other notes
- Run one session against the connector at a time; parallel sessions sharing one
  server can contend.
- The connector may have no delete tool — the operator removes files manually
  (e.g. a `git rm` in the closure block).
- Very large directory listings can be slow or unwieldy — use targeted
  `read_multiple_files` from a known index rather than listing a huge folder.

---

## Status tooling — the script-runner server

Status checks are MCP tools provided by the **script-runner** server
(`scripts/mcp-server/`, the `script_runner_server` parameter in `PROJECT.md`).
Each `@mcp-tool` script in `scripts/` is exposed as its own tool, run from the
superrepo root. There is no single umbrella "QS tool" — status checks are
individual tools called by name.

The lifecycle's git ground-truth comes from the `status_tool` (default
`gitstatus`): branch, upstream ahead/behind, short working-tree status, latest
commit, and submodule pointer alignment (a `+` prefix marks a pointer/HEAD
mismatch). Because the script-runner runs it from the superrepo root, one call
covers the superrepo and every submodule. It is the **only trusted source for
workspace state** (`WORKING_CONCEPT.md` §12) — never infer state from prose or
memory.

Call the status tool at session boot (`session-start`) and again immediately
before generating any git block (`session-closure`). After the operator runs a
git block, a follow-up call confirms the clean end state. See
`scripts/mcp-server/DESIGN.md` for the server and `scripts/README.md` for the
`@mcp-tool` script convention.

---

## Memory connector (Kumbuka)

Kumbuka (https://kumbuka.ai) provides the durable work-memory. Discipline:
`WORKING_CONCEPT.md` §10.

- `memory_load_context(scope: <memory_scope>)` returns the steering-type digest
  (decision / constraint / convention / glossary / status); `open_question` is
  excluded by default — pass it explicitly to review what is open.
- `memory_recall` does topic lookups; `memory_remember` writes (propose-before-
  write); `memory_forget` removes a keyed entry (entries are insert-only, so a
  revision is forget + fresh write).
- Keys are lowercase with dot/hyphen separators, no underscores.
- Unexpected behaviour (errors, odd latency, wrong scope visibility) is captured
  as a finding — the memory layer is also a product under test.

---

*Extend this file whenever the apparatus surprises you. A documented quirk is
cheaper than re-discovering it under closure pressure.*
