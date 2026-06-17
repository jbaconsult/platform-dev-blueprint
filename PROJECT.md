# PROJECT

> Instance configuration for this platform-dev workspace.
> This is the one file that carries everything **not** derivable from the
> structure. The skills in `skills/` read their parameters from here (and these
> values are mirrored into the project's runtime instructions so a session has
> them in context from the first message).
>
> In the blueprint this file is a **template**: the values below are
> placeholders for a fictional `example-project`. When you derive a real
> instance, replace them — and nothing else in the workspace needs to change.

---

## Parameters

These five drive the skills. Replace the `example-project` values.

| Parameter | Value | What it is |
|---|---|---|
| `project_name` | `example-project` | Human-readable name of this instance. Appears in STARTER headers and commit summaries. |
| `memory_scope` | `example-project` | The Kumbuka memory scope slug. `session-start` loads `memory_load_context(scope: <memory_scope>)`; `adr-author` writes mnemonics here. Each instance has its own scope so memories never bleed across projects. |
| `fs_connector` | `filesystem-work` | The filesystem MCP connector name (the mark3labs `mcp-filesystem-server`). Typically constant across all instances on one machine — one connector spans the whole work area. |
| `qs_tool` | `run-qs-dev` | The QS tool-script name. `session-start` and `session-closure` call it for authoritative git state. See `scripts/` for the script it runs. |
| `workspace_root` | `/path/to/work/example-project` | Absolute path to this workspace's root. Every filesystem operation uses absolute paths under this root. |

## Paths

| Path parameter | Value | What it is |
|---|---|---|
| `adr_path` | `spec/docs/adr/` | Where `adr-author` writes ADR documents. Overridable default; lives inside the `spec/` submodule. |
| `increment_branch` | `main` | The day-to-day working branch that closures commit and push to. Reserve a separate branch for milestone completion if the instance wants one (see `WORKING_CONCEPT.md` §12). |

## Memory layer (Kumbuka)

This workspace uses **Kumbuka** (https://kumbuka.ai) as its durable
work-memory. The `memory_scope` above is this instance's scope. The discipline
is in `docs/WORKING_CONCEPT.md` §10:

- Load the typed digest once at session start and obey every `constraint` entry.
- Propose-before-write: state the exact call and wait for a go.
- Mnemonics are pointers, not the record — the spec and the ADRs are the record.
- Source-of-truth order: spec wins → mnemonics → chat context.

If the instance does not use Kumbuka, the `session-start` memory step is
skipped and the workspace operates from the repository alone — but the memory
layer is recommended.

## The spec submodule

This workspace expects a product-specific specification repository mounted as a
git submodule at `spec/`. It holds the ADRs (`spec/docs/adr/`), doctrines, and
the product backlog. Closures that write the submodule use the two-stage git
sequence in `WORKING_CONCEPT.md` §12. If an instance has no separate spec repo,
set `adr_path` to a local directory and use the single-stage closure.

## How the skills use these

| Skill | Reads |
|---|---|
| `session-start` | `memory_scope`, `fs_connector`, `qs_tool`, `workspace_root` |
| `solve-problem` | (method only — no instance params) |
| `session-closure` | `qs_tool`, `fs_connector`, `workspace_root`, `memory_scope`, `increment_branch` |
| `code-handover` | `qs_tool`, `workspace_root` |
| `adr-author` | `adr_path`, `memory_scope`, `fs_connector` |
| `fs-write` | `fs_connector`, `workspace_root` |

---

*To derive an instance: copy the blueprint, replace the `example-project`
values above, point `spec/` at your specification repo, and you are operable.
See `README.md` for the full derivation guide.*
