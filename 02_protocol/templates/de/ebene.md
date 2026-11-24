<!-- Translation source: 02_protocol/templates/ebene.md; sha256: 400480ad6b18f47916b8f2167036263f89d568fbf3ee88149a308f758dc102b5 -->

# <Name der Ebene>

<!-- Ebenen-Router: eine CONTEXT.md je Ebene einer Record Library oder eines Knowledge Bundle. Aufbau nach der CONTEXT.md-Anatomie im ICM Workspace Blueprint (_examples/03-context-md-anatomy.md); 25 bis 80 Zeilen sind ein Richtwert, keine Regel. `impacts validate` prüft nur die Form-Zeile und dass dieser Router jeden Eintrag der Ebene relativ verlinkt; die Überschriften prüft es nicht. Jede nicht befüllte Platzhalterzeile löschen. -->

`Form: <Form> per <Einheit>`: diese Zeile nur dann ohne Einrückung und ohne Backticks schreiben, wenn die Ebene sich selbst deklariert; sonst deklariert sie ihr Elternrouter.

## Was hier liegt

`<Ein oder zwei Sätze: was diese Ebene hält, wer sie befüllt, wer sie liest.>`

## Was laden

| Anliegen | Öffnen | Nicht laden |
|---|---|---|
| `<Anliegen im Wortlaut der Arbeit>` | `<relativer Link auf <eintrag>/ oder <eintrag>/CONTEXT.md>` | `<naheliegender Eintrag, den dieses Anliegen überspringt, und warum>` |

## Übersicht

Eine Zeile je Eintrag; jede Zeile verlinkt den Eintrag mit relativem Pfad. Ein fehlender Link ist ein Prüfbefund.

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
