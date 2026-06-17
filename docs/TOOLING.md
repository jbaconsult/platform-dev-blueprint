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

### Read-back discipline
A success message is **not** proof the write landed where intended. After any
`write_file` to a new path, confirm with a targeted `list_directory`; when in
doubt, re-read the file. This is the single most important habit — it catches
silent path mistakes before they compound.

### Editing files
- Small files (STARTER, PROJECT): a whole-file `write_file` is reliable.
- Large files (WORKLIST, large docs): prefer sectional edits over a full
  rewrite; a wholesale rewrite of a large file is the higher-risk path. Anchor
  edits on a structurally distinctive, byte-exact string.
- A "zero changes" / no-op edit means the anchor did not match (often the file
  changed under you). Read fresh, retry with a shorter unique anchor; never
  assume it landed.

### Other notes
- Run one session against the connector at a time; parallel sessions sharing one
  server can contend.
- The connector may have no delete tool — the operator removes files manually.
- Very large directory listings can be slow or unwieldy — use targeted
  `read_multiple_files` from a known index rather than listing a huge folder.

---

## QS tool

The QS tool (the `qs_tool` parameter, e.g. `run-qs-dev`) reports authoritative
git state: branch, recent commits, submodule HEADs, pointer alignment (a `+`
prefix marks a pointer/HEAD mismatch), and working-tree status. It is the **only
trusted source for workspace state** (`WORKING_CONCEPT.md` §12) — never infer
state from prose or memory.

Call it at session boot (`session-start`) and again immediately before
generating any git block (`session-closure`). After the operator runs a git
block, a follow-up QS call confirms the clean end state.

The QS tool is a thin wrapper that runs a status script in `scripts/` and
returns its output. Its consolidation (one wrapper, modular sub-scripts) is a
separate design track — see `scripts/` and the project's own notes when that is
built.

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
