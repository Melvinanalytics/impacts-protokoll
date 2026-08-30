# Contract-only cold walk

This check creates a disposable workspace and reads its folder contract. It expects eight empty workspace folders plus three files:

```text
CONTEXT.md
00_steuerung/paketaktivierungen.yaml
02_grundlagen/datenautoritaet.yaml
```

Run:

```bash
python3 -m pip install -e .
python3 06_evaluations/cold-walk/check.py
```

Without the install, `PYTHONPATH=src python3 06_evaluations/cold-walk/check.py` also works.

The check validates folder names, file names and the read-only validation result. It rejects embedded process trees and generated work artifacts in the initial template.
