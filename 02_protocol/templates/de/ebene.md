<!-- Translation source: 02_protocol/templates/ebene.md; sha256: 541bf4c9183b3eb9ae34c44bdb87e6ca1c1319576441beb7a18cc94f1305eca7 -->

# <Name der Ebene>

<!-- Ebenen-Router: eine CONTEXT.md je Ebene einer Record Library, eines Knowledge Bundle oder einer Context Map; ein Router für Capability, Tool oder Check folgt demselben Aufbau. Aufbau nach der CONTEXT.md-Anatomie im ICM Workspace Blueprint (_examples/03-context-md-anatomy.md); 25 bis 80 Zeilen sind ein Richtwert, keine Regel. `impacts validate` prüft die Form-Zeile, dass dieser Router jeden Eintrag der Ebene relativ verlinkt, dass ein Ebenen-Router bei jeder Zahl von Einträgen die Überschriften Übersicht und Was laden enthält und dass der Router, außer dem einer Record Library oder Context Map, höchstens 24.000 Bytes groß ist; andere Überschriften prüft es nicht. Jede nicht befüllte Platzhalterzeile löschen. -->

`Form: <Form> per <Einheit>`: diese Zeile nur dann ohne Einrückung und ohne Backticks schreiben, wenn die Ebene sich selbst deklariert; sonst deklariert sie ihr Elternrouter.

## Was hier liegt

`<Ein oder zwei Sätze: was diese Ebene hält, wer sie befüllt, wer sie liest.>`

## Aufruf und Prüfung

Nur in einem Router für Capability, Tool oder Check; in einem Ebenen-Router diesen Abschnitt löschen.

- Aufruf: `<Befehl oder Operation mit ihren Eingaben>`
- Prüfung, bevor das Ergebnis zählt: `<Prüfung, wo sie berichtet, was ein Fehlschlag anhält>`

## Was laden

| Anliegen | Öffnen | Nicht laden |
|---|---|---|
| `<Anliegen im Wortlaut der Arbeit>` | `<relativer Link auf <eintrag>/ oder <eintrag>/CONTEXT.md>` | `<naheliegender Eintrag, den dieses Anliegen überspringt, und warum>` |

## Übersicht

Eine Zeile je Eintrag; jede Zeile verlinkt den Eintrag mit relativem Pfad. Ein fehlender Link ist ein Prüfbefund.

Optional, nur wenn ein Werkzeug Zeilen in diese Tabelle schreibt: `<!-- impacts:table-contract heading="Übersicht" columns="Eintrag, Stand und Quelle" -->` ohne Backticks in eine eigene Zeile dieses Routers setzen und die Spalten nennen, die das Werkzeug braucht. `impacts validate` schlägt dann fehl, wenn eine Spalte umbenannt wird oder fehlt.

| Eintrag | Was es ist | Schreiber | Stand und Quelle |
|---|---|---|---|
| `<relativer Link auf <eintrag>/ oder <eintrag>/CONTEXT.md>` | `<was ein Eintrag hält>` | `<Person oder Werkzeug, das Einträge anlegt>` | `<Evidenzlabel, Stichtag, Quelle>` |

## Regeln

- `Wenn <beobachtbare Bedingung>, dann <Handlung>; Quelle: <relativer Link>.`

## Werkzeuge

| Werkzeug | Wann | Erlaubte Wirkung |
|---|---|---|
| `<Werkzeug oder Capability>` | `<beobachtbarer Auslöser, nicht „verfügbar“>` | `<Dateien, die es schreiben oder ändern darf>` |

## Nicht tun

Nur beobachtete Fehler, jeweils mit Datum und Beleg; Zeilen kommen hinzu, wenn ein Fehler passiert, nie vorab.

- `<beobachteter Fehler> (gesehen am <JJJJ-MM-TT>, Beleg: <relativer Link>)`
