# WORKING_CONCEPT

> The consolidated working method for a **platform-dev** workspace.
> This document is the single, authoritative description of *how we work*.
> It is blueprint-generic: it describes the method, not any one product.
> Product-specific decisions live in the `spec/` submodule; the living work
> state lives in `chat-context/`; this file is stable reference and changes
> rarely.

**Status:** authoritative · **Scope:** the whole workspace · **Audience:**
anyone deriving or operating a platform-dev instance, human or AI.

Sections are stable, numbered anchors. Skills, commit messages, and findings
cite them as `WORKING_CONCEPT §N`. Do not renumber casually — references
depend on the numbers.

---

## Table of contents

- §1 Purpose & applicability
- §2 The apparatus model
- §3 Session lifecycle
- §4 Turn discipline (ratify-before-execute)
- §5 Decision method
- §6 Empirical discipline
- §7 Architecture doctrines
- §8 Findings vs. decisions
- §9 ADR-first persistence
- §10 Memory discipline
- §11 The task-file model (Backlog · Aktiv-Queue · Archive)
- §12 Git discipline
- §13 Language & notation
- §14 Handover to Code (§17 dispatch)
- §15 Glossary

---

## §1 Purpose & applicability

### §1.1 What this workspace is

A **platform-dev** workspace is the central repository for the development of a
software platform. It is not the product's source code and not its
specification — it is the *steering layer*: the place from which architecture
is decided, sprints are planned, decisions are recorded, and implementation is
dispatched. The product's code lives in its own repositories; the product's
specification lives in the `spec/` submodule. This repo holds the method and
the moving state of the work.

This repository is published as a **derivable blueprint**. A new project does
not invent its own way of working — it derives a platform-dev instance from the
blueprint, fills in a few parameters, and is immediately operable with the same
skills, the same lifecycle, and the same discipline as every other instance.

### §1.2 The three content classes

Every file in the workspace belongs to exactly one of three classes,
distinguished by a single criterion — **lifespan and change frequency**, not
topic:

1. **Stable reference → `docs/`.** Written once, referenced often, changes
   rarely, worth publishing. A newcomer reads `docs/` to understand the
   blueprint. This file lives here. So does `TOOLING_LL.md` and the derivation
   guide.
2. **Living state → `chat-context/`.** Changes in nearly every session, makes
   sense only for the running work, nobody reads it "from outside". The skills
   read and write it constantly: `WORKLIST.md`, `STARTER.md`, `sprints/`,
   `findings/`.
3. **Instance configuration → `PROJECT.md`** (repo root). The parameters plus
   paths. Static; changes only when the instance itself changes.

The test for any file: *Does it change almost every session?* → `chat-context/`.
*Written once and then referenced?* → `docs/`. *Would a new user of the
blueprint want to read it?* → `docs/`.

### §1.3 Workspace topology

```
platform-dev/                 central repository, published as blueprint
├── README.md                 entry point + derivation guide
├── PROJECT.md                instance config: the params + paths
├── skills/                   start / closure / solve / handover / adr / fs-write
├── scripts/                  QS wrapper + modular sub-scripts
├── docs/                     stable reference (this file, TOOLING_LL, guides)
├── chat-context/             living per-session state
│   ├── WORKLIST.md           ## Backlog — pull-only task pool (see §11)
│   ├── STARTER.md            boot doc + ## Aktiv-Queue (active execution queue)
│   ├── ARCHIVE.md            finished tasks + sprint chronicle (pull-only)
│   ├── REGISTRY.md           sole ID-allocation authority (all numbered families)
│   ├── TECH-DEBT.md          carry-overs, consulted on touch (pull-only)
│   ├── templates/            TEMPLATE-starter/task/sprint/finding/handover
│   ├── sprints/              sprint-NN-<slug>.md  (durable sprint records)
│   ├── findings/             <slug>.md, sec-*.md
│   └── handover/             Code-return reports, staged for curation (§14)
└── spec/                     git submodule — product-specific
    └── docs/
        ├── adr/              ADRs (see §9)
        └── …                 doctrines, epics, capabilities, features
```

`skills/`, `scripts/`, `docs/`, `chat-context/` sit at the root deliberately —
a visitor to the repository sees what the workspace *can do* at first glance,
without digging.

### §1.4 The instance parameters

Everything that is not derivable from the structure is captured in
`PROJECT.md` and mirrored into the project's runtime instructions:

| Parameter | What it is | Example (Forgenesis) |
|---|---|---|
| `project_name` | Human name of the instance | `Forgenesis` |
| `memory_scope` | Memory scope slug | `forgenesis` |
| `fs_connector` | Filesystem MCP connector name | `filesystem-work` |
| `qs_tool` | QS tool-script name | `run-qs-dev` |

Plus `workspace_root` (absolute path) and `adr_path` (overridable default
`spec/docs/adr/`). The skills are parametric over these — they never hard-code a
scope, tool, or path. Note that `fs_connector` is typically constant across all
instances on one machine (a single filesystem connector spanning the whole work
area); the values that genuinely vary per instance are `memory_scope`,
`qs_tool`, and `workspace_root`.

---

## §2 The apparatus model

Work happens across two apparatuses with a hard boundary between them.

**Desktop (concept apparatus)** — architecture decisions, sprint planning,
specification and schema work, markdown documentation, helper-script design,
orchestration. Desktop holds the overview. It does **not** write program code.

**Code (implementation apparatus)** — all program code: application sources,
build descriptors, infrastructure-as-code, test code, pipeline runs,
measurements. Code executes autonomously against a self-contained dispatch and
returns a pointer (see §14).

The boundary is by **artifact type**, not by difficulty: anything that is
`.java`/`.ts`/`.py`/`.hcl`/`.tf`/`pom.xml`/`package.json` or a code-bearing
submodule edit is Code apparatus, even if it looks trivial. Anything that is a
decision, a markdown document, a schema, or a steering-file edit is Desktop, even
if it is hard.

Why the split: the concept apparatus keeps the overview and the discipline; the
implementation apparatus keeps the focus and the measurement. Mixing them lets
implementation detail erode architectural clarity and lets architecture churn
destabilize measurement.

### §2.1 Steering-file ownership — Desktop is the single writer

The living state in `chat-context/` (`WORKLIST.md`, `STARTER.md`, `sprints/`,
`findings/`) is written **exclusively by the Desktop apparatus.** Code never edits
a steering file — not even a correct, surgical edit, not even its own sprint
record. Code returns results as a **handover** (§14.3); Desktop folds them into
the steering files.

*Reason:* multiple Code instances may run in parallel. The steering layer is only
coherent if it has a single writer — concurrent Code edits to `WORKLIST.md` would
race, and the central overview (the whole point of the Desktop apparatus) would
fragment. The artifact-type rule in §2 already places steering-file edits on the
Desktop side; this makes the consequence explicit and unconditional: **a
steering-file edit by Code is a boundary violation regardless of how small or
correct the edit is.** If Code observes that a steering file is stale, it says so
in its handover return — it does not fix it.

### §2.2 Parallel sessions & cross-session input

Work on a platform may run across **several parallel sessions** at once — one
canonical steering session plus one or more **satellite sessions**, each
discussing a particular topic in depth. Satellites are legitimate and useful:
they think, they design, and they may deliver **draft artifacts** into the
workspace through the normal channel — a written ADR document, a Code dispatch,
a finding. The filesystem is the delivery mechanism; an artifact appearing on
disk is the input *arriving*, not the input being *accepted*.

The rule is the **single-writer principle of §2.1 raised one level** — from the
steering *files* to the steering *record itself*:

- **Cross-session input is a draft by default.** A satellite session produces a
  **proposal or a finding (§8)**, never a ratification — *regardless of how
  thoroughly the topic was discussed in that session*. An ADR delivered by a
  satellite arrives at status `proposed`; a handover that tells the implementer
  "do not re-litigate" is **advisory**, not an acceptance.
- **Ratification and the canonical record are single-writer.** Promoting a draft
  to ratified — flipping an ADR to `Accepted`, writing the `INDEX` row (§9), the
  pointer mnemonic (§10), the WORKLIST integration (§11) — happens **only in the
  canonical steering session**. This is the same coherence guarantee as §2.1: if
  N sessions could each declare "ratified", there would be N truths and no
  record.
- **The canonical session re-derives ground truth.** It does not take a
  satellite's "ratified" or "done" at face value — the §14.3 control-check
  applied to cross-session input: read the artifact, confirm it against the spec
  and the standing constraints, *then* ratify and persist.

A satellite session never writes memory, never edits a steering file, and never
moves an artifact into the canonical record. It drafts; the canonical session
signs. (Operationally this also respects the one-active-connector-session rule
of the filesystem write discipline — concurrent steering writers contend.)

---

## §3 Session lifecycle

Every session follows the same three-phase arc. Each phase has a skill that
encodes its deterministic steps.

### §3.1 Boot (`session-start`)

In fixed order: load memory (and obey its constraints) → load the deferred
filesystem write tools → confirm the workspace root → run QS for ground-truth
state → read the STARTER → emit a one-line boot summary. Only then does
substantive work begin. State is never inferred from prose — only the QS tool is
ground truth.

**The boot loads exactly three things: the memory digest, the STARTER, and QS
ground-truth.** Everything else is pulled when needed, never boot-mandatory: the
WORKLIST backlog and ARCHIVE at closure, the REGISTRY on ID allocation, the INDEX
files on decision work, this document on method doubt. Keeping the boot to three
loads is deliberate — the STARTER carries the forward briefing and the active
queue (§11.2); loading the backlog and reference corpus on every boot is the
context-flooding failure this three-load model exists to prevent.

As an optimization, the previous closure persists a machine-checkable **repo
fingerprint** in the memory digest (per-submodule SHAs/branches/clean-flags; for
the superrepo only branch+clean, never its own HEAD). The boot does not
re-derive full verbose state — it cheap-verifies the live QS against this
fingerprint. This is not "trusting prose": the fingerprint is a checkable claim
and the boot checks it. **Branch on tool presence first:** QS tool absent (a
reduced runtime, e.g. a mobile/web session) → the fingerprint is the sole,
unverified anchor; proceed concept-only, no git/host mutation. QS tool present →
verify: match → proceed at near-zero cost; mismatch → that delta is the signal,
go verbose there and nowhere else.

### §3.2 Work (`solve-problem`)

The substantive middle of the session: one decision at a time, characterized
before constructed, recommendation-first, measured against the wall where
empirical (§4–§7).

### §3.3 Closure (`session-closure`)

In fixed order: write findings → write the sprint record → consolidate the task
files (§11: pull the next task(s) from the WORKLIST backlog into the STARTER's
`## Aktiv-Queue`, removed from the backlog; move each finished task to ARCHIVE.md)
→ rewrite STARTER → run QS → emit the operator-gated git block → emit the next
session's starter prompt as the final act, immediately preceded — after the
operator's push — by writing the repo fingerprint to memory from a post-push QS
read-back. Nothing follows the starter prompt.

**File moves and renames are deferred to the git block (§12.1), not executed
through the filesystem connector during the session.** When closure consumes a
handover (moving it to `handover/_consumed/`), retires or renames a doc, or a
spec-corpus cleanup renames ledgers, the move is *proposed* as a `git mv` line in
the operator-gated git block — it is not done mid-session as a connector
copy-then-delete. *Reason:* `git mv` preserves history (Git records a rename, not
a delete-plus-new file), and it avoids the error-prone whole-file copy the
connector forces (a re-typed copy can silently drop or truncate content). The
session may still *write* new files and *edit* existing ones through the
connector; only **moving and renaming** is reserved for the git block.

Sub-decisions that crossed the apparatus boundary are dispatched to Code
(`code-handover`, §14) during the work phase, not at closure. Where a Code
sub-sprint has returned, closure also **curates its handover report** from
`chat-context/handover/` into the durable record (the sprint file, a finding, or
a decision note) and **prunes the consumed report** — `handover/` is a staging
area, not the record (§14.3).

---

## §4 Turn discipline (ratify-before-execute)

The core interaction contract. Claude **proposes** → the operator **confirms**
(`mach` / `weiter` / `ja` / `passt`) → Claude **executes** the write → the
operator **validates**. Four rules apply inside every turn:

1. **One decision per turn.** Exactly one ratifiable decision. No multi-level
   proposals, no question catalogue at turn-end. If a decision implies
   follow-ups, ratify each one separately in its own turn. *Reason:*
   multi-decision turns produce long question lists that get half-answered,
   leaving the state underspecified.

2. **Spell out abbreviations on first use.** First mention in a turn writes the
   full term with the acronym in parentheses — *"Architecture Context Model
   (ACM)"*. The acronym alone is fine afterward in the same turn. *Reason:*
   reduces the reader's cognitive load; they should not reconstruct what each
   acronym means.

3. **State location and purpose before the decision.** Each proposal begins by
   naming **where** the decision sits (which series, which front, which
   document, what status quo) and **what purpose** it serves (what gap it
   closes, what risk it mitigates, what it unblocks). *Reason:* context is the
   precondition for ratification — the reader should not reconstruct it from
   memory.

4. **Always recommend with rationale.** Each proposal ends with a concrete
   recommendation (which variant, which scope, which next step) plus the
   reasoning — not a bare enumeration. The reader overrides or confirms; the
   default path is unambiguous. *Reason:* enumeration without recommendation
   pushes the decision burden back onto the operator for every minor choice;
   recommendation lets ratification be a confirm-or-correct action.

**Ratification signals.** `mach` / `weiter` confirm the current recommendation.
After ratification, Claude executes autonomously up to the next genuine decision
point — it does not re-ask for confirmation of fully-rationalized sub-steps.

**Velocity-Mode.** When sub-decisions are fully rationalized and their
alternatives clearly non-competitive, proceed without individual ratification.
Only ask when there is a genuine specification alternative not derivable from
existing documentation. Never present options for the sake of presenting
options — match the operator's careful, methodical standard rather than padding
with proposals.

**No silent regeneration.** Workspace-internal artifacts (plans, concepts,
backlog items, generated code) are never silently regenerated. The operator sees
every diff before it is applied, every plan change before re-execution, every
modification proposal before the write.

---

## §5 Decision method

### §5.1 Characterize before you construct

*Charakterisieren-vor-konstruieren.* Pin the root, the wall, the actual
constraint **before** proposing a construction. The problem space is mapped
first; the solution is its consequence. A proposal that constructs before it
characterizes is premature, however elegant.

### §5.2 The five-criteria decision matrix

For any non-trivial model or architecture decision, build a variant matrix with
at least these five columns, evaluated **in lexicographic order** — criterion 1
first, then 2, only breaking ties downward:

1. **Minimize misunderstandings.** Fewest ambiguities for all readers, human
   and machine. Ambiguity cascades — one ambiguous field poisons every
   traceability chain built on it — so it outranks everything.
2. **Internal consistency.** Fewest mismatches between meta-schema, models,
   docs, and examples.
3. **Sustainability / reversibility.** Carries long-term across expansion
   stages; additive change preferred over structural break. When 1–3 are
   otherwise even, reversibility is the tiebreaker: how hard is it to withdraw
   the decision in 6–12 months? This favours new-feature/new-node-type over
   renamed-concept/new-model.
4. **Machine readability.** Graph-queryable, structured, validatable,
   generator-friendly. Above human readability on purpose — the AI does the
   main work; the human edits, the machine masters the graph.
5. **Human readability.** Clearest for architects and analysts to read and
   edit.

The recommendation goes to the variant that wins by lexicographic order. State
the matrix; do not hide the reasoning behind a verdict.

### §5.3 Recommendation-first

Every decision turn ends on one concrete recommendation with its rationale
(§4.4). The matrix supports the recommendation; it does not replace it.

### §5.4 Cluster-end reflection

When work is structured into clusters of sub-decisions (typical for concept
sessions), each cluster ends with a short reflection: what was achieved ·
identified ambiguities and deferred items · which ambiguities need follow-up and
which are acceptable to defer · the state of the roadmap. After the last cluster
of a concept, a **final cross-cluster reflection** checks inter-cluster
consistency before the document is finalized. These reflections are mandatory,
not optional — they catch integration gaps that single-cluster work cannot see.

---

## §6 Empirical discipline

Applies whenever a decision is tested against a running pipeline or system
rather than reasoned in the abstract.

- **Empirie-first.** Build only against empirical wall evidence. Treat a wall as
  real only at **n ≥ 2**; one datapoint is a candidate, not a fact.
- **Predict-then-measure.** State the expected outcome *before* the run. A
  measurement that confirms an unstated expectation proves less.
- **NULL-FIX discipline.** Exactly one variable changes per measurement series.
  No mid-series hotfixes between the n runs of a stage. The guarantee lives in
  the gate, not in the fix.
- **Localize before you build.** Pin the root first, then fix minimally and
  non-duplicatively. Dispatch hypotheses are guidance — localization may refute
  them, and that is a valid result.
- **Optionsraum-Disziplin (option-space discipline).** Paths whose empirical
  validation is not intact are pre-excluded from the option space. Do not
  pre-build what the empirics do not force; do not "fish" for a symptom. A
  permanently-invalid option is named as such once and not re-litigated.

---

## §7 Architecture doctrines

Standing doctrines carried into every design. They are defaults with reasons,
not dogma — but overriding one is itself a ratifiable decision with a rationale.

- **Deterministic projection over LLM directive.** Projectors eliminate
  hallucination structurally; the LLM handles only what the model cannot
  determine. Prefer a deterministic projector to an instruction wherever the
  model already carries the information.
- **Fail-loud-over-hallucinate.** Escalation is mandatory. A false-positive
  finding is acceptable; a gate lied green is not. Never build a mutator that
  makes a gate pass by hiding a real gap.
- **Single-LLM-call-per-reasoning-task.** Multi-aspect output from one call, not
  several calls for one reasoning task.
- **Model truth over code truth.** The model leads; code is adjusted to the
  model, never the model to the code. Model changes never flow through the
  implementation/worker pipeline — they have their own path.
- **Contract immutability.** Interface contracts between components are model
  aspects, not pipeline artifacts. A required contract amendment is a hard
  rollback signal, not an in-pipeline patch.
- **Build-it-right-now (*Bau-jetzt-richtig*).** A confirmed-correct design is
  built immediately within the relevant scope, not deferred into a backlog that
  re-opens the decision.
- **Granularity-inflation trap.** Create independent architectural nodes only
  for genuinely independent decisions, not for provisioning consequences.
  Coarse granularity is the default.

---

## §8 Findings vs. decisions

A strict separation, because conflating them corrupts the record.

- A **finding** is *reported*. It is acknowledged, corrected, or carried
  forward (`weiter`). Maturity results, audit results, and observations are
  findings. A false-positive finding is a valuable result, not a distraction.
  Findings live in `chat-context/findings/`.
- A **decision / convention / design / rule** is *ratified*. The word
  "ratify" is reserved for these. Ratified architecture decisions that earn a
  stable identifier become ADRs (§9).

Never let a finding masquerade as a ratified decision, and never silently
promote one to the other. Reporting and ratifying are different acts with
different durability.

---

## §9 ADR-first persistence

A ratified architecture decision that earns a stable identifier (an ADR number)
is persisted **document-first**. This is a hard rule.

1. **Write the ADR document first**, under `adr_path` (default
   `spec/docs/adr/`), as `ADR-<id>-<slug>.md`. It carries the full **Context**,
   **Decision**, **Consequences**, and **Rejected alternatives**. These live in
   the document, never in a memory mnemonic.
2. **Handle supersession bidirectionally.** A new ADR names what it
   supersedes or refines; the superseded ADR gets a forward note at its head;
   partial supersession names the specific clause so the still-valid parts are
   not read as obsolete.
3. **Then** record a pointer mnemonic in memory (§10) — stable ID, one-paragraph
   gist, supersession notes, and the document path. The mnemonic is an index,
   not the record.
4. **On divergence, the document wins.** Correct a stale mnemonic; never follow
   it against its ADR.

The always-present memory digest must never be mistaken for the record. The
git-tracked ADR is the durable artifact; memory is the index into it.
Infrastructure and provisioning choices are subordinate to ratified
architecture: they choose adapters/backends within the frame an ADR sets and may
not circumvent it. If infrastructure reality breaks an ADR's assumption, the path
is ADR revision via supersession — never silent circumvention. On a technical
aspect the ADR is the last authoritative instance before implementation; a
decision-ledger entry touching the same technical aspect is reconciled to the
ADR, never the reverse.

---

## §10 Memory discipline

The memory layer is durable, work-steering pointers — distilled, not the record.

- **Source-of-truth order.** (1) the `spec/` repository / specification — wins on
  conflict; (2) memory mnemonics — distilled pointers; (3) chat context. If a
  mnemonic contradicts the spec, flag it as stale and propose a correction;
  do not follow it.
- **Load at session start.** Load the typed digest for the instance's
  `memory_scope` once, before substantive work, and obey every `constraint`
  entry as a hard rule for the session. If the call fails, say so and continue
  from the repository — never silently skip the memory layer.
- **Propose-before-write.** State the exact call (scope, type, key, content) and
  wait for an explicit go before writing a mnemonic — the same
  ratify-before-execute discipline as everywhere else.
- **Content rules.** English, self-contained, one fact per mnemonic, ≤ ~1,500
  characters. Keys are lowercase with dot/hyphen separators, no underscores
  (e.g. `decision.adr-p010`, `convention.blueprint-workspace-structure`).
  Ratified decisions carry their stable ID in key and content.
- **Types.** `decision` · `constraint` · `convention` · `glossary` ·
  `open_question` · `status`. Unratified speculation goes to `open_question`,
  never `decision`.
- **Updates.** Entries are insert-only. To revise, propose a delete of the old
  keyed entry plus a fresh write, and say that is what you are doing.
- **Never store.** Secrets, tokens, credentials, third-party personal data, or
  unratified speculation as fact.

---

## §11 The task-file model (Backlog · Aktiv-Queue · Archive)

The living task state is split across three files with three roles and a directed
flow — **Backlog → Aktiv-Queue → Archive**. A task is in **exactly one** of the
three at any time (disjointness).

### §11.1 `chat-context/WORKLIST.md` — the Backlog (pull-only)
The prioritized task pool and intake point for everything new. Schema v2: a single
`## Backlog` table (`# · Cluster · Titel · Komp · Typ · Prio · Größe · Disp ·
Status · Ref`). **Not part of the boot digest** — read only at closure and pulled
on demand. New tasks land here; the active *execution order* does not live in the
backlog row order (it lives in the Aktiv-Queue, §11.2).

### §11.2 `chat-context/STARTER.md` — the Aktiv-Queue
The next sprints/tasks in execution order live in the STARTER's `## Aktiv-Queue`
section (a formalized table, top = next), pulled from the backlog at closure. The
STARTER is the **one boot-loaded task file**; its queue is the execution cursor. A
task promoted into the queue has been **removed from the backlog** — the two never
hold the same task.

### §11.3 `chat-context/ARCHIVE.md` — the Archive (pull-only)
Finished tasks (`## Archiv-Tasks`: one line + link — a retrieval index that
discriminates, not a summary) and the sprint chronicle (`## Archiv-Sprints`).
**Not part of the boot digest** — appended at closure, searched on demand.

### §11.4 The flow (closure-driven)
New → backlog. At closure: pull the next task(s) from the backlog into the
STARTER's Aktiv-Queue (removed from the backlog); move each finished task to
ARCHIVE.md (`## Archiv-Tasks`, one line + link). The trigger is **closure**, not a
size threshold. Because the backlog and archive are pull-only, neither bloats the
boot; because a task lives in exactly one file, there is no dual-source drift.

### §11.5 Editing
The backlog and the Aktiv-Queue tables are edited via the `worklist-manager` skill
(read → modify in memory → whole-file write → read-back), never hand-edited. Sprint
numbers are informal conversational estimates, never canonical reservations (the
REGISTRY is the sole ID-allocation authority). **All task files are written only by
Desktop (§2.1)** — Code reports task-relevant state via its handover return, never
by editing a file.

---

## §12 Git discipline

All git operations are **operator-gated**: Claude proposes the exact command
block, the operator executes it. Claude does not push, merge, or commit.

- **Ground truth before the block.** Run QS immediately before generating any
  git block. The block is built from verified state, never from prose or memory.
  The first line of the block is always a branch check (`git branch
  --show-current`).
- **`--no-pager` for status-producing git (hard rule).** Every git command in the
  block that emits output to be read back — `status`, `log`, `diff`, `show`,
  `branch`, `tag --list`, `stash list` — is written as `git --no-pager <subcommand> …`.
  A pager (`less`) intercepts the output in the operator's terminal: it can hide
  truncation, require interaction to dismiss, or swallow the result entirely, which
  defeats the predict-then-measure read-back the block exists for. Mutating commands
  (`add`/`commit`/`push`/`merge`/`mv`/`checkout`/`pull`/`fetch`) take no `--no-pager`.
  The QS/`gitstatus` tool is unaffected — it already returns plain text.
- **Increment branch, not main.** Day-to-day work commits to the increment
  branch and pushes it. `main` is reserved for milestone completion.
- **Single-stage closure** (no submodule touched): stage `chat-context/` + any
  touched `docs/`, verify staging, commit, push the increment branch.
- **Two-stage closure** (a submodule such as `spec/` was written — the usual
  case for ADR work): the **submodule feature branch completes fully first** —
  merge `--no-ff` to its main, push, tag if any, delete the branch
  (local + remote) — **before** the superrepo's pointer bump and chat-context
  commit. Each sub-branch is complete through branch-delete before the
  super-pointer moves.
- **Multi-stage schema sessions:** one commit at session end, not one per stage.

### §12.1 File moves and renames belong in the git block

Moving or renaming a tracked file is done with **`git mv`** inside the
operator-gated git block, **never** as a filesystem-connector copy-then-delete
during the session. This covers: consuming a handover
(`git mv handover/<f>.md handover/_consumed/<f>.md`), retiring or renaming a doc,
archiving a sprint file, and bulk renames such as a spec-corpus ledger cleanup.

*Reasons:*
- **History is preserved.** `git mv` records a rename; Git's history and `blame`
  follow the file. A connector copy-then-delete looks like a deleted file plus an
  unrelated new file — the lineage is lost.
- **No content risk.** The connector offers only whole-file writes, so a "move"
  through it is a re-typed copy that can silently truncate or drop content (a
  real failure mode observed in practice). `git mv` moves the bytes untouched.
- **One audited step.** The move lands in the same operator-reviewed block as the
  rest of the closure, with the same ground-truth-before discipline.

Mechanics: propose the `git mv` lines as part of the closure block (after the
branch check, before `git add`/commit). For a submodule-internal move, the
`git mv` runs inside the submodule and follows the two-stage ordering above. The
session itself never moves or renames through the connector — it only *writes*
new files and *edits* existing ones; moving and renaming is deferred here.

---

## §13 Language & notation

- **Language.** German for chat. File content splits by content class (§1.2):
  - **`chat-context/` → German** (the chat-steering layer follows the chat
    language): `WORKLIST.md`, `STARTER.md`, new `sprints/`, `findings/`,
    `handover/`. This is living state read only from inside the running work —
    same language as the conversation that drives it. (An instance whose chat
    language is not German applies its own chat language here instead.)
  - **`docs/`, `spec/` (ADRs, doctrines), commit messages, schema, code → English**
    (publishable blueprint, upstream-/machine-relevant, this file included).
- **Notation.** Variant labels are **alphanumeric only**: `A1`/`A2`, `B1`/`B2`,
  `Variant 1/2/3`, `Option A/B/C`. Never Greek letters (α/β/γ), roman numerals,
  or emojis. *Reasons:* greppability across commits and queries, keyboard input
  without special methods, uniform referenceability. Labels are discussion
  handles only — they are not persisted. A ratified decision earns its stable
  ID as an ADR (§9), and that ID is the permanent citation.

---

## §14 Handover to Code (§17 dispatch)

When ratified design work must become program code (§2), it is handed to the
Code apparatus as a **self-contained copy-paste dispatch** — not a file, not a
STARTER. The Code session has none of the Desktop session's context, so the
dispatch must stand entirely on its own. **Every dispatch is regulated**: it ends
with a handover report (§14.3). There are no unregulated Code dispatches.

### §14.1 Dispatch principles
- **Fully autonomous to closure** — every gate is written into the dispatch; no
  operator pauses mid-run.
- **Single variable** — the sub-sprint touches exactly one variable; name
  explicitly what it must not touch.
- **NULL-FIX within each measurement series; predict-then-measure; n ≥ 2**
  (typically n = 3 plus a warmup) before a wall is real (§6).
- **Localize before build** — dispatch hypotheses are guidance; localization may
  refute them.
- **Fail-loud-over-hallucinate** — if diagnosis shows a gate rejects *correctly*
  (a genuine gap), the run fails loud and returns; it does not build a
  workaround. Only a confirmed hygiene bug is fixed autonomously.

### §14.2 Dispatch contents
Apparatus & autonomy · guiding philosophy (the doctrines it must carry) ·
single-variable boundary · mandatory reads (with anchors) · QS & branch ·
build steps (per stage) · verification (n, what is measured, evidence
convention) · gate (explicit, checkable MET criteria) · closure (the mandatory
handover report, §14.3).

### §14.3 Return and reconciliation
Every Code sub-sprint closes by writing a **structured report** to
`chat-context/handover/handover-<YYYY-MM-DD>-<slug>.md` — the result (gate met or
failed-loud and why), what was built/measured, evidence pointers, what was
deferred, and any new finding or decision that needs Concept ratification. Code
then returns a **one-line pointer** to that report (plus the sprint-document
path). The pointer is the **signal**; the report is the **substance** — Code
never returns substance only in chat. No STARTER (the Desktop session holds it).

Back on Desktop:
1. **Read the handover report**, not just the chat pointer.
2. **Post-run control check** — do not take "gate met" at face value if a
   confounder is plausible (for example, if the measured path was never actually
   exercised). Report confounders honestly.
3. Fold the result into the next decision (`solve-problem`).
4. **At closure, curate** the report into the durable record (the sprint file, a
   finding, or a decision note) and **prune the consumed report** from
   `handover/` (moved to `handover/_consumed/` via a `git mv` in the git block,
   §12.1). The folder is a staging area, not the record (§3.3).

The Code apparatus cannot write mnemonics or ledgers; anything newly decided in a
sub-sprint returns in the handover report and is ratified by Concept (§8).

---

## §15 Glossary

- **platform-dev** — the central steering repository for a platform's
  development; the thing this blueprint produces.
- **blueprint** — the published, derivable template from which platform-dev
  instances are created.
- **apparatus** — one of the two work environments: Desktop (concept) or Code
  (implementation), §2.
- **front** — the current focus of work, carried in the STARTER's `## Aktiv-Queue`
  and `## Arbeitsauftrag` (there is no separate WORKLIST pointer).
- **wall** — an empirical obstacle observed in a running system; real at n ≥ 2,
  §6.
- **ADR** — Architecture Decision Record; a ratified decision with a stable ID,
  persisted document-first, §9.
- **finding** — a reported observation, §8; not a ratified decision.
- **mnemonic** — a memory entry; a pointer into the record, not the record, §10.
- **ratify** — to confirm a decision/convention/design/rule (reserved word, §8).
- **QS** — the quick-status tool (`qs_tool`) that reports authoritative git
  state; the only trusted source for workspace state.
- **handover report** — the mandatory file a Code sub-sprint writes to
  `chat-context/handover/` at closure; staged for Desktop to curate, §14.3.
- **§17 dispatch** — the self-contained handover from Desktop to Code, §14.
- **spec** — the product-specific specification submodule (`spec/`), home of
  ADRs and product doctrines.

---

*This document is stable reference. To change the method, change this file —
and, where a skill encodes a step, the corresponding skill in `skills/`.*
