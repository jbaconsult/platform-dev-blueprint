---
name: fs-write
description: The write discipline for the filesystem MCP connector — load deferred write/edit tools, prefer anchored edit_file for existing files, whole-file write_file for new files, write_file does not auto-create parents, read-back after every write. Use this skill whenever you are about to write or edit a file in the workspace — triggers include "schreib die Datei", "editier", "edit_file", "write_file", "create_directory", "speichern", "parent directory does not exist", or any closure/doc step that lands content on disk. Use it before the first write of a session, not after a failure.
---

# Filesystem Write Discipline

Disk writes for the workspace go through the **official Anthropic `mcp-filesystem` server**
(https://github.com/modelcontextprotocol/servers/tree/HEAD/src/filesystem).
Its allowed root is set at the server config (typically the whole work area);
absolute paths are required. The canonical, evolving record of quirks is
`docs/TOOLING.md` — this skill is the working summary.

Parametric over `PROJECT.md`: `fs_connector`, `workspace_root`.

## Before the first write: load the deferred tools
The connector's `list_*` and read tools load by default, but the
**write/edit/directory tools are deferred** and need a `tool_search` before use
(the `session-start` skill does this at boot):

```
tool_search(query="<fs_connector> write edit_file create_directory write_file")
```

**Boot-confirm the edit tool.** This connector exposes an exact-match in-place
edit tool (`edit_file`). The exact parameter shape is what `tool_search` returns
— read it off the live schema, do not assume from memory.

## Structural characteristics of the official server

### 1. `write_file` does NOT auto-create parent directories
Writing to `a/b/c.md` when `a/b/` does not exist fails with
*"parent directory does not exist"*. Create the directory chain first.

### 2. `create_directory` behavior (non-recursive model TBD)
Verify at first use whether intermediate directories must be created
individually or whether the server auto-creates the chain. **Update `docs/TOOLING.md`
with empirical findings.**

### 3. `edit_file` uses exact-match text replacement, NOT regex
The new tool differs fundamentally from mark3labs `modify_file`:

- **Parameters:** `path`, `edits` (array), optional `dryRun`.
- **Each edit:** `oldText` (exact string match) and `newText` (replacement).
- **No regex anchoring.** The `oldText` must match character-for-character,
  including whitespace, indentation, and line breaks.
- **Multi-match behavior:** Unclear at this version. **Empirically verify:**
  - Does it replace all occurrences or only the first?
  - Does it error if `oldText` is found multiple times?
  Test at first live use and document in `docs/TOOLING.md`.

**Consequence for editing style:**
- For multi-line replacements, you must include the exact line breaks and
  indentation in both `oldText` and `newText`.
- Carriage returns, spaces, tabs all matter — copy-paste directly from a fresh
  read of the file.
- For safety, always do a `dryRun: true` first to verify the match before
  committing the edit.

## Editing existing files — prefer the exact-match edit

The connector **does** expose an exact-match in-place edit (`edit_file`). For
changes to an existing file this is the **default tool**: it edits a matched
region rather than rewriting the whole file, so it is lower-risk on large files
and does not silently clobber content outside the matched region.

`write_file` (whole-file overwrite) remains available and is the right tool for:
- **new files** (STARTER, PROJECT, a fresh doc), and
- **small files** where a clean full rewrite is simpler than exact-matching.

Consequences for the working style:
- **For existing files, reach for `edit_file` first.** A targeted exact-match
  edit on a large structured file (WORKLIST, big docs) is the *low*-risk write;
  a full `write_file` overwrite of such a file is the *higher*-risk one, because
  it is only as current as your last read and replaces everything at once.
- **Always read the relevant region immediately before editing it**, so your
  `oldText` matches current content exactly and no concurrent change is lost.
- When you *do* overwrite a whole file, treat it as the higher-risk path: read
  fresh, modify in full, write back — and read-back the whole file after.

## Read-back is mandatory

A success message is not proof the write landed where you think. After any
`write_file` to a new path, confirm via `list_directory` (targeted) and, if in
doubt, re-read the file. After an `edit_file` edit, re-read the changed region
to confirm the `oldText` match succeeded and nothing adjacent was disturbed.
This is the single most important habit — see `docs/TOOLING.md`.

**Always use `dryRun: true` first for complex multi-line edits.** The diff
output shows exactly what will change before you commit.

## Large-file reads

If a read returns a "result too large" sentinel, fall back to a targeted read
(known line/section) rather than pulling the whole file. Avoid directory
listings on very large folders — use targeted `read_multiple_files` from a known
index instead.

## Operational notes

- Keep one session active against the connector at a time; parallel sessions
  sharing one server can contend.
- The connector may lack a delete tool — the operator removes files manually
  (e.g. a `git rm` in the closure block).
- Record any new quirk you hit as a finding and fold it into `docs/TOOLING.md`;
  the connector is part of the apparatus and its behaviour is dogfooding
  evidence.

---
**Migration note from mark3labs:** The official server replaces mark3labs
`mcp-filesystem-server`. Key changes: `modify_file` → `edit_file`,
regex anchoring → exact-match text replacement, `oldText`/`newText` parameters.
Multiline handling is text-exact (no regex flags). Multi-match behaviour TBD —
verify empirically and pin into `docs/TOOLING.md`. All other structural quirks
(parent auto-create, recursive `create_directory`, mandatory read-back) carry
over; verify at first use.
