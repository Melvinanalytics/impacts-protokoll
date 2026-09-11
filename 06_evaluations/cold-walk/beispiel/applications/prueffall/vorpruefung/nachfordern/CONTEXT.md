---
type: arbeitsschritt
id: arbeitsschritt:nachfordern
eingaben:
  - input/pruefbericht.md
  - input/pruefbericht-herkunft.md
ausgaben:
  - output/nachforderung.md
  - output/nachreichung.md
pruefung: Nachforderung nennt jede Lücke; Nachreichung entspricht dem belegten Eingang für diesen Vorgang
routen:
  nachgereicht: arbeitsschritt:pruefen
customer_touchpoint: standard
---

# Nachfordern

## Ein Job

Fehlende Angaben beim Antragsteller anfordern und auf die Nachreichung warten.

## Eingaben

`input/pruefbericht.md` mit den Lücken; `input/pruefbericht-herkunft.md` belegt die Übergabe aus dem Prüfversuch.

## Nicht laden

Die frühere Antragsfassung; der Bericht trägt die Lücken. Dieser Schritt führt keine Fassungen oder Teilnachträge zusammen.

## Verarbeitung

1. Liste der fehlenden Angaben aus dem Bericht ziehen.
2. Anschreiben vorbereiten; ein Mensch führt das Gespräch.
3. Versuch auf `wartend` setzen, bis die Nachreichung eintrifft.
4. Den Eingang für diesen Vorgang als `output/nachreichung.md` sichern und seine Quelle als `Eingangsquelle: <Workspace-Pfad>` im Übergabenachweis festhalten. Erst der belegte Eingang erlaubt `nachgereicht`; ob er alle Lücken schließt, prüft der nächste Versuch.

Während des Wartens darf der Agent das Anschreiben aus den bereits gebundenen Berichtslücken weiter vorbereiten. Es bleibt ein Entwurf in `output/nachforderung.md`; der Mensch führt weiterhin das Gespräch. Gebundene Eingaben, Route und Freigabe ändern sich dabei nicht. Nachgereichte Angaben werden im folgenden Prüfversuch neu gebunden; eine erledigte Rückfrage wird nicht ungeprüft erneut verwendet.

## Ausgaben

`output/nachforderung.md`: bearbeitbarer Entwurf; beim Abschluss gilt die tatsächlich vorliegende Fassung. `output/nachreichung.md`: Kopie des zugeordneten Eingangs.

Für diesen Beispielablauf ist der Eingang eine vollständige berichtigte Antragsfassung. Ein Teilnachtrag darf sie nicht ersetzen; er benötigt eine ausdrücklich definierte Zusammenführung außerhalb dieses Beispiels. Diese Eingangsform ist eine fachliche Voraussetzung, kein zusätzlicher Core-Check.

Bei Route `nachgereicht`: `output/nachreichung.md -> arbeitsschritt:pruefen/input/antrag.md`.

## Prüfung

Jede Lücke des Berichts erscheint in der Nachforderung. Die Nachreichung muss mit dem gespeicherten Eingang für diesen Vorgang übereinstimmen. Ein fertiges Anschreiben allein erlaubt keinen Abschluss. Im synthetischen Walk benennt `continuation_ref` die Eingangsdatei innerhalb des Workspace; das Harness prüft Pfad, Existenz, Bytegleichheit und `Eingangsquelle` vor der Route. Dies ist die lokale Beschaffungsprüfung dieses Beispiels, keine allgemeine Core-Semantik für `continuation_ref`.

## Human Check

Kein Gate. Der Touchpoint ist `standard`: der Mensch spricht mit dem Antragsteller.
