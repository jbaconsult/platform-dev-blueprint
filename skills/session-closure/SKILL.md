---
name: session-closure
description: Close a platform-dev session in the correct, deterministic order — findings, sprint file, WORKLIST (with archiving), STARTER, then an operator-gated git block, with the next starter prompt as the final act. Use this skill at the END of a session whenever the user signals wrap-up — triggers include "Closure", "schließe ab", "Session-Ende", "lass uns abschließen", "Sprint schließen", "mach den Git-Block", "schreib den STARTER für morgen", or any request to persist results and prepare the next session. Use it even for a partial wrap ("halt hier fest und mach den Pointer").
---

# Session Closure

Persists a session's results and prepares the next. The authoritative order is
`docs/WORKING_CONCEPT.md` §3.3; the WORKLIST schema is §11; git discipline is
§12. This skill is the executable form.

Parametric over `PROJECT.md`: `status_tool`, `fs_connector`, `workspace_root`,
`adr_path`, `increment_branch`, `memory_scope`. Read the write discipline in
`docs/TOOLING.md` before editing — closure is where the connector's quirks bite
(no parent auto-create, read-back needed, large full-file writes risk failure →
sectional edits).

## Closure sequence (in order)

### 1. Findings → `chat-context/findings/`
Write reportive findings as their own files (one concern per file). Findings are
*reported*, not ratified (WORKING_CONCEPT §8). A deferred/open finding is
captured here, not dropped.

### 2. Sprint file → `chat-context/sprints/`
Write `sprint-NN-<slug>.md`: what was decided/ratified, the design or doctrine
text in full, wall balance / empirical results, deferred items with triggers.
This is the durable session narrative — the WORKLIST and mnemonics only point at
it.

### 3. WORKLIST.md — sectional edits + archiving (WORKING_CONCEPT §11)
Edit `chat-context/WORKLIST.md` sectionally (never a full rewrite). Three fixed
sections in order:
- **`## Pointer`** — set the next front (this is the only "where we stand"; the
  STARTER header is drawn from here).
- **`## Aktiv`** — mark the closed sprint done; add the next row; update the
  wall/active block.
- **`## Archiv`** — apply **archiving rule A1**: a completed sprint, once fully
  persisted in `sprints/`, moves from `## Aktiv` to `## Archiv`, reduced to a
  one-line pointer to its sprint file.

### 4. STARTER.md — rewritten, boot-only
Rewrite `chat-context/STARTER.md` as a minimal boot pointer (~1–2 KB): header +
mandatory reads + status check + next front + the first decision the next
session faces. Task briefing does NOT belong here — it lives in WORKLIST
`## Pointer` / the sprint file. A small file like STARTER is more reliably
written whole than chained edits.

### 5. Status check before the git block
Call the `<status_tool>` (default `gitstatus`) again. **Build the git block only
from this verified state** — never from STARTER prose or memory.

### 6. Git block — operator-gated (WORKING_CONCEPT §12)
Claude proposes, the operator executes. One copy-paste bash block. First line is
always a branch check.

**Single-stage** (no submodule touched):
```bash
cd <workspace_root>
git branch --show-current
git add chat-context/ docs/   # only what changed
git status -sb
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
`main` of the superrepo is reserved for milestone completion. Offer a post-push
`<status_tool>` call for a clean-state confirmation.

### 7. Starter prompt — the final act
The **last** thing emitted is the copy-paste starter prompt for the next
session, prefixed with the standing boot instruction:
```
Rufe zu Beginn memory_load_context(scope="<memory_scope>") auf und befolge jede
type=constraint-Regel. Notation ausschließlich alphanumerisch (A1/A2,
Variant 1/2/3, Option A/B/C), niemals griechische Buchstaben. Inhaltliches
gehört nach Git, nicht ins Memory.

# STARTER — Sprint NN+1 · <front>
...
```
Nothing comes after the starter prompt.

## Mnemonic writes during closure
If a decision earned a stable ADR ID this session, persist it document-first via
the `adr-author` skill (ADR before mnemonic). Propose the exact Kumbuka call and
wait for an explicit go (WORKING_CONCEPT §9, §10).
