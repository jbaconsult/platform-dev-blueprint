---
name: fs-write
description: The write discipline for the filesystem MCP connector — load deferred write/edit tools, create directories non-recursively, write_file does not auto-create parents, read-back after every write. Use this skill whenever you are about to write or edit a file in the workspace — triggers include "schreib die Datei", "editier", "write_file", "create_directory", "speichern", "parent directory does not exist", or any closure/doc step that lands content on disk. Use it before the first write of a session, not after a failure.
---

# Filesystem Write Discipline

Disk writes for the workspace go through the **`fs_connector`** MCP server — the
mark3labs `mcp-filesystem-server`
(https://github.com/mark3labs/mcp-filesystem-server). Its allowed root is set at
the server config (typically the whole work area); absolute paths are required.
The canonical, evolving record of quirks is `docs/TOOLING.md` — this skill is
the working summary.

Parametric over `PROJECT.md`: `fs_connector`, `workspace_root`.

## Before the first write: load the deferred tools
The connector's `list_*` and read tools load by default, but the
**write/edit/directory tools are deferred** and need a `tool_search` before use
(the `session-start` skill does this at boot):

```
tool_search(query="<fs_connector> write file modify create directory move copy")
```

## The two structural quirks (mark3labs server)
1. **`write_file` does NOT auto-create parent directories.** Writing to
   `a/b/c.md` when `a/b/` does not exist fails with *"parent directory does not
   exist"*. Create the directory chain first.
2. **`create_directory` is NOT recursive.** Each level must be created
   individually: `chat-context/`, then `chat-context/sprints/`. Creating a deep
   path in one call fails on the missing intermediate.

So the reliable pattern for a new nested file is: create each directory level
top-down, then `write_file`.

## Editing existing files — whole-file only
The connector exposes **`write_file` (whole-file write), not a sectional
find/replace edit.** Every change to an existing file is a full overwrite:
**read the current content fresh, modify it in full, write it back.** There is
no anchored in-place edit — do not assume a `modify_file`/`str_replace` exists
on this connector (a host may offer a generic `str_replace`/`view` pair, but
those act on a separate container filesystem, not the connector's work area, and
will not edit these files).

Consequences for the working style:
- **Always read the file immediately before overwriting it**, so no concurrent
  change is lost — the overwrite is only as current as your last read.
- **Keep large files (WORKLIST, big docs) well-structured** so a whole-file
  rewrite stays manageable and low-risk. A very large rewrite is the
  higher-risk write; if a file grows unwieldy, that is a signal to split it.
- For new files and small files (STARTER, PROJECT) the whole-file write is
  straightforward.

## Read-back is mandatory
A success message is not proof the write landed where you think. After any
`write_file` to a new path, confirm via `list_directory` (targeted) and, if in
doubt, re-read the file. After overwriting an existing file, re-read the changed
region. This is the single most important habit — see `docs/TOOLING.md`.

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
