---
# Findings-Frontmatter-Schema — template_version 1.
# Diesen YAML-Block an den Anfang jeder Datei in chat-context/findings/ setzen.
# Der Body darunter trägt die ausführliche Beschreibung (auf Deutsch, §13).
# YAML-Keys und kontrollierte Tokens (status, severity, component) bleiben Englisch
# (greppbar/Tooling, stabil über Querverweise); die Prosa ist Deutsch.
id: F-0001                 # globale laufende Nummer, chronologisch, mit führenden Nullen (F-0001, F-0002, …)
legacy-id:                 # etablierter Querverweis-Handle, falls vorhanden; sonst leer
title: <einzeilige Finding-Überschrift>
date: 2026-06-22           # Datum der Erfassung (YYYY-MM-DD)
sprint: 31                 # Sprint, in dem es gefunden wurde
status: open/new           # <state>/<disposition> — Vokabular unten
severity: medium           # low | medium | high | sev-1
component: server/memory   # Komponenten-Vokabular unten (Bereich oder Bereich/Unterbereich)
resolved-by:               # ADR-/D-/PR-/Commit-/Finding-Ref, die es schließt; nur bei geschlossenen Findings
related: []                # optional: verwandte WORKLIST-Task-IDs / Finding-IDs
---

# {{title}}

## Beobachtung
Was beobachtet wurde. Bei Dogfood-Findings: Tool / Input / Response, mit präziser Repro wo möglich.

## Ursache / Hypothese
Die bekannte Ursache, oder Hypothesen für die Triage, falls noch nicht diagnostiziert.

## Auswirkung
Wen/was es betrifft und warum es relevant ist.

## Nächster Schritt
Was es schließt — oder, bei einem aufgeschobenen Finding, der Trigger, der es freigibt.

<!--
STATUS-VOKABULAR  (status: <state>/<disposition>; filtern per `^status: open` oder `^status: closed`)
  open/new                 gemeldet, noch nicht getriaged
  open/accepted            als real anerkannt, wird angegangen
  open/in-progress         wird gerade bearbeitet
  open/deferred            anerkannt, aber bewusst zurückgestellt (Trigger im Body vermerken)
  closed/fixed             behoben (Fix in resolved-by verlinken)
  closed/wontfix           real, aber bewusst nicht angegangen
  closed/by-design         stellte sich als gewolltes Verhalten heraus, kein Defekt
  closed/duplicate         in ein anderes Finding gefaltet (in related verlinken)
  closed/cannot-reproduce  nicht reproduzierbar

KOMPONENTEN-VOKABULAR  (instanzdefiniert — Bereich oder Bereich/Unterbereich, an die eigenen
Submodule/Komponenten anpassen; Beispiel-Set):
  server · console · infra · e2etests · mcp · provisioning · process · tooling
-->
