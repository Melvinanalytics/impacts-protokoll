---
type: workspace
---

<!-- Translation source: 02_protocol/templates/workspace.md; sha256: 2b5a740f703e61e16f855f2325a422d84d0ae3fdc3c0cefd663b746718125ed8 -->

Working language: de

# IMPACTS-Arbeitsbereich

Vor neuer Geschäftsaufnahme die tatsächliche Protokollquelle, Revision und den auflösbaren Architect-Einstieg (`02_protocol/impacts-architect/SKILL.md`) benennen. Jeder `02_protocol/`-Pfad in diesem Workspace bezieht sich auf diese Quelle/Revision, nicht auf den erzeugten Kundenbaum. Dessen Formwahl bestimmt die kleinste passende fachliche Heimat. Diese Heimaten direkt mit ihrem Zweck verlinken; Fakten bleiben an ihrer Quelle. Bei vorliegenden Produkten oder Services zuerst „Reverse-engineer a product or service“ aus der Methode anwenden, bevor eine Pipeline angenommen wird.

Vor Aufnahme, Änderung oder Verwendung fachlicher Begriffe, Beziehungen und Schlussregeln `02_protocol/ontology.md` aus dieser Protokollrevision lesen und den passenden Zweig (Erfassen/Ändern oder Nutzen) anwenden. Die tatsächliche Fachdefinition an ihrer bestehenden Heimat verlinken; Ontologie-Abschluss und ausgeführte Fachchecks werden nicht durch `impacts validate` ersetzt.

## Einrichtung

`init` erzeugt diesen Router, `applications/` und `vorgaenge/`. Vor der Revisionsbindung Git an diesem Root einrichten. Git übernimmt keine leeren Ordner; die Validierung behandelt fehlende Sammlungen `applications/` oder `vorgaenge/` als leer. Vorhandene Sammlungen müssen gültige Inhalte enthalten; keine Platzhalterdateien ergänzen. Fachdateien nach der Formwahl nur für tatsächlichen Inhalt ergänzen. Vor einem echten Vorgang hier das eingerichtete Harness und seine Einrichtungs-/Abhängigkeitsreferenz benennen; Unterstützung für Operationen, Quellzugriffe, Checks, Übergaben und menschliche Grenzen der gewählten Application feststellen. Zugangsdaten bleiben in dieser Ausführungsumgebung. Ein leerer gültiger Workspace ist noch kein ausführbarer Prozess. Die folgenden Regeln für Applications und Vorgänge gelten erst bei einer gewählten Pipeline.

## Betriebsvertrag

1. Workspace-Root ist Git-Root. Ein Vorgang bindet nur einen committeten Application-Tree.
2. Application entwerfen: `impacts template application --language de` zeigt die Schablone des Baums, `impacts template <art> --language de` liefert jede `CONTEXT.md` (hauptprozess, teilprozess, arbeitsschritt). Ordner tragen fachliche Namen: `applications/<hauptprozess>/<teilprozess>/<arbeitsschritt>/CONTEXT.md`; die Rolle steht im `type`, die ID ist `<type>:<ordnername>`. Der Application-Baum enthält nur `CONTEXT.md`-Dateien. Nach dem Commit liefert `git rev-parse HEAD:applications/<slug>` die Revision. Eine Application aus einem anderen Repository kommt als Byte-Kopie von `applications/<slug>/` (`git archive | tar -x`), committet mit Quellcommit und Tree-OID in der Commit-Nachricht; gleiche Bytes erhalten den Tree-OID. Eine Übersetzung erzeugt eine neue Application-Revision.
3. Vorgang öffnen: Zuerst deklarierte Eingaben und Herkunftsnachweise des Einstiegs aus ihren erklärten Quellen materialisieren und prüfen, einschließlich benötigter Regeln/Vorlagen außerhalb der Application. Dann `vorgaenge/<slug>/CONTEXT.md` aus `impacts template vorgang --language de` mit `application_revision: git-tree:<oid>` erstellen. Der erste Laufpfadeintrag ist der Einstieg der Application, Versuch `001`, Status `aktiv`. Eingaben liegen unter `<schritt>/001/input/`; `impacts hash <versuchsordner> <flaeche>...` liefert `eingabe_hash`. Fehlgeschlagene Vorbereitung öffnet keinen Versuch.
4. Versuch mit tatsächlichem Prüfnachweis und passendem Ergebnisweg abschließen: Deklarierte Ausgaben unter `output/` schreiben, `impacts hash` liefert `ausgabe_hash`, `gewaehlte_route` eintragen, Status `abgeschlossen`. Eine deklarierte Fehlerroute trägt das negative Ergebnis; sie erlaubt keine erfolgreiche Nutzung. Eine Schrittroute erfordert den nächsten Eintrag mit gebundenen Eingaben im selben logischen Übergang; eine Route zu `end:<slug>` beendet den Vorgang.
5. Human Gate: der Eintrag bleibt `aktiv`, bis der benannte Mensch `freigabe` mit `by: human:<id>` und `at` schreibt. Kein Agent schreibt `human:<id>`.
6. Warten: Status `wartend` mit `wiedereinstieg` (`ausloeser`, `continuation_ref`). Erlaubte Entwürfe im aktuellen Job dürfen unter `output/` entstehen; gebundene Eingaben, Route und Freigabe bleiben dabei unverändert. Der Body des Vorgangs erklärt vorhandene Ergebnisse, Blockade und nächste erlaubte Arbeit anhand des Laufpfads und der Dateien. Die Fortsetzung schließt denselben Versuch über eine Route ab; neue Eingaben bindet der nächste vorgesehene Versuch. Der Core startet keine parallelen Arbeitsschritte.
7. `impacts validate .` vor jedem Commit. Exit 1 blockiert.
8. Der Core führt keinen Arbeitsschritt aus. Der gebundene Arbeitsschritt-Body liefert den Prompt und benennt Werkzeugoperationen, Versionen, Parameter, erlaubte Wirkungen und Checks. Das eingerichtete Harness lädt deklarierte Eingaben, führt erlaubte Arbeit aus und hält tatsächliche Ergebnisnachweise fest. Es folgt `02_protocol/impacts-method.md`, Abschnitt „Compose an Arbeitsschritt“, und `02_protocol/capabilities.md` in der gebundenen Protokollrevision.

## Arbeitssprache

Kundenarbeit erfolgt ausschließlich auf Deutsch: Aufnahme, Fachdefinitionen, Arbeitsanweisungen, Entwürfe, Rückfragen und Entscheidungen. Maschinenkennungen und Quellenzitate bleiben unverändert; ihre Bedeutung und Nutzungsfolgen werden auf Deutsch erklärt. Die englische Protokollquelle ändert diese Auswahl nicht. `impacts template <art> --language de` liefert deutsche Vorlagen. Vor Kundennutzung prüft der Arbeitsschritt die tatsächliche Ausgabe einschließlich eingefügter Werte gemäß `02_protocol/language.md` der gebundenen Protokollrevision. Fehlender oder nicht bestandener Sprach-/Bedeutungscheck sperrt nur die davon abhängige Nutzung. Sprachvorgabe und Prüfnachweis werden im bestehenden Vertrag und in den deklarierten Laufdateien gebunden.
