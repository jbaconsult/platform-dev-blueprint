---
name: adr-author
description: Persist a ratified architecture decision or product decision document-first — write the ADR or Decision doc under spec/docs/, update the INDEX, BEFORE any memory mnemonic, with full Context/Decision/Consequences/Rejected-alternatives, bidirectional supersession notes, then propose a pointer-only mnemonic for ratification. Use this skill whenever a decision has just been ratified and earns a stable ID — triggers include "schreib das als ADR", "D-<FAM>-<N>", "persistier die Entscheidung", "halt das als Decision fest", "document-first", or any moment a ratified design needs durable recording. Use it before writing the mnemonic, never after.
---

# ADR & Decision Author (document-first persistence)

A ratified architecture or product decision that earns a stable ID is persisted
**document-first**: the git-tracked document is the durable artifact; the
memory mnemonic is only an index pointer. Authoritative rule:
`docs/WORKING_CONCEPT.md` §9 (and §10 for the memory side). The always-present
memory digest must never be mistaken for the record.

Parametric over `PROJECT.md`: `adr_path` (default `spec/docs/adr/`),
`memory_scope`, `fs_connector`.

## Determine: ADR or Decision?

### ADR (Architecture Decision Record)

- **When:** Technical/build-driven architectural choice — contracts, interfaces,
  system structure, infrastructure decisions, technology selections
- **Where:** `spec/docs/adr/ADR-<id>-<slug>.md`
- **Family:** None — global sequence (ADR-0001, ADR-0002, ...)
- **Index:** `spec/docs/INDEX-adr.md`

**Examples:** ADR-0007 "Async messaging via transactional outbox" (architecture),
ADR-0003 "Postgres as the primary datastore" (tech structure)

### Decision (D-*)

- **When:** Product feature, business rule, operational policy, governance,
  licensing, market positioning, go-to-market strategy
- **Where:** `spec/docs/decisions/decision-<family>-<nr>-<slug>.md`
- **Family:** Thematic area slug — instance-defined, e.g. `lic | core | ops | gtm | ...`
  Numbers are per-family: `D-LIC-1`, `D-LIC-2`, ..., `D-CORE-1`, ..., `D-OPS-1`, ...
- **Index:** `spec/docs/INDEX-decisions.md`

**Examples:** D-OPS-1 "Provisioning via an internal backend seed endpoint"
(operational), D-LIC-1 "Open-core licensing boundary" (licensing model),
D-GTM-1 "Primary sales narrative" (positioning)

## Order of operations (do not invert)

### 1. Determine the next ID

**Allocation authority for EVERY ID family is `chat-context/REGISTRY.md` (the Naechste-freie-IDs
table) — never an INDEX scan, filename scan, prose, or memory.** The INDEX files remain the
content record (title/status/keywords, updated in step 4); the REGISTRY owns the number.

#### For ADR:

1. Read `chat-context/REGISTRY.md` → **Naechste freie IDs** → the ADR row is the new ID.
2. Add the new row to the REGISTRY's ADR table (ID · topic) and bump the Naechste-freie-IDs
   entry **in the same breath** — before or together with writing the document, never after
   the session moves on.
3. Burned/gap numbers stay burned — never fill a gap.

#### For Decision:

1. Determine the family (instance-defined; typical starter set):
   - Ask: "Is this a **licensing/business model** decision?" → `lic`
   - "Is this a **core product** decision?" → `core`
   - "Is this an **operations/provider** decision?" → `ops`
   - "Is this a **go-to-market/positioning** decision?" → `gtm`
   - Other thematic areas OK; document the family as a `convention` mnemonic

2. Read `chat-context/REGISTRY.md` → **Naechste freie IDs** → the family's row is the new ID.
   A family not yet in the REGISTRY starts at `<family>-1`; add its row.
3. Register the allocation in the REGISTRY (family table + Naechste-freie-IDs bump) **in the
   same breath**. The INDEX-decisions ledger row still lands in step 4 (content duty).

### 2. Write the document FIRST

Under the appropriate directory, as:

- **ADR:** `spec/docs/adr/ADR-<id>-<slug>.md`
- **Decision:** `spec/docs/decisions/decision-<family>-<nr>-<slug>.md`

The document holds the **full** content — these never live in the mnemonic:

- **Context** — the situation, the forces, what was unresolved, why this matters
- **Decision** — what was decided, precisely; no ambiguity in the wording
- **Consequences** — what follows, what is now constrained, what is unblocked,
  what risks are introduced, what becomes possible
- **Rejected alternatives** — the variants considered and why they lost
  (referenced by their discussion labels A1/A2/Variant 1/2, etc.; the stable ID
  is the permanent citation)
- **Supersession notes** (if applicable) — what this replaces, partial or full,
  and any forward/backward references

### 3. Handle supersession bidirectionally

If this ADR/Decision supersedes or refines an earlier one:

- the **new** document names what it supersedes/refines in the header
  (e.g., "Revises ADR-0015 §3.2" or "Supersedes D-CORE-14 entirely")
- the **old** document gets a forward note at its head
  (e.g., "Superseded by ADR-0019 as of 2026-06-20")
- **partial** supersession names the *specific clause* superseded, so the
  still-valid parts are not read as obsolete

### 4. Update the INDEX

After writing the document, update the corresponding index file.

#### For ADR: `spec/docs/INDEX-adr.md`

Add a row to the table in chronological order (newest at bottom):

```markdown
| ADR-0019 | Async messaging via transactional outbox | accepted | 2026-06-20 |
```

#### For Decision: `spec/docs/INDEX-decisions.md`

Find the family section. If it does not exist, create it:

```markdown
## Family: OPS (Operations & Provider)
```

Within the family, add a row in numerical order (by D-*-NR):

```markdown
| D-OPS-1 | Provisioning via an internal backend seed endpoint | accepted | 2026-06-20 |
```

Re-save the index file (via `fs_connector`).

### 5. Then propose the pointer mnemonic (propose-before-write)

Only after the document exists **and** the INDEX is updated, propose the memory call
and **wait for an explicit go**. The mnemonic is a pointer, not content:

- **scope:** `<memory_scope>`
- **type:** `decision`
- **key:** `decision.adr-<id>` (for ADRs) or `decision.d-<family>-<nr>` (for Decisions)
  - Lowercase, dot/hyphen only, no underscores
  - Examples: `decision.adr-0019`, `decision.d-ops-1`
- **content:** stable ID + acceptance date + one-paragraph gist + supersession
  notes + the document path. ≤ ~1,500 chars, English, self-contained, one fact.

#### ADR mnemonic example:

> ADR-0019 (accepted 2026-06-20): Async messaging via transactional outbox.
> Refines ADR-0007: delivery guarantees + retry contract. No new runtime deps.
> Doc: spec/docs/adr/ADR-0019-outbox.md

#### Decision mnemonic example:

> D-OPS-1 (accepted 2026-06-20): Provisioning via an internal backend seed
> endpoint instead of a console-side service. Fixes the provisioning boundary
> defect; respects the D-LIC-1 seam (the open component owns provisioning).
> Foundation for later self-service signup. Amends ADR-0015 (provisioning
> architecture). Doc: spec/docs/decisions/decision-ops-1-provisioning.md

### 6. On divergence, the document wins

If a mnemonic ever contradicts its ADR/Decision document, the document is authoritative.
Correct the mnemonic via `memory_forget` (by scope+key) + a fresh `memory_remember`,
and state that is what you are doing (entries are insert-only, no in-place edit).

## Namespace discipline

IDs are assigned deliberately, not guessed — and exclusively via `chat-context/REGISTRY.md`.

### For ADR:

Read the REGISTRY's Naechste-freie-IDs table. ADR IDs are a shared global sequence across
all architecture decisions, never reused, gaps stay burned.

### For Decision:

Read the REGISTRY, determine the family, take the family's next free number. Families are
open-ended; a new family starts at `*-1` — add its REGISTRY row when opening it.

Record any new decision family as a `convention` mnemonic (e.g., "D-SEC-* reserved
for security decisions") so it survives across sessions and is discoverable at boot.

## Architecture precedes infrastructure (WORKING_CONCEPT §9)

A ratified ADR is invariant w.r.t. infrastructure/provisioning decisions.
Architecture sets the frame (contract/interface form); infra chooses the
adapter/backend within it and may not circumvent it. If infra reality breaks an
assumption, the path is ADR revision via supersession — never silent
circumvention.

## Findings are not ADRs or Decisions

Only ratified decisions/conventions/designs/rules become ADRs or Decisions.
A maturity or audit finding is *reported* (`solve-problem`, WORKING_CONCEPT §8),
never turned into an ADR or Decision. Findings live in `chat-context/findings/`
and are acknowledged/corrected/deferred in the session, not elevated to a
ratified status.

A false-positive finding is a valuable result — it clarifies the actual state.
