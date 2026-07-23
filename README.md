# platform-dev-blueprint

A derivable blueprint for an **AI-driven platform development lifecycle**: a
central steering repository with a consolidated working method, a set of skills
that encode it, and the conventions that make a session deterministic from boot
to closure.

You derive a real project from this blueprint, fill in a handful of parameters,
and you are immediately operable — same skills, same lifecycle, same discipline
as every other instance. The method is not theoretical: everything in this repo
has been hardened across more than a hundred sprints of sustained production use
on a real product, and evolutions are backported here once they prove out.

---

## What this is

A **platform-dev** workspace is the *steering layer* for developing a software
platform. It is not the product's source code and not its specification — it is
where architecture is decided, sprints are planned, decisions are recorded as
ADRs, and implementation is dispatched. The product's code lives in its own
repositories; the product's specification lives in the `spec/` submodule.

The method is built around a few firm ideas:

- **One decision per turn, recommendation-first.** Proposals are confirm-or-
  correct, not evaluate-from-scratch.
- **Characterize before you construct.** Map the problem before building the
  solution.
- **Two apparatuses, one boundary.** A concept apparatus (architecture, docs,
  decisions) and an implementation apparatus (program code), handed work via a
  self-contained dispatch — and every dispatch returns through
  `chat-context/handover/`. The steering files have a **single writer**: the
  concept apparatus. Satellite sessions draft; the canonical session ratifies.
- **Document-first decisions.** A ratified decision becomes an ADR or Decision
  document before it becomes a memory note, and every numbered ID comes from
  one registry.
- **A lean, deterministic boot.** A session loads exactly three things — the
  memory digest, the STARTER, and git ground-truth — and cheap-verifies the
  state against a machine-checkable fingerprint instead of re-deriving it.
- **Operator-gated git.** Claude proposes the exact git block; the operator
  executes it. Nothing is committed or pushed without a human hand on it.
- **A durable memory layer.** Distilled, work-steering pointers via
  [Kumbuka](https://kumbuka.ai) — pointers into the record, never the record.

The full method is in **[`docs/WORKING_CONCEPT.md`](docs/WORKING_CONCEPT.md)** —
read it first.

---

## The session lifecycle

Every session follows the same three-phase arc (WORKING_CONCEPT §3):

**Boot (`session-start`).** The STARTER file carries the authoritative boot
sequence. The boot loads exactly three things: the typed memory digest, the
STARTER itself, and status-tool ground-truth. Everything else — backlog,
archive, registry, indices — is pulled when needed, never boot-mandatory. The
previous closure persisted a machine-checkable **repo fingerprint** (per-
submodule SHAs/branches/clean-flags); the boot cheap-verifies live status
against it and only goes verbose where something actually deviates.

**Work (`solve-problem`).** One decision at a time, characterized before
constructed, recommendation-first, measured against the wall where empirical.
Ratified decisions persist document-first (`adr-author`); implementation work
crosses the apparatus boundary as a self-contained dispatch (`code-handover`)
and returns as a structured handover report; tasks are captured through the
`worklist-manager` skill.

**Closure (`session-closure`).** In fixed order: findings, the sprint record,
consolidation of the three task files (finished tasks to the archive, the next
tasks pulled into the Aktiv-Queue), REGISTRY reconciliation, the STARTER
rewritten from its template, then the **operator-gated git block** — Claude
proposes it from verified status, the operator runs it. After the push the
session writes the fresh repo fingerprint and emits the next session's boot
prompt as its final act.

---

## Layout

```
platform-dev/
├── PROJECT.md          instance config — the parameters you fill in
├── CLAUDE.md           Code-apparatus rules, auto-loaded by Claude Code sessions
├── README.md           this file
├── .claude-plugin/     plugin manifest (plugin.json) — packages skills/ for Desktop
├── skills/             the seven skills that encode the lifecycle
├── scripts/            the workspace toolbox — scripts the AI can run for you
│   ├── gitstatus.sh         git ground-truth (superrepo + all submodules)
│   ├── update-git.sh        read-only pull of superrepo + submodules
│   └── mcp-server/          the script-runner MCP server
├── docs/               stable reference
│   ├── WORKING_CONCEPT.md   the method (authoritative)
│   ├── TOOLING.md           how the tools actually behave
│   └── PLUGIN-INSTALL.md    how to install the skills as a Desktop plugin
├── chat-context/       living per-session state (German — it follows the chat language)
│   ├── WORKLIST.md          the Backlog — prioritized task pool (Schema v2, pull-only)
│   ├── STARTER.md           boot doc + Aktiv-Queue (the one boot-loaded task file)
│   ├── ARCHIVE.md           finished tasks + sprint chronicle (pull-only)
│   ├── REGISTRY.md          sole ID-allocation authority for all numbered families
│   ├── TECH-DEBT.md         carry-overs, consulted on touch
│   ├── templates/           frontmatter schemas: starter/task/sprint/finding/handover
│   ├── sprints/             durable sprint records
│   ├── findings/            reported findings
│   └── handover/            Code dispatch/return files, staged for curation
└── spec/               git submodule — your product's specification + ADRs
```

`skills/`, `scripts/`, `docs/`, `chat-context/` sit at the root on purpose — a
visitor sees what the workspace can do at first glance.

### The three content classes
Every file is one of three kinds, by lifespan — **stable reference** (`docs/`),
**living state** (`chat-context/`), or **instance config** (`PROJECT.md`). The
test: *does it change almost every session?* → `chat-context/`; *written once
and referenced?* → `docs/`. See `WORKING_CONCEPT.md` §1.2. Language splits along
the same line (§13): `chat-context/` follows the chat language; `docs/`,
`spec/`, code, and commits are English.

### Two parametric config files
`PROJECT.md` and `CLAUDE.md` both carry the instance parameters (project name,
workspace root, memory scope, status tool, …) and both are **templates** you
fill in when deriving. They serve different readers: **`PROJECT.md`** is read by
the skills (Desktop / concept sessions); **`CLAUDE.md`** is auto-loaded by
**Claude Code** at the top of every Code session and carries the standing
Code-apparatus rules (apparatus boundary, the mandatory handover report,
empirical discipline, the DB-integration-test hard rule, operator-gated git,
read-only memory). Keep their shared values in sync.

---

## The task-file model

The living task state is split across three files with a directed flow —
**Backlog → Aktiv-Queue → Archive** — and strict disjointness: a task lives in
exactly one file at any time (WORKING_CONCEPT §11).

- **`WORKLIST.md` — the Backlog.** The prioritized pool and intake for
  everything new. One Schema-v2 row per task (cluster, components, type,
  priority, size, dispatch target, status, ref), no prose in cells. Pull-only —
  never loaded at boot.
- **`STARTER.md` — the Aktiv-Queue.** The next tasks in execution order, pulled
  from the backlog at closure. The STARTER is the one boot-loaded task file;
  its queue is the execution cursor.
- **`ARCHIVE.md` — the Archive.** Finished tasks as a one-line-plus-link
  retrieval index, plus the sprint chronicle. Appended at closure, searched on
  demand.

Two supporting files keep the model honest: **`REGISTRY.md`** is the sole
allocation authority for every numbered ID family (FEAT/CHORE/BUG/ADR/D-*/F/
Sprint — monotonic, never reused, pulled fresh at the moment of allocation),
and **`TECH-DEBT.md`** holds carry-overs until one grows teeth. The tables are
edited through the `worklist-manager` skill, never by hand.

---

## The skills

Seven skills encode the lifecycle. They trigger automatically by their
description; you do not call them by name. They are **parametric** — they read
their values from `PROJECT.md` and never hard-code a scope, tool, or path.

| Skill | Phase | What it does |
|---|---|---|
| `session-start` | boot | Execute the STARTER-carried boot sequence: memory + constraints, deferred FS tools, root confirm, status tool cheap-verified against the repo fingerprint and the STARTER's stated expectation. |
| `solve-problem` | work | The decision method: one decision per turn, recommendation-first, the five-criteria matrix, empirical discipline, findings vs. decisions. |
| `worklist-manager` | work | The only sanctioned way to edit the Backlog / Aktiv-Queue tables: add, reposition, update markers, archive, promote from tech-debt — propose-before-write, validated, read back. |
| `adr-author` | work | Persist a ratified decision document-first: ADR or Decision (`D-<family>-<n>`) doc + INDEX before the memory pointer, IDs from the REGISTRY, supersession handled both ways. |
| `code-handover` | work | Build a self-contained dispatch to hand an implementation sub-sprint to the code apparatus; dispatch/return files carry a frontmatter lifecycle, every PR is watched to green, every dispatch returns a handover report. |
| `session-closure` | closure | Findings → sprint record → three-file consolidation + REGISTRY → STARTER rewritten from the template → operator-gated git block → post-push repo fingerprint → next boot prompt. |
| `fs-write` | any | The write discipline for the filesystem connector — load deferred tools, prefer anchored `edit_file` for existing files, `dryRun` first, read back after every write. |

A typical day runs `session-start` → `solve-problem` (repeatedly, with
`fs-write` on every write and `worklist-manager` on every task touch) →
optionally `adr-author` and/or `code-handover` → `session-closure`. You don't
steer the order; it follows what you're doing.

The skills are packaged as a **Claude plugin** (`.claude-plugin/plugin.json` +
`skills/`). To make them trigger in a Claude Desktop session, build the plugin
ZIP and upload it via Customize → Skills — see
[`docs/PLUGIN-INSTALL.md`](docs/PLUGIN-INSTALL.md). (Claude Desktop uses a plugin
ZIP, not the `~/.claude/skills/` directory that Claude Code reads.) Give each
instance's plugin a unique `name` (e.g. `<project>-platform-dev`) so two
instances' plugins coexist cleanly in one Desktop account.

---

## Tooling

- **Filesystem:** the official Anthropic
  [`mcp-filesystem` server](https://github.com/modelcontextprotocol/servers/tree/HEAD/src/filesystem),
  one connector spanning the work area. Anchored `edit_file` is the default for
  existing files; `write_file` for new/small files; read-back always. The
  quirks — parent auto-creation, the **container trap** (never write workspace
  files through code-execution container tools), recursive `create_directory` —
  are documented in [`docs/TOOLING.md`](docs/TOOLING.md).
- **Memory:** [Kumbuka](https://kumbuka.ai) — the durable, scoped work-memory.
  Each instance has its own `memory_scope`. Loaded at boot, written
  document-first for decisions, propose-before-write always; the Code apparatus
  reads it scope-pinned and never writes it.
- **Scripts (`scripts/`):** the workspace toolbox. The **script-runner** MCP
  server exposes each script with an `@mcp-tool` header as its own tool, run from
  the superrepo root — so the AI can call them during a session: `gitstatus`
  (git ground-truth), `updategit` (read-only pull of everything), plus your own
  status/build checks. Register each
  instance's server under a unique name (e.g. `scripts-<project>`). See
  [`scripts/README.md`](scripts/README.md) and
  [`scripts/mcp-server/DESIGN.md`](scripts/mcp-server/DESIGN.md).

---

## Deriving an instance

1. **Copy the blueprint** into your workspace (or use it as a GitHub template).
2. **Fill in `PROJECT.md`** — replace the `example-project` placeholders with
   your `project_name`, `memory_scope`, `fs_connector`, `script_runner_server`
   (unique per instance, e.g. `scripts-<project>`), `status_tool`,
   `workspace_root`, and `adr_path`. Mirror these into your project's runtime
   instructions so a session has them from the first message.
3. **Fill in `CLAUDE.md`** — the same instance values in the Code-apparatus rule
   file, so Claude Code sessions boot with the right scope, root, status tool,
   and the standing rules (handover report, apparatus boundary, testing
   discipline, operator-gated git). Keep it in sync with `PROJECT.md`.
4. **Set the instance vocabularies** — the WORKLIST **cluster set** and
   **component tokens** (declared in `PROJECT.md`, used by `worklist-manager`).
   Keep the skill and the WORKLIST header in sync.
5. **Instantiate the STARTER** — copy
   `chat-context/templates/TEMPLATE-starter.md` over `chat-context/STARTER.md`
   and fill the parameters; the (fix) sections are the boot's boilerplate and
   are carried verbatim through every closure from then on.
6. **Mount your repositories** as submodules — `spec/` for the specification
   (ADRs under `spec/docs/adr/`), plus your source and infra repos. See the
   submodule section below. If you have no separate spec repo yet, point
   `adr_path` at a local directory and use single-stage closures.
7. **Set up the tools** — the filesystem connector (point its root at your work
   area), the script-runner server (`scripts/mcp-server/`, registered under your
   unique name), and (recommended) a Kumbuka scope.
8. **Install the skills plugin** — give your plugin a unique `name` in
   `.claude-plugin/plugin.json` (e.g. `<project>-platform-dev`), build the ZIP,
   and upload it in Claude Desktop (`docs/PLUGIN-INSTALL.md`).
9. **Start working** — open a session; `session-start` boots it. Your first
   closure fills the real Aktiv-Queue, and you're rolling.

The blueprint stays neutral and publishable; only `PROJECT.md`, `CLAUDE.md`,
`spec/`, and the instance vocabularies carry anything project-specific.

---

## Submodules — platform-dev as the bracket around your work

`platform-dev` is the **steering layer**, not a monorepo. Your actual
development — source code, specification, infrastructure — lives in its own
repositories, and `platform-dev` pulls them in as **git submodules** so that one
workspace becomes the single bracket around the whole effort. This is the
recommended topology, and it is what makes the tooling (`gitstatus`,
`updategit`) and the git discipline (`WORKING_CONCEPT.md` §12) meaningful.

The idea: from the `platform-dev` root you — and the AI — see and steer every
part of the project at once. A single `gitstatus` call reports the superrepo and
every submodule: which branch each is on, what is uncommitted, whether each
pointer is aligned. A closure that touches a submodule completes that
submodule's feature branch fully before bumping its pointer in the superrepo,
so the recorded state is always coherent — and implementation submodules reach
main only through merged PRs.

### Recommended layout

```
platform-dev/                 the steering bracket (this repo)
├── spec/                     submodule — specification + ADRs (docs/adr/)
├── <product-api>/            submodule — a service / app source repo
├── <product-web>/            submodule — another source repo
├── <infra>/                  submodule — infrastructure-as-code
└── …                         as many as the project needs
```

`spec/` is the one submodule the blueprint assumes by convention: it is where
`adr-author` writes ADRs and Decisions, and it is the only submodule that
commits direct-to-main (a Concept act; everything else goes through PRs). The
rest are yours to add as the project grows.

### Adding submodules

```bash
cd <workspace_root>
git submodule add <git-url> spec
git submodule add <git-url> <product-api>
git commit -m "add submodules: spec, <product-api>"
```

After cloning a platform-dev instance elsewhere, hydrate the submodules:

```bash
git clone <platform-dev-url>
cd <repo>
git submodule update --init --recursive
```

### Working across submodules

- **Status:** `gitstatus` reports the superrepo and all submodules in one call —
  the boot and pre-closure ground-truth check; `updategit` pulls everything
  read-only.
- **Branches:** each submodule has its own branches; a feature spans the
  submodule(s) it touches plus the superrepo pointer. The Code apparatus opens
  PRs on implementation submodules and watches them to green; the operator
  merges.
- **Closure:** two-stage when a submodule changed — finish the submodule's
  feature branch (merge `--no-ff`, push, delete) *before* bumping its pointer in
  the superrepo and committing `chat-context/` (`WORKING_CONCEPT.md` §12). File
  moves and renames ride the git block as `git mv` (§12.1), never as connector
  copy-then-delete.

If a project genuinely has no separate repositories yet, start without submodules
and add them as the work splits out — the structure does not force the bracket,
it enables it.

---

## License

Apache License 2.0 — see [`LICENSE`](LICENSE).
