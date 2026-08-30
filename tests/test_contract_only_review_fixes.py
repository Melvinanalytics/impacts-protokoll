from contextlib import contextmanager
import hashlib
import json
from pathlib import Path
import sys
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

import yaml


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from impacts_protocol.generator import generate_workspace
from impacts_protocol.validator import validate_workspace


class ContractOnlyReviewFixTests(unittest.TestCase):
    def test_malformed_activation_id_returns_issue_instead_of_crashing(self):
        with workspace() as root:
            dump(
                root / "00_steuerung/paketaktivierungen.yaml",
                {
                    "customer_id": "kunde",
                    "packages": [
                        {
                            "id": ["not", "a", "string"],
                            "version": "1.0.0",
                            "activation": "active",
                            "evidence_status": "reported",
                        }
                    ],
                },
            )

            report = validate_workspace(root)

        self.assertIn("schema.invalid", codes(report))

    def test_malformed_authority_kind_returns_issue_instead_of_crashing(self):
        with workspace() as root:
            write_authority(root, {"kind": ["file"], "path": "03_records"})

            report = validate_workspace(root)

        self.assertIn("authority.invalid", codes(report))

    def test_malformed_nested_authority_fields_return_issue_without_crash(self):
        configs = (
            {"kind": "file", "path": {"nested": True}},
            {"kind": "external", "authority_id": ["nested"]},
            {
                "kind": "postgres-team",
                "authority_id": {"nested": True},
                "dsn_ref": ["nested"],
            },
        )
        for config in configs:
            with self.subTest(config=config), workspace() as root:
                write_authority(root, config)

                report = validate_workspace(root)

                self.assertIn("authority.invalid", codes(report), report.issues)

    def test_authority_rejects_unknown_kind_and_requires_kind_fields(self):
        cases = (
            ({"kind": "banana", "path": "03_records"}, "authority.invalid"),
            ({"kind": "file"}, "authority.invalid"),
            ({"kind": "sqlite-local"}, "authority.invalid"),
            ({"kind": "postgres-team"}, "authority.invalid"),
            ({"kind": "external"}, "authority.invalid"),
        )
        for config, expected in cases:
            with self.subTest(config=config), workspace() as root:
                write_authority(root, config)
                report = validate_workspace(root)
                self.assertIn(expected, codes(report), report.issues)

    def test_local_authority_path_is_normalized_and_contained(self):
        for unsafe in (
            "/tmp/records",
            "../records",
            "./99_ansichten",
            "02_grundlagen/../99_ansichten",
            "03_records/../99_ansichten",
        ):
            with self.subTest(path=unsafe), workspace() as root:
                write_authority(root, {"kind": "file", "path": unsafe})
                report = validate_workspace(root)
                self.assertTrue(
                    {"authority.invalid", "authority.generated_view_write"}
                    & codes(report),
                    report.issues,
                )

    def test_local_authority_rejects_symlink_path(self):
        with workspace() as root:
            external = root.parent / "outside-records"
            external.mkdir()
            local = root / "03_records/external"
            local.symlink_to(external, target_is_directory=True)
            write_authority(root, {"kind": "file", "path": "03_records/external"})

            report = validate_workspace(root)

        self.assertIn("authority.invalid", codes(report))

    def test_local_authority_rejects_record_subpaths(self):
        with workspace() as root:
            write_authority(root, {"kind": "file", "path": "03_records/customers"})

            report = validate_workspace(root)

        self.assertIn("authority.invalid", codes(report), report.issues)

    def test_authority_path_control_characters_return_issue(self):
        for unsafe in ("03_records/\x00hidden", "03_records/\x01hidden"):
            with self.subTest(path=repr(unsafe)), workspace() as root:
                write_authority(root, {"kind": "file", "path": unsafe})

                report = validate_workspace(root)

                self.assertIn("authority.invalid", codes(report), report.issues)

    def test_remote_authority_uses_no_local_record_folder(self):
        cases = (
            {"kind": "external", "authority_id": "crm:customers"},
            {
                "kind": "postgres-team",
                "authority_id": "postgres:customers",
                "dsn_ref": "secret:customer-db",
            },
        )
        for config in cases:
            with self.subTest(config=config), workspace() as root:
                write_authority(root, config)
                (root / "03_records").rmdir()

                report = validate_workspace(root)

                self.assertTrue(report.valid, report.issues)

    def test_local_record_type_must_use_its_declared_authority(self):
        with workspace() as root:
            dump(
                root / "02_grundlagen/datenautoritaet.yaml",
                {
                    "records": {
                        "customer": {
                            "writes": "crm",
                            "kind": "external",
                            "authority_id": "crm:customers",
                        },
                        "order": {
                            "writes": "customer",
                            "kind": "file",
                            "path": "03_records",
                        },
                    }
                },
            )
            dump(
                root / "03_records/customer-1/record.yaml",
                {"id": "customer-1", "type": "customer"},
            )

            report = validate_workspace(root)

        self.assertIn("authority.record_type", codes(report), report.issues)

    def test_customer_workspace_rejects_embedded_application_documents(self):
        for name in (
            "leistung.yaml",
            "hauptprozess.yaml",
            "teilprozess.yaml",
            "arbeitsschritt.yaml",
        ):
            with self.subTest(name=name), workspace() as root:
                path = root / "01_prozesse/demo" / name
                path.parent.mkdir()
                path.write_text("id: embedded\n", encoding="utf-8")

                report = validate_workspace(root)

                self.assertIn("workspace.embedded_application", codes(report))

    def test_customer_workspace_rejects_legacy_evidence_files(self):
        for name in ("lauf.quittung.yaml", "initialisierung.delta.yaml"):
            with self.subTest(name=name), workspace() as root:
                path = root / "05_aenderungsnachweise" / name
                path.write_text("id: legacy\n", encoding="utf-8")

                report = validate_workspace(root)

                self.assertIn("workspace.legacy_evidence", codes(report))

    def test_yml_embedded_application_and_legacy_evidence_are_rejected(self):
        cases = (
            ("01_prozesse/demo/hauptprozess.yml", "workspace.embedded_application"),
            ("05_aenderungsnachweise/lauf.quittung.yml", "workspace.legacy_evidence"),
            (
                "05_aenderungsnachweise/initialisierung.delta.yml",
                "workspace.legacy_evidence",
            ),
        )
        for relative, expected in cases:
            with self.subTest(relative=relative), workspace() as root:
                path = root / relative
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text("id: legacy\n", encoding="utf-8")

                report = validate_workspace(root)

                self.assertIn(expected, codes(report), report.issues)

    def test_workspace_requires_canonical_root_directories(self):
        with workspace() as root:
            (root / "04_aktive-verbesserung").rmdir()
            (root / "extra").mkdir()

            report = validate_workspace(root)

        self.assertIn("workspace.missing_directory", codes(report))
        self.assertIn("workspace.unexpected_directory", codes(report))

    def test_workspace_rejects_root_directory_symlink(self):
        with workspace() as root:
            directory = root / "04_aktive-verbesserung"
            directory.rmdir()
            target = root.parent / "outside-improvement"
            target.mkdir()
            directory.symlink_to(target, target_is_directory=True)

            report = validate_workspace(root)

        self.assertIn("workspace.symlink_directory", codes(report))

    def test_nested_symlinks_are_rejected_without_reading_targets(self):
        with workspace() as root:
            external_file = root.parent / "outside.yaml"
            external_file.write_text("broken: [", encoding="utf-8")
            (root / "99_ansichten/linked.yaml").symlink_to(external_file)
            external_directory = root.parent / "outside-directory"
            external_directory.mkdir()
            (external_directory / "hidden.yaml").write_text(
                "broken: [", encoding="utf-8"
            )
            (root / "02_grundlagen/linked-directory").symlink_to(
                external_directory, target_is_directory=True
            )

            report = validate_workspace(root)

        self.assertEqual(
            2,
            sum(issue.code == "structure.symlink" for issue in report.issues),
        )
        self.assertNotIn("format.invalid_yaml", codes(report))

    def test_json_is_parsed_strictly(self):
        with workspace() as root:
            (root / "02_grundlagen/source.json").write_text(
                '{"id": "one", "id": "two"}', encoding="utf-8"
            )

            report = validate_workspace(root)

        self.assertIn("format.invalid_json", codes(report))

    def test_record_has_stable_path_id_and_type(self):
        cases = (
            ("2026-08-26-kunde", {"id": "kunde", "type": "customer"}),
            ("kunde-2026-08-26", {"id": "kunde", "type": "customer"}),
            ("kunde-run-001", {"id": "kunde", "type": "customer"}),
            ("kunde", {"type": "customer"}),
            ("kunde", {"id": "andere-id", "type": "customer"}),
            ("kunde", {"id": "kunde"}),
        )
        for record_id, document in cases:
            with self.subTest(record_id=record_id, document=document):
                with workspace() as root:
                    dump(root / "03_records" / record_id / "record.yaml", document)

                    report = validate_workspace(root)

                    self.assertIn("record.invalid", codes(report), report.issues)

    def test_record_markdown_graph_node_requires_type(self):
        with workspace() as root:
            dump(
                root / "03_records/kunde/record.yaml",
                {"id": "kunde", "type": "customer"},
            )
            (root / "03_records/kunde/note.md").write_text(
                "---\ntitle: Notiz\n---\n\nText\n", encoding="utf-8"
            )

            report = validate_workspace(root)

        self.assertIn("graph.missing_type", codes(report))

    def test_vorgang_requires_contract_directories(self):
        with workspace() as root:
            run = root / "06_vorgaenge/demo"
            run.mkdir()
            dump(
                run / "vorgang.yaml",
                {
                    "id": "vorgang:demo",
                    "hauptprozess_ref": "hauptprozess:demo",
                    "status": "angelegt",
                    "run_id": "run:demo",
                    "receipt_refs": [],
                },
            )

            report = validate_workspace(root)

        self.assertIn("vorgang.incomplete_structure", codes(report))

    def test_process_binding_allows_only_provenance_and_delta(self):
        with workspace() as root:
            application = root / "01_prozesse/demo"
            application.mkdir()
            dump(
                application / "provenance.yaml",
                {"id": "application:demo", "version": "1.0.0"},
            )
            dump(application / "delta.yaml", {"changes": []})
            (application / "notes.md").write_text("Not allowed", encoding="utf-8")

            report = validate_workspace(root)

        self.assertIn("process_binding.unexpected_entry", codes(report))

    def test_process_binding_requires_manual_minimum(self):
        cases = (
            ({"id": "application:demo"}, {"changes": []}),
            ({"id": "application:demo", "version": "1.0.0"}, {}),
            (
                {"id": "application:demo", "version": "1.0.0"},
                {"changes": "not-a-list"},
            ),
        )
        for provenance, delta in cases:
            with self.subTest(provenance=provenance, delta=delta), workspace() as root:
                application = root / "01_prozesse/demo"
                application.mkdir()
                dump(application / "provenance.yaml", provenance)
                dump(application / "delta.yaml", delta)

                report = validate_workspace(root)

                self.assertIn("process_binding.invalid", codes(report), report.issues)

    def test_process_binding_must_match_folder_and_active_package(self):
        cases = (
            ("application:different", "1.0.0", []),
            (
                "application:demo",
                "1.0.0",
                [
                    {
                        "id": "application:demo",
                        "version": "2.0.0",
                        "activation": "active",
                        "evidence_status": "reported",
                    }
                ],
            ),
        )
        for package_id, version, packages in cases:
            with self.subTest(package_id=package_id, version=version), workspace() as root:
                activate(root, packages)
                application = root / "01_prozesse/demo"
                application.mkdir()
                dump(
                    application / "provenance.yaml",
                    {"id": package_id, "version": version},
                )
                dump(application / "delta.yaml", {"changes": []})

                report = validate_workspace(root)

            self.assertIn("process_binding.unresolved_package", codes(report), report.issues)

    def test_process_delta_allows_only_scalar_path_changes(self):
        with workspace() as root:
            activate(
                root,
                [
                    {
                        "id": "application:demo",
                        "version": "1.0.0",
                        "activation": "active",
                        "evidence_status": "reported",
                    }
                ],
            )
            application = root / "01_prozesse/demo"
            application.mkdir()
            dump(
                application / "provenance.yaml",
                {"id": "application:demo", "version": "1.0.0"},
            )
            dump(
                application / "delta.yaml",
                {
                    "changes": [
                        {
                            "path": "/nodes",
                            "value": {"hauptprozess": {"nodes": []}},
                        }
                    ]
                },
            )

            report = validate_workspace(root)

        self.assertIn("process_binding.invalid", codes(report), report.issues)

    def test_wiedervorlage_nested_receipt_refs_return_issue_without_crash(self):
        with workspace() as root:
            run = make_complete_run(root)
            dump(
                run / "wiedervorlage.yaml",
                {
                    "id": "wiedervorlage:demo",
                    "vorgang_ref": "vorgang:demo",
                    "run_id": "run:demo",
                    "owner": "rolle:bearbeitung",
                    "trigger": "antwort",
                    "continuation": "arbeitsschritt:pruefen",
                    "status": "wartend",
                    "receipt_refs": [["nested"]],
                },
            )

            report = validate_workspace(root)

        self.assertTrue(
            {"schema.invalid", "reference.wiedervorlage"} <= codes(report),
            report.issues,
        )

    def test_wiedervorlage_malformed_field_matrix_never_crashes(self):
        fields = {
            "wiedervorlage": (
                "id",
                "continuation",
                "vorgang_ref",
                "run_id",
                "receipt_refs",
            ),
            "vorgang": (
                "id",
                "hauptprozess_ref",
                "run_id",
                "receipt_refs",
            ),
        }
        malformed_values = (["nested"], {"nested": True})
        for target, target_fields in fields.items():
            for field in target_fields:
                for value in malformed_values:
                    with self.subTest(target=target, field=field, value=value):
                        with workspace() as root:
                            run = make_complete_run(root)
                            document = valid_wiedervorlage()
                            if target == "wiedervorlage":
                                document[field] = value
                            else:
                                vorgang = yaml.safe_load(
                                    (run / "vorgang.yaml").read_text(encoding="utf-8")
                                )
                                vorgang[field] = value
                                dump(run / "vorgang.yaml", vorgang)
                            dump(run / "wiedervorlage.yaml", document)

                            report = validate_workspace(root)

                            if field != "receipt_refs" or isinstance(value, dict):
                                self.assertIn(
                                    "schema.invalid", codes(report), report.issues
                                )
                            reference_fields = {
                                "wiedervorlage": {
                                    "continuation",
                                    "vorgang_ref",
                                    "run_id",
                                    "receipt_refs",
                                },
                                "vorgang": {"id", "run_id", "receipt_refs"},
                            }
                            if field in reference_fields[target]:
                                self.assertIn(
                                    "reference.wiedervorlage",
                                    codes(report),
                                    report.issues,
                                )

    def test_wiedervorlage_handles_malformed_contained_receipts(self):
        with workspace() as root:
            run = make_complete_run(root)
            vorgang = yaml.safe_load(
                (run / "vorgang.yaml").read_text(encoding="utf-8")
            )
            vorgang["receipt_refs"] = [["nested"]]
            dump(run / "vorgang.yaml", vorgang)
            dump(run / "wiedervorlage.yaml", valid_wiedervorlage())

            report = validate_workspace(root)

        self.assertIn("schema.invalid", codes(report), report.issues)
        self.assertIn("reference.wiedervorlage", codes(report), report.issues)

    def test_wiedervorlage_resolves_against_its_vorgang_without_embedded_application(self):
        with workspace() as root:
            run = make_complete_run(root)
            dump(run / "wiedervorlage.yaml", valid_wiedervorlage())

            report = validate_workspace(root)

        self.assertTrue(report.valid, report.issues)

    def test_non_document_views_use_adjacent_provenance_sidecars(self):
        with workspace() as root:
            source = root / "02_grundlagen/source.yaml"
            dump(source, {"id": "source"})
            for name in ("graph.dot", "preview.png"):
                artifact = root / "99_ansichten" / name
                artifact.write_bytes(b"derived")
                dump(
                    artifact.with_name(f"{artifact.name}.provenance.yaml"),
                    {
                        "generated": True,
                        "generated_from": ["02_grundlagen/source.yaml"],
                    },
                )

            report = validate_workspace(root)

        self.assertTrue(report.valid, report.issues)

    def test_non_document_view_without_sidecar_is_rejected(self):
        with workspace() as root:
            (root / "99_ansichten/preview.png").write_bytes(b"derived")

            report = validate_workspace(root)

        self.assertIn("view.missing_provenance", codes(report), report.issues)

    def test_view_cannot_claim_write_authority(self):
        with workspace() as root:
            source = root / "02_grundlagen/source.yaml"
            dump(source, {"id": "source"})
            dump(
                root / "99_ansichten/status.yaml",
                {
                    "generated": True,
                    "generated_from": ["02_grundlagen/source.yaml"],
                    "writes": "customer",
                    "write_authority": True,
                },
            )

            report = validate_workspace(root)

        self.assertIn("view.write_authority", codes(report))

    def test_snapshot_record_ref_must_resolve(self):
        cases = (
            "missing",
            "sor:missing/customer-1",
            "sor:broken",
            ["nested"],
            {"nested": True},
        )
        for record_ref in cases:
            with self.subTest(record_ref=record_ref), workspace() as root:
                run = make_complete_run(root)
                dump(run / "snapshot/customer.yaml", {"record_ref": record_ref})

                report = validate_workspace(root)

                self.assertIn(
                    "snapshot.invalid_record_ref", codes(report), report.issues
                )

    def test_snapshot_artifact_without_record_ref_needs_no_record_binding(self):
        with workspace() as root:
            run = make_complete_run(root)
            dump(run / "snapshot/measurement.yaml", {"measurement": 42})

            report = validate_workspace(root)

        self.assertTrue(report.valid, report.issues)

    def test_snapshot_json_read_failure_returns_issue_without_crash(self):
        with workspace() as root:
            run = make_complete_run(root)
            dump_json(run / "snapshot/customer.json", {"record_ref": "kunde"})

            with patch(
                "impacts_protocol.validator._load_json",
                side_effect=[
                    {"record_ref": "kunde"},
                    OSError("synthetic read failure"),
                ],
            ):
                report = validate_workspace(root)

        self.assertIn("format.invalid_json", codes(report), report.issues)

    def test_snapshot_record_ref_positive_local_and_remote_cases(self):
        with workspace() as root:
            dump(
                root / "03_records/kunde/record.yaml",
                {"id": "kunde", "type": "customer"},
            )
            run = make_complete_run(root)
            dump(run / "snapshot/local.yaml", {"record_ref": "kunde"})

            local_report = validate_workspace(root)

        self.assertTrue(local_report.valid, local_report.issues)

        remote_cases = (
            (
                {"kind": "external", "authority_id": "crm:customers"},
                "sor:crm:customers/customer-1",
            ),
            (
                {
                    "kind": "postgres-team",
                    "authority_id": "postgres:customers",
                    "dsn_ref": "secret:customers",
                },
                "sor:postgres:customers/customer-1",
            ),
        )
        for authority, reference in remote_cases:
            with self.subTest(authority=authority), workspace() as root:
                write_authority(root, authority)
                (root / "03_records").rmdir()
                run = make_complete_run(root)
                dump_json(
                    run / "snapshot/remote.json",
                    {"record_ref": reference},
                )

                remote_report = validate_workspace(root)

            self.assertTrue(remote_report.valid, remote_report.issues)

    def test_complete_landed_state_validates(self):
        with workspace() as root:
            activate(
                root,
                [
                    {
                        "id": "application:demo",
                        "version": "1.0.0",
                        "activation": "active",
                        "evidence_status": "reported",
                    }
                ],
            )
            application = root / "01_prozesse/demo"
            application.mkdir()
            dump(
                application / "provenance.yaml",
                {"id": "application:demo", "version": "1.0.0"},
            )
            dump(application / "delta.yaml", {"changes": []})
            dump(
                root / "03_records/kunde/record.yaml",
                {"id": "kunde", "type": "customer"},
            )
            run = make_complete_run(root)
            dump(run / "snapshot/customer.yaml", {"record_ref": "kunde"})

            report = validate_workspace(root)

        self.assertTrue(report.valid, report.issues)

    def test_vorgang_id_must_match_its_folder(self):
        with workspace() as root:
            run = make_complete_run(root)
            vorgang = yaml.safe_load(
                (run / "vorgang.yaml").read_text(encoding="utf-8")
            )
            vorgang["id"] = "vorgang:different"
            dump(run / "vorgang.yaml", vorgang)

            report = validate_workspace(root)

        self.assertIn("vorgang.path_identity", codes(report), report.issues)

    def test_receipt_refs_must_resolve_inside_vorgang(self):
        with workspace() as root:
            run = make_complete_run(root)
            (run / "receipts/receipt-demo.yaml").unlink()

            report = validate_workspace(root)

        self.assertIn("receipt.unresolved", codes(report), report.issues)

    def test_receipt_ids_must_be_unique_inside_vorgang(self):
        with workspace() as root:
            run = make_complete_run(root)
            dump_json(run / "receipts/duplicate.json", {"id": "receipt:demo"})

            report = validate_workspace(root)

        self.assertIn("receipt.duplicate_id", codes(report), report.issues)
        self.assertIn("receipt.unresolved", codes(report), report.issues)

    def test_validate_is_read_only(self):
        with workspace() as root:
            before = tree_digest(root)

            validate_workspace(root)

            self.assertEqual(before, tree_digest(root))


def codes(report):
    return {issue.code for issue in report.issues}


def dump(path: Path, document) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        yaml.safe_dump(document, allow_unicode=True, sort_keys=False),
        encoding="utf-8",
    )


def dump_json(path: Path, document) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(document), encoding="utf-8")


def write_authority(root: Path, config: dict) -> None:
    config = {"writes": "customer", **config}
    dump(root / "02_grundlagen/datenautoritaet.yaml", {"records": {"default": config}})


def activate(root: Path, packages: list[dict]) -> None:
    dump(
        root / "00_steuerung/paketaktivierungen.yaml",
        {"customer_id": "kunde", "packages": packages},
    )


def make_complete_run(root: Path) -> Path:
    run = root / "06_vorgaenge/demo"
    for name in ("snapshot", "receipts", "freigaben"):
        (run / name).mkdir(parents=True, exist_ok=True)
    dump(
        run / "vorgang.yaml",
        {
            "id": "vorgang:demo",
            "hauptprozess_ref": "hauptprozess:demo",
            "status": "angelegt",
            "run_id": "run:demo",
            "receipt_refs": ["receipt:demo"],
        },
    )
    dump(run / "receipts/receipt-demo.yaml", {"id": "receipt:demo"})
    return run


def valid_wiedervorlage() -> dict:
    return {
        "id": "wiedervorlage:demo",
        "vorgang_ref": "vorgang:demo",
        "run_id": "run:demo",
        "owner": "rolle:bearbeitung",
        "trigger": "antwort",
        "continuation": "arbeitsschritt:pruefen",
        "status": "wartend",
        "receipt_refs": ["receipt:demo"],
    }


def tree_digest(root: Path) -> str:
    digest = hashlib.sha256()
    for path in sorted(root.rglob("*")):
        digest.update(path.relative_to(root).as_posix().encode())
        digest.update(b"d" if path.is_dir() else b"f")
        if path.is_file():
            digest.update(path.read_bytes())
    return digest.hexdigest()


@contextmanager
def workspace():
    with TemporaryDirectory() as directory:
        yield generate_workspace(Path(directory) / "workspace", "kunde")


if __name__ == "__main__":
    unittest.main()
