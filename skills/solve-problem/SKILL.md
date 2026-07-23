---
name: solve-problem
description: The working method for a decision or architecture problem during a platform-dev session — characterize-before-construct, one decision per turn, recommendation-first, empirie-first. Use this skill DURING substantive work whenever a decision, design choice, trade-off, or architecture question is on the table. Triggers include "entscheide", "wie lösen wir", "Varianten", "welche Option", "ADR", "wand", "finding", "n=2", "predict-then-measure", or any turn where you weigh alternatives, propose a design, or characterize a problem. Use it even when the user just says "mach weiter" on an open decision — that is a ratification signal inside this discipline.
---

# Solve a Problem

The method for working decisions and designs during a session — the substantive
middle between boot (`session-start`) and closure (`session-closure`). The full,
authoritative description is `docs/WORKING_CONCEPT.md` §4–§8. This skill is the
operating summary; when in doubt, the document governs.

## The governing principle
**Characterize before you construct** (WORKING_CONCEPT §5.1). Pin the root, the
wall, the actual constraint *before* proposing a construction. The problem space
is mapped first; the solution is its consequence.

## Turn discipline (WORKING_CONCEPT §4)
Claude proposes → operator confirms (`mach` / `weiter` / `ja` / `passt`) →
Claude executes → operator validates. Four rules in every turn:

1. **One decision per turn** — exactly one ratifiable decision; no question
   catalogue at turn-end. Follow-ups get their own turns.
2. **Spell out abbreviations on first use** — full term + acronym in parentheses.
3. **State location and purpose before the decision** — where it sits, what it
   closes/unblocks. Context is the precondition for ratification.
4. **Always recommend with rationale** — end on one concrete recommendation, not
   a bare enumeration. Ratification should be confirm-or-correct, not
   evaluate-from-scratch.

`mach` / `weiter` ratify the current recommendation; then execute autonomously
to the next genuine decision point. **Velocity-Mode:** when sub-decisions are
fully rationalized and alternatives clearly non-competitive, proceed without
individual ratification; ask only when there is a genuine specification
alternative not derivable from the docs. Never present options for their own
sake.

## Notation (WORKING_CONCEPT §13)
Variant labels are alphanumeric only — `A1`/`A2`, `Variant 1/2/3`,
`Option A/B/C`. Never Greek letters, roman numerals, emojis. Labels are
discussion handles; a ratified decision earns its stable ID as an ADR.

## The five-criteria decision matrix (WORKING_CONCEPT §5.2)
For any non-trivial model/architecture decision, build a variant matrix with
these five columns, evaluated lexicographically (criterion 1 first):

1. **Minimize misunderstandings** — fewest ambiguities for human + machine.
2. **Internal consistency** — fewest mismatches across schema/models/docs.
3. **Sustainability / reversibility** — additive over structural break;
   reversibility breaks ties on 1–3.
4. **Machine readability** — graph-queryable, validatable, generator-friendly.
5. **Human readability** — clearest to read and edit.

Recommendation goes to the lexicographic winner. State the matrix; don't hide
the reasoning behind a verdict.

## Empirical discipline (WORKING_CONCEPT §6)
When testing against a running system: **empirie-first** (wall is real at n≥2) ·
**predict-then-measure** · **NULL-FIX** (one variable per series, no mid-series
hotfixes) · **localize before build** · **option-space discipline** (paths
without intact empirical validation are pre-excluded; don't fish for symptoms).

## Standing doctrines (WORKING_CONCEPT §7)
Carry these into every design (defaults with reasons; overriding one is itself a
ratifiable decision): deterministic projection over LLM directive ·
fail-loud-over-hallucinate · single-LLM-call-per-reasoning-task · model truth
over code truth · contract immutability · build-it-right-now · granularity-
inflation trap (coarse by default).

## Findings vs. decisions (WORKING_CONCEPT §8)
A **finding** is *reported* (acknowledged / corrected / `weiter`) and lives in
`chat-context/findings/`. A **decision/convention/design/rule** is *ratified* —
that word is reserved for these. Never let a finding masquerade as a decision. A
false-positive finding is a valuable result.

## Cluster-end reflection (WORKING_CONCEPT §5.4)
When work is a cluster of sub-decisions, end each cluster with: what was
achieved · ambiguities/deferred items · which need follow-up vs. defer ·
roadmap state. After the last cluster, a final cross-cluster consistency check.
Mandatory, not optional.

## No silent regeneration
Plans, concepts, backlog items, generated code are never silently regenerated —
the operator sees every diff/change/proposal before it is applied.

## When the decision earns an ADR
A ratified decision with a stable ID is persisted document-first — see the
`adr-author` skill (and WORKING_CONCEPT §9). Write the ADR before the mnemonic.

## Communication
Detailed prose, not terse bullet dumps. Chat is German, and so is `chat-context/` —
the steering layer follows the chat language. Everything **outside** `chat-context/` is
English: `docs/`, the `spec/` submodule (ADRs, doctrines), code, and commit messages
(WORKING_CONCEPT §13).
