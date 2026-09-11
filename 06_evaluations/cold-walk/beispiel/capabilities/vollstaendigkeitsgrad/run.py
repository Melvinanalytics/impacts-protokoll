#!/usr/bin/env python3
"""Deterministic synthetic calculation owned by this Capability tree."""

import argparse
import json
from pathlib import Path


OPERATION = "vollstaendigkeitsgrad-berechnen"
SENTINEL = "vollstaendigkeitsgrad-v1"


def calculate(rules: str, record: str) -> dict:
    rule_line = next((line for line in rules.splitlines() if line.startswith("Pflichtfelder:")), "")
    required = [item.strip().rstrip(".") for item in rule_line.partition(":")[2].split(",") if item.strip()]
    if not required:
        raise ValueError("Keine Pflichtfelder in der Regel")

    values = {}
    for line in record.splitlines():
        name, separator, value = line.partition(":")
        if separator:
            values[name.strip()] = value.strip()

    present = [name for name in required if values.get(name)]
    missing = [name for name in required if not values.get(name)]
    percent = round(len(present) / len(required) * 100)
    if not 0 <= percent <= 100 or len(present) > len(required):
        raise ValueError("Prüfung des Rechenergebnisses fehlgeschlagen")
    return {
        "operation": OPERATION,
        "sentinel": SENTINEL,
        "required": required,
        "present": present,
        "missing": missing,
        "percent": percent,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--rules", type=Path, required=True)
    parser.add_argument("--record", type=Path, required=True)
    args = parser.parse_args()
    result = calculate(
        args.rules.read_text(encoding="utf-8"),
        args.record.read_text(encoding="utf-8"),
    )
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
