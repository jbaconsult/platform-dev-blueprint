---
# TEMPLATE-handover — Frontmatter fuer Dispatch- und Return-Dateien in chat-context/handover/
# Kopieren, Platzhalter ersetzen, Kommentarzeilen loeschen.
id: SPRINT_NN.X                  # Sub-Sprint-ID des Austauschs (z. B. SPRINT_68.1)
type: dispatch                   # dispatch | return
apparatus: code                  # code | design — die Gegenstelle des Austauschs
date: YYYY-MM-DD                 # Erstellungsdatum der Datei
sprint: NN                       # Sprint, in dem der Austausch lief
task: [FEAT-NN]                  # Steering-Referenzen (Task-/Finding-IDs)
counterpart:                     # Dateiname des Gegenstuecks (dispatch <-> return);
                                 # leer bei interaktiven Fenstern ohne File-Gegenstueck
status: open                     # open     = Return steht aus (Dispatch unterwegs)
                                 # closed   = wurde erfolgreich abgearbeitet (bevor es verschoben wird)
                                 # active   = Lauf ist JETZT in Arbeit — Datei nicht anfassen
                                 # consumed = in den durablen Record kuratiert -> _consumed/
curated-in:                      # Pfad des kuratierenden Records (sprints/sprint-NN-...md),
                                 # Pflicht sobald status: consumed
---

# <Titel der Dispatch-/Return-Datei>

<!--
Konventionen (README.md im Ordner ist massgeblich):
- Dispatches: dispatch-<YYYY-MM-DD>-<slug>.md · Returns: handover-<YYYY-MM-DD>-<slug>.md
- Der Ordner ist Staging, nicht Record: status: consumed => Umzug nach _consumed/
  (via `git mv` im Closure-Git-Block, WORKING_CONCEPT §12.1).
- Dateien mit status: active oder open werden von Aufraeum-Laeufen NICHT bewegt und
  NICHT editiert — ein laufender Code-/Design-Prozess liest sie moeglicherweise gerade.
- Frontmatter ist Pflicht fuer neue Dateien.
-->
