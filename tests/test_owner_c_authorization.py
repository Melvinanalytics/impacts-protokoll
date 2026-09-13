"""Owner C audit — action authorization, human gates, forgery attempts (O4, O7.4).

Authoritative meaning: capabilities.md §Signale und Human-Gates — "Actual
freigegeben/abgelehnt and freigabe come exclusively from the responsible human",
"Core validation neither enforces that preflight nor authenticates a person",
"A written attribution does not authenticate a person". The explicit forgery
below is constructed to prove where the trust boundary actually sits.
"""

from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
import sys
from tempfile import TemporaryDirectory

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from impacts_protocol import validate
from tests.c_owner_support import (
    HUMAN,
    codes,
    committed_workspace,
    entry_active,
    entry_completed,
    make_attempt,
    write_run,
)
from tests.support import read_context, replace_context

CAPABILITIES = ROOT / "02_protocol" / "capabilities.md"
CHECK_PATH = ROOT / "06_evaluations" / "cold-walk" / "check.py"


def _gate_run(root: Path, revision: str, freigabe: dict | None, name="video-001") -> Path:
    run = root / "vorgaenge" / name
    a1 = make_attempt(run, "start", 1, input_bytes="eins", output_bytes="a1")
    p1 = make_attempt(run, "pruefen", 1, input_bytes="zwei", output_bytes="p1")
    entries = [
        entry_completed("start", 1, a1, "weiter"),
        entry_completed("pruefen", 1, p1, "freigegeben", freigabe=freigabe),
    ]
    write_run(root, name, revision, entries)
    return run


def _cold_walk_module():
    spec = spec_from_file_location("impacts_cold_walk_for_audit_c", CHECK_PATH)
    module = module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


# --- O4.3: the explicit forgery attempt ----------------------------------------


def test_forged_human_attribution_passes_only_the_syntactic_check(tmp_path):
    """FORGERY CONSTRUCTED EXPLICITLY: this test is written by an agent, and the
    `human:` attribution below is fabricated by that same agent — no human decided
    anything. Core validation ACCEPTS it, because Core checks attribution SHAPE
    only. This is the documented narrow guarantee, not proof of authorization.
    """
    root, revision = committed_workspace(tmp_path)
    forged = {"by": "human:nicht-vorhanden", "at": "2026-08-30T10:00:00+02:00"}
    _gate_run(root, revision, forged)

    report = validate(root)
    assert report.valid, report.issues  # forgery is structurally indistinguishable

    # The contract must keep disclaiming exactly this; if these sentences vanish,
    # the acceptance above becomes a contract defect.
    text = CAPABILITIES.read_text(encoding="utf-8")
    assert "authenticates" in text and "nor authenticates a person" in text
    assert "A written attribution does not authenticate a person" in (
        ROOT / "02_protocol" / "impacts-method.md"
    ).read_text(encoding="utf-8")


def test_reference_harness_consumes_a_fabricated_fixture_syntactically(tmp_path):
    """The reference harness's human-fixture check is syntactic as well: a
    fabricated decision dict passes close_human. The guarantee is only that the
    decision arrives as an EXTERNAL record, not that a human made it."""
    check = _cold_walk_module()
    with TemporaryDirectory() as directory:
        root, _, _, revision, _ = check._prepare_workspace(Path(directory))
        harness = check.Harness(root, revision)

        # Direct opening of the human gate is refused: it must arrive via handoff.
        with pytest.raises(check.ProofError, match="proven producer handoff"):
            harness.open("entscheiden", 1, {})

        # But a fabricated "human" decision dict is consumed without authentication.
        fabricated = {
            "route": "freigegeben",
            "freigabe": {"by": "human:erfunden", "at": "2026-09-01T09:00:00+02:00"},
            "output": "Prüfbericht: ok\nBegründung: synthetisch gefälscht\n",
        }
        entry = {"arbeitsschritt_ref": "arbeitsschritt:entscheiden", "versuch": 1}
        harness.laufpfad.append(entry)
        harness.close_human(entry, fabricated)  # no ProofError: syntactic check only
        assert entry["freigabe"]["by"] == "human:erfunden"


# --- O4.1/O4.4: structural forgeries ARE rejected -------------------------------


@pytest.mark.parametrize(
    "freigabe",
    [
        {"by": "agent:codex", "at": "2026-08-30T10:00:00+02:00"},
        {"by": "human:", "at": "2026-08-30T10:00:00+02:00"},
        {"by": "human: namenslos", "at": "2026-08-30T10:00:00+02:00"},
        {"by": "Human:gross", "at": "2026-08-30T10:00:00+02:00"},
        {"by": "human:prueferin", "at": "2026-08-30T10:00:00"},  # no timezone
        {"by": "human:prueferin", "at": "bald"},
        {"by": "human:prueferin"},  # missing timestamp
        {"by": "human:prueferin", "at": "2026-08-30T10:00:00+02:00", "rolle": "chef"},
        "human:prueferin",  # not an object
    ],
)
def test_structural_approval_forgeries_are_rejected(tmp_path, freigabe):
    root, revision = committed_workspace(tmp_path)
    _gate_run(root, revision, freigabe)

    report = validate(root)
    assert not report.valid
    assert {"trust.invalid", "schema.invalid"} & {
        issue.code for issue in report.issues
    }, report.issues


def test_missing_approval_on_human_gate_is_rejected(tmp_path):
    root, revision = committed_workspace(tmp_path)
    _gate_run(root, revision, None)

    assert "trust.invalid" in codes(root)


def test_approval_on_non_human_gate_is_rejected(tmp_path):
    root, revision = committed_workspace(tmp_path)
    run = root / "vorgaenge" / "video-001"
    a1 = make_attempt(run, "start", 1, input_bytes="eins", output_bytes="a1")
    # "start" has no gate; an approval here is out of scope for the step.
    entry = entry_completed("start", 1, a1, "weiter", freigabe=HUMAN)
    p1 = make_attempt(run, "pruefen", 1, input_bytes="zwei")
    write_run(root, "video-001", revision, [entry, entry_active("pruefen", 1, p1)])

    assert "trust.invalid" in codes(root)


def test_human_gate_needs_exactly_the_two_gate_routes(tmp_path):
    root, revision = committed_workspace(tmp_path)
    step = root / "applications/video/produktion/pruefen/CONTEXT.md"
    metadata = read_context(step)
    metadata["routen"] = {"freigegeben": "end:video-veroeffentlicht"}  # abgelehnt missing
    replace_context(step, metadata)

    assert "process.gate" in codes(root)


# --- O7.4: writer prevents damage at the harness layer ---------------------------


def test_reference_harness_refuses_to_overwrite_changed_output(tmp_path):
    """_write_outputs binds existing editable files only with their actual current
    bytes: the WRITER prevents stale-draft overwrite; Core's validator only DETECTS."""
    check = _cold_walk_module()
    with TemporaryDirectory() as directory:
        attempt = Path(directory) / "001"
        check._write_files(attempt, {"output/ergebnis.md": "vom Menschen überarbeitet\n"})

        with pytest.raises(check.ProofError, match="Existing output differs"):
            check._write_outputs(attempt, {"output/ergebnis.md": "veralteter Entwurf\n"})

        # Nothing was written: the reviewed draft survives.
        assert (attempt / "output" / "ergebnis.md").read_text(
            encoding="utf-8"
        ) == "vom Menschen überarbeitet\n"

        # Reading the actual bytes first (as the contract demands) succeeds.
        check._write_outputs(
            attempt, {"output/ergebnis.md": "vom Menschen überarbeitet\n"}
        )
