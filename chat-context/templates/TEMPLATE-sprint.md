---
# Sprint-Frontmatter-Schema — template_version 1.
# Diesen YAML-Block an den Anfang jeder Datei in chat-context/sprints/ setzen.
# Der Body darunter trägt das Sprint-Narrativ (auf Deutsch, §13).
# YAML-Keys bleiben Englisch (greppbar/Tooling); Prosa ist Deutsch.
sprint: "31.1"               # Nummer; Sub-Sprints gequotet ("31.1"), sonst parst YAML es als Float
date: 2026-06-22             # YYYY-MM-DD (Session-Datum; erster Tag bei mehrteiligem Sprint)
apparatus: concept           # concept | code | design
title: <Sprint-Front / Thema>
status: closed               # in-progress | closed (Sprint-Dateien sind i.d.R. abgeschlossene Records)
tracks: [A2, cross-cutting]  # berührte Spuren: A1 | A2 | B | cross-cutting
ratified: [ADR-0012-A1, CHORE-02]  # optional: ADR-/D-/Task-IDs, die der Sprint gelandet/geschlossen hat
template_version: 1
---

# {{title}}

## Wo wir standen
Ausgangslage und Ground-Truth zu Sprint-Beginn.

## Was entschieden / ratifiziert wurde
Die Entscheidungen, Designs oder Doktrinen im Volltext (oder Verweis auf den ADR-/Decision-Doc).

## Empirie / Ergebnis
Wall-Balance, Messungen, Resultate — sofern zutreffend.

## Aufgeschoben (mit Trigger)
Verschobene Punkte und was sie jeweils auslöst.

<!--
Erhaltungsregel bei der Übersetzung: Identifier (ADR-…, D-…, CHORE-…, FEAT-…),
Dateipfade, Code, Commit-Hashes, Branch-/Befehlsnamen, YAML und alles in `code` / ```code```
bleiben unverändert. Etablierte Tech-Begriffe (rollback, deploy, commit, gate, smoke) dürfen
als Denglisch stehen, wenn das natürlicher ist als eine erzwungene Eindeutschung.
-->
