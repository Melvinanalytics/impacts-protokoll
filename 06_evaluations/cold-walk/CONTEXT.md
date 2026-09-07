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

Every state is validated. Closing an attempt whose route leads to another Arbeitsschritt and opening that successor is one logical transition after preflight, not a transactional filesystem write: the validator rejects a Laufpfad that ends on such a closed entry (`run.invalid: Next Laufpfad entry must follow selected route`). The final step carries a synthetic `freigabe` by `human:beispiel-pruefer`; a real workspace receives that entry only from the named human. The mutation proves that the validator fires.

Run:

```bash
python3 -m pip install -e .
python3 06_evaluations/cold-walk/check.py
```

Without the install, `PYTHONPATH=src python3 06_evaluations/cold-walk/check.py` also works. The example Application validates on its own with `impacts validate 06_evaluations/cold-walk/beispiel/applications/prueffall`.

Exit 0 only when every state validates as expected and the mutation is detected.
