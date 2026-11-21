---
type: workspace
protocol: v0.6.1
---

<!-- Translation source: 02_protocol/templates/workspace.md; sha256: c6318287635a096260c1d6c1c908d2e8356f772d9be798ad4fddd7bc529751e9 -->

Working language: de

# IMPACTS-Arbeitsbereich

Vor Anwendung eines Protokollpfads gemäß Root-`README.md` der vollständigen Protokollquelle, Abschnitt „Version and entry points“, unter „Quelle, Harness und Heimaten“ die tatsächliche Quelle, Revision und den auflösbaren Architect-Einstieg (`02_protocol/impacts-architect/SKILL.md`) benennen. Fehlt diese Quelle nach `init`, das erzeugende Paket mit `python -m pip show impacts-protocol` in seiner Python-Umgebung identifizieren und die zugehörige vollständige Quelle von den [Releases](https://github.com/Melvinanalytics/impacts-protokoll/releases) beziehen. Die Paketversion allein identifiziert keine genaue Quellenrevision. Bei Fortsetzung die hier bereits benannte Quelle/Revision und Arbeitssprache verwenden.

Jeder `02_protocol/`-Pfad in diesem Arbeitsbereich bezieht sich auf diese Quelle/Revision, nicht auf den erzeugten Kundenbaum. Dessen Formwahl bestimmt die kleinste passende fachliche Heimat. Diese Heimaten mit ihrem Zweck unter „Fachliche Heimaten“ verlinken; Fakten bleiben an ihrer Quelle. Bei vorliegenden Produkten oder Services zuerst `02_protocol/impacts-method.md#reverse-engineer-a-product-or-service` anwenden, bevor eine Pipeline angenommen wird.

Vor Aufnahme oder Änderung fachlicher Begriffe, Beziehungen und Schlussregeln `02_protocol/ontology.md#author-or-change` anwenden, vor ihrer Verwendung `02_protocol/ontology.md#use`. Die tatsächliche Fachdefinition an ihrer bestehenden Heimat verlinken.

## Quelle, Harness und Heimaten

Konfigurierte Fakten hier festhalten und den Betriebsvertrag erhalten. Änderungen an Anweisungen oder Arbeitssprache folgen dem anwendbaren geprüften Revisionsweg unter `02_protocol/impacts-method.md#maintain-agent-instructions` einschließlich seiner Abschlussprüfungen.

- Ort der vollständigen Quelle (Herkunft; Release-Pin im Frontmatter): `<Pfad oder URL>`
- Quell-Commit und lokale Änderungen: `<Commit und jede lokale Änderung>`
- Architect-Einstieg: `<auflösbarer Pfad von 02_protocol/impacts-architect/SKILL.md>`
- Harness und Einrichtungsreferenz, wenn Core-Vorgänge ausgeführt werden: `<eingerichtetes Harness und seine Einrichtungsreferenz, oder nicht gewählt>`
- Fachliche Heimaten: `<Link und Zweck jeder Heimat>`
- Wertschöpfungskette, bei mehr als einem Hauptprozess (`02_protocol/impacts-architect/references/formwahl.md#composition`): `<je Hauptprozess eine Zeile: Links auf Leistung und Auslöser-Zeilen; seine Einheit, verlinkt auf die Record-Art; welches Ende oder Außenereignis ihn öffnet; jeder Hauptprozess oder Empfänger, der sein Ende nutzt, auch vorgelagerte>`

`Ablage: <name> <Ort oder System>, <Ort der Zugriffsregel>`: jede externe Ablage auf einer eigenen, nicht eingerückten Body-Zeile deklarieren; Agenten erfinden niemals eine Ablage.

`Form: <folder>/ <form> per <unit>`: eine nicht eingerückte Body-Zeile je Top-Level-Ordner (Formen: `02_protocol/impacts-architect/references/formwahl.md#folder-structure-by-form`).

Bei Nutzung von Capabilities aus einem Fachrepo oder einer anderen fachlichen Heimat deren frühen zuständigen Router unter „Fachliche Heimaten“ verlinken und `02_protocol/impacts-architect/references/formwahl.md#capability-orientation` aus der benannten Protokollquelle anwenden.

## Routing

Aufgaben, die Ausgaben erzeugen oder ändern, von reinen Lese-Fragen trennen (`02_protocol/impacts-method.md#load-context-locally-first`). Platzhalterzeilen nur durch befüllte Links ersetzen; unbefüllte Bereiche bleiben aus den Tabellen draußen.

### Arbeit (erzeugt oder ändert Ausgabe)

| Anliegen | Öffnen | Ausgabe und Ziel | Prüfung |
|---|---|---|---|
| `<wiederkehrender Job ohne Core-Arbeitsschritt>` | `<Link auf zuständige Datei#Job-Abschnitt>` | `<Artefakt und Zielpfad>` | `<beobachtbare Prüfung>` |
| `<gewählte Core-Pipeline>` | `<Link auf hauptprozesse/<slug>/CONTEXT.md>` | `<Vorgangsausgabe>` | `impacts validate` |

### Reine Lese-Fragen

| Frage zu | Öffnen | Stoppbedingung |
|---|---|---|
| `<Grundlagen, Regeln, Angebote>` | `<Link auf grundlagen/CONTEXT.md>` | `<zitierte Regel und Evidenzstatus>` |
| `<Fälle, Vereinbarungen, Gegenstände>` | `<Link auf records/CONTEXT.md>` | `<zitierter Datensatz und Standzeit>` |
| `<Erfassungen, Kandidaten>` | `<Link auf analyse/CONTEXT.md>` | `<zitierte Analyse und offene Lücken>` |

## Einrichtung

`init` erzeugt den Agenteneinstieg `AGENTS.md`, diesen Router, `hauptprozesse/`, `vorgaenge/`, `.gitattributes` (`* -text`, damit ein Checkout gebundene Bytes und ihre Hashes unverändert lässt) und eine `.gitignore` für System- und Office-Reste (`Thumbs.db`, `desktop.ini`, `~$*`), die die Ebenenprüfung überspringt. Bevor ein Core-Vorgang eine Revision bindet, Git an diesem Root einrichten. Git übernimmt keine leeren Ordner; die Validierung behandelt fehlende Sammlungen `hauptprozesse/` oder `vorgaenge/` als leer. Vorhandene Sammlungen müssen gültige Inhalte enthalten; keine Platzhalterdateien ergänzen. Fachdateien nach der Formwahl nur für tatsächlichen Inhalt ergänzen; `analyse/` entsteht erst, wenn Analyse es benötigt. Für Stufenbefugnis und Kandidatenplatzierung `02_protocol/impacts-architect/references/formwahl.md#data-kinds` verwenden. Vor einem Core-Vorgang unter „Quelle, Harness und Heimaten“ das eingerichtete Harness (`02_protocol/binding.md#history-retention`) und seine Einrichtungs-/Abhängigkeitsreferenz benennen; Unterstützung für Operationen, Quellzugriffe, Checks, Übergaben und menschliche Grenzen des gewählten Hauptprozesses feststellen, einschließlich erforderlicher Aufbewahrung und Prüfung der Historie nach diesem Zuständigkeitsvertrag. Zugangsdaten bleiben in dieser Ausführungsumgebung. Ein leerer gültiger Arbeitsbereich ist noch kein ausführbarer Prozess.

Für gewählte Core-Verträge für Hauptprozesse und Vorgänge (`02_protocol/impacts-architect/references/formwahl.md#tooling-stop`) stehen die Bäume in `02_protocol/binding.md#hauptprozess-tree-rules`. `analyse/`, `capabilities/`, `grundlagen/` und `records/` entstehen erst mit Inhalt.

Für neue oder verschobene Dateien und Ordner Form und Heimat über `02_protocol/impacts-architect/references/formwahl.md#folder-structure-by-form` wählen. Fachordner nach `02_protocol/impacts-architect/references/zuschnitt.md#naming` benennen; für die Benennung von Core-Slugs und Identitäten `02_protocol/binding.md#hauptprozess-tree-rules` verwenden.

```text
<workspace>/
├── AGENTS.md                          # init: Agenteneinstieg
├── CONTEXT.md                         # init: Router und Protokoll-Pin
├── hauptprozesse/                      # init
├── vorgaenge/                          # init
├── analyse/                           # erste Erfassung
├── capabilities/                      # verdiente wiederverwendbare Operation
├── grundlagen/                        # Grundlagen ohne einzelnen zuständigen Schritt
└── records/                           # erster Datensatz
```

`init` legt `analyse/` nicht an. Jede Record-Art hat ihren eigenen Ordner unter `records/` und beginnt als eine Tabelle; sobald eine Instanz einen eigenen Ordner verdient, wandert die Tabelle in die `CONTEXT.md` der Art; ein Arbeitsbereich mit nur einer Record-Art darf seine Tabelle direkt in `records/` führen (`02_protocol/impacts-architect/references/formwahl.md#folder-structure-by-form`). `grundlagen/` enthält nur Grundlagen, die kein einzelner Schritt besitzt.

<a id="tree-clearance-and-imports"></a>
## Tree-Freigaben und Importe

Form der Freigabezeile:

`hauptprozess:<slug> cleared for real work: human:<id>, <YYYY-MM-DD>, git-tree:<oid>, tested by vorgang:<id>[, ...]`

Eine abgelöste Zeile bleibt durchgestrichen erhalten. Agenten schreiben niemals eine Freigabezeile. Die verantwortliche Person schreibt sie in ihrem eigenen Commit oder diktiert und bestätigt sie. Die Zeile authentifiziert niemanden; der Core prüft sie nicht.

Hier steht pro importiertem Tree eine Importzeile neben seinen Freigabezeilen:

`Imported <hauptprozess|capability>:<slug>: source repository <repository>, commit <commit>, tree git-tree:<oid>, source protocol <Fachrepo protocol pin>`

Erstimport oder geprüfte Übernahme folgen `02_protocol/impacts-method.md#scale`. Der Nachweis bleibt außerhalb des importierten Trees; der Core prüft ihn nicht.

## Betriebsvertrag

1. Für Core-Vorgänge ist der Arbeitsbereichs-Root der Git-Root.
2. Hauptprozess an der durch `02_protocol/impacts-architect/references/formwahl.md#data-kinds` gewählten Heimat entwerfen: `02_protocol/binding.md#hauptprozess-tree-rules` liefert Schablone und Regeln des Baums, `impacts template <art> --language de` liefert jede `CONTEXT.md` (hauptprozess, teilprozess, arbeitsschritt). Nach dem Commit liefert `git rev-parse HEAD:hauptprozesse/<slug>` die Revision. Einen Hauptprozess aus einem anderen Repository nur nach dem Verfahren in `02_protocol/impacts-method.md#scale` übernehmen; eine Übersetzung erzeugt eine neue Hauptprozess-Revision.
3. Vor einem echten Vorgang unten eine Freigabezeile für den aktuellen Hauptprozess-Tree finden. Fehlt sie, den verantwortlichen Kunden fragen und nichts öffnen. Einen synthetischen Testgegenstand als "synthetischer Testfall" markieren.
4. Vorgänge nach `02_protocol/binding.md#execution` des gepinnten Releases ausführen.

5. Für erforderliche Core-Konformität `impacts validate` im gewählten Umfang ausführen. Die Core-Grenze anwenden (`02_protocol/ontology.md#enforcement-and-completion`).
6. Unter der Core-Grenze aus Punkt 5 liefert der gebundene Arbeitsschritt-Body den Prompt und benennt Werkzeugoperationen, Versionen, Parameter, erlaubte Eingriffe und Checks. Das eingerichtete Harness lädt deklarierte Eingaben, führt erlaubte Arbeit aus und hält tatsächliche Ergebnisnachweise fest. Es folgt `02_protocol/impacts-method.md#compose-an-arbeitsschritt` und `02_protocol/binding.md`.
7. Die Zeilen dieses Routers nach `02_protocol/impacts-method.md#load-context-locally-first` schreiben und Arbeit von reinen Lese-Fragen trennen. Jeden wiederkehrenden Job ohne Core-Arbeitsschritt in einem Abschnitt seiner zuständigen Datei nach `02_protocol/impacts-method.md#maintain-agent-instructions` festhalten.
8. Zeigt laufende Arbeit einen nachgewiesenen Mangel oder folgenreiche wiederholte Reibung in diesem Arbeitsbereich, den eingetragenen Architect-Einstieg (`Choose a mode`) öffnen und `02_protocol/impacts-method.md#reviewed-correction` anwenden.

## Arbeitssprache

Kundenarbeit erfolgt auf Deutsch: Aufnahme, Fachdefinitionen, Arbeitsanweisungen, Entwürfe, Rückfragen und Entscheidungen; eine andere Sprache bindet ein Arbeitsschritt nur, soweit `02_protocol/language.md` es erlaubt. Maschinenkennungen und Quellenzitate bleiben unverändert; ihre Bedeutung und Nutzungsfolgen werden auf Deutsch erklärt. Die englische Protokollquelle ändert diese Auswahl nicht. `impacts template <art> --language de` liefert deutsche Vorlagen. Vor Kundennutzung prüft der Arbeitsschritt die tatsächliche Ausgabe einschließlich eingefügter Werte gemäß `02_protocol/language.md#enforce-at-use-boundaries`. Fehlender oder nicht bestandener Sprach-/Bedeutungscheck sperrt nur die davon abhängige Nutzung. Sprachvorgabe und Prüfnachweis werden im bestehenden Vertrag und in den deklarierten Vorgangsdateien gebunden.
