# WORKLIST

> **Backlog-Pool, Pull-only.** Fixture-Kopie für die closure.py-Testsuite —
> Schema v2 wie die echte Datei, auf drei Zeilen reduziert.
>
> **Legende (Marker-System, Schema v2):**
> Cluster: 🚀 LAUNCH · 🔧 DEPLOY · 🔒 SEC · 🧠 CORE · 🔌 CONN · 📣 GTM · 💎 EE · 🧹 HK
> Prio: 🔴 P1 · 🟠 P2 · 🔵 P3   —   Größe: 🌑 S · 🌓 M · 🌕 L   —   Disp: `C` Code · `D` Design · `—` keiner
> Status: ⬜ todo · 🔄 in-progress · 👀 needs-review · 💤 deferred · 🚧 partial

---

## New Tasks

> ID-loser Einwurf-Kanal. Rohe Notizen ohne Struktur/ID — Mid-Session-Zuruf. Bei Closure
> gesichtet: behaltenswerte Zeilen wandern als add_to_backlog/add_to_queue (mit ID) ins Manifest,
> der Rest wird verworfen. Diese Sektion ist bei Closure-Ende leer.

## Backlog

> Priorisierter Task-Pool, Aufnahme-Ort für alles Neue. Schema v2.

| # | Cluster | Titel | Komp | Typ | Prio | Größe | Disp | Status | Ref |
|---|---------|-------|------|-----|------|-------|------|--------|-----|
| CHORE-165 | 🔧 DEPLOY | ADR-0034 Stufe 1: Deploy-Engine als versioniertes Artefakt (deploy.cfg-Key INFRA_VERSION); Host verliert Git-Checkout, tötet F-0157 | infra host | chore | 🔴 P1 | 🌕 L | C | ⬜ todo | ADR-0034 · F-0157 |
| CHORE-166 | 🔧 DEPLOY | ADR-0034 Stufe 2a: Trigger-Umbau — Merge deployt nicht mehr, workflow_dispatch auf infra, RELEASE_GO im Payload; Vorbedingung für CHORE-167 | infra | chore | 🔴 P1 | 🌓 M | C | ⬜ todo | ADR-0034 |
| FEAT-56 | 🧠 CORE | Suche + Staleness-Signal (absorbiert FEAT-49): tsvector-FTS, Scope-Modus (cross-scope≠cross-user), open_question im Suchraum; mit FEAT-50 bauen | srv | feature | 🔴 P1 | 🌕 L | C | ⬜ todo | tasks/FEAT-56 · F-0151 |
