---
type: teilprozess
id: teilprozess:vorpruefung
ergebnis: Prüffähiger Prüfbericht
---

<!-- Translation source: 02_protocol/templates/teilprozess.md; sha256: 4ec7c2e7648a3ef68dc392670a2ef140a08c34a7e8f53d2668d0ea3f2b1c2196 -->

# Vorprüfung

Diese Vorlage gilt für gewählte Core-Verträge gemäß `02_protocol/impacts-architect/references/formwahl.md`, Abschnitt „Tooling stop“, in der benannten Protokollquelle und Revision.

Ein Teilprozess ist ein fachlich geschlossener Abschnitt des Hauptprozesses. Seine Arbeitsschritte sind seine Unterordner; der Ordnername ist der Slug seiner ID. Beispielwerte ersetzen.

## Beitrag zur Leistung

Ein fachlich geschlossenes Ergebnis dieses Abschnitts, seinen Empfänger oder konsumierenden Folgeabschnitt und seine erlaubte Nutzung angeben. Erklären, wie `ergebnis` zur akzeptierten Leistung des Hauptprozesses beiträgt; Hauptprozess und untergeordnete Arbeitsschritte nicht wiederholen.

## Eingaben und Grenzen

Abschnittsübergreifend benötigte vorgelagerte Ergebnisse, Fachdefinitionen, Regeln, Ressourcen und Befugnisse benennen. Relevante Ausschlüsse und Bedingungen nennen, unter denen der Abschnitt sein Ergebnis nicht beanspruchen darf. Auf jede Quellenheimat verweisen; ihren Inhalt nicht in diesen Teilprozessvertrag kopieren.

## Zusammenspiel der Arbeitsschritte

Jeden erforderlichen Bestandteil von `ergebnis` dem erzeugenden Arbeitsschritt zuordnen. Bei einer internen Übergabe auf die vom Producer deklarierte Übergabe und anwendbare Prüfung verweisen, ohne ihre Pfade zu wiederholen oder eine zweite Routentabelle zu führen. An einer terminalen Grenze stattdessen finalen Empfänger, akzeptiertes Ergebnis und anwendbares Ende nennen; keinen nachgelagerten Consumer erfinden. Jeder untergeordnete Arbeitsschritt muss zum Abschnittsergebnis beitragen.

## Einrichtungsabschluss

Die Definitionseinrichtung ist abgeschlossen, wenn jeder Ergebnisbestandteil erzeugenden Arbeitsschritt, sichtbare Ausgabe und anwendbare Prüfung hat; jedes interne Ergebnis referenziert seine konsumierende Grenze, jedes terminale Ergebnis nennt finalen Empfänger und Ende. Jede erforderliche Eingabe ist beschaffbar oder mit nächster Aktion und Nutzungsgrenze ausdrücklich offen, und kein untergeordneter Job oder Claim liegt außerhalb des Abschnittsbeitrags. Vor dem Kandidaten-Commit einen gestützten Fall, einen Fall mit fehlender oder widersprüchlicher Voraussetzung und einen Fall mit plausibler unzulässiger Schlussfolgerung über diesen Abschnitt prüfen; Voraussetzungen, erwartete Ergebnisse und offene Lücken festhalten. Nach dem Commit liefert die Test-Phase beobachtete Harness-Evidenz für genau diese Revision. Strukturelle Gültigkeit und Designprüfung belegen weder Einsatzbereitschaft noch `ergebnis`.

## Frühindikator

Nur wenn eine früh beobachtbare Größe eine konkrete Steuerungsentscheidung unterstützt: Indikator, vermuteten Zusammenhang zur Kennzahl der Leistung und mögliche Handlung nennen. Der Zusammenhang bleibt `hypothesis`, bis beobachtete Vorgänge ihn stützen. Sonst diesen Abschnitt weglassen; Beitrag und Ergebnis des Abschnitts bleiben erforderlich.
