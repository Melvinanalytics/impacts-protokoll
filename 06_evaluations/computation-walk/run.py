#!/usr/bin/env python3
"""Bounded synthetic scenario arithmetic. No DSL, effects, CRM or Core extension."""
from __future__ import annotations

import argparse
from datetime import datetime
from decimal import Decimal, DecimalException, localcontext
import hashlib
import json
from pathlib import Path
import sys


STATUSES = {"verified", "reported", "hypothesis", "open"}
ASSUMPTIONS = {"same_window", "comparable_cases", "non_overlapping_pools", "constraints_included"}


def blocked(path, reason, question):
    return {"value": None, "inputs": [path], "blockers": [{"input": path, "reason": reason, "question": question}]}


def parameter(group, key, prefix, unit, question, *, positive=False, share=False):
    path = f"{prefix}.{key}"
    entry = group.get(key)
    if not isinstance(entry, dict):
        return blocked(path, "missing parameter", question)
    if set(entry) != {"value", "unit", "status", "origin"}:
        return blocked(path, "expected value, unit, status and origin only", question)
    value = entry["value"]
    if value is None or entry["status"] == "open":
        return blocked(path, "missing or explicitly open input", question)
    if entry["status"] not in STATUSES or not isinstance(entry["origin"], str) or not entry["origin"].strip():
        return blocked(path, "unusable evidence declaration", question)
    if entry["unit"] != unit:
        return blocked(path, f"expected unit {unit}; no implicit conversion", question)
    try:
        if isinstance(value, bool) or not isinstance(value, (int, float, str)):
            raise ValueError("finite number required")
        number = Decimal(str(value))
        if not number.is_finite() or number < 0 or (positive and number == 0) or (share and number > 1):
            raise ValueError("number outside supported domain")
    except (DecimalException, ValueError) as exc:
        return blocked(path, str(exc), question)
    return {"value": number, "blockers": [], "inputs": [path]}


def calculate(arguments, operation, unit):
    blockers = []
    for argument in arguments:
        for item in argument["blockers"]:
            if item not in blockers:
                blockers.append(item)
    return {
        "value": None if blockers else operation(*(item["value"] for item in arguments)),
        "unit": unit,
        "blockers": blockers,
        "inputs": sorted({name for item in arguments for name in item.get("inputs", [])}),
    }


def fields(value, permitted, name):
    if not isinstance(value, dict) or set(value) - permitted:
        raise ValueError(f"{name}: expected object with only {sorted(permitted)}")


def unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate snapshot key: {key}")
        result[key] = value
    return result


def evaluate(data):
    fields(data, {"kind", "subject", "window", "as_of", "assumptions", "demand", "resources", "economics"}, "snapshot")
    if data.get("kind") != "scenario":
        raise ValueError("This example accepts scenarios only, not observed effects")
    for key in ("subject", "window", "as_of"):
        if not isinstance(data.get(key), str) or not data[key].strip():
            raise ValueError(f"{key}: non-empty binding required")
    if datetime.fromisoformat(data["as_of"].replace("Z", "+00:00")).utcoffset() is None:
        raise ValueError("as_of: timestamp with UTC offset required")
    assumptions = data.get("assumptions", {})
    fields(assumptions, ASSUMPTIONS, "assumptions")
    constraints = [blocked(f"assumptions.{key}", "not confirmed for this scenario", f"Does {key} hold within this subject and window?")
                   for key in sorted(ASSUMPTIONS) if assumptions.get(key) is not True]
    result = {}
    if "demand" in data:
        demand = data["demand"]
        fields(demand, {"buyers", "reach", "conversion", "frequency"}, "demand")
        params = [parameter(demand, name, "demand", unit, question, share=name in {"reach", "conversion"}) for name, unit, question in (
            ("buyers", "buyer", "How many distinct eligible buyers exist in this scope?"),
            ("reach", "share", "What share of distinct eligible buyers is reached?"),
            ("conversion", "share", "What share of reached buyers purchases?"),
            ("frequency", "case/buyer/window", "How many cases does each purchasing buyer generate in this window?"),
        )]
        result["demand"] = calculate(params, lambda n, r, c, f: n * r * c * f, "case/window")
    resources = data.get("resources")
    if not isinstance(resources, dict) or not resources:
        raise ValueError("resources: at least one explicitly named pool required")
    for name, resource in resources.items():
        if not name.strip():
            raise ValueError("resource name must be non-empty")
        fields(resource, {"hours", "effort"}, f"resources.{name}")
        hours = parameter(resource, "hours", f"resources.{name}", "staff_hour/window", f"How many usable hours does {name} have in this window?")
        effort = parameter(resource, "effort", f"resources.{name}", "staff_hour/case", f"How much {name} effort does one accepted case consume, including review/rework?", positive=True)
        result[f"capacity:{name}"] = calculate([hours, effort], lambda h, t: h / t, "case/window")
    if "demand" in result:
        bounds = list(result.values())
        result["modeled_volume"] = calculate(bounds + constraints, lambda *values: min(values), "case/window")
        result["modeled_volume"]["inputs"] = sorted(set(result["modeled_volume"]["inputs"]) | {f"assumptions.{key}" for key in ASSUMPTIONS})
    if "economics" in data:
        economics = data["economics"]
        fields(economics, {"price", "variable_cost", "retained_fixed_cost", "incremental_cost"}, "economics")
        params = {name: parameter(economics, name, "economics", unit, question) for name, unit, question in (
            ("price", "EUR/case", "What net price applies to this homogeneous case?"),
            ("variable_cost", "EUR/case", "Which costs genuinely vary with an additional case?"),
            ("retained_fixed_cost", "EUR/window", "Which fixed costs, including retained payroll, remain in this window?"),
            ("incremental_cost", "EUR/window", "What complete additional operating cost does this intervention incur in this window?"),
        )}
        result["unit_contribution"] = calculate([params["price"], params["variable_cost"]], lambda p, v: p - v, "EUR/case")
        volume = result.get("modeled_volume", blocked("demand", "no demand model supplied", "What demand bound applies?"))
        result["operating_result"] = calculate([volume, result["unit_contribution"], params["retained_fixed_cost"], params["incremental_cost"]], lambda q, m, f, c: q * m - f - c, "EUR/window")
    for item in result.values():
        value = item["value"]
        text = None if value is None else format(value, "f")
        item["value"] = "0" if value == 0 else (text.rstrip("0").rstrip(".") if text and "." in text else text)
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("snapshot", type=Path)
    args = parser.parse_args()
    try:
        payload = args.snapshot.read_bytes()
        data = json.loads(payload, object_pairs_hook=unique_object)
        with localcontext() as context:
            context.prec = 28
            results = evaluate(data)
        output = {
            "interpretation": "conditional scenario; no observed impact or authorization",
            "subject": data["subject"], "window": data["window"], "as_of": data["as_of"],
            "input_digest": "sha256:" + hashlib.sha256(payload).hexdigest(),
            "local_rule_file_digest": "sha256:" + hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
            "runtime": {"python": sys.version.split()[0], "decimal_precision": 28},
            "results": results,
            "evidence": data,
        }
        print(json.dumps(output, ensure_ascii=False, sort_keys=True, indent=2))
        return 0
    except (OSError, ValueError, TypeError, DecimalException) as exc:
        print(f"Cannot evaluate snapshot: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
