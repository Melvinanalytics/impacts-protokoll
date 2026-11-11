# Cold walk

This local walk uses the reference implementation and Git, and it executes one complete Vorgang bound to the synthetic Hauptprozess under [beispiel/hauptprozesse/prueffall](beispiel/hauptprozesse/prueffall/):

```text
pruefen 001       aktiv
nachfordern 001   wartend        after klaerung, wiedereinstieg
pruefen 002       aktiv          after nachgereicht (loop)
entscheiden 001   wartend        after bestanden, human gate, walk stops
entscheiden 001   abgeschlossen  freigegeben -> end:entschieden
mutation          one input byte changed -> hash.mismatch
```

The `nachfordern` definition declares no timed review or non-arrival result, so this walk does not demonstrate time-bounded waiting under the [Waits](../../02_protocol/binding.md#waits) rule. A green structural walk does not establish those business controls.

The import branch copies the Hauptprozess and referenced Capability unchanged, rejects a missing Capability, and checks the supplied source snapshot and provenance against the configured source repository before any destination execution. The [regression tests](../../tests/test_cold_walk.py) reject a false origin or source revision at that boundary and stop when the configured source repository cannot reach a source revision or read its bytes. The branch then executes that Capability and opens `pruefen 001 aktiv`; it does not complete a destination process. Its import commits record the configured source repository's local path and full commit. That path locates a checkout; it is not a source namespace, and the retained source provenance still has only a relative origin and revision. This demonstrates the configured source mapping; acquiring the source from the destination record alone remains open, and its check must show two negative cases: an unreachable commit or namespace gives a blocker with no attempt, and the same path with other bytes or no mapping gives a rejection.

The fixture uses German workspaces. This walk checks the stated state, source and handoff contracts; the [paired offer walk](../offer-walk/CONTEXT.md) separately exercises the language boundary.

The Hauptprozess keeps readable headings such as `Human Check`; this walk checks compatibility and execution boundaries, not adoption of the [step areas](../../02_protocol/impacts-method.md#step-areas). New definitions use the [Arbeitsschritt templates](../../02_protocol/templates/arbeitsschritt.md), whose generated structure is checked separately. The harness commits the Hauptprozess first, then binds `beispiel/fixtures/gate-final-rejection.md` as a new Hauptprozess revision for new Vorgänge. `human-decision-final.yaml` supplies the decision; final rejection ends at `end:abgelehnt`. Tests exercise both endings and missing or conflicting decision content.

Every state is validated. Closing an attempt whose route leads to another Arbeitsschritt and opening that successor is one logical transition after preflight of the current persisted Vorgang, bound surfaces, route and handoff, not a transactional filesystem write: the validator rejects a Laufpfad that ends on such a closed entry (`execution.attempt`). The final step carries a synthetic `freigabe` by `human:beispiel-pruefer`; a real workspace applies [Signals and human gates](../../02_protocol/binding.md#signals-and-human-gates) when receiving and recording the actual human decision. The mutation proves that the validator fires.

This reference helper rejects supplied filenames that become identical under canonical Unicode composition and case folding, including aliased parent-file collisions, before writing. It also rejects components longer than 255 UTF-8 bytes or ending in a dot or space before writing. These portable support restrictions also apply on case-sensitive filesystems. It preserves original filenames and raw byte digests; it does not change Core path semantics or guarantee rollback after arbitrary filesystem failures.

During `nachfordern 001 wartend`, the harness prepares the declared draft from its bound report and derives the Vorgang's visible Progress section for its current attempt from Laufpfad and files. Bound inputs and decision remain unchanged. The synthetic response is first received in the file named by this example's `continuation_ref`; the local receipt check rejects unsafe paths and missing or different content before continuation. The declared output and handoff then bind the response plus its origin in `pruefen 002`. The example requires a complete corrected request, not a partial amendment; its receipt check does not prove that semantic distinction. A simulated human draft edit is retained; a stale overwrite is rejected. Further counterexamples alter bound input or place an active entry after a waiting entry. This proves the exercised file/state and handoff boundaries, not autonomous scheduling, authentic human communication or reduced business waiting time. Independent partial arithmetic is exercised separately in the [computation example](../computation-walk/CONTEXT.md).

Run:

```bash
python3 -m pip install -e .
python3 06_evaluations/cold-walk/check.py
```

Without the install, `PYTHONPATH=src python3 06_evaluations/cold-walk/check.py` also works, provided the runtime dependencies (`jsonschema`, `referencing`, `PyYAML`) are importable; the editable install supplies them. The example Hauptprozess validates on its own with `impacts validate 06_evaluations/cold-walk/beispiel/hauptprozesse/prueffall`.

The helper reads per-file Markdown provenance and exactly one mapping to the selected immediate successor. Its human-gate completion supports only `freigegeben` or `abgelehnt` leading to `end:<slug>`. Core permits gate routes to Arbeitsschritte, but this helper does not execute them. Later consumers and shared provenance require another configured harness; the [offer walk](../offer-walk/CONTEXT.md) demonstrates shared `herkunft.json`.

Exit 0 only when every state validates as expected and the mutation is detected.

The fixture harness resolves logical input declarations through [reference_files.py](../reference_files.py). Synthetic stable sources and provenance live at their committed `records/` home; handoffs reference completed producer outputs without copying them. Core reads source blobs at their recorded commits. The harness also checks the concrete bytes it reads.
