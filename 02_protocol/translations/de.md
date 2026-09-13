<!-- Translation source: 02_protocol/language.md; sha256: 4480f36c278bb9acdb271c1138a66416b7440999cd14917e2a2fc39349e91147 -->

# IMPACTS auf Deutsch anwenden

Diese Bedienhilfe übersetzt den [englischen Sprachvertrag](../language.md). Die englische Protokolldefinition bleibt maßgeblich für die Technik; die Arbeitsunterlagen Ihres Unternehmens bleiben Deutsch. Eine englische Quelle, Werkzeugmeldung oder importierte Application ändert diese Arbeitssprache nicht.

## Einstieg mit vorhandenen Dateien

<!-- Translation source: README.md; sha256: 2bc73cf820552e732ed86f7c82517eb645f4731ca9bdb2fd39f7ea3653906444 -->
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

## Optionale technische Nutzung

<!-- Translation source: 02_protocol/impacts-method.md; sha256: b073d71ed69b540d635a45cdf85f736b87e876021d1343336fd903f4d590a65f -->
Fortschritt, Evidenz, offene Punkte und Fortsetzung bleiben bei gewöhnlicher Prozessarbeit in den bestehenden Prozess-, Fall- oder Geschäftsrecords; Versuch, `laufpfad` und Bindung gelten für ausgewählte Core-Läufe.

Die [Methode](../impacts-method.md) und [Formwahl](../impacts-architect/references/formwahl.md#tooling-stopp) bestimmen den Umfang: Maschinenvalidierung wird für eine konkrete benötigte Prüfung aufgerufen, wenn ein geeigneter Prüfer verfügbar ist. Sie ist keine allgemeine Zugangsschranke für Arbeit. Ein fehlendes Werkzeug bedeutet „Prüfung nicht durchgeführt“; eine fehlgeschlagene Prüfung bleibt fehlgeschlagen. Unabhängige erlaubte Vorbereitung geht weiter, während genau die Aussage oder Handlung eingeschränkt bleibt, die den fehlenden Nachweis benötigt. Benennen Sie Fortschritt, Folge und nächste Handlung; Rohdiagnosen bleiben für Betreibende erhalten.

Ist Git bei der Vorbereitung eines Git-gebundenen Laufs nicht verfügbar, bleiben Entwurf, Quellen, Fragen und Definitionsentwurf erhalten und fortsetzbar. Die historische Laufvalidierung wurde nicht durchgeführt; die Vorbereitung bleibt ungebunden und ist kein validierter Lauf. Nächster Schritt: an einem Rechner mit Git und Python-CLI den Application-Vertrag samt erforderlichen Setup-Fällen vervollständigen, die Application am Core-Root committen, den Lauf anhand der [Laufvorlage](../templates/vorgang.md) an den tatsächlichen committed Tree binden und `impacts validate` auf dem Arbeitsbereich ausführen. Das wirkliche Ergebnis erhalten und Fehler vor einer Behauptung validierter Bindung korrigieren. Keine Tree-ID, keinen Hash, keinen Verlauf und keine Freigabe erfinden. Validierung allein beweist weder Ausführung noch fachlichen Erfolg.

Für eine ausgewählte Core-Nutzung erläutert die [technische Anleitung](../../README.md#optional-technical-use) die Python-Installation. Die folgenden Befehle erzeugen oder prüfen Dateien; sie führen keine Kundenarbeit aus:

```sh
impacts init ../mein-arbeitsbereich --language de
impacts template application --language de
impacts template arbeitsschritt --language de
impacts validate ../mein-arbeitsbereich
```

`init` erzeugt einen neuen, leeren Arbeitsbereich; es verweigert ein vorhandenes Ziel. Der Root-Router enthält `Working language: de`. Git wird nicht erzeugt und ist für Application-Strukturprüfung ohne Lauf nicht nötig; die aktuelle historische Laufvalidierung benötigt Git und die committed Application-Bindung. Git-Historie oder Hashes belegen weder die Wahrheit einer Quelle noch eine authentifizierte Entscheidung. `setuptools` wird nur für die Entwicklungs-Packagingtests benötigt. Der [programmierte Angebotslauf](../../06_evaluations/offer-walk/CONTEXT.md) ist eine optionale technische Evaluation mit synthetischen Daten, kein Beweis für die Nutzung durch einen Menschen oder einen Agenten allein aus Dateien.

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
