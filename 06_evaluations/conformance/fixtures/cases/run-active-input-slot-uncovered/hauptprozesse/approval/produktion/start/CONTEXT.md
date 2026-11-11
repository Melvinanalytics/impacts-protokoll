---
type: arbeitsschritt
id: arbeitsschritt:start
eingaben:
  - input/auftrag.md
  - records/not-recorded.md
ausgaben:
  - output/ergebnis.md
pruefung: Request fields are recorded
routen:
  weiter: arbeitsschritt:pruefen
  abbrechen: end:abgebrochen
---

# Record request

Synthetic coverage scenario: run-active-input-slot-uncovered; file hauptprozesse/approval/produktion/start/CONTEXT.md.
