<!-- Translation source: CONTRIBUTING.md; sha256: 4df17209e42a9d4d04bec9ac0b7cdba86d13154b33363e0bde7e0331d4ca97ed -->

# Mitwirken

Änderungen gelangen über einen geprüften Pull Request nach `main`. Kundenmaterial bleibt im Kunden-Repository. Revision, erwartetes und beobachtetes Verhalten, synthetische Evidenz und nicht ausgeführte Prüfungen angeben.

Ausgabe v0.4.0 verwendet `hauptprozesse/` und `hauptprozess_revision` und verlangt für neue Arbeit `protocol`-Pins im Arbeitsbereich und Vorgang; Arbeit mit einer anderen major.minor und gekennzeichnete Altbestände werden als nicht beurteilt statt als fehlgeschlagen gemeldet. Die Textausgabe der Validierung beginnt mit einer Statuszeile und verlinkt fehlgeschlagene Prüfungen mit ihren Regeln; JSON-Berichte verwenden `report_version: 3`. Eine `ablage`-Referenz muss einen Speicher nennen, der im Wurzel-Router des Arbeitsbereichs deklariert ist.

Die vollständige Liste steht unter [Breaking changes from v0.3](../../README.md#breaking-changes-from-v03).

Ein neuer Vorgang ohne `protocol` scheitert mit `protocol pin missing; add protocol: <release> to the frontmatter`.

## Offene externe Evidenz

Diese externen Gates bleiben `open`: unabhängige Implementierung, unbegleiteter Erstgebrauch und Korrektur, eine zweite Betreiberperson nach 168 verstrichenen Stunden, Listening-Intake in autorisiertem Langdock, begrenzte Fachprüfung und abgeglichener Geschäftsvergleich. CI, von Luna erzeugte Ausgaben, synthetische Wiederholungen, interne Modellprüfungen oder Repository-Anweisungen ersetzen nicht die benannte externe Evidenz. Jeder verlinkte Vertrag bestimmt seine Passregel und seine erlaubte Aussage: [Implementierungsaufruf](../../06_evaluations/conformance/CONTEXT.md#independent-implementation-challenge), [Follow-up-Gates A bis D](../../06_evaluations/nontechnical-reconstruction/FOLLOW-UP.md) und [Listening-Intake-Prüfung](../../06_evaluations/nontechnical-reconstruction/listening-intake.md). Das Ausführungs-Issue jedes Gates verlinkt dessen Vertrag und hält jeden Lauf in Kommentaren fest: den Freeze-Commit, die Evidenz und die Abschlussentscheidung einer benannten betreuenden Person nach Prüfung der eingefrorenen Evidenz. Ein geschlossenes Gate stützt nur seine erlaubte Aussage und nur für die Revision, die diese Aussage nennt. Produktionseinsatz außerhalb des erklärten, geprüften öffentlichen Repository-Umfangs ist unbekannt.

## Begrenzte Linux-Installation

Für eine frische virtuelle Umgebung mit CPython 3.11 auf Linux x86_64 und glibc 2.17 oder neuer das Rezept aus dem vollständigen Checkout aufrufen: `python3.11 -m venv .venv`, `source .venv/bin/activate`, `python .github/scripts/install_runtime.py`. Das Skript prüft Interpreter, Architektur, libc und virtuelle Umgebung; es installiert binäre Abhängigkeiten vom PyPI-Index mit `--require-hashes` und installiert anschließend genau diesen Checkout ohne erneute Abhängigkeitsauflösung editierbar. Den Git-Commit des Checkouts festhalten. Die Bindung gilt nur für die ausgewählten Wheel-Bytes dieses Ziels; Python, pip, Quellenauthentizität, Build-Herkunft und Paket-Herausgeber sind nicht gebunden. Andere Python-Versionen, Betriebssysteme, Architekturen und libc-Versionen sind nicht abgedeckt.
