---
name: session-closure
description: Close a platform-dev session in the correct, deterministic order — findings, sprint file, task-file consolidation (Backlog / Aktiv-Queue / Archive), REGISTRY reconciliation, handover flips, STARTER rewritten from the template, then an operator-gated git block, the post-push repo fingerprint, and the next starter prompt as the final act. Use this skill at the END of a session whenever the user signals wrap-up — triggers include "Closure", "schließe ab", "Session-Ende", "lass uns abschließen", "Sprint schließen", "mach den Git-Block", "schreib den STARTER für morgen", or any request to persist results and prepare the next session. Use it even for a partial wrap ("halt hier fest und schreib den Stand fest").
---

# Session Closure

Persists a session's results and prepares the next. The authoritative order is
`docs/WORKING_CONCEPT.md` §3.3; the task-file model is §11; git discipline is
§12. This skill is the executable form. **All closure edits are proposed and
written by Concept; all git is operator-gated** — Claude proposes the exact
block, the operator executes it.

Parametric over `PROJECT.md`: `status_tool`, `fs_connector`, `workspace_root`,
`adr_path`, `increment_branch`, `memory_scope`, `project_name`. Read the write
discipline in `docs/TOOLING.md` before editing — closure is where the
connector's quirks bite (parent creation, read-back needed, prefer anchored
`edit_file` on large files).

## Two cross-cutting rules

**STARTER ≠ status mnemonic ≠ ARCHIVE.md — no duplication.** The STARTER is the
forward briefing plus the Aktiv-Queue; a status mnemonic is a host/live
*pointer*; `ARCHIVE.md` is the historical index (one line + link). Restating one
inside another is the failure mode this skill exists to prevent. No
retrospective prose ("erreicht", "geschafft") in the STARTER — the retrospective
belongs in the sprint record and the archive.

**Never freeze live/git state into a durable doc as prose.** SHAs, ahead/behind
counts, committed-file lists go stale by the next boot. They belong only in the
post-push fingerprint mnemonic (step 7), never in the STARTER. The STARTER
carries the *expectation* the next boot's status read is checked against.

## Closure sequence (in order)

### 1. Findings → `chat-context/findings/`
Write reportive findings as their own files (one concern per file, frontmatter
per `chat-context/templates/TEMPLATE-finding.md`, F-ID from the REGISTRY).
Findings are *reported*, not ratified (WORKING_CONCEPT §8). A deferred/open
finding is captured here, not dropped.

### 2. Sprint file → `chat-context/sprints/`
Write `sprint-NN-<slug>.md` (frontmatter per `TEMPLATE-sprint.md`): what was
decided/ratified, the design or doctrine text in full, wall balance / empirical
results, deferred items with triggers. This is the durable session narrative —
the task files and mnemonics only point at it.

### 3. Task-file consolidation (WORKING_CONCEPT §11, via `worklist-manager`)
Consolidate the three task files — a task lives in exactly one of them:
- **Capture:** every task noted this session becomes a proper Backlog row
  (Schema v2, ID from the REGISTRY) — no rough notes left dangling.
- **Archive:** every finished Aktiv-Queue/Backlog task moves to `ARCHIVE.md`
  `## Archiv-Tasks` as one line + link (discriminating, ≤200 chars — the link
  carries the information). Add the sprint's one-liner to `## Archiv-Sprints`.
- **Pull:** promote the next task(s) from the Backlog into the STARTER's
  `## Aktiv-Queue` (removed from the Backlog — disjointness), in execution
  order.

### 4. REGISTRY reconciliation + handover flips
- **REGISTRY:** every ID allocated this session has its row and the
  Naechste-freie-IDs counters are past it; advance the Sprint row to NN+1.
  A stale registry is worse than none.
- **Handover lifecycle:** for every dispatch/return pair processed this session,
  flip the frontmatter of BOTH files: `status: consumed` + `curated-in: <record
  path>` once curated into the durable record (or `status: closed` if processed
  but not yet captured). The physical move to `handover/_consumed/` rides the
  git block as `git mv` (§12.1) — never a connector copy-then-delete.

### 5. STARTER.md — rewritten from the template
Rewrite `chat-context/STARTER.md` from
`chat-context/templates/TEMPLATE-starter.md`: the **(fix)** sections verbatim
(dropping or trimming one is a closure bug), the **(variable)** sections fresh —
`Erwartung & Anomalien` (expectation, not history; no SHAs), the `Aktiv-Queue`
table (from step 3), the `Arbeitsauftrag` (forward only), the `Code interface`
block only if the next session dispatches Code. Title
`"<project_name> Sprint #<NN+1> — <front>"`.

### 6. Status check, then the git block — operator-gated (§12)
Call `<status_tool>` immediately before generating the block; build the block
only from that verified state. One copy-paste bash block; first line is always a
branch check; status-producing git commands use `--no-pager` (§12); file
moves/renames are `git mv` lines in the block (§12.1).

**Single-stage** (no submodule touched):
```bash
cd <workspace_root>
git branch --show-current
git mv chat-context/handover/<consumed>.md chat-context/handover/_consumed/<consumed>.md   # if any
git add chat-context/ docs/   # only what changed
git --no-pager status -sb
git commit -m "Sprint NN closure: <summary>"
git push origin <increment_branch>
```

**Two-stage** (a submodule such as `spec/` was written — usual for ADR work):
the submodule feature branch completes **fully first** (merge `--no-ff` → push →
tag if any → branch delete local+remote) **before** the superrepo pointer bump:
```bash
# --- spec submodule: feature closure ---
cd <workspace_root>/spec
git branch --show-current        # expect: feature/<name>
git switch main && git pull --ff-only
git merge --no-ff feature/<name> -m "Merge Sprint NN: <adrs>"
git push origin main
git branch -d feature/<name>
git push origin --delete feature/<name> 2>/dev/null || true
# --- superrepo: chat-context + pointer bump ---
cd <workspace_root>
git add chat-context/ docs/ spec
git commit -m "Sprint NN closure: <summary>; spec pointer bump"
git push origin <increment_branch>
```
`main` of the superrepo is reserved for milestone completion. Implementation
submodules are never committed here — their PRs are merged on GitHub by the
operator before closure.

### 7. After the operator's push — repo fingerprint
Call `<status_tool>` again for the post-push read-back (clean-state
confirmation). From that output write `status.repo-fingerprint` via
forget+remember on the fixed key: per-submodule SHA + branch + clean-flag,
superrepo only branch + clean (**never its own HEAD** — the closure commit just
changed it). This is a mechanical transcription of verified tool output. If the
status tool is not available (reduced runtime), ask the operator to paste a
read-back; never write an unverified fingerprint.

### 8. Starter prompt — the final act
Print a short achievements list (chat-only — the one place a retrospective
belongs), then the copy-paste boot trigger for the next session, in a code
block:
```markdown
Titel des Chats: <project_name> Sprint #<NN+1> — <front>

Rufe zu Beginn memory_load_context(scope="<memory_scope>") auf und befolge jede
type=constraint-Regel. Inhaltliches gehört nach Git, nicht ins Memory.

Boote die Session (session-start) und lies chat-context/STARTER.md — Schema
chat-context/templates/TEMPLATE-starter.md: die (fix)-Sektionen gelten
unverändert; arbeite den Arbeitsauftrag ab.
```
Nothing comes after the starter prompt.

## Partial closure (pausing, not finishing)
If the session is interrupted mid-work, do **not** fake a full closure: rewrite
the STARTER's Arbeitsauftrag to say honestly *"mid-flight, not cleanly closed"*
with the concrete next action, capture anything half-done as a holding finding,
and offer a checkpoint git block only if wanted. The tell: an Arbeitsauftrag
that reads "continue X" rather than "start the next front" is a pause — skipping
the sprint file / archiving / fingerprint is then correct, not an omission.

## Mnemonic writes during closure
If a decision earned a stable ADR/D-* ID this session, persist it
document-first via the `adr-author` skill (document + INDEX before mnemonic).
Propose the exact memory call and wait for an explicit go (WORKING_CONCEPT §9,
§10). The fingerprint write in step 7 is the one exception to
propose-before-write — it is a transcription, not a judgment.
