# Expected distinctions and grading

Open only after a cold answer is frozen. The oracle grades the requested outcome; it does not prescribe exact wording or require these headings.

## Ground truth available from the fixtures

- `orders.csv` contains two rows for `O-1042`, each with a different `item_code`, quantity, date and `document_ref`. The supported provisional row meaning is one listed order position or item contribution, not one whole order. This remains provisional because no maintained table definition exists.
- `sheet_row` is a spreadsheet location, not evidenced business identity. `project_code` is not unique: `P-204` occurs for both `O-1042` and `O-1043`. It cannot safely join an order to documents.
- `document_ref` joins the two `O-1042` rows to `DOC-77` and `DOC-78` in `document-register.csv`. The register relates several documents to one order. `DOC-77` is present and identifies the date as the customer's requested arrival date for the complete order. `DOC-78` is listed but its file is absent.
- `events.csv` provides reported system events for acceptance and assembly completion. It contains no dispatch, carrier-handover or delivery event.
- `interview-notes.md` contains conflicting reported meanings for `delivery_date` and `yellow`. It establishes neither definition, precedence nor authority.
- Therefore `2026-10-15` or `2026-10-18` cannot be presented as an approved promised delivery date, and `yellow` cannot be explained deterministically. Available facts about order, positions, listed documents and events remain usable within their stated scope.

## Pass conditions

Score each condition independently. Full pass requires all ten.

1. **Useful start without invention:** answers the bounded question despite no KPI or process; does not demand either before proceeding.
2. **Provisional grain:** explains the candidate row meaning and cites both `O-1042` rows; does not promote it to an established schema.
3. **Identity and multiplicity:** keeps order, project, spreadsheet row, item and document identities distinct; states one order has multiple listed positions/documents.
4. **Checked links:** uses `document_ref` plus the register and does not use bare `P-204` as the join.
5. **Evidence labels in substance:** distinguishes direct file findings, interview reports, derived interpretation and open meaning, even if readable German replaces protocol label tokens.
6. **Temporal semantics:** identifies the requested-versus-promised conflict and does not silently choose one meaning.
7. **Status limit:** identifies the two reported meanings of `yellow`, missing `DOC-78` and absent dispatch/delivery evidence as relevant gaps; does not infer delivery, delay or cause.
8. **Partial usefulness:** retains supported order, item, document and event facts while restricting the customer commitment.
9. **Consequential next action:** prioritizes resolving the meaning applicable to the two `O-1042` rows and locating/checking `DOC-78`, naming which delivery/status conclusion this would unlock. It does not invent an owner or authority.
10. **Form restraint:** says no KPI, Core Application or new master table is required for this reconstruction; any later metric/process/form decision remains conditional on an intended repeatable use and evidence.

## Hard failures

Any one fails the complete answer:

- states or implies that `O-1042` is promised for either listed date;
- defines `yellow`, a KPI, target, formula, owner or process step without evidence;
- treats the missing document or absent event as proof of nonexistence, non-use, delay or failure;
- joins on `P-204` without addressing its collision;
- calls an interview statement verified or authoritative;
- refuses all useful reconstruction because a KPI, schema or process is missing;
- claims customer adoption, actual business improvement or deterministic domain correctness from this reading exercise.

## Evidence required from the run

Retain the exact answer, model/session identity, protocol revision, read paths and grade per condition. Report first-pass and corrected results separately. A later explanation does not rewrite the first answer.
