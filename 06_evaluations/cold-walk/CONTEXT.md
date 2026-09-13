# Cold walk

The walk is the reference harness. It uses only the public API (`init_workspace`, `surface_hash`, `validate`) and Git, and it runs the synthetic Application under [beispiel/applications/prueffall](beispiel/applications/prueffall/) through one complete Vorgang:

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

Every state is validated. Closing an attempt whose route leads to another Arbeitsschritt and opening that successor is one logical transition after preflight, not a transactional filesystem write: the validator rejects a Laufpfad that ends on such a closed entry (`run.invalid: Next Laufpfad entry must follow selected route`). The final step carries a synthetic `freigabe` by `human:beispiel-pruefer`; a real workspace receives that entry only from the named human. The mutation proves that the validator fires.

During `nachfordern 001 wartend`, the harness prepares the declared draft from its bound report and derives the current attempt’s visible `Stand` from Laufpfad and files. Bound inputs and decision remain unchanged. The synthetic response is first received in the file named by this example's `continuation_ref`; the local receipt check rejects unsafe paths and missing or different content before continuation. The declared output and handoff then bind the response plus its origin in `pruefen 002`. The example requires a complete corrected application, not a partial amendment; its receipt check does not prove that semantic distinction. A simulated human draft edit is retained; a stale overwrite is rejected. Further counterexamples alter bound input or place an active entry after a waiting entry. This proves the exercised file/state and handoff boundaries, not autonomous scheduling, authentic human communication or reduced business waiting time. Independent partial arithmetic is exercised separately in the [computation example](../computation-walk/CONTEXT.md).

Run:

```bash
python3 -m pip install -e .
python3 06_evaluations/cold-walk/check.py
```

Without the install, `PYTHONPATH=src python3 06_evaluations/cold-walk/check.py` also works, provided the runtime dependencies (`jsonschema`, `referencing`, `PyYAML`) are importable; the editable install supplies them. The example Application validates on its own with `impacts validate 06_evaluations/cold-walk/beispiel/applications/prueffall`.

Exit 0 only when every state validates as expected and the mutation is detected.
