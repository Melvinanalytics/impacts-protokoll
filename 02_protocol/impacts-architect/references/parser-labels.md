### Parser-consumed labels

This table serves translators: it inventories finite labels parsed from readable Markdown bodies, not frontmatter keys or schema enums, whose homes are the [schemas](../../schemas/) and [protocol vocabulary](../../ontology.md#protocol-vocabulary). Use the EN or DE form shown; a DE cell of — means German uses the EN spelling unchanged. Heading, answer and owner readers case-fold their labels; case-sensitive labels retain the spelling shown. Generic Markdown syntax, path/ID grammars and arbitrary caller text are outside this inventory. An executor leads a top-level Processing list item before its colon; an owner leads a labelled paragraph or top-level list item. Leading Minimize move names are compared longest first; `keep`/`behalten` leave rows 2, 7 and 8 as alternatives. The [inventory test](../../../tests/test_parser_label_inventory.py) checks every label and reader; [Minimize tests](../../../tests/test_minimize.py) check the ordered rule.

| Meaning | EN | DE | Reader (file:function) |
|---|---|---|---|
| External store declaration | `Ablage:` | — | `src/impacts_protocol/validator.py:_declared_stores`; first router body line label read by the validator (root router only) |
| Flow headings | `flow` | `ablauf` | `src/impacts_protocol/view/page.html:headingText`, `src/impacts_protocol/view/project.py:annotate`, `src/impacts_protocol/view/project.py:sheet_parts`, `src/impacts_protocol/view/project.py:step_refs` |
| Authority headings | `authority` | `befugnis` | `src/impacts_protocol/view/page.html:headingText`, `src/impacts_protocol/view/project.py:annotate`, `src/impacts_protocol/view/project.py:sheet_parts`, `src/impacts_protocol/view/project.py:step_refs` |
| Job headings | `one job` | `ein job` | `src/impacts_protocol/view/page.html:headingText`, `src/impacts_protocol/view/project.py:annotate`, `src/impacts_protocol/view/project.py:sheet_parts`, `src/impacts_protocol/view/project.py:step_refs` |
| Input headings | `inputs` | `eingaben` | `src/impacts_protocol/view/page.html:headingText`, `src/impacts_protocol/view/project.py:sheet_parts` |
| Output headings | `outputs` | `ausgaben` | `src/impacts_protocol/view/page.html:headingText`, `src/impacts_protocol/view/project.py:sheet_parts` |
| Output and effect headings | `outputs and effects` | `ausgaben und wirkungen` | EN: `src/impacts_protocol/view/page.html:headingText`, `src/impacts_protocol/view/project.py:sheet_parts`; DE: `src/impacts_protocol/view/project.py:sheet_parts` |
| Processing headings | `processing` | `verarbeitung` | `src/impacts_protocol/view/page.html:headingText`, `src/impacts_protocol/view/project.py:sheet_parts`, `src/impacts_protocol/view/project.py:step_refs` |
| Handgrip headings | `handgrips` | `handgriffe` | EN: `src/impacts_protocol/view/page.html:headingText`, `src/impacts_protocol/view/project.py:sheet_parts`; DE: `src/impacts_protocol/view/project.py:sheet_parts` |
| Check headings | `check` | `prüfung` | `src/impacts_protocol/view/page.html:headingText`, `src/impacts_protocol/view/project.py:sheet_parts` |
| Human-check headings | `human check` | `menschliche prüfung` | `src/impacts_protocol/view/page.html:headingText`, `src/impacts_protocol/view/project.py:sheet_parts`, `src/impacts_protocol/view/project.py:step_refs` |
| Excluded context headings | `excluded context` | `nicht laden` | EN: `src/impacts_protocol/view/page.html:headingText`, `src/impacts_protocol/view/project.py:annotate`, `src/impacts_protocol/view/project.py:sheet_parts`; DE: `src/impacts_protocol/view/project.py:annotate`, `src/impacts_protocol/view/project.py:sheet_parts` |
| Analysis section | `analysis` | `analyse` | `src/impacts_protocol/view/project.py:_scopes` |
| Required conditions section | `required conditions` | `geforderte bedingungen` | `src/impacts_protocol/view/project.py:_scopes` |
| Activity section | `activities in flow order` | `tätigkeiten in ablaufreihenfolge` | `src/impacts_protocol/view/project.py:_scopes` |
| Activity column | `activity` | `tätigkeit` | `src/impacts_protocol/view/project.py:_shaped` |
| Condition column | `condition` | `bedingung` | `src/impacts_protocol/view/project.py:_shaped` |
| Basis column | `imposed by and basis` | `urheber und grundlage` | `src/impacts_protocol/view/project.py:_shaped` |
| Evidence column | `evidence` | `evidenz` | `src/impacts_protocol/view/project.py:_shaped` |
| Activity number column | `no.` | `nr.` | `src/impacts_protocol/view/project.py:_shaped` |
| Served condition column | `serves` | `dient` | `src/impacts_protocol/view/project.py:_shaped` |
| Result-work column | `result work` | `ergebnisarbeit` | `src/impacts_protocol/view/project.py:_shaped` |
| Coordination column | `coordination` | `koordination` | `src/impacts_protocol/view/project.py:_shaped` |
| Failure-demand column | `failure demand` | `fehlerfolge` | `src/impacts_protocol/view/project.py:_shaped` |
| Duplicate column | `duplicate` | `doppelung` | `src/impacts_protocol/view/project.py:_shaped` |
| Excess column | `excess` | `überschuss` | `src/impacts_protocol/view/project.py:_shaped` |
| Proposed move column | `proposed move` | `vorgeschlagene massnahme` | `src/impacts_protocol/view/project.py:_shaped` |
| Subject link | `Subject` | `Gegenstand` | `src/impacts_protocol/view/project.py:annotate`, `src/impacts_protocol/view/selection.py:subject_record` |
| Human executor | `human` | `mensch` | `src/impacts_protocol/view/page.html:workstepSheet`, `src/impacts_protocol/view/project.py:execution` |
| Deterministic executor | `deterministic system` | `deterministisches system` | `src/impacts_protocol/view/page.html:workstepSheet`, `src/impacts_protocol/view/project.py:execution` |
| Classifier executor | `classifier` | `klassifikator` | `src/impacts_protocol/view/page.html:workstepSheet`, `src/impacts_protocol/view/project.py:execution` |
| Responsible owner | `responsible` | `verantwortlich` | `src/impacts_protocol/view/page.html:workstepSheet`, `src/impacts_protocol/view/project.py:step_owners` |
| Owner role | `role` | `rolle` | `src/impacts_protocol/view/page.html:workstepSheet`, `src/impacts_protocol/view/project.py:step_owners` |
| Positive answer | `yes` | `ja` | `src/impacts_protocol/view/project.py:answer` |
| Negative answer | `no` | `nein` | `src/impacts_protocol/view/project.py:answer` |
| Unresolved answer | `open` | `offen` | EN: `src/impacts_protocol/view/project.py:answer`, `src/impacts_protocol/view/project.py:labels`; DE: `src/impacts_protocol/view/project.py:answer` |
| Required separation | `yes, required` | `ja, erforderlich` | `src/impacts_protocol/view/project.py:minimize` |
| Current separation | `yes, today only` | `ja, nur heute` | `src/impacts_protocol/view/project.py:minimize` |
| Recipient basis | `recipient acceptance` | `abnahme durch den empfänger`, `die abnahme durch den empfänger` | `src/impacts_protocol/view/project.py:minimize` |
| Confirmed own-rule basis | `own rule, confirmed` | `eigene regel, bestätigt` | `src/impacts_protocol/view/project.py:minimize` |
| Open own-rule basis | `own rule, open` | `eigene regel, offen` | `src/impacts_protocol/view/project.py:minimize` |
| Third-party basis | `third-party obligation` | `pflicht eines dritten` | `src/impacts_protocol/view/project.py:minimize` |
| Correct earlier contribution | `correct` | `den formularfehler seinem eigentümer melden und das formular korrigieren` | `src/impacts_protocol/view/project.py:minimize` |
| Retain contribution | `keep` | `behalten` | `src/impacts_protocol/view/project.py:minimize` |
| Remove separation | `remove the separation` | `trennung aufheben` | `src/impacts_protocol/view/project.py:minimize` |
| Ask rule owner | `ask` | `abteilungsleitung fragen` | `src/impacts_protocol/view/project.py:minimize` |
| Trim contribution | `trim` | `bericht auf befunde mit verweisen kürzen` | `src/impacts_protocol/view/project.py:minimize` |
| Agent executor | `agent` | — | `src/impacts_protocol/view/page.html:workstepSheet`, `src/impacts_protocol/view/project.py:execution` |
| Capability call identity | `Aufruf-ID` | — | `06_evaluations/cold-walk/check.py:_hauptprozess_call` |
| Missing finding | `Befund: fehlt` | — | `06_evaluations/cold-walk/check.py:walk` |
| Decision rationale | `Begründung` | — | `06_evaluations/cold-walk/check.py:_fields` |
| Handoff route | `Bei Route` | — | `06_evaluations/cold-walk/check.py:_hauptprozess_handoff`, `06_evaluations/offer-walk/run.py:bound_inputs` |
| Capability call heading | `capability call` | — | `src/impacts_protocol/view/page.html:headingText` |
| Capability path | `Capability-Pfad` | — | `06_evaluations/cold-walk/check.py:_hauptprozess_call` |
| Capability revision | `Capability-Revision` | — | `06_evaluations/cold-walk/check.py:_hauptprozess_call` |
| Commitment data kind | `Commitment` | — | `src/impacts_protocol/view/project.py:source_kinds` |
| Control content digest | `Content-Digest` | — | `06_evaluations/cold-walk/check.py:_fields` |
| Source data kind | `Datenart` | — | `src/impacts_protocol/view/project.py:source_kinds` |
| Decision data kind | `Decision record` | — | `src/impacts_protocol/view/project.py:source_kinds` |
| Control input source | `Eingangsquelle` | — | `06_evaluations/cold-walk/check.py:_fields` |
| Proposed removal | `entfaellt` | — | `src/impacts_protocol/view/project.py:necessity` |
| Control decision | `Entscheidung` | — | `06_evaluations/cold-walk/check.py:_fields` |
| Required source control | `Erforderliche Kontrolle` | — | `06_evaluations/cold-walk/check.py:_fields`, `06_evaluations/cold-walk/check.py:_hauptprozess_source` |
| Foundation data kind | `Foundations` | — | `src/impacts_protocol/view/project.py:source_kinds` |
| Source origin | `Herkunft` | — | `06_evaluations/cold-walk/check.py:_fields`, `06_evaluations/cold-walk/check.py:_hauptprozess_source` |
| Hypothesis evidence | `hypothesis` | — | `src/impacts_protocol/view/project.py:labels` |
| Condition identity column | `id` | — | `src/impacts_protocol/view/project.py:_shaped` |
| Control evidence | `Kontrollnachweis` | — | `06_evaluations/cold-walk/check.py:_fields` |
| Loop bound declaration | `Loop bound` | — | `06_evaluations/cold-walk/check.py:_check_loop_bounds` |
| Capability operation | `Operation` | — | `06_evaluations/cold-walk/check.py:_execute_capability`, `06_evaluations/cold-walk/check.py:_hauptprozess_call` |
| Owner attribution | `owner` | — | `src/impacts_protocol/view/page.html:workstepSheet`, `src/impacts_protocol/view/project.py:step_owners` |
| Required fields declaration | `Pflichtfelder` | — | `06_evaluations/cold-walk/beispiel/capabilities/vollstaendigkeitsgrad/run.py:calculate` |
| Population data kind | `Population` | — | `src/impacts_protocol/view/project.py:source_kinds` |
| Control report | `Prüfbericht` | — | `06_evaluations/cold-walk/check.py:_fields` |
| Source input declaration | `Quell-Eingabe` | — | `06_evaluations/cold-walk/check.py:_hauptprozess_source`, `src/impacts_protocol/view/project.py:source_kinds` |
| Received-source data kind | `Received source` | — | `src/impacts_protocol/view/project.py:source_kinds` |
| Remove contribution | `remove` | — | `src/impacts_protocol/view/project.py:minimize` |
| Reported evidence | `reported` | — | `src/impacts_protocol/view/project.py:labels` |
| Run data kind | `Run record` | — | `src/impacts_protocol/view/project.py:source_kinds` |
| Subject stage | `Stage` | — | `src/impacts_protocol/view/selection.py:record_stages` |
| Source version | `Stand` | — | `06_evaluations/cold-walk/check.py:_fields`, `06_evaluations/cold-walk/check.py:_hauptprozess_source` |
| Subject data kind | `Subject record` | — | `src/impacts_protocol/view/project.py:source_kinds` |
| Control origin | `Ursprung` | — | `06_evaluations/cold-walk/check.py:_fields`, `06_evaluations/cold-walk/check.py:_hauptprozess_source` |
| Verified evidence | `verified` | — | `src/impacts_protocol/view/project.py:labels` |
| Tool headings | `tools` | `werkzeuge` | `src/impacts_protocol/view/page.html:headingText` |
| Work data kind | `Work` | — | `src/impacts_protocol/view/project.py:source_kinds` |
| Offer customer placeholder | `{{customer_id}}` | — | `06_evaluations/offer-walk/run.py:fill_offer` |
| Offer identity placeholder | `{{offer_id}}` | — | `06_evaluations/offer-walk/run.py:fill_offer` |
| Offer positions placeholder | `{{positions}}` | — | `06_evaluations/offer-walk/run.py:fill_offer` |
| Offer request placeholder | `{{request_ref}}` | — | `06_evaluations/offer-walk/run.py:fill_offer` |
| Offer total placeholder | `{{total}}` | — | `06_evaluations/offer-walk/run.py:fill_offer` |
| Offer version placeholder | `{{version}}` | — | `06_evaluations/offer-walk/run.py:fill_offer` |

