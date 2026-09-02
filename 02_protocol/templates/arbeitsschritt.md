---
type: arbeitsschritt
id: arbeitsschritt:entscheiden
eingaben:
  - input/pruefbericht.md
ausgaben:
  - output/entscheidung.md
pruefung: Entscheidung nennt Prüfbericht und Begründung
gate: human  # nur an einer Autoritäts- oder Risikogrenze; sonst diese Zeile löschen
routen:
  freigegeben: end:entschieden
  abgelehnt: arbeitsschritt:pruefen
customer_touchpoint: sacred  # fehlend, standard oder sacred
---

# Entscheiden

Ein Arbeitsschritt ist eine ICM-Stage: deklarierte Eingaben, sichtbare Ausgaben, eine Prüfregel, vollständige Routen. Pfade gelten relativ zum Versuchsordner. Mit `gate: human` heißen die Routen genau `freigegeben` und `abgelehnt`. Beispielwerte ersetzen.

## Ein Job

Ein Satz: was dieser Schritt erzeugt und wofür der nächste Schritt es braucht.

## Eingaben

Arbeitseingaben unter `input/` und stabile Referenzen aus `grundlagen/` oder `records/`. Jede Eingabe wird beim Versuchsbeginn gehasht.

## Nicht laden

Was dieser Schritt bewusst nicht liest. Stufenkontext statt Alleskontext.

## Verarbeitung

1. Erster Schritt der Bearbeitung.
2. Zweiter Schritt.
3. Dritter Schritt. Deterministische Rechnung läuft in Code oder einer Capability; das Modell liefert Parameter und Text.

## Ausgaben

Dateien unter `output/`. Jede Ausgabe ist eine Editierfläche, die ein Mensch vor dem nächsten Schritt öffnen und ändern kann.

## Prüfung

Wie `pruefung` beobachtbar wird: welche Datei, welches Kriterium, welche Route bei Nichtbestehen.

## Human Check

Was der Mensch am Gate sieht, in welcher Zeit er entscheidet und welche Route jede Entscheidung nimmt. Nur der benannte Mensch schreibt `freigabe` in den Laufpfad.
