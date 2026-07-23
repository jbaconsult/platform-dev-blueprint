"""Fixture test suite for scripts/closure.py (manifest-driven closure).

Never touches the live steering files — every test runs against a copy of
scripts/tests/fixtures/ in a temp sandbox with its own git repo and a bare
"origin" remote, so commit AND push are exercised for real.

Run:  python3 -m unittest discover -s scripts/tests -v   (cwd = workspace root)
"""

import hashlib
import os
import shutil
import subprocess
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
FIXTURES = os.path.join(HERE, "fixtures")
SCRIPT = os.path.abspath(os.path.join(HERE, "..", "closure.py"))

MARKER_EMOJIS = "🔧🔒🧠🔴🟠🔵🌑🌓🌕⬜🔄👀💤🚧🚀📣💎🧹🔌"

HAPPY_MANIFEST = """---
sprint: 108
next_sprint: 109
next_front: "Test-Front"
date: 2026-07-18
sprint_slug: test-closure

findings:
  - category: process
    severity: low
    component: tooling
    slug: closure-script-probe

worklist:
  add_to_backlog:
    - { cluster: "🧹 HK", titel: "Backlog-Testtask — Fixture mit em-dash, Komma und Emoji 🔌", komp: "—", typ: chore, prio: "🔵 P3", groesse: "🌑 S", disp: "—", status: "⬜ todo", ref: "sprints/sprint-108-test-closure.md" }
  add_to_queue:
    - { cluster: "🔒 SEC", titel: "Queue-Testtask (neue ID direkt in die Aktiv-Queue)", komp: srv, typ: feature, prio: "🔴 P1", groesse: "🌓 M", disp: C, status: "⬜ todo", ref: TBD }
  promote:
    - CHORE-165
  archive:
    - { id: CHORE-178, summary: "Deploy-Welle \\"#103\\" Rest abgeschlossen — diskriminierende Test-Summary", ref: "sprints/sprint-108-test-closure.md" }
  reposition:
    - [ CHORE-138, CHORE-165, FEAT-59, BUG-04 ]

handover:
  - { dispatch: dispatch-2026-07-18-test-slug.md, return: handover-2026-07-18-test-slug.md, status: consumed, curated_in: sprints/sprint-108-test-closure.md }
---

## Sprint

# Sprint 108 — Test-Closure (Fixture-Narrativ)

## Wo wir standen

Fixture-Ausgangslage mit Umlauten (äöüß) und em-dash — deterministisch.

## Was entschieden / ratifiziert wurde

Closure-Testlauf: closure.py gebaut.

## Finding: closure-script-probe

# Testfinding — Emoji-Probe 🔧 und Umlaute äöüß

## Beobachtung

Deterministische Fixture-Beobachtung.

## Nächster Schritt

Keiner — Testartefakt.

## STARTER Erwartung

- **Erwartet:** Superrepo `main` synchron, working tree clean.
- **Anomalien & Bedeutungen:** keine — Fixture.

## STARTER Arbeitsauftrag

- **Nächste Aufgabe (oberste Queue-Zeile):** CHORE-138 — Fixture-Auftrag, rein vorwärtsgerichtet.
- **Guardrails:** keine Secrets ins Repo.

## Achievements

- Wird vom Script ignoriert (nur Chat-Output).
"""


def run(cwd, *args, expect=0):
    proc = subprocess.run(args, cwd=cwd, capture_output=True, text=True)
    if expect is not None and proc.returncode != expect:
        raise AssertionError(f"{args} rc={proc.returncode}\nstdout:\n{proc.stdout}\nstderr:\n{proc.stderr}")
    return proc


def run_closure(sandbox, manifest_text, *flags):
    manifest = os.path.join(sandbox, "manifest.md")
    with open(manifest, "w", encoding="utf-8") as fh:
        fh.write(manifest_text)
    return subprocess.run([sys.executable, SCRIPT, manifest, *flags],
                          cwd=sandbox, capture_output=True, text=True)


def tree_hashes(root):
    out = {}
    for dirpath, _, filenames in os.walk(os.path.join(root, "chat-context")):
        for name in filenames:
            path = os.path.join(dirpath, name)
            with open(path, "rb") as fh:
                out[os.path.relpath(path, root)] = hashlib.sha256(fh.read()).hexdigest()
    return out


def commit_count(cwd):
    return int(run(cwd, "git", "rev-list", "--count", "HEAD").stdout.strip())


def read(sandbox, rel):
    with open(os.path.join(sandbox, rel), encoding="utf-8") as fh:
        return fh.read()


class ClosureTestCase(unittest.TestCase):
    def setUp(self):
        self.sandbox = tempfile.mkdtemp(prefix="closure-sandbox-")
        self.origin = tempfile.mkdtemp(prefix="closure-origin-")
        self.addCleanup(shutil.rmtree, self.sandbox, ignore_errors=True)
        self.addCleanup(shutil.rmtree, self.origin, ignore_errors=True)
        shutil.copytree(FIXTURES, self.sandbox, dirs_exist_ok=True)
        run(self.sandbox, "git", "init", "-q", "-b", "main")
        run(self.sandbox, "git", "config", "user.email", "closure-test@example.invalid")
        run(self.sandbox, "git", "config", "user.name", "closure-test")
        run(self.sandbox, "git", "config", "commit.gpgsign", "false")
        run(self.sandbox, "git", "add", "-A")
        run(self.sandbox, "git", "commit", "-q", "-m", "fixture baseline")
        run(self.origin, "git", "init", "-q", "--bare", "-b", "main")
        run(self.sandbox, "git", "remote", "add", "origin", self.origin)
        run(self.sandbox, "git", "push", "-q", "-u", "origin", "main")

    # ------------------------------------------------------------------ happy

    def test_happy_path_dry_run_changes_nothing(self):
        before = tree_hashes(self.sandbox)
        proc = run_closure(self.sandbox, HAPPY_MANIFEST, "--dry-run")
        self.assertEqual(proc.returncode, 0, proc.stderr + proc.stdout)
        self.assertIn("ok (dry-run)", proc.stdout)
        self.assertIn("geplanter git-Block:", proc.stdout)
        # expected diffs are previewed
        self.assertIn("b/chat-context/STARTER.md", proc.stdout)
        self.assertIn("b/chat-context/WORKLIST.md", proc.stdout)
        self.assertIn("b/chat-context/ARCHIVE.md", proc.stdout)
        self.assertIn("b/chat-context/REGISTRY.md", proc.stdout)
        self.assertIn("b/chat-context/sprints/sprint-108-test-closure.md", proc.stdout)
        self.assertIn("finding-process-2026-07-18-closure-script-probe.md", proc.stdout)
        # nothing written, nothing committed
        self.assertEqual(before, tree_hashes(self.sandbox))
        self.assertEqual(commit_count(self.sandbox), 1)

    def test_happy_path_real_run(self):
        old_worklist = read(self.sandbox, "chat-context/WORKLIST.md")
        promoted_line = next(l for l in old_worklist.splitlines(keepends=True)
                             if l.startswith("| CHORE-165 |"))
        proc = run_closure(self.sandbox, HAPPY_MANIFEST)
        self.assertEqual(proc.returncode, 0, proc.stderr + proc.stdout)
        self.assertRegex(proc.stdout.strip().splitlines()[-1], r"^ok [0-9a-f]{40}$")

        # finding written with the allocated ID
        finding = read(self.sandbox,
                       "chat-context/findings/finding-process-2026-07-18-closure-script-probe.md")
        self.assertIn("id: F-0180", finding)
        self.assertIn("status: open/new", finding)
        self.assertIn("severity: low", finding)
        self.assertIn("Emoji-Probe 🔧", finding)

        # sprint file written; E1 defaults apply when tracks/ratified absent
        sprint = read(self.sandbox, "chat-context/sprints/sprint-108-test-closure.md")
        self.assertIn("sprint: 108", sprint)
        self.assertIn("Fixture-Ausgangslage mit Umlauten (äöüß)", sprint)
        self.assertIn("tracks: [cross-cutting]", sprint)
        self.assertIn("ratified: []", sprint)

        # worklist: promoted row gone, others intact, new backlog task appended
        worklist = read(self.sandbox, "chat-context/WORKLIST.md")
        self.assertNotIn("| CHORE-165 |", worklist)
        self.assertIn("| CHORE-166 |", worklist)
        self.assertIn("| FEAT-56 |", worklist)
        self.assertIn("| CHORE-184 | 🧹 HK | Backlog-Testtask — Fixture mit em-dash, Komma und Emoji 🔌 |", worklist)

        # starter: rewritten from template, queue in reposition order
        starter = read(self.sandbox, "chat-context/STARTER.md")
        self.assertIn('title: "example-project Sprint #109 — Test-Front"', starter)
        self.assertIn("# example-project Sprint #109 — Test-Front", starter)
        self.assertIn("Dies ist **Concept/Desktop**", starter)  # fix section content present
        self.assertNotIn("| CHORE-178 |", starter)
        queue_ids = [l.split("|")[1].strip() for l in starter.splitlines()
                     if l.startswith("| ") and not l.startswith("| # |")]
        self.assertEqual(queue_ids, ["CHORE-138", "CHORE-165", "FEAT-59", "BUG-04"])
        # UTF-8 read-back: the moved row is byte-identical in its new home
        self.assertIn(promoted_line, starter)
        self.assertIn("n/a", starter)  # Code-Interface defaulted

        # archive: newest-first row for the archived task
        archive = read(self.sandbox, "chat-context/ARCHIVE.md")
        self.assertIn('| CHORE-178 | Deploy-Welle "#103" Rest abgeschlossen — diskriminierende Test-Summary | sprints/sprint-108-test-closure.md |', archive)
        arch_rows = [l for l in archive.splitlines() if l.startswith("| CHORE")]
        self.assertTrue(arch_rows[0].startswith("| CHORE-178 |"), "archive row not at top")

        # registry: counters bumped, rows added, archived Ort repointed
        registry = read(self.sandbox, "chat-context/REGISTRY.md")
        self.assertIn("| CHORE-185 |", registry)   # counter
        self.assertIn("| FEAT-60 |", registry)     # counter
        self.assertIn("| F-0181 |", registry)      # counter
        self.assertIn("| CHORE-184 | Backlog-Testtask", registry)
        self.assertIn("| FEAT-59 | Queue-Testtask", registry)
        self.assertIn("| F-0180 | Testfinding — Emoji-Probe 🔧 und Umlaute äöüß | findings/finding-process-2026-07-18-closure-script-probe.md |", registry)
        self.assertIn("| CHORE-178 | Deploy-Welle #103 Rest: EE-server v0.8.2 + web | sprints/sprint-108-test-closure.md |", registry)

        # handover: both flipped, curated-in inserted where missing
        dispatch = read(self.sandbox, "chat-context/handover/dispatch-2026-07-18-test-slug.md")
        ret = read(self.sandbox, "chat-context/handover/handover-2026-07-18-test-slug.md")
        self.assertIn("status: consumed", dispatch)
        self.assertIn("curated-in: sprints/sprint-108-test-closure.md", dispatch)
        self.assertIn("status: consumed", ret)
        self.assertIn("curated-in: sprints/sprint-108-test-closure.md", ret)

        # no mojibake anywhere
        for rel in ("chat-context/STARTER.md", "chat-context/WORKLIST.md",
                    "chat-context/ARCHIVE.md", "chat-context/REGISTRY.md"):
            self.assertNotIn("�", read(self.sandbox, rel), f"replacement char in {rel}")

        # git: committed and pushed
        self.assertEqual(commit_count(self.sandbox), 2)
        msg = run(self.sandbox, "git", "log", "-1", "--format=%s").stdout.strip()
        self.assertEqual(msg, "Sprint 108 closure: test-closure")
        local = run(self.sandbox, "git", "rev-parse", "main").stdout.strip()
        remote = run(self.origin, "git", "rev-parse", "main").stdout.strip()
        self.assertEqual(local, remote, "push did not land on origin")
        # add -A price (deliberate): the manifest inside the
        # working tree rides the commit — nothing is selectively left out
        tracked = run(self.sandbox, "git", "ls-files").stdout
        self.assertIn("manifest.md", tracked)

    # ------------------------------------------------------------- null / fix

    def test_null_probe_archive_id_not_in_queue_fails_red(self):
        """F-0152 class: the gate must actually turn red — and commit nothing."""
        broken = HAPPY_MANIFEST.replace("id: CHORE-178", "id: CHORE-166")  # in backlog, not queue
        before = tree_hashes(self.sandbox)
        proc = run_closure(self.sandbox, broken)
        self.assertEqual(proc.returncode, 3, proc.stdout + proc.stderr)
        self.assertIn("steht nicht in der Aktiv-Queue", proc.stderr)
        self.assertEqual(before, tree_hashes(self.sandbox), "fail-closed run must write nothing")
        self.assertEqual(commit_count(self.sandbox), 1, "fail-closed run must not commit")

    def test_null_probe_dropped_fix_section_fails_red(self):
        tpl_path = os.path.join(self.sandbox, "chat-context/templates/TEMPLATE-starter.md")
        with open(tpl_path, encoding="utf-8") as fh:
            tpl = fh.read()
        start = tpl.index("## Method & Konvention (fix)")
        end = tpl.index("## Erwartung & Anomalien")
        with open(tpl_path, "w", encoding="utf-8") as fh:
            fh.write(tpl[:start] + tpl[end:])
        run(self.sandbox, "git", "commit", "-aqm", "mutilate template")  # keep tree clean
        proc = run_closure(self.sandbox, HAPPY_MANIFEST)
        self.assertNotEqual(proc.returncode, 0)
        self.assertIn("(fix)-Sektion fehlt im Template", proc.stderr)
        self.assertEqual(commit_count(self.sandbox), 2, "must not commit on a broken template")

    def test_null_probe_reposition_id_set_mismatch(self):
        broken = HAPPY_MANIFEST.replace("[ CHORE-138, CHORE-165, FEAT-59, BUG-04 ]",
                                        "[ CHORE-138, CHORE-165, FEAT-59 ]")
        proc = run_closure(self.sandbox, broken)
        self.assertEqual(proc.returncode, 3, proc.stdout + proc.stderr)
        self.assertIn("reposition", proc.stderr)
        self.assertEqual(commit_count(self.sandbox), 1)

    def test_schema_violation_consumed_without_curated_in(self):
        broken = HAPPY_MANIFEST.replace(", curated_in: sprints/sprint-108-test-closure.md", "")
        proc = run_closure(self.sandbox, broken)
        self.assertEqual(proc.returncode, 2, proc.stdout + proc.stderr)
        self.assertIn("curated_in", proc.stderr)

    def test_dead_pointer_ref_fails_red(self):
        broken = HAPPY_MANIFEST.replace(
            'ref: "sprints/sprint-108-test-closure.md" }\n  add_to_queue',
            'ref: "sprints/does-not-exist.md" }\n  add_to_queue')
        proc = run_closure(self.sandbox, broken)
        self.assertEqual(proc.returncode, 3, proc.stdout + proc.stderr)
        self.assertIn("Toter Zeiger", proc.stderr)
        self.assertEqual(commit_count(self.sandbox), 1)

    # ------------------------------------------------------------------ utf-8

    def test_utf8_promote_reposition_roundtrip(self):
        """F-0117 / F-0179: marker emojis and em-dashes survive a promote +
        reposition byte-identically; second independent run (n=2 with the
        happy-path test, which asserts the same property)."""
        manifest = """---
sprint: 108
next_sprint: 109
next_front: "UTF-8-Probe"
date: 2026-07-18
sprint_slug: test-closure

worklist:
  promote:
    - CHORE-165
  reposition:
    - [ CHORE-165, CHORE-178, CHORE-138, BUG-04 ]
---

## Sprint

# Sprint 108 — UTF-8-Probe

Minimalnarrativ.

## STARTER Erwartung

- **Erwartet:** clean.

## STARTER Arbeitsauftrag

- **Nächste Aufgabe:** CHORE-165.
"""
        old_worklist = read(self.sandbox, "chat-context/WORKLIST.md")
        promoted_line = next(l for l in old_worklist.splitlines(keepends=True)
                             if l.startswith("| CHORE-165 |"))
        old_starter = read(self.sandbox, "chat-context/STARTER.md")
        kept_lines = [l for l in old_starter.splitlines(keepends=True)
                      if l.startswith(("| CHORE-178 |", "| CHORE-138 |", "| BUG-04 |"))]
        proc = run_closure(self.sandbox, manifest)
        self.assertEqual(proc.returncode, 0, proc.stderr + proc.stdout)
        starter = read(self.sandbox, "chat-context/STARTER.md")
        self.assertIn(promoted_line, starter)
        for line in kept_lines:
            self.assertIn(line, starter, "existing queue row not byte-identical after rewrite")
        for emoji in MARKER_EMOJIS:
            if emoji in old_starter or emoji in promoted_line:
                self.assertIn(emoji, starter, f"marker emoji {emoji!r} lost")
        self.assertNotIn("�", starter)

    # --------------------------------------------------- E1: tracks/ratified

    def test_e1_tracks_ratified_verbatim_from_manifest(self):
        manifest = HAPPY_MANIFEST.replace(
            "sprint_slug: test-closure\n",
            "sprint_slug: test-closure\ntracks: [A2, cross-cutting]\nratified: [CHORE-01, ADR-0038]\n")
        proc = run_closure(self.sandbox, manifest)
        self.assertEqual(proc.returncode, 0, proc.stderr + proc.stdout)
        sprint = read(self.sandbox, "chat-context/sprints/sprint-108-test-closure.md")
        self.assertIn("tracks: [A2, cross-cutting]", sprint)
        self.assertIn("ratified: [CHORE-01, ADR-0038]", sprint)

    # -------------------------------------------------- E2: reposition handle

    def test_e2_handle_resolved_to_allocated_id(self):
        manifest = HAPPY_MANIFEST.replace(
            '{ cluster: "🔒 SEC", titel: "Queue-Testtask (neue ID direkt in die Aktiv-Queue)"',
            '{ handle: h1, cluster: "🔒 SEC", titel: "Queue-Testtask (neue ID direkt in die Aktiv-Queue)"'
        ).replace("[ CHORE-138, CHORE-165, FEAT-59, BUG-04 ]",
                  "[ CHORE-138, h1, CHORE-165, BUG-04 ]")
        proc = run_closure(self.sandbox, manifest)
        self.assertEqual(proc.returncode, 0, proc.stderr + proc.stdout)
        starter = read(self.sandbox, "chat-context/STARTER.md")
        queue_ids = [l.split("|")[1].strip() for l in starter.splitlines()
                     if l.startswith("| ") and not l.startswith("| # |")]
        self.assertEqual(queue_ids, ["CHORE-138", "FEAT-59", "CHORE-165", "BUG-04"])
        self.assertNotIn("h1", "".join(queue_ids), "handle must never reach the disk")

    def test_e2_null_probe_undefined_handle(self):
        manifest = HAPPY_MANIFEST.replace("[ CHORE-138, CHORE-165, FEAT-59, BUG-04 ]",
                                          "[ CHORE-138, h2, CHORE-165, FEAT-59, BUG-04 ]")
        before = tree_hashes(self.sandbox)
        proc = run_closure(self.sandbox, manifest)
        self.assertEqual(proc.returncode, 2, proc.stdout + proc.stderr)
        self.assertIn("'h2' ist in add_to_queue nicht definiert", proc.stderr)
        self.assertEqual(before, tree_hashes(self.sandbox))
        self.assertEqual(commit_count(self.sandbox), 1)

    # ------------------------------------------------------- New-Tasks channel

    NEW_TASK_STUBS = ("- Rate-Limit-Doku nachziehen — Notiz mit em-dash und Emoji 🔒\n"
                      "- zweiter roher Stub (wird verworfen)\n")

    def _inject_stubs(self):
        path = os.path.join(self.sandbox, "chat-context/WORKLIST.md")
        with open(path, encoding="utf-8") as fh:
            content = fh.read()
        content = content.replace("der Rest wird verworfen. Diese Sektion ist bei Closure-Ende leer.\n\n",
                                  "der Rest wird verworfen. Diese Sektion ist bei Closure-Ende leer.\n\n"
                                  + self.NEW_TASK_STUBS + "\n")
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(content)

    def test_new_tasks_unreviewed_stubs_fail_red(self):
        self._inject_stubs()
        before = tree_hashes(self.sandbox)
        proc = run_closure(self.sandbox, HAPPY_MANIFEST)  # no clear_new_tasks flag
        self.assertEqual(proc.returncode, 3, proc.stdout + proc.stderr)
        self.assertIn("New Tasks: 2 ungesichtete Stubs", proc.stderr)
        self.assertIn("clear_new_tasks: true", proc.stderr)
        self.assertEqual(before, tree_hashes(self.sandbox), "must write nothing")
        self.assertEqual(commit_count(self.sandbox), 1)

    def test_new_tasks_cleared_and_logged(self):
        self._inject_stubs()
        manifest = HAPPY_MANIFEST.replace("worklist:\n", "worklist:\n  clear_new_tasks: true\n")
        proc = run_closure(self.sandbox, manifest)
        self.assertEqual(proc.returncode, 0, proc.stderr + proc.stdout)
        # every removed stub logged, byte-preserved (emoji + em-dash)
        self.assertIn("removed new-task stub: Rate-Limit-Doku nachziehen — Notiz mit em-dash und Emoji 🔒",
                      proc.stdout)
        self.assertIn("removed new-task stub: zweiter roher Stub (wird verworfen)", proc.stdout)
        worklist = read(self.sandbox, "chat-context/WORKLIST.md")
        nt_section = worklist.split("## New Tasks")[1].split("## Backlog")[0]
        self.assertNotIn("\n- ", nt_section, "New-Tasks section must be empty after the run")
        # the lifted stub arrived as a real backlog row with a fresh ID
        self.assertIn("| CHORE-184 | 🧹 HK | Backlog-Testtask", worklist)

    # -------------------------------------------- closure.sh (MCP decorator)

    def _install_wrapper(self):
        """Copy closure.py + closure.sh into the sandbox's scripts/ dir so the
        decorator runs end-to-end against the sandbox repo."""
        scripts_dir = os.path.join(self.sandbox, "scripts")
        os.makedirs(scripts_dir, exist_ok=True)
        shutil.copy(SCRIPT, os.path.join(scripts_dir, "closure.py"))
        shutil.copy(os.path.join(os.path.dirname(SCRIPT), "closure.sh"),
                    os.path.join(scripts_dir, "closure.sh"))

    def _run_wrapper(self, *args):
        return subprocess.run(["bash", "scripts/closure.sh", *args],
                              cwd=self.sandbox, capture_output=True, text=True)

    def test_decorator_real_run_passes_through(self):
        self._install_wrapper()
        with open(os.path.join(self.sandbox, "manifest.md"), "w", encoding="utf-8") as fh:
            fh.write(HAPPY_MANIFEST)
        proc = self._run_wrapper("manifest=manifest.md")
        self.assertEqual(proc.returncode, 0, proc.stderr + proc.stdout)
        self.assertRegex(proc.stdout.strip().splitlines()[-1], r"^ok [0-9a-f]{40}$")
        self.assertEqual(commit_count(self.sandbox), 2)
        local = run(self.sandbox, "git", "rev-parse", "main").stdout.strip()
        remote = run(self.origin, "git", "rev-parse", "main").stdout.strip()
        self.assertEqual(local, remote)

    def test_decorator_passes_exit_code_and_stderr(self):
        self._install_wrapper()
        broken = HAPPY_MANIFEST.replace("id: CHORE-178", "id: CHORE-166")
        with open(os.path.join(self.sandbox, "manifest.md"), "w", encoding="utf-8") as fh:
            fh.write(broken)
        proc = self._run_wrapper("manifest=manifest.md")
        self.assertEqual(proc.returncode, 3, "decorator must not swallow the exit code")
        self.assertIn("FAIL: ASSERTION:", proc.stderr, "decorator must not swallow stderr")

    def test_decorator_usage_without_manifest(self):
        self._install_wrapper()
        proc = self._run_wrapper()
        self.assertEqual(proc.returncode, 1)
        self.assertIn("missing required argument: manifest=", proc.stderr)

    def test_decorator_dry_run_skips_push_preflight(self):
        self._install_wrapper()
        run(self.sandbox, "git", "remote", "remove", "origin")  # any preflight would fail now
        with open(os.path.join(self.sandbox, "manifest.md"), "w", encoding="utf-8") as fh:
            fh.write(HAPPY_MANIFEST)
        before = tree_hashes(self.sandbox)
        proc = self._run_wrapper("manifest=manifest.md", "dry_run")
        self.assertEqual(proc.returncode, 0, proc.stderr + proc.stdout)
        self.assertIn("ok (dry-run)", proc.stdout)
        self.assertEqual(before, tree_hashes(self.sandbox))

    def test_decorator_preflight_refuses_before_any_write(self):
        self._install_wrapper()
        run(self.sandbox, "git", "remote", "remove", "origin")
        with open(os.path.join(self.sandbox, "manifest.md"), "w", encoding="utf-8") as fh:
            fh.write(HAPPY_MANIFEST)
        before = tree_hashes(self.sandbox)
        proc = self._run_wrapper("manifest=manifest.md")
        self.assertEqual(proc.returncode, 4, proc.stdout + proc.stderr)
        self.assertIn("push preflight failed", proc.stderr)
        # closure.py never started: nothing written, nothing committed
        self.assertEqual(before, tree_hashes(self.sandbox))
        self.assertEqual(commit_count(self.sandbox), 1)

    # ------------------------------------- REGISTRY sprint line

    # No allocations/worklist ops: the sprint line is the ONLY registry change,
    # so the family counters can be asserted byte-identical (one-variable series).
    SPRINT_LINE_MANIFEST = """---
sprint: 108
next_sprint: 109
next_front: "Sprint-Zeilen-Probe"
date: 2026-07-18
sprint_slug: test-closure
---

## Sprint

# Sprint 108 — Sprint-Zeilen-Probe

Minimalnarrativ.

## STARTER Erwartung

- **Erwartet:** clean.

## STARTER Arbeitsauftrag

- **Nächste Aufgabe:** CHORE-138.
"""

    SPRINT_ROW_TAIL = "(F-0076-Regel) | 107 |"  # fixture row value = sprint - 1

    def _edit_registry(self, old, new, commit_msg):
        """Mutate the sandbox REGISTRY (never the fixture) and commit, so the
        baseline stays clean and failed runs can assert 'nothing committed'."""
        path = os.path.join(self.sandbox, "chat-context/REGISTRY.md")
        with open(path, encoding="utf-8") as fh:
            content = fh.read()
        self.assertIn(old, content, "registry mutation anchor missing")
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(content.replace(old, new))
        run(self.sandbox, "git", "commit", "-aqm", commit_msg)

    def _registry_sprint_value(self):
        registry = read(self.sandbox, "chat-context/REGISTRY.md")
        line = next(l for l in registry.splitlines() if l.startswith("| Sprint |"))
        return line.rstrip().rstrip("|").rsplit("|", 1)[1].strip()

    FAMILY_COUNTER_CELLS = ("| FEAT-59 |", "| CHORE-184 |", "| BUG-25 |",
                            "| ADR-0038 |", "| F-0180 |")

    def test_sprint_line_happy_advanced_to_sprint_plus_one(self):
        """Fixture row at N-1 (107), manifest sprint N=108 → row lands on N+1."""
        proc = run_closure(self.sandbox, self.SPRINT_LINE_MANIFEST)
        self.assertEqual(proc.returncode, 0, proc.stderr + proc.stdout)
        self.assertEqual(self._registry_sprint_value(), "109")
        # ID-family counter rows untouched
        registry = read(self.sandbox, "chat-context/REGISTRY.md")
        for cell in self.FAMILY_COUNTER_CELLS:
            self.assertIn(cell, registry, f"family counter changed: {cell}")
        # the change is part of the closure commit
        self.assertEqual(commit_count(self.sandbox), 2)
        shown = run(self.sandbox, "git", "show", "HEAD", "--",
                    "chat-context/REGISTRY.md").stdout
        self.assertIn("+| Sprint |", shown)
        self.assertIn("| 109 |", shown)

    def test_sprint_line_lag_overtaken_not_incremented(self):
        """Row lagging at N-2 (the real transcript case) is overtaken to N+1,
        not merely bumped by one."""
        self._edit_registry(self.SPRINT_ROW_TAIL, "(F-0076-Regel) | 106 |",
                            "sprint row lags at 106")
        proc = run_closure(self.sandbox, self.SPRINT_LINE_MANIFEST)
        self.assertEqual(proc.returncode, 0, proc.stderr + proc.stdout)
        self.assertEqual(self._registry_sprint_value(), "109")

    def test_sprint_line_monotonic_never_regresses(self):
        self._edit_registry(self.SPRINT_ROW_TAIL, "(F-0076-Regel) | 113 |",
                            "sprint row already ahead at 113")
        proc = run_closure(self.sandbox, self.SPRINT_LINE_MANIFEST)
        self.assertEqual(proc.returncode, 0, proc.stderr + proc.stdout)
        self.assertEqual(self._registry_sprint_value(), "113")

    def test_sprint_line_missing_fails_exit2(self):
        """NULL probe: no findable Sprint row → exit 2, nothing written."""
        registry = read(self.sandbox, "chat-context/REGISTRY.md")
        sprint_row = next(l for l in registry.splitlines(keepends=True)
                          if l.startswith("| Sprint |"))
        self._edit_registry(sprint_row, "", "drop sprint row")
        before = tree_hashes(self.sandbox)
        proc = run_closure(self.sandbox, self.SPRINT_LINE_MANIFEST)
        self.assertEqual(proc.returncode, 2, proc.stdout + proc.stderr)
        self.assertIn("Sprint-Zeile nicht eindeutig", proc.stderr)
        self.assertEqual(before, tree_hashes(self.sandbox), "must write nothing")
        self.assertEqual(commit_count(self.sandbox), 2)  # only the mutation commit

    def test_sprint_line_ambiguous_fails_exit2(self):
        """NULL probe 2: duplicated Sprint row → exit 2, nothing written (the
        script must not guess which row to hit)."""
        registry = read(self.sandbox, "chat-context/REGISTRY.md")
        sprint_row = next(l for l in registry.splitlines(keepends=True)
                          if l.startswith("| Sprint |"))
        self._edit_registry(sprint_row, sprint_row + sprint_row, "duplicate sprint row")
        before = tree_hashes(self.sandbox)
        proc = run_closure(self.sandbox, self.SPRINT_LINE_MANIFEST)
        self.assertEqual(proc.returncode, 2, proc.stdout + proc.stderr)
        self.assertIn("Sprint-Zeile nicht eindeutig", proc.stderr)
        self.assertEqual(before, tree_hashes(self.sandbox), "must write nothing")
        self.assertEqual(commit_count(self.sandbox), 2)

    def test_sprint_line_dry_run_previews_change(self):
        before = tree_hashes(self.sandbox)
        proc = run_closure(self.sandbox, self.SPRINT_LINE_MANIFEST, "--dry-run")
        self.assertEqual(proc.returncode, 0, proc.stderr + proc.stdout)
        self.assertIn("b/chat-context/REGISTRY.md", proc.stdout)
        self.assertIn("+| Sprint |", proc.stdout)
        self.assertIn("| 109 |", proc.stdout)
        self.assertEqual(before, tree_hashes(self.sandbox))
        self.assertEqual(commit_count(self.sandbox), 1)
        self.assertEqual(self._registry_sprint_value(), "107", "dry run must not write")

    # ------------------------------------------------------------- frozen git

    def test_frozen_git_state_in_starter_fails_red(self):
        broken = HAPPY_MANIFEST.replace(
            "- **Erwartet:** Superrepo `main` synchron, working tree clean.",
            "- **Erwartet:** Superrepo auf c3e7f35a synchron, 2 commits ahead.")
        proc = run_closure(self.sandbox, broken)
        self.assertEqual(proc.returncode, 3, proc.stdout + proc.stderr)
        self.assertIn("Eingefrorener Git-Zustand", proc.stderr)
        self.assertEqual(commit_count(self.sandbox), 1)

    # ---------------------------- robust, LLM-free git phase

    SUB_IDENT = (("user.email", "closure-test@example.invalid"),
                 ("user.name", "closure-test"), ("commit.gpgsign", "false"))

    def _add_submodule(self, name):
        """Register a real submodule in the sandbox superrepo: seed repo with an
        initial commit on main, its own bare origin, a clone inside the sandbox
        plus .gitmodules entry + gitlink, committed and pushed."""
        bare = tempfile.mkdtemp(prefix=f"closure-sub-{name}-origin-")
        seed = tempfile.mkdtemp(prefix=f"closure-sub-{name}-seed-")
        self.addCleanup(shutil.rmtree, bare, ignore_errors=True)
        self.addCleanup(shutil.rmtree, seed, ignore_errors=True)
        run(bare, "git", "init", "-q", "--bare", "-b", "main")
        run(seed, "git", "init", "-q", "-b", "main")
        for key, val in self.SUB_IDENT:
            run(seed, "git", "config", key, val)
        with open(os.path.join(seed, "README.md"), "w", encoding="utf-8") as fh:
            fh.write(f"{name} seed\n")
        run(seed, "git", "add", "-A")
        run(seed, "git", "commit", "-qm", "seed")
        run(seed, "git", "remote", "add", "origin", bare)
        run(seed, "git", "push", "-q", "-u", "origin", "main")
        sub = os.path.join(self.sandbox, name)
        run(self.sandbox, "git", "clone", "-q", bare, name)
        for key, val in self.SUB_IDENT:
            run(sub, "git", "config", key, val)
        with open(os.path.join(self.sandbox, ".gitmodules"), "a", encoding="utf-8") as fh:
            fh.write(f'[submodule "{name}"]\n\tpath = {name}\n\turl = {bare}\n')
        run(self.sandbox, "git", "add", ".gitmodules", name)
        run(self.sandbox, "git", "commit", "-qm", f"add submodule {name}")
        run(self.sandbox, "git", "push", "-q", "origin", "main")
        return sub, bare

    def _sub_head(self, sub):
        return run(sub, "git", "rev-parse", "HEAD").stdout.strip()

    def _gitlink(self, name):
        """Submodule pointer recorded in the superrepo HEAD commit."""
        out = run(self.sandbox, "git", "ls-tree", "HEAD", name).stdout.strip()
        return out.split()[2]

    def test_git_sync_pulls_feature_checkout_and_merged_main(self):
        """Happy Sync: one impl submodule stuck on feature/x whose work is merged
        on the remote main, one clean on main -> after the run both are clean on
        main and the pointer bump rides the pushed superrepo commit."""
        sub_a, _ = self._add_submodule("server-a")
        sub_b, _ = self._add_submodule("server-b")
        run(sub_a, "git", "checkout", "-q", "-b", "feature/x")
        with open(os.path.join(sub_a, "impl.txt"), "w", encoding="utf-8") as fh:
            fh.write("merged via PR\n")
        run(sub_a, "git", "add", "-A")
        run(sub_a, "git", "commit", "-qm", "feature work")
        run(sub_a, "git", "push", "-q", "origin", "feature/x:main")  # the merged PR
        merged = self._sub_head(sub_a)
        proc = run_closure(self.sandbox, self.SPRINT_LINE_MANIFEST)
        self.assertEqual(proc.returncode, 0, proc.stderr + proc.stdout)
        for sub in (sub_a, sub_b):
            self.assertEqual(run(sub, "git", "branch", "--show-current").stdout.strip(),
                             "main")
            self.assertEqual(run(sub, "git", "status", "--porcelain").stdout.strip(), "")
        self.assertEqual(self._sub_head(sub_a), merged)
        self.assertEqual(self._gitlink("server-a"), merged, "pointer not bumped")
        local = run(self.sandbox, "git", "rev-parse", "main").stdout.strip()
        remote = run(self.origin, "git", "rev-parse", "main").stdout.strip()
        self.assertEqual(local, remote, "superrepo push did not land on origin")

    def test_git_spec_dirty_committed_direct_main(self):
        spec, spec_bare = self._add_submodule("spec")
        with open(os.path.join(spec, "neue-doku.md"), "w", encoding="utf-8") as fh:
            fh.write("Spec-Doku — em-dash und Umlaute äöü\n")
        proc = run_closure(self.sandbox, self.SPRINT_LINE_MANIFEST)
        self.assertEqual(proc.returncode, 0, proc.stderr + proc.stdout)
        spec_sha = self._sub_head(spec)
        self.assertEqual(run(spec, "git", "log", "-1", "--format=%s").stdout.strip(),
                         "Sprint 108 closure: test-closure")  # generated message
        self.assertEqual(run(spec, "git", "status", "--porcelain").stdout.strip(), "")
        self.assertEqual(run(spec_bare, "git", "rev-parse", "main").stdout.strip(),
                         spec_sha, "spec push did not land on its origin")
        self.assertEqual(self._gitlink("spec"), spec_sha, "spec pointer not bumped")
        self.assertIn(f"(spec: {spec_sha})", proc.stdout, "spec sha not reported")

    def test_git_commit_message_field_applies_to_all_commits(self):
        spec, _ = self._add_submodule("spec")
        with open(os.path.join(spec, "neue-doku.md"), "w", encoding="utf-8") as fh:
            fh.write("doc\n")
        manifest = self.SPRINT_LINE_MANIFEST.replace(
            "sprint_slug: test-closure\n",
            'sprint_slug: test-closure\n'
            'commit_message: "Closure #108 — Sonderfall, gequotet"\n')
        proc = run_closure(self.sandbox, manifest)
        self.assertEqual(proc.returncode, 0, proc.stderr + proc.stdout)
        self.assertEqual(run(spec, "git", "log", "-1", "--format=%s").stdout.strip(),
                         "Closure #108 — Sonderfall, gequotet")
        self.assertEqual(run(self.sandbox, "git", "log", "-1", "--format=%s").stdout.strip(),
                         "Closure #108 — Sonderfall, gequotet")

    def test_null_probe_impl_submodule_dirty_fails_red(self):
        """The core gate: 'commit everything dirty' must stop at a non-whitelisted
        submodule — operator precondition (PR merged) violated."""
        sub, _ = self._add_submodule("server-a")
        with open(os.path.join(sub, "README.md"), "a", encoding="utf-8") as fh:
            fh.write("uncommitted work\n")
        before = tree_hashes(self.sandbox)
        base = commit_count(self.sandbox)
        proc = run_closure(self.sandbox, self.SPRINT_LINE_MANIFEST)
        self.assertEqual(proc.returncode, 4, proc.stdout + proc.stderr)
        self.assertIn("server-a", proc.stderr)
        self.assertIn("direct-main", proc.stderr)
        self.assertEqual(before, tree_hashes(self.sandbox), "nothing may be written")
        self.assertEqual(commit_count(self.sandbox), base, "nothing may be committed")
        self.assertEqual(run(sub, "git", "rev-list", "--count", "HEAD").stdout.strip(),
                         "1", "submodule must not be committed either")
        self.assertIn("uncommitted work", read(self.sandbox, "server-a/README.md"))

    def test_null_probe_impl_submodule_ahead_fails_red(self):
        sub, bare = self._add_submodule("server-a")
        with open(os.path.join(sub, "local.txt"), "w", encoding="utf-8") as fh:
            fh.write("local only\n")
        run(sub, "git", "add", "-A")
        run(sub, "git", "commit", "-qm", "local unpushed commit")
        local = self._sub_head(sub)
        base = commit_count(self.sandbox)
        proc = run_closure(self.sandbox, self.SPRINT_LINE_MANIFEST)
        self.assertEqual(proc.returncode, 4, proc.stdout + proc.stderr)
        self.assertIn("server-a", proc.stderr)
        self.assertIn("ahead", proc.stderr)
        self.assertEqual(commit_count(self.sandbox), base)
        self.assertEqual(self._sub_head(sub), local, "local commit must survive")
        self.assertNotEqual(run(bare, "git", "rev-parse", "main").stdout.strip(),
                            local, "unpushed impl commit must never be pushed")

    def test_null_probe_blocked_checkout_fails_red_without_force(self):
        sub, _ = self._add_submodule("server-a")
        run(sub, "git", "checkout", "-q", "-b", "feature/x")
        with open(os.path.join(sub, "README.md"), "w", encoding="utf-8") as fh:
            fh.write("feature version\n")
        run(sub, "git", "add", "-A")
        run(sub, "git", "commit", "-qm", "feature rewrites README")
        with open(os.path.join(sub, "README.md"), "w", encoding="utf-8") as fh:
            fh.write("local edit, not committed\n")
        before = tree_hashes(self.sandbox)
        base = commit_count(self.sandbox)
        proc = run_closure(self.sandbox, self.SPRINT_LINE_MANIFEST)
        self.assertEqual(proc.returncode, 4, proc.stdout + proc.stderr)
        self.assertIn("server-a", proc.stderr)
        self.assertIn("checkout main", proc.stderr)
        self.assertEqual(read(self.sandbox, "server-a/README.md"),
                         "local edit, not committed\n",
                         "no --force — nothing may be lost")
        self.assertEqual(run(sub, "git", "branch", "--show-current").stdout.strip(),
                         "feature/x")
        self.assertEqual(before, tree_hashes(self.sandbox))
        self.assertEqual(commit_count(self.sandbox), base)

    def test_null_probe_non_ff_pull_fails_red(self):
        sub, bare = self._add_submodule("server-a")
        # remote main advances independently (via a second clone)
        other = tempfile.mkdtemp(prefix="closure-sub-other-")
        self.addCleanup(shutil.rmtree, other, ignore_errors=True)
        run(self.sandbox, "git", "clone", "-q", bare, other)
        for key, val in self.SUB_IDENT:
            run(other, "git", "config", key, val)
        with open(os.path.join(other, "remote.txt"), "w", encoding="utf-8") as fh:
            fh.write("remote work\n")
        run(other, "git", "add", "-A")
        run(other, "git", "commit", "-qm", "remote main advances")
        run(other, "git", "push", "-q", "origin", "main")
        # local main diverges
        with open(os.path.join(sub, "local.txt"), "w", encoding="utf-8") as fh:
            fh.write("diverging local work\n")
        run(sub, "git", "add", "-A")
        run(sub, "git", "commit", "-qm", "local main diverges")
        local = self._sub_head(sub)
        base = commit_count(self.sandbox)
        proc = run_closure(self.sandbox, self.SPRINT_LINE_MANIFEST)
        self.assertEqual(proc.returncode, 4, proc.stdout + proc.stderr)
        self.assertIn("server-a", proc.stderr)
        self.assertIn("ff-only", proc.stderr)
        self.assertEqual(self._sub_head(sub), local, "no merge/rebase — HEAD untouched")
        self.assertEqual(run(sub, "git", "rev-list", "--count", "--merges",
                             "HEAD").stdout.strip(), "0")
        self.assertEqual(commit_count(self.sandbox), base)

    def test_null_probe_preflight_spec_target_unreachable(self):
        """Preflight covers ALL push targets: a dead spec origin refuses the run
        BEFORE any mutation — even the submodule sync has not run yet."""
        _, spec_bare = self._add_submodule("spec")
        sub, _ = self._add_submodule("server-a")
        run(sub, "git", "checkout", "-q", "-b", "feature/x")  # marker: sync must not run
        shutil.rmtree(spec_bare)
        before = tree_hashes(self.sandbox)
        base = commit_count(self.sandbox)
        proc = run_closure(self.sandbox, self.SPRINT_LINE_MANIFEST)
        self.assertEqual(proc.returncode, 4, proc.stdout + proc.stderr)
        self.assertIn("Push-Preflight", proc.stderr)
        self.assertIn("spec", proc.stderr)
        self.assertEqual(before, tree_hashes(self.sandbox), "no mutation on failed preflight")
        self.assertEqual(commit_count(self.sandbox), base)
        self.assertEqual(run(sub, "git", "branch", "--show-current").stdout.strip(),
                         "feature/x", "sync must not have run")
        # dry_run skips the preflight entirely (offline preview)
        proc2 = run_closure(self.sandbox, self.SPRINT_LINE_MANIFEST, "--dry-run")
        self.assertEqual(proc2.returncode, 0, proc2.stderr + proc2.stdout)
        self.assertIn("ok (dry-run)", proc2.stdout)

    def test_null_probe_preflight_superrepo_target_unreachable(self):
        run(self.sandbox, "git", "remote", "remove", "origin")
        before = tree_hashes(self.sandbox)
        base = commit_count(self.sandbox)
        proc = run_closure(self.sandbox, self.SPRINT_LINE_MANIFEST)
        self.assertEqual(proc.returncode, 4, proc.stdout + proc.stderr)
        self.assertIn("Push-Preflight Superrepo", proc.stderr)
        self.assertEqual(before, tree_hashes(self.sandbox))
        self.assertEqual(commit_count(self.sandbox), base)

    def test_add_a_captures_unexpected_working_tree_file(self):
        """Deliberate price of add -A, fixed as behaviour: an unexpected file in
        the superrepo working tree rides the closure commit — git is the central
        backup, nothing is selectively left out."""
        with open(os.path.join(self.sandbox, "unerwartete-notiz.md"), "w",
                  encoding="utf-8") as fh:
            fh.write("unklare Provenienz\n")
        proc = run_closure(self.sandbox, self.SPRINT_LINE_MANIFEST)
        self.assertEqual(proc.returncode, 0, proc.stderr + proc.stdout)
        shown = run(self.sandbox, "git", "show", "--stat", "--format=", "HEAD").stdout
        self.assertIn("unerwartete-notiz.md", shown)
        self.assertIn("manifest.md", shown)  # same rule applies to the manifest

    def test_decorator_preflight_covers_spec_target(self):
        self._install_wrapper()
        _, spec_bare = self._add_submodule("spec")
        shutil.rmtree(spec_bare)
        with open(os.path.join(self.sandbox, "manifest.md"), "w", encoding="utf-8") as fh:
            fh.write(HAPPY_MANIFEST)
        before = tree_hashes(self.sandbox)
        proc = self._run_wrapper("manifest=manifest.md")
        self.assertEqual(proc.returncode, 4, proc.stdout + proc.stderr)
        self.assertIn("push preflight failed for 'spec'", proc.stderr)
        self.assertEqual(before, tree_hashes(self.sandbox), "closure.py never started")


if __name__ == "__main__":
    unittest.main()
