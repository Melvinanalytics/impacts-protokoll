---
type: teilprozess
id: teilprozess:vorpruefung
ergebnis: Prüffähiger Prüfbericht
---

<!-- Translation source: 02_protocol/templates/teilprozess.md; sha256: 08b2f7390007088a4e2dfd0f46fa9b63e09f4fe1ced877f0c9f9d49fcbce85cf -->

# Vorprüfung

Ein Teilprozess ist ein fachlich geschlossener Abschnitt des Hauptprozesses. Seine Arbeitsschritte sind seine Unterordner; der Ordnername ist der Slug seiner ID. Beispielwerte ersetzen.

## Beitrag zur Leistung

Ein fachlich geschlossenes Ergebnis dieses Abschnitts, seinen Empfänger oder konsumierenden Folgeabschnitt und seine erlaubte Nutzung angeben. Den Bestandteil der Leistungsstückliste nennen, den der Abschnitt erzeugt oder vollendet, samt den Verbindungen, die er verantwortet, gemäß `02_protocol/impacts-architect/references/zuschnitt.md`, Abschnitt „Teilprozess“. Hauptprozess und untergeordnete Arbeitsschritte nicht wiederholen.

## Eingaben und Grenzen

Abschnittsübergreifend benötigte vorgelagerte Ergebnisse, Fachdefinitionen, Regeln, Ressourcen und Befugnisse benennen. Relevante Ausschlüsse und Bedingungen nennen, unter denen der Abschnitt sein Ergebnis nicht beanspruchen darf. Auf jede Quellenheimat verweisen; ihren Inhalt nicht in diesen Teilprozessvertrag kopieren.

## Zusammenspiel der Arbeitsschritte

Jeden erforderlichen Bestandteil von `ergebnis` dem erzeugenden Arbeitsschritt zuordnen. Bei einer internen Übergabe auf die vom Producer deklarierte Übergabe und anwendbare Prüfung verweisen, ohne ihre Pfade zu wiederholen oder eine zweite Routentabelle zu führen. An einer terminalen Grenze stattdessen finalen Empfänger, akzeptiertes Ergebnis und anwendbares Ende nennen; keinen nachgelagerten Consumer erfinden. Jeder untergeordnete Arbeitsschritt muss zum Abschnittsergebnis beitragen.

## Einrichtungsabschluss

Die Definitionseinrichtung ist abgeschlossen, wenn jeder Ergebnisbestandteil erzeugenden Arbeitsschritt, sichtbare Ausgabe und anwendbare Prüfung hat; jedes interne Ergebnis referenziert seine konsumierende Grenze, jedes terminale Ergebnis nennt finalen Empfänger und Ende. Jede erforderliche Eingabe ist beschaffbar oder mit nächster Aktion und Nutzungsgrenze ausdrücklich offen, und kein untergeordneter Job oder Claim liegt außerhalb des Abschnittsbeitrags. Vor dem Kandidaten-Commit hier einen gestützten Fall, einen Fall mit fehlender oder widersprüchlicher Voraussetzung und einen Fall mit plausibler unzulässiger Schlussfolgerung über diesen Abschnitt festhalten und prüfen. Je Fall Voraussetzung, erwartetes Ergebnis, Prüfergebnis und offene Lücken festhalten. Synthetische Fälle kennzeichnen; erwartete Ergebnisse sind keine beobachteten Ausführungsergebnisse. Nach dem Commit liefert die Test-Phase beobachtete Harness-Evidenz für genau diese Revision. Strukturelle Gültigkeit und Designprüfung belegen weder Einsatzbereitschaft noch `ergebnis`.

## Frühindikator

Nur wenn eine früh beobachtbare Größe eine konkrete Steuerungsentscheidung unterstützt: Indikator, vermuteten Zusammenhang zur Kennzahl der Leistung und mögliche Handlung nennen. Der Zusammenhang bleibt `hypothesis`, bis beobachtete Vorgänge ihn stützen. Sonst diesen Abschnitt weglassen; Beitrag und Ergebnis des Abschnitts bleiben erforderlich.
