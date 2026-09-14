<!-- Translation source: 02_protocol/language.md; sha256: 4480f36c278bb9acdb271c1138a66416b7440999cd14917e2a2fc39349e91147 -->

# IMPACTS auf Deutsch anwenden

Diese Bedienhilfe übersetzt den [englischen Sprachvertrag](../language.md). Die englische Protokolldefinition bleibt maßgeblich für die Technik; die Arbeitsunterlagen Ihres Unternehmens bleiben Deutsch. Eine englische Quelle, Werkzeugmeldung oder importierte Application ändert diese Arbeitssprache nicht.

<!-- Translation source: README.md; sha256: 150b0b7ab6fea482cf6669335ef39f8a53081dccd8622f2118e64ada06f856ba -->

## Protokoll beziehen

Für neue Arbeit das vollständige Quellarchiv des [Releases v0.3.4](https://github.com/Melvinanalytics/impacts-protokoll/releases/tag/v0.3.4) oder den zugehörigen Tag-Checkout verwenden. Der Clone-Befehl steht unter [Get the protocol](../../README.md#get-the-protocol). Methode, Architect, Referenzen, Vorlagen und Beispiele zusammenhalten; Lesen braucht keine Installation. Ein kopierter Architect-Ordner bleibt auch mit `references/` unvollständig: Er benötigt übergeordnete Protokolldateien und die Root-Anleitung. Das Wheel enthält CLI, Schemas und Vorlagen. Für die methodische Nutzung seines erzeugten Arbeitsbereichs ist die passende vollständige Quelle nötig.

## Version und Einstiegspunkte

Die Quellausgabe steht in `[project].version` der Root-[pyproject.toml](../../pyproject.toml). Für ein installiertes Paket `python -m pip show impacts-protocol` in der Python-Umgebung von `impacts` ausführen und `Version` lesen. Die veröffentlichte Paketversion `X` gehört zum Release-Tag `vX`. Die Paketversion bezeichnet die Ausgabe; sie identifiziert weder eine genaue Quellenrevision noch belegt sie Kompatibilität.

Tatsächlichen Quellenort und Identität im vorhandenen Kunden-Root `CONTEXT.md` festhalten. Im Git-Checkout mit `git rev-parse HEAD` und `git status --short` Commit und lokale Änderungen feststellen; einen Release-Tag nur erhalten, wenn er diese Quelle bezeichnet. Ohne Git tatsächliche Archivherkunft, Tag oder Dateinamen und lokalen Quellenort benennen; eine verfügbare Prüfsumme erhalten und lokale Änderungen beschreiben. Der Archivname allein belegt seinen Inhalt nicht. Fehlende Identität oder widersprüchliche Versionen bleiben ausdrücklich offen; die zugehörige Quelle beschaffen, bevor eine Regel mit ungeklärter Version angewendet wird. Ein Checkout nach einem Release oder geänderte Dateien werden entsprechend benannt, auch bei unveränderter Ausgabe in `pyproject.toml`.

| Ausgangspunkt | Einstieg und Abschluss |
|---|---|
| Vollständige Protokollquelle | Root-[CONTEXT.md](../../CONTEXT.md) dieses Protokolls und anschließend den gewählten Aufgabenpfad lesen. Kundenarbeit in einem eigenen Ordner halten. |
| Neuer oder vorhandener Kundenordner | Dessen `CONTEXT.md` lesen; tatsächliche Protokollquelle/Revision und Arbeitssprache benennen oder der vorhandenen Angabe folgen. `02_protocol/`-Pfade gegen diese Quelle auflösen. |
| Vorhandener Core-Lauf | Bei dessen `vorgaenge/<id>/CONTEXT.md` und deklarierten Eingaben beginnen. Gebundene Application, Quellen und Sprache erhalten; ein neueres Paket oder Protokoll aktualisiert sie nicht. |
| Wheel oder kopierter Skill mit fehlender Quelle | Vollständige zugehörige Quelle von den [Releases](https://github.com/Melvinanalytics/impacts-protokoll/releases) beziehen. Benötigte Links dort auflösen, bevor deren Regeln angewendet werden. |

Der Einstieg ist geklärt, wenn Aufgabenrouter, Quellenidentität und benötigte Links erreichbar sind, ohne `main`, eine andere Ausgabe oder Modellwissen einzusetzen. Bei einer Lücke diese samt nächster Handlung erhalten; unabhängige erlaubte Vorbereitung geht weiter. Änderungen vorhandener Definitionen folgen [Reviewed correction](../impacts-method.md#reviewed-correction); früher gebundene Arbeit behält ihre Revisionen. Maßgeblicher englischer Abschnitt: [Version and entry points](../../README.md#version-and-entry-points).

## Einstieg mit vorhandenen Dateien

**Machen Sie Ihr Unternehmen für Menschen und KI leichter verständlich und bearbeitbar.** Das [Ziel von IMPACTS](../../README.md) ist, kleinen und mittleren Unternehmen zu helfen, ihr Geschäft besser zu verstehen, Arbeit zu vereinfachen und KI sowie Data Science zu nutzen, ohne selbst Fachleute dafür werden zu müssen. Das ist eine Zielaussage; ein nachgewiesener Nutzen braucht Beobachtungen im eigenen Betrieb.

Gewöhnliche Dateien und Ordner sind eine vollständige Möglichkeit, IMPACTS anzuwenden. IMPACTS ist Handbuch, Ausführungsprotokoll und Struktur; das Framework führt selbst keine Arbeit aus. Menschen können die Dateien lesen und bearbeiten. Ein unterstützender Agent braucht Dateizugriff und die passenden Lese- und Schreibrechte. Dafür sind weder Git noch Python oder eine Installation nötig.

<!-- Translation source: FIRST-WIN.md; sha256: 842955d4999f944d399637d4eacd165143295a7502263c66433bb10355ac54ba -->
Die [erste nützliche Vorbereitung](../../FIRST-WIN.md) verwendet die bestehenden Rollen Katalog, Anfrage, Angebotsvorlage und Geschäftsrecord aus dem synthetischen Unternehmensbeispiel. Legen Sie die dort gezeigten Markdown-Dateien in einem eigenen Übungsordner an; verwenden Sie deutsche lesbare Inhalte und `Working language: de` im Root-Router `CONTEXT.md`. Maschinenkennungen, Referenzen, Mengen und Einheiten bleiben erhalten: C-1 fragt P-10, 2 Stück, und S-20, 12 Stunden, für O-1/Fassung 1 an. Es sind Beispieldaten; ein Preis, ein Lieferdatum und eine Freigabe werden nicht geliefert.

Der Auftrag für einen Agenten lautet:

> Lesen Sie CONTEXT.md und die drei verlinkten Quelldateien. Füllen Sie eine Kopie der Angebotsvorlage unter records/offer-o1/draft.md. Nennen Sie die Quelle jeder Aussage. Lassen Sie Preis, Summe und Lieferdatum offen. Halten Sie Rückfrage, zuständige Person und nächste Handlung beim Entwurf fest; verlinken Sie den Entwurf im Root-Router. Erfinden Sie keine Beträge, Prüfungen oder Liefernachweise. Erteilen Sie keine Freigabe und versenden Sie nichts.

Die Übergabe benennt den tatsächlichen Fortschritt:

> Entwurf zur internen Durchsicht vorbereitet — Preis und Lieferdatum sind offen, daher ist keine bepreiste Lieferzusage belegt. Nächster Schritt: gültige Preisquelle und Rechenregel beschaffen, die Berechnung tatsächlich deterministisch prüfen und die zuständige Person nach Prüfung der Verfügbarkeit über den Liefertermin entscheiden lassen. Quellen beim Entwurf erhalten. Versand braucht eine eigene Erlaubnis.

Eine neue Sitzung startet nur bei `CONTEXT.md`, findet Entwurf und Quellen und benennt die offenen Punkte sowie die nächste Handlung. Das ist der erwartete Übungsablauf, kein bereits durchgeführter Agententest und keine bestätigte Kundenzusage. Vorhandenes Wissen und Geschäftsrecords behalten ihre Heimat; daraus entsteht kein gebundener `vorgang`.

**Flexibel im Denken. Unnachgiebig darin, was zählt.** Ein Agent darf interpretieren und entwerfen. Eine geprüfte Berechnung braucht die tatsächliche deterministische Ausführung nach der maßgeblichen Regel; eine menschliche Entscheidung kommt vom zuständigen Menschen. Unbekannte Fakten bleiben unbekannt.

## Arbeitsschritte und Prüfhinweise

<!-- Translation source: 02_protocol/impacts-architect/references/zuschnitt.md; sha256: 458fc4a003447f5517616910f9936a6c2342c614395a385c9253d3ba6eb80f24 -->
Beim Entwurf eines Arbeitsschritts für seine Quellenzuordnungen [Data Governance](../capabilities.md#data-governance) anwenden.

<!-- Translation source: 02_protocol/impacts-architect/references/formwahl.md; sha256: ae6865c3a3ad6e6d0cdb5b7bf77d9b6d4fabee4348f64cdb3b31dfa5cb99591a -->
Wenn mehrere offene Entscheidungen koordiniert werden müssen, eine datierte Liste in der vorhandenen Fall- oder Record-Heimat verwenden, die jede Frage mit zuständiger Entscheidungsperson, benötigten Eingaben und Folge bis zur Entscheidung verknüpft; sie koordiniert, ist keine Faktenheimat und leitet einen etwaigen Laufstatus aus `laufpfad` ab.

Bei einer benötigten, nicht durchgeführten Prüfung die fehlende Prüfung, ihre Folge und die nächste Handlung beim betroffenen Ergebnis verständlich machen; eine gleichwertige vorhandene Notiz genügt. Beispiel: `Entwurf bereit — <Prüfung> nicht durchgeführt; <Folge>; als Nächstes: <Handlung>`. Vorhandene Rohdiagnosen erhalten und aus Übersichten auf die Notiz verlinken, statt sie doppelt zu pflegen.

<!-- Translation source: 02_protocol/impacts-method.md; sha256: 6307684845a4574eb1337b75c414ec1df59dcae50c6af15e0437b01df61da8d9 -->
### Kennzahlen- und Berechnungsmodelle entwerfen

Der [Entwurfsweg](../impacts-method.md#design-a-kpi-and-calculation-model) nutzt gewöhnliche Dateien und explizite Links an den bestehenden fachlichen Heimaten. Core, Gateway, Installation und Verbindung zu Live-Daten sind keine Voraussetzung.

1. Von der vorgesehenen Entscheidung oder Leistung ausgehen: Empfänger, Geltungsbereich und abhängige Nutzung benennen; nur benötigte Kennzahlen und Leitplanken nach [Identify](../impacts-method.md#identify) auswählen, einschließlich Kennzahlbedeutung und Regeln für Frühindikatoren.
2. Das vorhandene Fachmodell wiederverwenden und jede Kennzahl mit Definition, maßgeblicher Rechenregel, Abhängigkeiten und Eingangsvariablen verknüpfen. Vorhandene Definitionen nach [Use](../ontology.md#use) anwenden; fehlende oder geänderte Bedeutung folgt [Author or change](../ontology.md#author-or-change). Definitionen einmal pflegen; Regeln, Fallwerte, Beobachtungen und Annahmen unterscheiden. Eine noch nicht übernommene vorgeschlagene Regel bleibt Vorschlag.
3. Quellen und Verantwortung nach [Data Governance](../capabilities.md#data-governance) beschreiben: dokumentierte Dateien, Felder oder mögliche APIs den benötigten Eingaben zuordnen; Geltungsbereich, Einheiten und relevanten Quellenstand erhalten. Dokumentierte Verfügbarkeit, nutzbarer Zugriff und tatsächlich beschaffte Daten bleiben verschiedene Aussagen.
4. Fehlende Eingaben, unklare Bedeutung und widersprüchliche Regeln mit Quelle, zuständiger Person, Frage oder Entscheidung, nächster Handlung und Folge für die abhängige Nutzung erreichbar halten. Unabhängiger Entwurf geht weiter; Werte, Befugnisse oder konkurrierende Stammdatenheimaten werden nicht erfunden.
5. Vorhandene Definitionen anhand der Prüfung ihrer vorgesehenen Nutzung nach [Use](../ontology.md#use) anwenden; fehlende oder geänderte Bedeutung anhand relevanter gültiger, fehlender oder widersprüchlicher Voraussetzungen und plausibler unzulässiger Schlussfolgerungen nach [Author or change](../ontology.md#author-or-change) prüfen. Erwartungen und tatsächliche Prüfungen getrennt erhalten. Für den Entwurf muss Rechencode weder gebaut noch ausgeführt sein; ein als geprüft bezeichnetes Rechenergebnis braucht die tatsächliche deterministische Prüfung.

Der Entwurf ist vollständig, wenn jedes benötigte Ergebnis nachvollziehbar mit Definition, Regel, Eingaben, dokumentierten Quellen oder ausdrücklichen Lücken samt nächster Handlung und Nutzungseinschränkung sowie seiner abhängigen Entscheidung oder Ausgabe verbunden ist. Das belegt einen nützlichen verknüpften Entwurf mit Prüffällen; offene Fragen, Ausführungsbereitschaft und Geschäftsergebnisse sind dadurch nicht bestätigt. Ein neues Pflichtformat entsteht nicht.

### Prozessaufnahme und Verbesserung

Bei der Entwicklung von Möglichkeiten regulatorische oder physische Grenzen anhand von Evidenz und Geltungsbereich von Gewohnheiten unterscheiden; eine aktuelle Kapazitätsgrenze belegt nicht, dass ihre Verteilung oder Ausgestaltung unveränderlich ist. Den Evidenzstand jeder Nutzenaussage von der Befugnis zum Erproben, Übernehmen oder Ausführen der Option gemäß [Evidence and obligations](../ontology.md#evidence-and-obligations) trennen.

**Synthetisches Beispiel — erwartetes Verhalten, kein ausgeführtes Ergebnis.** Eine verantwortliche Person braucht eine aktuelle interne Fallübersicht; die bestehende Quelle liefert sie mit ausreichender Herkunft, während Wochenkopie und Weiterleitungsrunde in diesem abgegrenzten Fall weder zusätzlichen Empfängernutzen noch Aufbewahrungs- oder Prüfpflicht erfüllen.

| Auftrag oder geänderte Voraussetzung | Beitrag des Agenten | Was das Ergebnis belegt |
|---|---|---|
| Den heutigen Ablauf beschreiben; einige Angaben fehlen. | Kopie und Weiterleitungsrunde mit Quellen und Lücken aufnehmen; nur fragen, was den nächsten sinnvollen Schritt verändert. | Eine nützliche Beschreibung; Neugestaltung, Installation und Maschinenvalidierung sind keine Einstiegsvoraussetzungen. |
| Bei der Verbesserung helfen. | Die benötigte Übersicht bis zur Quelle zurückverfolgen und das Entfernen doppelter Arbeit vorschlagen; vor Automation der Kopie den Gesamtaufwand betrachten. | Ein begründeter Vorschlag; die Aufnahme bleibt nützlich und tatsächlicher Nutzen unbelegt. |
| Nachbarfall: Eine datierte Prüfung durch eine befugte Person ist vorgeschrieben. | Diese Prüfung samt Nachweis erhalten; eine aktuelle Live-Ansicht führt sie nicht aus. | Der schützende Beitrag bleibt bestehen; der Entwurf erteilt keine Freigabe. |

Der Agent übernimmt die Analyse. Der Nutzer ergänzt entscheidungsrelevante Fakten oder Entscheidungen; vollständige Neugestaltung, eine feste Zahl von Optionen oder ein verbindlicher Reduktionsnachweis sind keine Voraussetzung für weitere erlaubte Arbeit.

<!-- Translation source: 02_protocol/capabilities.md; sha256: 9134ccbf832ed08af54953537df9877e4137fbaaaff85273c8d631fc50e52594 -->
### Quellen, Stammdaten und Verantwortung beschreiben

Benötigte Quellen an ihren bestehenden fachlichen Heimaten beschreiben, auch bei gewöhnlicher Dateinutzung ohne Application oder Live-Verbindung. Dokumentierte Quelle oder Schnittstelle, beschaffte Daten, geprüfter Zugriff und Erlaubnis zur vorgesehenen Nutzung bleiben getrennte Befunde.

Für relevante Attribute oder Fachbereiche und ihren Gültigkeitszeitraum die maßgebliche Faktenquelle, die für Bedeutung und erlaubte Änderungen zuständige Entscheidungsperson sowie Aufgaben der pflegenden und bereitstellenden Personen benennen. Eine Person kann mehrere Aufgaben übernehmen; unbekannte tatsächliche Verantwortliche bleiben `open`. Stabile Stammdatendefinitionen, Geschäftsvorfälle und abgeleitete Kennzahlen in vorhandenen Beschreibungen unterscheiden; neue Record-Typen sind dafür nicht nötig.

Benötigte Einheiten, Zeilenbedeutung und Granularität, Auswahl- und Gültigkeitszeit, Identität und Namensraum, Beziehungen und Quellenfeldbedeutungen gemäß [Tables and relationships](../capabilities.md#tables-and-relationships) und [Ontology](../ontology.md#meaning-and-valid-inference) beschreiben. Dokumentquellen brauchen dieselben relevanten Unterscheidungen, aber keine Tabellenform.

Die bekannte Quellenform festhalten: Datei, Export, Bericht, manuelle Eingabe oder API. Herkunft sowie bei tatsächlich gelesener Dokumentation URL oder Pfad, Fassung oder Datum und Lesedatum erhalten. Mögliche Endpunkte, Schemas, Authentifizierung und Zugangsbedingungen nur beschreiben, soweit bekannt. Zuerst vorhandene lokale Quellen nutzen; bei ausdrücklichen Lücken Quellen erkunden. Unbekanntes bleibt Frage, keine erfundene Schnittstelle.

Öffentlich dokumentierte Schnittstellen belegen für sich weder Zugriff auf Unternehmensdaten, aktuelle Werte, fachliche Maßgeblichkeit noch eine Nutzungserlaubnis; bekannte Zugangs- und Nutzungsbedingungen erhalten. Die Quellenbeschreibung braucht keinen API-Aufruf, keine Zugangsdaten und keine Live-Anbindung. Gültige Quellen- und Identitätszuordnungen samt ihren Fakten- oder Bereichsheimaten wiederverwenden; nur für die vorgesehene Nutzung fehlende oder widersprüchliche Zuordnungen klären. Gleichsetzung von Quellen oder Auswahl zwischen konkurrierenden Stammdatenheimaten anhand belegter Geltungsbereiche oder Zuordnungen begründen. Offene Entscheidungen samt zuständiger Entscheidungsperson und unbekannter Verantwortung an ihren Heimaten erhalten; nur abhängige Nutzungen einschränken.

## Marktbeziehungen bei Bedarf erschließen

Bei einer Frage zur Marktstruktur beschreibt der Agent die für das benötigte Ergebnis relevanten Beteiligten und Beziehungen: Wer fragt an, liefert, nutzt, bezahlt oder genehmigt was, für wen und unter welchen Bedingungen? Dieses abgegrenzte Gefüge ist die Markttopologie des Kunden. [Ontology](../ontology.md#domain-definition-pattern) regelt auch die Bedeutung und Evidenz dieser fachlichen Beziehungen. Die vorhandene Fach- oder Prozessheimat unter [Formwahl](../impacts-architect/references/formwahl.md#native-topology-and-boundaries) genügt; eine kurze Beschreibung, Beziehungstabelle oder Skizze kann ausreichen. Gewöhnliche Prozessaufnahme braucht kein vollständiges Marktbild.

Für die geschäftliche Betrachtung das relevante Angebot und, soweit vorhanden, seine Vereinbarung, Fassung und Gültigkeitsperiode auswählen. Unterscheiden, wer was mit wem austauscht, was versprochen und bezahlt wird und wie dieses Versprechen erfüllt wird. Ein Unternehmen kann mehrere Angebote verbinden; seine Branchenbezeichnung belegt weder die Dynamik noch die Pflichten einer bestimmten Leistung oder eines Vertrags.

Nur Fragen aufgreifen, deren Antwort die vorgesehene Nutzung verändern könnte. Die sechs Blickrichtungen überschneiden sich; sie sind weder abschließende Taxonomie noch Pflichtfragebogen:

| Blickrichtung | Frage an die relevante Quelle oder den konkreten Fall |
|---|---|
| Beteiligte | Wer fragt an, empfängt, liefert und zahlt? Welche Gruppen interagieren über das Unternehmen? Rollen und Gruppenzahl allein belegen weder Plattformseiten noch Netzwerkeffekte. |
| Nachfrage | Wie entsteht der Bedarf, wie erreicht er das Unternehmen und wodurch wird daraus ein angenommener Auftrag? Den tatsächlichen Kanal und die Entscheidung nachvollziehen, statt aus der Branche eine feste Abfolge abzuleiten. |
| Leistung und Geld | Was wird wem versprochen oder geliefert; wer schuldet oder zahlt wem wofür und wann? Vereinbarung, tatsächliche Lieferung und Zahlungseingang unterscheiden. |
| Skalierung | Was benötigt ein weiteres angenommenes Ergebnis: Arbeitszeit, physische Kapazität, wiederverwendbare Arbeit oder Koordination? Behauptete Netzwerkeffekte oder skalierbare Margen brauchen eigene Evidenz. |
| Engpass | Welche Abhängigkeit begrenzt das benötigte Ergebnis? Warteschlange oder lange Dauer allein belegen die Ursache nicht; Kapazität hängt auch von Ressourcen, Arbeitsmenge, Ablauf und Nachfrage ab. |
| Befugnisse | Welche Qualifikation, Erlaubnis oder Entscheidung ist laut tatsächlicher Regel vor welcher Handlung nötig? Die erklärte menschliche Grenze erhalten; eine Branchenbezeichnung begründet sie nicht. |

Richtung, Geltungsbereich und Quelle jeder relevanten Beziehung gemäß [Use](../ontology.md#use) erhalten; bei Prozessgestaltung den benötigten Beitrag mit seiner erzeugenden Arbeit verbinden. Beobachtete Arbeit und vorgeschlagene Alternativen unterscheiden. Das Auftreten eines Akteurs im Fall eines anderen Unternehmens belegt diese Interaktion, nicht sein gesamtes Geschäftsmodell. Der Agent bereitet die Darstellung vor und fragt nur, was die nächste sinnvolle Handlung verändert. Der [Abschluss der Erhebung](../impacts-method.md#capture-business-meaning) erlaubt ein abgegrenztes nützliches Ergebnis mit benannten Lücken. Topologiedatei, Graph, Archetypenbezeichnung oder eine vollständig ausgefüllte Liste sind dafür nicht erforderlich.

**Synthetische Gegenüberstellungen — gesetzte Voraussetzungen, keine Kundenbeobachtungen:**

| Voraussetzung | Nützliche Beziehungsbeschreibung und ihre Grenze |
|---|---|
| Ein Verlag vereinbart die Platzierung einer Sponsorenbotschaft gegen ein vereinbartes Entgelt; Leser erhalten die Publikation. | Sponsor → Verlag: vereinbarte Zahlung; Verlag → Leser: Inhalt. Tatsächliche Zahlung und die Wirkung der Leserschaft auf Sponsorennachfrage brauchen Evidenz; Netzwerkeffekte folgen daraus nicht automatisch. |
| Ein Arbeitgeber kauft laufenden Support für Gerät D-1 einschließlich täglicher Backup-Prüfung; ein Mitarbeiter fragt einen Besuch an und der Dienstleister nutzt einen Teilelieferanten. Heute ist kein Ticket offen, aber der Tätigkeitsnachweis nennt die Prüfung als nicht durchgeführt. | Zahler, Anfragenden, Empfänger und Lieferanten unterscheiden. Die gesetzte tägliche Pflicht bleibt trotz leerer Warteschlange unerfüllt. Einen Besuch seiner Vereinbarung und dem abgedeckten Objekt zuordnen; Abdeckung von D-1 belegt keine Abdeckung von D-2, und vier Rollen belegen keine vier Plattformseiten. |
| Ein Hersteller schuldet eine Charge; die Vereinbarung verlangt vor Versand die Freigabe einer benannten Person. | Produktion, Freigabe und Versand sind unterschiedliche Beiträge. Vorbereitete Nachweise ersetzen die menschliche Entscheidung nicht; die Pflicht stammt aus dieser Vereinbarung, nicht aus einer vermuteten Branchenregel. |

### Laufender Service und Nachfrage

Wenn fortdauernde Verantwortung oder wiederholte Kontakte relevant sind, fragen, welche Leistung auch ohne offenes Ticket geschuldet bleibt. An den vorhandenen Heimaten die geltende Vereinbarung samt Fassung, Gültigkeitsperiode, abgedecktem Objekt, angefragter Handlung und Erfüllungsnachweisen klären. Monatsabrechnung, gleicher Servicetyp oder Ticketabschluss allein belegen weder Abdeckung noch Erfüllung. Wiederkehrende Arbeit nach [Reverse-engineer a product or service](../impacts-method.md#reverse-engineer-a-product-or-service) durch den relevanten Fall oder Zeitraum begrenzen. Ein Einzelauftrag ohne laufende Pflicht braucht kein Serviceinventar.

Ein Ticket kann angefragte Arbeit, eine Störung, geplante Wartung oder eine durch Monitoring ausgelöste Handlung festhalten. Tatsächlichen Auslöser und Pflicht prüfen. Wenn zuvor ausgebliebene oder fehlerhafte Leistung zusätzliche Kontakte oder Nacharbeit verursachen könnte (Failure Demand), diese Erklärung auf Evidenz zurückführen; ein Ticket oder Defekt allein belegt weder Ursache noch Vermeidbarkeit. Ungewisse Ursachen bleiben `hypothesis` mit der Beobachtung, die sie unterscheiden kann.

Vor beschleunigten Antworten die vorgeschlagene Bearbeitungsverbesserung mit der Korrektur einer belegten Ursache oder der Vermeidung einer Wiederholung nach [Identify](../impacts-method.md#identify) und [Minimize](../impacts-method.md#minimize) vergleichen. Ein Chatbot kann belegte Auskünfte oder Triage beitragen; schneller geschlossene Kontakte beheben für sich keine Ursache. Nach [Test](../impacts-method.md#test) das versprochene Ergebnis und relevante Wiederholungen, unerfüllte Pflichten und Gesamtaufwand einschließlich Eskalation und Nacharbeit prüfen. Weniger Tickets allein können auch nicht erfasste oder verlagerte Arbeit bedeuten. Erforderliche Reaktionen, Leistungspflichten und menschliche Grenzen während der Ursachenklärung erhalten; nützlicher Entwurf setzt weder Live-Anbindung noch Einsatz oder belegten Nutzen voraus.

### Szenarien verwenden

Bei einer Was-wäre-wenn-Frage beobachtete Beziehungen und Parameter von Annahmen über ihre Wirkungen trennen. Eine Skizze ist keine Prognose. Frühe Szenarien dürfen ausdrückliche Annahmen oder Bandbreiten verwenden; Rechnung und Schlussfolgerung bleiben daran gebunden. Bevor Prognosen eine Entscheidung tragen, die Übereinstimmung mit relevanten Beobachtungen und die Empfindlichkeit gegenüber unsicheren Voraussetzungen nach den für die Nutzung nötigen Prüfungen beurteilen. Eine benötigte Simulation bleibt ein externer Nutzer der Dateien. Ihr Zweck, verfügbare Evidenz und nötige Prüfungen bestimmen ihren Umfang, keine feste Monatszahl oder vorgeschriebene Modellierungsleiter. Der Betrieb liefert nur tatsächlich erfasste Messwerte; fehlende Abdeckung oder Parameter bleiben Lücken.

Unter passenden Annahmen eines stabilen Flusses verknüpft beispielsweise [Little's Law](https://pubsonline.informs.org/doi/abs/10.1287/opre.9.3.383) langfristige Mittelwerte: `L = λ × W`. `L` ist die mittlere Anzahl im System, `λ` die mittlere Eintrittsrate (für diese stabile Grundgesamtheit gleich der Austrittsrate), `W` die mittlere Verweildauer innerhalb der Grenze. Systemgrenze, Grundgesamtheit, Einheiten und Messgrundlage müssen zusammenpassen; eine momentane Warteschlange und die Dauer ausgewählter abgeschlossener Fälle genügen allein nicht. Feste Rechnungen gemäß [Perfect](../impacts-method.md#perfect) tatsächlich ausführen. Die Beziehung prognostiziert weder allein die Wirkung einer beschleunigten Stufe noch bestimmt sie den Engpass oder belegt vorhandene Messdaten.

## Optionale technische Nutzung

Fortschritt, Evidenz, offene Punkte und Fortsetzung bleiben bei gewöhnlicher Prozessarbeit in den bestehenden Prozess-, Fall- oder Geschäftsrecords; Versuch, `laufpfad` und Bindung gelten für ausgewählte Core-Läufe.

Die [Methode](../impacts-method.md) und [Formwahl](../impacts-architect/references/formwahl.md#tooling-stopp) bestimmen den Umfang: Maschinenvalidierung wird für eine konkrete benötigte Prüfung aufgerufen, wenn ein geeigneter Prüfer verfügbar ist. Sie ist keine allgemeine Zugangsschranke für Arbeit. Ein fehlendes Werkzeug bedeutet „Prüfung nicht durchgeführt“; eine fehlgeschlagene Prüfung bleibt fehlgeschlagen. Unabhängige erlaubte Vorbereitung geht weiter, während genau die Aussage oder Handlung eingeschränkt bleibt, die den fehlenden Nachweis benötigt. Benennen Sie Fortschritt, Folge und nächste Handlung; Rohdiagnosen bleiben für Betreibende erhalten.

Ist Git bei der Vorbereitung eines Git-gebundenen Laufs nicht verfügbar, bleiben Entwurf, Quellen, Fragen und Definitionsentwurf erhalten und fortsetzbar. Die historische Laufvalidierung wurde nicht durchgeführt; die Vorbereitung bleibt ungebunden und ist kein validierter Lauf. Nächster Schritt: an einem Rechner mit Git und Python-CLI den Application-Vertrag samt erforderlichen Setup-Fällen vervollständigen, die Application am Core-Root committen, den Lauf anhand der [Laufvorlage](../templates/vorgang.md) an den tatsächlichen committed Tree binden und `impacts validate` auf dem Arbeitsbereich ausführen. Das wirkliche Ergebnis erhalten und Fehler vor einer Behauptung validierter Bindung korrigieren. Keine Tree-ID, keinen Hash, keinen Verlauf und keine Freigabe erfinden. Validierung allein beweist weder Ausführung noch fachlichen Erfolg.

Mit Python 3.11+ im gewählten Arbeitsordner eine virtuelle Umgebung anlegen und aktivieren: `python3 -m venv .venv`, anschließend `source .venv/bin/activate` (macOS/Linux). Eine Installationsquelle wählen: Im vollständigen Checkout `python -m pip install -e .` ausführen; oder das Wheel und `SHA256SUMS` vom oben verlinkten Release in einen gemeinsamen Ordner herunterladen. Dort mit `shasum -a 256 -c SHA256SUMS` (macOS/Linux) prüfen und nur bei passender Prüfsumme mit `python -m pip install ./impacts_protocol-0.3.4-py3-none-any.whl` installieren. Paket und zugehörige vollständige Quelle nach [Version und Einstiegspunkte](#version-und-einstiegspunkte) identifizieren. Die folgenden Befehle außerhalb des vorgesehenen neuen Kundenordners ausführen.

Die Befehle erzeugen oder prüfen Dateien; sie führen keine Kundenarbeit aus:

```sh
impacts init ../mein-arbeitsbereich --language de
impacts template application --language de
impacts template arbeitsschritt --language de
impacts validate ../mein-arbeitsbereich
```

`init` erzeugt einen neuen, leeren Arbeitsbereich; es verweigert ein vorhandenes Ziel. Der Root-Router enthält `Working language: de`. Git wird nicht erzeugt und ist für Application-Strukturprüfung ohne Lauf nicht nötig; die aktuelle historische Laufvalidierung benötigt Git und die committed Application-Bindung. Git-Historie oder Hashes belegen weder die Wahrheit einer Quelle noch eine authentifizierte Entscheidung. `setuptools` wird nur für die Entwicklungs-Packagingtests benötigt. Der [programmierte Angebotslauf](../../06_evaluations/offer-walk/CONTEXT.md) ist eine optionale technische Evaluation mit synthetischen Daten, kein Beweis für die Nutzung durch einen Menschen oder einen Agenten allein aus Dateien.

<!-- Translation source: 02_protocol/capabilities.md; sha256: 9134ccbf832ed08af54953537df9877e4137fbaaaff85273c8d631fc50e52594 -->
Die Übernahme einer Application erhält ihre Definitionsbytes; Anwendbarkeit der Quellen und Befugnisse am Ziel folgen [Data Governance](../capabilities.md#data-governance), wobei gültige lokale Zuordnungen und Befugnisse weitergelten und offene Fragen an die dafür zuständige Entscheidungsperson gehen.
Ausführung am Ziel erst behaupten, wenn dort ein `vorgang` mit seinen anwendbaren Voraussetzungen und Prüfungen tatsächlich den benannten Testendpunkt erreicht hat; Kopieren oder Linkprüfungen allein belegen dies nicht, und unabhängig erlaubte Vorbereitung bleibt bei eingeschränkter abhängiger Ausführung nützlich.
[Reviewed correction](../impacts-method.md#reviewed-correction) an der Revisionsgrenze der geänderten Heimat anwenden: Geänderte Application-Definitionen benötigen eine neue Application-Bindung, während geänderte externe Zuordnungen in ihrer Quellenheimat bleiben und entsprechende Quellenbindung sowie betroffene Prüfungen benötigen, unter Erhalt früher gebundener Eingaben.

## Was Menschen lesen

Gespräche, Fachdefinitionen, Arbeitsanweisungen, Entwürfe, Rückfragen, Prüfbegründungen und menschliche Entscheidungen werden auf Deutsch verfasst. Eigennamen, notwendige Originalzitate und technische Kennungen dürfen erhalten bleiben. Ihre Bedeutung und Folgen werden bei Bedarf auf Deutsch erklärt. Quellenwerte, Mengen, Einheiten und Identitäten werden durch Übersetzung nicht verändert.

| Stabile Kennung | Deutsche Bedeutung |
|---|---|
| `leistung` | Abnehmbares Prozessergebnis mit Kennzahl und Abnahmebedingungen; nicht automatisch ein angebotenes Produkt oder eine Dienstleistung. |
| `hauptprozess`, `teilprozess`, `arbeitsschritt` | Hauptprozess, fachlicher Abschnitt und einzelner zusammenhängender Job. |
| `vorgang`, `laufpfad`, `versuch` | Konkreter Lauf, sein verbindlicher Verlauf und Bearbeitungsversuch. |
| `eingaben`, `ausgaben`, `pruefung`, `routen` | Gebundene Eingaben, sichtbare Ergebnisse, Prüfkriterium und mögliche Folgewege. |
| `reported` | Quelle berichtet die Aussage; ihr sachlicher Inhalt ist noch nicht geprüft. |
| `verified` | Genau diese Aussage wurde im benannten Umfang geprüft oder eine zuständige Entscheidung belegt. |
| `hypothesis`, `open` | Zu prüfende Interpretation beziehungsweise offene Frage oder fehlende Eingabe. |
| `MUST` | Verbindliche Bedingung für die benannte Verwendung; kein Beleg und keine Freigabe. |

## Deutsche Nutzung durchsetzen

Vor Kundennutzung prüft der Arbeitsschritt die tatsächliche Ausgabe einschließlich eingefügter Werte auf deutsche Sprache und unveränderte fachliche Bedeutung. Der Nachweis bleibt bei der tatsächlich geprüften Ausgabe und ihrer Sprachvorgabe; in einem gebundenen Lauf gehört er zu den vorhandenen Laufdateien. Bei fehlender, veralteter oder nicht bestandener Prüfung bleibt genau diese Nutzung offen; unabhängig erlaubte Vorbereitung geht weiter. Eine englische Entscheidungsfrage genügt für einen deutschen Kunden nicht.

Feste Texte kommen aus der gebundenen deutschen Vorlage. Freitext benötigt die erklärte Sprach- und Bedeutungsprüfung durch den eingerichteten Prüfer oder zuständigen Menschen. Ein Sprachkennzeichen, Wortfilter oder Modellurteil garantiert nicht jeden möglichen Text. `impacts validate` prüft die Core-Struktur; es prüft weder natürliche Sprache noch fachliche Wahrheit oder die Identität einer Person.

Der Mensch entscheidet nur an den erklärten Grenzen. Ein Agent kann einen Entwurf und eine verständliche Entscheidungsfrage vorbereiten; dadurch entsteht keine Versandbefugnis und keine `freigabe`. Fehlende Preise oder Liefernachweise werden als konkrete Lücken benannt, nicht erfunden.

Ein importierter englischer Ablauf wird vor deutscher Kundennutzung übersetzt; bei Git-gebundener Application-Nutzung entsteht dafür eine neue gebundene Revision. Seine bisherige Tree-ID kann nach einer Textänderung nicht erhalten bleiben. Bereits gebundene Läufe und Quellen bleiben unverändert. Übersetzungen nennen den Quellenstand; bei Widerspruch bleibt die betroffene Nutzung offen, bis die Bedeutung geklärt ist.

Das [synthetische Unternehmensbeispiel](../impacts-architect/references/datenbezug.md#vom-katalog-über-die-pipeline-zum-ausgefüllten-angebot) zeigt die Verbindung von Produkten, Services, Angebot und wiederverwendbarer Vorlage. Die deutschen Beispieldaten sind keine Kundendaten und keine tatsächlich erteilte Freigabe.

Bei beobachteten Fehlern oder wiederkehrender Reibung führt [Reviewed correction](../impacts-method.md#reviewed-correction) zur bestehenden zuständigen Quelle. Der Ablauf gilt auch für Wissens- und Record-Formen; gebundene frühere Läufe bleiben erhalten.

Die [Prüfung vor menschlichen Gates und geschützten Kundenkontakten](../capabilities.md#signale-und-human-gate) benennt die Voraussetzung für diese Handlungsgrenzen; eine technische Prüfung ersetzt keine menschliche Entscheidung.
