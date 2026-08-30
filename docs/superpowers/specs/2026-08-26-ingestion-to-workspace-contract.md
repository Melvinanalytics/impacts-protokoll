---
status: draft
review_state: ready-for-human-review
binds: docs/superpowers/specs/2026-08-26-contract-only-core-design.md
does_not_add_protocol_schemas: true
---

# Ingestion zum Customer-Workspace

Datum: 2026-08-26

## Ziel

Jede kundenseitige Ingestion, Datei, CRM-Abzug oder SQL-Projektion, muss im Workspace dieselbe Struktur hinterlassen, die ein Mensch und ein Agent ohne Graph-Datenbank lesen können. Der Core bekommt dafür keinen CRM-Typen und kein neues Protokollschema. Das Komplexitätsbudget bleibt `root_dirs: 6`, `protocol_schemas: 9`, `max_total_required_fields_per_schema: 21`.

Diese Spezifikation bindet ausschließlich den Landepunkt im Customer-Workspace. Adapter und Agent-Harness bleiben außerhalb des Core.

## Was Ingestion nicht darf

Ingestion speichert keinen Satz als eine Notiz. „Product team runs Slack workflow which consumes tickets“ wird nicht eine Datei. Team, Workflow und Ticket bleiben getrennte Nouns. Kanten sind Referenzen auf stabile IDs, nicht Prosa.

Ingestion erzeugt keine identitätsstiftenden Datumsnamen. `kunde-2026-08-26.yaml` ist ungültig als Record-Identität. `03_records/kunde-2026-08-26/` ist ungültig.

Ingestion schreibt keine operative Wahrheit in eine IMPACTS-eigene Neo4j-Projektion, ein Obsidian-Canvas oder `99_ansichten/`. Ein deklariertes externes System of Record behält unabhängig von seiner Speichertechnik die eigene Autorität; dieser Vertrag materialisiert daraus nur Referenz und Snapshot. Ein Analysegraph darf denselben Stand abziehen. Er ist nicht der Record und nicht das SoR.

Dieser Record-Vertrag entscheidet nicht, ob eine aktivierte Capability den Abzug zusätzlich als Graph-Intelligence-Projektion verarbeitet. Die nichtnormative [Forschungs- und Diskussionsgrundlage](../../research/2026-08-29-graph-intelligence-layer.md) trennt diese optionale Entscheidung von der operativen Record-Autorität.

Ingestion legt keinen zweiten Master neben der in `datenautoritaet.yaml` genannten Autorität.

## Kanonisches Ergebnis

```text
02_grundlagen/datenautoritaet.yaml          immer erzeugt
03_records/<record-id>/record.yaml          nur ohne externes SoR
06_vorgaenge/<vorgang-id>/
  vorgang.yaml
  snapshot/
  receipts/
  freigaben/
99_ansichten/                               erzeugt, nie schreibautoritativ
```

`record-id` folgt `[a-z0-9][a-z0-9._-]{0,127}` und bleibt über Importe hinweg stabil. Dieselbe Quelle, dieselbe ID, derselbe Pfad.

## Drei Schreibweisen

| Gegenstand | Bei neuem Datenstand | Linkziel |
| --- | --- | --- |
| Record, Noun | vorhandene Datei am selben Pfad überschreiben | `record-id` oder `sor:<authority-id>/<opaque-id>` |
| Lauf-Snapshot | neue unveränderliche Datei im Vorgang | Snapshot-Hash plus `record_ref` |
| Receipt | neue, capability-spezifische Datei | Ereignis-ID |

Latest ist der Record-Pfad selbst. Ein Alias `current_revision` darf auf einen Hash zeigen. Er darf die Identität nicht ersetzen. Wikilinks und `record_ref` zeigen nie auf einen Datumsnamen.

## `datenautoritaet.yaml`

Der Generator schreibt diese Datei immer, auch bei `kind: file`. Autorität ist feld- oder bereichsbezogen, nicht pauschal je System.

```yaml
records:
  <entity>:
    writes: customer
    kind: file | sqlite-local | postgres-team | external
    path: 03_records
    # bei external und postgres-team:
    # authority_id: <sor-id>
    # bei postgres-team:
    # dsn_ref: <secret-ref>
```

`kind: file` und `path: 03_records` ist der Start. Der Schlüssel `<entity>` entspricht dem Feld `type` in `record.yaml`. Ein lokaler Record ist nur für einen lokal autorisierten Typ zulässig. `default` gilt als Rückfall für nicht eigens benannte Typen. `file` und `sqlite-local` binden exakt `03_records`. Unterpfade sind unzulässig. `postgres-team` bindet `authority_id` und `dsn_ref`. `external` bindet `authority_id`. Remote-Autoritäten führen keinen lokalen Record-Ordner. Ein externes SoR ersetzt `03_records/` als Wertautorität, nicht den Vorgang.

Eine strukturierte Snapshot-Datei darf beliebige fachliche Felder in einer Abbildung tragen. Sobald eine YAML- oder JSON-Abbildung `record_ref` deklariert, muss der Wert auf eine vorhandene lokale Record-ID oder auf `sor:<authority-id>/<opaque-id>` zeigen. Die `authority-id` muss als `external` oder `postgres-team` in `datenautoritaet.yaml` stehen.

Ein SQL- oder CRM-Abzug landet als unveränderlicher Vorgangssnapshot oder als abgeleitete Datei unter `99_ansichten/`. Er legt keinen lokalen Record-Ordner an.

YAML-, JSON- und Markdown-Ansichten tragen ihre Provenienz direkt. Andere Formate erhalten `<dateiname>.provenance.yaml` mit `generated: true` und `generated_from`.

## Adapterpflicht

Ein Ingestion-Adapter materialisiert für die Stage eine sichtbare Datei. Die Stage liest keine freie Datenbankansicht und keinen freien Graph-Query.

1. Quelle lesen, stabile ID bestimmen oder erzeugen.
2. Record am kanonischen Pfad schreiben oder, bei externem SoR, nur Snapshot plus `record_ref`.
3. Hash des aufgenommenen Standes binden.
4. Vorgang bekommt den Snapshot, nicht den lebenden Record als editierbare Wahrheit des Laufs.
5. Nach menschlichem Gate schreibt nur die in `datenautoritaet.yaml` genannte Autorität zurück.

Ein Analysegraph, eine zeitliche Auswertung oder eine Ansicht liest einen datierten Abzug. Der Abzug liegt in Layer 4 oder `99_ansichten/`. Er stempelt keine Record-Identität und gehört nicht in diesen Record-Vertrag.

## Application versus Ingestion

Die Application definiert Prozessgraph, Gates, benötigte Record-Projektion und zulässige Mutationen. Sie besitzt kein generisches Modell für Customer, Contact, Deal oder Activity.

Ingestion besitzt die Abbildung Quelle auf ID und Pfad. Felder und Lifecycle bleiben Application- oder kundenspezifisch. Ein `schema_ref` in der Application ist ein Kunden- oder Paketvertrag, kein Core-Schema.

OKF-Konzepte behalten stabile IDs. Ein neuer Fall ist eine neue Experience-Datei. Der Concept-Pfad ändert sich nicht, weil ein Import neuer ist.

## Fail-closed

Ein Validator oder Ingestion-Check wird rot bei:

- Record-Pfad mit Datums- oder Laufstempel in der Identität
- zweitem schreibenden Store neben `datenautoritaet.yaml`
- Snapshot, der den Record überschreibt
- capability-spezifische Receipt-Datei, die eine vorhandene Datei ersetzt
- Graph- oder Ansichtsdatei, die als `writes:` geführt wird
- fehlender `datenautoritaet.yaml` nach Generatorlauf

## Nicht in diesem Vorhaben

- neues Core-Schema für Record, Snapshot, CRM oder Datenautorität
- Erhöhung des Komplexitätsbudgets
- Neo4j, Obsidian oder Canvas als SoR
- dynamische Verlinkung, deren Ziel die neueste Datei nach Namen ist

## Nachweis

Der Core-Nachweis arbeitet mit statischen Mutationen. Datumsstempel im Record-Pfad, abweichende Record-ID, fehlender Typ, lokal gespeicherte Records mit externer Typ-Autorität, unvollständige Vorgangsordner, abweichende Vorgangs-ID, unaufgelöste Receipt-Referenzen und schreibautoritative Ansichten müssen `impacts validate` rot setzen. Wiederholte Importe prüft der jeweilige Adapter außerhalb des Core.
