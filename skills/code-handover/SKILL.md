---
name: code-handover
description: Build a self-contained dispatch prompt to hand an implementation sub-sprint from the concept apparatus (Desktop) to the implementation apparatus (Claude Code, autonomous executor). Use this skill whenever ratified design work needs to become program code — triggers include "dispatch", "Übergabe an Code", "gib das an Claude Code", "Sub-Sprint", "Build-Order", "bau das", or any point where work crosses the apparatus boundary into .java/.ts/.hcl/.tf/pom.xml/.py territory. Use it the moment a design is ratified and the next step is implementation, not just when the user says "dispatch".
---

# Code Handover

Desktop is the orchestrator and overview-holder; Claude Code runs autonomous
sub-sprints. The handover is a single **self-contained copy-paste prompt** — not
a file, not a STARTER. Every dispatch ends with Code writing a **report to
`chat-context/handover/`** and returning a **one-line pointer** to it — the
pointer is the signal, the handover file is the substance. There are no
unregulated Code dispatches. Authoritative description: `docs/WORKING_CONCEPT.md`
§2 (apparatus boundary) and §14 (dispatch).

## Apparatus boundary — when to dispatch (WORKING_CONCEPT §2)
Dispatch when the work touches program code:
- **Desktop keeps:** architecture decisions, sprint planning, spec/schema work,
  markdown documentation, helper-script design.
- **Code gets:** all program code — `.java`, `.ts`, `.py`, `.hcl`, `.tf`,
  `pom.xml`, `package.json`, code-bearing submodule edits, pipeline runs,
  measurements.

The boundary is by artifact type, not difficulty. If it is implementation, it is
a Code sub-sprint, dispatched from here.

## Dispatch principles (WORKING_CONCEPT §14.1)
- **Fully autonomous to closure** — every gate is written into the dispatch; no
  operator pauses mid-run.
- **Single variable** — touches exactly one variable; name what it must NOT
  touch.
- **NULL-FIX per measurement series; predict-then-measure; n≥2** (typically n=3
  + warmup) before a wall is real (§6).
- **Localize before build** — dispatch hypotheses are guidance; localization may
  refute them.
- **Fail-loud-over-hallucinate** — if a gate rejects *correctly* (genuine gap),
  fail loud and return; do not build a workaround. Only a confirmed hygiene bug
  is fixed autonomously.
- **Closure is a handover report** — the sub-sprint is not done until its report
  is written to `chat-context/handover/` (see Closure below).
- **A PR is not delivered while it is red** — after opening a PR, Code polls its
  checks on GitHub until ALL pass, including any configured code-quality gate
  (e.g. SonarQube), where the instance runs one. In-scope fixes are pushed until
  green; a correctly-rejecting gate is a fail-loud return, never a workaround.
- Notation latin/alphanumeric (Stufe 0/1/2, Variant 1/2). No Greek letters.
- **Reserved sprint identity** — a dispatch/plan that spins off a parallel track
  carries the sprint identity the canonical line assigns it
  (`sprint-N-<track-slug>`); the track never claims its own integer `N`. This
  prevents two sessions double-claiming the same sprint number.

## Dispatch template
Fill every section. The prompt must stand alone — Code has none of this chat's
context. Every dispatch file STARTS with the frontmatter block from
`chat-context/templates/TEMPLATE-handover.md` (the schema authority; folder rules
live in `chat-context/handover/README.md`) — `type: dispatch`, `status: open`,
`counterpart` = the expected return filename.

```markdown
---
id: SPRINT_NN.X
type: dispatch
apparatus: code            # code | design
date: YYYY-MM-DD
sprint: NN
task: [FEAT-NN]
counterpart: handover-<YYYY-MM-DD>-<slug>.md   # the expected return file
status: open               # open until the return is curated; never edited mid-run
curated-in:                # Desktop fills this at curation -> status: consumed
---

# DISPATCH — SPRINT_NN.X · <title>

## Apparatus & autonomy
Claude Code, fully autonomous to closure. No operator pauses — all gates are
written here. <N> stages, sequential, each its own NULL-FIX series. Notation
latin/alphanumeric. No Greek letters.

## Guiding philosophy (carry)
- Characterize, don't construct. Option-space discipline: build nothing the
  empirics don't force.
- Localize BEFORE building: pin the root, then fix minimally, non-duplicatively.
- Predict-then-measure; one change per series; NULL-FIX within each series.
- Guarantee in the gate, not the fix.
- Fail-loud-over-hallucinate: no mutator that lies a gate green.

## Single-variable boundary
Touches ONLY <X> (e.g. scripts/ + tests/), NEVER <Y> (e.g. pipeline/mandate
code). <file from commit ZZZ> stays untouched.

## Mandatory reads
- <finding paths with section anchors>
- <WORKING_CONCEPT anchors: §6 empirical discipline, §14 dispatch>
- <code anchors: locate, don't guess — run-driver, smoke suite, projector stack>

## Status & branch
1. Get ground truth via the status tool (e.g. gitstatus) or plain git in the
   work tree.
2. Anchor = <main SHA, clean>. Branch off this anchor.
3. Idempotent: git switch -c feature/<name> 2>/dev/null || git switch feature/<name>

## Build (per stage)
Stage 0: …
Stage 1: …

## Verification
<n=3 + warmup; what is measured; evidence-capture convention>

## Gate (→ next stage / closure)
<explicit, checkable MET criteria; on a correctly-rejecting gate → fail-loud return>

## PR & checks (when the dispatch delivers PRs)
1. Open the PR from the feature branch (operator merges via GitHub UI — you
   never merge).
2. Watch the PR until GREEN: `gh pr checks <n> --watch` (fallback:
   `gh pr view <n> --json statusCheckRollup` in a poll loop). Green = ALL
   checks pass, including any configured code-quality gate (e.g. SonarQube) —
   CI green alone is not delivery where a quality gate runs.
3. Red checks: localize, fix IN-SCOPE (hygiene, new-code issues the quality
   gate flags on your own diff), push, re-watch. Repeat until green.
4. Red for out-of-scope reasons (correctly-rejecting gate, needed scope
   expansion, persistent infra flake) → fail-loud return with the check
   transcript in the report. Never force, never game the gate.
The closure gate is NOT met while any delivered PR is red.

## Closure (MANDATORY — every dispatch)
1. Write a structured report to
   `chat-context/handover/handover-<YYYY-MM-DD>-<slug>.md`:
   - the report STARTS with the frontmatter block per
     `chat-context/templates/TEMPLATE-handover.md` — `type: return`,
     `apparatus`/`sprint`/`task` mirrored from this dispatch, `counterpart` =
     THIS dispatch's filename, `status: open` (Desktop flips it to `consumed`
     at curation);
   - result (gate met / failed-loud + why), what was built/measured, evidence
     pointers, PR number(s) with FINAL check state (green, incl. the quality
     gate — or failed-loud with transcript), what was deferred, and any NEW
     finding or decision that needs Concept ratification.
2. Return a ONE-LINE pointer to the handover file ("done, report:
   chat-context/handover/handover-…md"). The pointer is the signal; the report
   is the substance — never return substance only in chat.
3. NO STARTER (Desktop holds it). Git operator-gated.

The sprint-doc is NOT written by Code. It is Desktop/Concept curation at
session-closure, filed under `chat-context/sprints/`. Code's only durable output
is the handover report.
```

## Handing the dispatch to the operator
Dispatches are written as files under `chat-context/handover/`; the operator
copy-pastes them to Claude Code. After writing the dispatch file(s), Desktop
**always lists the full absolute path(s) in a single copy-box** — one path per
line, no prose inside the box — so the operator can paste them straight to Code
without searching the tree. One box even for a single dispatch; one box holding
every path when a dispatch ships as a set (e.g. backend + frontend).

## After Code returns (WORKING_CONCEPT §14.3)
Code returns a one-line pointer to its `chat-context/handover/` report. Back on
Desktop:
1. **Read the handover report**, not just the chat pointer.
2. **Post-run control check** — do not take "gate met" at face value if a
   confounder is plausible (e.g. the measured path was never actually
   exercised). Report confounders honestly.
3. Reconcile the wall table / promotions (e.g. candidate→real at n≥2).
4. Fold the result into the next decision (`solve-problem`).
5. **The frontmatter lifecycle of the exchange files is NOT flipped here.** It is done as one
   explicit step at session-closure (`session-closure` step 4.2), where this session's judgment
   "verified / curated" is applied to every dispatch/return pair at once and this skill is no longer
   the one in context. Flipping it here — at the moment the return lands, hours after this skill was
   read at dispatch time — is exactly why it was chronically skipped. Leave the files `open` until
   closure; closure owns the flip.
6. **At closure (`session-closure` steps 2–4.2), curate then flip.** The handover report is folded
   into the durable record — the sprint file under `chat-context/sprints/`, a finding, or a decision
   note. Then the frontmatter of BOTH files of the exchange (dispatch + return) is flipped:
   `status: consumed` + `curated-in: <record path>` (or `status: closed` if the return was processed
   but not yet captured in a record). **The session flips the frontmatter in place; the physical move
   to `handover/_consumed/` happens as a `git mv` in the closure git block (§12.1)** or in a separate
   cleanup pass that follows `curated-in`. The folder is a staging area, not the record. See
   `session-closure` step 4.2 and WORKING_CONCEPT §3.3 — that step is authoritative for the exact
   tool calls and the read-back.

## Git for the code apparatus
Impl submodules: Code works branch → commit → push → PR autonomously
(convention: code-creates-impl-prs) and watches every PR to green (see PR &
checks above). Everything beyond that stays operator-gated (WORKING_CONCEPT
§12): merge `--no-ff`/UI-merge to main, superrepo commits and pointer bumps,
tags, branch deletion. Pre-commit: verify the branch via the status tool (e.g.
gitstatus) or `git branch --show-current`, not from prose.
