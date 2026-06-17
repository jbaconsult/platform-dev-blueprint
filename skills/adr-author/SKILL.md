---
name: adr-author
description: Persist a ratified architecture decision document-first — write the ADR doc under the spec submodule's adr/ directory BEFORE any memory mnemonic, with full Context/Decision/Consequences/Rejected-alternatives, bidirectional supersession notes, then a pointer-only mnemonic proposed for ratification. Use this skill whenever a decision has just been ratified and earns a stable ID — triggers include "schreib das als ADR", "ADR-NNN", "persistier die Entscheidung", "halt das als Decision fest", or any moment a ratified design needs durable recording. Use it before writing the mnemonic, never after.
---

# ADR Author (document-first persistence)

A ratified architecture decision that earns a stable ID is persisted
**document-first**: the git-tracked ADR document is the durable artifact; the
memory mnemonic is only an index pointer. Authoritative rule:
`docs/WORKING_CONCEPT.md` §9 (and §10 for the memory side). The always-present
memory digest must never be mistaken for the record.

Parametric over `PROJECT.md`: `adr_path` (default `spec/docs/adr/`),
`memory_scope`, `fs_connector`.

## Order of operations (do not invert)

### 1. Write the ADR document FIRST
Under `<adr_path>`, as `ADR-<id>-<slug>.md`. The document holds the **full**
content — these never live in the mnemonic:
- **Context** — the situation, the forces, what was unresolved.
- **Decision** — what was decided, precisely.
- **Consequences** — what follows, what is now constrained, what is unblocked.
- **Rejected alternatives** — the variants considered and why they lost
  (referenced by their discussion labels A1/A2/… as needed; the ADR ID is the
  permanent citation).

### 2. Handle supersession bidirectionally
If this ADR supersedes or refines an earlier one:
- the **new** ADR names what it supersedes/refines;
- the **old** ADR gets a forward note at its head;
- **partial** supersession names the *specific clause* superseded, so the
  still-valid parts are not read as obsolete.

### 3. Then propose the pointer mnemonic (propose-before-write)
Only after the document exists, propose the Kumbuka call and **wait for an
explicit go**. The mnemonic is a pointer, not content:
- **scope:** `<memory_scope>`
- **type:** `decision`
- **key:** `decision.adr-<id>` (lowercase, dot/hyphen, no underscores)
- **content:** stable ID + acceptance date + one-paragraph gist + supersession
  notes + the document path. ≤ ~1,500 chars, English, self-contained, one fact.

Example content shape:
> ADR-<id> (accepted YYYY-MM-DD): <one-paragraph gist>. Refines/supersedes
> <ADR-…> (<clause>). Doc: <adr_path>/ADR-<id>-<slug>.md

### 4. On divergence, the ADR wins
If a mnemonic ever contradicts its ADR document, the document is authoritative —
correct the mnemonic via `memory_forget` (by scope+key) + a fresh
`memory_remember`, and say that is what you are doing (entries are insert-only).

## Namespace discipline
ADR IDs are assigned deliberately, not guessed. Confirm the next free number
against QS / the `<adr_path>` directory before assigning. If the instance
reserves ID ranges for specific blocks (e.g. a security series), respect the
reservation — record it as a `convention` mnemonic so it survives across
sessions.

## Architecture precedes infrastructure (WORKING_CONCEPT §9)
A ratified ADR is invariant w.r.t. infrastructure/provisioning decisions.
Architecture sets the frame (contract/interface form); infra chooses the
adapter/backend within it and may not circumvent it. If infra reality breaks an
assumption, the path is ADR revision via supersession — never silent
circumvention.

## Findings are not ADRs
Only ratified decisions/conventions/designs/rules become ADRs. A maturity or
audit finding is *reported* (`solve-problem`, WORKING_CONCEPT §8), never turned
into an ADR.
