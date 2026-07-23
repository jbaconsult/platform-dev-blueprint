---
name: worklist-manager
description: Manage WORKLIST items inline during sessions. Add tasks to the Backlog (the prioritized pool and intake for everything new) with full Schema-v2 metadata, reposition or re-sort rows, update any marker, archive a finished task (→ Archiv-Tasks, one line + link), or promote a Backlog task into a planned sprint in ## Aktiv. Use whenever you need to capture a task mid-session ("add to worklist"/"add to backlog"), consolidate at closure, reorder, update status/markers, or close out a finished item. Triggers include "worklist", "add task", "backlog", "promote task", "reposition", "resort", "task done", "archive task", "update status", or any request to modify WORKLIST.md.
---

# Worklist Manager

The WORKLIST lives in `chat-context/WORKLIST.md`. Since the Schema-v2 reform it is a pure
steering index with cluster-tagged rows — no task prose lives in it. Structure, top to bottom:

- **`## Aktiv`** — the **sprint window**: the next ~5 planned sprints. This is NOT the task
  table. Its row format is being ratified separately (the Aktiv-Sprint-planning step); until
  then, do not invent a format here — see Operation 6 (deferred).
- **`## Backlog`** — the **prioritized task pool and the intake for everything new**. One
  Schema-v2 row per task (10 columns, below), no prose in cells. This is the section this skill
  primarily manages. It absorbs both roles that a rough-notes intake section and the old
  `## Aktiv` task table used to split.
The archive does **not** live in the WORKLIST: finished tasks retire to
`chat-context/ARCHIVE.md` — **`## Archiv-Tasks`** (one line + link — a retrieval index,
**3 columns**, deliberately NOT the v2 schema) and **`## Archiv-Sprints`** (session narrative
pointers, written by `session-closure` directly, not by this skill). See WORKING_CONCEPT §11.3.

Task substance itself lives elsewhere: a real spec-doc (`spec/docs/features|bugs|chores/`) once
specced, or a carried-context file at `chat-context/tasks/<ID>-<slug>.md` (template:
`chat-context/templates/TEMPLATE-task.md`) before that. This skill manages the WORKLIST index
and, where warranted, the `tasks/` files — never the spec-doc layer.

Parametric over `PROJECT.md`: `fs_connector`, `workspace_root`, plus the two
instance vocabularies below.

## Schema v2 (enforced)

The Backlog table has **10 columns**:

```markdown
## Backlog

| # | Cluster | Titel | Komp | Typ | Prio | Größe | Disp | Status | Ref |
|---|---------|-------|------|-----|------|-------|------|--------|-----|
| CHORE-34 | 🔧 DEPLOY | One-sentence title, ≤150 chars | ops srv | chore | 🔴 P1 | 🌑 S | — | ⬜ todo | sprints/sprint-07-...md |
| FEAT-12  | 🧠 CORE  | One-sentence title, ≤150 chars | srv | feature | 🔴 P1 | 🌕 L | C | ⬜ todo | tasks/FEAT-12 · F-0009 |
```

**Marker vocabulary** (emoji + grep-able plain text — both are carried so the row stays
greppable by either):

- **Cluster** — the *primary theme*, NOT launch-blocking status (blocking rides on Prio-P1, so
  that a launch cluster doesn't swallow every gating task). **The cluster set is
  instance-defined** — declare it in `PROJECT.md` and keep this skill, the WORKLIST
  header, and the closure script in sync. Shipped default set:
  `🚀 LAUNCH` · `🔧 DEPLOY` · `🔒 SEC` · `🧠 CORE` · `🔌 CONN` · `📣 GTM` · `💎 EE` · `🧹 HK`
- **Prio:** `🔴 P1` · `🟠 P2` · `🔵 P3`
- **Größe:** `🌑 S` · `🌓 M` · `🌕 L`
- **Status:** `⬜ todo` · `🔄 in-progress` · `👀 needs-review` · `💤 deferred` · `🚧 partial`
- **Disp** (who executes): `C` = Code (autonomous dispatch) · `D` = Design · `—` = none / Concept
- **Komp** (touched components, space-separated): **instance-defined tokens** for the
  workspace's submodules/components, declared in `PROJECT.md`
  (e.g. `srv con ops infra web e2e doc spec ldev`), plus `—`

**Emoji are permitted here and in `WORKLIST.md` only** — they are functional marker data. They
remain forbidden in ADRs, specs, configs, and code.

**Titel — one sentence, ≤ 150 characters (hard).** The diet rule: strip retrospective prose
("… ist ERLEDIGT", "TEST-GATE-HÄLFTE ERLEDIGT") — the WORKLIST points forward, it is not a
sprint log; the retrospective belongs in the sprint record. Keep only the **open work core**.
If the open core *itself* exceeds 150 chars (non-negotiable sequences, hard preconditions),
move the substance into `chat-context/tasks/<ID>-<slug>.md` and let the Titel be the condensed
heading. Never lose unique open substance to the diet — only retrospective is dropped.

**ID prefixes:** `FEAT-`, `BUG-`, `CHORE-` (no generic `P-NNN`).

**No `✓`/checkmark column.** A row is retired by *archiving* (Operation 4), not by a status
flag; a finished row moves to Archiv-Tasks at the next closure.

## ID allocation — REGISTRY is the sole authority

`chat-context/REGISTRY.md` is the **single source of truth** for ID allocation. **Never** assign
an ID by scanning the WORKLIST, filenames, or prose — that is exactly the defect class of a
used ID without a REGISTRY row. To allocate: read the next-free number for the prefix from
REGISTRY, use it, and record the new row in REGISTRY as part of the same operation. Retired IDs
stay retired because REGISTRY, not a live-table scan, tracks them.

## Operations

### Operation 1: Add to Backlog

**When:** A task needs tracking — captured mid-session or formalized at closure. There is no
rough-notes staging area anymore; a task enters as a real Backlog row.

**Input:**
```
action: "add_to_backlog"
title: str            # one sentence, ≤150 chars — the Titel cell (apply the diet rule)
cluster: str          # one of the instance cluster set (primary theme)
komp: str             # space-separated component tokens, or "—"
typ: str              # "feature" | "bugfix" | "chore" | "test"
prio: str             # "P1" | "P2" | "P3"
size: str             # "S" | "M" | "L"
disp: str             # "C" | "D" | "—"
status: str           # "todo" | "in-progress" | "needs-review" | "deferred" | "partial"
position?: str        # "prio-cluster" (default: place per the Backlog sort) | "top"
                       #   | "after:<ID>" | "before:<ID>"
carried_context?: str # if there is more than the one-line title — seeds a tasks/ file (R1–R4)
```

**What happens:**
1. Read current WORKLIST.md.
2. Allocate the ID from REGISTRY (above); resolve Ref (R1–R4, below); write the `tasks/` file
   first if one is needed (so Ref never points at a missing file).
3. Emit the 10-column row with the emoji+text markers and insert it into `## Backlog` at
   `position` (default: within its Prio tier, then Cluster — matching the table's sort).
4. Record the ID in REGISTRY.
5. Write WORKLIST.md (and REGISTRY / the tasks/ file if touched); read back to confirm each.

**Ref-assignment rule (R1–R4):**
- **R3 first:** if an existing spec-doc / ADR / decision / finding already covers the substance,
  set `Ref` to that (as `Document#anchor` where a specific section is meant) — no `tasks/` file,
  even if `carried_context` was given (point there instead of duplicating).
- **R2:** if `carried_context` is non-trivial and no covering ref exists, create
  `chat-context/tasks/<ID>-<slug>.md` from `TEMPLATE-task.md`, populate `Kontext (carried)`,
  set `Ref = tasks/<ID>` (`spur` only if genuinely known; default `—`, no guessing).
- **No file, no ref:** `Ref = TBD`. Never create a near-empty `tasks/` file just to fill Ref.

### Operation 2: Reposition / re-sort

**When:** The Backlog is normally ordered **by Prio tier, then Cluster** — position is largely
derived, not manual. Use this op to (a) restore that sort after inserts, or (b) place a row
out-of-sort deliberately (rare, and worth a note in the row's Ref or a comment).

**Input:**
```
action: "reposition"
id: str
position: str   # "prio-cluster" (re-sort into place) | "top" | "after:<ID>" | "before:<ID>"
```

**What happens:** read → remove the row for `id` → reinsert at `position` → write → read back.
To move a row *between* Prio/Cluster buckets, change the marker (Operation 3), don't hand-place.

### Operation 3: Update markers (status / prio / cluster / size / disp / komp)

**When:** A marker changes but the task isn't finished. Supersedes the old status-only update —
any of the six marker fields can change here.

**Input:**
```
action: "update_row"
id: str
set: { status?, prio?, cluster?, size?, disp?, komp? }   # any subset, using the vocab above
```

**What happens:** read → find the row in `## Backlog` → set the given cells (emoji+text) →
write → read back. There is no `done` status; when a task is finished, use Operation 4.

### Operation 4: Archive a task (Backlog → Archiv-Tasks)

**When:** A task is genuinely finished (or superseded / resolved-by-prior-work) and its row
should retire.

**Input:**
```
action: "archive_task"
id: str
summary: str   # ≤200 chars — must DISCRIMINATE (which archived row is this), not summarize
                # at length. The link carries the real information.
link: str      # sprint file / ADR / decision / finding / another task's tasks/ file (superseded-by)
```

**What happens:**
1. Read current WORKLIST.md.
2. Remove the row from `## Backlog` (or `## Aktiv`, if it was promoted there).
3. Add a **3-column** row to `ARCHIVE.md` `## Archiv-Tasks`: `| id | summary | link |` —
   Archiv-Tasks does NOT use the v2 schema; it stays a lean retrieval index.
4. **Tasks/-file disposition** — if `chat-context/tasks/<id>-*.md` exists:
   - If `link` is a real spec-doc/ADR/decision/finding that now carries the substance: confirm
     the substance actually migrated there, then **delete** the tasks/ file (its job is done).
   - If archived as **superseded-by-another-task** (`link` → `tasks/<other-id>`): keep this
     file only if it holds distinct rationale not captured by the other; otherwise delete it.
   - If unsure, ask — deleting a tasks/ file is not reversible via this skill.
5. Write back; read back to confirm both tables.

### Operation 5: Promote from Tech-Debt

**When:** An item in `chat-context/TECH-DEBT.md` grows teeth — becomes worth tracking.

**Input:**
```
action: "promote_from_tech_debt"
source: str    # the bullet text in TECH-DEBT.md
# ...then the same fields as Operation 1 (add_to_backlog)
```

**What happens:** same as Operation 1, plus: remove the bullet from `TECH-DEBT.md`. Confirm
both files via read-back.

### Operation 6: Promote to Sprint (Backlog → ## Aktiv) — DEFERRED

**When:** A Backlog task is scheduled into one of the planned sprints in `## Aktiv`.

**Status: not yet defined.** The `## Aktiv` sprint-window row format is being ratified in the
separate Aktiv-Sprint-planning step. Until that format is fixed, do **not** invent a row shape
here — a sprint entry and a task row are different structures. When the format lands, this
operation gets its input contract (likely: `id`, target sprint, and whether the Backlog row
stays or moves). Flag any request to schedule sprints as blocked on that ratification.

## Closure-Consolidation Workflow

**At session-closure, Concept must:**
1. Ensure every task captured this session is a proper Backlog row (Operation 1) — no rough
   notes left dangling (there is no rough-notes staging area to sweep).
2. Archive any finished row (Operation 4) — don't leave finished work sitting in the Backlog
   across a closure boundary.
3. Re-sort the Backlog (Operation 2, `prio-cluster`) if inserts disturbed the order.
4. Read the final WORKLIST to verify structure before `session-closure` proceeds to the STARTER
   rewrite.

## Propose-Before-Write Discipline

Every operation is proposed first: state the exact operation, wait for an explicit go ("ok",
"ja", "passt", or a corrected variant), then execute. If the user says "batch-consolidate
everything," you may execute a sequence without per-op confirmation — but state the full batch
plan (every ID, target position/markers) first and wait for one approval.

## Validation Rules

- **id:** unique across `## Aktiv`, `## Backlog`, and `ARCHIVE.md` `## Archiv-Tasks`; allocated
  from REGISTRY (never from a live-table/filename scan).
- **cluster:** one of the instance cluster set (default: LAUNCH | DEPLOY | SEC | CORE | CONN |
  GTM | EE | HK).
- **typ:** one of feature | bugfix | chore | test.
- **prio:** one of P1 | P2 | P3.  **size:** one of S | M | L.  **disp:** one of C | D | —.
- **status:** one of todo | in-progress | needs-review | deferred | partial. No `done`
  (archiving retires a row, not a status flag).
- **komp:** space-separated tokens from the instance Komp vocabulary, or `—`.
- **Titel:** one sentence, ≤150 chars; reject a paragraph — route it to a `tasks/` file.
- **Ref:** a real `Document#anchor` / path / `tasks/<ID>` / `TBD` — nothing else.
- **Emoji:** only in the marker cells, using the exact vocabulary above; never decorative.

If validation fails, report the error and ask for correction before writing.

## File Safety

Follow the `fs-write` discipline (not whole-file rewrites): prefer anchored `edit_file` for
row-level changes to the existing WORKLIST, with `dryRun: true` before every mutation and a
read-back after apply; use whole-file `write_file` only for a brand-new `tasks/` file. Read
back every touched file — the WORKLIST section AND any `tasks/` / REGISTRY file changed in the
same operation. A filesystem connector can hang; if a call times out, don't retry into the
timeout — ask the operator to restart the MCP server.

If the WORKLIST structure is corrupted (malformed table), do NOT repair inline — report the
corruption and ask for manual intervention (git reset or manual edit).
