# Capability Vollständigkeitsgrad

Operation: `vollstaendigkeitsgrad-berechnen`

Zweck: Anteil vorhandener Pflichtfelder eines synthetischen Antrags berechnen.

Parameterschema:

- Prüfregeln: kommaseparierte Pflichtfelder unter `Pflichtfelder:`.
- Antrag: ein Feld je Zeile als `Name: Wert`.

Rechenregel: `vorhandene Pflichtfelder / alle Pflichtfelder * 100`.

Einheit: Prozent, ganzzahlig. Zeitbezug: aktueller Versuch.

Blockierfall: keine Pflichtfelder in der gebundenen Regel.

Prüfer: Ergebnis liegt zwischen 0 und 100; Anzahl vorhanden ist nicht größer als Anzahl gesamt.

Belegformat: JSON-Rohresultat für das Harness; der sichtbare Markdown-Beleg wird vom Harness mit der aufgelösten Aufrufbindung geschrieben.

Sentinel: `vollstaendigkeitsgrad-v1`.

Fixtures: `fixtures/vollstaendig.md` und `fixtures/vollstaendig-erwartet.json`.
