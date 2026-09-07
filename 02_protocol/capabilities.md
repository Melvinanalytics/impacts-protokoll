# Capability-Regel

Diese Datei ist die einzige öffentliche Begriffs- und Verhaltensautorität für Capabilities in IMPACTS.

Eine **Capability** ist eine begrenzte, wiederverwendbare Verarbeitung innerhalb eines Arbeitsschritts. Sie nimmt deklarierte Eingaben entgegen und erzeugt ein sichtbares, prüfbares Ergebnis. Sie kann Recherche, Analyse, Transformation, Berechnung oder einen engen Werkzeugaufruf enthalten.

Eine Capability ist kein sechster Core-Typ. D-10 bleibt bestehen: Weder Core-Schema noch allgemeiner Validator binden oder führen Capabilities aus. Die folgenden Regeln sind Markdown-Konvention und Verantwortung des Fachrepo-, Workspace- oder Vorgangs-Harnesses.

## Begriffe

| Begriff | Bedeutung |
|---|---|
| Herkunft | fachliche Quelle eines Werts, etwa ERP, Rezeptur oder Produktionsleitung |
| Ursprung | konkrete lokale Laufdatei oder externe Referenz, aus der der Lauf gelesen hat |
| Snapshot | im Lauf tatsächlich verwendete Bytes |
| Datenkontrolle | für einen Nutzungszweck verlangtes Verfahren |
| Kontrollnachweis | Beleg der im konkreten Lauf ausgeführten Kontrolle |
| `pruefung` | Bewertung der beobachtbaren Arbeitsschrittausgabe |
| technische Nutzungsbedingung | Bedingung, unter der ein Capability-Ergebnis fachlich belastbar ist |
| Nutzungsgrenze | erlaubter Geschäftszweck der Arbeitsschrittausgabe |

`verified`, aktuell, kontrolliert und verbindlich nutzbar sind verschiedene Aussagen.

## Wann extrahieren

Jede Berechnung verweist auf ihre sanktionierte Rechenregel. Eine Verarbeitung erhält nur dann eine eigene Capability-Heimat, wenn mindestens eins gilt:

- mehrere Arbeitsschritte oder Applications brauchen dieselbe Operation;
- sie besitzt einen eigenen deterministischen Kern;
- sie besitzt eigene Quellen-, Aktualitäts- oder Prüfregeln;
- sie soll unabhängig vom Arbeitsschritt versioniert werden.

Sonst bleibt sie im Arbeitsschritt. Capability-Heimat ist `capabilities/<slug>/` im Fachrepo oder Workspace, außerhalb des Core und der Application.

## Rechen-Capability

Eine Rechen-Capability besitzt einen kompakten, versionsgebundenen Fachvertrag:

1. Operation und Zweck;
2. Parameterschema mit Einheiten, Granularität und Zeitbezug;
3. sanktionierte Methode oder Formel;
4. Fehler- und Blockierfälle einschließlich der Datenanforderungen je Nutzung;
5. deterministischen Prüfer;
6. sichtbares Belegformat;
7. Fixtures;
8. Sensitivitätsfälle nur bei relevanter Ergebnistoleranz.

Definition, Formel, Prüfer, Belegformat und Fixtures liegen unter derselben gebundenen Capability-Revision. Ein Git-Tree-OID bindet diese Dateien, aber keine Interpreter- oder Bibliotheksumgebung. Wo die Umgebung das Ergebnis beeinflusst, nennt der Fachvertrag sie als technische Nutzungsbedingung.

## Capability-Aufruf

Der Arbeitsschritt wiederholt den Fachvertrag nicht. Er bindet lokal:

```markdown
Aufruf-ID: liefertermin-1
Capability-Pfad: capabilities/liefertermin/CONTEXT.md
Capability-Revision: git-tree:<oid>
Operation: liefertermin-berechnen
```

Bei genau einem Aufruf darf die ID als `<arbeitsschritt-slug>-1` abgeleitet werden; mehrere Aufrufe erhalten explizite IDs. Autorität ist das Tupel aus Aufruf-ID, auflösbarem Pfad, Tree-OID und Operation in der gebundenen Application-Revision. Vor dem Vorgang bindet das Harness eine erreichbare Workspace-Revision, löst darin das Elternverzeichnis des Capability-Pfads auf und verlangt denselben Tree-OID. Es führt diesen aufgelösten Tree aus und schreibt Workspace-Revision sowie Aufruftupel in den normalen Capability-Beleg. Die Capability bescheinigt ihre eigene Herkunft nicht.

Der Tree-OID bindet Identität, nicht Vertrauenswürdigkeit. Ein produktives Harness führt nur fachlich freigegebene Capability-Revisionen aus. Isolation, Berechtigungen, Geheimnisse und Laufzeitumgebung liegen außerhalb des IMPACTS-Core.

IMPACTS kennt an dieser Grenze nur:

```text
Capability-Aufruf -> sichtbare Ausgabe -> pruefung -> Route
```

## Data Governance

Die Application nennt erwartete Herkunft und Mindestkontrolle. Erst der Vorgang belegt tatsächliche Daten.

Eine maschinenlesbare Minimalbindung darf direkt beim Aufruf stehen:

```markdown
### Quellenanforderung

- Quell-Eingabe: `input/rezeptur.md`
- Herkunft: `freigegebene Rezeptur`
- Ursprung: `grundlagen/rezeptur.md`
- Stand: `git:<commit>`
- Erforderliche Kontrolle: `revisionsgebunden materialisieren`
```

Der Block wird für jede stabile Quell-Eingabe wiederholt. Das Harness liest die Sollbindung aus derselben gebundenen Application-Revision wie den Capability-Aufruf. Der Vorgang schreibt die tatsächlich gelesenen Bytes und den Kontrollnachweis separat unter `input/`.

| Objekt | Laufbezogene Aussagen |
|---|---|
| Eingabe | Evidenzstatus, Herkunft, Ursprung/Snapshot, Stand, erforderliche Datenkontrolle und Kontrollnachweis |
| Capability-Ergebnis | offene Annahmen und technische Nutzungsbedingungen |
| Arbeitsschrittausgabe | Nutzungsgrenze des Geschäftszwecks |
| Route | tatsächliche Prozessfolge |

Zulässige Evidenzlabels bleiben `verified`, `reported`, `hypothesis` und `open`. Eine erforderliche Kontrolle wie „vor Zusage manuell abgleichen“ bleibt getrennt vom tatsächlichen Nachweis wie „bestätigt durch `human:produktionsplanung` am ...“. Diese Attribution schreibt im realen Vorgang nur der benannte Mensch.

Kontrollstärke folgt Volatilität, Wiederholung, Schadenshöhe, Ergebnistoleranz, Reproduzierbarkeit und vorhandener Infrastruktur. Revisionsbindung, manuelle Bestätigung und automatische Überwachung sind Praktiken, keine Reifestufen. Kleine Betriebe dürfen mit Dateien und dokumentierten Bestätigungen arbeiten.

## Snapshot und Herkunftsnachweis

Vor Ausführung liegen die kleinste fachlich ausreichende, reproduzierbar herleitbare Quelle oder Projektion und eine separate `*-herkunft.md` unter dem Versuch in `input/`. Beide sind deklarierte Eingaben und werden vom bestehenden Eingabe-Flächenhash gebunden.

- Direkte Kopie liest die Bytes aus der gebundenen Revision, etwa `git show <commit>:<pfad>`, nicht aus dem aktuellen Working Tree.
- Projektion nennt Quellrevision, Quellpfad, Quelldigest und reproduzierbare Extraktionsregel.
- Nicht deterministische Extraktion nennt ihre menschliche oder capability-spezifische Bestätigung.

`Content-Digest` ist kleingeschriebenes hexadezimales SHA-256 über rohe Datei-Bytes. Er ist nicht der aggregierte Flächenhash.

## Sichtbare Ausgabe und Übergabe

Der Capability-Beleg bleibt eine normale Datei unter `output/`; sein Format gehört der Capability. Er zeigt gebundene Rechenregel, verwendete Eingaben, Ergebnis, ausgeführte Checks, Annahmen und technische Nutzungsbedingungen. Eine Parametertabelle oder gleichwertige Blockliste ist zulässig. Es entsteht kein Receipt-Schema.

Eine lokale Schrittübergabe hat zwei Belege:

1. Application: erwartete Abbildung `A/output/datei.md -> B/input/datei.md`, genau einmal im erzeugenden Arbeitsschritt neben Ausgabe und Route.
2. Vorgang: bytegleiche Consumer-Datei plus `*-herkunft.md` mit versuchsqualifiziertem, zum aktuellen Vorgang relativem Ursprung und gleichem Content-Digest.

Producer-`ausgabe_hash` und Consumer-`eingabe_hash` binden ihre jeweiligen Oberflächen. Weil relative Pfade eingehen, werden sie nicht verglichen und bilden keine Hashkette. Der allgemeine Validator prüft auch Herkunfts- und Digestbehauptungen nicht; ein lokales Harness kann dies tun, wenn der Nutzungszweck es verlangt.

## Signale und Human Gate

- `hypothesis` nennt Wirkung und konkreten Validierungsauftrag.
- `open` bleibt ohne Ersatzwert und erzeugt eine gezielte Frage.
- Eine Warnung ohne Nutzungsgrenze, Prüfauftrag, Frage oder blockierende Folge genügt nicht.

Vor `open()` eines Schritts mit `gate: human` prüft das ausführende Harness dessen deklarierte Eingaben und erforderliche Kontrollnachweise. Scheitert diese Vorbedingung, bleibt der bisherige Lauf unverändert. Nach menschlicher Bearbeitung bewertet `pruefung` weiterhin nur die Ausgabe des Gate-Schritts. `freigegeben` oder `abgelehnt` und `freigabe` stammen im realen Vorgang ausschließlich vom Menschen.

Der allgemeine Validator erzwingt diese Vorbedingung nicht und authentifiziert keine Person. Ein synthetischer Walk kann nur zeigen, dass `open()` keine Route oder Freigabe schreibt und der Abschluss eine extern zugeführte Entscheidungs-Fixture benötigt.

## Transport

Eine Application ohne Capability-Aufruf wird allein transportiert. Bei einem Capability-Aufruf wird zusätzlich jedes benötigte Verzeichnis `capabilities/<slug>/` aus derselben Fachrepo-Revision an denselben relativen Pfad materialisiert. Vor dem ersten Vorgang muss `git rev-parse <workspace-revision>:capabilities/<slug>` den in der Application gebundenen Tree-OID ergeben. Fehlt der Pfad oder weicht der OID ab, wird die Capability nicht ausgeführt. Dafür entsteht weder ein Package-Manifest noch ein Resolver im Core.

## Nicht-Ziele

Keine neue Core-Schema-Eigenschaft, Registry, Resolver, Datenbank, Graph, universelle Ontologie, allgemeiner Extraktor, Pflicht-API, Monitoring-Runtime oder automatische Freigabe.
