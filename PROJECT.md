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

These drive the skills. Replace the `example-project` values.

| Parameter | Value | What it is |
|---|---|---|
| `project_name` | `example-project` | Human-readable name of this instance. Appears in STARTER headers and commit summaries. |
| `memory_scope` | `example-project` | The Kumbuka memory scope slug. `session-start` loads `memory_load_context(scope: <memory_scope>)`; `adr-author` writes mnemonics here. Each instance has its own scope so memories never bleed across projects. |
| `fs_connector` | `filesystem-work` | The filesystem MCP connector name (the mark3labs `mcp-filesystem-server`). Typically constant across all instances on one machine — one connector spans the whole work area. |
| `script_runner_server` | `script-runner` | The MCP server (in `scripts/mcp-server/`) that exposes each `@mcp-tool` script in `scripts/` as its own tool. There is no single "QS tool" — status checks are individual tools (`gitstatus`, …) called by name. |
| `status_tool` | `gitstatus` | The script-runner tool the lifecycle uses for git ground-truth. `session-start` and `session-closure` call this tool by name for authoritative state. Defaults to `gitstatus`; an instance may point it at a richer status tool. |
| `workspace_root` | `/path/to/work/example-project` | Absolute path to this workspace's root. Every filesystem operation uses absolute paths under this root. |

## Paths

| Path parameter | Value | What it is |
|---|---|---|
| `adr_path` | `spec/docs/adr/` | Where `adr-author` writes ADR documents. Overridable default; lives inside the `spec/` submodule. |
| `increment_branch` | `main` | The day-to-day working branch that closures commit and push to. Reserve a separate branch for milestone completion if the instance wants one (see `WORKING_CONCEPT.md` §12). |

## Tooling: the script-runner server

Status and other helper scripts in `scripts/` are exposed as MCP tools by the
**script-runner** server (`scripts/mcp-server/`, see its `DESIGN.md`). Each
script carrying an `@mcp-tool` header becomes one tool, run from the superrepo
root. The lifecycle does not call a single "QS tool"; it calls the specific tool
it needs — `status_tool` (`gitstatus`) for git ground-truth at boot and before
closures, and any other script tools as the work requires. Register the server
with your client and keep `script_runner_server` / `status_tool` in sync with
it.

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
| `session-start` | `memory_scope`, `fs_connector`, `status_tool`, `workspace_root` |
| `solve-problem` | (method only — no instance params) |
| `session-closure` | `status_tool`, `fs_connector`, `workspace_root`, `memory_scope`, `increment_branch` |
| `code-handover` | `status_tool`, `workspace_root` |
| `adr-author` | `adr_path`, `memory_scope`, `fs_connector` |
| `fs-write` | `fs_connector`, `workspace_root` |

---

*To derive an instance: copy the blueprint, replace the `example-project`
values above, point `spec/` at your specification repo, register the
script-runner server, and you are operable. See `README.md` for the full
derivation guide.*
