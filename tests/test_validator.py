from dataclasses import FrozenInstanceError
from pathlib import Path
import shutil
import sys
from tempfile import TemporaryDirectory
import unittest

import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from impacts_protocol import validate_application, validate_workspace
from impacts_protocol.io import load_frontmatter, load_yaml
from impacts_protocol.model import Issue, ValidationReport
from impacts_protocol.generator import generate_workspace


FIXTURES = Path(__file__).parent / "fixtures"
APPLICATION_ROUTER_PATHS = (
    "CONTEXT.md",
    "00_steuerung/leistungen/gutachten/CONTEXT.md",
    "01_prozesse/gutachten/CONTEXT.md",
    "01_prozesse/gutachten/teilprozesse/pruefung/CONTEXT.md",
    "01_prozesse/gutachten/teilprozesse/pruefung/arbeitsschritte/01_pruefen/CONTEXT.md",
)


class ValidatorTests(unittest.TestCase):
    def test_valid_workspace_has_no_issues(self):
        with self.workspace_copy() as root:
            report = validate_workspace(root)
            self.assertTrue(report.valid, report.issues)

    def test_dead_end_is_rejected(self):
        report = validate_application(FIXTURES / "dead-end-application-package")
        self.assertIn("bpm.dead_end", {issue.code for issue in report.issues})

    def test_application_requires_part_processes_and_worksteps(self):
        with self.application_copy() as root:
            shutil.rmtree(root / "01_prozesse/gutachten/teilprozesse")

            report = validate_application(root)

        self.assertIn("hierarchy.missing_child", {issue.code for issue in report.issues})

    def test_application_requires_process_roots(self):
        with TemporaryDirectory() as directory:
            root = Path(directory) / "empty-application"
            root.mkdir()
            (root / "README.md").write_text("# Empty\n", encoding="utf-8")

            report = validate_application(root)

        self.assertIn("hierarchy.missing_root", {issue.code for issue in report.issues})

    def test_application_requires_canonical_routers(self):
        for relative in APPLICATION_ROUTER_PATHS:
            with self.subTest(relative=relative), self.application_copy() as root:
                (root / relative).unlink()

                report = validate_application(root)

            self.assertIn(
                "routing.missing_router",
                {issue.code for issue in report.issues},
                report.issues,
            )

    def test_application_routers_require_type_frontmatter(self):
        router_contents = (
            "# Router without frontmatter\n",
            "---\ntitle: Router without type\n---\n\n# Router\n",
        )
        for relative in APPLICATION_ROUTER_PATHS:
            for content in router_contents:
                with (
                    self.subTest(relative=relative, content=content),
                    self.application_copy() as root,
                ):
                    (root / relative).write_text(content, encoding="utf-8")

                    report = validate_application(root)

                self.assertIn(
                    "routing.missing_type",
                    {issue.code for issue in report.issues},
                    report.issues,
                )

    def test_valid_application_package_has_no_issues(self):
        report = validate_application(FIXTURES / "application-package")

        self.assertTrue(report.valid, report.issues)

    def test_application_rejects_invalid_frontmatter(self):
        with self.application_copy() as root:
            (root / "notes.md").write_text("---\ninvalid: [\n---\n", encoding="utf-8")

            report = validate_application(root)

        self.assertIn("format.invalid_frontmatter", {issue.code for issue in report.issues})

    def test_application_rejects_invalid_json(self):
        with self.application_copy() as root:
            (root / "data.json").write_text('{"broken":', encoding="utf-8")

            report = validate_application(root)

        self.assertIn("format.invalid_json", {issue.code for issue in report.issues})

    def test_router_aliases_are_rejected_case_insensitively(self):
        for alias in ("context.md", "Kontext.md", "KONTEXT.md"):
            with self.subTest(alias=alias), self.workspace_copy() as root:
                (root / "CONTEXT.md").unlink()
                (root / alias).write_text("falscher Router", encoding="utf-8")

                report = validate_workspace(root)

                self.assertIn(
                    "routing.noncanonical_filename",
                    {issue.code for issue in report.issues},
                )

    def test_missing_canonical_router_is_rejected(self):
        with self.workspace_copy() as root:
            (root / "CONTEXT.md").unlink()

            report = validate_workspace(root)

        self.assertIn("routing.missing_router", {issue.code for issue in report.issues})

    def test_schema_violation_is_rejected(self):
        with self.application_copy() as root:
            path = root / "00_steuerung/leistungen/gutachten/leistung.yaml"
            document = load_yaml(path)
            document["unexpected"] = True
            path.write_text(yaml.safe_dump(document), encoding="utf-8")

            report = validate_application(root)

        self.assertIn("schema.invalid", {issue.code for issue in report.issues})

    def test_schema_invalid_graph_fields_do_not_crash_validation(self):
        nodes = [{"id": "start", "type": "task", "next": None}]

        report = self.validate_nodes(nodes)

        self.assertIn("schema.invalid", {issue.code for issue in report.issues})

    def test_malformed_yaml_and_frontmatter_are_rejected(self):
        with self.workspace_copy() as root:
            yaml_path = root / "02_grundlagen/broken.yaml"
            yaml_path.write_text("id: [", encoding="utf-8")
            router = root / "CONTEXT.md"
            router.write_text("---\ntitle: [\n---\n", encoding="utf-8")

            report = validate_workspace(root)

        codes = {issue.code for issue in report.issues}
        self.assertIn("format.invalid_yaml", codes)
        self.assertIn("format.invalid_frontmatter", codes)

    def test_nested_duplicate_node_type_is_rejected_without_crashing(self):
        with self.application_copy() as root:
            path = root / "01_prozesse/gutachten/hauptprozess.yaml"
            path.write_text(
                path.read_text(encoding="utf-8").replace(
                    "    type: task\n",
                    "    type: end\n    type: task\n",
                ),
                encoding="utf-8",
            )

            report = validate_application(root)

        matching = [
            issue for issue in report.issues if issue.code == "format.invalid_yaml"
        ]
        self.assertTrue(matching, report.issues)
        self.assertTrue(any("duplicate key" in issue.message for issue in matching))
        self.assertTrue(any("type" in issue.message for issue in matching))

    def test_unclassified_yaml_with_nested_duplicate_key_is_rejected(self):
        with self.workspace_copy() as root:
            path = root / "operator-notes.yaml"
            path.write_text(
                "metadata:\n  type: first\n  type: second\n",
                encoding="utf-8",
            )

            report = validate_workspace(root)

        matching = [
            issue
            for issue in report.issues
            if issue.code == "format.invalid_yaml"
            and issue.path == "operator-notes.yaml"
        ]
        self.assertTrue(matching, report.issues)
        self.assertIn("duplicate key", matching[0].message)

    def test_unclassified_yaml_symlink_outside_workspace_is_rejected(self):
        with self.workspace_copy() as root:
            external = root.parent / "external-notes.yaml"
            external.write_text("metadata:\n  type: note\n", encoding="utf-8")
            path = root / "operator-notes.yaml"
            path.symlink_to(external)

            report = validate_workspace(root)

        matching = [
            issue
            for issue in report.issues
            if issue.code == "structure.symlink"
            and issue.path == "operator-notes.yaml"
        ]
        self.assertTrue(matching, report.issues)

    def test_topology_yaml_symlink_outside_workspace_is_rejected(self):
        with self.application_copy() as root:
            path = root / "01_prozesse/gutachten/hauptprozess.yaml"
            external = root.parent / "external-hauptprozess.yaml"
            external.write_text(path.read_text(encoding="utf-8"), encoding="utf-8")
            path.unlink()
            path.symlink_to(external)

            report = validate_application(root)

        self.assertIn(
            "structure.symlink",
            {issue.code for issue in report.issues},
            report.issues,
        )

    def test_leistung_and_hauptprozess_must_be_reciprocal(self):
        with self.application_copy() as root:
            path = root / "01_prozesse/gutachten/hauptprozess.yaml"
            path.write_text(
                "id: hauptprozess:gutachten\nleistung_ref: leistung:unbekannt\n",
                encoding="utf-8",
            )

            report = validate_application(root)

        self.assertIn(
            "reference.nonreciprocal", {issue.code for issue in report.issues}
        )

    def test_process_parent_references_must_match_containment(self):
        with self.application_copy() as root:
            teilprozess = (
                root
                / "01_prozesse/gutachten/teilprozesse/pruefung/teilprozess.yaml"
            )
            teilprozess.write_text(
                "id: teilprozess:pruefung\nhauptprozess_ref: hauptprozess:falsch\n",
                encoding="utf-8",
            )
            arbeitsschritt = root / (
                "01_prozesse/gutachten/teilprozesse/pruefung/"
                "arbeitsschritte/01_pruefen/arbeitsschritt.yaml"
            )
            arbeitsschritt.write_text(
                "id: arbeitsschritt:pruefen\nteilprozess_ref: teilprozess:falsch\n",
                encoding="utf-8",
            )

            report = validate_application(root)

        codes = {issue.code for issue in report.issues}
        self.assertIn("reference.process_parent", codes)

    def test_process_documents_must_live_in_canonical_containment(self):
        with self.application_copy() as root:
            source = root / "01_prozesse/gutachten/hauptprozess.yaml"
            misplaced = root / "hauptprozess.yaml"
            source.rename(misplaced)

            report = validate_application(root)

        self.assertIn("structure.containment", {issue.code for issue in report.issues})

    def test_vorgang_may_reference_hauptprozess_from_application_package(self):
        with self.workspace_copy() as root:
            path = root / "06_vorgaenge/gutachten-001/vorgang.yaml"
            path.parent.mkdir()
            for name in ("snapshot", "receipts", "freigaben"):
                (path.parent / name).mkdir()
            path.write_text(
                "id: vorgang:gutachten-001\n"
                "hauptprozess_ref: hauptprozess:externes-paket\n"
                "status: in_pruefung\n"
                "run_id: run:vorgang-gutachten-001\n"
                "receipt_refs: [receipt:vorgang-gutachten-001]\n",
                encoding="utf-8",
            )

            report = validate_workspace(root)

        self.assertNotIn("reference.vorgang", {issue.code for issue in report.issues})

    def test_unresolved_targets_and_unreachable_nodes_are_rejected(self):
        nodes = [
            {"id": "start", "type": "task", "next": ["fehlt"]},
            {"id": "verwaist", "type": "end", "next": [], "event": "Fertig"},
        ]

        report = self.validate_nodes(nodes)

        codes = {issue.code for issue in report.issues}
        self.assertIn("bpm.unresolved_target", codes)
        self.assertIn("bpm.unreachable", codes)

    def test_gateway_requires_complete_routes(self):
        nodes = [
            {"id": "start", "type": "gateway", "next": [], "routes": []},
        ]

        report = self.validate_nodes(nodes)

        self.assertIn("bpm.incomplete_gateway", {issue.code for issue in report.issues})

    def test_wait_requires_trigger_and_continuation(self):
        nodes = [{"id": "start", "type": "wait", "next": []}]

        report = self.validate_nodes(nodes)

        self.assertIn("bpm.wait_trigger", {issue.code for issue in report.issues})

    def test_handoff_requires_artifact_and_consumer(self):
        nodes = [{"id": "start", "type": "handoff", "next": []}]

        report = self.validate_nodes(nodes)

        self.assertIn("bpm.handoff_consumer", {issue.code for issue in report.issues})

    def test_end_requires_named_event(self):
        nodes = [{"id": "start", "type": "end", "next": []}]

        report = self.validate_nodes(nodes)

        self.assertIn("bpm.unnamed_end", {issue.code for issue in report.issues})

    def test_cycle_requires_explicit_continuation_or_exit_condition(self):
        nodes = [
            {"id": "start", "type": "task", "next": ["repeat"]},
            {"id": "repeat", "type": "task", "next": ["start"]},
        ]

        report = self.validate_nodes(nodes)

        self.assertIn(
            "bpm.cycle_without_condition", {issue.code for issue in report.issues}
        )

    def test_declared_cycle_is_a_complete_path(self):
        nodes = [
            {"id": "start", "type": "task", "next": ["repeat"]},
            {
                "id": "repeat",
                "type": "task",
                "next": ["start"],
                "continuation_condition": "Neue Eingabe liegt vor",
            },
        ]

        report = self.validate_nodes(nodes)

        bpm_codes = {issue.code for issue in report.issues if issue.code.startswith("bpm.")}
        self.assertEqual(set(), bpm_codes, report.issues)

    def test_exit_condition_cycle_requires_exit_to_complete_outcome(self):
        nodes = [
            {"id": "start", "type": "task", "next": ["repeat"]},
            {
                "id": "repeat",
                "type": "task",
                "next": ["start"],
                "exit_condition": "Prüfung abgeschlossen",
            },
        ]

        report = self.validate_nodes(nodes)

        self.assertIn(
            "bpm.cycle_without_condition", {issue.code for issue in report.issues}
        )

    def test_exit_condition_cycle_with_complete_exit_is_valid(self):
        nodes = [
            {"id": "start", "type": "task", "next": ["repeat"]},
            {
                "id": "repeat",
                "type": "task",
                "next": ["start", "finished"],
                "exit_condition": "Prüfung abgeschlossen",
            },
            {"id": "finished", "type": "end", "next": [], "event": "Fertig"},
        ]

        report = self.validate_nodes(nodes)

        bpm_codes = {issue.code for issue in report.issues if issue.code.startswith("bpm.")}
        self.assertEqual(set(), bpm_codes, report.issues)

    def test_gateway_route_condition_declares_cycle_continuation(self):
        nodes = [
            {
                "id": "start",
                "type": "gateway",
                "next": [],
                "routes": [{"condition": "Wiederholen", "target": "start"}],
            }
        ]

        report = self.validate_nodes(nodes)

        bpm_codes = {issue.code for issue in report.issues if issue.code.startswith("bpm.")}
        self.assertEqual(set(), bpm_codes, report.issues)

    def test_gateway_rejects_unconditioned_next_edges(self):
        nodes = [
            {
                "id": "start",
                "type": "gateway",
                "next": ["bypass"],
                "routes": [{"condition": "Regulär", "target": "finished"}],
            },
            {"id": "finished", "type": "end", "next": [], "event": "Fertig"},
            {"id": "bypass", "type": "end", "next": [], "event": "Umgangen"},
        ]

        report = self.validate_nodes(nodes)

        self.assertIn("bpm.incomplete_gateway", {issue.code for issue in report.issues})

    def test_non_gateway_routes_cannot_validate_an_exitless_cycle(self):
        nodes = [
            {
                "id": "start",
                "type": "task",
                "next": ["repeat"],
                "routes": [{"condition": "Wiederholen", "target": "start"}],
            },
            {"id": "repeat", "type": "task", "next": ["start"]},
        ]

        report = self.validate_nodes(nodes)

        codes = {issue.code for issue in report.issues}
        self.assertIn("schema.invalid", codes)
        self.assertIn("bpm.invalid_routes", codes)
        self.assertIn("bpm.cycle_without_condition", codes)

    def test_gateway_routes_can_exit_cycle_to_named_end(self):
        nodes = [
            {
                "id": "decide",
                "type": "gateway",
                "next": [],
                "routes": [
                    {"condition": "Wiederholen", "target": "repeat"},
                    {"condition": "Fertig", "target": "finished"},
                ],
            },
            {"id": "repeat", "type": "task", "next": ["decide"]},
            {"id": "finished", "type": "end", "next": [], "event": "Fertig"},
        ]

        report = self.validate_nodes(nodes, entry="decide")

        bpm_codes = {issue.code for issue in report.issues if issue.code.startswith("bpm.")}
        self.assertEqual(set(), bpm_codes, report.issues)

    def test_report_types_are_immutable(self):
        issue = Issue("demo", "CONTEXT.md", "Demo")
        report = ValidationReport((issue,))

        with self.assertRaises(FrozenInstanceError):
            issue.code = "changed"  # type: ignore[misc]
        with self.assertRaises(FrozenInstanceError):
            report.issues = ()  # type: ignore[misc]
        self.assertFalse(report.valid)

    def test_yaml_and_frontmatter_readers_return_mappings(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            yaml_path = root / "record.yaml"
            yaml_path.write_text("id: demo\n", encoding="utf-8")
            markdown_path = root / "CONTEXT.md"
            markdown_path.write_text("---\ntitle: Demo\n---\nText\n", encoding="utf-8")

            self.assertEqual({"id": "demo"}, load_yaml(yaml_path))
            self.assertEqual({"title": "Demo"}, load_frontmatter(markdown_path))

    def validate_nodes(
        self, nodes: list[dict[str, object]], entry: str = "start"
    ) -> ValidationReport:
        with self.application_copy() as root:
            path = root / "01_prozesse/gutachten/hauptprozess.yaml"
            path.write_text(
                yaml.safe_dump(
                    {
                        "id": "hauptprozess:gutachten",
                        "leistung_ref": "leistung:gutachten",
                        "entry": entry,
                        "nodes": nodes,
                    },
                    sort_keys=False,
                ),
                encoding="utf-8",
            )
            return validate_application(root)

    def workspace_copy(self):
        temporary_directory = TemporaryDirectory()
        root = generate_workspace(
            Path(temporary_directory.name) / "workspace", "demo-kunde"
        )

        class WorkspaceContext:
            def __enter__(self):
                return root

            def __exit__(self, exc_type, exc_value, traceback):
                temporary_directory.cleanup()

        return WorkspaceContext()

    def application_copy(self):
        temporary_directory = TemporaryDirectory()
        root = Path(temporary_directory.name) / "application-package"
        shutil.copytree(FIXTURES / "application-package", root)

        class WorkspaceContext:
            def __enter__(self):
                return root

            def __exit__(self, exc_type, exc_value, traceback):
                temporary_directory.cleanup()

        return WorkspaceContext()


if __name__ == "__main__":
    unittest.main()
