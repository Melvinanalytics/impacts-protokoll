from pathlib import Path
import shutil
from tempfile import TemporaryDirectory

import pytest


ROOT = Path(__file__).resolve().parents[1]

from impacts_protocol import init_workspace, validate
from tests.support import codes, read_context, replace_context, write_application, write_context, write_workstep


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

        assert "structure.invalid" in codes(root)


def test_application_folder_requires_a_slug():
    with TemporaryDirectory() as directory:
        root = write_application(Path(directory) / "Bad Application")

        issue = next(issue for issue in validate(root).issues if issue.code == "structure.invalid")

        assert issue.path == "."
        assert "lowercase ASCII letters and digits" in issue.message
        assert "single hyphens" in issue.message
        assert "bestellung-ausloesen" in issue.message


@pytest.mark.parametrize("slug", ["caf\u00e9", "cafe\u0301"])
def test_application_folder_rejects_non_ascii_slug(tmp_path, slug):
    root = write_application(tmp_path / slug)

    assert any(
        issue.code == "structure.invalid" and "slug" in issue.message.lower()
        for issue in validate(root).issues
    )


def test_application_rejects_an_unknown_runtime_subtree():
    with TemporaryDirectory() as directory:
        root = write_application(Path(directory) / "video")
        runtime = root / "produktion" / "start" / "runtime"
        runtime.mkdir()
        (runtime / "state.json").write_text("{}", encoding="utf-8")

        assert "structure.invalid" in codes(root)


def test_application_requires_each_hierarchy_child():
    with TemporaryDirectory() as directory:
        root = write_application(Path(directory) / "video")
        shutil.rmtree(root / "produktion")

        assert "structure.invalid" in codes(root)


def test_application_root_is_its_hauptprozess():
    with TemporaryDirectory() as directory:
        root = write_application(Path(directory) / "video")
        write_context(root / "CONTEXT.md", {"type": "application"}, "# Video")

        assert "routing.type" in codes(root)


def test_application_rejects_a_file_beside_context():
    with TemporaryDirectory() as directory:
        root = write_application(Path(directory) / "video")
        (root / "notizen.md").write_text("frei", encoding="utf-8")

        assert "structure.invalid" in codes(root)


def test_schema_violation_fails_at_public_interface():
    with TemporaryDirectory() as directory:
        root = write_application(Path(directory) / "video")
        path = root / "CONTEXT.md"
        metadata = read_context(path)
        metadata.pop("leistung")
        replace_context(path, metadata)

        errors = [issue for issue in validate(root).issues if issue.code == "schema.invalid"]
        assert len(errors) == 1
        assert errors[0].path == "CONTEXT.md"
        assert errors[0].message == (
            "'leistung' is a required property; add `leistung` to this frontmatter mapping"
        )


def test_missing_id_reports_nearest_mapping_and_avoids_folder_mismatch(tmp_path):
    root = write_application(tmp_path / "video")
    path = root / "CONTEXT.md"
    metadata = read_context(path)
    metadata.pop("id")
    replace_context(path, metadata)

    issues = validate(root).issues

    assert not any(
        issue.code == "structure.invalid" and "ID must match folder slug" in issue.message
        for issue in issues
    )
    schema = [issue for issue in issues if issue.code == "schema.invalid"]
    assert len(schema) == 1
    assert schema[0].message == (
        "'id' is a required property; add `id` to this frontmatter mapping"
    )


def test_workspace_application_issues_include_each_application_path(tmp_path):
    root = init_workspace(tmp_path / "kunde")
    for slug in ("video-a", "video-b"):
        application = write_application(root / "applications" / slug)
        metadata = read_context(application / "CONTEXT.md")
        metadata["id"] = f"hauptprozess:{slug}"
        metadata.pop("einstieg_ref")
        replace_context(application / "CONTEXT.md", metadata)

    errors = [
        issue
        for issue in validate(root).issues
        if issue.code == "schema.invalid"
        and issue.message == (
            "'einstieg_ref' is a required property; "
            "add `einstieg_ref` to this frontmatter mapping"
        )
    ]

    assert [issue.path for issue in errors] == [
        "applications/video-a/CONTEXT.md",
        "applications/video-b/CONTEXT.md",
    ]
    assert validate(root / "applications" / "video-a").issues[0].path == "CONTEXT.md"


@pytest.mark.parametrize("field", ["pruefung", "routen"])
def test_missing_top_level_workstep_field_omits_root_prefix(tmp_path, field):
    root = write_application(tmp_path / "video")
    path = root / "produktion/start/CONTEXT.md"
    metadata = read_context(path)
    metadata.pop(field)
    replace_context(path, metadata)

    errors = [issue for issue in validate(root).issues if issue.code == "schema.invalid"]

    assert len(errors) == 1
    assert errors[0].path == "produktion/start/CONTEXT.md"
    assert errors[0].message == (
        f"'{field}' is a required property; add `{field}` to this frontmatter mapping"
    )


@pytest.mark.parametrize("invalid", [[42, 17], []])
def test_schema_errors_locate_nested_array_values(tmp_path, invalid):
    root = write_application(tmp_path / "video")
    metadata = read_context(root / "CONTEXT.md")
    metadata["leistung"]["abnahme"] = invalid
    replace_context(root / "CONTEXT.md", metadata)

    errors = [issue for issue in validate(root).issues if issue.code == "schema.invalid"]

    expected = ["/leistung/abnahme/0:", "/leistung/abnahme/1:"] if invalid else ["/leistung/abnahme:"]
    assert len(errors) == len(expected)
    assert all(issue.path == "CONTEXT.md" for issue in errors)
    assert all(issue.message.startswith(pointer) for issue, pointer in zip(errors, expected))


def test_wrong_type_has_one_primary_diagnostic_and_keeps_other_schema_errors(tmp_path):
    root = write_application(tmp_path / "video")
    path = root / "produktion/start/CONTEXT.md"
    metadata = read_context(path)
    metadata["eingaben"] = "input/auftrag.md"
    metadata["ausgaben"] = ["output//ergebnis.md"]
    replace_context(path, metadata)

    errors = [issue for issue in validate(root).issues if issue.code == "schema.invalid"]

    assert len(errors) == 2
    assert any(issue.message.startswith("/eingaben:") and "type" in issue.message for issue in errors)
    assert any(issue.message.startswith("/ausgaben/0:") for issue in errors)


@pytest.mark.parametrize("body", ["", "   \n\t"])
def test_workstep_requires_a_processing_body(body):
    with TemporaryDirectory() as directory:
        root = write_application(Path(directory) / "video")
        path = root / "produktion/start/CONTEXT.md"
        metadata = read_context(path)
        write_context(path, metadata, body)

        assert "routing.missing" in codes(root)


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

        assert "reference.duplicate" in codes(root)


def test_workstep_id_matches_its_folder_slug():
    with TemporaryDirectory() as directory:
        root = write_application(Path(directory) / "video")
        path = root / "produktion/start/CONTEXT.md"
        metadata = read_context(path)
        metadata["id"] = "arbeitsschritt:anderer-name"
        replace_context(path, metadata)

        assert "structure.invalid" in codes(root)


def test_invalid_teilprozess_slug_is_primary_over_dependent_graph_errors():
    with TemporaryDirectory() as directory:
        root = write_application(Path(directory) / "video")
        invalid_part = root / "Bestellung_Auslösen"
        (root / "produktion").rename(invalid_part)

        issues = validate(root).issues

    primary = next(
        issue for issue in issues
        if issue.code == "structure.invalid" and issue.path == invalid_part.name
    )
    assert "lowercase ASCII letters and digits" in primary.message
    assert "single hyphens" in primary.message
    assert "bestellung-ausloesen" in primary.message
    assert not any(issue.code == "reference.unresolved" for issue in issues)
    assert not any("Hauptprozess needs at least one Teilprozess" in issue.message for issue in issues)


def test_incomplete_step_enumeration_keeps_independent_human_gate_error():
    with TemporaryDirectory() as directory:
        root = write_application(Path(directory) / "video")
        write_workstep(
            root / "produktion",
            "Bad_step",
            step_id="arbeitsschritt:bad-step",
        )
        metadata = read_context(root / "CONTEXT.md")
        metadata["einstieg_ref"] = "arbeitsschritt:bad-step"
        replace_context(root / "CONTEXT.md", metadata)
        gate_path = root / "produktion" / "pruefen" / "CONTEXT.md"
        metadata = read_context(gate_path)
        metadata["routen"] = {"yes": "end:done"}
        replace_context(gate_path, metadata)

        issues = validate(root).issues

    assert any(
        issue.code == "process.gate" and issue.path == "produktion/pruefen/CONTEXT.md"
        for issue in issues
    )
    assert any(issue.code == "structure.invalid" and issue.path == "produktion/Bad_step" for issue in issues)
    assert not any(issue.code in {"reference.unresolved", "process.unreachable", "process.no_end"} for issue in issues)


def test_double_leading_bom_has_one_primary_format_error():
    with TemporaryDirectory() as directory:
        root = write_application(Path(directory) / "video")
        path = root / "produktion" / "start" / "CONTEXT.md"
        original = path.read_bytes()

        path.write_bytes(b"\xef\xbb\xbf" + original)
        assert validate(root).valid

        path.write_bytes(b"\xef\xbb\xbf\xef\xbb\xbf" + original)
        report = validate(root)

    assert not report.valid
    assert len(report.issues) == 1
    issue = report.issues[0]
    assert issue.code == "format.invalid"
    assert issue.path == "produktion/start/CONTEXT.md"
    assert "line 1" in issue.message
    assert "remove extra leading BOMs" in issue.message


def test_unresolved_route_is_rejected():
    with TemporaryDirectory() as directory:
        root = write_application(Path(directory) / "video")
        path = root / "produktion/start/CONTEXT.md"
        metadata = read_context(path)
        metadata["routen"] = {"weiter": "arbeitsschritt:fehlt"}
        replace_context(path, metadata)

        issues = validate(root).issues

        assert any(
            issue.code == "reference.unresolved"
            and issue.path == "produktion/start/CONTEXT.md"
            and "Route target does not resolve" in issue.message
            for issue in issues
        )


def test_missing_routes_blocks_only_route_derived_graph_conclusions(tmp_path):
    root = write_application(tmp_path / "video")
    path = root / "produktion/start/CONTEXT.md"
    metadata = read_context(path)
    metadata.pop("routen")
    replace_context(path, metadata)

    issues = validate(root).issues

    assert any(
        issue.code == "schema.invalid" and "`routen`" in issue.message
        for issue in issues
    )
    assert not any(
        issue.code in {"process.unreachable", "process.no_end"}
        for issue in issues
    )


def test_missing_routes_does_not_hide_independent_local_gate_error(tmp_path):
    root = write_application(tmp_path / "video")
    start_path = root / "produktion/start/CONTEXT.md"
    metadata = read_context(start_path)
    metadata.pop("routen")
    replace_context(start_path, metadata)
    gate_path = root / "produktion/pruefen/CONTEXT.md"
    metadata = read_context(gate_path)
    metadata["routen"] = {"ok": "end:fertig"}
    replace_context(gate_path, metadata)

    issues = validate(root).issues

    assert any(issue.code == "schema.invalid" for issue in issues)
    assert any(
        issue.code == "process.gate" and issue.path == "produktion/pruefen/CONTEXT.md"
        for issue in issues
    )
    assert not any(
        issue.code in {"process.unreachable", "process.no_end"}
        for issue in issues
    )


def test_unknown_regular_file_does_not_hide_computable_graph_error():
    with TemporaryDirectory() as directory:
        root = write_application(Path(directory) / "video")
        (root / ".DS_Store").write_bytes(b"metadata")
        path = root / "produktion" / "start" / "CONTEXT.md"
        metadata = read_context(path)
        metadata["routen"] = {"weiter": "arbeitsschritt:fehlt"}
        replace_context(path, metadata)

        issues = validate(root).issues

    assert any(
        issue.code == "structure.invalid"
        and issue.path == ".DS_Store"
        and issue.message == "Unknown Application entry"
        for issue in issues
    )
    assert any(
        issue.code == "reference.unresolved"
        and issue.path == "produktion/start/CONTEXT.md"
        and "Route target does not resolve" in issue.message
        for issue in issues
    )


def test_unresolved_entry_is_rejected_when_tree_is_fully_readable():
    with TemporaryDirectory() as directory:
        root = write_application(Path(directory) / "video")
        path = root / "CONTEXT.md"
        metadata = read_context(path)
        metadata["einstieg_ref"] = "arbeitsschritt:fehlt"
        replace_context(path, metadata)

        issues = validate(root).issues

    assert any(
        issue.code == "reference.unresolved"
        and issue.path == "CONTEXT.md"
        and "Hauptprozess entry does not resolve" in issue.message
        for issue in issues
    )


def test_unreachable_workstep_is_rejected():
    with TemporaryDirectory() as directory:
        root = write_application(Path(directory) / "video")
        write_workstep(root / "produktion", "verwaist")

        assert "process.unreachable" in codes(root)


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

        assert "process.no_end" in codes(root)


def test_human_gate_has_exact_decision_routes():
    with TemporaryDirectory() as directory:
        root = write_application(Path(directory) / "video")
        path = root / "produktion/pruefen/CONTEXT.md"
        metadata = read_context(path)
        metadata["routen"] = {"ok": "end:fertig"}
        replace_context(path, metadata)

        assert "process.gate" in codes(root)


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


def test_unresolved_route_suppresses_only_derived_graph_issues(tmp_path):
    root = write_application(tmp_path / 'video')
    path = root / 'produktion/start/CONTEXT.md'
    metadata = read_context(path)
    metadata['routen'] = {'weiter': 'arbeitsschritt:pruefn'}
    replace_context(path, metadata)

    issues = validate(root).issues

    assert len(issues) == 1
    assert issues[0].code == 'reference.unresolved'
    assert 'arbeitsschritt:pruefn' in issues[0].message


def test_unresolved_route_keeps_independent_gate_and_schema_errors(tmp_path):
    root = write_application(tmp_path / 'video')
    path = root / 'produktion/start/CONTEXT.md'
    metadata = read_context(path)
    metadata['routen'] = {'weiter': 'arbeitsschritt:pruefn'}
    replace_context(path, metadata)
    gate = root / 'produktion/pruefen/CONTEXT.md'
    metadata = read_context(gate)
    metadata['routen'] = {'ok': 'end:done'}
    metadata['pruefung'] = 42
    replace_context(gate, metadata)

    issues = validate(root).issues

    assert sorted(issue.code for issue in issues) == ['process.gate', 'reference.unresolved', 'schema.invalid']
    assert not any(issue.code in {'process.unreachable', 'process.no_end'} for issue in issues)


@pytest.mark.parametrize('preamble', ['\n', 'Text before metadata\n', ''])
def test_typed_context_without_an_opening_delimiter_has_one_format_error(tmp_path, preamble):
    root = write_application(tmp_path / 'video')
    path = root / 'produktion/start/CONTEXT.md'
    original = path.read_text()
    path.write_text(preamble + original if preamble else '')

    issues = validate(root).issues

    assert len(issues) == 1
    assert issues[0].code == 'format.invalid'
    assert issues[0].path == 'produktion/start/CONTEXT.md'
    assert 'line 1' in issues[0].message and 'frontmatter must open with ---' in issues[0].message


@pytest.mark.parametrize('bom', ['', '\ufeff'])
def test_accepted_whitespace_around_frontmatter_delimiters_stays_valid(tmp_path, bom):
    root = write_application(tmp_path / 'video')
    path = root / 'produktion/start/CONTEXT.md'
    original = path.read_text()
    path.write_text(bom + original.replace('---', ' \t--- \t', 2))

    assert validate(root).valid


def test_delimited_empty_metadata_is_not_a_missing_opening_delimiter(tmp_path):
    root = write_application(tmp_path / 'video')
    path = root / 'produktion/start/CONTEXT.md'
    path.write_text('---\n---\n# Body\n')

    issues = validate(root).issues

    assert issues and all(issue.code == 'schema.invalid' for issue in issues)
    assert not any('frontmatter must open' in issue.message for issue in issues)


def test_missing_router_type_keeps_only_the_required_schema_error(tmp_path):
    root = write_application(tmp_path / 'video')
    path = root / 'produktion/CONTEXT.md'
    metadata = read_context(path)
    metadata.pop('type')
    replace_context(path, metadata)

    issues = validate(root).issues

    assert len(issues) == 1 and issues[0].code == 'schema.invalid'
    assert "'type' is a required property" in issues[0].message


def test_tagged_quoted_scalar_diagnostic_does_not_claim_it_was_unquoted(tmp_path):
    root = write_application(tmp_path / 'video')
    path = root / 'produktion/start/CONTEXT.md'
    metadata = read_context(path)
    metadata['pruefung'] = 'tagged-value-marker'
    replace_context(path, metadata)
    path.write_text(path.read_text().replace('tagged-value-marker', '!!int "42"'))

    issues = validate(root).issues

    assert len(issues) == 1 and issues[0].code == 'schema.invalid'
    message = issues[0].message
    assert '/pruefung:' in message and 'YAML read this value as int' in message
    assert 'remove an explicit non-string tag if present' in message
    assert 'unquoted' not in message


def test_unresolved_route_does_not_hide_an_independent_closed_cycle(tmp_path):
    root = write_application(tmp_path / 'video')
    start = root / 'produktion/start/CONTEXT.md'
    metadata = read_context(start)
    metadata['routen'] = {'weiter': 'arbeitsschritt:fehlt'}
    replace_context(start, metadata)
    write_workstep(root / 'produktion', 'cycle-a', routes={'weiter': 'arbeitsschritt:cycle-b'})
    write_workstep(root / 'produktion', 'cycle-b', routes={'weiter': 'arbeitsschritt:cycle-a'})

    issues = validate(root).issues

    assert sorted(issue.code for issue in issues) == ['process.no_end', 'process.no_end', 'reference.unresolved']
    assert {issue.path for issue in issues if issue.code == 'process.no_end'} == {
        'produktion/cycle-a', 'produktion/cycle-b',
    }
    assert not any(issue.code == 'process.unreachable' for issue in issues)


@pytest.mark.parametrize('routes', [None, {}, 'not a mapping', {'weiter': 42}, {'weiter': 'arbeitsschritt:fehlt'}])
def test_reaching_an_uncertain_route_does_not_prove_no_end(tmp_path, routes):
    root = write_application(tmp_path / 'video')
    start = root / 'produktion/start/CONTEXT.md'
    metadata = read_context(start)
    metadata['routen'] = {'weiter': 'arbeitsschritt:uncertain'}
    replace_context(start, metadata)
    uncertain = write_workstep(root / 'produktion', 'uncertain')
    metadata = read_context(uncertain)
    if routes is None:
        metadata.pop('routen')
    else:
        metadata['routen'] = routes
    replace_context(uncertain, metadata)

    issues = validate(root).issues

    assert issues
    assert not any(issue.code in {'process.no_end', 'process.unreachable'} for issue in issues)
