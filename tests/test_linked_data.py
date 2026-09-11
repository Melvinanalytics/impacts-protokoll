"""Executable counterexamples for datenbezug.md, not a Core reader or connector.

The fixture owns this small x_tables dialect. All loaded rows are checked before
selection; it neither verifies source truth nor interprets arbitrary prose rules.
"""

import copy
import csv
from datetime import date
from decimal import Decimal
from io import StringIO
import json
from pathlib import Path
import re
import sys

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from impacts_protocol.validator import SCHEMA_REGISTRY


DOCUMENT = ROOT / "02_protocol/impacts-architect/references/datenbezug.md"


@pytest.fixture
def source():
    text = DOCUMENT.read_text(encoding="utf-8")
    model = yaml.safe_load(re.search(r"```markdown\n---\n(.*?)\n---", text, re.S)[1])["x_tables"]
    blocks = re.findall(r"^### `records/([^`]+)\.csv`\n\n```csv\n(.*?)\n```", text, re.M | re.S)
    tables = {name: list(csv.DictReader(StringIO(body))) for name, body in blocks}
    assert set(tables) == set(model)
    return model, tables


def read(source, customer_id="C-1", as_of="2026-09-10"):
    """Exercise this example's declared keys, intervals, units and selection."""
    model, tables = source
    indexes = {}
    for name, spec in model.items():
        index = {}
        for row in tables[name]:
            key = tuple(row.get(field) for field in spec["primary_key"])
            if not all(key):
                raise ValueError("empty primary key")
            if key in index:
                raise ValueError("duplicate primary key")
            index[key] = row
        indexes[name] = index
    for name, spec in model.items():
        for row in tables[name]:
            for link in spec.get("foreign_keys", []):
                assert link["references"] == model[link["target"]]["primary_key"]
                key = tuple(row.get(field) for field in link["fields"])
                if link.get("nullable") and all(value == "" for value in key):
                    continue
                if key not in indexes[link["target"]]:
                    raise ValueError("unresolved foreign key")
            fields = spec.get("exactly_one")
            if fields and sum(bool(row.get(field)) for field in fields) != 1:
                raise ValueError("exactly one target required")
    intervals = {}
    for row in tables["agreements"]:
        if not re.fullmatch(r"[1-9][0-9]*", row["version"]):
            raise ValueError("non-canonical version")
        start = date.fromisoformat(row["valid_from"])
        end = date.fromisoformat(row["valid_to"]) if row["valid_to"] else None
        if end is not None and start >= end:
            raise ValueError("empty applicability interval")
        previous = intervals.setdefault(row["agreement_id"], [])
        for prior_start, prior_end in previous:
            if (prior_end is None or start < prior_end) and (end is None or prior_start < end):
                raise ValueError("overlapping agreement versions")
        previous.append((start, end))
    for row in tables["agreement_items"]:
        value = Decimal(row["quantity"])
        if not value.is_finite() or value < 0:
            raise ValueError("invalid quantity")
        expected_unit = "Stück" if row["product_id"] else "Stunde"
        if row["unit"] != expected_unit:
            raise ValueError("incompatible unit")
    if (customer_id,) not in indexes["customers"]:
        raise LookupError("customer identity unresolved")
    day = date.fromisoformat(as_of)
    agreements = [row for row in tables["agreements"]
                  if row["customer_id"] == customer_id
                  and date.fromisoformat(row["valid_from"]) <= day
                  and (not row["valid_to"] or day < date.fromisoformat(row["valid_to"]))]
    if not agreements:
        raise LookupError("no matching agreement in this source scope")
    keys = {(row["agreement_id"], row["version"]) for row in agreements}
    items = [row for row in tables["agreement_items"]
             if (row["agreement_id"], row["agreement_version"]) in keys]
    return {"customer": indexes["customers"][(customer_id,)], "as_of": as_of,
            "agreements": agreements, "items": items,
            "products": [indexes["products"][(row["product_id"],)] for row in items if row["product_id"]],
            "services": [indexes["services"][(row["service_id"],)] for row in items if row["service_id"]]}


@pytest.mark.parametrize("customer,day,items", [
    ("C-1", "2026-09-10", ["I-2", "I-3"]),
    ("C-2", "2026-09-10", ["I-4"]),
    ("C-1", "2026-06-30", ["I-1"]),
    ("C-1", "2026-07-01", ["I-2", "I-3"]),
])
def test_selection_preserves_identity_and_version(source, customer, day, items):
    before = copy.deepcopy(source)
    result = read(source, customer, day)
    assert [row["item_id"] for row in result["items"]] == items
    assert source == before


@pytest.mark.parametrize("table,index,change,error", [
    ("customers", 1, {"customer_id": "C-1"}, "duplicate primary key"),
    ("customers", 0, {"customer_id": ""}, "empty primary key"),
    ("agreement_items", 2, {"service_id": "S-404"}, "unresolved foreign key"),
    ("agreement_items", 2, {"agreement_version": "99"}, "unresolved foreign key"),
    ("agreement_items", 2, {"agreement_version": "02"}, "unresolved foreign key"),
    ("agreement_items", 2, {"product_id": "P-10"}, "exactly one target required"),
    ("agreement_items", 2, {"service_id": ""}, "exactly one target required"),
    ("agreement_items", 2, {"quantity": "-1"}, "invalid quantity"),
    ("agreement_items", 2, {"quantity": "NaN"}, "invalid quantity"),
    ("agreement_items", 2, {"unit": "Stück"}, "incompatible unit"),
    ("agreements", 0, {"valid_to": ""}, "overlapping agreement versions"),
    ("agreements", 0, {"valid_to": "2026-01-01"}, "empty applicability interval"),
    # This reader deliberately checks even rows outside the selected customer.
    ("agreement_items", 3, {"service_id": "S-404"}, "unresolved foreign key"),
])
def test_bad_source_cannot_yield_a_successful_excerpt(source, table, index, change, error):
    source[1][table][index].update(change)
    with pytest.raises(ValueError, match=f"^{error}$"):
        read(source)


@pytest.mark.parametrize("customer,day,error", [
    ("C-404", "2026-09-10", "customer identity unresolved"),
    ("Beispielkunde", "2026-09-10", "customer identity unresolved"),
    ("C-1", "2025-12-31", "no matching agreement in this source scope"),
])
def test_missing_evidence_is_a_scoped_gap(source, customer, day, error):
    with pytest.raises(LookupError, match=f"^{error}$"):
        read(source, customer, day)


def test_multiple_valid_agreements_are_not_reduced_to_first(source):
    tables = source[1]
    tables["agreements"].append(dict(tables["agreements"][2], agreement_id="A-3", customer_id="C-1"))
    tables["agreement_items"].append(dict(tables["agreement_items"][3], item_id="I-5", agreement_id="A-3"))
    result = read(source)
    assert [row["agreement_id"] for row in result["agreements"]] == ["A-1", "A-3"]
    assert [row["item_id"] for row in result["items"]] == ["I-2", "I-3", "I-5"]


def test_valid_foreign_key_does_not_verify_source_truth(source):
    # Reassign to a real, different version. Integrity checks cannot know that
    # the original source assertion was true or that this reassignment is false.
    source[1]["agreement_items"][2]["agreement_version"] = "1"
    assert [row["item_id"] for row in read(source)["items"]] == ["I-2"]


def test_compact_document_view_matches_computed_excerpt(source):
    shown = json.loads(re.search(r"```json\n(.*?)\n```", DOCUMENT.read_text(), re.S)[1])
    result = read(source)
    assert shown["customer_id"] == result["customer"]["customer_id"]
    assert shown["as_of"] == result["as_of"]
    assert shown["agreement"] == {"agreement_id": result["agreements"][0]["agreement_id"],
                                  "version": int(result["agreements"][0]["version"])}
    for compact, full in zip(shown["items"], result["items"], strict=True):
        for key, value in compact.items():
            assert value == (Decimal(full[key]) if key == "quantity" else full[key])


@pytest.fixture
def offer():
    text = DOCUMENT.read_text(encoding="utf-8")
    template = re.search(r"```text\n(.*?)\n```", text.split("### Document blank\n", 1)[1], re.S)[1]
    values = json.loads(re.search(r"```json\n(.*?)\n```", text.split("### Concrete run inputs\n", 1)[1], re.S)[1])
    expected = re.search(r"```text\n(.*?)\n```", text.split("### Filled output\n", 1)[1], re.S)[1]
    return template, values, expected


# Use the executed example implementation; do not maintain a second calculator.
import importlib.util
_spec = importlib.util.spec_from_file_location("offer_walk", ROOT / "06_evaluations/offer-walk/run.py")
_offer_walk = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_offer_walk)
fill_offer = _offer_walk.fill_offer


def test_offer_blank_becomes_the_documented_instance_without_changing_inputs(offer):
    template, values, expected = offer
    before = copy.deepcopy(offer)
    assert fill_offer(template, values) == expected
    assert offer == before


def test_same_blank_fills_an_independent_second_run(offer):
    template, first, _ = offer
    first_result = fill_offer(template, first)
    second = copy.deepcopy(first)
    second.update(offer_id="O-2", customer_id="C-2", request_ref="AN-2")
    second["items"][0]["quantity"] = "1"
    second["items"][1]["quantity"] = "3"
    result = fill_offer(template, second)
    assert "Angebot O-2" in result and "Kunde: C-2" in result and "340.00 EUR" in result
    assert fill_offer(template, first) == first_result
    assert "{{offer_id}}" in template


@pytest.mark.parametrize("change,error", [
    ({"currency": "USD"}, "incompatible unit or currency"),
    ({"unit_price": ""}, "missing quantity or price"),
    ({"price_source": ""}, "missing or duplicate position identity/source"),
    ({"quantity": "NaN"}, "invalid quantity or price"),
    ({"unit_price": "100.001"}, "rounding rule required"),
])
def test_undefined_offer_inputs_do_not_produce_a_filled_result(offer, change, error):
    template, values, _ = offer
    values["items"][0].update(change)
    with pytest.raises(ValueError, match=f"^{error}$"):
        fill_offer(template, values)


def test_offer_cannot_hide_an_unfilled_required_placeholder(offer):
    template, values, _ = offer
    with pytest.raises(ValueError, match="^unfilled placeholder$"):
        fill_offer(template + "\nLieferung: {{delivery}}", values)


@pytest.fixture
def offer_workstep():
    section = DOCUMENT.read_text().split("### Worked workstep contract\n", 1)[1]
    return yaml.safe_load(re.search(r"```markdown\n---\n(.*?)\n---", section, re.S)[1])


def test_worked_offer_step_uses_the_existing_core_schema(offer_workstep):
    assert list(SCHEMA_REGISTRY.errors("arbeitsschritt", offer_workstep)) == []


@pytest.mark.parametrize("changes", [
    {"role": "dokumentrohling-agent"},
    {"input_spec": [{"name": "angebotsdaten.json"}]},
    {"id": "entwerfen"},
    {"pruefung": [{"name": "betraege_korrekt"}]},
])
def test_weak_model_schema_inventions_are_rejected(offer_workstep, changes):
    offer_workstep.update(changes)
    assert list(SCHEMA_REGISTRY.errors("arbeitsschritt", offer_workstep))
