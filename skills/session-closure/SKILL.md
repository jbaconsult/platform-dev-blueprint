---
name: session-closure
description: Close a platform-dev session the manifest way — collect every judgment decision of the session into ONE closure manifest, let a dry-run surface any gap, ratify the verified plan at a single point, then run scripts/closure.py which performs all mechanical edits (findings, sprint file, WORKLIST/STARTER/ARCHIVE consolidation, REGISTRY, handover flips, STARTER rewrite) and the entire git phase itself; afterwards Concept only writes the repo-fingerprint from the post-push status read-back. Use this skill at the END of a session whenever the user signals wrap-up — triggers include "Closure", "schließe ab", "Session-Ende", "lass uns abschließen", "Sprint schließen", "geh ins Closure", "schreib den STARTER für morgen", or any request to persist results and prepare the next session. Use it even for a partial wrap ("halt hier fest und schreib den Stand fest").
---

# Session Closure

Persists a session's results and prepares the next.

**Authoritative sources:** order is `docs/WORKING_CONCEPT.md` §3.3; the task-file model is §11; git
discipline is §12. The mechanical part — including the whole git phase — is executed by
`scripts/closure.py`; this skill is the human-judgment wrapper around that script.

**Parametric over `PROJECT.md`:** `status_tool`, `fs_connector`, `workspace_root`, `adr_path`,
`increment_branch`, `memory_scope`, `project_name` (mirrored in `PROJECT_NAME` in
`scripts/closure.py`).

**Before any write:** read the write discipline in `docs/TOOLING.md` (or the `fs-write` skill).
Closure is where the connector's quirks bite — no parent auto-create, read-back needed.

---

## The model in one sentence

Concept writes every **judgment** decision of the session into ONE **closure manifest**
(`.scratch/closure-manifest.md` — the gitignored scratchpad, never committed), a **dry-run** surfaces
any gap the script can detect, the operator ratifies the verified plan at a **single** point, and
`scripts/closure.py` performs all mechanical edits **and the entire git phase** itself. Concept
afterwards writes only the `status.repo-fingerprint` from a post-push `<status_tool>` call. **Concept
touches git nowhere in a closure** — you never run a git command, and you don't need to know how the
script does its git work (that lives in the script, not here). **Git is the central backup** — the
script is fail-closed: one broken assertion or an unmerged PR and it commits nothing and says why.

**The discipline that keeps this fast: do not pre-verify what the oracle catches.** The expensive part
of a closure is not the writing — it is Concept rummaging ahead of the run ("is the sprint line stale?
are there New-Tasks stubs? which submodule is on which branch? is that ID registered?"). Every such
pre-check is a reasoning generator, and the script answers all of them fail-closed. Write the judgment
sections, run one dry-run, fix exactly what it flags. Nothing more.

---

## The boundary — script vs. Concept

**The script does (mechanical, from the manifest):** findings files · sprint file · WORKLIST/
STARTER/ARCHIVE consolidation (three-file model) · REGISTRY reconciliation · advancing the REGISTRY
sprint row · handover frontmatter flips · STARTER rewrite from the template · fail-closed assertions ·
**the entire git phase** (it syncs, commits, and pushes — you never touch git).

**Concept decides (judgment, INTO the manifest):** which findings and their content · the sprint
narrative · which tasks promote/archive/reposition and the discriminating archive summaries · the
New-Tasks triage · each handover's `closed`/`consumed` status · the STARTER's Erwartung and
Arbeitsauftrag · `tracks`/`ratified`.

**Concept does AFTER the run (not the script's job):** call `<status_tool>` post-push and write
`status.repo-fingerprint` (step 5) · `status.current-workstate` only on a real steering delta ·
emit the achievements list + boot copy-block (step 6).

**Never the script:** memory writes · ADR/Decision docs (must be on disk *before* the manifest
references them — via `adr-author`) · **Impl-submodule PR-merges** (GitHub UI) · the
achievements/copy-block.

---

## The two cross-cutting rules (still yours, now enforced at manifest-writing time)

**STARTER ≠ status mnemonic ≠ ARCHIVE.md — no duplication.** The STARTER is the full forward
briefing plus the Aktiv-Queue; a status mnemonic is a host/live *pointer*; `ARCHIVE.md` is the
historical index (one line + link). Restating one inside another is the failure mode this skill
exists to prevent. When you catch yourself writing retrospective prose ("erreicht", "geschafft",
"wo wir herkommen") into the `## STARTER Arbeitsauftrag` manifest section instead of the archive —
stop, that is the bug. The script rejects some of this (a `done` row left in the queue, a SHA in
the STARTER, a dropped (fix) section) but the *no-retrospective-prose* judgment is yours.

**Never freeze live/git state into a durable doc as prose.** SHAs, ahead/behind counts, committed-
file lists go stale by the next boot. They belong only in the post-push fingerprint mnemonic
(step 5), never in the STARTER. What the STARTER carries instead is the *expectation* the next
boot's status read is checked against — write expectation, not history, from the start.

---

## Preconditions (check before writing the manifest)

- Any decision that earned (or should earn) a stable ID this session is **ratified or explicitly
  deferred-with-trigger** — not half-open. A decision still in flight blocks closure.
- If a decision earned an ADR/D-* ID: its **document is already on disk** (via `adr-author`),
  because the manifest's `## Sprint` / `ratified` only *reference* it — the script writes no ADRs.
- **Every implementation-submodule PR is merged on GitHub before you run the closure.** An unmerged
  Impl submodule stops the run (exit 4) rather than pushing un-reviewed code — operator duty, the one
  git fact the closure depends on.
- The session's outcome is clear enough to narrate. If you cannot yet say what was decided, you are
  pausing, not closing (see *Partial closure*).

---

## Closure sequence (in order)

### 1. Write the closure manifest → `.scratch/closure-manifest.md`

One Markdown file: YAML frontmatter (structured decisions) + named `##` prose sections
(narratives). Write it to `.scratch/closure-manifest.md` with the `fs_connector` (create `.scratch/`
first if absent — the connector doesn't auto-create parents), read it back. The full schema is in the
**Manifest reference** below.

**Write the judgment, skip the bookkeeping — but do read your judgment inputs.** Your job is the four
prose sections, the archive summaries, the promote/archive/reposition decisions, `tracks`/`ratified`.
"Don't pre-verify" means: don't go check what the *oracle* catches — the REGISTRY sprint line, whether
`## New Tasks` needs `clear_new_tasks`. It does **not** mean writing blind: reading the current
**Aktiv-Queue** (to know what to archive/reposition, and whether a task is even in it) and the
**WORKLIST cluster/marker vocabulary** is legitimate judgment input, not an oracle duplicate — a
targeted read beats guessing-then-iterating on exit 2. Read those; skip the rest. And **`next_front`
is a proposal, not an optimization problem** — best guess at the coming front, the operator corrects
it at ratification; don't circle it.

The essentials while writing:

- **Quote any value containing `#` or a comma after a space** (the parser is stdlib-only, no
  PyYAML; unquoted `#` starts a comment). Long prose goes only in the `##` body sections — there
  are no `|`/`>` block scalars.
- **Section names are the grammar.** Only the exact names below are block boundaries; the sprint
  narrative may carry its own `##` headings freely. A mistyped section name falls into the previous
  block and the script's required-section check fails loud — so spell them exactly.
- **New-Tasks triage (only the stubs you know you jotted).** If you jotted stubs into `## New Tasks`
  this session, triage them now: lift the keepers into `worklist.add_to_backlog`/`add_to_queue` (they
  get an ID there), then set `worklist.clear_new_tasks: true`. If you're not sure any exist, leave it
  out — the dry-run reports `N ungesichtete Stubs` (exit 3) and *then* you read and triage.
- **New queue tasks + reposition:** give each new `add_to_queue` entry a `handle` (`h1`, `h2`, …)
  and reference the handle in `reposition` — never anticipate the ID the script will mint.

### 2. Dry-run — the oracle

Call the `closure` tool on `<script_runner_server>` with `manifest=.scratch/closure-manifest.md` and
bare `dry_run` (fallback: `python3 scripts/closure.py .scratch/closure-manifest.md --dry-run`,
cwd = `<workspace_root>`). It writes nothing and makes zero git calls (fully offline); it runs every
assertion and prints every planned diff.

**This replaces pre-verification of what it catches.** Instead of rummaging ahead of the run, let the
exit code tell you what's missing:

- **`2` schema** — a manifest field is malformed (unquoted `#`, a mistyped section name, a bad
  handle, an unknown cluster/marker). Fix that field.
- **`3` assertion** — a fail-closed invariant would break, named precisely: `clear_new_tasks` missing
  with N stubs, a `done` row in the queue, a dead pointer, disjointness, a frozen SHA in the STARTER.
  Fix exactly that.
- **`0`** — the plan is clean. The printed diff *is* the preview the operator ratifies in step 3.

Loop step 1 ↔ 2 until exit 0 — each fix is surgical, aimed at what the oracle named. Do not try to
make the manifest perfect up front; make it green. (The git phase isn't checked here — a forgotten
Impl-PR-merge surfaces only at the real run, exit 4, harmlessly. See step 4.)

### 3. Ratify — the single point

Present the clean dry-run plan to the operator (the diff, or a pointer to the manifest) and get one
explicit ratification. **This is the one ratification gate of the closure.** Do not drip-ratify
individual edits; the verified manifest is the unit.

### 4. Run the script (for real)

Call the `closure` tool on `<script_runner_server>` with `manifest=.scratch/closure-manifest.md`, no
`dry_run`. **It does the whole git phase itself — you issue no git commands.** You only read the exit
code:

- **`0`** (`ok <sha>`) — committed and pushed. Done.
- **`4`** — an Impl-PR isn't merged on GitHub, or a push/network failure. **Nothing was written.**
  Merge the PR, run again.
- **`2`/`3`** — a manifest problem the dry-run should have caught; if it slips through, fix as in
  step 2 and rerun.

Nothing to undo on any non-zero exit — the git gate and assertions run before the first write.

### 5. After a green run — status read-back + repo-fingerprint

The script has committed and pushed. Now, and only now:

- Call `<status_tool>` yourself — it is read-only, not git-gated. This is also the post-run control
  check: the working tree should be clean but for anything deliberately left.
- From that **post-push** output write `status.repo-fingerprint` via forget+remember on the fixed
  key: per-submodule SHA + branch + clean-flag, superrepo only branch + clean (**never its own
  HEAD** — the closure commit just changed it). **No propose-before-write gate** — this is a
  mechanical transcription of verified tool output. Confirm the write landed.
- `status.current-workstate` only if there is a real steering delta (host/live facts the status
  tool can't surface, the coming front). No delta → skip memory entirely and say so.

If `<status_tool>` genuinely isn't loaded (reduced-runtime/mobile boot), ask the operator to paste
a post-push read-back; never write an unverified fingerprint.

### 6. Session end — achievements + boot copy-block (the final act)

Print a short bullet list of the session's achievements (the one place a retrospective belongs — a
chat message, not a durable doc). Then the boot trigger, in a **code block** or the operator
overlooks it:

```markdown
Titel des Chats: <project_name> Sprint #<N> — <front>

Rufe zu Beginn memory_load_context(scope="<memory_scope>") auf und befolge jede
type=constraint-Regel. Inhaltliches gehört nach Git, nicht ins Memory.

Boote die Session (session-start) und lies chat-context/STARTER.md — Schema
chat-context/templates/TEMPLATE-starter.md: die (fix)-Sektionen (Apparatur · Boot · Method) gelten
unverändert; arbeite den Arbeitsauftrag ab.
```

Then a goodbye — nothing after it.

---

## Manifest reference (the ratified schema)

```yaml
---
sprint: <NN>                 # the session being CLOSED
next_sprint: <NN+1>          # STARTER to write
next_front: "<front title>"  # → title "<project_name> Sprint #<NN+1> — <front>"; a proposal, corrected at ratification
date: <YYYY-MM-DD>
sprint_slug: <kebab>         # → sprints/sprint-<NN>-<slug>.md; also the commit-message tail
commit_message: "<text>"     # optional; used for ALL commits of the run. else "Sprint <NN> closure: <sprint_slug>"
tracks: [ <t>, … ]           # optional; default [cross-cutting]        (E1)
ratified: [ <ID>, … ]        # optional; default []                     (E1)

findings:                    # optional; one file each. id minted from REGISTRY.
  - { category: <slug>, severity: <low|medium|high>, component: <slug>, slug: <kebab> }

worklist:
  add_to_backlog:            # brand-new task → WORKLIST Backlog (id minted)
    - { cluster, titel, komp, typ, prio, groesse, disp, status, ref }
  add_to_queue:              # brand-new task → STARTER Aktiv-Queue (id minted)
    - { handle: h1, cluster, titel, komp, typ, prio, groesse, disp, status, ref }   # handle optional (E2)
  promote: [ <ID>, … ]       # existing Backlog ID → Aktiv-Queue (row pulled, removed from Backlog)
  archive:                   # Aktiv-Queue ID → ARCHIVE ## Archiv-Tasks
    - { id: <ID>, summary: "<=200 chars, discriminating", ref: <link> }
  reposition: [ <ID|handle>, … ]   # final queue order; handles allowed & substituted (E2)
  clear_new_tasks: true      # REQUIRED once ## New Tasks holds stubs; else exit 3

handover:                    # one flip per touched pair
  - { dispatch: <file>, return: <file>, status: <closed|consumed>, curated_in: <path?> }
---

## Sprint
<full sprint narrative — may contain its own ## headings>

## Finding: <slug>
<body, per findings[] entry>

## STARTER Erwartung
<expectation the next boot's status read is checked against; anomalies; stale mnemonics. No frozen SHAs.>

## STARTER Arbeitsauftrag
<forward only — next tasks from the top of the Aktiv-Queue, first task in startable detail,
 guardrails, frame. No retrospective prose.>

## STARTER Code-Interface
<optional; the Hin-/Rückgabe block if the next session's first act dispatches Code; else omit → n/a>

## Achievements
<chat-only; the script ignores this section>
```

**Canonicalization the script applies:** `cluster`/`prio`/`groesse`/`status` accept marker form
(`"🔧 DEPLOY"`) or plaintext (`DEPLOY`), canonicalized to marker form; unknown → exit 2 (the cluster
vocabulary is instance-defined — `CLUSTERS` in `scripts/closure.py`). `typ` → family: feature→FEAT,
chore→CHORE, bugfix/test→BUG. `disp: -` → `—`. Titel >150 chars or archive summary >200 chars →
exit 2. `add_to_backlog` appends to the Backlog end; archive rows land newest-first. STARTER (fix)
sections are copied verbatim from `TEMPLATE-starter.md`; the Aktiv-Queue gets the generic template
blockquote (put sprint-specific context in the Arbeitsauftrag). `consumed` requires `curated_in`.
The REGISTRY sprint row is advanced automatically — you never touch it.

---

## Partial closure (pausing, not finishing)

If the session is interrupted mid-work and the goal is to save state safely, do **not** fake a full
closure. The script is built for a full closure; a pause is usually lighter than a manifest run:

- **STARTER** — rewrite the Arbeitsauftrag to say honestly *"mid-flight, not cleanly closed"* with
  the concrete next action. You may do this via a minimal manifest (only the STARTER sections +
  next_sprint/front, no findings/archive) and a dry-run to preview — or, if the script would be
  overkill for a one-section touch, hand-edit the STARTER via the connector and skip the script.
- **A holding finding** if anything half-done would otherwise be lost.
- The **git phase is optional** on a pause — run the script for a checkpoint commit only if you
  want one; a pause does not require pushing.

**The tell:** if the Arbeitsauftrag reads "continue X" rather than "start the next front," you are
pausing, and skipping the sprint file / archiving / fingerprint is correct — not an omission.

---

## Definition of done — final self-check

Most mechanical invariants are now the script's fail-closed assertions (disjointness, no `done` in
the queue, (fix) sections verbatim, no frozen git-state, REGISTRY rows + sprint-line advance,
no half-flipped handover, dead-pointer check, New-Tasks emptied, the git phase). Concept's residual
checks before emitting step 6:

- [ ] The manifest captured every outcome: findings, the sprint narrative, all WORKLIST
      dispositions, every touched handover pair's status, the New-Tasks triage (`clear_new_tasks`
      set if stubs existed), tracks/ratified.
- [ ] Any ADR/D-* earned this session is on disk (via `adr-author`) and referenced, not invented in
      the manifest.
- [ ] The dry-run reached exit 0 before the real run, and the **real run exited `0`** — not "mostly
      worked". A non-zero exit is a closure that has **not** happened; fix and re-run.
- [ ] `status.repo-fingerprint` written from the post-push status read-back (step 5); no other
      `status.*` write without a stated Git-can't-carry-this reason.

A failed check is a closure bug to fix before step 6, not after.

---

## Appendix — findings that need a ratified closure

Some findings need a ratified decision to resolve: (1) put the finding in `findings[]`; (2) ratify
the decision; (3) it lands via `adr-author` (ADR or D-*) **before** the manifest run; (4) the
finding body references the decision doc ("Resolved by ADR-0019").
