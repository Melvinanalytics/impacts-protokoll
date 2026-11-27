---
type: workspace
protocol: v0.9.0
---

<!-- Translation source: 02_protocol/templates/workspace.md; sha256: 55a550f3a9c01af2b9849446d8ee2c7d4ee736ba69ec50290c2a0f7ca2593960 -->

Working language: de

# IMPACTS-Arbeitsbereich

Kundenarbeit erfolgt in dieser Arbeitssprache nach `02_protocol/language.md`. Jeder `02_protocol/`-Pfad hier bezieht sich auf die unten benannte Protokollquelle und Revision, nicht auf diesen Kundenbaum.

## Quelle, Harness und Heimaten

Vor Anwendung eines Protokollpfads Quelle, Revision und Architect-Einstieg nach der Root-`README.md` der Quelle, Abschnitt „Version and entry points“, festhalten. Fehlt die Quelle nach `init`? Das Paket mit `python -m pip show impacts-protocol` identifizieren und die vollständige Quelle von den [Releases](https://github.com/Melvinanalytics/impacts-protokoll/releases) beziehen; die Paketversion allein nennt keine genaue Revision. Bei Fortsetzung das hier Festgehaltene verwenden. Änderungen an Anweisungen oder Arbeitssprache folgen `02_protocol/impacts-method.md#maintain-agent-instructions`.

- Ort der vollständigen Quelle (Release-Pin im Frontmatter): `<Pfad oder URL>`
- Quell-Commit und lokale Änderungen: `<Commit und jede lokale Änderung>`
- Architect-Einstieg: `<auflösbarer Pfad von 02_protocol/impacts-architect/SKILL.md>`
- Harness und Einrichtungsreferenz, wenn Core-Ausführung gewählt ist: `<Harness und Einrichtungsreferenz, oder nicht gewählt>`
- Fachliche Heimaten: `<Link und Zweck jeder Heimat>`
- Wertschöpfungskette, bei mehr als einem Hauptprozess (`02_protocol/impacts-architect/references/formwahl.md#composition`): `<je Hauptprozess: Links auf Leistung und Auslöser, Einheit, was ihn öffnet, wer sein Ende nutzt>`

`Ablage: <name> <Ort oder System>, <Ort der Zugriffsregel>`: eine nicht eingerückte Body-Zeile je externer Ablage.

`Form: <folder>/ <form> per <unit>`: eine nicht eingerückte Body-Zeile je Top-Level-Ordner (`02_protocol/impacts-architect/references/formwahl.md#folder-structure-by-form`).

Jede Heimat über die Formwahl wählen; Fakten bleiben an ihrer Quelle. Bei vorliegenden Produkten oder Services `02_protocol/impacts-method.md#reverse-engineer-a-product-or-service` anwenden, bevor eine Pipeline angenommen wird. Fachliche Bedeutung nach `02_protocol/ontology.md#author-or-change` aufnehmen oder ändern, nach `02_protocol/ontology.md#use` anwenden. Für Capabilities aus einem Fachrepo oder einer anderen Heimat deren zuständigen Router unter „Fachliche Heimaten“ verlinken und `02_protocol/impacts-architect/references/formwahl.md#capability-orientation` anwenden.

## Routing

Arbeit von reinen Lese-Fragen trennen (`02_protocol/impacts-method.md#load-context-locally-first`). Platzhalterzeilen nur durch befüllte Links ersetzen; unbefüllte Bereiche weglassen.

### Arbeit (erzeugt oder ändert Ausgabe)

| Anliegen | Öffnen | Zusätzlich, nur bei Anlass | Ausgabe und Ziel | Prüfung |
|---|---|---|---|---|
| `<wiederkehrender Job ohne Core-Arbeitsschritt>` | `<Link auf zuständige Datei#Job-Abschnitt>` | `<wenn <beobachtbarer Auslöser>: <Link auf die dann nötige Quelle>>` | `<Artefakt und Zielpfad>` | `<beobachtbare Prüfung>` |
| `<gewählte Core-Pipeline>` | `<Link auf hauptprozesse/<slug>/CONTEXT.md>` | — | `<Vorgangsausgabe>` | `impacts validate` |

Der Standardfall liest nur „Öffnen“; „Zusätzlich“ nennt einen Auslöser und die dann nötige Quelle, so weiß der Bearbeiter des Standardfalls, was er überspringt. Jeder Ebenen-Router folgt `impacts template ebene --language de`.

### Reine Lese-Fragen

Eine reine Lese-Frage geht direkt in diese Tabelle und überspringt die Arbeitsregeln oben.

| Frage zu | Öffnen | Stoppbedingung |
|---|---|---|
| `<Grundlagen, Regeln, Angebote>` | `<Link auf grundlagen/CONTEXT.md>` | `<zitierte Regel und Evidenzstatus>` |
| `<Fälle, Vereinbarungen, Gegenstände>` | `<Link auf records/CONTEXT.md>` | `<zitierter Datensatz und Standzeit>` |
| `<Erfassungen, Kandidaten>` | `<Link auf analyse/CONTEXT.md>` | `<zitierte Analyse und offene Lücken>` |

## Einrichtung

`init` erzeugt `AGENTS.md`, diesen Router, `hauptprozesse/`, `vorgaenge/`, `.gitattributes` (`* -text`, damit ein Checkout gebundene Bytes und Hashes erhält) und eine `.gitignore` für System- und Office-Reste. Fehlende `hauptprozesse/` oder `vorgaenge/` gelten als leer. Ein leerer gültiger Arbeitsbereich ist noch kein ausführbarer Prozess.

`analyse/`, `capabilities/`, `grundlagen/` und `records/` nur mit Inhalt anlegen. Neue oder verschobene Dateien nach `02_protocol/impacts-architect/references/formwahl.md#folder-structure-by-form` und `02_protocol/impacts-architect/references/formwahl.md#data-kinds` platzieren. Fachordner nach `02_protocol/impacts-architect/references/zuschnitt.md#naming` benennen; Core-Bäume, Slugs und Identitäten folgen `02_protocol/binding.md#hauptprozess-tree-rules`.

<a id="tree-clearance-and-imports"></a>
## Tree-Freigaben und Importe

Form der Freigabezeile:

`hauptprozess:<slug> cleared for real work: human:<id>, <YYYY-MM-DD>, git-tree:<oid>, tested by vorgang:<id>[, ...]`

Nur die verantwortliche Person schreibt sie, in ihrem eigenen Commit oder diktiert und bestätigt. Eine abgelöste Zeile löschen; die Git-Historie behält sie. Die Zeile authentifiziert niemanden; der Core prüft sie nicht.

Eine Importzeile je importiertem Tree, außerhalb dieses Trees; Erstimport und geprüfte Übernahme folgen `02_protocol/impacts-method.md#scale`:

`Imported <hauptprozess|capability>:<slug>: source repository <repository>, commit <commit>, tree git-tree:<oid>, source protocol <Fachrepo protocol pin>`

## Betriebsvertrag

1. Für Core-Vorgänge ist der Arbeitsbereichs-Root der Git-Root.
2. Einen Hauptprozess an seiner gewählten Heimat entwerfen; `impacts template <art> --language de` liefert jede `CONTEXT.md`. Aus einem anderen Repository nur nach `02_protocol/impacts-method.md#scale` übernehmen; eine Übersetzung ist eine neue Revision.
3. Vor einem echten Vorgang eine Freigabezeile für den aktuellen Hauptprozess-Tree finden. Fehlt sie, den verantwortlichen Kunden fragen und nichts öffnen. Einen synthetischen Testgegenstand als "synthetischer Testfall" markieren.
4. Vorgänge nach `02_protocol/binding.md#execution` des gepinnten Releases ausführen.
5. Für erforderliche Core-Konformität `impacts validate` ausführen; ein Commit-Gate führt `impacts validate --require-judged` aus, das scheitert, wenn der Pin eine andere Release-Linie nennt. Es prüft nur Struktur (`02_protocol/ontology.md#enforcement-and-completion`) und ersetzt keine Fachprüfung und keine menschliche Entscheidung.
6. Der gebundene Arbeitsschritt-Body liefert Prompt, Operationen, erlaubte Eingriffe und Checks; das eingerichtete Harness lädt deklarierte Eingaben und hält tatsächliche Ergebnisnachweise fest (`02_protocol/impacts-method.md#compose-an-arbeitsschritt`).
7. Jeden wiederkehrenden Job ohne Core-Arbeitsschritt in einem Abschnitt seiner zuständigen Datei festhalten (`02_protocol/impacts-method.md#maintain-agent-instructions`).
8. Agenten erfinden keine `Ablage`, schreiben keine Freigabezeile und erzeugen keine menschliche Entscheidung.
9. Zeigt laufende Arbeit einen nachgewiesenen Mangel oder folgenreiche wiederholte Reibung, den eingetragenen Architect-Einstieg (`Choose a mode`) öffnen und `02_protocol/impacts-method.md#reviewed-correction` anwenden.
