# Cold walk

This local walk uses the reference implementation and Git, and it runs the synthetic Application under [beispiel/applications/prueffall](beispiel/applications/prueffall/) through one complete Vorgang:

```text
pruefen 001       aktiv
nachfordern 001   aktiv          after klaerung
nachfordern 001   wartend        wiedereinstieg
pruefen 002       aktiv          after nachgereicht (loop)
entscheiden 001   aktiv          after bestanden, human gate, walk stops
entscheiden 001   abgeschlossen  freigegeben -> end:entschieden
mutation          one input byte changed -> hash.mismatch
```

The retained fixture uses German workspaces. This walk checks the stated state, source and handoff contracts; the [paired offer walk](../offer-walk/CONTEXT.md) separately exercises the language boundary.

The retained Application's older readable headings, including `Human Check`, are historical fixture content. Keep its bound trees and runs unchanged: this walk checks compatibility and execution boundaries, not adoption of the current [step areas](../../02_protocol/impacts-method.md#step-areas). New definitions use the current [workstep templates](../../02_protocol/templates/arbeitsschritt.md); their generated structure is checked separately. The harness now commits those historical bytes first, then binds `beispiel/fixtures/gate-final-rejection.md` as a new Application revision for new runs. `human-decision-final.yaml` supplies the new decision-bearing positive fixture; final rejection ends at `end:abgelehnt`. The historical Application and decision fixture remain byte-identical. Tests exercise both endings and missing/conflicting decision content.

Every state is validated. Closing an attempt whose route leads to another Arbeitsschritt and opening that successor is one logical transition after preflight of the current persisted run, bound surfaces, route and handoff, not a transactional filesystem write: the validator rejects a Laufpfad that ends on such a closed entry (`run.invalid`). The final step carries a synthetic `freigabe` by `human:beispiel-pruefer`; a real workspace applies [Signals and human gates](../../02_protocol/capabilities.md#signale-und-human-gate) when receiving and recording the actual human decision. The mutation proves that the validator fires.

This reference helper rejects supplied filenames that become identical under canonical Unicode composition and case folding, including aliased parent-file collisions, before writing. It also rejects components longer than 255 UTF-8 bytes or ending in a dot or space before writing. These portable support restrictions also apply on case-sensitive filesystems. It preserves original filenames and raw byte hashes; it does not change Core path semantics or guarantee rollback after arbitrary filesystem failures.

During `nachfordern 001 wartend`, the harness prepares the declared draft from its bound report and derives the current attempt’s visible `Stand` from Laufpfad and files. Bound inputs and decision remain unchanged. The synthetic response is first received in the file named by this example's `continuation_ref`; the local receipt check rejects unsafe paths and missing or different content before continuation. The declared output and handoff then bind the response plus its origin in `pruefen 002`. The example requires a complete corrected application, not a partial amendment; its receipt check does not prove that semantic distinction. A simulated human draft edit is retained; a stale overwrite is rejected. Further counterexamples alter bound input or place an active entry after a waiting entry. This proves the exercised file/state and handoff boundaries, not autonomous scheduling, authentic human communication or reduced business waiting time. Independent partial arithmetic is exercised separately in the [computation example](../computation-walk/CONTEXT.md).

Run:

```bash
python3 -m pip install -e .
python3 06_evaluations/cold-walk/check.py
```

Without the install, `PYTHONPATH=src python3 06_evaluations/cold-walk/check.py` also works, provided the runtime dependencies (`jsonschema`, `referencing`, `PyYAML`) are importable; the editable install supplies them. The example Application validates on its own with `impacts validate 06_evaluations/cold-walk/beispiel/applications/prueffall`.

The helper reads per-file Markdown provenance and exactly one mapping to the selected immediate successor. Its human-gate completion supports only `freigegeben` or `abgelehnt` leading to `end:<slug>`. Core permits gate routes to worksteps, but this helper does not execute them. Later consumers and shared provenance require another configured harness; the [offer walk](../offer-walk/CONTEXT.md) demonstrates shared `herkunft.json`.

Exit 0 only when every state validates as expected and the mutation is detected.
