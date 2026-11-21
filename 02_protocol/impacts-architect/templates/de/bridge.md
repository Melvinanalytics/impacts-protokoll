<!-- Translation source: 02_protocol/impacts-architect/templates/bridge.md; sha256: 586fa7e5ee4cb064c244b24f8a0305b031797aedb801b94162dd1f88a8d8c617 -->

# Realitäts- und Leistungsstücklisten-Brücke: <Angebot oder Ergebnisname>

Kompakte einseitige Analyse für `analyse/`, bevor ein stabiler Ablauf besteht; für die tiefe Aufnahme laufender mehrstufiger Arbeit dient [ist-prozess.md](ist-prozess.md). Sie verbindet das, was der Empfänger erhält (`Leistungsstückliste`, siehe `02_protocol/impacts-method.md#leistungsstückliste`), mit rückwärts hergeleiteten Voraussetzungen und beobachteter Unternehmensrealität (`A#`), bevor entschieden wird, was entfällt, zusammengelegt wird, als Job-Abschnitt in seiner zuständigen Datei bleibt oder als `hauptprozesse/`-Pipeline aufgebaut wird. Jede Aussage mit Quelle als `verified`, `reported`, `hypothesis` oder `open` markieren.

## 1. Ergebnisgrenze

- **Einheit:** `<Gegenstand> | <wer wem schuldet> | <Auslöser-Ereignis> | <Enden, negative eingeschlossen>`
- **Kommerzielle Grenze:** `<Angebot | Nachfrage | Lieferung | Beschaffung oder Kapazität>` (`02_protocol/impacts-architect/references/zuschnitt.md#commercial-boundary-cut`)
- **Abnahme (`abnahme`):** `<beobachtbare Bedingungen, unter denen der Empfänger das Ergebnis abnimmt>`
- **Schutzgröße:** `<was nicht leiden darf: Vertraulichkeit, Trennung der Arbeitsräume, Freigabe vor Versand, Belastung>`

## 2. Leistungsstückliste (was der Empfänger erhält)

`C#` ist eine Komponente, `J#` eine Verbindung zwischen Komponenten.

| ID | Element | Abnahme / Prüfung | Evidenz |
|---|---|---|---|
| C1 | `<Lieferbestandteil oder Rahmen>` | `<beobachtbare Prüfung>` | `reported` |
| C2 | `<Lieferbestandteil>` | `<beobachtbare Prüfung>` | `hypothesis` |
| J1 | `<C1 <-> C2: erforderliche Konsistenz, geteilte Kennzahl oder Übergang>` | `<beobachtbare Verbindungsprüfung>` | `open` |

## 3. Rückwärtige Voraussetzungsspur

Jedes `C#` und `J#` rückwärts bis zu seiner Quelle, Regel, Ressource oder Entscheidung verfolgen.

| Ziel | Erforderliche Voraussetzung | Heimat und Arbeitsraum (Grundlage / interner Record / Kunden-Record / Entscheidung) | Inhaber und Zugriff | Evidenz |
|---|---|---|---|---|
| C1 | `<benötigter Fakt, Berechnung oder Vorlage>` | `<Pfad, Arbeitsraum oder externes System>` | `<Inhaber; zugänglich oder Lücke>` | `open` |
| J1 | `<Regel zur Abstimmung von C1 und C2>` | `<Pfad oder Regelinhaber>` | `<Inhaber>` | `open` |

## 4. Realitäts-Überlagerung

Beobachtete Tätigkeiten (`A#`), Wartezeiten und Reibung auf `C#`, `J#` und Schutzgrößen abbilden. Eine Tätigkeit, die keinem davon dient, ist ein `Minimize`-Kandidat.

| Tätigkeit | Beobachtete Arbeit | Dient (`C#` / `J#` / Schutzgröße / keinem) | Reibung, Engpass und Gegenerklärung | Evidenz |
|---|---|---|---|---|
| A1 | `<was heute passiert>` | `C1` | `<Wartezeit, Nacharbeit, Kopie, Suche; und was es sonst erklären könnte>` | `reported` |
| A2 | `<was heute passiert>` | `keinem` | `<Doppelprüfung oder Kanalkopie; und was es sonst erklären könnte>` | `hypothesis` |

## 5. Minimize und Heimatentscheidung

Zielheimat ist eines von: `entfaellt`, ein Job-Abschnitt in der bestehenden zuständigen Datei (`grundlagen/...#<abschnitt>`), `hauptprozesse/<slug>/`, `grundlagen/`, `records/` oder `open`.

| Punkt | Vorgeschlagener Schritt | Zielheimat | Begründung (und offene Frage) |
|---|---|---|---|
| A2 | `entfaellt` | `entfaellt` | `<dient keinem C#, J# und keiner Schutzgröße>` |
| A1 | Als einen wiederkehrenden Job behalten | `<zuständige Datei>#<Job-Abschnitt>` | `<wiederkehrend in einem Durchlauf; kein mehrstufiger Zustand>` |
