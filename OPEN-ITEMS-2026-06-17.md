# Open items after the platform-dev harmonization (2026-06-17)

Carry-over from the big harmonization session: blueprint finished + published,
script-runner installed for both instances, skills installed as a Desktop
plugin, Forgenesis migrated + committed, Kumbuka migrated + synced + committed
(superrepo stage), handover mechanism added to the blueprint. The items below
are the deliberate leftovers, grouped by where they get done. Each project gets
a dedicated after-rebuild session.

---

## Kumbuka (dedicated Kumbuka session)

1. **Stufe 1 — cut the chat-context out of the `platform-specs` submodule.**
   The superrepo now owns `chat-context/` (migrated + committed). Remove
   `spec/chat-context/` and `spec/scripts/` (old `qs.sh`/`qs-fetch.sh`, obsolete)
   from the active `platform-specs` repo. This is a commit INTO the live product
   repo — do it only after verifying the superrepo state is complete, and follow
   `platform-specs`' own direct-to-main convention. Until done, the chat-context
   exists in both places (harmless, but divergent if edited).

2. **Curate the `handover/` files.** Five files staged in
   `chat-context/handover/` (renamed to `handover-YYYY-MM-DD-<slug>.md`): sight,
   clean up, and fold their substance into the relevant sprint records /
   findings, then prune the consumed ones. Content work deliberately deferred
   from the migration.

3. **Resolve the Sonderlocken finding**
   (`chat-context/findings/migration-working-concept-kumbuka-specifics.md`):
   - Record the **decision-ID convention** (`D-LIC-*`/`D-OPS-*`/`D-CORE-*`) as a
     `convention` mnemonic in scope `kumbuka`.
   - Record the **direct-to-main commit workflow** (platform-specs no PR; impl
     repos keep PRs) as a `convention` mnemonic — it overrides the blueprint's
     operator-gated feature→main default, so it must be explicit.
   - Decide the home for the **north-star invariants** (P1 private-memory, tenant
     isolation, ops-no-content): a `spec/docs/` doctrine doc vs. `constraint`
     mnemonics vs. both.

4. **Note on the SESSION_NNN → sprint-NN rename.** Done in the superrepo (bridge
   table: `chat-context/sprints/README.md`). Prose references to "SESSION_NNN" in
   `spec/docs/` decision notes and in Kumbuka memory still use the old IDs —
   reconcile opportunistically; they are prose pointers, not broken links.

---

## Forgenesis (first platform session)

1. **Un-mount the `dev-archive` submodule** once its history is confirmed no
   longer needed live (the frozen archive holds the old platform-dev history;
   valuable history lives in the real submodules).
2. **ADR-P015 reconciliation** — the migrated chat-context is one step behind the
   ADR series (see `MIGRATION.md`); update the WORKLIST `## Pointer` accordingly.
3. **Decide §11/§18 re-expression** — the migration finding
   (`migration-working-concept-11-18-not-reexpressed.md`): the two Forgenesis-
   specific WORKING_CONCEPT sections that were not folded into the generic one.

---

## Blueprint (already done this session, propagation pending)

The **handover mechanism is now in the blueprint** (mandatory handover report
for every Code dispatch): `chat-context/handover/` + README, `code-handover`
skill (closure writes the report; after-return curates from `handover/`),
`WORKING_CONCEPT.md` §1.3/§3.3/§14.2/§14.3/§15, README layout. **Commit the
blueprint changes.**

**Propagation:** the handover mechanism must reach both instances —
- Forgenesis and Kumbuka each need `chat-context/handover/` (Kumbuka already has
  it from the migration; Forgenesis needs it added) and the updated
  `code-handover` skill + `WORKING_CONCEPT` §3.3/§14 carried in.
- Instance skills are account-bound **plugin ZIPs** — after changing a
  `SKILL.md`, **re-zip and re-upload** the instance's plugin in Claude Desktop
  (`docs/PLUGIN-INSTALL.md`). The repo is the source of truth; the uploaded
  plugin is a snapshot.

### Known blueprint inconsistency to sweep (separate, ratifiable)
`docs/WORKING_CONCEPT.md` still carries **`qs_tool`-era** language in §1.3, §1.4
(`qs_tool: run-qs-dev`), §3.1, §12, §15 — not yet updated to the
`script_runner_server` / `status_tool` / `gitstatus` model that PROJECT.md,
TOOLING.md, and the README already use. Deliberately left out of the handover
edit to keep that diff clean. Decide + sweep as its own change, then propagate.
