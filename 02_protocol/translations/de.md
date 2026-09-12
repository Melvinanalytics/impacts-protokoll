<!-- Translation source: 02_protocol/language.md; sha256: 4480f36c278bb9acdb271c1138a66416b7440999cd14917e2a2fc39349e91147 -->

# IMPACTS auf Deutsch anwenden

Diese Bedienhilfe übersetzt den [englischen Sprachvertrag](../language.md). Die englische Protokolldefinition bleibt maßgeblich für die Technik; die Arbeitsunterlagen Ihres Unternehmens bleiben Deutsch. Eine englische Quelle, Werkzeugmeldung oder importierte Application ändert diese Arbeitssprache nicht.

## Einstieg

<!-- Translation source: README.md; sha256: 406cbab6554dd8f3cfbf41788c5fc242d75a3fb4c5c56c22b18983894fc05464 -->
Das [Ziel von IMPACTS](../../README.md) ist, kleinen und mittleren Unternehmen zu helfen, ihr Geschäft besser zu verstehen, ihre Arbeit zu vereinfachen und KI sowie Data Science zu nutzen, ohne dafür Experten werden zu müssen. Ein passendes Ergebnis kann eine geklärte Kennzahl, ein entfallender Abstimmungsschritt, eine verlässliche Zusage oder die begründete Entscheidung sein, nichts zu automatisieren. Das ist eine Zielaussage; ein nachgewiesener Nutzen braucht Beobachtungen im eigenen Betrieb.

<!-- Translation source: 02_protocol/impacts-method.md; sha256: e368815b13f50cf15f5254299153f2cfebc5c30fa2a50e6998bc8ad512b2e69a -->
Für die fachliche Nutzung erläutern Unternehmensverantwortliche Problem, Ergebnis, Quellen und nötige Entscheidungen; Betreibende richten den technischen Arbeitsbereich mit den folgenden Befehlen ein. Die englische [Methode](../impacts-method.md#readability-and-processing) erklärt diese Rollen- und Verständlichkeitsgrenze.

```sh
impacts init ../mein-arbeitsbereich --language de
impacts template application --language de
impacts template arbeitsschritt --language de
impacts validate ../mein-arbeitsbereich
```

`init` erzeugt einen neuen, leeren Arbeitsbereich; ein vorhandenes Verzeichnis bleibt erhalten. Es führt keine Kundenarbeit aus. Der Root-Router `CONTEXT.md` enthält `Working language: de`. Bei einem vorhandenen Arbeitsbereich wird die bereits vereinbarte deutsche Sprache beibehalten und an dieser einen Stelle benannt. Git wird im Arbeitsbereich eingerichtet, bevor eine Application versioniert wird.

Der Architect ordnet vorhandenes Wissen der kleinsten passenden Form zu. Nur ein klar begrenzter, wiederholbarer Ablauf mit abnehmbarem Ergebnis wird eine Application. Vorhandene Fachdefinitionen werden wiederverwendet. Neue oder geänderte Bedeutung wird an ihrer bestehenden Heimat geklärt; ein neuer Angebotslauf erfasst das Fachmodell nicht erneut.

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

Vor Kundennutzung prüft der Arbeitsschritt die tatsächliche Ausgabe einschließlich eingefügter Werte auf deutsche Sprache und unveränderte fachliche Bedeutung. Der Nachweis gehört zu den vorhandenen Laufdateien. Bei fehlender, veralteter oder nicht bestandener Prüfung bleibt genau diese Nutzung offen; unabhängig erlaubte Vorbereitung geht weiter. Eine englische Entscheidungsfrage genügt für einen deutschen Kunden nicht.

Feste Texte kommen aus der gebundenen deutschen Vorlage. Freitext benötigt die erklärte Sprach- und Bedeutungsprüfung durch den eingerichteten Prüfer oder zuständigen Menschen. Ein Sprachkennzeichen, Wortfilter oder Modellurteil garantiert nicht jeden möglichen Text. `impacts validate` prüft die Core-Struktur; es prüft weder natürliche Sprache noch fachliche Wahrheit oder die Identität einer Person.

Der Mensch entscheidet nur an den erklärten Grenzen. Ein Agent kann einen Entwurf und eine verständliche Entscheidungsfrage vorbereiten; dadurch entsteht keine Versandbefugnis und keine `freigabe`. Fehlende Preise oder Liefernachweise werden als konkrete Lücken benannt, nicht erfunden.

Ein importierter englischer Ablauf wird vor deutscher Kundennutzung übersetzt und als neue Application-Revision gebunden. Seine bisherige Tree-ID kann nach einer Textänderung nicht erhalten bleiben. Bereits gebundene Läufe und Quellen bleiben unverändert. Übersetzungen nennen den Quellenstand; bei Widerspruch bleibt die betroffene Nutzung offen, bis die Bedeutung geklärt ist.

Das [synthetische Unternehmensbeispiel](../impacts-architect/references/datenbezug.md#vom-katalog-über-die-pipeline-zum-ausgefüllten-angebot) zeigt die Verbindung von Produkten, Services, Angebot und wiederverwendbarer Vorlage. Die deutschen Beispieldaten sind keine Kundendaten und keine tatsächlich erteilte Freigabe.

Bei beobachteten Fehlern oder wiederkehrender Reibung führt [Reviewed correction](../impacts-method.md#reviewed-correction) zur bestehenden zuständigen Quelle. Der Ablauf gilt auch für Wissens- und Record-Formen; gebundene frühere Läufe bleiben erhalten.

Die [Prüfung vor menschlichen Gates und geschützten Kundenkontakten](../capabilities.md#signale-und-human-gate) benennt die Voraussetzung für diese Handlungsgrenzen; eine technische Prüfung ersetzt keine menschliche Entscheidung.
