---
title: "example-project Sprint #108 — Beta-Gate A (erster Fremd-Tenant)"
sprint: 108
apparatus: concept
date: 2026-07-18
template_version: 6
---

# example-project Sprint #108 — Beta-Gate A (erster Fremd-Tenant)

> Fixture-STARTER für die closure.py-Testsuite. Das Script liest hieraus nur die
> Aktiv-Queue-Tabelle; alles andere wird beim Rewrite aus dem Template neu gebaut.

## Apparatur (fix)

(Fixture-Platzhalter — wird beim Rewrite aus dem Template ersetzt.)

## Erwartung & Anomalien (variable)

- **Erwartet:** Fixture-Zustand.

## Aktiv-Queue (variable)

> **Der Ausführungs-Cursor** — Fixture-Queue mit echten Marker-Emojis und em-dashes.

| # | Cluster | Titel | Komp | Typ | Prio | Größe | Disp | Status | Ref |
|---|---------|-------|------|-----|------|-------|------|--------|-----|
| CHORE-178 | 🔧 DEPLOY | Deploy-Welle #103 Rest: EE-server v0.8.2 (Mapping OSS→EXAMPLE_EE_VERSION + GHCR-Existenz + Flyway-Gate messen → DB_MIGRATION-Weiche) + web; ops v0.13.3 + keycloak v0.9.7 bereits live | ee-srv web infra | chore | 🔴 P1 | 🌓 M | — | ⬜ todo | sprints/sprint-90-old-record.md |
| CHORE-138 | 🔧 DEPLOY | ADR-0034 Stufe 0: rollback.sh-Fossil unparken (nennt CHORE-138 als Erben) + deploy.env-Altkeys entfernen + ADR-0012-Rollback-Tupel korrigieren | infra host | chore | 🔴 P1 | 🌓 M | — | ⬜ todo | ADR-0034 · ADR-0012 |
| BUG-04 | 🔒 SEC | SEV-1-Regression-Lock-IT (Cross-Tenant-KC-User-Listing) | srv e2e | test | 🔴 P1 | 🌓 M | C | ⬜ todo | tasks/BUG-04 |

## Arbeitsauftrag (variable)

- **Nächste Aufgabe:** Fixture-Platzhalter.
