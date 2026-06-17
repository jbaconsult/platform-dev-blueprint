---
name: code-handover
description: Build a self-contained dispatch prompt to hand an implementation sub-sprint from the concept apparatus (Desktop) to the implementation apparatus (Claude Code, autonomous executor). Use this skill whenever ratified design work needs to become program code — triggers include "dispatch", "Übergabe an Code", "gib das an Claude Code", "Sub-Sprint", "Build-Order", "bau das", or any point where work crosses the apparatus boundary into .java/.ts/.hcl/.tf/pom.xml/.py territory. Use it the moment a design is ratified and the next step is implementation, not just when the user says "dispatch".
---

# Code Handover

Desktop is the orchestrator and overview-holder; Claude Code runs autonomous
sub-sprints. The handover is a single **self-contained copy-paste prompt** — not
a file, not a STARTER. Code returns only a **pointer** (sprint-doc path +
one-line result). Authoritative description: `docs/WORKING_CONCEPT.md` §2
(apparatus boundary) and §14 (dispatch).

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
- Notation latin/alphanumeric (Stufe 0/1/2, Variant 1/2). No Greek letters.

## Dispatch template
Fill every section. The prompt must stand alone — Code has none of this chat's
context.

```markdown
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

## Closure
Sprint-doc `sprints/sprint-NN.X-<slug>.md` + pointer return. NO STARTER (Desktop
holds it). Write findings. Git operator-gated.
```

## After Code returns (WORKING_CONCEPT §14.3)
Code returns a sprint-doc pointer + one-line result. Back on Desktop:
1. **Post-run control check** — read the returned evidence; do not take "gate
   met" at face value if a confounder is plausible (e.g. the measured path was
   never actually exercised). Report confounders honestly.
2. Reconcile the wall table / promotions (e.g. candidate→real at n≥2).
3. Fold the result into the next decision (`solve-problem`) and the closure
   (`session-closure`).

## Git for the code apparatus
All git stays operator-gated (WORKING_CONCEPT §12): commit + push feature +
merge `--no-ff` to main + push + branch delete. Pre-commit: verify the branch
via the status tool (e.g. gitstatus) or `git branch --show-current`, not from
prose.
