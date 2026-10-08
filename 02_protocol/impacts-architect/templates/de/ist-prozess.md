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

<!-- Translation source: 02_protocol/impacts-architect/templates/ist-prozess.md; sha256: 487105a787c1f04d978598a4fa837da635640b55057140a257e73f558a7a7ebd -->

# Antrag prüfen und entscheiden

Synthetisches Erfassungsbeispiel. Bestehende Quellenheimat nutzen; andernfalls unter `grundlagen/ist-prozesse/` erfassen. Diese Datei ist Quellmaterial für Identify, selbst nie eine Application. Bei einer Produkt-/Servicebeschreibung oder einem fertigen Ergebnis Quellaussagen vom rekonstruierten Ablauf (`hypothesis`) unterscheiden; ein unbekannter heutiger Ablauf bleibt `open`. Beispielwerte in der Arbeitssprache des Kunden ersetzen. Evidenzlabels und Quellen direkt an der jeweiligen Aussage nennen.

Das beispielhafte Feld `owner` ordnet diese Aufnahme der genannten Rolle zu. Es belegt weder Eigentum an einer Regel noch Entscheidungsautorität; diese Rollen mit ihrer jeweiligen Evidenz getrennt festhalten.

## Ablauf heute

Die geforderten Bedingungen der Leistung rückwärts und die heutigen Tätigkeiten vorwärts erfassen und beide nach „Step areas“ und „Result work and coordination“ in `02_protocol/impacts-method.md` der festgehaltenen Protokollrevision abgleichen; „Minimize“ schlägt je Tätigkeit eine Maßnahme vor. Die synthetischen Zeilen durch beobachtete Formulierungen, Quellen und offene Fragen ersetzen. Eine Person nur nach einer Zelle fragen, deren Antwort eine vorgeschlagene Maßnahme ändern könnte. Ein „Ja“ ist ein begrenzter Befund mit Evidenzlabel; es weist keine Ausführungsform zu und erteilt keine Befugnis. Das Feld `touchpoint` im Frontmatter fasst die Aufnahme zusammen; jeden Kundenkontakt in der Spalte „Entscheidet oder erlaubt“ seiner Tätigkeit einstufen.

### Geforderte Bedingungen

| ID | Bedingung | Urheber und Grundlage | Evidenz |
|---|---|---|---|
| C1 | Der Antragsteller erhält eine begründete Entscheidung, die auf festgehaltenen Befunden beruht. | Abnahme durch den Empfänger, in diesem synthetischen Fall ausdrücklich vorausgesetzt | `reported`: synthetische Prämisse; mit der zuständigen Leitung bestätigen |
| C2 | Eine Entscheidung in der Sache beruht auf einer nach Prüfkatalog Version 3 vollständigen Akte. | Die Abnahme durch den Empfänger verlangt ausdrücklich dieses Kriterium; es dient C1, ohne den Urheber aus dieser Abhängigkeit abzuleiten | `reported`; Katalogfassung `open` |
| C3 | Eine zweite Person zeichnet jeden Bescheid mit. | Eigene Regel; Eigentümer: Abteilungsleitung; ob sie die Regel für den Zielentwurf behält, ist `open` | `reported`; Regel und anwendbare Entscheidung der Eigentümerin auffinden |
| C4 | Der Bescheid wird für die gesetzliche Frist aufbewahrt. | Pflicht eines Dritten; Rechtsgrundlage `open` | `reported` |

### Tätigkeiten in Ablaufreihenfolge

Eine Zeile je Tätigkeit; ein wiederholter Durchlauf erhält eine eigene Zeile. Die Spalten folgen den Schrittbereichen; den Job jeder Tätigkeit liefert die Analyse darunter.

| Nr. | Tätigkeit | Auslöser und Warten davor | Nimmt, woher | Wer, womit | Gibt, an wen | Prüft | Entscheidet oder erlaubt | Danach |
|---|---|---|---|---|---|---|---|---|
| 1 | Per E-Mail eingegangenen Antrag erfassen | E-Mail geht ein | Antrag mit Anlagen, E-Mail-Postfach | Sachbearbeitung, Fachanwendung | Fallakte in der Fachanwendung, angelegt durch Übernahme der Antragsdaten, in die Liste der Sachbearbeitung | Nichts | Nichts | 2 |
| 2 | Vollständigkeit prüfen | Fallakte liegt vor; wartet in der Liste (Dauer `open`) | Akte, Katalog Version 3 | Sachbearbeitung | Befund in der Fachanwendung festgehalten | Gegen den Katalog | Nichts | Vollständig: 6; unvollständig, etwa 4 von 10 (`reported`): 3 |
| 3 | Fehlende Unterlagen beim Antragsteller anfragen | Befund: unvollständig | Befund, Anschrift des Antragstellers | Sachbearbeitung, E-Mail | Nachforderung per E-Mail, an den Antragsteller | Nichts | Kontakt erlaubt (`open`) | Antwort: 4; keine Antwort innerhalb der Frist (`open`): 8 lehnt als unvollständig ab |
| 4 | Nachgereichte Unterlagen zur Akte nehmen | Antwort kommt nach 2 bis 10 Tagen (`reported`) | Antwort, E-Mail-Postfach; Fallakte | Sachbearbeitung | Unterlagen aus der E-Mail in die Akte kopiert | Nichts | Nichts | 5 |
| 5 | Vollständigkeit erneut prüfen | Unterlagen ergänzt | Akte, Katalog Version 3 | Sachbearbeitung | Befund in der Fachanwendung festgehalten | Gegen den Katalog | Nichts | Vollständig: 6; unvollständig: 3 |
| 6 | Prüfbericht erstellen | Befund: vollständig | Akte, Katalog, Vollständigkeitsbefund aus 2 oder dem letzten 5 | Sachbearbeitung | Neu festgehaltene Entscheidungsbefunde und vollständige Kopie jeder Anlage, an die Leitung; keine bloße Kopie des Vollständigkeitsbefunds | Nichts | Nichts | 7 |
| 7 | Alle Anlagen erneut lesen | Bericht geht ein | Bericht, Akte | Leitung | Nichts | Vollständigkeit gegen den Katalog | Nichts | 8 |
| 8 | Entscheiden | Lesen abgeschlossen oder keine Antwort auf 3 bis zur Frist | Bericht aus 6; bei Ablehnung ohne Antwort der Befund aus 2 oder 5 und die verstrichene Frist | Leitung | Entscheidung in der Fachanwendung festgehalten | Nichts | Entscheidet nach einer Delegationsregel (`open`) | Bewilligung oder Ablehnung: 9 |
| 9 | Bescheid entwerfen | Entscheidung getroffen | Entscheidung, Bescheidvorlage | Sachbearbeitung | Bescheidentwurf in der Fachanwendung angelegt | Nichts | Nichts | 10 |
| 10 | Bescheid mitzeichnen | Entwurf liegt vor | Bescheidentwurf | Stellvertretung | Mitgezeichneter Bescheid | Nichts | Gibt nach C3 frei | 11 |
| 11 | Bescheid versenden | Mitgezeichnet | Bescheid, Anschrift | Sachbearbeitung, Post | Bescheid, per Post an den Antragsteller | Nichts | Kundenkontakt `standard` (`hypothesis`) | 12 |
| 12 | Bescheid zur Aufbewahrung ablegen | Versendet | Bescheid | Sachbearbeitung, Archiv | Bescheid ins Archiv kopiert | Nichts | Nichts | Ende |

### Analyse

| Nr. | Dient | Ergebnisarbeit? | Koordination? | Fehlerfolge? | Doppelung? | Überschuss? | Vorgeschlagene Maßnahme |
|---|---|---|---|---|---|---|---|
| 1 | Bringt den Antrag in die Bearbeitung | Nein | Ja; getrennt nur durch E-Mail-Kanal und Fachanwendung (`hypothesis`) | Nein; erster Durchlauf | Nein | Nein | Trennung aufheben: Eingang legt die Fallakte direkt an (`hypothesis`) |
| 2 | C2 | Ja (`reported`) | Nein | Nein; erster Durchlauf | Nein | Nein | Behalten; nicht weiter reduzierbar, soweit C2 trägt (`reported`); das Warten davor nach der Zeitregel beurteilen |
| 3 | Fehlende Eingabe für C2 | Nein | Ja; der Antragsteller ist Dritter | Ja (`hypothesis`): das Antragsformular, vor dieser Aufnahme gelegen, fragt diese Unterlagen nicht ab; Identify prüft es | Nein | Nein | Den Formularfehler seinem Eigentümer melden und das Formular korrigieren; Nachforderung für Akten behalten, die weiter unvollständig eingehen |
| 4 | Fehlende Eingabe für C2 | Nein | Ja | Ja; folgt aus 3 (`hypothesis`) | Nein | Nein | Dieselbe Korrektur wie bei 3 |
| 5 | C2 | Ja (`reported`) | Nein | Ja; folgt aus 3 (`hypothesis`) | Nein; das Material hat sich geändert | Nein | Dieselbe Korrektur wie bei 3 |
| 6 | Von C1 geforderte festgehaltene Entscheidungsbefunde | Ja (`reported`) | Nein für die Erzeugung der Befunde; eine Übergabe getrennt beurteilen, falls sie eine Abhängigkeit regelt | Nein | Nein | Ja: die Kopien dienen nach Prüfung relevanter Empfänger und Pflichten keiner Bedingung oder Abhängigkeit (`reported`) | Bericht auf Befunde mit Verweisen kürzen |
| 7 | C2 | Ja (`reported`) | Nein | Nein | Ja: die anwendbare Prüfung, 2 oder das letzte 5, prüft C2 nach demselben Katalog an derselben Aktenfassung; keine Regel für eine zweite Prüfung gefunden (`hypothesis`) | Nein | Die anwendbare Prüfung der Sachbearbeitung samt Nachweis behalten; die Leitung sieht die zitierten Stellen ein |
| 8 | C1 | Ja (`reported`) | Nein | Nein | Nein | Nein | Behalten; nicht weiter reduzierbar, soweit C1 trägt (`reported`) |
| 9 | C1 | Ja (`reported`) | Nein | Nein | Nein | Nein | Behalten; nicht weiter reduzierbar, soweit C1 trägt (`reported`) |
| 10 | C3 | Ja, nur für eine eigene Regel (`reported`) | Nein | Nein | Nein | Nein | Abteilungsleitung fragen, ob die Regel bleibt oder sich ändert |
| 11 | C1 | Ja (`reported`) | Nein | Nein | Nein | Nein | Behalten; nicht weiter reduzierbar, soweit C1 trägt (`reported`) |
| 12 | C4 | Ja, Pflicht eines Dritten (`reported`) | Nein | Nein | Nein | Nein | Behalten (`reported`); Rechtsgrundlage bestätigen, bevor mehr behauptet wird |

Jede Tätigkeit nennt eine Bedingung oder Abhängigkeit, und jede Bedingung nennt eine Tätigkeit. Ungeklärte Antworten offenlassen. „Keines“ ist eine Minimize-Frage, keine Löschbefugnis. Die Korrektur von 3 verhindert das Warten vor 4 in späteren Fällen; das Warten in der Liste vor 2 nach der Zeitregel beurteilen. Für Vergleiche unter einer Ergebnisgrenze, Grundgesamtheit, Periode und Einheit nicht überlappenden beobachteten Aufwand genau einmal unter Kombination und Maßnahme seiner Tätigkeit zurechnen, Wartezeit getrennt halten und kein 100-Prozent-Kreisdiagramm erzwingen.

## Wo wird angehalten und geprüft

In diesem Beispiel liest die Leitung vor der Entscheidung den Prüfbericht. Klären, warum diese menschliche Grenze erforderlich ist, was genau entschieden wird und wer die Grenze ändern darf. Erforderliche Autorität, menschliche Interaktion und gewohnte Arbeitsteilung unterscheiden. Bereits erlaubte Unterstützung und offene Entscheidungen benennen.

Für die genannte Dauer: Von welchem Start bis zu welchem akzeptierten Ende? Welche Zeit ist Bearbeitung, welche Warten auf Eingaben, Übergabe oder Entscheidung, welche Nacharbeit? Quellen oder berichtete Spannen nennen; fehlende Messung offenlassen.

Welche Information oder Entscheidung fehlt beim Warten tatsächlich? Welche Beiträge wären mit bereits verfügbaren Informationen, Regeln und Befugnissen möglich? Beobachtete Möglichkeiten von noch zu bestätigenden Verbesserungsvorschlägen trennen.

## Was bleibt gleich, was ist je Lauf neu

Gleich: Prüfkatalog, Bescheidvorlage, Zuständigkeiten. Antrag, Anlagen und Rückfragen gehören zum konkreten Fall; dessen Geschäftsbestand kann mehrere Prozessläufe überdauern. Der Lauf bindet den benötigten Ausschnitt.

Welche angebotene Leistung oder welcher fachliche Gegenstand ist betroffen, welche konkreten Instanzen/Fassungen gehören zusammen und wodurch sind sie belegt? Vorhandene fachliche Definitionen und Records aus diesem Kundenworkspace verlinken, nicht erneut pflegen.

## Was verlässt den Prozess, wer nimmt es ab

Der Bescheid geht an den Antragsteller. Abnahmebedingungen unter „Geforderte Bedingungen“ festhalten; „Ablauf heute“ nennt die Tätigkeit, die jede erfüllt. Einen Zahler nur bei Relevanz nennen. Bei einem Angebot Katalogversprechen, vereinbarten Umfang und tatsächliche Erfüllung unterscheiden. „Reverse-engineer a product or service“ aus der Methode anwenden; unbelegte Verbindungen und nächste Evidenzaktion benennen, statt beobachtete Arbeit zu erfinden.

## Wer fasst es an

Synthetische Rollen: Sachbearbeitung, Leitung, Stellvertretung und Abteilungsleitung als Eigentümerin der Regel; der Antragsteller ist externer Beteiligter.

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

Wo liegen benötigte Werte, Regeln und Dokumentrohlinge, welches System führt und wo liegen Kopien? Datenobjekte und Facetten aus `02_protocol/impacts-architect/references/datenumgang.md` verwenden. Schlüssel/Auswahl, Fassung oder fachlichen Stand zum genannten Zeitpunkt, tatsächliche Beschaffungs- oder Lesezeit beziehungsweise liefernde Person, Zieleingabe und nötige Quellenprüfung benennen; für den Weg der Eingaben bis zur Nutzung einer gerechneten Größe die Fallnotiz oben verwenden. Wo Aktualität zählt, Auslöser der Aktualisierung oder Prüfung und zuständige Pflegeperson nennen; unbekannte Fassung oder unbekannten fachlichen Stand `open` lassen. Fehlenden Zugriff getrennt von fehlenden Daten oder unbekanntem Vorhandensein festhalten. Bestehende Arbeitsanweisung, implementiertes Werkzeug oder vorgeschlagene Änderung unterscheiden. Illustrative Evidenz ist eine datierte Gesprächsnotiz der Sachbearbeitung vom 2026-09-02; sie stützt nur eine berichtete Fallaussage und erzeugt keine `quelle:`-Adresse. Der illustrative Prüfkatalog Version 3 kann bei eigenständiger Zitierung eine wiederverwendbare Regelquelle sein. Beide durch erreichbare Evidenz ersetzen; weder Gespräch noch Katalog werden als tatsächlich vorhanden behauptet.
