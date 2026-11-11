---
type: arbeitsschritt
id: arbeitsschritt:entwerfen
eingaben:
  - material/angebotsdaten.json
  - material/angebotsdaten-herkunft.md
  - material/angebotsregeln.md
  - material/angebotsregeln-herkunft.md
  - material/angebotsvorlage.md
  - material/angebotsvorlage-herkunft.md
ausgaben:
  - output/angebot.md
  - output/pruefbericht.md
pruefung: Prüfbericht bestätigt vollständige Füllung, passende Beträge und belegte Aussagen.
routen:
  bestanden: arbeitsschritt:freigeben
  fehlerhaft: arbeitsschritt:vorbereiten
---

# Angebot entwerfen

## Ein Job
Einen prüfbaren internen Angebotsentwurf aus den gebundenen Daten erzeugen.

## Verarbeitung
Die in den Herkunftsdateien gebundene Fachdefinition, Rechenregel und Vorlage
verwenden. Zuerst den nötigen Vorbereitungsnachweis prüfen. Dann die Vorlage
als Ausgabekopie füllen; Zahlen deterministisch berechnen und vergleichen.
Keine Liefer-, Annahme- oder Versandbestätigung hinzufügen.

## Prüfung
Der lokale Füllprüfer kontrolliert Pflichtwerte, Einheiten, Beträge und offene
Platzhalter. Die Aussageprüfung verfolgt entscheidende Behauptungen zu ihren
Quellen und Regeln. Der Prüfbericht nennt tatsächlich ausgeführte Checks und
offene Nutzungsgrenzen. Fehlende Pflichtchecks erlauben keinen bestandenen
Abschluss. Dieses Beispiel selbst dokumentiert keine ausgeführte Freigabe.

## Übergabe
Bei Route `bestanden`: `output/angebot.md -> arbeitsschritt:freigeben:material/angebot.md`.
Bei Route `bestanden`: `output/pruefbericht.md -> arbeitsschritt:freigeben:material/pruefbericht.md`.
Das produktive Harness muss beide Übergaben tragen. Das bestehende
Referenz-Harness unterstützt nur eine Übergabe je Route; dieser Vertrag
behauptet deshalb keinen damit ausführbaren vollständigen Angebotslauf.
