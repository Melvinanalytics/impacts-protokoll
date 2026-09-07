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

Arbeitseingaben liegen unter `input/`. Stabile Referenzen bleiben an ihrer einzigen Heimat; der Vorgang materialisiert die fachlich ausreichenden Bytes und eine separate `*-herkunft.md` als deklarierte Inputs. Beide werden beim Versuchsbeginn gehasht.

## Nicht laden

Was dieser Schritt bewusst nicht liest. Stufenkontext statt Alleskontext.

## Verarbeitung

Benötigte Beiträge benennen: Was bleibt beim Menschen, was erschließt oder entwirft der Agent, was verarbeitet das System deterministisch? Nur tatsächlich nötige Beiträge aufnehmen; keine Pflicht, alle drei einzusetzen. Menschliche Grenze und Begründung aus Identify beachten. Vorbereitung ist keine Entscheidungs- oder Ausführungsbefugnis.

1. Erster Schritt der Bearbeitung.
2. Zweiter Schritt.
3. Dritter Schritt. Deterministische Rechnung läuft in Code oder einer Capability; das Modell liefert Parameter und Text.

### Capability-Aufruf

Nur bei einer wiederverwendbaren Verarbeitung; Details bleiben in der öffentlichen Capability-Regel:

- Aufruf-ID: bei einem Aufruf aus dem Arbeitsschritt ableitbar, sonst explizit
- Capability-Pfad: `capabilities/<slug>/CONTEXT.md`
- Capability-Revision: `git-tree:<oid>`
- Operation:
- erwartete Ausgabe:
- Mindestprüfung:

### Quellenanforderung

- Quell-Eingabe: `input/<datei>.md`
- Herkunft:
- Ursprung: `grundlagen/<datei>.md` oder externe Referenz
- Stand: `git:<commit>` oder fachlicher Stand
- Erforderliche Kontrolle:

## Ausgaben

Dateien unter `output/`. Jede Ausgabe ist eine Editierfläche, die ein Mensch vor dem nächsten Schritt öffnen und ändern kann.

Optionale Schrittübergabe, genau einmal beim Producer: `output/quelle.md -> arbeitsschritt:<ziel>/input/ziel.md`. Der Vorgang ergänzt versuchsqualifizierten Ursprung und Content-Digest in `input/ziel-herkunft.md`.

## Prüfung

Wie `pruefung` beobachtbar wird: welche Datei, welches Kriterium, welche Route bei Nichtbestehen.

## Human Check

Was der Mensch sieht, warum seine Entscheidung nötig ist und welche Folgen jede Option hat. Gegenstand und Stand der Entscheidung sowie die erlaubte nachfolgende Handlung benennen; Vorbereitung, Entscheidung und Ausführung nicht gleichsetzen. Ändert sich der freigegebene Gegenstand, seine Deckung vor weiterer Nutzung prüfen. Verfügbarkeit beziehungsweise erwartete Wartezeit nur mit passender Quelle oder als offen angeben. Nur der benannte Mensch schreibt `freigabe` in den Laufpfad.
