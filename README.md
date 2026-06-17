# platform-dev-blueprint

A derivable blueprint for an **AI-driven platform development lifecycle**: a
central steering repository with a consolidated working method, a set of skills
that encode it, and the conventions that make a session deterministic from boot
to closure.

You derive a real project from this blueprint, fill in a handful of parameters,
and you are immediately operable — same skills, same lifecycle, same discipline
as every other instance.

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
  self-contained dispatch.
- **Document-first decisions.** A ratified decision becomes an ADR document
  before it becomes a memory note.
- **A durable memory layer.** Distilled, work-steering pointers via
  [Kumbuka](https://kumbuka.ai) — pointers into the record, never the record.

The full method is in **[`docs/WORKING_CONCEPT.md`](docs/WORKING_CONCEPT.md)** —
read it first.

---

## Layout

```
platform-dev/
├── PROJECT.md          instance config — the parameters you fill in
├── README.md           this file
├── skills/             the six skills that encode the lifecycle
├── scripts/            the workspace toolbox — scripts the AI can run for you
├── docs/               stable reference
│   ├── WORKING_CONCEPT.md   the method (authoritative)
│   └── TOOLING.md           how the tools actually behave
├── chat-context/       living per-session state
│   ├── WORKLIST.md          ## Pointer / ## Aktiv / ## Archiv
│   ├── STARTER.md           boot pointer
│   ├── sprints/             durable sprint records
│   └── findings/            reported findings
└── spec/               git submodule — your product's specification + ADRs
```

`skills/`, `scripts/`, `docs/`, `chat-context/` sit at the root on purpose — a
visitor sees what the workspace can do at first glance.

### The three content classes
Every file is one of three kinds, by lifespan — **stable reference** (`docs/`),
**living state** (`chat-context/`), or **instance config** (`PROJECT.md`). The
test: *does it change almost every session?* → `chat-context/`; *written once
and referenced?* → `docs/`. See `WORKING_CONCEPT.md` §1.2.

---

## The skills

Six skills encode the lifecycle. They trigger automatically by their
description; you do not call them by name. They are **parametric** — they read
their values from `PROJECT.md` and never hard-code a scope, tool, or path.

| Skill | Phase | What it does |
|---|---|---|
| `session-start` | boot | Load memory + constraints, load deferred FS tools, confirm root, run QS, read steering docs, boot summary. |
| `solve-problem` | work | The decision method: one decision per turn, recommendation-first, the five-criteria matrix, empirical discipline, findings vs. decisions. |
| `session-closure` | closure | Findings → sprint file → WORKLIST (with archiving) → STARTER → operator-gated git block → next starter prompt. |
| `code-handover` | work | Build a self-contained dispatch to hand an implementation sub-sprint to the code apparatus. |
| `adr-author` | work | Persist a ratified decision document-first: ADR doc before the memory pointer, supersession handled both ways. |
| `fs-write` | any | The write discipline for the filesystem connector — load deferred tools, create dirs non-recursively, read back after every write. |

A typical day runs `session-start` → `solve-problem` (repeatedly, with
`fs-write` in the background on every write) → optionally `adr-author` and/or
`code-handover` → `session-closure`. You don't steer the order; it follows what
you're doing.

---

## Tooling

- **Filesystem:** the mark3labs
  [`mcp-filesystem-server`](https://github.com/mark3labs/mcp-filesystem-server),
  one connector spanning the work area. Its quirks (no parent auto-creation,
  non-recursive `create_directory`, read-back discipline) are documented in
  [`docs/TOOLING.md`](docs/TOOLING.md).
- **Memory:** [Kumbuka](https://kumbuka.ai) — the durable, scoped work-memory.
  Each instance has its own `memory_scope`. Loaded at boot, written
  document-first for decisions, propose-before-write always.
- **Scripts (`scripts/`):** the workspace toolbox. The **script-runner** MCP
  server exposes each script with an `@mcp-tool` header as its own tool, run from
  the superrepo root — so the AI can call them during a session. Status checks
  (QS — git ground-truth via `gitstatus`, build-health, …) are one kind; any
  repeatable command belongs here. See [`scripts/README.md`](scripts/README.md).

---

## Deriving an instance

1. **Copy the blueprint** into your workspace (or use it as a GitHub template).
2. **Fill in `PROJECT.md`** — replace the `example-project` placeholders with
   your `project_name`, `memory_scope`, `fs_connector`, `qs_tool`,
   `workspace_root`, and `adr_path`. Mirror these into your project's runtime
   instructions so a session has them from the first message.
3. **Mount your repositories** as submodules — `spec/` for the specification
   (ADRs under `spec/docs/adr/`), plus your source and infra repos. See the
   submodule section below. If you have no separate spec repo yet, point
   `adr_path` at a local directory and use single-stage closures.
4. **Set up the tools** — the filesystem connector (point its root at your work
   area), the script-runner server (`scripts/mcp-server/`), and (recommended) a
   Kumbuka scope.
5. **Start working** — open a session; `session-start` boots it. Your first
   closure writes the real `## Pointer`, and you're rolling.

The blueprint stays neutral and publishable; only `PROJECT.md` and `spec/` carry
anything project-specific.

---

## Submodules — platform-dev as the bracket around your work

`platform-dev` is the **steering layer**, not a monorepo. Your actual
development — source code, specification, infrastructure — lives in its own
repositories, and `platform-dev` pulls them in as **git submodules** so that one
workspace becomes the single bracket around the whole effort. This is the
recommended topology, and it is what makes the tooling (`gitstatus`) and the
two-stage git discipline (`WORKING_CONCEPT.md` §12) meaningful.

The idea: from the `platform-dev` root you — and the AI — see and steer every
part of the project at once. A single `gitstatus` call reports the superrepo and
every submodule: which branch each is on, what is uncommitted, whether each
pointer is aligned. A closure that touches a submodule completes that submodule's
feature branch fully before bumping its pointer in the superrepo, so the recorded
state is always coherent.

### Recommended layout

```
platform-dev/                 the steering bracket (this repo)
├── spec/                     submodule — specification + ADRs (docs/adr/)
├── <product-api>/            submodule — a service / app source repo
├── <product-web>/            submodule — another source repo
├── <infra>/                  submodule — infrastructure-as-code
└── …                         as many as the project needs
```

`spec/` is the one submodule the blueprint assumes by convention (it is where
`adr-author` writes ADRs). The rest are yours to add as the project grows.

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
  the boot and pre-closure ground-truth check.
- **Branches:** each submodule has its own branches; a feature spans the
  submodule(s) it touches plus the superrepo pointer.
- **Closure:** two-stage when a submodule changed — finish the submodule's
  feature branch (merge `--no-ff`, push, delete) *before* bumping its pointer in
  the superrepo and committing `chat-context/` (`WORKING_CONCEPT.md` §12).

If a project genuinely has no separate repositories yet, start without submodules
and add them as the work splits out — the structure does not force the bracket,
it enables it.

---

## License

Apache License 2.0 — see [`LICENSE`](LICENSE).
