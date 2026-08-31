# Contract-only cold walk

This check creates a disposable workspace and reads its folder contract. It expects two empty workspace folders plus one file:

```text
CONTEXT.md
applications/
vorgaenge/
```

Run:

```bash
python3 -m pip install -e .
python3 06_evaluations/cold-walk/check.py
```

Without the install, `PYTHONPATH=src python3 06_evaluations/cold-walk/check.py` also works.

The check validates folder names, file names and the read-only validation result.
