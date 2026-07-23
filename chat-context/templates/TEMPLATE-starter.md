---
title: "<project_name> Sprint #<N> — <front>"   # wird wörtlich als Chat-Session-Name verwendet
sprint: <N>
apparatus: concept                        # concept | code | design — STARTER.md ist immer 'concept'
date: <YYYY-MM-DD>
template_version: 6
---

# {{title}}

> Boot-Datei für die nächste Session. Schema = dieses Template (template_version 6). Das Frontmatter-
> `title` wird **wörtlich** als Chat-Session-Name verwendet (Format `<project_name> Sprint #<N> — <front>`,
> **nie** ein "STARTER"-Präfix). **(fix)**-Sektionen sind Boilerplate — wörtlich übernehmen, nie pro
> Session editieren; **(variable)**-Sektionen bei jeder Closure neu schreiben. Reihenfolge beibehalten.
> Eine Closure, die eine (fix)-Sektion streicht oder kürzt, ist ein Closure-Bug.
>
> **Diese Datei trägt die maßgebliche Boot-Sequenz** (`## Boot`), die **Aktiv-Queue** (den aktiven
> Task-Cursor, `## Aktiv-Queue`) UND das Steuerungs-Briefing (`## Arbeitsauftrag`). Sie ist die
> einzige beim Boot geladene Task-Datei — der Backlog (`WORKLIST.md`) und das Archiv (`ARCHIVE.md`)
> werden NICHT geladen, nur bei Bedarf gepullt. Das `session-start`-Skill führt den Boot aus und
> wiederholt ihn nicht — fehlt der Boot-Block, bootet die nächste Instanz ins Leere.
>
> **Harte Regel — keine Historie im STARTER.** Diese Datei zeigt ausschließlich nach vorn. Kein
> "erreicht", kein "geschafft", keine Rückschau auf abgeschlossene Arbeit — dafür ist `ARCHIVE.md`
> da (`## Archiv-Tasks`), das jede fertige Zeile mit Link aufnimmt. Eine Closure, die hier Vergangenes
> einträgt, ist ein Closure-Bug — genau wie eine, die eine (fix)-Sektion kürzt.

## Apparatur (fix)

Dies ist **Concept/Desktop** — Architektur, Entscheidungen, Doku, Schema, Memory-Writes, Session-
Closure. Schreibt **nie** Programmcode und committet/pusht/merged **nie** git (operator-gated: Concept
schlägt Blöcke vor, der Operator führt sie aus). Programmcode wird an die autonome **Claude-Code**-
Instanz via `code-handover` dispatcht; jeder Code-Sub-Sprint liefert einen Report nach
`chat-context/handover/` zurück. UI-/Visual-Arbeit geht an die separate **Design**-Instanz.

## Boot (fix — maßgebliche, geordnete Sequenz; nicht editieren)

Top-down ausführen. **Der Boot lädt genau DREI Dinge: den Memory-Digest, diese STARTER-Datei und
den `<status_tool>`-Ground-Truth.** Alles andere ist Pull-when-needed, nie Boot-Pflicht.

1. `memory_load_context(scope: "<memory_scope>")` — Digest für die ganze Session halten; jede
   `type=constraint`-Regel befolgen.
2. Die deferred `<fs_connector>`-Write-Tools laden (`tool_search`); Workspace-Root
   `<workspace_root>` bestätigen (`list_allowed_directories`).
3. `<status_tool>` (`<script_runner_server>`, verbose) für Ground-Truth — Superrepo + alle Submodule
   (Branch, Tracking, ahead/behind, Uncommitted). **Erst auf Tool-Präsenz verzweigen:** Tool nicht
   ladbar (reduziertes Runtime, z. B. Handy/Web) → `status.repo-fingerprint` aus dem Digest ist der
   einzige, *unverifizierte* Anker; concept-only, keine Git-/Host-Mutation. Tool da → Live-Status
   billig gegen `status.repo-fingerprint` abgleichen (maschinenprüfbarer Claim, keine Prosa;
   Submodul-Mismatch → nur dort verbose). Niemals Prosa über den Status trauen; gegen **Erwartung &
   Anomalien** (unten) abgleichen (Match → wortlos weiter; Abweichung → nur die prüfen).
4. Diese STARTER-Datei zu Ende lesen: `## Aktiv-Queue` (der Task-Cursor — oberste Zeile = nächste
   Aufgabe) und `## Arbeitsauftrag` (erster Akt, Guardrails, Frame). Dann den Arbeitsauftrag abarbeiten.

**Pull-when-needed, NICHT im Boot laden:** `chat-context/REGISTRY.md` (bei JEDER ID-Vergabe — alleinige
Vergabe-Autorität für alle Familien; die Vergabe ist gegen Nebenläufigkeit strukturell wirkungslos,
daher frisch pullen, nie aus einem Boot-Snapshot, weil Satelliten-Sessions parallel Nummern ziehen
können), `spec/docs/INDEX-adr.md` / `INDEX-decisions.md` (bei Entscheidungsarbeit),
`chat-context/WORKLIST.md` (der Backlog — nur beim Closure oder gezieltem Pull),
`chat-context/ARCHIVE.md` (Retrieval-Index), `docs/WORKING_CONCEPT.md` (maßgeblich, bei
Methodenzweifel). Der Boot lädt sie NICHT — das volle Referenzkorpus bei jedem Boot zu lesen ist genau
der Kontextflut-Fehler, den das Drei-Load-Modell verhindert.

## Method & Konvention (fix)

`docs/WORKING_CONCEPT.md` ist maßgeblich; **spec gewinnt bei Konflikt**. Eine Entscheidung pro Turn,
recommendation-first, charakterisieren-vor-konstruieren, ratify-before-execute. Git operator-gated
(Blöcke vorschlagen, nie pushen/mergen; Moves/Renames via `git mv` gemäß §12.1). Notation ausschließlich
alphanumerisch (A1/A2, Variant 1/2/3 — nie griechische Buchstaben). Deutsch im Chat **und in
`chat-context/`** (die Steuerungsschicht folgt der Chat-Sprache); Englisch überall außerhalb
`chat-context/` — `docs/`, `spec/`, Code, Commits (§13).

## Erwartung & Anomalien (variable)

> **Der Boot-`<status_tool>` ist die ALLEINIGE Git-Wahrheit — diese Sektion ist KEIN Status-Snapshot.**
> Hier steht nur, was der Status selbst nicht liefert: (a) die **Erwartung**, gegen die der Boot
> abgleicht, und (b) **Anomalien/Bedeutungen**. Boot-Status = Erwartung → wortlos weiter (billiger
> Häkchen-Check). Abweichung → genau die ist das Signal; dort und nur dort Tokens investieren.
> **NIEMALS** ahead/behind, SHAs oder Listen committeter Dateien hier einfrieren — die holt der Boot
> frisch, und sie sind beim nächsten Boot ohnehin stale (genau das verursacht die Diskrepanz). Die
> maschinenprüfbare Git-Erwartung (SHAs/Branches/clean) liegt im `status.repo-fingerprint`-Mnemonic,
> NICHT hier — diese Sektion trägt nur die Prosa-Anomalien & Bedeutungen, die der nackte Status nicht
> erklärt. Diese Sektion ist Erwartung, keine Historie — auch hier gilt: kein Rückblick, nur der
> Maßstab, gegen den der nächste Boot prüft.

- **Erwartet:** z. B. „Superrepo `main` synchron, working tree clean **bis auf** `M spec`" — nenne nur,
  was abweichen *darf*; jedes andere Dirty/Unpushed = unerwartet → prüfen.
- **Anomalien & Bedeutungen:** was der nackte Status nicht erklärt — z. B. „`M spec` = unaufgelöster
  Drift, nicht anfassen" · noch offene operator-gated Punkte · stale Mnemonics zum Abgleich.
- **Host-/Live-Zustand** (falls relevant): vom Concept-Apparat nicht abfragbar, daher hier als
  getragener Kontext zulässig (das ist kein Git-Snapshot).

## Aktiv-Queue (variable)

> **Der Ausführungs-Cursor** — die nächsten Aufgaben in Abarbeitungsreihenfolge (oberste Zeile =
> nächste). Beim Closure aus dem `WORKLIST.md`-Backlog hierher gezogen (dort **entfernt** —
> Disjunktheit, eine Task lebt in genau einer Datei); fertige Zeilen wandern beim Closure nach
> `ARCHIVE.md`. Das ist **kein Pool** — der Pool ist der Backlog. Hier steht nur, was als Nächstes
> drankommt (typisch ein 3–5-Aufgaben-Fenster). Schema = Backlog-Schema v2.

| # | Cluster | Titel | Komp | Typ | Prio | Größe | Disp | Status | Ref |
|---|---------|-------|------|-----|------|-------|------|--------|-----|
_(bei Closure aus dem Backlog befüllt — leer heißt: nächste Session zieht sich die erste Aufgabe selbst)_

## Arbeitsauftrag (variable)

> Rein vorwärtsgerichtet — siehe Regel oben. Steuerungswarnungen, die über diese Session hinaus
> gelten (z. B. „Host nicht kalt bootstrappen"), leben im `chat-context/tasks/`-File der
> blockierenden Task, nicht hier — hier steht nur ein Verweis, falls relevant für den ersten Akt.

- **Nächste Aufgaben:** die obersten Zeilen der `## Aktiv-Queue` (oben), kurz benannt (Titel + Ref
  reicht — die Tabelle selbst trägt das Detail). Ist die Queue leer, benenne die erste aus dem
  Backlog zu ziehende Aufgabe.
- **Erste Aufgabe im Detail:** das Allererste, was diese Session tut — konkret genug, um ohne
  Rückfrage zu starten.
- **Guardrails:** phasenspezifische Leitplanken (z. B. „keine Secrets ins Repo", „ssh-Mode, kein
  autonomer Handover") — nur was für DIESE Session gilt, nicht generische Method-Regeln (die stehen
  oben unter Method & Konvention).
- **Frame:** welcher ADR / Plan / welches `chat-context/tasks/`-File gilt.
- **Durable Record:** wohin diese Session ihre Ergebnisse schreiben wird (Sprint-Datei-Pfad noch
  ohne Inhalt, Memory-Keys, relevante ADRs/Findings) — Ziel-Pointer, kein Rückblick auf Vergangenes.

## Code interface — Hin- & Rückgabe (variable; nur wenn diese Session Code dispatcht)

Nur ausfüllen, wenn der erste Akt ein Code-Dispatch ist. Input: wo der Dispatch liegt
(`chat-context/handover/`). Rückgabe: `chat-context/handover/return-*` (Code→Concept-Report).
Disziplin: **fail-loud-over-hallucinate** — Code eskaliert Architekturfragen, löst sie nie autonom;
git bleibt operator-gated; spec gewinnt bei Konflikt.
