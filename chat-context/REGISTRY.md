# REGISTRY — zentrales ID-Verzeichnis (Vergabe-Autorität)

> **Diese Datei ist die alleinige Vergabe-Autorität für alle nummerierten IDs im Projekt.**
> Eine ID, die hier nicht steht, existiert nicht. Eine neue ID wird ausschließlich so
> vergeben: (1) hier die nächste freie Nummer der Familie ablesen, (2) die neue Zeile
> **im selben Atemzug** hier eintragen, (3) erst dann in WORKLIST/INDEX/Finding-Datei
> verwenden. Eine Session, die eine ID benutzt, die hier fehlt, hat einen Prozessfehler —
> nicht die Registry.
>
> **Was diese Datei NICHT führt:** Status, Prio, Reihenfolge, Substanz. Das lebt in den
> kanonischen Orten (WORKLIST = Task-Steuerung, INDEX-adr/INDEX-decisions = Entscheidungen,
> findings/ = Befunde, sprints/ = Narrativ). Der Deskriptor hier benennt das Thema und
> ändert sich nicht mit dem Status — Drift-Vermeidung ist Designziel.
>
> **Regeln:**
> - IDs werden NIE wiederverwendet, auch nicht aus Lücken (monotone Vergabe,
>   Kollisionen sind teuer).
> - Nicht rekonstruierbare Nummern bleiben als "nicht rekonstruiert" stehen — sie sind
>   verbrannt, nicht frei.
> - Closure-Pflicht: jede Session, die IDs vergeben hat, aktualisiert diese Datei vor dem
>   Closure-Commit. Ein stales Register ist schlimmer als keines.
> - Sub-Sprint-/Dispatch-IDs (SPRINT_NN.X) leiten sich aus der Sprint-Nummer ab und
>   werden hier nicht einzeln geführt (Dateien in chat-context/handover/).

---

## Nächste freie IDs

| Familie | Bedeutung | Nächste freie ID |
|---|---|---|
| FEAT | Feature-Task: neue Produkt-/Plattformfunktionalität (Steuerung in WORKLIST, Substanz in tasks/ bzw. spec) | FEAT-01 |
| CHORE | Chore-Task: Wartung, Prozess, Doku, Infra, Audits, Migrationen — Arbeit ohne neue Produktfunktion | CHORE-01 |
| BUG | Bug-Task: Defekt in bestehendem Verhalten (Symptom + Fix-Auftrag; Befund-Substanz oft in einem F-Finding) | BUG-01 |
| ADR | Architecture Decision Record: ratifizierte Architekturentscheidung (spec/docs/adr/ + INDEX-adr.md) | ADR-0001 |
| F (Finding) | Befund: empirisch festgestellter Sachverhalt (Bug-Wurzel, Prozessfehler, Erkenntnis) — dokumentiert, nicht priorisiert; Ort: findings/ oder Sprint-Record | F-0001 |
| Sprint | Sprint-/Session-Record-Nummer (chat-context/sprints/); Vergabe nur durch die kanonische Steering-Line | 1 |

_Neue Decision-Ledger-Familien (`D-<family>`, z. B. D-LIC, D-CORE, D-OPS, D-GTM) werden hier als
eigene Zeile eröffnet, sobald die erste Entscheidung der Familie ratifiziert wird (Start bei
`D-<family>-1`; siehe das `adr-author`-Skill)._

---

## FEAT

| ID | Thema | Kanonischer Ort |
|---|---|---|

## CHORE

| ID | Thema | Kanonischer Ort |
|---|---|---|

## BUG

| ID | Thema | Kanonischer Ort |
|---|---|---|

## ADR

| ID | Thema |
|---|---|

## F (Findings)

| ID | Thema | Kanonischer Ort |
|---|---|---|

## Sprints

| Nr | Front | Record |
|---|---|---|
