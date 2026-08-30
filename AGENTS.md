# Agent guidance

Read [CONTEXT.md](CONTEXT.md) before repository work. Follow its routing and the protocol documents for the affected surface.

Use these evidence labels in records and reviews:

- `verified`: supported by an inspectable source or confirmed decision.
- `reported`: stated by a source without independent verification.
- `hypothesis`: interpretation awaiting validation.
- `open`: unanswered question or missing input.

Keep each claim with its source and review state. Keep method examples synthetic. Store customer-specific material in its customer repository.

## Einfachheitsvertrag (bindend, ICM/OKF-fundiert)

Modelle brechen unter Druck in Komplexität aus. Dieser Vertrag hält dagegen. Er ist maschinell durchgesetzt: `06_evaluations/complexity-budget/check.py` misst das Budget in `budget.yaml`. Eine Budgeterhöhung braucht dort eine nichtleere `approved_by: human:<id>`-Attribution mit Begründung. Der Checker prüft Metrik, Baseline und Attributionsform. Die Attribution dokumentiert eine Freigabe. Kein Agent erhöht das Budget selbst.

Die sieben Regeln, jede mit Primärquelle:

1. **Ordner und Markdown sind die Architektur.** Ein neues Konzept ist zuerst eine Datei in einem bestehenden Ordner, nie ein neues System. (ICM: "folder structure tells it what to do at each step"; OKF: Bundle = Verzeichnis aus `.md`-Dateien)
2. **Der Mindestvertrag ist ein Feld.** OKF verlangt genau ein Pflichtfeld (`type`). Jedes weitere Pflichtfeld in unseren Schemas trägt eine Begründung im Commit. (OKF: "minimally opinionated")
3. **Interface fixieren.** Core beschreibt Dateien, IDs und Referenzen. Git und Harness übernehmen Pakettransport und Ausführung. (OKF Non-Goals: "fixes the interface, not the packaging")
4. **Factory getrennt von Product.** Stabiles Wissen (Expertise, Methodik) wird nie durch einen einzelnen Lauf verändert; Läufe schreiben nur in ihren Vorgang. (ICM Layer 3/4: "Layer 3 is the factory. Layer 4 is what the factory produces each time.")
5. **Stufenkontext statt Alleskontext.** Jede Stufe erhält nur ihre deklarierten Inputs, und jede Zwischenausgabe ist eine Datei, die ein Mensch öffnen, ändern und speichern kann, bevor die nächste Stufe läuft. (ICM: "Every output is an edit surface.")
6. **Die Trust-Trias wird nie überschrieben.** Ohne `verified.by: human:<id>` ist ein Stand höchstens `machine-confirmed`. Agentenkonsens, Ultra-Modelle und delegierte Prüfungen erzeugen niemals `human-reviewed`. (OKF Trust Signals)
7. **Modelle liefern Parameter, nie die Rechnung.** Capabilities deklarieren Berechnung und deterministischen Prüfer. Das Harness ruft sie auf. (OKF Attested Computations: das Modell "MAY only supply values for the declared parameters"; Attester = "deterministic (no-LLM) code")

**Die Stopp-Frage vor jeder Erweiterung:** Bevor du einen neuen Begriff, ein neues Schema, eine neue Rolle, ein neues Objekt oder eine neue Datei-Art einführst: Nenne die bestehende Struktur, die das bereits kann, und nutze sie. Findest du keine, lösche etwas Gleichgroßes oder hole die Budgeterhöhung beim Menschen. Drei Namen für dasselbe Objekt sind zwei zu viel.

Quellen: [ICM, arXiv 2603.16021](https://arxiv.org/abs/2603.16021) · [OKF v0.2 SPEC](https://github.com/GoogleCloudPlatform/open-knowledge-format/blob/main/SPEC.md)
