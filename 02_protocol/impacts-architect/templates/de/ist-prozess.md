---
type: ist-prozess
name: Antrag prüfen und entscheiden
owner: Sachbearbeitung
frequency: je Antrag
trigger: Antrag geht ein
inputs:
  - Antrag mit Anlagen
outputs:
  - Bescheid
tools:
  - E-Mail
  - Fachanwendung
duration: drei Tage bis zwei Wochen
touchpoint: standard
evidence_status: reported
---

<!-- Translation source: 02_protocol/impacts-architect/templates/ist-prozess.md; sha256: 6b5bdb1965d9e499d30ae65b9e0a1cf7cd4e514a5adf2c8b98e5103b009c333c -->

# Antrag prüfen und entscheiden

Synthetisches Erfassungsbeispiel. Bestehende Quellenheimat nutzen; andernfalls unter `grundlagen/ist-prozesse/` erfassen. Diese Datei ist Quellmaterial für Identify, selbst nie eine Application. Bei einer Produkt-/Servicebeschreibung oder einem fertigen Ergebnis Quellaussagen vom rekonstruierten Ablauf (`hypothesis`) unterscheiden; ein unbekannter heutiger Ablauf bleibt `open`. Beispielwerte in der Arbeitssprache des Kunden ersetzen. Evidenzlabels und Quellen direkt an der jeweiligen Aussage nennen.

Das beispielhafte Feld `owner` ordnet diese Aufnahme der genannten Rolle zu. Es belegt weder Eigentum an einer Regel noch Entscheidungsautorität; diese Rollen mit ihrer jeweiligen Evidenz getrennt festhalten.

## Ablauf heute

1. Antrag geht per E-Mail ein und wird erfasst.
2. Sachbearbeitung prüft Vollständigkeit.
3. Bei Lücken Rückfrage beim Antragsteller, Vorgang bleibt liegen.
4. Prüfbericht, dann Entscheidung durch die Leitung.
5. Bescheid geht raus.

## Wo wird angehalten und geprüft

In diesem Beispiel liest die Leitung vor der Entscheidung den Prüfbericht. Klären, warum diese menschliche Grenze erforderlich ist, was genau entschieden wird und wer die Grenze ändern darf. Erforderliche Autorität, menschliche Interaktion und gewohnte Arbeitsteilung unterscheiden. Bereits erlaubte Unterstützung und offene Entscheidungen benennen.

Für die genannte Dauer: Von welchem Start bis zu welchem akzeptierten Ende? Welche Zeit ist Bearbeitung, welche Warten auf Eingaben, Übergabe oder Entscheidung, welche Nacharbeit? Quellen oder berichtete Spannen nennen; fehlende Messung offenlassen.

Welche Information oder Entscheidung fehlt beim Warten tatsächlich? Welche Beiträge wären mit bereits verfügbaren Informationen, Regeln und Befugnissen möglich? Beobachtete Möglichkeiten von noch zu bestätigenden Verbesserungsvorschlägen trennen.

## Was bleibt gleich, was ist je Lauf neu

Gleich: Prüfkatalog, Bescheidvorlage, Zuständigkeiten. Antrag, Anlagen und Rückfragen gehören zum konkreten Fall; dessen Geschäftsbestand kann mehrere Prozessläufe überdauern. Der Lauf bindet den benötigten Ausschnitt.

Welche angebotene Leistung oder welcher fachliche Gegenstand ist betroffen, welche konkreten Instanzen/Fassungen gehören zusammen und wodurch sind sie belegt? Vorhandene fachliche Definitionen und Records aus diesem Kundenworkspace verlinken, nicht erneut pflegen.

## Was verlässt den Prozess, wer nimmt es ab

Der Bescheid geht an den Antragsteller; die Leitung prüft die Abnahmebedingungen. Einen Zahler nur bei Relevanz nennen. Für jeden erforderlichen Ergebnisbestandteil erzeugenden Job, Voraussetzungen und beobachtbare Abnahme benennen. Bei einem Angebot Katalogversprechen, vereinbarten Umfang und tatsächliche Erfüllung unterscheiden. „Reverse-engineer a product or service“ aus der Methode anwenden; unbelegte Verbindungen und nächste Evidenzaktion benennen, statt beobachtete Arbeit zu erfinden.

## Wer fasst es an

Synthetische Rollen: Sachbearbeitung, Leitung und Antragsteller bei Rückfragen. Eine externe Beteiligung wird nicht behauptet.

## Was bricht, wenn ein Schritt falsch läuft, und fällt es auf

Eine falsche Entscheidung kann einen Widerspruch auslösen und erst dadurch sichtbar werden; einen unvollständigen Prüfbericht kann die Leitung früher erkennen. Tatsächlichen Schaden und Belege zur Erkennbarkeit erfassen.

## Beobachtungen und Belege

Eine Beobachtung ist eine begrenzte Aussage über einen Gegenstand oder Fall, die aus unmittelbarer Beobachtung, einer gelesenen Quelle, einem Bericht oder einer Messung festgehalten wurde. Sie ist nicht das Quellen- oder Evidenzartefakt und kein künftiger Arbeitsschritt; ihre Erfassung verifiziert weder die Aussage noch das Artefakt. Jeden relevanten Zeitpunkt in seiner eigenen Bedeutung festhalten: Sachverhalts- oder Gültigkeitszeit, Ausgabezeit oder fachlicher Stand/Fassung der Quelle, tatsächliche Beobachtungs-, Beschaffungs- oder Lesezeit und Erfassungszeit. Unterschiedliche Zeiten getrennt halten, unbekannte benötigte Zeiten `open` lassen und nie einen Zeitpunkt durch einen anderen ersetzen. Aussage, Quellenverweis und Evidenzlabel, relevante fachliche Verknüpfungen und verbleibende Lücken festhalten. Eine aus einer Quelle abgeleitete Beobachtung darf deren Aussage sinngemäß wiedergeben. Sie darf daraus nicht stillschweigend tatsächliches Verhalten, Ursache, Regelgültigkeit oder Zuständigkeit ableiten. Wenn eine andere Datei die Beobachtung eigenständig zitiert, erhält sie eine stabile Adresse nach [fachlichen Adressen und Beziehungen](../../../ontology.md#domain-addresses-and-relationships). Berichtende Person, Datenlieferant, rechnende Person, Pflegeperson, Regeleigentümer und Entscheidungsautorität bleiben verschiedene Rollen, auch wenn Evidenz zeigt, dass eine Person mehrere davon ausübt; jede Zuordnung getrennt belegen. Eine Beobachtung bleibt mit ihrem Evidenzstatus erhalten, während ihre Prozesszuordnung `open` ist.

## Berechnungen und Entscheidungen

Für jede relevante beobachtete Rechnung oder fachliche Ableitung diese Fallnotiz einmal übernehmen; alle daraus entstehenden Größen gemeinsam nennen. Jede eigenständig zitierte Beobachtung über diese Rechnung erhält eine stabile Adresse. Für die konkrete Berechnungsdurchführung außerdem einen fallbezogenen Schlüssel oder Quellenverweis festhalten; dieser bezeichnet das konkrete Vorkommen, keine zweite `rechenweg:`-Identität. Relevante Kennzahldefinitionen, Regeln und Quellen über ihre vorhandenen Adressen verlinken und optionale lokale Kennungen nur bei Bedarf verwenden, statt hier eine zweite Regelheimat zu schaffen. Vorgeschriebene Regel, beobachtete Praxis und Änderungsvorschlag als getrennt belegte Aussagen mit eigenem Geltungsbereich erhalten. Weicht eine beobachtete Formel wesentlich von der vorgeschriebenen ab, erhält sie nur dann eine weitere `rechenweg:`-Adresse, wenn sie eigenständig zitiert, wiederverwendet oder geändert wird; sonst bleibt sie in dieser Fallnotiz. Tabelle oder Code bleibt ihr Implementierungs- oder Evidenzartefakt. Unbekannte Antworten mit nächster Evidenzaktion `open` lassen.

- Ergebnis und Bedeutung: Welche Größen entstanden für welchen Fall, mit welcher Einheit, Grundgesamtheit und welchem Zeitraum? Bei Kennzahlen auf ihre Definition verweisen.
- Vorgegebene Regel: Wo liegt die geltende Regel, welche Fassung gilt, wer darf sie ändern und welche Kontrollen sind vorgeschrieben?
- Tatsächliche Berechnung: Wer rechnete, wo (auch im Kopf oder in einer persönlichen Tabelle), mit welcher tatsächlich verwendeten Formel oder Datei/Fassung, und wer pflegt sie? Was löst Neuberechnung oder Prüfung aus?
- Eingaben: Für jeden verwendeten Wert Quelle oder liefernde Person, Schlüssel/Auswahl, Gültigkeitszeit oder Fassung, tatsächliche Beschaffungs-/Lesezeit und Übertragungsweg in diese Rechnung nennen. Welche Quellenprüfung war nötig?
- Prüfung und Abnahme: Unter welcher Bedingung durfte der jeweilige Empfänger die Größe verwenden, welche Prüfung wurde tatsächlich von wem oder was mit welchem Ergebnis und Beleg ausgeführt? Wurde die Größe für ihren vorgesehenen Zweck von wem oder was mit welchem Ergebnis und Beleg abgenommen? Unbekannte Abnahme `open` lassen und von einer nach der geltenden Regel nicht erforderlichen Abnahme unterscheiden. Eine vorgeschriebene Prüfung belegt ihre Durchführung nicht.
- Ziel und Nutzung: Wohin ging jede Größe, wer nutzte sie für welche weitere Arbeit, Entscheidung oder Kundenausgabe? Die berechnete Zahl allein erlaubt nichts davon. Unbekannte Nutzung `open` lassen; Nichtnutzung nur nach Prüfung relevanter Empfänger, des Zeitraums und der Pflichten behaupten, nicht aus fehlender Evidenz wie einer leeren Ablage oder ausbleibender Rückmeldung.

Bestehende Beiträge von Mensch, Agent und deterministischem System erfassen. Ihre künftige Kombination nur innerhalb geklärter Grenzen entwerfen.

## Quellen und Aktualität

Wo liegen benötigte Werte, Regeln und Dokumentrohlinge? Schlüssel/Auswahl, Fassung oder fachlichen Stand zum genannten Zeitpunkt, tatsächliche Beschaffungs- oder Lesezeit beziehungsweise liefernde Person, Zieleingabe und nötige Quellenprüfung benennen; für den Weg der Eingaben bis zur Nutzung einer gerechneten Größe die Fallnotiz oben verwenden. Wo Aktualität zählt, Auslöser der Aktualisierung oder Prüfung und zuständige Pflegeperson nennen; unbekannte Fassung oder unbekannten fachlichen Stand `open` lassen. Fehlenden Zugriff getrennt von fehlenden Daten oder unbekanntem Vorhandensein festhalten. Bestehende Arbeitsanweisung, implementiertes Werkzeug oder vorgeschlagene Änderung unterscheiden. Illustrative Evidenz ist eine datierte Gesprächsnotiz der Sachbearbeitung vom 2026-09-02; sie stützt nur eine berichtete Fallaussage und erzeugt keine `quelle:`-Adresse. Der illustrative Prüfkatalog Version 3 kann bei eigenständiger Zitierung eine wiederverwendbare Regelquelle sein. Beide durch erreichbare Evidenz ersetzen; weder Gespräch noch Katalog werden als tatsächlich vorhanden behauptet.
