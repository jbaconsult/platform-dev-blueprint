#!/usr/bin/env python3
"""closure.py — manifest-driven session-closure executor for the platform-dev superrepo.

Executes the mechanical part of a session closure (see skills/session-closure/SKILL.md): findings, sprint file, WORKLIST/STARTER/ARCHIVE consolidation
(three-file model), REGISTRY reconciliation (ID counters + sprint-line advance), handover frontmatter flips, STARTER rewrite
from the template — then checks a fail-closed set of definition-of-done assertions and,
only if every assertion is green, commits and pushes the superrepo.

Usage:
    python scripts/closure.py <manifest.md> [--dry-run]

Run with cwd = workspace root (the superrepo checkout). The manifest is one Markdown
file: YAML frontmatter (structured decisions) + named "##" prose sections (narratives).
The contract is ratified — this script parses exactly that schema and fails loud on
anything else.

Behaviour:
  * All changes are computed in-memory first (a file overlay). Nothing touches disk
    until every assertion is green.
  * --dry-run: print all planned changes as unified diffs plus the planned git block;
    exit 0 only if all assertions would pass. Never writes, never runs git at all
    (offline-capable preview — the git phase is skipped entirely).
  * Real run — the dumb-uniform git phase (no state analysis):
      1. push preflight (git push --dry-run origin main) against EVERY push target
         — the superrepo AND each whitelisted submodule — before any mutation;
      2. every submodule: git checkout main + git pull --ff-only origin main
         (never --force, never merge/rebase — any deviation fails loud);
      3. whitelist gate: a submodule that is dirty or ahead after the sync may only
         be committed if it is in COMMIT_WHITELIST ({spec}); any implementation
         submodule in that state fails the run closed — un-reviewed code never
         lands direct-main from here, implementation changes go through PRs;
      4. write files, read each back from disk (byte compare — a success message
         is not proof), then commit whitelisted submodules (add -A + commit +
         push, direct to main) and finally the superrepo: git add -A (EVERYTHING
         in the working tree incl. all pointer bumps — deliberate, git is the
         central backup) + commit + push origin main.

Exit codes:
    0   ok (real run prints "ok <superrepo-sha>" plus "(spec: <sha>)" if a
        whitelisted submodule was pushed; dry run prints "ok (dry-run)")
    1   usage / unexpected I/O error
    2   manifest schema violation (nothing written)
    3   definition-of-done assertion broken (fail-closed: nothing committed;
        in a real run nothing is written either — assertions run pre-write)
    4   git phase blocked or failed (push preflight, blocked checkout, non-ff
        pull, non-whitelisted submodule dirty/ahead, push error)

Messages addressed to the operator/Concept session are German (chat-context layer);
code and comments are English per WORKING_CONCEPT §13.
"""

import difflib
import os
import re
import subprocess
import sys
import unicodedata

EXIT_OK = 0
EXIT_USAGE = 1
EXIT_SCHEMA = 2
EXIT_ASSERT = 3
EXIT_GIT = 4

# Instance configuration: the project name prefixes the STARTER title
# ("<PROJECT_NAME> Sprint #N — <front>"). Two more instance-defined constants
# live below: CLUSTERS (manifest marker vocabulary — keep in sync with the
# worklist-manager skill and the WORKLIST header) and COMMIT_WHITELIST (the
# submodules the closure may commit direct-to-main). Edit all three when
# deriving an instance.
PROJECT_NAME = "example-project"


class ClosureError(Exception):
    def __init__(self, exit_code, message):
        super().__init__(message)
        self.exit_code = exit_code


def schema_fail(msg):
    raise ClosureError(EXIT_SCHEMA, f"MANIFEST-SCHEMA: {msg}")


def assert_fail(msg):
    raise ClosureError(EXIT_ASSERT, f"ASSERTION: {msg}")


def git_fail(msg):
    raise ClosureError(EXIT_GIT, f"GIT: {msg}")


# ---------------------------------------------------------------------------
# Mini-YAML parser — supports exactly the ratified manifest frontmatter subset:
# scalars, nested block mappings, block sequences of scalars / flow mappings /
# flow sequences / block mappings. Anything beyond that fails loud (no silent
# best-effort parse). PyYAML deliberately not required (stdlib-only script).
# ---------------------------------------------------------------------------

def _strip_comment(line):
    """Remove a trailing YAML comment (a '#' preceded by whitespace or at col 0),
    respecting single/double quotes."""
    out = []
    in_s = in_d = False
    prev = ""
    for ch in line:
        if ch == "'" and not in_d:
            in_s = not in_s
        elif ch == '"' and not in_s and prev != "\\":
            in_d = not in_d
        elif ch == "#" and not in_s and not in_d and (prev == "" or prev in " \t"):
            break
        out.append(ch)
        prev = ch
    return "".join(out).rstrip()


def _parse_scalar(tok):
    tok = tok.strip()
    if len(tok) >= 2 and tok[0] == tok[-1] == '"':
        return tok[1:-1].replace('\\"', '"').replace("\\\\", "\\")
    if len(tok) >= 2 and tok[0] == tok[-1] == "'":
        return tok[1:-1].replace("''", "'")
    if tok in ("null", "~", ""):
        return None
    if tok in ("true", "True"):
        return True
    if tok in ("false", "False"):
        return False
    if re.fullmatch(r"-?\d+", tok):
        return int(tok)
    return tok


def _split_flow(body):
    """Split a flow collection body on top-level commas (quote/bracket aware)."""
    parts, buf = [], []
    depth = 0
    in_s = in_d = False
    prev = ""
    for ch in body:
        if ch == "'" and not in_d:
            in_s = not in_s
        elif ch == '"' and not in_s and prev != "\\":
            in_d = not in_d
        elif not in_s and not in_d:
            if ch in "[{":
                depth += 1
            elif ch in "]}":
                depth -= 1
            elif ch == "," and depth == 0:
                parts.append("".join(buf))
                buf = []
                prev = ch
                continue
        buf.append(ch)
        prev = ch
    if "".join(buf).strip():
        parts.append("".join(buf))
    return parts


def _parse_flow(tok, where):
    tok = tok.strip()
    if tok.startswith("{") and tok.endswith("}"):
        out = {}
        for part in _split_flow(tok[1:-1]):
            if ":" not in part:
                schema_fail(f"Flow-Mapping-Eintrag ohne ':' in {where}: {part!r}")
            k, v = part.split(":", 1)
            out[k.strip()] = _parse_flow(v, where)
        return out
    if tok.startswith("[") and tok.endswith("]"):
        return [_parse_flow(p, where) for p in _split_flow(tok[1:-1])]
    return _parse_scalar(tok)


def parse_mini_yaml(text):
    """Parse the manifest frontmatter subset. Returns a dict."""
    lines = []
    for raw in text.splitlines():
        stripped = _strip_comment(raw)
        if stripped.strip() == "":
            continue
        indent = len(raw) - len(raw.lstrip(" "))
        lines.append((indent, stripped.strip(), raw))

    pos = [0]

    def parse_block(min_indent):
        # Decide by first line whether this block is a mapping or a sequence.
        if pos[0] >= len(lines):
            return {}
        first_indent = lines[pos[0]][0]
        if first_indent < min_indent:
            return {}
        if lines[pos[0]][1].startswith("- "):
            return parse_sequence(first_indent)
        return parse_mapping(first_indent)

    def parse_mapping(indent):
        out = {}
        while pos[0] < len(lines):
            ind, content, raw = lines[pos[0]]
            if ind < indent:
                break
            if ind > indent or content.startswith("- "):
                schema_fail(f"unerwartete Einrückung/Sequenz in Frontmatter-Zeile: {raw!r}")
            if ":" not in content:
                schema_fail(f"Frontmatter-Zeile ohne ':': {raw!r}")
            key, rest = content.split(":", 1)
            key = key.strip()
            rest = rest.strip()
            pos[0] += 1
            if rest == "":
                # nested block (mapping or sequence) or empty value
                if pos[0] < len(lines) and lines[pos[0]][0] > indent:
                    out[key] = parse_block(indent + 1)
                elif pos[0] < len(lines) and lines[pos[0]][0] == indent and lines[pos[0]][1].startswith("- "):
                    out[key] = parse_sequence(indent)
                else:
                    out[key] = None
            elif rest.startswith(("{", "[")):
                out[key] = _parse_flow(rest, f"Key '{key}'")
            else:
                out[key] = _parse_scalar(rest)
        return out

    def parse_sequence(indent):
        out = []
        while pos[0] < len(lines):
            ind, content, raw = lines[pos[0]]
            if ind < indent or not content.startswith("- "):
                break
            item = content[2:].strip()
            pos[0] += 1
            if item == "":
                out.append(parse_block(indent + 1))
            elif item.startswith(("{", "[")):
                out.append(_parse_flow(item, "Sequenz-Eintrag"))
            elif ":" in item and not item.startswith(("'", '"')):
                # block mapping written inline after the dash:  - category: x
                key, rest = item.split(":", 1)
                entry = {key.strip(): _parse_scalar(rest)}
                # continuation lines are indented deeper than the dash
                while pos[0] < len(lines) and lines[pos[0]][0] > indent:
                    ind2, content2, raw2 = lines[pos[0]]
                    if content2.startswith("- ") or ":" not in content2:
                        schema_fail(f"unerwartete Zeile in Listen-Mapping: {raw2!r}")
                    k2, r2 = content2.split(":", 1)
                    r2 = r2.strip()
                    pos[0] += 1
                    if r2.startswith(("{", "[")):
                        entry[k2.strip()] = _parse_flow(r2, f"Key '{k2.strip()}'")
                    else:
                        entry[k2.strip()] = _parse_scalar(r2)
                out.append(entry)
            else:
                out.append(_parse_scalar(item))
        return out

    result = parse_mapping(lines[0][0] if lines else 0)
    if pos[0] != len(lines):
        schema_fail(f"Frontmatter ab Zeile nicht parsebar: {lines[pos[0]][2]!r}")
    return result


# ---------------------------------------------------------------------------
# Manifest parsing & validation
# ---------------------------------------------------------------------------

CLUSTERS = {"LAUNCH": "🚀 LAUNCH", "DEPLOY": "🔧 DEPLOY", "SEC": "🔒 SEC", "CORE": "🧠 CORE",
            "CONN": "🔌 CONN", "GTM": "📣 GTM", "EE": "💎 EE", "HK": "🧹 HK"}
PRIOS = {"P1": "🔴 P1", "P2": "🟠 P2", "P3": "🔵 P3"}
SIZES = {"S": "🌑 S", "M": "🌓 M", "L": "🌕 L"}
STATUSES = {"todo": "⬜ todo", "in-progress": "🔄 in-progress", "needs-review": "👀 needs-review",
            "deferred": "💤 deferred", "partial": "🚧 partial"}
TYPES = ("feature", "bugfix", "chore", "test")
TYPE_PREFIX = {"feature": "FEAT", "chore": "CHORE", "bugfix": "BUG", "test": "BUG"}
DISPS = ("C", "D", "—")
SEVERITIES = ("low", "medium", "high")

TASK_FIELDS = ("cluster", "titel", "komp", "typ", "prio", "groesse", "disp", "status", "ref")


def _canon_marker(value, table, what):
    value = str(value).strip()
    if value in table.values():
        return value
    if value in table:
        return table[value]
    schema_fail(f"{what} nicht im Marker-Vokabular: {value!r} (erlaubt: {sorted(table)} bzw. Marker-Form)")


def canon_task(entry, where):
    if not isinstance(entry, dict):
        schema_fail(f"{where}: Eintrag ist kein Mapping: {entry!r}")
    missing = [f for f in TASK_FIELDS if f not in entry or entry[f] in (None, "")]
    if missing:
        schema_fail(f"{where}: fehlende Felder {missing}")
    t = {k: str(entry[k]).strip() for k in TASK_FIELDS}
    t["cluster"] = _canon_marker(t["cluster"], CLUSTERS, f"{where}.cluster")
    t["prio"] = _canon_marker(t["prio"], PRIOS, f"{where}.prio")
    t["groesse"] = _canon_marker(t["groesse"], SIZES, f"{where}.groesse")
    t["status"] = _canon_marker(t["status"], STATUSES, f"{where}.status")
    if t["typ"] not in TYPES:
        schema_fail(f"{where}.typ nicht in {TYPES}: {t['typ']!r}")
    if t["disp"] == "-":
        t["disp"] = "—"
    if t["disp"] not in DISPS:
        schema_fail(f"{where}.disp nicht in {DISPS}: {t['disp']!r}")
    if len(t["titel"]) > 150:
        schema_fail(f"{where}.titel länger als 150 Zeichen ({len(t['titel'])})")
    return t


def split_frontmatter(text, what):
    if not text.startswith("---"):
        schema_fail(f"{what}: kein YAML-Frontmatter am Dateianfang")
    m = re.match(r"^---\s*\n(.*?)\n---\s*\n?", text, re.DOTALL)
    if not m:
        schema_fail(f"{what}: Frontmatter nicht abgeschlossen (kein zweites '---')")
    return m.group(1), text[m.end():]


MANIFEST_SECTIONS = ("Sprint", "STARTER Erwartung", "STARTER Arbeitsauftrag",
                     "STARTER Code-Interface", "Achievements")


def _is_manifest_heading(name):
    return name in MANIFEST_SECTIONS or name.startswith("Finding: ")


def parse_prose_sections(body):
    """Split the manifest body into {'<H2 title>': '<content>'}. Only the contract's
    named sections are boundaries — any other '## ' line (e.g. '## Wo wir standen'
    inside the sprint narrative) belongs to the current block verbatim."""
    sections = {}
    current = None
    buf = []
    for line in body.splitlines(keepends=True):
        if line.startswith("## ") and _is_manifest_heading(line[3:].strip()):
            if current is not None:
                sections[current] = "".join(buf).strip("\n")
            current = line[3:].strip()
            buf = []
        elif current is not None:
            buf.append(line)
    if current is not None:
        sections[current] = "".join(buf).strip("\n")
    return sections


def load_manifest(path):
    try:
        with open(path, encoding="utf-8") as fh:
            text = fh.read()
    except OSError as exc:
        raise ClosureError(EXIT_USAGE, f"Manifest nicht lesbar: {exc}")
    fm_text, body = split_frontmatter(text, "Manifest")
    fm = parse_mini_yaml(fm_text)
    prose = parse_prose_sections(body)

    for key in ("sprint", "next_sprint", "next_front", "date", "sprint_slug"):
        if key not in fm or fm[key] in (None, ""):
            schema_fail(f"Pflichtfeld fehlt im Frontmatter: {key}")
    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", str(fm["date"])):
        schema_fail(f"date ist kein YYYY-MM-DD: {fm['date']!r}")
    if not re.fullmatch(r"[a-z0-9]+(-[a-z0-9]+)*", str(fm["sprint_slug"])):
        schema_fail(f"sprint_slug ist kein kebab-case-Slug: {fm['sprint_slug']!r}")

    manifest = {
        "sprint": int(fm["sprint"]),
        "next_sprint": int(fm["next_sprint"]),
        "next_front": str(fm["next_front"]),
        "date": str(fm["date"]),
        "sprint_slug": str(fm["sprint_slug"]),
        "commit_message": None,
        "tracks": None,
        "ratified": None,
        "findings": [],
        "worklist": {"add_to_backlog": [], "add_to_queue": [], "promote": [],
                     "archive": [], "reposition": None, "clear_new_tasks": False},
        "handover": [],
        "prose": prose,
    }

    # Optional commit message, applied to ALL commits of the run
    # (whitelisted submodules + superrepo); absent -> generated (unchanged form)
    cm = fm.get("commit_message")
    if cm is not None:
        if not isinstance(cm, str) or not cm.strip():
            schema_fail(f"commit_message ist kein nicht-leerer String: {cm!r}")
        manifest["commit_message"] = cm

    # E1: optional verbatim sprint-frontmatter lists
    for key in ("tracks", "ratified"):
        val = fm.get(key)
        if val is None:
            continue
        if not isinstance(val, list) or not all(isinstance(x, (str, int)) for x in val):
            schema_fail(f"{key} ist keine Liste von Skalaren: {val!r}")
        manifest[key] = [str(x) for x in val]

    for i, f in enumerate(fm.get("findings") or []):
        if not isinstance(f, dict):
            schema_fail(f"findings[{i}] ist kein Mapping")
        for key in ("category", "severity", "component", "slug"):
            if key not in f or f[key] in (None, ""):
                schema_fail(f"findings[{i}]: Feld fehlt: {key}")
        if str(f["severity"]) not in SEVERITIES:
            schema_fail(f"findings[{i}].severity nicht in {SEVERITIES}: {f['severity']!r}")
        slug = str(f["slug"])
        if f"Finding: {slug}" not in prose:
            schema_fail(f"Prosa-Sektion '## Finding: {slug}' fehlt für findings[{i}]")
        manifest["findings"].append({k: str(f[k]) for k in ("category", "severity", "component", "slug")})

    wl = fm.get("worklist") or {}
    if not isinstance(wl, dict):
        schema_fail("worklist ist kein Mapping")
    handles = set()
    for op in ("add_to_backlog", "add_to_queue"):
        for i, entry in enumerate(wl.get(op) or []):
            task = canon_task(entry, f"worklist.{op}[{i}]")
            # E2: manifest-local handle so reposition can name a
            # queue task whose ID the script only allocates at run time
            handle = entry.get("handle") if isinstance(entry, dict) else None
            if handle is not None:
                if op != "add_to_queue":
                    schema_fail(f"worklist.{op}[{i}]: handle ist nur in add_to_queue erlaubt")
                handle = str(handle)
                if re.fullmatch(r"(FEAT|CHORE|BUG)-\d+", handle):
                    schema_fail(f"worklist.add_to_queue[{i}]: handle {handle!r} sieht aus wie eine echte Task-ID")
                if handle in handles:
                    schema_fail(f"worklist.add_to_queue: handle {handle!r} doppelt definiert")
                handles.add(handle)
            task["handle"] = handle
            manifest["worklist"][op].append(task)

    cnt = wl.get("clear_new_tasks", False)
    if not isinstance(cnt, bool):
        schema_fail(f"worklist.clear_new_tasks muss true/false sein: {cnt!r}")
    manifest["worklist"]["clear_new_tasks"] = cnt
    for i, pid in enumerate(wl.get("promote") or []):
        if not isinstance(pid, str) or not re.fullmatch(r"(FEAT|CHORE|BUG)-\d+", pid):
            schema_fail(f"worklist.promote[{i}] ist keine Task-ID: {pid!r}")
        manifest["worklist"]["promote"].append(pid)
    for i, entry in enumerate(wl.get("archive") or []):
        if not isinstance(entry, dict) or not all(k in entry for k in ("id", "summary", "ref")):
            schema_fail(f"worklist.archive[{i}]: braucht id, summary, ref")
        summary = str(entry["summary"])
        if len(summary) > 200:
            schema_fail(f"worklist.archive[{i}].summary länger als 200 Zeichen ({len(summary)})")
        manifest["worklist"]["archive"].append(
            {"id": str(entry["id"]), "summary": summary, "ref": str(entry["ref"])})
    repo = wl.get("reposition")
    if repo:
        # contract shows a list containing one full ID list; tolerate the flat form
        if isinstance(repo, list) and len(repo) == 1 and isinstance(repo[0], list):
            repo = repo[0]
        if not isinstance(repo, list) or not all(isinstance(x, str) for x in repo):
            schema_fail(f"worklist.reposition ist keine ID-Liste: {repo!r}")
        # E2: every handle must resolve — an undefined reposition handle, or a
        # defined handle that a given reposition never names, is a schema error
        for tok in repo:
            if not re.fullmatch(r"(FEAT|CHORE|BUG)-\d+", tok) and tok not in handles:
                schema_fail(f"worklist.reposition: Handle {tok!r} ist in add_to_queue nicht definiert")
        for h in sorted(handles):
            if h not in repo:
                schema_fail(f"worklist.add_to_queue: Handle {h!r} wird im gesetzten reposition nicht referenziert")
        manifest["worklist"]["reposition"] = repo

    for i, h in enumerate(fm.get("handover") or []):
        if not isinstance(h, dict) or not all(k in h for k in ("dispatch", "return", "status")):
            schema_fail(f"handover[{i}]: braucht dispatch, return, status")
        status = str(h["status"])
        if status not in ("closed", "consumed"):
            schema_fail(f"handover[{i}].status nicht in (closed, consumed): {status!r}")
        curated = h.get("curated_in")
        if status == "consumed" and not curated:
            schema_fail(f"handover[{i}]: status consumed braucht curated_in")
        manifest["handover"].append({"dispatch": str(h["dispatch"]), "return": str(h["return"]),
                                     "status": status,
                                     "curated_in": str(curated) if curated else None})

    for sec in ("Sprint", "STARTER Erwartung", "STARTER Arbeitsauftrag"):
        if sec not in prose or not prose[sec].strip():
            schema_fail(f"Prosa-Sektion '## {sec}' fehlt oder ist leer")
    return manifest


# ---------------------------------------------------------------------------
# File overlay — all mutations in memory until assertions are green
# ---------------------------------------------------------------------------

class FileSet:
    def __init__(self, root):
        self.root = root
        self.overlay = {}       # relpath -> new content
        self.originals = {}     # relpath -> original content or None (new file)

    def abspath(self, rel):
        return os.path.join(self.root, rel)

    def exists(self, rel):
        return rel in self.overlay or os.path.exists(self.abspath(rel))

    def read(self, rel):
        if rel in self.overlay:
            return self.overlay[rel]
        with open(self.abspath(rel), encoding="utf-8") as fh:
            return fh.read()

    def write(self, rel, content):
        if rel not in self.originals:
            if os.path.exists(self.abspath(rel)):
                with open(self.abspath(rel), encoding="utf-8") as fh:
                    self.originals[rel] = fh.read()
            else:
                self.originals[rel] = None
        self.overlay[rel] = content

    def changed(self):
        return {rel: content for rel, content in self.overlay.items()
                if self.originals.get(rel) != content}

    def flush(self):
        """Real run: write to disk, then read back and byte-compare (fail-closed)."""
        for rel, content in self.changed().items():
            path = self.abspath(rel)
            os.makedirs(os.path.dirname(path), exist_ok=True)
            with open(path, "w", encoding="utf-8", newline="") as fh:
                fh.write(content)
        for rel, content in self.changed().items():
            with open(self.abspath(rel), encoding="utf-8") as fh:
                back = fh.read()
            if back != content:
                raise ClosureError(EXIT_ASSERT,
                                   f"READ-BACK: {rel} weicht nach dem Schreiben vom Soll ab — Abbruch vor git")


# ---------------------------------------------------------------------------
# Markdown helpers (sections + pipe tables), row-preserving (UTF-8/emoji safe)
# ---------------------------------------------------------------------------

def find_section(lines, heading_start):
    """Return (start, end) line indices of the section whose '## ' heading starts
    with heading_start; end is exclusive (next '## ' or EOF)."""
    start = None
    for i, line in enumerate(lines):
        if line.startswith("## ") and line[3:].strip().startswith(heading_start):
            start = i
            break
    if start is None:
        return None
    end = len(lines)
    for j in range(start + 1, len(lines)):
        if lines[j].startswith("## "):
            end = j
            break
    return start, end


def find_table(lines, start, end):
    """Find the first pipe table in lines[start:end]. Returns (header_idx, sep_idx,
    row_indices) — row_indices are the data-row line numbers."""
    i = start
    while i < end:
        if lines[i].lstrip().startswith("|") and i + 1 < end and re.match(r"^\s*\|[\s\-|:]+\|\s*$", lines[i + 1]):
            header, sep = i, i + 1
            rows = []
            j = sep + 1
            while j < end and lines[j].lstrip().startswith("|"):
                rows.append(j)
                j += 1
            return header, sep, rows
        i += 1
    return None


def row_cells(line):
    """Split a table row into stripped cells (outer pipes removed). Table cells in
    this corpus never contain escaped pipes."""
    parts = line.strip().strip("|").split("|")
    return [p.strip() for p in parts]


def row_id(line):
    cells = row_cells(line)
    return cells[0] if cells else ""


class Doc:
    """A markdown file as a mutable line list."""

    def __init__(self, files, rel):
        self.files = files
        self.rel = rel
        self.lines = files.read(rel).splitlines(keepends=True)

    def save(self):
        self.files.write(self.rel, "".join(self.lines))

    def section(self, heading_start):
        span = find_section(self.lines, heading_start)
        if span is None:
            schema_fail(f"Sektion '## {heading_start}…' nicht gefunden in {self.rel}")
        return span

    def table_in(self, heading_start):
        start, end = self.section(heading_start)
        tab = find_table(self.lines, start, end)
        if tab is None:
            schema_fail(f"Keine Tabelle in Sektion '## {heading_start}…' von {self.rel}")
        return tab

    def take_row(self, heading_start, task_id):
        """Remove and return the raw row line with the given ID, or None."""
        header, sep, rows = self.table_in(heading_start)
        for idx in rows:
            if row_id(self.lines[idx]) == task_id:
                return self.lines.pop(idx)
        return None

    def append_row(self, heading_start, row_line, at_top=False):
        header, sep, rows = self.table_in(heading_start)
        if not row_line.endswith("\n"):
            row_line += "\n"
        insert_at = sep + 1 if at_top else (rows[-1] + 1 if rows else sep + 1)
        self.lines.insert(insert_at, row_line)

    def table_row_lines(self, heading_start):
        header, sep, rows = self.table_in(heading_start)
        return [self.lines[i] for i in rows]


def make_task_row(task_id, t):
    return (f"| {task_id} | {t['cluster']} | {t['titel']} | {t['komp']} | {t['typ']} | "
            f"{t['prio']} | {t['groesse']} | {t['disp']} | {t['status']} | {t['ref']} |\n")


# ---------------------------------------------------------------------------
# REGISTRY operations
# ---------------------------------------------------------------------------

REGISTRY = "chat-context/REGISTRY.md"
COUNTER_LABEL = {"FEAT": "FEAT", "CHORE": "CHORE", "BUG": "BUG", "F": "F (Finding)"}
FAMILY_SECTION = {"FEAT": "FEAT", "CHORE": "CHORE", "BUG": "BUG", "F": "F (Findings)"}


class Registry:
    def __init__(self, files):
        self.doc = Doc(files, REGISTRY)
        self.allocated = []   # [(id, family)]

    def _counter_row(self, family):
        header, sep, rows = self.doc.table_in("Nächste freie IDs")
        label = COUNTER_LABEL[family]
        for idx in rows:
            if row_cells(self.doc.lines[idx])[0] == label:
                return idx
        schema_fail(f"REGISTRY: Familie {label!r} fehlt in der Nächste-freie-IDs-Tabelle")

    def next_free(self, family):
        idx = self._counter_row(family)
        cell = row_cells(self.doc.lines[idx])[-1]
        m = re.fullmatch(rf"{family}-(\d+)" if family != "F" else r"F-(\d+)", cell)
        if not m:
            schema_fail(f"REGISTRY: Zähler-Zelle unlesbar für {family}: {cell!r}")
        return cell, m.group(1)

    def allocate(self, family, topic, ort):
        """Take the next free ID, bump the counter and add the family row in the
        same in-memory write (register-in-the-same-breath rule)."""
        new_id, num = self.next_free(family)
        width = len(num)
        bumped = f"{family}-{str(int(num) + 1).zfill(width)}"
        idx = self._counter_row(family)
        line = self.doc.lines[idx]
        # replace only the last cell (the counter) to keep the rest byte-identical
        head, _, _ = line.rstrip("\n").rstrip().rstrip("|").rpartition("|")
        self.doc.lines[idx] = f"{head}| {bumped} |\n"
        self.add_row(family, new_id, topic, ort)
        self.allocated.append((new_id, family))
        return new_id

    def advance_sprint_line(self, sprint):
        """Set the Sprint row of the next-free-IDs table to max(current, sprint + 1)
        The value is a mechanical transcription of the ratified
        manifest.sprint — "+ 1" is the definition of "next free", not a
        derived-snapshot guess. Monotonic: a row already further ahead is never
        lowered. The ID-family counters are untouched (bumped only on allocation)."""
        header, sep, rows = self.doc.table_in("Nächste freie IDs")
        hits = [idx for idx in rows if row_cells(self.doc.lines[idx])[0] == "Sprint"]
        if len(hits) != 1:
            schema_fail(f"REGISTRY: Sprint-Zeile nicht eindeutig in der "
                        f"Nächste-freie-IDs-Tabelle ({len(hits)} Treffer statt 1)")
        idx = hits[0]
        cell = row_cells(self.doc.lines[idx])[-1]
        if not re.fullmatch(r"\d+", cell):
            schema_fail(f"REGISTRY: Sprint-Zeile trägt keine nackte Zahl als Zähler: {cell!r}")
        target = max(int(cell), sprint + 1)
        if target != int(cell):
            line = self.doc.lines[idx]
            head, _, _ = line.rstrip("\n").rstrip().rstrip("|").rpartition("|")
            self.doc.lines[idx] = f"{head}| {target} |\n"

    def add_row(self, family, entry_id, topic, ort):
        self.doc.append_row(FAMILY_SECTION[family], f"| {entry_id} | {topic} | {ort} |")

    def has_row(self, entry_id):
        return any(re.match(rf"^\|\s*{re.escape(entry_id)}\s*\|", line) for line in self.doc.lines)

    def set_ort(self, entry_id, ort):
        for i, line in enumerate(self.doc.lines):
            if line.startswith("|") and row_id(line) == entry_id and "|" in line[1:]:
                cells = row_cells(line)
                if len(cells) >= 3:
                    cells[-1] = ort
                    self.doc.lines[i] = "| " + " | ".join(cells) + " |\n"
                    return True
        return False

    def save(self):
        self.doc.save()


# ---------------------------------------------------------------------------
# Closure steps
# ---------------------------------------------------------------------------

WORKLIST = "chat-context/WORKLIST.md"
STARTER = "chat-context/STARTER.md"
ARCHIVE = "chat-context/ARCHIVE.md"
TPL_STARTER = "chat-context/templates/TEMPLATE-starter.md"
HANDOVER_DIR = "chat-context/handover"

QUEUE_HEADER = "| # | Cluster | Titel | Komp | Typ | Prio | Größe | Disp | Status | Ref |\n"
QUEUE_SEP = "|---|---------|-------|------|-----|------|-------|------|--------|-----|\n"


def title_and_body(prose, fallback_title):
    """If the prose block starts with an H1, use it as title; otherwise synthesise
    an H1 from the fallback. Returns (title, body_with_h1)."""
    stripped = prose.lstrip("\n")
    m = re.match(r"^#\s+(.+)\n?", stripped)
    if m:
        return m.group(1).strip(), stripped
    return fallback_title, f"# {fallback_title}\n\n{stripped}"


def step_findings(manifest, files, registry, new_paths):
    for f in manifest["findings"]:
        prose = manifest["prose"][f"Finding: {f['slug']}"]
        fallback = f["slug"].replace("-", " ")
        title, body = title_and_body(prose, fallback)
        rel = f"chat-context/findings/finding-{f['category']}-{manifest['date']}-{f['slug']}.md"
        if files.exists(rel):
            schema_fail(f"Finding-Datei existiert bereits: {rel}")
        fid = registry.allocate("F", title, f"findings/{os.path.basename(rel)}")
        content = (
            "---\n"
            f"id: {fid}\n"
            "legacy-id:\n"
            f"title: {title}\n"
            f"date: {manifest['date']}\n"
            f"sprint: {manifest['sprint']}\n"
            "status: open/new\n"
            f"severity: {f['severity']}\n"
            f"component: {f['component']}\n"
            "resolved-by:\n"
            "related: []\n"
            "---\n\n"
            f"{body.rstrip()}\n"
        )
        files.write(rel, content)
        new_paths.append(rel)


def step_sprint_file(manifest, files, new_paths):
    prose = manifest["prose"]["Sprint"]
    fallback = manifest["sprint_slug"].replace("-", " ")
    title, body = title_and_body(prose, fallback)
    rel = f"chat-context/sprints/sprint-{manifest['sprint']}-{manifest['sprint_slug']}.md"
    if files.exists(rel):
        schema_fail(f"Sprint-Datei existiert bereits: {rel}")
    # E1: tracks/ratified verbatim from the manifest when given,
    # neutral defaults otherwise
    tracks = manifest["tracks"] if manifest["tracks"] is not None else ["cross-cutting"]
    ratified = manifest["ratified"] if manifest["ratified"] is not None else []
    content = (
        "---\n"
        f"sprint: {manifest['sprint']}\n"
        f"date: {manifest['date']}\n"
        "apparatus: concept\n"
        f"title: {title}\n"
        "status: closed\n"
        f"tracks: [{', '.join(tracks)}]\n"
        f"ratified: [{', '.join(ratified)}]\n"
        "template_version: 1\n"
        "---\n\n"
        f"{body.rstrip()}\n"
    )
    files.write(rel, content)
    new_paths.append(rel)
    return rel


def process_new_tasks(manifest, worklist_doc, notes):
    """New-Tasks channel (legacy intake): the ID-less intake section above the
    Backlog. Stubs present without the explicit clear_new_tasks confirmation fail
    loud; with it, the section is emptied and every removed line is logged."""
    span = find_section(worklist_doc.lines, "New Tasks")
    if span is None:
        return  # section not (yet) present in this worklist — no-op
    start, end = span
    stub_idx = [i for i in range(start, end)
                if worklist_doc.lines[i].lstrip().startswith("- ")]
    if not stub_idx:
        return
    if not manifest["worklist"]["clear_new_tasks"]:
        assert_fail(f"New Tasks: {len(stub_idx)} ungesichtete Stubs; "
                    f"setze clear_new_tasks: true nach der Sichtung")
    for i in stub_idx:
        notes.append("removed new-task stub: " + worklist_doc.lines[i].lstrip()[2:].rstrip())
    for i in reversed(stub_idx):
        worklist_doc.lines.pop(i)


def step_worklist(manifest, files, registry, touched_rows, notes):
    wl = manifest["worklist"]
    worklist = Doc(files, WORKLIST)
    starter = Doc(files, STARTER)
    archive = Doc(files, ARCHIVE)

    process_new_tasks(manifest, worklist, notes)

    for t in wl["add_to_backlog"]:
        family = TYPE_PREFIX[t["typ"]]
        ort = f"{t['ref']} · WORKLIST" if t["ref"] not in ("TBD", "") else "WORKLIST"
        tid = registry.allocate(family, t["titel"], ort)
        row = make_task_row(tid, t)
        worklist.append_row("Backlog", row)
        touched_rows.append(row)

    queue_rows = starter.table_row_lines("Aktiv-Queue")
    queue = [(row_id(r), r) for r in queue_rows]

    for aid in [a["id"] for a in wl["archive"]]:
        if aid not in [q[0] for q in queue]:
            assert_fail(f"worklist.archive: {aid} steht nicht in der Aktiv-Queue")
    for a in wl["archive"]:
        queue = [(qid, r) for qid, r in queue if qid != a["id"]]
        arch_row = f"| {a['id']} | {a['summary']} | {a['ref']} |"
        archive.append_row("Archiv-Tasks", arch_row, at_top=True)
        touched_rows.append(arch_row + "\n")
        if not registry.set_ort(a["id"], a["ref"]):
            assert_fail(f"REGISTRY: keine Row für archivierte ID {a['id']}")

    for pid in wl["promote"]:
        row = worklist.take_row("Backlog", pid)
        if row is None:
            assert_fail(f"worklist.promote: {pid} steht nicht im WORKLIST-Backlog")
        queue.append((pid, row))
        touched_rows.append(row)

    handle_map = {}
    for t in wl["add_to_queue"]:
        family = TYPE_PREFIX[t["typ"]]
        ort = f"{t['ref']} · Aktiv #{manifest['next_sprint']}" if t["ref"] not in ("TBD", "") \
            else f"Aktiv #{manifest['next_sprint']}"
        tid = registry.allocate(family, t["titel"], ort)
        if t.get("handle"):
            handle_map[t["handle"]] = tid
        row = make_task_row(tid, t)
        queue.append((tid, row))
        touched_rows.append(row)

    if wl["reposition"] is not None:
        # E2: substitute manifest-local handles with the freshly allocated IDs
        # BEFORE the set comparison
        want = [handle_map.get(tok, tok) for tok in wl["reposition"]]
        have = [qid for qid, _ in queue]
        if sorted(want) != sorted(have):
            assert_fail(f"worklist.reposition: ID-Menge passt nicht zur Queue nach den Ops "
                        f"(reposition: {sorted(want)}, Queue: {sorted(have)})")
        by_id = dict(queue)
        queue = [(qid, by_id[qid]) for qid in want]

    worklist.save()
    archive.save()
    return [r if r.endswith("\n") else r + "\n" for _, r in queue]


def flip_frontmatter(files, rel, status, curated_in):
    content = files.read(rel)
    fm_text, _ = split_frontmatter(content, rel)
    if not re.search(r"^status:", fm_text, re.MULTILINE):
        schema_fail(f"{rel}: keine status:-Zeile im Frontmatter")
    m = re.match(r"^---\s*\n.*?\n(?=---)", content, re.DOTALL)  # up to the closing fence
    end = m.end()
    fm_block = content[:end]
    fm_block = re.sub(r"^status:[^\n]*$", f"status: {status}", fm_block, count=1, flags=re.MULTILINE)
    if curated_in:
        if re.search(r"^curated-in:", fm_block, re.MULTILINE):
            fm_block = re.sub(r"^curated-in:[^\n]*$", f"curated-in: {curated_in}",
                              fm_block, count=1, flags=re.MULTILINE)
        else:
            fm_block = re.sub(r"^(status:[^\n]*)$", rf"\1\ncurated-in: {curated_in}",
                              fm_block, count=1, flags=re.MULTILINE)
    files.write(rel, fm_block + content[end:])


def resolve_handover(name):
    return name if "/" in name else f"{HANDOVER_DIR}/{name}"


def step_handover(manifest, files):
    for h in manifest["handover"]:
        for key in ("dispatch", "return"):
            rel = resolve_handover(h[key])
            if not files.exists(rel):
                schema_fail(f"handover: Datei fehlt: {rel}")
            flip_frontmatter(files, rel, h["status"], h["curated_in"])
        for key in ("dispatch", "return"):
            # read-back from the overlay (and later from disk via FileSet.flush)
            rel = resolve_handover(h[key])
            fm_text, _ = split_frontmatter(files.read(rel), rel)
            m = re.search(r"^status:\s*(\S+)", fm_text, re.MULTILINE)
            if not m or m.group(1) != h["status"]:
                assert_fail(f"handover: {rel} trägt nach dem Flip nicht status: {h['status']}")


def template_sections(tpl_text):
    """Split the STARTER template into (frontmatter, intro, [(heading, body_lines)])."""
    fm_text, body = split_frontmatter(tpl_text, TPL_STARTER)
    lines = body.splitlines(keepends=True)
    first_h2 = next((i for i, l in enumerate(lines) if l.startswith("## ")), len(lines))
    intro = lines[:first_h2]
    sections = []
    i = first_h2
    while i < len(lines):
        j = i + 1
        while j < len(lines) and not lines[j].startswith("## "):
            j += 1
        sections.append((lines[i], lines[i + 1:j]))
        i = j
    return fm_text, intro, sections


def step_starter(manifest, files, queue_rows):
    tpl_text = files.read(TPL_STARTER)
    fm_text, intro, sections = template_sections(tpl_text)

    m = re.search(r"^template_version:\s*(\d+)", fm_text, re.MULTILINE)
    if not m:
        schema_fail(f"{TPL_STARTER}: template_version fehlt im Frontmatter")
    tpl_version = m.group(1)

    fix_found = [h for h, _ in sections if "(fix" in h]
    for want in ("## Apparatur (fix)", "## Boot (fix", "## Method & Konvention (fix)"):
        if not any(h.startswith(want) for h, _ in sections):
            schema_fail(f"{TPL_STARTER}: (fix)-Sektion fehlt im Template: {want}…")
    if len(fix_found) != 3:
        schema_fail(f"{TPL_STARTER}: erwartet genau 3 (fix)-Sektionen, gefunden {len(fix_found)}")

    title = f"{PROJECT_NAME} Sprint #{manifest['next_sprint']} — {manifest['next_front']}"
    prose = manifest["prose"]

    # Intro blockquote: everything after the '# {{title}}' placeholder line, verbatim
    intro_out = intro
    for i, line in enumerate(intro):
        if line.strip() == "# {{title}}":
            intro_out = intro[i + 1:]
            break

    out = []
    out.append("---\n")
    out.append(f'title: "{title}"\n')
    out.append(f"sprint: {manifest['next_sprint']}\n")
    out.append("apparatus: concept\n")
    out.append(f"date: {manifest['date']}\n")
    out.append(f"template_version: {tpl_version}\n")
    out.append("---\n\n")
    out.append(f"# {title}\n")
    out.extend(intro_out)

    def section_prose(name):
        return prose[name].rstrip() + "\n"

    for heading, body_lines in sections:
        h = heading.strip()
        if "(fix" in h:
            out.append(heading)
            out.extend(body_lines)
        elif h.startswith("## Erwartung & Anomalien"):
            out.append(heading)
            out.append("\n")
            out.append(section_prose("STARTER Erwartung"))
            out.append("\n")
        elif h.startswith("## Aktiv-Queue"):
            out.append(heading)
            out.append("\n")
            # keep the template's explanatory blockquote, then the derived table
            for line in body_lines:
                if line.lstrip().startswith(">"):
                    out.append(line)
            out.append("\n")
            out.append(QUEUE_HEADER)
            out.append(QUEUE_SEP)
            out.extend(queue_rows)
            out.append("\n")
        elif h.startswith("## Arbeitsauftrag"):
            out.append(heading)
            out.append("\n")
            out.append(section_prose("STARTER Arbeitsauftrag"))
            out.append("\n")
        elif h.startswith("## Code interface"):
            out.append(heading)
            out.append("\n")
            if prose.get("STARTER Code-Interface", "").strip():
                out.append(section_prose("STARTER Code-Interface"))
            else:
                out.append("n/a\n")
        else:
            schema_fail(f"{TPL_STARTER}: unbekannte Template-Sektion: {h!r}")

    files.write(STARTER, "".join(out))


# ---------------------------------------------------------------------------
# Assertions (definition-of-done, fail-closed)
# ---------------------------------------------------------------------------

def norm_section_text(lines):
    return "".join(lines).strip("\n")


def check_assertions(manifest, files, registry, touched_rows, warnings):
    starter_text = files.read(STARTER)
    starter_lines = starter_text.splitlines(keepends=True)
    tpl_text = files.read(TPL_STARTER)
    _, _, tpl_sections = template_sections(tpl_text)
    _, starter_body = split_frontmatter(starter_text, STARTER)
    st_lines = starter_body.splitlines(keepends=True)
    st_sections = []
    i = next((k for k, l in enumerate(st_lines) if l.startswith("## ")), len(st_lines))
    while i < len(st_lines):
        j = i + 1
        while j < len(st_lines) and not st_lines[j].startswith("## "):
            j += 1
        st_sections.append((st_lines[i], st_lines[i + 1:j]))
        i = j

    # A1: no done rows in the Aktiv-Queue
    starter = Doc(files, STARTER)
    queue_rows = starter.table_row_lines("Aktiv-Queue")
    for row in queue_rows:
        cells = row_cells(row)
        if len(cells) >= 9 and ("done" in cells[8].lower() or "✅" in cells[8] or "✓" in cells[8]):
            assert_fail(f"Aktiv-Queue enthält eine done-Zeile: {row_id(row)}")

    # A2: archived IDs present in ARCHIVE, absent from the queue
    archive = Doc(files, ARCHIVE)
    arch_ids = {row_id(r) for r in archive.table_row_lines("Archiv-Tasks")}
    queue_ids = [row_id(r) for r in queue_rows]
    for a in manifest["worklist"]["archive"]:
        if a["id"] not in arch_ids:
            assert_fail(f"{a['id']} fehlt nach dem Lauf in ARCHIVE ## Archiv-Tasks")
        if a["id"] in queue_ids:
            assert_fail(f"{a['id']} steht nach dem Archivieren noch in der Aktiv-Queue")

    # A3: (fix) sections byte-identical with the template
    tpl_fix = {h.strip(): norm_section_text(b) for h, b in tpl_sections if "(fix" in h.strip()}
    st_fix = {h.strip(): norm_section_text(b) for h, b in st_sections if "(fix" in h.strip()}
    if set(tpl_fix) != set(st_fix):
        assert_fail(f"(fix)-Sektionen weichen ab: Template {sorted(tpl_fix)} vs. STARTER {sorted(st_fix)}")
    for h in tpl_fix:
        if tpl_fix[h] != st_fix[h]:
            assert_fail(f"(fix)-Sektion nicht byte-identisch mit dem Template: {h}")

    # A4: no frozen git state in the (variable) sections
    hexish = re.compile(r"\b[0-9a-f]{7,40}\b")
    aheadish = re.compile(r"(\bahead\b\s*[:=]?\s*\d|\d+\s+(commits?\s+)?(ahead|behind)\b|\b(ahead|behind)\b\s+\d)",
                          re.IGNORECASE)
    for heading, body_lines in st_sections:
        if "(fix" in heading:
            continue
        text = "".join(body_lines)
        for m2 in hexish.finditer(text):
            tok = m2.group(0)
            if any(c.isdigit() for c in tok) and any(c in "abcdef" for c in tok):
                assert_fail(f"Eingefrorener Git-Zustand (SHA-artig: {tok!r}) in STARTER-Sektion {heading.strip()!r}")
        if aheadish.search(text):
            assert_fail(f"Eingefrorener Git-Zustand (ahead/behind-Zählung) in STARTER-Sektion {heading.strip()!r}")

    # A5: REGISTRY — every allocated ID has a row; counters bumped; referenced IDs exist
    for entry_id, family in registry.allocated:
        if not registry.has_row(entry_id):
            assert_fail(f"REGISTRY: vergebene ID {entry_id} hat keine Row")
        counter, _ = registry.next_free(family)
        if int(re.search(r"(\d+)$", counter).group(1)) <= int(re.search(r"(\d+)$", entry_id).group(1)):
            assert_fail(f"REGISTRY: Nächste-freie-IDs für {family} nicht über {entry_id} hinaus hochgesetzt")
    for pid in manifest["worklist"]["promote"] + [a["id"] for a in manifest["worklist"]["archive"]]:
        if not registry.has_row(pid):
            assert_fail(f"REGISTRY: referenzierte ID {pid} hat keine Row")

    # A6: no half-flipped handover pair
    for h in manifest["handover"]:
        statuses = []
        for key in ("dispatch", "return"):
            rel = resolve_handover(h[key])
            fm_text, _ = split_frontmatter(files.read(rel), rel)
            m3 = re.search(r"^status:\s*(\S+)", fm_text, re.MULTILINE)
            statuses.append(m3.group(1) if m3 else "?")
        if statuses[0] != statuses[1] or statuses[0] != h["status"] or "open" in statuses:
            assert_fail(f"handover-Paar {h['dispatch']} / {h['return']} halb geflippt: {statuses}")

    # A7: disjointness backlog vs. queue
    worklist = Doc(files, WORKLIST)
    backlog_ids = {row_id(r) for r in worklist.table_row_lines("Backlog")}
    dupes = backlog_ids.intersection(queue_ids)
    if dupes:
        assert_fail(f"Disjunktheit verletzt — ID(s) in Backlog UND Aktiv-Queue: {sorted(dupes)}")

    # A10: the New-Tasks intake section, if present, is empty
    nt_span = find_section(worklist.lines, "New Tasks")
    if nt_span is not None:
        for i in range(nt_span[0], nt_span[1]):
            if worklist.lines[i].lstrip().startswith("- "):
                assert_fail("New Tasks: Sektion ist nach dem Lauf nicht leer")

    # A8: dead-pointer check on refs of newly written/moved rows
    for row in touched_rows:
        cells = row_cells(row)
        ref_cell = cells[-1] if cells else ""
        for part in [p.strip() for p in ref_cell.split("·")]:
            check_ref_path(files, part)

    # A9 is obsolete: the uniform superrepo `git add -A`
    # captures skills/ (and everything else) structurally.

    # Soft check: retrospective prose in the Arbeitsauftrag (warning only)
    for heading, body_lines in st_sections:
        if heading.strip().startswith("## Arbeitsauftrag"):
            text = "".join(body_lines)
            hits = re.findall(r"\b(erreicht|geschafft|erledigt)\b", text, re.IGNORECASE)
            if hits:
                warnings.append(f"::warning:: Rückschau-Marker im Arbeitsauftrag: {sorted(set(h.lower() for h in hits))}")


def check_ref_path(files, part):
    """If a ref part looks like a repo file pointer, it must exist (overlay-aware).
    Bare IDs (ADR-0034, F-0157, D-OPS-1 …) are not paths and are skipped."""
    if not part or part in ("TBD", "—", "-"):
        return
    anchored = part.split("#", 1)[0]
    is_pathish = "/" in anchored or anchored.endswith(".md")
    if not is_pathish:
        return
    if anchored.startswith("plan:"):
        return
    candidates = [anchored, f"chat-context/{anchored}"]
    if re.fullmatch(r"tasks/[A-Z]+-\d+", anchored):
        # carrier files are named tasks/<ID>-<slug>.md
        base = anchored.split("/", 1)[1]
        import glob as _glob
        if _glob.glob(os.path.join(files.root, "chat-context", "tasks", base + "*")):
            return
        assert_fail(f"Toter Zeiger: {part!r} — kein chat-context/tasks/{base}*-File")
    for cand in candidates:
        if files.exists(cand):
            return
    assert_fail(f"Toter Zeiger: Ref {part!r} zeigt auf keine existierende Datei")


# ---------------------------------------------------------------------------
# git phase — dumb-uniform and LLM-free. There is deliberately
# NO state analysis here: every run performs the same steps, and every
# deviation from the happy path exits 4 without further mutation. Concept
# never reasons about git again — it only reads the post-push gitstatus.
#
#   1. preflight: git push --dry-run against ALL push targets (superrepo +
#      whitelisted submodules) — before any mutation
#   2. every submodule: git checkout main + git pull --ff-only origin main
#   3. whitelist gate: dirty/ahead submodule outside COMMIT_WHITELIST -> exit 4
#   4. whitelisted dirty/ahead submodules: add -A + commit + push (direct main)
#   5. superrepo: add -A + commit + push (captures everything, incl. all
#      pointer bumps from the sync — deliberate, git is the central backup)
# ---------------------------------------------------------------------------

# The one guard against un-reviewed code on main: only these submodules may be
# committed direct-to-main by the closure. A fixed code constant — not a
# manifest field, not a Concept judgment. Implementation submodules always go through the PR workflow.
COMMIT_WHITELIST = ("spec",)


def run_git(root, *args, check=True):
    proc = subprocess.run(["git", "-C", root, *args], capture_output=True, text=True)
    if check and proc.returncode != 0:
        git_fail(f"git {' '.join(args)} rc={proc.returncode}: {proc.stderr.strip()}")
    return proc.stdout


def submodule_paths(root):
    gm = os.path.join(root, ".gitmodules")
    if not os.path.exists(gm):
        return []
    out = subprocess.run(["git", "config", "--file", gm, "--get-regexp", r"path"],
                         capture_output=True, text=True)
    return [line.split(None, 1)[1] for line in out.stdout.splitlines() if line.strip()]


def git_in(root, sub, *args):
    """Run git inside a submodule; returns the CompletedProcess (no auto-fail)."""
    return subprocess.run(["git", "-C", os.path.join(root, sub), *args],
                          capture_output=True, text=True)


def preflight_push_targets(root):
    """Git step 1: verify push capability against EVERY target this run may push
    to (superrepo origin/main + each whitelisted submodule), plus the superrepo
    branch guard. Runs before any mutation — a credential/network problem that
    is visible up front can never produce a 'commit exists but push failed'
    state for either remote. dry_run skips this entirely (offline preview)."""
    branch = run_git(root, "branch", "--show-current").strip()
    if branch != "main":
        git_fail(f"Superrepo steht auf Branch {branch!r}, erwartet 'main' — kein Lauf.")
    targets = [("Superrepo", root)]
    subs = submodule_paths(root)
    targets += [(f"Submodul {s}", os.path.join(root, s))
                for s in COMMIT_WHITELIST if s in subs]
    for label, path in targets:
        proc = subprocess.run(["git", "-C", path, "push", "--dry-run", "origin", "main"],
                              capture_output=True, text=True)
        if proc.returncode != 0:
            git_fail(f"Push-Preflight {label} (origin main) fehlgeschlagen — nichts mutiert. "
                     f"git: {(proc.stderr or proc.stdout).strip()}")


def sync_submodules(root):
    """Git step 2: pull every submodule onto main, uniformly. Remote-merged
    PR states land on the local main; a checkout stuck on a feature branch is
    moved to main. Never --force (silent data loss), never merge/rebase."""
    for sub in submodule_paths(root):
        co = git_in(root, sub, "checkout", "main")
        if co.returncode != 0:
            git_fail(f"Submodul {sub}: uncommittete Änderungen blockieren checkout main — "
                     f"als PR mergen oder verwerfen (niemals --force). "
                     f"git: {(co.stderr or co.stdout).strip()}")
        pl = git_in(root, sub, "pull", "--ff-only", "origin", "main")
        if pl.returncode != 0:
            git_fail(f"Submodul {sub}: pull --ff-only origin main fehlgeschlagen "
                     f"(lokaler main divergiert?) — kein Merge, kein Rebase, kein Raten. "
                     f"git: {(pl.stderr or pl.stdout).strip()}")


def submodule_delta(root, sub):
    """Return (dirty, ahead_count) for a submodule after the sync."""
    st = git_in(root, sub, "status", "--porcelain")
    if st.returncode != 0:
        git_fail(f"Submodul {sub}: git status fehlgeschlagen: {st.stderr.strip()}")
    rl = git_in(root, sub, "rev-list", "--count", "origin/main..HEAD")
    if rl.returncode != 0:
        git_fail(f"Submodul {sub}: rev-list origin/main..HEAD fehlgeschlagen: {rl.stderr.strip()}")
    return bool(st.stdout.strip()), int(rl.stdout.strip())


def enforce_commit_whitelist(root):
    """Git step 3: after the sync, a dirty or ahead submodule outside the
    whitelist means the operator precondition (all implementation PRs merged
    on GitHub before the closure) is violated — stop, never push it through."""
    offenders = []
    for sub in submodule_paths(root):
        if sub in COMMIT_WHITELIST:
            continue
        dirty, ahead = submodule_delta(root, sub)
        if dirty or ahead:
            state = " und ".join((["dirty"] if dirty else [])
                                 + ([f"ahead {ahead}"] if ahead else []))
            offenders.append(f"Submodul {sub} ist {state} — als PR mergen, "
                             f"gehört nicht direct-main")
    if offenders:
        git_fail("; ".join(offenders) + ". Nichts committet.")


def commit_whitelisted_submodules(root, message):
    """Git step 4: commit + push each dirty/ahead whitelisted submodule
    (practically: spec) direct to main. Returns {sub: pushed_head_sha}."""
    pushed = {}
    subs = submodule_paths(root)
    for sub in COMMIT_WHITELIST:
        if sub not in subs:
            continue
        sub_path = os.path.join(root, sub)
        dirty, ahead = submodule_delta(root, sub)
        if dirty:
            run_git(sub_path, "add", "-A")
            run_git(sub_path, "commit", "-m", message)
            ahead = submodule_delta(root, sub)[1]
        if ahead:
            run_git(sub_path, "push", "origin", "main")
            pushed[sub] = run_git(sub_path, "rev-parse", "HEAD").strip()
    return pushed


def commit_superrepo(root, message):
    """Git step 5: add -A (everything in the working tree — deliberate; robust
    beats surgical, git is the central backup) + commit + push."""
    run_git(root, "add", "-A")
    run_git(root, "commit", "-m", message)
    sha = run_git(root, "rev-parse", "HEAD").strip()
    run_git(root, "push", "origin", "main")
    return sha


# ---------------------------------------------------------------------------
# main
# ---------------------------------------------------------------------------

def print_diffs(files):
    for rel in sorted(files.changed()):
        old = files.originals.get(rel)
        old_lines = old.splitlines(keepends=True) if old else []
        new_lines = files.overlay[rel].splitlines(keepends=True)
        fromfile = f"a/{rel}" if old is not None else "/dev/null"
        sys.stdout.writelines(difflib.unified_diff(old_lines, new_lines,
                                                   fromfile=fromfile, tofile=f"b/{rel}"))
        sys.stdout.write("\n")


def check_no_replacement_chars(files):
    for rel, content in files.changed().items():
        if "�" in content:
            assert_fail(f"Replacement-Char (U+FFFD) in {rel} — Encoding-Schaden, Abbruch")
        unicodedata.normalize("NFC", content)  # decodable sanity pass


def main(argv):
    args = [a for a in argv[1:] if a != "--dry-run"]
    dry_run = "--dry-run" in argv[1:]
    if len(args) != 1:
        sys.stderr.write("usage: python scripts/closure.py <manifest.md> [--dry-run]\n")
        return EXIT_USAGE

    root = os.getcwd()
    for required in (REGISTRY, WORKLIST, STARTER, ARCHIVE, TPL_STARTER):
        if not os.path.exists(os.path.join(root, required)):
            sys.stderr.write(f"FEHLER: {required} nicht gefunden — cwd muss der Workspace-Root sein\n")
            return EXIT_USAGE

    warnings = []
    notes = []
    try:
        manifest = load_manifest(args[0])
        files = FileSet(root)
        registry = Registry(files)
        new_paths = []
        touched_rows = []

        step_findings(manifest, files, registry, new_paths)          # step 2
        step_sprint_file(manifest, files, new_paths)                 # step 3
        queue_rows = step_worklist(manifest, files, registry, touched_rows, notes)  # step 4
        registry.advance_sprint_line(manifest["sprint"])             # step 5
        registry.save()                                              # step 5 (write side)
        step_handover(manifest, files)                               # step 6
        step_starter(manifest, files, queue_rows)                    # step 7

        check_no_replacement_chars(files)
        check_assertions(manifest, files, registry, touched_rows, warnings)  # step 8

        for n in notes:
            print(n)
        for w in warnings:
            print(w)

        message = manifest["commit_message"] or \
            f"Sprint {manifest['sprint']} closure: {manifest['sprint_slug']}"

        if dry_run:
            print_diffs(files)
            print("geplanter git-Block:")
            print("  (Git-Phase im dry-run komplett übersprungen — offline-fähige Vorschau)")
            print("  1. Push-Preflight: git push --dry-run origin main "
                  f"(Superrepo + Whitelist-Submodule {list(COMMIT_WHITELIST)})")
            print("  2. je Submodul: git checkout main && git pull --ff-only origin main")
            print(f"  3. Whitelist-Riegel: dirty/ahead außerhalb {list(COMMIT_WHITELIST)} -> Exit 4")
            print(f"  4. je dirty/ahead Whitelist-Submodul: git add -A && "
                  f"git commit -m \"{message}\" && git push origin main")
            print(f"  5. Superrepo: git add -A && git commit -m \"{message}\" && "
                  f"git push origin main")
            print("ok (dry-run)")
            return EXIT_OK

        preflight_push_targets(root)                                 # git step 1
        sync_submodules(root)                                        # git step 2
        enforce_commit_whitelist(root)                               # git step 3
        files.flush()                                                # write + read-back
        pushed = commit_whitelisted_submodules(root, message)        # git step 4
        sha = commit_superrepo(root, message)                        # git step 5
        suffix = "".join(f" ({sub}: {psha})" for sub, psha in sorted(pushed.items()))
        print(f"ok {sha}{suffix}")
        return EXIT_OK

    except ClosureError as exc:
        sys.stderr.write(f"FAIL: {exc}\n")
        return exc.exit_code
    except Exception as exc:  # unexpected — still fail loud, never half-commit
        sys.stderr.write(f"FAIL (unerwartet): {type(exc).__name__}: {exc}\n")
        return EXIT_USAGE


if __name__ == "__main__":
    sys.exit(main(sys.argv))
