<!-- Translation source: 02_protocol/language.md; sha256: f44df1dad7faaa229f5e958033ff3883bb408c80e81738d7ac6baa342fa815e4 -->

# IMPACTS auf Deutsch anwenden

Diese Bedienhilfe erklärt nach dem [englischen Sprachvertrag](../language.md) den nutzbaren Weg und die festen Maschinenbegriffe. Englisch ist maßgeblich für aktives Protokoll, Methode, technische Dokumentation und Hinweise für Mitwirkende. Eine englische Quelle, Werkzeugmeldung oder ein importierter Hauptprozess ändert die vereinbarte Arbeitssprache Ihres Unternehmens nicht.

Die Arbeitssprache einmal im Body des Root-`CONTEXT.md` festhalten, für Deutsch mit `Working language: de`. Überschriften, Text und beschreibende Werte übersetzen; Maschinenkennungen, [parsergelesene Labels](../impacts-architect/references/parser-labels.md), Referenzen, Identitäten, Mengen und Einheiten bleiben erhalten.

## Was Menschen lesen

Kundengespräche, Fachdefinitionen, Arbeitsanweisungen, Entwürfe, Erklärungen, Rückfragen und menschliche Entscheidungen werden auf Deutsch verfasst; eine andere Sprache bindet ein Arbeitsschritt nur für eine Ausgabe, deren fachlicher Zweck diese Sprache ist, etwa eine Übersetzung oder ein Exportdokument. Für eine Ausgabe in einer anderen Sprache vor dem Hauptprozess-Commit deren Zielsprache und fachlichen Zweck im Arbeitsschritt-Body erklären oder den Eingabevertrag deklarieren, der beide liefert. Die tatsächliche Zielsprache und den Zweck aus diesem Body oder den deklarierten Eingaben des vorgesehenen Versuchs binden, bevor dieser Versuch öffnet oder ausgeführt wird. Andere Ausgaben verwenden die gebundene Arbeitssprachvorgabe. Anweisungen, Erklärungen, Rückfragen und menschliche Entscheidungen bleiben in der Arbeitssprache; die Ausnahme gilt nur für das erklärte Arbeitsergebnis. Spätere Routeränderungen ändern keine gebundene Arbeit. Eigennamen, notwendige Originalzitate und technische Kennungen dürfen erhalten bleiben. Ihre Bedeutung und Folgen werden bei Bedarf auf Deutsch erklärt. Quellenwerte, Mengen, Einheiten und Identitäten werden durch Übersetzung nicht verändert.

## Deutsche Nutzung durchsetzen

Vor Kundennutzung prüft der Arbeitsschritt die tatsächliche Ausgabe einschließlich eingefügter Werte auf ihre gebundene Sprache und unveränderte fachliche Bedeutung. Der Nachweis bleibt bei der tatsächlich geprüften Ausgabe und ihrer Sprachvorgabe. Bei fehlender, veralteter oder nicht bestandener Prüfung bleibt genau diese Nutzung offen; unabhängig erlaubte Arbeit geht weiter. Eine englische Entscheidungsfrage genügt für einen deutschen Kunden nicht.

Feste Texte kommen aus der passenden versionierten Vorlage. Freitext benötigt die erklärte Sprach- und Bedeutungsprüfung durch den eingerichteten Prüfer oder zuständigen Menschen. Ein Sprachkennzeichen, Wortfilter oder Modellurteil garantiert nicht jeden möglichen Text. Der allgemeine Core-Validator `impacts validate` erkennt keine natürliche Sprache und authentifiziert keine prüfende Person.

Der Import eines Hauptprozesses erhält seine ursprünglichen Bytes und seine Tree-ID; die Übersetzung erzeugt vor deutscher Kundennutzung eine neue Hauptprozess-Revision. Nach geänderten Bytes kann eine Übersetzung die ursprüngliche Tree-ID nicht behalten. Bereits gebundene Vorgänge und Quellen bleiben unverändert. Übersetzungen nennen den Quellenstand; bei Widerspruch bleibt die betroffene Nutzung offen, bis die Bedeutung geklärt ist.

## Deutsche Leseflächen

Englisch enthält die Protokollregeln; deutsche Bedienhilfen und Vorlagen unterstützen die Anwendung. Die folgenden Bedienhilfen nennen jeweils ihren englischen Quellenpfad und SHA-256:

- [Einstieg](readme.de.md)
- [Erster Beitrag](first-win.de.md)
- [Mitwirken](contributing.de.md)
- [Englische Aufgabenrouten und Regelquellen](../CONTEXT.md#task-routes)
