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
- §11 The WORKLIST schema
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
│   ├── WORKLIST.md           ## Pointer / ## Aktiv / ## Archiv (see §11)
│   ├── STARTER.md            boot pointer (~1–2 KB)
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

---

## §3 Session lifecycle

Every session follows the same three-phase arc. Each phase has a skill that
encodes its deterministic steps.

### §3.1 Boot (`session-start`)

In fixed order: load memory (and obey its constraints) → load the deferred
filesystem write tools → confirm the workspace root → run QS for ground-truth
state → read the mandatory steering files → emit a one-line boot summary. Only
then does substantive work begin. State is never inferred from prose — only the
QS tool is ground truth.

### §3.2 Work (`solve-problem`)

The substantive middle of the session: one decision at a time, characterized
before constructed, recommendation-first, measured against the wall where
empirical (§4–§7).

### §3.3 Closure (`session-closure`)

In fixed order: write findings → write the sprint record → update WORKLIST
(including archiving, §11) → rewrite STARTER → run QS → emit the operator-gated
git block → emit the next session's starter prompt as the final act. Nothing
follows the starter prompt.

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
is ADR revision via supersession — never silent circumvention.

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

## §11 The WORKLIST schema

`chat-context/WORKLIST.md` is the living state of the work. It has three fixed
sections in fixed order:

### §11.1 `## Pointer`
Always first, always current. The single next front — what the next session
opens with. The STARTER's header is drawn from here. This is the one place the
"where do we stand" lives; there is no separate state file.

### §11.2 `## Aktiv`
The running sprint series and the wall / active work block: open sprints and the
sprint just closed. Kept lean — only what is genuinely in play.

### §11.3 `## Archiv`
Completed sprint series, retained as history but no longer actively referenced.
Each archived series is reduced to a one-line pointer to its `sprints/` record.

### §11.4 Archiving rule (A1)
A sprint block moves from `## Aktiv` to `## Archiv` **at session closure**, once
its wall and result are fully persisted in a `sprints/sprint-NN-<slug>.md`
record. The WORKLIST then keeps only the one-line pointer; the detailed content
lives in the sprint file. The trigger is closure, not a size threshold —
archiving is regel-clear and machine-unambiguous, and "see the last few sprints"
is served by `## Archiv` directly below. This keeps `## Aktiv` lean, bounds the
WORKLIST's growth, and keeps sectional edits small (which the filesystem write
discipline depends on — see `TOOLING_LL.md`).

### §11.5 Editing
WORKLIST is edited with **sectional** edits, never a wholesale rewrite (large
full-file writes risk a crash). Sprint numbers are informal conversational
estimates, never canonical reservations.

---

## §12 Git discipline

All git operations are **operator-gated**: Claude proposes the exact command
block, the operator executes it. Claude does not push, merge, or commit.

- **Ground truth before the block.** Run QS immediately before generating any
  git block. The block is built from verified state, never from prose or memory.
  The first line of the block is always a branch check (`git branch
  --show-current`).
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

---

## §13 Language & notation

- **Language.** German for chat; **English for all file content** — documents,
  ADRs, commit messages, schema, code, and this file.
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
   `handover/`. The folder is a staging area, not the record (§3.3).

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
- **front** — the current focus of work, recorded in WORKLIST `## Pointer`.
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
