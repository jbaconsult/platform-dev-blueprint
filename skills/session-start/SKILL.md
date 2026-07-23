---
name: session-start
description: Boot a platform-dev working session in the correct, deterministic order. Use this skill at the START of any session — triggers include "boot", "Session-Boot", "starte die Session", "Sprint N starten", "lade die Tools", pasting a STARTER prompt, or any first message that references the workspace, a branch, a sprint number, or the chat-context steering docs. Use it even when the user just says "weiter wo wir waren" at the top of a fresh chat. Loads memory, filesystem tools, workspace state, decision indices, and steering docs.
---

# Session Start (Boot Sequence)

Boot a platform-dev session deterministically: establish memory, filesystem
access, ground-truth state, and steering-doc context before substantive work.

Parametric over `PROJECT.md`: `memory_scope`, `fs_connector`, `workspace_root`,
`status_tool`, `adr_path`, `increment_branch`.

## The boot sequence lives in the STARTER

**`chat-context/STARTER.md` `## Boot (fix)` is the authoritative, ordered boot
sequence** — memory load, deferred FS tools, workspace confirm, the status tool,
then reading the STARTER's own `## Aktiv-Queue` + `## Arbeitsauftrag`. **The boot
loads exactly three things: the memory digest, the STARTER, and status-tool
ground-truth.** Everything else — the WORKLIST backlog, ARCHIVE, REGISTRY, the
INDEX files, WORKING_CONCEPT — is pulled when needed, never boot-mandatory
(WORKING_CONCEPT §3.1). Execute it top to bottom. This skill does not restate those
steps; it carries only the boot behaviour the template can't, below.

If STARTER.md is missing or its `## Boot (fix)` section is absent, that is a
broken state (first session, or a closure bug) — see *Edge cases* at the bottom;
do not improvise a boot from memory.

## Boot behaviour the template doesn't carry

### Memory digest is the session's steering context
`memory_load_context(scope: "<memory_scope>")` returns decision · constraint ·
convention · glossary · status (excludes open_question unless asked). **Hold the
digest for the whole session.** Every `type=constraint` is active — if one is
violated mid-session, interrupt and restate it. Non-negotiable.

### Status tool vs. STARTER expectation — the cheap-checkmark rule
After the status tool (step 4), check it against the STARTER's **Erwartung &
Anomalien**, NOT against any frozen state:
- **Match → proceed silently.** Do not spend tokens reconstructing or narrating
  the state. This is the common case and must stay cheap.
- **Deviation from the stated expectation → that delta is the only signal.**
  Investigate it and nothing else.

The STARTER carries no SHAs/ahead-behind by design — the live status tool is the
sole live git truth — but no longer the *only* truth checked. The previous
closure wrote a `status.repo-fingerprint` mnemonic (per-submodule SHA/branch/
clean) into the memory digest; the cheap-checkmark above verifies the live
status against *that* — a machine-checkable claim, not prose. Match →
near-zero cost; a submodule mismatch → go verbose there only.

**Branch on tool presence first.** If `<status_tool>` cannot be loaded at all (a
reduced runtime, e.g. mobile/web), there is no ground truth to verify — the
fingerprint is the sole, *unverified* anchor. Proceed concept-only; no git or
host mutation. An absent tool is not drift, and a mobile session never writes the
fingerprint.

### Sprint number is assigned, never guessed
The session's sprint number comes from the STARTER `title` / the operator, not
from whatever number happens to be visible in context. A spun-off **track**
session takes the identity its dispatch/plan prompt assigns it
(`sprint-N-<track-slug>`), never its own integer `N`. Monotonic IDs (sprint
numbers + finding F-IDs) are owned by the canonical steering line
(WORKING_CONCEPT §2.2).

### Every ID comes from the REGISTRY
`chat-context/REGISTRY.md` is the sole allocation authority for ALL numbered ID
families (FEAT/CHORE/BUG/ADR/D-*/F/Sprint). It is **pulled fresh at the moment of
allocation** — not boot-mandatory reading. Registry allocation is not
concurrency-safe, so a boot snapshot would go stale as satellite sessions draw
numbers in parallel; read it fresh when you allocate, never from a boot snapshot.
Never mint an ID from prose, memory, filename scans, or table scans; never reuse
a burned/gap number. Every new ID is registered there in the same breath it is
first used — the closure backstop is session-closure step 4.1, not a substitute
for this.

### Synthesize the brief
From the STARTER, hold: the next tasks in execution order (the STARTER's
`## Aktiv-Queue`, top rows — there is no separate Pointer; the queue lives in the
STARTER, not the WORKLIST, and the table itself is the queue), the first
decision/task and any blockers (STARTER `## Arbeitsauftrag`), open/deferred items
with triggers. Then follow the STARTER's Arbeitsauftrag — that is the authority
for what happens next.

After you have read and understood the current task from the STARTER.md for this
sprint, print out its name and a brief yet understandable explanation of the
task. Afterwards start reading the task-related documents.

## Resuming within a session
The sequence is idempotent. On resume after a break, re-run only the memory load
and the status tool to confirm nothing changed, then continue.

## Edge cases
- **A boot step fails (memory / FS tools / workspace / status tool):** report the
  specific failure, do **not** proceed, wait for operator guidance.
- **Git dirty UNEXPECTEDLY:** flag only drift the STARTER's Erwartung does NOT
  cover; report just that delta and ask — proceed (risky) or stash/commit first?
  Drift that matches a stated anomaly is expected → proceed silently.
- **Steering docs missing:** report which ones and ask if expected (first
  session, or repo restructured). For a genuine first-session bootstrap
  (no `chat-context/`, no INDEX/WORKLIST/STARTER), the operator directs Concept
  to create the skeleton structure — a one-time step, not part of normal boot.
