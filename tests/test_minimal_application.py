from pathlib import Path
import shutil
import sys
from tempfile import TemporaryDirectory

import pytest


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from impacts_protocol import validate
from tests.support import read_context, replace_context, write_application, write_context, write_workstep


def issue_codes(root: Path) -> set[str]:
    return {issue.code for issue in validate(root).issues}


def test_valid_application_has_no_issues():
    with TemporaryDirectory() as directory:
        root = write_application(Path(directory) / "video")

        report = validate(root)

        assert report.valid, report.issues


def test_hauptprozess_id_matches_its_folder_slug():
    with TemporaryDirectory() as directory:
        root = write_application(Path(directory) / "video")
        metadata = read_context(root / "CONTEXT.md")
        metadata["id"] = "hauptprozess:anderer-name"
        replace_context(root / "CONTEXT.md", metadata)

        assert "structure.invalid" in issue_codes(root)


def test_application_folder_requires_a_slug():
    with TemporaryDirectory() as directory:
        root = write_application(Path(directory) / "Bad Application")

        assert "structure.invalid" in issue_codes(root)


def test_application_rejects_an_unknown_runtime_subtree():
    with TemporaryDirectory() as directory:
        root = write_application(Path(directory) / "video")
        runtime = root / "produktion" / "start" / "runtime"
        runtime.mkdir()
        (runtime / "state.json").write_text("{}", encoding="utf-8")

        assert "structure.invalid" in issue_codes(root)


def test_application_requires_each_hierarchy_child():
    with TemporaryDirectory() as directory:
        root = write_application(Path(directory) / "video")
        shutil.rmtree(root / "produktion")

        assert "structure.invalid" in issue_codes(root)


def test_application_root_is_its_hauptprozess():
    with TemporaryDirectory() as directory:
        root = write_application(Path(directory) / "video")
        write_context(root / "CONTEXT.md", {"type": "application"}, "# Video")

        assert "routing.type" in issue_codes(root)


def test_application_rejects_a_file_beside_context():
    with TemporaryDirectory() as directory:
        root = write_application(Path(directory) / "video")
        (root / "notizen.md").write_text("frei", encoding="utf-8")

        assert "structure.invalid" in issue_codes(root)


def test_schema_violation_fails_at_public_interface():
    with TemporaryDirectory() as directory:
        root = write_application(Path(directory) / "video")
        path = root / "CONTEXT.md"
        metadata = read_context(path)
        metadata.pop("leistung")
        replace_context(path, metadata)

        assert "schema.invalid" in issue_codes(root)


@pytest.mark.parametrize("body", ["", "   \n\t"])
def test_workstep_requires_a_processing_body(body):
    with TemporaryDirectory() as directory:
        root = write_application(Path(directory) / "video")
        path = root / "produktion/start/CONTEXT.md"
        metadata = read_context(path)
        write_context(path, metadata, body)

        assert "routing.missing" in issue_codes(root)


def test_workstep_ids_are_application_wide_unique():
    with TemporaryDirectory() as directory:
        root = write_application(Path(directory) / "video")
        second = root / "zweite"
        write_context(
            second / "CONTEXT.md",
            {
                "type": "teilprozess",
                "id": "teilprozess:zweite",
                "ergebnis": "Zweites Ergebnis",
            },
        )
        write_workstep(
            second,
            "start",
            step_id="arbeitsschritt:start",
        )

        assert "reference.duplicate" in issue_codes(root)


def test_workstep_id_matches_its_folder_slug():
    with TemporaryDirectory() as directory:
        root = write_application(Path(directory) / "video")
        path = root / "produktion/start/CONTEXT.md"
        metadata = read_context(path)
        metadata["id"] = "arbeitsschritt:anderer-name"
        replace_context(path, metadata)

        assert "structure.invalid" in issue_codes(root)


def test_unresolved_route_is_rejected():
    with TemporaryDirectory() as directory:
        root = write_application(Path(directory) / "video")
        path = root / "produktion/start/CONTEXT.md"
        metadata = read_context(path)
        metadata["routen"] = {"weiter": "arbeitsschritt:fehlt"}
        replace_context(path, metadata)

        assert "reference.unresolved" in issue_codes(root)


def test_unreachable_workstep_is_rejected():
    with TemporaryDirectory() as directory:
        root = write_application(Path(directory) / "video")
        write_workstep(root / "produktion", "verwaist")

        assert "process.unreachable" in issue_codes(root)


def test_every_workstep_needs_a_path_to_end():
    with TemporaryDirectory() as directory:
        root = write_application(Path(directory) / "video")
        path = root / "produktion/pruefen/CONTEXT.md"
        metadata = read_context(path)
        metadata["routen"] = {
            "freigegeben": "arbeitsschritt:start",
            "abgelehnt": "arbeitsschritt:start",
        }
        replace_context(path, metadata)

        assert "process.no_end" in issue_codes(root)


def test_human_gate_has_exact_decision_routes():
    with TemporaryDirectory() as directory:
        root = write_application(Path(directory) / "video")
        path = root / "produktion/pruefen/CONTEXT.md"
        metadata = read_context(path)
        metadata["routen"] = {"ok": "end:fertig"}
        replace_context(path, metadata)

        assert "process.gate" in issue_codes(root)


def test_validation_is_read_only():
    with TemporaryDirectory() as directory:
        root = write_application(Path(directory) / "video")
        before = {
            path.relative_to(root): path.read_bytes()
            for path in root.rglob("*")
            if path.is_file()
        }

        validate(root)

        after = {
            path.relative_to(root): path.read_bytes()
            for path in root.rglob("*")
            if path.is_file()
        }
        assert after == before
