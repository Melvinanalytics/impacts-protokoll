---
status: draft
review_state: discussion-background
evidence_status: hypothesis
date: 2026-08-29
scope: graph-intelligence-layer
informs: docs/superpowers/specs/2026-08-26-contract-only-core-design.md
normative: false
does_not_add_protocol_schemas: true
---

# Graph Intelligence zwischen System of Record und ICM

## Geltungsstatus

`verified`: Diese Notiz ist Hintergrund- und Diskussionsmaterial. Sie erweitert weder den IMPACTS-Core noch den Workspace-Vertrag. Sie aktiviert keine Datenbank, führt kein Pflichtfeld ein und wird nicht durch `impacts validate` ausgewertet. Ein Workspace bleibt ohne SQL- oder Graph-Datenbank vollständig vertragskonform.

`verified`: Die Entscheidungshilfe gilt nach menschlicher Freigabe für Systemdaten allgemein. Customer Records sind ein möglicher Quellbereich neben Prozess-, Paket-, Capability-, Vorgangs-, Receipt- und Provenienzdaten. Kundenspezifische Beispiele und Pilotbefunde bleiben in den jeweiligen privaten Repositories. Erst wiederkehrende Anforderungen aus mindestens drei realen Konsumenten rechtfertigen eine Promotion in einen normativen Core-Vertrag. [Einfachheitsvertrag](../../AGENTS.md)

## Forschungsfrage

Wie trennt IMPACTS operative Wahrheit, deterministisch abgeleitete Graph-Intelligence, file-native Unternehmenswissen und ICM-Ausführung? Wann genügen Dateien oder SQLite, wann braucht ein Workspace Postgres, ein externes System of Record oder Neo4j?

## Kurzurteil

`verified`: Neo4j kann technisch ACID-Transaktionen, Sperren sowie Eindeutigkeits-, Existenz-, Typ- und Schlüsselconstraints bereitstellen. Diese Datenbankfähigkeiten machen eine Neo4j-Instanz nicht automatisch zur fachlichen Autorität. Autorität bleibt eine Architekturentscheidung je Datenbereich. [Neo4j Transactions](https://neo4j.com/docs/operations-manual/current/database-internals/transaction-management/), [Neo4j Concurrent data access](https://neo4j.com/docs/operations-manual/current/database-internals/concurrent-data-access/), [Neo4j Constraints](https://neo4j.com/docs/cypher-manual/current/schema/constraints/)

`hypothesis`: IMPACTS kann optional eine orthogonale **Graph-Intelligence-Projektion** einsetzen. Der Graph kann attested Ableitungen materialisieren und ausliefern, ohne operative Quellfakten zu besitzen. Neo4j wird deshalb kein fünfter Record-Typ neben `file`, `sqlite-local`, `postgres-team` und `external`. Falls ein graph-natives Fachsystem tatsächlich operative Fakten besitzt, wird es bereits als `external` deklariert. Der bestehende Record-Vertrag liegt in [`datenautoritaet.yaml`](../superpowers/specs/2026-08-26-ingestion-to-workspace-contract.md#datenautoritaetyaml).

`hypothesis`: Die aktuelle Gleichstellung von Neo4j mit Obsidian, Canvas und Graphviz als bloßer Ansicht ist zu eng. Präsentationsansichten bleiben unter `99_ansichten/`. Eine Graph-Intelligence-Projektion ist dagegen ein maschinell beschriebener, wiederaufbaubarer Rechen- und Abfragebestand. Sie erhält keine Schreibautorität über operative Records. Die heutige Grenze steht im [Contract-only-Core-Design](../superpowers/specs/2026-08-26-contract-only-core-design.md#file-graph).

## Drei analytische Datenrollen und eine Ausführungsrolle

`hypothesis`: Für die Diskussion lassen sich drei Datenrollen und eine Ausführungsrolle trennen. Sie sind keine neuen Core-Ebenen und keine Speicherklassen. Dateien können mehrere Rollen darstellen; jeder konkrete Fakt behält trotzdem genau eine deklarierte Autorität.

| Rolle | Besitzt | Darf nicht besitzen |
| --- | --- | --- |
| Operative Fakten | den aktuellen, fachlich autorisierten Wert je Datenbereich | unbelegte algorithmische oder LLM-abgeleitete Behauptungen |
| Wiederverwendbares Wissen | Methoden, Quellen, Entscheidungen und Begriffe | operative Instanzzustände oder laufbezogene Arbeitsartefakte |
| Abgeleitete Intelligence | benannte Projektionen und berechnete Ergebnisse mit Provenienz und Review-State | stillschweigende Mutation der Quellfakten oder den automatischen Status `human-reviewed` |
| ICM-Ausführungsartefakte | stufenspezifische Inputs, Snapshots, Vorgangszustand, Outputs, Gates und Receipts | wiederverwendbare Methode oder freie Schreibzugriffe auf SoR beziehungsweise Graph |

`hypothesis`: Innerhalb abgeleiteter Graph Intelligence bezeichnen **Knowledge Graph**, **Berechnungsprojektion** und **Context Graph** unterschiedliche Rollen, nicht automatisch unterschiedliche Systeme. Der Knowledge Graph hält identifizierte Entitäten, Beziehungen und Provenienz. Eine Berechnungsprojektion ist ein benannter Rechenstand. Ein Context Graph ist ein selektiver, zeitgebundener Lesekontext für einen Arbeitsschritt oder Agenten. Eine exportierte Visualisierung bleibt dagegen eine Ansicht unter `99_ansichten/`.

`verified`: Neo4j GDS lädt Daten aus der Datenbank in einen benannten In-Memory-Graphen. Algorithmen können Ergebnisse `stream`en, statistisch ausgeben, nur im Projektionsgraphen `mutate`n oder explizit in die Datenbank `write`n. Nur `write` verändert die Neo4j-Datenbank. [Neo4j GDS: Graph projection](https://neo4j.com/docs/graph-data-science/current/management-ops/graph-creation/graph-project/), [Neo4j GDS: Running algorithms](https://neo4j.com/docs/graph-data-science/current/common-usage/running-algos/)

`verified`: W3C PROV trennt verwendete und erzeugte Entitäten, die erzeugende Aktivität sowie verantwortliche Agents. [W3C PROV-DM](https://www.w3.org/TR/prov-dm/)

`hypothesis`: Dieselbe Trennung sollte IMPACTS für Quellstand, Ableitungslauf, Executor und Ergebnis verwenden. Die Graphprojektion darf Systemmetadaten, Application-Strukturen, Knowledge-Konzepte, Records und Vorgänge über stabile IDs verbinden. Jeder Eingang behält seine eigene Quellautorität.

## Zwei unabhängige Entscheidungen

### 1. Wo liegt operative Wahrheit?

`hypothesis`: Folgende Schwellen dienen als Entscheidungshilfe, nicht als Core-Pflicht:

| Profil | Verwenden, wenn | Grenze |
| --- | --- | --- |
| `file` | ein schreibender Arbeitskontext, geringe Änderungsfrequenz, menschliche Editierbarkeit und Git-Nachvollziehbarkeit genügen | keine konkurrierenden Mutationen oder serverseitige Queue voraussetzen |
| `sqlite-local` | SQLite nach ausdrücklichem Cutover die lokale operative Autorität mit strukturierten Abfragen und Transaktionen übernimmt | bleibt auf einen lokalen Schreibhost begrenzt; keine Remote-Worker voraussetzen |
| `postgres-team` | mindestens ein Korrektheitstrigger **und** ein Remote-Betriebstrigger vorliegen | Provider ist Deployment-Entscheidung; Vertrag bleibt Postgres |
| `external` | ein vorhandenes Fachsystem einen Record-Bereich bereits autoritativ besitzt | Workspace übernimmt Referenz und Snapshot, keinen zweiten Master |

`hypothesis`: Korrektheitstrigger sind parallele Schreiber, atomare Multi-Record-Mutation, disjunkter Queue-Claim oder zeilenbezogene Rechte. Remote-Betriebstrigger sind mehrere Geräte oder Nutzer am selben Live-Stand, dauerhaft laufende Integrationen beziehungsweise Worker oder verbindliche Recovery-Anforderungen. Datenmenge allein ist kein SQL-Trigger.

`hypothesis`: Solange SQLite nur regenerierbarer Query- oder Indexbestand über autoritativen Dateien ist, bleibt `kind: file` deklariert. Erst der ausdrückliche Autoritätswechsel setzt `kind: sqlite-local`.

`verified`: Neon dokumentiert vollständige PostgreSQL-Kompatibilität. Supabase dokumentiert eine dedizierte Postgres-Datenbank je Projekt. [Neon: PostgreSQL introduction](https://neon.com/docs/postgresql/introduction), [Supabase: architecture](https://github.com/supabase/supabase/blob/master/apps/docs/content/guides/getting-started/architecture.mdx)

`hypothesis`: IMPACTS bindet bei `postgres-team` den Postgres-Vertrag, nicht den Provider. Neon, Supabase, andere Managed-Postgres-Dienste und selbst betriebene Instanzen sind damit mögliche, nichtnormative Betriebsoptionen. Das behauptet weder Funktionsgleichheit noch aufwandsfreie Migration zwischen Anbietern; providerspezifische Funktionen bleiben außerhalb des Core.

### 2. Braucht der Bestand eine Graph-Intelligence-Projektion?

`hypothesis`: Eine persistente Graph-Engine ist sinnvoll, wenn Beziehungen selbst wiederholt Recheninput sind und mindestens einer dieser Bedarfe nicht mehr durch lesbare Referenzen oder einfache SQL-Joins getragen wird:

- variable Mehrsprung-, Pfad-, Abhängigkeits- oder Auswirkungsanalysen;
- Centrality-, Community-, Ähnlichkeits-, Link-Prediction- oder Entity-Resolution-Verfahren;
- zeitbezogene Traversalen über viele Entitäten und Beziehungsstände;
- graphkonditionierte Kontextauswahl für mehrere Applications oder Agents.

`hypothesis`: Für eine dauerhafte Graph-Datenbank kommt mindestens ein Wiederverwendungs- oder Betriebssignal hinzu: dieselbe Projektion versorgt mehrere Vorgänge oder Capabilities, muss dauerhaft per API bereitstehen oder trägt materialisierte attested Ableitungen. Eine einmalige Analyse kann als lokale, verwerfbare Projektion ausgeführt werden.

`verified`: GDS stellt unter anderem Centrality-, Community-Detection-, Similarity-, Pathfinding- und Link-Prediction-Verfahren bereit. Das typische Verfahren projiziert den Datenbankstand, führt Algorithmen auf der Projektion aus und schreibt Ergebnisse optional zurück. [Neo4j: Data science with Neo4j](https://neo4j.com/docs/getting-started/gds/)

`hypothesis`: Keine persistente Graph-Datenbank, wenn lediglich Dateien verlinkt, wenige feste Nachbarschaften gelesen oder tabellarische Filter und Aggregationen ausgeführt werden. Datei-Graph beziehungsweise SQLite/Postgres bleiben dann einfacher. Graph-Eignung folgt der Form wiederkehrender Fragen, nicht dem Wunsch nach einer Visualisierung. Neo4j/GDS ist eine mögliche Umsetzung, nicht der abstrakte Vertrag.

`hypothesis`: Record-Delivery-Profil und Intelligence-Projektion sind unabhängige Achsen. Ein file-nativer Workspace kann eine Neo4j-Projektion speisen. Ein Postgres-Workspace braucht nicht automatisch einen Graphen. Die Graphentscheidung erzeugt deshalb keinen fünften Wert in `datenautoritaet.yaml`.

## Zulässiger Datenfluss

`hypothesis`: Ein zulässiger generischer Datenfluss sieht so aus:

```text
operatives SoR
  -> versionierter Abzug mit Snapshot-Hash
     oder Baseline-Snapshot plus quellenspezifisches CDC-Intervall
  -> deklarierte Ingestion-Capability
  -> Projektion in eine Graph-Engine
  -> deklarierter Intelligence-Executor
  -> derived intelligence
  -> Attester + capability-spezifisches Receipt
  -> selektiver Stage-Input für ICM
```

`hypothesis`: Nur deklarierte Capabilities schreiben in den Graphen. Agents lesen Graph-Kontext oder liefern deklarierte Parameter. Freie agentische Graph-Mutationen sind unzulässig. Bei Neo4j schließt das freie Cypher-Mutationen ein. Constraints schützen Identität und Form; sie belegen nicht die Wahrheit einer fachlichen Aussage. [Neo4j Constraints](https://neo4j.com/docs/cypher-manual/current/schema/constraints/)

`reported`: Neo4j positioniert Graphen als persistente Knowledge-Layer, Context Graphs, Agent Memory und Retrieval-Kontext für agentische Systeme. Dies ist eine Herstellerposition, keine neutrale Autoritätsnorm. [Neo4j: A knowledge layer for your agentic systems](https://neo4j.com/blog/news/knowledge-layer-agentic-systems-google-cloud/)

`verified`: Neo4js Knowledge-Graph-Builder kann Entitäten und Beziehungen per LLM extrahieren und ist als experimentell gekennzeichnet. Microsoft GraphRAG baut seinen Graphindex ebenfalls per LLM und erzeugt Community-Zusammenfassungen. [Neo4j KG Builder](https://neo4j.com/docs/neo4j-graphrag-python/current/user_guide_kg_builder.html), [Microsoft GraphRAG paper](https://www.microsoft.com/en-us/research/publication/from-local-to-global-a-graph-rag-approach-to-query-focused-summarization/)

`hypothesis`: Vier Eigenschaften bleiben unabhängig: Wiederholbarkeit der Ausführung, exakte oder approximative Methode, Evidence-Review-State und Materialisierungs-/Serving-Rolle. Ein fixer Seed kann eine approximative Methode wiederholbar machen, aber weder exakt noch epistemisch verifiziert. Neo4j weist selbst darauf hin, dass Vector Retrieval approximativ sein kann. [Neo4j GraphRAG RAG guide](https://neo4j.com/docs/neo4j-graphrag-python/current/user_guide_rag.html)

`verified`: Die Trust-Trias des IMPACTS-Einfachheitsvertrags begrenzt jeden maschinell erzeugten Stand ohne `verified.by: human:<id>` auf höchstens `machine-confirmed`. Ein Receipt attestiert Ausführung und gebundene Inputs; es beweist nicht automatisch fachliche Wahrheit. [Einfachheitsvertrag](../../AGENTS.md)

`hypothesis`: LLM-extrahierte Knoten, Beziehungen und Zusammenfassungen bleiben `reported` oder `hypothesis`, bis eine zulässige Quelle und Prüfung sie hochstuft. GraphRAG-Ausgaben dürfen Agentenkontext liefern. Sie dürfen keine operative Record-Autorität oder deterministische Attestation vortäuschen.

## Kandidaten-Prüfliste für reproduzierbare Graph-Ableitungen

`verified`: GDS-Ausführung ist nicht pauschal deterministisch. Beispielsweise verlangt Neo4j für deterministische KNN-Ergebnisse ausdrücklich `concurrency: 1` und einen gesetzten `randomSeed`; das offizielle FastRP/KNN-Verfahren fixiert beide Werte für wiederholbare Ergebnisse. Reproduzierbarkeit muss daher je Algorithmus geprüft und konfiguriert werden. [Neo4j KNN](https://neo4j.com/docs/graph-data-science/current/algorithms/knn/), [Neo4j FastRP/KNN workflow](https://neo4j.com/docs/graph-data-science/current/getting-started/fastrp-knn-example/)

`hypothesis`: Falls eine Capability Graph-Ableitungen materialisiert, sollte ihr bestehendes capability-spezifisches Receipt die jeweils anwendbaren Punkte dieser Pilot-Prüfliste binden. Die Liste ist kein Core-Schema und führt keine Pflichtfelder ein:

- Quellautoritäten, Quellrevisionen und Hash eines konsistenten Baseline-Snapshots;
- bei inkrementeller Reproduktion zusätzlich quellenspezifisches CDC-Intervall und Transaktionsgrenzen;
- Mapping- und Projektionsdefinition samt Code-Commit oder Inhalts-Hash;
- Graphmodell- und Constraint-Version;
- Graph-Engine-, Algorithmusbibliothek-, Executor- und Attester-Version;
- Algorithmus, Modus und anwendbare Parameter einschließlich Seed, Concurrency, Toleranz und Iterationsgrenze;
- kanonisch sortierten Ergebnishash, Laufzeitpunkt und Lauf-ID.

`hypothesis`: Der Graph kann als materialisierte Serving Copy einer attested Ableitung dienen, wenn nur Capability-Writes zugelassen sind und jede materialisierte Ableitung auf ein gültiges capability-spezifisches Receipt zeigt. Er wird dadurch keine zweite Quellautorität. Operative Fakten bleiben beim deklarierten SoR. Das Receipt belegt den konkreten Ableitungslauf, nicht dessen fachliche Wahrheit; die mutable Graph-Instanz allein belegt beides nicht.

## Zeit und Historie

`verified`: Neo4j unterstützt temporale Werte. Historische Zustände entstehen jedoch erst durch ein gewähltes Versionierungsmodell, beispielsweise unveränderliche Zustandsknoten oder `validFrom`/`validTo` auf zeitbezogenen Elementen. Damit sind Zeitpunkt-Snapshots, Differenzen und temporale Traversalen modellierbar. [Neo4j: Versioning](https://neo4j.com/docs/getting-started/data-modeling/versioning/), [Neo4j: Temporal values](https://neo4j.com/docs/cypher-manual/current/values-and-types/temporal/)

`verified`: Neo4j CDC liest Änderungen aus dem angereicherten Transaction Log. Änderungen außerhalb der Transaktionsschicht, etwa bestimmte Admin-Importe, werden nicht erfasst. Change-IDs sind datenbankspezifisch, Transaktionsnummern können Lücken besitzen, und beobachtete Eventreihenfolge entspricht nicht zwingend der Ausführungsreihenfolge innerhalb einer Transaktion. [Neo4j CDC setup](https://neo4j.com/docs/cdc/current/get-started/self-managed/), [Neo4j CDC procedures](https://neo4j.com/docs/cdc/current/procedures/)

`hypothesis`: Zeitreihenanalyse trennt mindestens fachliche Gültigkeitszeit, Quellaktualisierungs- beziehungsweise Commit-Zeit und technische Beobachtungs- beziehungsweise Laufzeit. Ein reproduzierbarer Graphlauf bindet einen abgeschlossenen Quellstand. Eine Abfrage gegen den jeweils aktuellen Graphen genügt nicht als historische Evidenz.

`hypothesis`: Dichte skalare Messreihen bleiben in der Regel im operativen oder analytischen Store. Ein Graph lohnt sich für Zeitdaten, wenn Identitäten, Beziehungen, Pfade oder Netzwerktopologie über die Zeit ausgewertet werden. Er hält dann zeitbezogene Zustände oder Referenzen auf unveränderliche Abzüge, nicht zwingend jeden Rohmesswert.

## Einbau in die Decomplected Structure

`hypothesis`: Der Core braucht dafür keinen neuen Root-Ordner, Record-Typ oder Protokollschema. Bestehende Strukturen tragen den Zuschnitt:

- `02_grundlagen/datenautoritaet.yaml` bleibt einzige Deklaration operativer Record-Autorität;
- `02_grundlagen/` und aktivierte Knowledge-Bundles tragen file-native stabile Bedeutung;
- `06_vorgaenge/<id>/` trägt verwendete Snapshots, Stage-Inputs und, falls eingesetzt, capability-spezifische Receipts einer Graphberechnung;
- `99_ansichten/` trägt exportierte, menschenlesbare Graphansichten;
- Graph-Ingestion, Algorithmen, Attester und API-Schreibwege gehören in eine Capability.

`hypothesis`: Erst nach mindestens drei realen Konsumenten derselben Bindung wäre zu prüfen, ob ein normativer Designtext **Record-Delivery-Profil** und **optionale Intelligence-Projektion** ausdrücklich trennt. Bis dahin bleibt diese zweite Achse Diskussionsmaterial. Sie erzeugt weder ein Feld in `datenautoritaet.yaml` noch ein neues Core-Schema.

## Offene Validierung

- `open`: Welcher bestehende Capability-Vertrag bindet Graph-Projektion, Algorithmus und Attester ohne neue Core-Oberfläche?
- `open`: Welche algorithmusspezifischen Reproduzierbarkeitsprüfungen muss ein Graph-Attester verweigern, wenn Seed, Concurrency oder Version fehlen?
- `open`: Ab welchem wiederholten Beziehungsproblem ist Neo4j wirtschaftlich gerechtfertigt? Diese Schwelle benötigt reale, synthetisch dokumentierte Consumer-Evidenz.

## Quellenstatus

Alle externen Sachclaims oben verweisen auf Primärquellen: offizielle Neo4j-Dokumentation beziehungsweise Herstellerveröffentlichung, Microsoft Research oder W3C-Spezifikation. Architekturzuordnungen bleiben bis zur menschlichen Entscheidung `hypothesis`.
