from pathlib import Path
import json
import os
import subprocess
import sys
from tempfile import TemporaryDirectory


ROOT = Path(__file__).resolve().parents[1]

import impacts_protocol
import impacts_protocol.validator as validator
from impacts_protocol import init_workspace, validate


def test_package_import_does_not_load_validator_dependencies():
    environment = os.environ.copy()
    environment["PYTHONPATH"] = str(ROOT / "src")
    process = subprocess.run(
        [sys.executable, "-c", "import impacts_protocol, sys, json; "
         "print(json.dumps(sorted(name for name in sys.modules if "
         "name == 'impacts_protocol.validator' or "
         "name == 'yaml' or name.startswith(('yaml.', 'jsonschema', 'referencing')))))"],
        cwd=ROOT, env=environment, capture_output=True, text=True,
    )
    assert process.returncode == 0, process.stderr
    assert json.loads(process.stdout) == []


def test_public_validate_import_loads_yaml():
    environment = os.environ.copy()
    environment["PYTHONPATH"] = str(ROOT / "src")
    process = subprocess.run(
        [sys.executable, "-c", "from impacts_protocol import validate; "
         "import json, sys; print(json.dumps(sorted(name for name in sys.modules "
         "if name in ('impacts_protocol.validator', 'yaml'))))"],
        cwd=ROOT, env=environment, capture_output=True, text=True,
    )
    assert process.returncode == 0, process.stderr
    assert json.loads(process.stdout) == ["impacts_protocol.validator", "yaml"]


def test_public_validate_is_original_callable_and_repeated_results_match():
    from impacts_protocol.validator import validate as implementation

    assert validate is implementation
    with TemporaryDirectory() as directory:
        root = init_workspace(Path(directory) / "workspace")
        assert validate(root) == validate(root)


def test_public_api_contains_only_minimal_contract():
    assert set(impacts_protocol.__all__) == {
        "HashSurfaceError",
        "Issue",
        "ValidationReport",
        "init_workspace",
        "surface_hash",
        "validate",
    }
    assert not hasattr(validator, "validate_workspace")
    assert not hasattr(validator, "validate_application")


def test_retired_core_surfaces_are_absent():
    assert not (ROOT / "00_charter").exists()
    schemas = ROOT / "02_protocol" / "schemas"
    assert {path.name for path in schemas.glob("*.json")} == {
        "leistung.schema.json",
        "hauptprozess.schema.json",
        "teilprozess.schema.json",
        "arbeitsschritt.schema.json",
        "vorgang.schema.json",
    }


def test_missing_router_fails_closed():
    with TemporaryDirectory() as directory:
        root = init_workspace(Path(directory) / "workspace")
        (root / "CONTEXT.md").unlink()

        assert {issue.code for issue in validate(root).issues} == {"routing.missing"}


def test_invalid_frontmatter_fails_closed():
    with TemporaryDirectory() as directory:
        root = init_workspace(Path(directory) / "workspace")
        (root / "CONTEXT.md").write_text("---\ntype: [\n---\n", encoding="utf-8")

        assert "format.invalid" in {issue.code for issue in validate(root).issues}


def test_router_type_and_exclusive_frontmatter_are_enforced():
    with TemporaryDirectory() as directory:
        root = init_workspace(Path(directory) / "workspace")
        (root / "CONTEXT.md").write_text(
            "---\ntype: workspace\nname: duplicate-authority\n---\n",
            encoding="utf-8",
        )

        assert "routing.type" in {issue.code for issue in validate(root).issues}

        (root / "CONTEXT.md").write_text("---\ntype: unknown\n---\n", encoding="utf-8")
        assert "routing.type" in {issue.code for issue in validate(root).issues}

        (root / "CONTEXT.md").write_text(
            "---\ntype: [workspace]\n---\n", encoding="utf-8"
        )
        assert "routing.type" in {issue.code for issue in validate(root).issues}


def test_core_folder_symlink_fails_closed():
    with TemporaryDirectory() as directory:
        base = Path(directory)
        root = init_workspace(base / "workspace")
        (root / "applications").rmdir()
        (root / "applications").symlink_to(base, target_is_directory=True)

        assert "structure.symlink" in {issue.code for issue in validate(root).issues}


def test_workspace_root_symlink_fails_closed():
    with TemporaryDirectory() as directory:
        base = Path(directory)
        root = init_workspace(base / "workspace")
        alias = base / "workspace-alias"
        alias.symlink_to(root, target_is_directory=True)

        assert "structure.symlink" in {issue.code for issue in validate(alias).issues}


def test_customer_owned_extra_folder_is_outside_core_validation():
    with TemporaryDirectory() as directory:
        root = init_workspace(Path(directory) / "workspace")
        (root / "customer-notes").mkdir()
        (root / "customer-notes" / "note.md").write_text("frei", encoding="utf-8")

        assert validate(root).valid


def test_filesystem_scan_error_fails_closed(monkeypatch):
    with TemporaryDirectory() as directory:
        root = init_workspace(Path(directory) / "workspace")
        original = Path.iterdir

        def fail_for_applications(path):
            if path == root / "applications":
                raise PermissionError("denied")
            return original(path)

        monkeypatch.setattr(Path, "iterdir", fail_for_applications)

        assert "structure.invalid" in {issue.code for issue in validate(root).issues}
