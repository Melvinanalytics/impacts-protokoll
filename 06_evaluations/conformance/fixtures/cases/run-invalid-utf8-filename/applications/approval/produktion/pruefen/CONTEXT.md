---
type: arbeitsschritt
id: arbeitsschritt:pruefen
eingaben:
  - input/daten
ausgaben:
  - output/ergebnis.md
pruefung: Decision follows recorded request
gate: human
routen:
  freigegeben: end:freigegeben
  abgelehnt: arbeitsschritt:start
---

# Review request
