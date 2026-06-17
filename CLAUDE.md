# CLAUDE.md — platform-dev (Code apparatus rules)

> Standing rules for the **Code apparatus** (Claude Code) in this workspace.
> Loaded automatically at the top of every Code session in this repo. These are
> the rules that must hold regardless of what any individual dispatch prompt
> says — the dispatch carries the task; this file carries the discipline.
>
> This is a **blueprint template**: replace the `example-project` placeholders
> when you derive an instance. Keep it lean (< ~150 lines) — long rule files get
> silently dropped. The full method is in `docs/WORKING_CONCEPT.md`; this file is
> the Code-side digest, not a second copy of it.

## Instance
- **Project:** `example-project`
- **Workspace root:** `/path/to/work/example-project`
- **Memory scope (Kumbuka):** `example-project`
- **Status tool:** `gitstatus` (via the `script-runner` MCP server) — git
  ground-truth; trust it, not prose, for branch/commit/submodule state.

## Apparatus boundary (WORKING_CONCEPT §2)
This is the **implementation apparatus**. It owns program code: `.java`, `.ts`,
`.py`, `.hcl`, `.tf`, `pom.xml`, `package.json`, test code, IaC, pipeline runs,
measurements. It does **not** make architecture decisions, write ADRs, or edit
the steering docs — those are the concept apparatus (Desktop). If a task would
cross that line, stop and return it to Desktop rather than deciding unilaterally.

## Every sub-sprint ends with a handover report (WORKING_CONCEPT §14.3)
**There are no unregulated dispatches.** A sub-sprint is not done until its
report is written:

- Write a structured report to
  `chat-context/handover/handover-<YYYY-MM-DD>-<slug>.md` containing: the result
  (gate met / failed-loud and why), what was built/measured, evidence pointers,
  what was deferred, and any new finding or decision that needs Concept
  ratification.
- Return a **one-line pointer** to that report (plus the sprint-doc path) as the
  signal back to Desktop. The pointer is the signal; the report is the
  substance — never return substance only in chat.
- Desktop curates the report into the durable record at its next closure and
  prunes it. `handover/` is a staging area, not the record.

## Empirical discipline (WORKING_CONCEPT §6)
- Predict-then-measure; one variable per measurement series (NULL-FIX); n ≥ 2
  (typically n = 3 + warmup) before a wall is treated as real.
- Localize before you build — pin the root, then fix minimally and
  non-duplicatively.
- **Fail-loud-over-hallucinate:** if a gate rejects *correctly* (a genuine gap),
  fail loud and return — never build a workaround that lies a gate green. Only a
  confirmed hygiene bug is fixed autonomously.

## Git (WORKING_CONCEPT §12) — operator-gated
- **Code never merges or pushes to main.** Finished feature branches / PRs are
  handed back to the operator (sole git operator). Code may commit + push a
  feature branch where the instance allows it; the merge to main is the
  operator's.
- Before any git step, get ground truth from the status tool (`gitstatus`) or
  `git branch --show-current` — never from prose.

## Notation & language (WORKING_CONCEPT §13)
- Variant labels are **alphanumeric only** (A1/A2, Variant 1/2/3, Option A/B/C).
  Never Greek letters, roman numerals, or emojis.
- File content in **English** (code, commits, docs); chat may be German.

## Memory (WORKING_CONCEPT §10)
The Code apparatus **cannot** write mnemonics or ledgers. Anything newly decided
in a sub-sprint goes into the handover report and is ratified by Concept. Do not
attempt to persist decisions to memory from a Code session.

---
*Source of truth for the method: `docs/WORKING_CONCEPT.md`. This file is the
Code-side digest; if the two ever diverge, WORKING_CONCEPT wins and this file
should be corrected.*
