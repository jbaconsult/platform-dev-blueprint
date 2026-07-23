# REGISTRY — zentrales ID-Verzeichnis (Vergabe-Autorität)

> Fixture-Kopie für die closure.py-Testsuite — Struktur wie die echte REGISTRY,
> Inhalt auf das Nötigste reduziert. NIE gegen die Live-Datei testen.

---

## Nächste freie IDs

| Familie | Bedeutung | Nächste freie ID |
|---|---|---|
| FEAT | Feature-Task: neue Produkt-/Plattformfunktionalität (Steuerung in WORKLIST, Substanz in tasks/ bzw. spec) | FEAT-59 |
| CHORE | Chore-Task: Wartung, Prozess, Doku, Infra, Audits, Migrationen — Arbeit ohne neue Produktfunktion | CHORE-184 |
| BUG | Bug-Task: Defekt in bestehendem Verhalten (Symptom + Fix-Auftrag; Befund-Substanz oft in einem F-Finding) | BUG-25 |
| ADR | Architecture Decision Record: ratifizierte Architekturentscheidung (spec/docs/adr/ + INDEX-adr.md) | ADR-0038 |
| F (Finding) | Befund: empirisch festgestellter Sachverhalt (Bug-Wurzel, Prozessfehler, Erkenntnis) — dokumentiert, nicht priorisiert; Ort: findings/ oder Sprint-Record | F-0180 |
| Sprint | Sprint-/Session-Record-Nummer (chat-context/sprints/); Vergabe nur durch die kanonische Steering-Line (F-0076-Regel) | 107 |

---

## FEAT

| ID | Thema | Kanonischer Ort |
|---|---|---|
| FEAT-28 | Per-Tenant/Token-Write-Rate-Limit (Bucket4j) | D-OPS-31 · WORKLIST |
| FEAT-56 | Suche + Staleness-Signal (absorbiert FEAT-49) | tasks/FEAT-56 · WORKLIST |

## CHORE

| ID | Thema | Kanonischer Ort |
|---|---|---|
| CHORE-138 | ADR-0034 Stufe 0: rollback.sh-Fossil unparken | ADR-0034 · WORKLIST |
| CHORE-165 | ADR-0034 Stufe 1: Deploy-Engine als versioniertes Artefakt | ADR-0034 · F-0157 · WORKLIST |
| CHORE-166 | ADR-0034 Stufe 2a: Trigger-Umbau | ADR-0034 · WORKLIST |
| CHORE-178 | Deploy-Welle #103 Rest: EE-server v0.8.2 + web | sprints/sprint-90-old-record.md · WORKLIST |

## BUG

| ID | Thema | Kanonischer Ort |
|---|---|---|
| BUG-04 | SEV-1-Regression-Lock-IT (Cross-Tenant-KC-User-Listing) | tasks/BUG-04 · WORKLIST |

## F (Findings)

Kanonischer Ort: chat-context/findings/ (Datei) oder der Sprint-Record.

| ID | Thema |
|---|---|
| F-0157 | git status ohne fetch ist keine Drift-Messung | sprints/sprint-90-old-record.md |
| F-0179 | write_file über den workspace-Connector ist UTF-8-sicher | findings/F-0179-f0117-reassessment-writefile-utf8-safe.md |

## Sprints

Kanonischer Ort: chat-context/sprints/. Aktuell vergeben bis: 107.
