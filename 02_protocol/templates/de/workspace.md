---
type: workspace
---

<!-- Translation source: 02_protocol/templates/workspace.md; sha256: a75e14fa053766bfabaed6a76cb7302f3c6e07da9f16262147a3e337eb34cb3e -->

Working language: de

# IMPACTS-Arbeitsbereich

Vor neuer Geschäftsaufnahme gemäß Root-`README.md` der vollständigen Protokollquelle, Abschnitt „Version and entry points“, unter „Quelle, Harness und Heimaten“ die tatsächliche Quelle, Revision und den auflösbaren Architect-Einstieg (`02_protocol/impacts-architect/SKILL.md`) benennen. Fehlt diese Quelle nach `init`, das erzeugende Paket mit `python -m pip show impacts-protocol` in seiner Python-Umgebung identifizieren und die zugehörige vollständige Quelle von den [Releases](https://github.com/Melvinanalytics/impacts-protokoll/releases) beziehen. Die Paketversion allein identifiziert keine genaue Quellenrevision. Bei Fortsetzung die hier bereits benannte Quelle/Revision und Arbeitssprache verwenden.

Jeder `02_protocol/`-Pfad in diesem Workspace bezieht sich auf diese Quelle/Revision, nicht auf den erzeugten Kundenbaum. Dessen Formwahl bestimmt die kleinste passende fachliche Heimat. Diese Heimaten mit ihrem Zweck unter „Fachliche Heimaten“ verlinken; Fakten bleiben an ihrer Quelle. Bei vorliegenden Produkten oder Services zuerst `02_protocol/impacts-method.md#reverse-engineer-a-product-or-service` anwenden, bevor eine Pipeline angenommen wird.

Vor Aufnahme oder Änderung fachlicher Begriffe, Beziehungen und Schlussregeln `02_protocol/ontology.md#author-or-change` anwenden, vor ihrer Verwendung `02_protocol/ontology.md#use`. Die tatsächliche Fachdefinition an ihrer bestehenden Heimat verlinken.

## Quelle, Harness und Heimaten

Konfigurierte Fakten hier festhalten und den Betriebsvertrag erhalten. Änderungen an Anweisungen oder Arbeitssprache folgen dem anwendbaren geprüften Revisionsweg unter `02_protocol/impacts-method.md#maintain-agent-instructions`.

- Protokollquelle: `<verwendete vollständige Quelle>`
- Revision und lokale Änderungen: `<Tag oder Commit und jede lokale Änderung>`
- Architect-Einstieg: `<auflösbarer Pfad von 02_protocol/impacts-architect/SKILL.md>`
- Harness und Einrichtungsreferenz, wenn Core-Vorgänge ausgeführt werden: `<eingerichtetes Harness und seine Einrichtungsreferenz, oder nicht gewählt>`
- Fachliche Heimaten: `<Link und Zweck jeder Heimat>`

## Einrichtung

`init` erzeugt diesen Router, `applications/`, `vorgaenge/` und `.gitattributes` (`* -text`, damit ein Checkout gebundene Bytes und ihre Hashes unverändert lässt). Bevor ein Core-Vorgang eine Revision bindet, Git an diesem Root einrichten. Git übernimmt keine leeren Ordner; die Validierung behandelt fehlende Sammlungen `applications/` oder `vorgaenge/` als leer. Vorhandene Sammlungen müssen gültige Inhalte enthalten; keine Platzhalterdateien ergänzen. Fachdateien nach der Formwahl nur für tatsächlichen Inhalt ergänzen. Vor einem Core-Vorgang unter „Quelle, Harness und Heimaten“ das eingerichtete Harness (`02_protocol/capabilities.md#responsibilities`) und seine Einrichtungs-/Abhängigkeitsreferenz benennen; Unterstützung für Operationen, Quellzugriffe, Checks, Übergaben und menschliche Grenzen der gewählten Application feststellen. Zugangsdaten bleiben in dieser Ausführungsumgebung. Ein leerer gültiger Workspace ist noch kein ausführbarer Prozess. Die folgenden Regeln gelten für gewählte Core-Verträge für Applications und Vorgänge gemäß `02_protocol/impacts-architect/references/formwahl.md#tooling-stopp`.

## Betriebsvertrag

1. Für Core-Vorgänge ist der Workspace-Root der Git-Root. Ein Vorgang bindet nur einen committeten Application-Tree.
2. Application entwerfen: `impacts template application --language de` zeigt die Schablone des Baums, `impacts template <art> --language de` liefert jede `CONTEXT.md` (hauptprozess, teilprozess, arbeitsschritt). Ordner tragen fachliche Namen: `applications/<hauptprozess>/<teilprozess>/<arbeitsschritt>/CONTEXT.md`; die Rolle steht im `type`, die ID ist `<type>:<ordnername>`. Der Application-Baum enthält nur `CONTEXT.md`-Dateien. Nach dem Commit liefert `git rev-parse HEAD:applications/<slug>` die Revision. Eine Application aus einem anderen Repository nur nach dem Verfahren in `02_protocol/impacts-method.md#scale` übernehmen; eine Übersetzung erzeugt eine neue Application-Revision.
3. Vorgang öffnen: Zuerst deklarierte Eingaben und Herkunftsnachweise des Einstiegs aus ihren erklärten Quellen materialisieren und prüfen, einschließlich benötigter Regeln/Vorlagen außerhalb der Application. Dann `vorgaenge/<vorgang>/CONTEXT.md` aus `impacts template vorgang --language de` mit `application_revision: git-tree:<oid>` erstellen. Der erste Laufpfadeintrag ist der Einstieg der Application, Versuch `001`, Status `aktiv`. Eingaben liegen unter `<arbeitsschritt>/001/input/`; `impacts hash <versuchsordner> <jeder eingaben-Pfad>...` liefert `eingabe_hash`. Fehlgeschlagene Vorbereitung öffnet keinen Versuch.
4. Versuch mit tatsächlichem Prüfnachweis und passendem Ergebnisweg abschließen: Deklarierte Ausgaben unter `output/` schreiben, `impacts hash <versuchsordner> <jeder ausgaben-Pfad>...` liefert `ausgabe_hash`, den `routen`-Schlüssel des tatsächlichen `pruefung`-Ergebnisses als `gewaehlte_route` eintragen, Status `abgeschlossen`. Eine deklarierte Fehlerroute trägt das negative Ergebnis; sie erlaubt keine erfolgreiche Nutzung. Eine Schrittroute erfordert den nächsten Eintrag mit gebundenen Eingaben im selben logischen Übergang; eine Route zu `end:<slug>` beendet den Vorgang.
5. Human Gate: der Eintrag bleibt `aktiv`, bis die Entscheidung des benannten Menschen ihn nach Punkt 4 abschließt, mit `freigabe` (`by: human:<id>` und `at: "<JJJJ-MM-TT>T<hh:mm:ss>+<hh:mm>"`, in Anführungszeichen, mit Offset) neben `gewaehlte_route` und `ausgabe_hash`. Belegte menschliche Entscheidungen nur nach `02_protocol/capabilities.md#signale-und-human-gate` erfassen.
6. Warten: Status `wartend` mit `wiedereinstieg` (`ausloeser`, `continuation_ref`). Erlaubte Entwürfe im aktuellen Job dürfen unter `output/` entstehen; gebundene Eingaben, Route und Freigabe bleiben dabei unverändert. Der Body des Vorgangs erklärt vorhandene Ergebnisse, Blockade und nächste erlaubte Arbeit anhand des Laufpfads und der Dateien. Die Fortsetzung schließt denselben Versuch über eine Route ab; neue Eingaben bindet der nächste vorgesehene Versuch. Der Core startet keine parallelen Arbeitsschritte.
7. Für erforderliche Core-Konformität `impacts validate` im gewählten Umfang ausführen. Es prüft nur die Core-Struktur (`02_protocol/ontology.md#enforcement-and-completion`), daher belegt Exit 0 nichts darüber hinaus, auch nicht, dass `gewaehlte_route` zum tatsächlichen `pruefung`-Ergebnis passt; den Rest verantworten der unter „Prüfung“ jedes Schritts benannte Prüfer und das eingerichtete Harness. Ein fehlgeschlagener oder nicht ausgeführter erforderlicher Check beschränkt die davon abhängige Aussage oder Handlung.
8. Der Core führt keinen Arbeitsschritt aus. Der gebundene Arbeitsschritt-Body liefert den Prompt und benennt Werkzeugoperationen, Versionen, Parameter, erlaubte Wirkungen und Checks. Das eingerichtete Harness lädt deklarierte Eingaben, führt erlaubte Arbeit aus und hält tatsächliche Ergebnisnachweise fest. Es folgt `02_protocol/impacts-method.md#compose-an-arbeitsschritt` und `02_protocol/capabilities.md`.

## Arbeitssprache

Kundenarbeit erfolgt auf Deutsch: Aufnahme, Fachdefinitionen, Arbeitsanweisungen, Entwürfe, Rückfragen und Entscheidungen; eine andere Sprache bindet ein Arbeitsschritt nur, soweit `02_protocol/language.md` es erlaubt. Maschinenkennungen und Quellenzitate bleiben unverändert; ihre Bedeutung und Nutzungsfolgen werden auf Deutsch erklärt. Die englische Protokollquelle ändert diese Auswahl nicht. `impacts template <art> --language de` liefert deutsche Vorlagen. Vor Kundennutzung prüft der Arbeitsschritt die tatsächliche Ausgabe einschließlich eingefügter Werte gemäß `02_protocol/language.md#enforce-at-use-boundaries`. Fehlender oder nicht bestandener Sprach-/Bedeutungscheck sperrt nur die davon abhängige Nutzung. Sprachvorgabe und Prüfnachweis werden im bestehenden Vertrag und in den deklarierten Laufdateien gebunden.
