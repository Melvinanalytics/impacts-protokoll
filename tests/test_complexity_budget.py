from contextlib import redirect_stdout
from importlib.util import module_from_spec, spec_from_file_location
from io import StringIO
from pathlib import Path
import shutil
import subprocess
import sys
from tempfile import TemporaryDirectory
import unittest

import yaml


ROOT = Path(__file__).resolve().parents[1]
CHECK_PATH = ROOT / "06_evaluations" / "complexity-budget" / "check.py"
BUDGET_PATH = ROOT / "06_evaluations" / "complexity-budget" / "budget.yaml"


def load_check_module():
    spec = spec_from_file_location("impacts_complexity_budget", CHECK_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot load complexity checker from {CHECK_PATH}")
    module = module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class ComplexityBudgetTests(unittest.TestCase):
    def test_core_budget_uses_version_three_without_approvals(self):
        budget = yaml.safe_load(BUDGET_PATH.read_text(encoding="utf-8"))

        self.assertEqual(3, budget["version"])
        self.assertEqual([], budget["approvals"])
        self.assertEqual(6, budget["limits"]["root_dirs"])

    def test_repository_stays_within_complexity_budget(self):
        check = load_check_module()

        with redirect_stdout(StringIO()) as output:
            exit_code = check.main()

        self.assertEqual(0, exit_code, output.getvalue())
        self.assertIn("Komplexitätsbudget eingehalten.", output.getvalue())

    def test_clean_export_without_private_git_history_uses_portable_baseline(self):
        check = load_check_module()
        with TemporaryDirectory() as directory:
            repository = Path(directory) / "repo"
            _copy_measured_structure(repository)
            budget_path = repository / "06_evaluations/complexity-budget/budget.yaml"
            budget_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(BUDGET_PATH, budget_path)
            check.REPO = repository
            check.HISTORY_REPO = repository
            check.BUDGET = budget_path
            _git(repository, "init", "-b", "main")
            _git(repository, "config", "user.email", "test@example.invalid")
            _git(repository, "config", "user.name", "Test")
            _git(repository, "add", ".")
            _git(repository, "commit", "-m", "fresh public root")

            with redirect_stdout(StringIO()) as output:
                exit_code = check.main()

            self.assertEqual(0, exit_code, output.getvalue())
            self.assertEqual(
                {
                    "root_dirs": 6,
                    "protocol_schemas": 7,
                    "max_total_required_fields_per_schema": 20,
                },
                check.accepted_baseline(),
            )
            self.assertEqual(
                {
                    "root_dirs": 6,
                    "protocol_schemas": 9,
                    "max_total_required_fields_per_schema": 21,
                },
                check.accepted_limits(),
            )

    def test_portable_baseline_rejects_unapproved_budget_raise(self):
        check = load_check_module()
        with TemporaryDirectory() as directory:
            repository = Path(directory) / "repo"
            _copy_measured_structure(repository)
            budget_path = repository / "06_evaluations/complexity-budget/budget.yaml"
            budget_path.parent.mkdir(parents=True, exist_ok=True)
            budget = yaml.safe_load(BUDGET_PATH.read_text(encoding="utf-8"))
            budget["limits"] = {field: 999 for field in budget["limits"]}
            budget_path.write_text(
                yaml.safe_dump(budget, allow_unicode=True, sort_keys=False),
                encoding="utf-8",
            )
            check.REPO = repository
            check.HISTORY_REPO = repository
            check.BUDGET = budget_path
            _git(repository, "init", "-b", "main")
            _git(repository, "config", "user.email", "test@example.invalid")
            _git(repository, "config", "user.name", "Test")
            _git(repository, "add", ".")
            _git(repository, "commit", "-m", "fresh public root")

            with redirect_stdout(StringIO()) as output:
                exit_code = check.main()

            self.assertEqual(1, exit_code)
            self.assertIn("ohne dokumentierte human:-Attribution", output.getvalue())

    def test_invalid_git_metadata_does_not_enable_portable_fallback(self):
        check = load_check_module()
        with TemporaryDirectory() as directory:
            repository = Path(directory) / "repo"
            _copy_measured_structure(repository)
            budget_path = repository / "06_evaluations/complexity-budget/budget.yaml"
            budget_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(BUDGET_PATH, budget_path)
            (repository / ".git").mkdir()
            check.REPO = repository
            check.HISTORY_REPO = repository
            check.BUDGET = budget_path

            with redirect_stdout(StringIO()) as output:
                exit_code = check.main()

        self.assertEqual(1, exit_code)
        self.assertIn("Budget oder Git-Baseline nicht prüfbar", output.getvalue())

    def test_corrupt_baseline_object_does_not_enable_portable_fallback(self):
        check = load_check_module()
        with TemporaryDirectory() as directory:
            repository = Path(directory) / "repo"
            _copy_measured_structure(repository)
            budget_path = repository / "06_evaluations/complexity-budget/budget.yaml"
            budget_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(BUDGET_PATH, budget_path)
            _git(repository, "init", "-b", "main")
            _git(repository, "config", "user.email", "test@example.invalid")
            _git(repository, "config", "user.name", "Test")
            _git(repository, "add", ".")
            _git(repository, "commit", "-m", "fresh public root")
            object_path = (
                repository
                / ".git/objects"
                / check.ACCEPTED_BASELINE_REVISION[:2]
                / check.ACCEPTED_BASELINE_REVISION[2:]
            )
            object_path.parent.mkdir(parents=True, exist_ok=True)
            object_path.write_bytes(b"corrupt")
            check.REPO = repository
            check.HISTORY_REPO = repository
            check.BUDGET = budget_path

            with redirect_stdout(StringIO()) as output:
                exit_code = check.main()

        self.assertEqual(1, exit_code)
        self.assertIn("Budget oder Git-Baseline nicht prüfbar", output.getvalue())

    @unittest.skipIf(sys.platform == "win32", "symlink creation is not portable on Windows")
    def test_broken_git_symlink_does_not_enable_portable_fallback(self):
        check = load_check_module()
        with TemporaryDirectory() as directory:
            repository = Path(directory) / "repo"
            _copy_measured_structure(repository)
            budget_path = repository / "06_evaluations/complexity-budget/budget.yaml"
            budget_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(BUDGET_PATH, budget_path)
            (repository / ".git").symlink_to(repository / "missing-git-dir")
            check.REPO = repository
            check.HISTORY_REPO = repository
            check.BUDGET = budget_path

            with redirect_stdout(StringIO()) as output:
                exit_code = check.main()

        self.assertEqual(1, exit_code)
        self.assertIn("Budget oder Git-Baseline nicht prüfbar", output.getvalue())

    def test_unapproved_root_directories_break_the_ratchet(self):
        check = load_check_module()
        with TemporaryDirectory() as directory:
            repository = Path(directory) / "repo"
            _copy_measured_structure(repository)
            (repository / "03_wissen").mkdir()
            (repository / "07_framework").mkdir()
            check.REPO = repository

            with redirect_stdout(StringIO()) as output:
                exit_code = check.main()

        self.assertEqual(1, exit_code)
        self.assertIn("Budget verletzt: root_dirs", output.getvalue())

    def test_budget_file_cannot_raise_its_own_ceiling(self):
        check = load_check_module()
        with TemporaryDirectory() as directory:
            budget_path = Path(directory) / "budget.yaml"
            budget = yaml.safe_load(check.BUDGET.read_text(encoding="utf-8"))
            budget["limits"] = {field: 999 for field in budget["limits"]}
            budget_path.write_text(
                yaml.safe_dump(budget, allow_unicode=True, sort_keys=False),
                encoding="utf-8",
            )
            check.BUDGET = budget_path

            with redirect_stdout(StringIO()) as output:
                exit_code = check.main()

        self.assertEqual(1, exit_code)
        self.assertIn("ohne dokumentierte human:-Attribution", output.getvalue())

    def test_budget_file_rejects_nonhuman_attribution(self):
        check = load_check_module()
        with TemporaryDirectory() as directory:
            budget_path = Path(directory) / "budget.yaml"
            budget = yaml.safe_load(check.BUDGET.read_text(encoding="utf-8"))
            baseline = check.accepted_baseline()
            budget["limits"]["root_dirs"] = baseline["root_dirs"] + 1
            budget["approvals"] = [{
                "field": "root_dirs",
                "from": baseline["root_dirs"],
                "to": baseline["root_dirs"] + 1,
                "approved_by": "agent:codex",
                "reason": "self approval",
            }]
            budget_path.write_text(
                yaml.safe_dump(budget, allow_unicode=True, sort_keys=False),
                encoding="utf-8",
            )
            check.BUDGET = budget_path

            with redirect_stdout(StringIO()) as output:
                exit_code = check.main()

        self.assertEqual(1, exit_code)
        self.assertIn("approved_by human:<id>", output.getvalue())

    def test_empty_human_identity_is_rejected(self):
        check = load_check_module()
        with TemporaryDirectory() as directory:
            budget_path = Path(directory) / "budget.yaml"
            budget = yaml.safe_load(check.BUDGET.read_text(encoding="utf-8"))
            budget["approvals"] = [{
                "field": "root_dirs",
                "from": 6,
                "to": 7,
                "approved_by": "human:",
                "reason": "invalid identity",
            }]
            budget_path.write_text(yaml.safe_dump(budget, sort_keys=False), encoding="utf-8")
            check.BUDGET = budget_path

            with redirect_stdout(StringIO()) as output:
                exit_code = check.main()

        self.assertEqual(1, exit_code)
        self.assertIn("approved_by", output.getvalue())

    def test_main_commit_cannot_use_its_own_measurement_as_baseline(self):
        check = load_check_module()
        with TemporaryDirectory() as directory:
            repository = _budget_repository(Path(directory) / "repo")
            check.ACCEPTED_BASELINE_REVISION = _git_output(
                repository, "rev-parse", "HEAD"
            ).strip()
            (repository / "06_growth").mkdir()
            (repository / "06_growth/.keep").write_text("candidate", encoding="utf-8")
            _git(repository, "add", ".")
            _git(repository, "commit", "-m", "unapproved main growth")
            budget_path = _budget_file(repository, root_dirs=7)
            check.REPO = repository
            check.HISTORY_REPO = repository
            check.BUDGET = budget_path

            with redirect_stdout(StringIO()) as output:
                exit_code = check.main()

        self.assertEqual(1, exit_code)
        self.assertIn("Budgeterhöhung ohne dokumentierte human:-Attribution: root_dirs 6 -> 7", output.getvalue())

    def test_two_main_commits_cannot_launder_budget_growth(self):
        check = load_check_module()
        with TemporaryDirectory() as directory:
            repository = _budget_repository(Path(directory) / "repo")
            check.ACCEPTED_BASELINE_REVISION = _git_output(
                repository, "rev-parse", "HEAD"
            ).strip()
            (repository / "06_growth").mkdir()
            (repository / "06_growth/.keep").write_text("candidate", encoding="utf-8")
            _git(repository, "add", ".")
            _git(repository, "commit", "-m", "growth before budget")
            budget_path = _budget_file(repository, root_dirs=7)
            _git(repository, "add", "budget.yaml")
            _git(repository, "commit", "-m", "raise budget after growth")
            check.REPO = repository
            check.HISTORY_REPO = repository
            check.BUDGET = budget_path

            with redirect_stdout(StringIO()) as output:
                exit_code = check.main()

        self.assertEqual(1, exit_code)
        self.assertIn(
            "Budgeterhöhung ohne dokumentierte human:-Attribution: root_dirs 6 -> 7",
            output.getvalue(),
        )

    def test_later_commit_cannot_launder_budget_growth(self):
        check = load_check_module()
        with TemporaryDirectory() as directory:
            repository = _budget_repository(Path(directory) / "repo")
            check.ACCEPTED_BASELINE_REVISION = _git_output(
                repository, "rev-parse", "HEAD"
            ).strip()
            (repository / "06_growth").mkdir()
            (repository / "06_growth/.keep").write_text(
                "candidate", encoding="utf-8"
            )
            _git(repository, "add", ".")
            _git(repository, "commit", "-m", "growth before budget")
            budget_path = _budget_file(repository, root_dirs=7)
            _git(repository, "add", "budget.yaml")
            _git(repository, "commit", "-m", "raise budget after growth")
            (repository / "README.md").write_text("later commit\n", encoding="utf-8")
            _git(repository, "add", "README.md")
            _git(repository, "commit", "-m", "unrelated later commit")
            check.REPO = repository
            check.HISTORY_REPO = repository
            check.BUDGET = budget_path

            with redirect_stdout(StringIO()) as output:
                exit_code = check.main()

        self.assertEqual(1, exit_code)
        self.assertIn(
            "Budgeterhöhung ohne dokumentierte human:-Attribution: root_dirs 6 -> 7",
            output.getvalue(),
        )

    def test_single_root_main_commit_uses_its_bootstrap_head(self):
        check = load_check_module()
        with TemporaryDirectory() as directory:
            repository = _budget_repository(Path(directory) / "repo")
            check.HISTORY_REPO = repository
            head = _git_output(repository, "rev-parse", "HEAD").strip()
            check.ACCEPTED_BASELINE_REVISION = head

            baseline = check._baseline_revision()

        self.assertEqual(head, baseline)

    def test_human_attribution_is_generic(self):
        check = load_check_module()
        with TemporaryDirectory() as directory:
            budget_path = Path(directory) / "budget.yaml"
            baseline = check.accepted_baseline()
            actual = check.measure()
            budget_path.write_text(
                yaml.safe_dump(
                    {
                        "version": 3,
                        "limits": {
                            "root_dirs": baseline["root_dirs"] + 1,
                            "protocol_schemas": actual["protocol_schemas"],
                            "max_total_required_fields_per_schema": actual["max_total_required_fields_per_schema"],
                        },
                        "approvals": [{
                            "field": "root_dirs",
                            "from": baseline["root_dirs"],
                            "to": baseline["root_dirs"] + 1,
                            "approved_by": "human:reviewer-17",
                            "reason": "fixture attribution",
                        }],
                    },
                    allow_unicode=True,
                    sort_keys=False,
                ),
                encoding="utf-8",
            )
            check.BUDGET = budget_path

            with redirect_stdout(StringIO()) as output:
                exit_code = check.main()

        self.assertEqual(0, exit_code, output.getvalue())
        self.assertIn("Komplexitätsbudget eingehalten.", output.getvalue())

    def test_feature_commit_cannot_become_its_own_baseline(self):
        check = load_check_module()
        with TemporaryDirectory() as directory:
            repository = Path(directory) / "repo"
            schema_dir = repository / "02_protocol/schemas"
            schema_dir.mkdir(parents=True)
            for name in ("00_a", "01_b", "03_c", "04_d", "05_e"):
                (repository / name).mkdir()
                (repository / name / ".keep").write_text("baseline", encoding="utf-8")
            (schema_dir / "one.json").write_text(
                '{"type":"object","required":["id"],"properties":{"id":{"type":"string"}}}',
                encoding="utf-8",
            )
            _git(repository, "init", "-b", "main")
            _git(repository, "config", "user.email", "test@example.invalid")
            _git(repository, "config", "user.name", "Test")
            _git(repository, "add", ".")
            _git(repository, "commit", "-m", "baseline")
            baseline = _git_output(repository, "rev-parse", "HEAD").strip()
            _git(repository, "switch", "-c", "feature")
            (repository / "06_growth").mkdir()
            (repository / "06_growth/.keep").write_text("candidate", encoding="utf-8")
            _git(repository, "add", ".")
            _git(repository, "commit", "-m", "candidate growth")
            budget_path = repository / "budget.yaml"
            budget_path.write_text(
                "version: 3\nlimits:\n  root_dirs: 7\n  protocol_schemas: 1\n"
                "  max_total_required_fields_per_schema: 1\napprovals: []\n",
                encoding="utf-8",
            )
            check.REPO = repository
            check.HISTORY_REPO = repository
            check.BUDGET = budget_path
            check.ACCEPTED_BASELINE_REVISION = baseline

            with redirect_stdout(StringIO()) as output:
                exit_code = check.main()

        self.assertEqual(1, exit_code)
        self.assertIn("Budgeterhöhung ohne dokumentierte human:-Attribution: root_dirs 6 -> 7", output.getvalue())

    def test_schema_budget_counts_required_fields(self):
        check = load_check_module()

        actual = check.measure()

        self.assertIn("max_total_required_fields_per_schema", actual)
        self.assertNotIn("max_required_fields_per_schema", actual)
        self.assertNotIn("max_properties_per_schema", actual)

    def test_build_directories_are_not_architecture(self):
        check = load_check_module()
        with TemporaryDirectory() as directory:
            repository = Path(directory) / "repo"
            _copy_measured_structure(repository)
            (repository / "build").mkdir(exist_ok=True)
            (repository / "impacts_protocol.egg-info").mkdir(exist_ok=True)
            check.REPO = repository

            actual = check.measure()

        self.assertNotIn("build", actual["root_dir_names"])
        self.assertNotIn("impacts_protocol.egg-info", actual["root_dir_names"])
        self.assertEqual(6, actual["root_dirs"])

    def test_schema_budget_counts_nested_required_fields(self):
        check = load_check_module()
        with TemporaryDirectory() as directory:
            repository = Path(directory) / "repo"
            schema_dir = repository / "02_protocol" / "schemas"
            schema_dir.mkdir(parents=True)
            (schema_dir / "nested.json").write_text(
                '{"type":"object","required":["root"],"properties":'
                '{"root":{"type":"object","required":["left","right"]}}}',
                encoding="utf-8",
            )
            check.REPO = repository

            actual = check.measure()

        self.assertEqual(3, actual["required_field_counts"]["nested.json"])


def _copy_measured_structure(repository: Path) -> None:
    repository.mkdir()
    for path in ROOT.iterdir():
        if (
            path.is_dir()
            and path.name not in {".git", ".superpowers", "__pycache__", ".pytest_cache", ".venv", "node_modules", "build"}
            and not path.name.endswith(".egg-info")
        ):
            (repository / path.name).mkdir()
    shutil.copytree(
        ROOT / "02_protocol" / "schemas",
        repository / "02_protocol" / "schemas",
        dirs_exist_ok=True,
    )


def _budget_repository(repository: Path) -> Path:
    schema_dir = repository / "02_protocol/schemas"
    schema_dir.mkdir(parents=True)
    for name in ("00_a", "01_b", "03_c", "04_d", "05_e"):
        (repository / name).mkdir()
        (repository / name / ".keep").write_text("baseline", encoding="utf-8")
    (schema_dir / "one.json").write_text(
        '{"type":"object","required":["id"],"properties":{"id":{"type":"string"}}}',
        encoding="utf-8",
    )
    _budget_file(repository, root_dirs=6)
    _git(repository, "init", "-b", "main")
    _git(repository, "config", "user.email", "test@example.invalid")
    _git(repository, "config", "user.name", "Test")
    _git(repository, "add", ".")
    _git(repository, "commit", "-m", "baseline")
    return repository


def _budget_file(repository: Path, *, root_dirs: int) -> Path:
    path = repository / "budget.yaml"
    path.write_text(
        "version: 3\n"
        "limits:\n"
        f"  root_dirs: {root_dirs}\n"
        "  protocol_schemas: 1\n"
        "  max_total_required_fields_per_schema: 1\n"
        "approvals: []\n",
        encoding="utf-8",
    )
    return path


def _git(repository: Path, *args: str) -> None:
    subprocess.run(["git", "-C", str(repository), *args], check=True, capture_output=True, text=True)


def _git_output(repository: Path, *args: str) -> str:
    return subprocess.check_output(["git", "-C", str(repository), *args], text=True)


if __name__ == "__main__":
    unittest.main()
