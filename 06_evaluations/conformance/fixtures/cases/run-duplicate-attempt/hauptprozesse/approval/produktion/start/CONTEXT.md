---
type: arbeitsschritt
id: arbeitsschritt:start
eingaben:
  - input/auftrag.md
ausgaben:
  - output/ergebnis.md
pruefung: Request fields are recorded
routen:
  wiederholen: arbeitsschritt:start
  weiter: arbeitsschritt:pruefen
  abgeschlossen: end:abgeschlossen
---

# Start step with explicit retry loop
