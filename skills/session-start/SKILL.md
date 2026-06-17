---
name: session-start
description: Boot a platform-dev working session in the correct, deterministic order. Use this skill at the START of any session — triggers include "boot", "Session-Boot", "starte die Session", "Sprint N starten", "lade die Tools", pasting a STARTER prompt, or any first message that references the workspace, a branch, a sprint number, or the chat-context steering docs. Use it even when the user just says "weiter wo wir waren" at the top of a fresh chat.
---

# Session Start

Boots a working session for a **platform-dev** workspace in a fixed,
deterministic order. Each step gates the next. The authoritative description of
the lifecycle is `docs/WORKING_CONCEPT.md` §3.1 — this skill is its executable
form.

This skill is **parametric**. It reads the instance's values from `PROJECT.md`
at the repo root (and they are mirrored in the project's runtime instructions):

- `memory_scope` — the memory scope slug to load
- `fs_connector` — the filesystem MCP connector name (typically
  `filesystem-work`)
- `status_tool` — the script-runner status tool to call for git ground-truth
  (default `gitstatus`), provided by `script_runner_server`
- `workspace_root` — the absolute path of the workspace
- `adr_path` — default `spec/docs/adr/`

Never hard-code these. If `PROJECT.md` is not yet read this session, read it
first.

## Boot sequence

Run in order. End with a one-line **boot summary**.

### 1. Load memory (Kumbuka)
Call `memory_load_context` with `scope: <memory_scope>`. This returns the
steering-type digest (decision / constraint / convention / glossary / status).
Then **obey every `type=constraint` entry as a hard rule** for the session.

If the call fails or times out, say so explicitly and continue from the
repository — never silently skip the memory layer (it is also the product under
test; unexpected behaviour is a finding, not a nuisance). See
`docs/WORKING_CONCEPT.md` §10 for the full memory discipline and the
source-of-truth order (spec wins → mnemonics → chat context).

Two standing constraints to surface immediately (WORKING_CONCEPT §13):
notation is alphanumeric only (A1/A2, Variant 1/2/3, Option A/B/C), never Greek
letters; and content goes to git, not to memory — mnemonics are pointers.

### 2. Load the deferred filesystem write tools
The `<fs_connector>` server (the mark3labs `mcp-filesystem-server`,
https://github.com/mark3labs/mcp-filesystem-server) loads its `list_*` tools by
default, but the **write/edit tools are deferred** and need an explicit
`tool_search` before first use:

```
tool_search(query="<fs_connector> write file modify create directory move copy")
```

Do this at boot so closure does not stall later. See `docs/TOOLING.md` for the
connector's quirks (no parent-directory auto-creation; non-recursive
`create_directory`; read-back discipline).

### 3. Confirm the workspace root
Call `<fs_connector>:list_allowed_directories` and confirm `<workspace_root>` is
reachable. Absolute paths are required for every file operation — relative
paths fail.

### 4. Status — ground truth
Call the `<status_tool>` tool (default `gitstatus`) provided by the
`script_runner_server`. It returns the authoritative git state: branch, upstream
ahead/behind, short working-tree status, latest commit, and submodule pointer
alignment (`+` prefix = mismatch). The script-runner runs it from the superrepo
root, so it covers the superrepo and every submodule in one call.

This is the **only** trusted source for workspace state (WORKING_CONCEPT §12).
Read it; do not infer state from the STARTER prose or from memory. Flag any
anomaly (unexpected untracked submodule, `+` pointer, dirty tree) before doing
substantive work — do not write over an unclear state.

### 5. Mandatory reads
Read the steering docs via one batched `read_multiple_files` call (absolute
paths):
- `chat-context/WORKLIST.md` — the `## Pointer` section (next front), `## Aktiv`,
  the wall/active block (schema in WORKING_CONCEPT §11)
- `chat-context/STARTER.md` — the boot pointer the previous session left

If the STARTER names additional mandatory reads (a sprint file, a finding), read
those too in the same batched call.

### 6. Boot summary
Emit one short paragraph: memory loaded + constraints in force · root confirmed ·
status fresh & state (clean / named anomaly) · reads absorbed (one clause each).
Then proceed to the **first decision** — which the STARTER usually pre-stages —
under the `solve-problem` discipline (one decision per turn,
recommendation-first).

## What NOT to do at boot
- Don't produce an overwhelming first turn (full harvest + several decisions at
  once). One thing per turn from the start (WORKING_CONCEPT §4).
- Don't write anything before the status tool confirms a clean/understood state.
- Don't trust the STARTER's prose about branch or commit — verify via the status
  tool.
