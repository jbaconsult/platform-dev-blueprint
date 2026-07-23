---
title: "example-project Sprint #1 — <front>"
sprint: 1
apparatus: concept
date: <YYYY-MM-DD>
template_version: 6
---

# {{title}}

> **Blueprint-Platzhalter.** Die erste echte Closure ersetzt diese Datei durch eine aus
> `chat-context/templates/TEMPLATE-starter.md` erzeugte Instanz (dort stehen auch die
> maßgeblichen Regeln: (fix)-Sektionen wörtlich übernehmen, keine Historie im STARTER,
> Drei-Load-Boot). Beim Aufsetzen einer Instanz: Template kopieren, `<memory_scope>`,
> `<fs_connector>`, `<workspace_root>`, `<status_tool>` aus `PROJECT.md` einsetzen,
> die (variable)-Sektionen für die erste Session füllen.

## Boot (fix — maßgebliche, geordnete Sequenz; nicht editieren)

Top-down ausführen. **Der Boot lädt genau DREI Dinge: den Memory-Digest, diese STARTER-Datei und
den Status-Tool-Ground-Truth.** Alles andere ist Pull-when-needed, nie Boot-Pflicht.

1. `memory_load_context(scope: "<memory_scope>")` — Digest für die ganze Session halten; jede
   `type=constraint`-Regel befolgen.
2. Die deferred `<fs_connector>`-Write-Tools laden (`tool_search`); Workspace-Root
   `<workspace_root>` bestätigen.
3. `<status_tool>` für Ground-Truth; gegen **Erwartung & Anomalien** abgleichen (Match → wortlos
   weiter; Abweichung → nur die prüfen).
4. Diese Datei zu Ende lesen (`## Aktiv-Queue`, `## Arbeitsauftrag`), dann den Arbeitsauftrag
   abarbeiten.

## Erwartung & Anomalien (variable)

- **Erwartet:** _(erste Session: frisch abgeleitetes Repo, main, clean)_

## Aktiv-Queue (variable)

| # | Cluster | Titel | Komp | Typ | Prio | Größe | Disp | Status | Ref |
|---|---------|-------|------|-----|------|-------|------|--------|-----|
_(bei Closure aus dem Backlog befüllt — leer heißt: nächste Session zieht sich die erste Aufgabe selbst)_

## Arbeitsauftrag (variable)

- **Erste Aufgabe im Detail:** _(von der ableitenden Instanz gesetzt — z. B. „PROJECT.md-Parameter
  füllen und die erste Sprint-Front festlegen")_
