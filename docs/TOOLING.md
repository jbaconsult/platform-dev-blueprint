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

## Workspace connector — official Anthropic `mcp-filesystem` server

The workspace's filesystem MCP connector is the **official Anthropic
`mcp-filesystem` server**
(https://github.com/modelcontextprotocol/servers/tree/HEAD/src/filesystem),
which replaced the earlier mark3labs `mcp-filesystem-server`. Referred to by the
`fs_connector` parameter in `PROJECT.md` — typically named `workspace`; pick a
connector name that cannot be confused with the ephemeral code-execution
container's own filesystem. Allowed root is set in the server config; absolute
paths are required for every operation.

### Deferred tools
The `list_*` and read tools load by default. The **write, edit, and directory
tools are deferred** — they must be loaded with a `tool_search` before first
use:

```
tool_search(query="<fs_connector> write edit_file create_directory write_file")
```

The `session-start` skill does this at boot so closure does not stall.

### Two structural quirks (verified)
1. **`write_file` does not auto-create parent directories.** Writing
   `a/b/c.md` when `a/b/` does not exist fails with *"parent directory does not
   exist"*. Create the directory chain first.
2. **`create_directory` is documented as recursive** on the official server (it
   can create multiple nested directories in one call) — unlike the mark3labs
   predecessor, which was per-level. Verify at first deep use before relying on
   it; if a deep path fails, fall back to creating each level top-down.

Reliable pattern for a new nested file: ensure the directory chain exists
(`create_directory`), then `write_file`.

### Anchored `edit_file` is the default for existing files
The connector exposes an exact-match in-place edit, `edit_file`
(`path`, `edits` array of `oldText`/`newText`, optional `dryRun`). For any change
to an existing file this is the **default** — it replaces only the matched region
rather than rewriting the whole file, so it is lower-risk on large structured
files (WORKLIST, big docs). `oldText` must match character-for-character
(whitespace, indentation, line breaks); always `dryRun: true` first for complex
multi-line edits to confirm the match. `write_file` (whole-file overwrite) stays
the right tool for **new** files and **small** files where a clean full rewrite
is simpler; treat a whole-file overwrite of a large file as the higher-risk path
(read fresh, rewrite in full, read back). (The mark3labs predecessor had a
regex-anchored `modify_file`; the official server uses exact-match `edit_file`
instead.)

### Read-back discipline
A success message is **not** proof the write landed where intended. After any
`write_file` to a new path, confirm with a targeted `list_directory` or
`get_file_info`; when in doubt, re-read the file. This is the single most
important habit — it catches silent path mistakes before they compound.

**The container trap (recurring — see `constraint.workspace-writes-via-connector-only`).**
Write workspace files ONLY through the filesystem connector
(`write_file`/`edit_file`/`create_directory`). NEVER reach for the computer-use
tools `create_file`/`bash`/`str_replace`: they write to the ephemeral
code-execution container, silently create a look-alike path (e.g.
`<workspace_root>/...` INSIDE the container), and return "success" while the
real machine's tree never receives the file. Symptom: Code or the operator
cannot find a file you "wrote"; `get_file_info` returns ENOENT despite the
success message. The read-back above is what catches it — trust the stat, not
the success line.

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
- **Content limit:** ≤ 1,500 characters per entry. A violation returns a **typed,
  self-explanatory error** with the exact count (e.g. `content too long: max 1500
  characters (was 1610)`) — verified empirically against a live workspace. An older
  note claiming a raw JSON-RPC `-32603` for this case is obsolete; if you still see
  a bare `-32603` on a length violation, that is a regression finding.
- Unexpected behaviour (errors, odd latency, wrong scope visibility) is captured
  as a finding — the memory layer is also a product under test.

---

*Extend this file whenever the apparatus surprises you. A documented quirk is
cheaper than re-discovering it under closure pressure.*
