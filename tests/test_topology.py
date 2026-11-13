"""Synthetic mutations of the declared workspace form and its shape."""
import json
from pathlib import Path

import pytest

from impacts_protocol import init_workspace, validate
from impacts_protocol.cli import main
from .support import write_context, write_hauptprozess


def workspace(tmp_path, declaration="Form: records/ Record Library per subject"):
    root = init_workspace(tmp_path / "workspace")
    (root / "records").mkdir()
    for name in ("grundlagen", "legacy", "tools", "library"):
        if f"Form: {name}/" in declaration:
            (root / name).mkdir()
    router = root / "CONTEXT.md"
    router.write_text(router.read_text() + "\n" + declaration + "\n")
    return root


def router(folder, body):
    folder.mkdir(parents=True, exist_ok=True)
    (folder / "CONTEXT.md").write_text(body + "\n")


def assert_code(root, code):
    assert [issue.code for issue in validate(root).issues] == [code]


def test_clean_composed_workspace(tmp_path):
    root = workspace(tmp_path)
    router(root / "records", "Form: people/ Record Library per person\nForm: orders/ Record Library per order")
    for kind in ("people", "orders"):
        for instance in ("one", "two"):
            (root / "records" / kind / instance).mkdir(parents=True)
    router(root / "grundlagen", "[rule](rule.md)\n[topic](topic/)")
    (root / "grundlagen/rule.md").touch()
    router(root / "grundlagen/topic", "Form: Knowledge Bundle per subtopic")
    router(root / "analyse", "# Captures")
    (root / "tools").mkdir()
    with (root / "CONTEXT.md").open("a") as handle:
        handle.write("Form: grundlagen/ Knowledge Bundle per topic\nForm: analyse/ Context Map per capture\nForm: tools/ Tool\n")
    assert validate(root).valid


def test_missing_root_row_ignores_dot_and_cache_folders(tmp_path):
    root = workspace(tmp_path, "")
    (root / ".git-like").mkdir()
    (root / "__pycache__").mkdir()
    (root / "records/data.csv").touch()
    assert_code(root, "topology.form_missing")


@pytest.mark.parametrize("declaration", [
    "Form: records/ Unknown per subject",
    "Form: records/ Record Library",
    "Form: records/nested/ Record Library per subject",
    "Form: legacy/ none: ; decided by human:fixture",
    "Form: legacy/ none: synthetic hold",
    "Form: legacy/ none: synthetic hold; decided by human::bad",
], ids=["unknown_token", "missing_unit", "two_segment_path", "held_without_reason", "held_without_decided_by", "held_invalid_human_id"])
def test_invalid_declaration(tmp_path, declaration):
    root = workspace(tmp_path, "Form: records/ Record Library per subject\n" + declaration if "legacy/" in declaration else declaration)
    (root / "legacy").mkdir(exist_ok=True)
    (root / "legacy/old.md").touch()
    messages = [issue.message for issue in validate(root).issues if issue.code == "topology.form_invalid"]
    assert messages
    if "legacy/" in declaration:
        assert messages == [f"Form line for legacy/ is not valid: {declaration.split('legacy/ ', 1)[1]!r}; write a form with its unit, `Capability`, `Tool` or `Check` alone, or a held row with reason and decided by human:<id>"]


def test_code_token_in_non_root_router(tmp_path):
    root = workspace(tmp_path)
    router(root / "records", "Form: child/ Tool")
    (root / "records/child").mkdir()
    issue, = validate(root).issues
    assert issue.code == "topology.form_invalid"
    assert issue.message == "top-level lines live only in the root CONTEXT.md; move this line there or use the parent's form"


def test_duplicate_parent_declaration(tmp_path):
    root = workspace(tmp_path, "Form: records/ Record Library per subject\nForm: records/ Context Map per capture")
    assert_code(root, "topology.form_invalid")


def test_duplicate_own_and_parent_declaration(tmp_path):
    root = workspace(tmp_path)
    router(root / "records", "Form: Record Library per subject")
    assert_code(root, "topology.form_invalid")


def test_declared_missing_folder(tmp_path):
    root = workspace(tmp_path)
    (root / "records").rmdir()
    assert_code(root, "topology.form_invalid")


def test_declared_file_instead_of_folder(tmp_path):
    root = workspace(tmp_path)
    (root / "records").rmdir()
    (root / "records").touch()
    assert_code(root, "topology.form_invalid")


def test_held_row_keeps_valid_and_prints_count(tmp_path, capsys):
    root = workspace(tmp_path, "Form: legacy/ none: synthetic hold; decided by human:fixture")
    report = validate(root)
    assert report.valid
    assert report.held == ({"path": "legacy/", "reason": "synthetic hold", "decided_by": "human:fixture"},)
    assert main(["validate", str(root)]) == 0
    assert "1 folders held without form\nheld: legacy/ (synthetic hold; decided by human:fixture)\n" in capsys.readouterr().out
    assert main(["validate", str(root), "--json"]) == 0
    assert json.loads(capsys.readouterr().out)["held"] == list(report.held)


def test_removed_held_row_requires_form(tmp_path):
    root = workspace(tmp_path, "")
    (root / "records/data.csv").touch()
    assert_code(root, "topology.form_missing")


def test_file_beside_instance_folders(tmp_path):
    root = workspace(tmp_path)
    router(root / "records/one", "# Instance")
    (root / "records/table.csv").touch()
    assert_code(root, "topology.shape")


def test_file_beside_declared_sublevels(tmp_path):
    root = workspace(tmp_path)
    router(root / "records", "Form: people/ Record Library per person")
    router(root / "records/people", "# Kind")
    (root / "records/table.csv").touch()
    [issue] = validate(root).issues
    assert issue.code == "topology.shape"
    assert "a level holds kinds or instances, not both: move it into its kind, or move the kinds to their own Record Library" in issue.message


def test_undeclared_folder_beside_declared_sublevel(tmp_path):
    root = workspace(tmp_path)
    router(root / "records", "Form: people/ Record Library per person")
    router(root / "records/people", "# Kind")
    router(root / "records/other", "# Instance")
    assert_code(root, "topology.shape")


def test_single_table_file(tmp_path):
    root = workspace(tmp_path)
    (root / "records/table.csv").touch()
    assert validate(root).valid


def test_file_instances_keep_one_shape(tmp_path):
    root = workspace(tmp_path)
    (root / "records/one.md").touch()
    (root / "records/two.md").touch()
    assert validate(root).valid
    router(root / "records/three", "# Instance")
    findings = [issue.path for issue in validate(root).issues if issue.code == "topology.shape"]
    assert findings == ["records/three"]


def test_knowledge_bundle_unlinked_file(tmp_path):
    root = workspace(tmp_path, "Form: grundlagen/ Knowledge Bundle per topic")
    router(root / "grundlagen", "# Synthetic foundations")
    (root / "grundlagen/rule.md").touch()
    assert_code(root, "topology.shape")


def test_knowledge_bundle_missing_router(tmp_path):
    root = workspace(tmp_path, "Form: grundlagen/ Knowledge Bundle per topic")
    (root / "grundlagen/rule.md").touch()
    assert_code(root, "topology.shape")


def test_anchor_and_topic_context_links(tmp_path):
    root = workspace(tmp_path, "Form: grundlagen/ Knowledge Bundle per topic")
    router(root / "grundlagen", "[rule](./rule.md#anchor)\n[topic](topic/CONTEXT.md#anchor)")
    (root / "grundlagen/rule.md").touch()
    router(root / "grundlagen/topic", "Form: Knowledge Bundle per subtopic")
    assert validate(root).valid


def test_held_folder_contents_never_listed(tmp_path, monkeypatch):
    root = workspace(tmp_path, "Form: legacy/ none: synthetic hold; decided by human:fixture")
    router(root / "legacy/broken", "---\nmalformed: [\nForm: nonsense")
    original = Path.iterdir
    def guarded(path):
        assert not path.is_relative_to(root / "legacy"), "Held contents were listed"
        return original(path)
    monkeypatch.setattr(Path, "iterdir", guarded)
    assert validate(root).valid


@pytest.mark.parametrize("token", ["Tool", "Capability", "Check"])
def test_code_folder_is_not_checked_for_topology(tmp_path, token):
    root = workspace(tmp_path, "Form: tools/ " + token)
    router(root / "tools/broken", "Form: nonsense")
    (root / "tools/loose.md").touch()
    assert not [issue for issue in validate(root).issues if issue.code.startswith("topology.")]


def test_hauptprozess_has_no_topology_or_held_text(tmp_path, capsys):
    root = write_hauptprozess(tmp_path / "video")
    assert validate(root).valid
    assert not validate(root).held
    assert main(["validate", str(root)]) == 0
    output = capsys.readouterr().out
    assert "topology." not in output and "held" not in output


@pytest.mark.parametrize("language", ["en", "de"])
def test_initialized_workspace_passes_unchanged(tmp_path, language):
    root = init_workspace(tmp_path / language, language=language)
    assert validate(root).valid


def test_fenced_and_indented_form_lines_are_ignored(tmp_path):
    root = workspace(tmp_path, "```text\nForm: missing/ Unknown\n```\n   Form: missing/ Unknown\nForm: records/ Record Library per subject")
    assert validate(root).valid


def test_own_sublevel_declaration(tmp_path):
    root = workspace(tmp_path)
    router(root / "records/people", "Form: Record Library per person")
    (root / "records/people/one").mkdir()
    assert validate(root).valid


def test_pin_mismatch_skips_topology(tmp_path):
    root = workspace(tmp_path, "Form: records/ Unknown")
    write_context(root / "CONTEXT.md", {"type": "workspace", "protocol": "v7.0.0"})
    assert validate(root).valid
    assert not validate(root).held


def test_file_based_process_home_holds_only_process_folders(tmp_path):
    root = workspace(tmp_path, "Form: records/ Record Library per subject\nForm: prozesse/ Pipeline per recurring job")
    router(root / "prozesse/anlage", "# Process")
    assert validate(root).valid
    (root / "prozesse/notiz.md").touch()
    assert_code(root, "topology.shape")


def test_process_folder_without_router_breaks_pipeline_shape(tmp_path):
    root = workspace(tmp_path, "Form: records/ Record Library per subject\nForm: prozesse/ Pipeline per recurring job")
    (root / "prozesse/anlage").mkdir(parents=True)
    (root / "prozesse/anlage/work.md").touch()
    assert_code(root, "topology.shape")


def test_pipeline_token_is_top_level_only(tmp_path):
    root = workspace(tmp_path, "Form: grundlagen/ Knowledge Bundle per topic")
    router(root / "grundlagen", "Form: jobs/ Pipeline per job\n[jobs](jobs/)")
    (root / "grundlagen/jobs").mkdir()
    assert "topology.form_invalid" in [issue.code for issue in validate(root).issues]


@pytest.mark.parametrize(("form", "finding"), [("Knowledge Bundle per topic", True), ("Context Map per capture", False)])
def test_definition_outside_hauptprozesse_is_a_finding_unless_candidate(tmp_path, form, finding):
    root = workspace(tmp_path, f"Form: records/ Record Library per subject\nForm: {'grundlagen' if finding else 'analyse'}/ {form}")
    write_hauptprozess(root / ("grundlagen" if finding else "analyse") / "video")
    router_file = root / ("grundlagen" if finding else "analyse") / "CONTEXT.md"
    router_file.write_text("[video](video/)\n")
    report = validate(root)
    assert ("topology.shape" in [issue.code for issue in report.issues]) is finding
    assert any(item.reason == "definition tree outside hauptprozesse/, not bindable" for item in report.not_judged)


def bundle_beside_cases(tmp_path, entry_router="Form: Knowledge Bundle per topic"):
    root = workspace(tmp_path, "Form: records/ Record Library per case\nForm: grundlagen/ Knowledge Bundle per topic")
    router(root / "records/fall-alpha", "# Case")
    router(root / "grundlagen", "[rule](rule.md)\n[alpha](fall-alpha/)")
    (root / "grundlagen/rule.md").touch()
    router(root / "grundlagen/fall-alpha", entry_router)
    return root


def test_undeclared_folder_in_bundle_is_a_finding(tmp_path):
    root = bundle_beside_cases(tmp_path, "# Case material")
    (root / "records/fall-alpha").rename(root / "records/another-case")
    messages = [issue.message for issue in validate(root).issues if issue.code == "topology.shape"]
    assert any("fall-alpha/ is not a declared sub-level" in message for message in messages)


def test_case_folder_declared_linked_and_routed_is_still_a_finding(tmp_path):
    root = bundle_beside_cases(tmp_path)
    issues = validate(root).issues
    assert [issue.code for issue in issues] == ["topology.shape"]
    assert "records/fall-alpha" in issues[0].message


def test_dated_file_in_bundle_is_a_finding(tmp_path):
    root = workspace(tmp_path, "Form: records/ Record Library per subject\nForm: grundlagen/ Knowledge Bundle per topic")
    router(root / "grundlagen", "[run](2026-09-13-run.md)")
    (root / "grundlagen/2026-09-13-run.md").touch()
    messages = [issue.message for issue in validate(root).issues if issue.code == "topology.shape"]
    assert any("2026-09-13-run.md is dated work" in message for message in messages)


def test_dated_capture_in_context_map_is_valid(tmp_path):
    root = workspace(tmp_path, "Form: records/ Record Library per subject\nForm: analyse/ Context Map per capture")
    router(root / "analyse", "# Captures")
    (root / "analyse/2026-09-13-capture.md").touch()
    router(root / "analyse", "[capture](2026-09-13-capture.md)")
    assert validate(root).valid


def test_unresolved_router_link_is_a_finding(tmp_path):
    root = workspace(tmp_path, "Form: records/ Record Library per subject\nForm: grundlagen/ Knowledge Bundle per topic")
    router(root / "grundlagen", "[rule](rule.md)\n[gone](gone.md)\n[web](https://example.invalid/x)")
    (root / "grundlagen/rule.md").touch()
    messages = [issue.message for issue in validate(root).issues if issue.code == "topology.shape"]
    assert messages == ["Link 'gone.md' does not resolve; correct or remove it"]


def test_each_offending_entry_is_named_once(tmp_path):
    root = workspace(tmp_path, "Form: records/ Record Library per subject\nForm: grundlagen/ Knowledge Bundle per topic")
    router(root / "grundlagen", "[rule](rule.md)")
    for name in ("rule.md", "a.md", "b.md"):
        (root / "grundlagen" / name).touch()
    paths = [issue.path for issue in validate(root).issues]
    assert paths == ["grundlagen/a.md", "grundlagen/b.md"]
    assert all("CONTEXT.md; link it" in issue.message for issue in validate(root).issues)


def test_capture_folder_named_like_a_record_is_valid(tmp_path):
    root = workspace(tmp_path, "Form: records/ Record Library per case\nForm: analyse/ Context Map per captured case")
    router(root / "records/fall-alpha", "# Case")
    router(root / "analyse/fall-alpha", "# Capture")
    router(root / "analyse", "[capture](fall-alpha/)")
    assert validate(root).valid


def test_rule_file_beside_kind_prefixed_record_is_valid(tmp_path):
    root = workspace(tmp_path, "Form: records/ Record Library per offer\nForm: grundlagen/ Knowledge Bundle per topic")
    (root / "records/angebot-1002").mkdir()
    router(root / "grundlagen", "[offer rules](angebot.md)")
    (root / "grundlagen/angebot.md").touch()
    assert validate(root).valid


def test_bundle_file_with_the_record_name_is_a_finding(tmp_path):
    root = workspace(tmp_path, "Form: records/ Record Library per case\nForm: grundlagen/ Knowledge Bundle per topic")
    router(root / "records/fall-alpha", "# Case")
    router(root / "grundlagen", "[alpha](fall-alpha.md)")
    (root / "grundlagen/fall-alpha.md").touch()
    assert_code(root, "topology.shape")


def test_single_table_file_names_no_unit(tmp_path):
    root = workspace(tmp_path, "Form: records/ Record Library per customer\nForm: grundlagen/ Knowledge Bundle per topic")
    (root / "records/kunden.md").touch()
    router(root / "grundlagen", "[discount](kunden.md)")
    (root / "grundlagen/kunden.md").touch()
    assert validate(root).valid


@pytest.mark.parametrize("link", ["<rule%20one.md>", "rule%20one.md", "<rule one.md>"])
def test_encoded_and_bracketed_links_resolve(tmp_path, link):
    root = workspace(tmp_path, "Form: records/ Record Library per subject\nForm: grundlagen/ Knowledge Bundle per topic")
    router(root / "grundlagen", f"[rule]({link})")
    (root / "grundlagen/rule one.md").touch()
    assert validate(root).valid


@pytest.mark.parametrize(("link", "text"), [("/etc/hosts", "is absolute"),
                                             ("../../outside/CONTEXT.md", "leaves the workspace")])
def test_absolute_and_escaping_links_are_findings(tmp_path, link, text):
    root = workspace(tmp_path, "Form: records/ Record Library per subject\nForm: grundlagen/ Knowledge Bundle per topic")
    router(root / "grundlagen", f"[rule](rule.md) [x]({link})")
    (root / "grundlagen/rule.md").touch()
    messages = [issue.message for issue in validate(root).issues]
    assert len(messages) == 1 and text in messages[0]


def test_root_router_links_are_checked_inside_only(tmp_path):
    root = workspace(tmp_path)
    with (root / "CONTEXT.md").open("a") as handle:
        handle.write("\n[sibling](../sibling/02_protocol/SKILL.md)\n")
    assert validate(root).valid
    with (root / "CONTEXT.md").open("a") as handle:
        handle.write("\n[gone](records/gone.md)\n")
    messages = [issue.message for issue in validate(root).issues]
    assert len(messages) == 1 and "does not resolve" in messages[0]


@pytest.mark.parametrize("name", ["Fall-Alpha", "fall-alpha.md", "FALL-ALPHA.txt"])
def test_unit_names_ignore_case_and_extension(tmp_path, name):
    root = workspace(tmp_path, "Form: records/ Record Library per case\nForm: grundlagen/ Knowledge Bundle per topic")
    (root / "records/fall-alpha.json").touch()
    (root / "records/fall-beta.json").touch()
    entry = root / "grundlagen" / name
    router(root / "grundlagen", f"[x]({name}/)" if "." not in name else f"[x]({name})")
    if "." in name:
        entry.touch()
    else:
        router(entry, "Form: Knowledge Bundle per topic")
    assert [issue.code for issue in validate(root).issues] == ["topology.shape"]


@pytest.mark.parametrize(("parent", "child"), [("Knowledge Bundle per topic", "Record Library per case"),
                                               ("Record Library per kind", "Knowledge Bundle per topic")])
def test_sub_level_keeps_its_parent_form(tmp_path, parent, child):
    root = workspace(tmp_path, f"Form: library/ {parent}")
    router(root / "library", "[sub](sub/)")
    router(root / "library/sub", f"Form: {child}")
    assert "topology.form_invalid" in [issue.code for issue in validate(root).issues]
    router(root / "library/sub", f"Form: {parent}")
    assert validate(root).valid


def test_definition_parked_in_code_folder_is_a_finding(tmp_path):
    root = workspace(tmp_path, "Form: records/ Record Library per subject\nForm: tools/ Tool")
    write_hauptprozess(root / "tools" / "video")
    (root / "tools/broken.md").write_text("---\nmalformed: [\n")
    paths = [issue.path for issue in validate(root).issues]
    assert paths == ["tools/video/CONTEXT.md"]


def test_definition_in_held_folder_is_not_read(tmp_path):
    root = workspace(tmp_path, "Form: records/ Record Library per subject\nForm: alt/ none: synthetic hold; decided by human:fixture")
    write_hauptprozess(root / "alt" / "video")
    report = validate(root)
    assert report.valid and not report.not_judged


@pytest.mark.parametrize(("form", "finding"), [("Record Library per kind", True), ("Context Map per capture", False)])
def test_definition_in_a_deeper_level_is_found(tmp_path, form, finding):
    root = workspace(tmp_path, f"Form: {'records' if finding else 'analyse'}/ {form}")
    router(root / ("records" if finding else "analyse"), "Form: kind/ Record Library per item" if form.startswith("Record") else "[kind](kind/)")
    write_hauptprozess(root / ("records" if finding else "analyse") / "kind" / "video")
    codes = [issue.code for issue in validate(root).issues]
    assert ("topology.shape" in codes) is finding


def test_two_segment_path_fails_even_when_the_folder_exists(tmp_path):
    root = workspace(tmp_path, "Form: records/ Record Library per kind\nForm: records/kind/ Record Library per item")
    router(root / "records", "[kind](kind/)")
    (root / "records/kind").mkdir()
    messages = [issue.message for issue in validate(root).issues if issue.code == "topology.form_invalid"]
    assert messages == ["Form path 'records/kind/' is not one folder; write one relative folder name with a trailing slash"]


def test_equal_names_only_no_hyphen_prefix(tmp_path):
    root = workspace(tmp_path, "Form: records/ Record Library per offer\nForm: grundlagen/ Knowledge Bundle per topic")
    router(root / "records/angebot-2026-001", "# Offer")
    router(root / "grundlagen", "[offer](angebot/)")
    router(root / "grundlagen/angebot", "Form: Knowledge Bundle per topic")
    assert validate(root).issues == ()


@pytest.mark.parametrize("name", ["ＦＡＬＬ", "fa\u200b\u200c\u200dll\ufeff"])
def test_unit_equality_normalises_nfkc_and_zero_width(tmp_path, name):
    root = workspace(tmp_path, "Form: records/ Record Library per case\nForm: grundlagen/ Knowledge Bundle per topic")
    router(root / "records/fall", "# Case")
    router(root / "grundlagen", f"[case]({name}.md)")
    (root / "grundlagen" / (name + ".md")).touch()
    issue, = validate(root).issues
    assert issue.code == "topology.shape"
    assert "has the name of record records/fall; if it holds that record's material, move it there; otherwise rename it" in issue.message


def test_record_kind_names_are_not_units(tmp_path):
    root = bundle_beside_cases(tmp_path)
    router(root / "records", "Form: fall-alpha/ Record Library per item")
    assert validate(root).issues == ()


def test_record_match_prefers_folder_and_counts_other_matches(tmp_path):
    root = workspace(tmp_path, "Form: records/ Record Library per kind\nForm: grundlagen/ Knowledge Bundle per topic")
    router(root / "records", "Form: a/ Record Library per case\nForm: b/ Record Library per case")
    router(root / "records/a/fall", "# Case")
    (root / "records/b").mkdir()
    for name in ("fall.md", "other.md"):
        (root / "records/b" / name).touch()
    router(root / "grundlagen", "[fall](fall.md)")
    (root / "grundlagen/fall.md").touch()
    issue, = validate(root).issues
    assert issue.code == "topology.shape"
    assert "record records/a/fall and 1 more;" in issue.message


@pytest.mark.parametrize("name", ["README.md", "readme.txt", "context.txt"])
def test_router_and_readme_stems_never_register_units(tmp_path, name):
    root = workspace(tmp_path, "Form: records/ Record Library per case\nForm: grundlagen/ Knowledge Bundle per topic")
    for filename in (name, "other.md"):
        (root / "records" / filename).touch()
    router(root / "grundlagen", f"[rule]({Path(name).stem}.md)")
    (root / "grundlagen" / (Path(name).stem + ".md")).touch()
    assert validate(root).issues == ()


@pytest.mark.parametrize(("name", "dated"), [("2024-02-29-work.md", True), ("2023-02-29-work.md", False), ("1000-10-99.md", False), ("2026-13-01.md", False)])
def test_dated_requires_real_calendar_date(tmp_path, name, dated):
    root = workspace(tmp_path, "Form: records/ Record Library per case\nForm: grundlagen/ Knowledge Bundle per topic")
    router(root / "grundlagen", f"[x]({name})")
    (root / "grundlagen" / name).touch()
    issues = validate(root).issues
    if dated:
        issue, = issues
        assert issue.code == "topology.shape"
        assert "is dated work;" in issue.message
        assert "a rule's validity date goes inside the file or after its name" in issue.message
    else:
        assert issues == ()


@pytest.mark.parametrize(("record", "name", "message"), [(True, "2026-01-01", "has the name of record"), (False, "2026-01-01", "is dated work"), (False, "topic", "is not a declared sub-level")])
def test_bundle_entry_emits_only_most_specific_finding(tmp_path, record, name, message):
    root = workspace(tmp_path, "Form: records/ Record Library per case\nForm: grundlagen/ Knowledge Bundle per topic")
    if record:
        router(root / "records" / name, "# Case")
    router(root / "grundlagen", "# Rules")
    router(root / "grundlagen" / name, "# Material")
    issue, = validate(root).issues
    assert issue.code == "topology.shape"
    assert message in issue.message


@pytest.mark.parametrize(("name", "form", "expected"), [("records", "Tool", "Record Library"), ("grundlagen", "Record Library per case", "Knowledge Bundle"), ("analyse", "Pipeline per job", "Context Map"), ("capabilities", "Check", "Capability")])
def test_fixed_homes_require_fixed_forms(tmp_path, name, form, expected):
    root = workspace(tmp_path, f"Form: {name}/ {form}")
    (root / name).mkdir(exist_ok=True)
    issue, = validate(root).issues
    assert issue.code == "topology.form_invalid"
    assert f"{name}/ must be {expected}; use its fixed form" == issue.message


def test_context_map_only_lives_in_analyse(tmp_path):
    root = workspace(tmp_path, "Form: other/ Context Map per capture")
    (root / "other").mkdir()
    issue, = validate(root).issues
    assert issue.code == "topology.form_invalid"
    assert "Context Map lives only in analyse/" in issue.message


def test_context_map_router_links_every_entry(tmp_path):
    root = workspace(tmp_path, "Form: analyse/ Context Map per capture")
    router(root / "analyse", "# Captures")
    (root / "analyse/capture.md").touch()
    issue, = validate(root).issues
    assert issue.code == "topology.shape"
    assert "capture.md is not linked from analyse/CONTEXT.md;" in issue.message


def test_context_map_missing_router_is_one_level_finding(tmp_path):
    root = workspace(tmp_path, "Form: analyse/ Context Map per capture")
    (root / "analyse").mkdir()
    for name in ("a.md", "b.md"):
        (root / "analyse" / name).touch()
    issue, = validate(root).issues
    assert (issue.code, issue.path, issue.message) == ("topology.shape", "analyse", "analyse/ has no CONTEXT.md; add one that links every entry")


@pytest.mark.parametrize(("name", "form"), [("analyse", "Context Map per capture"), ("jobs", "Pipeline per job")])
def test_context_map_and_pipeline_cannot_have_sublevels(tmp_path, name, form):
    root = workspace(tmp_path, f"Form: {name}/ {form}")
    router(root / name, "Form: child/ Record Library per case\n[child](child/)")
    router(root / name / "child", "# Child")
    issue, = validate(root).issues
    assert issue.code == "topology.form_invalid"
    assert issue.message == f"{name}/child/ cannot be a sub-level of a {form.split(' per ')[0]}; remove the line or move the folder out"


@pytest.mark.parametrize("form", ["Record Library per case", "Knowledge Bundle per topic", "Context Map per capture"])
@pytest.mark.parametrize("router_shape", ["directory", "dangling_symlink"])
def test_context_directory_is_not_regular_router(tmp_path, form, router_shape):
    name = {"Record Library": "records", "Knowledge Bundle": "grundlagen", "Context Map": "analyse"}[form.split(" per ")[0]]
    root = workspace(tmp_path, f"Form: {name}/ {form}")
    (root / name).mkdir(exist_ok=True)
    if router_shape == "directory":
        (root / name / "CONTEXT.md").mkdir()
    else:
        (root / name / "CONTEXT.md").symlink_to("missing")
    issue, = validate(root).issues
    assert issue.code == "topology.shape"
    assert issue.message == f"{name}/CONTEXT.md is not a regular file; replace it with the level's router"


def test_dot_files_and_dot_folders_skipped_on_clean_tree(tmp_path):
    root = workspace(tmp_path, "Form: grundlagen/ Knowledge Bundle per topic")
    router(root / "grundlagen", "# Rules")
    for folder in (root, root / "grundlagen"):
        (folder / ".DS_Store").touch()
        router(folder / ".hidden", "---\ntype: hauptprozess\n---")
    assert validate(root).issues == ()


def test_empty_top_level_and_entry_folders_skipped(tmp_path):
    root = workspace(tmp_path, "Form: grundlagen/ Knowledge Bundle per topic")
    router(root / "grundlagen", "# Rules")
    for folder in (root / "empty/deep", root / "grundlagen/empty/deep"):
        folder.mkdir(parents=True)
        (folder / ".gitkeep").touch()
    assert validate(root).issues == ()


def test_comments_fences_and_inline_code_hide_forms_and_links(tmp_path):
    root = workspace(tmp_path)
    with (root / "CONTEXT.md").open("a") as handle:
        handle.write('\n<!--\nForm: missing/ Tool\n[x](missing.md)\n-->\n`Form: missing/ Tool`\n`[x](missing.md)`\n```text\n[x](missing.md)\nForm: missing/ Tool\n```\n')
    assert validate(root).issues == ()


def test_form_paths_support_spaces(tmp_path):
    root = workspace(tmp_path, "Form: 01 Grundlagen/ Knowledge Bundle per topic")
    router(root / "01 Grundlagen", "[rule](rule.md)")
    (root / "01 Grundlagen/rule.md").touch()
    assert validate(root).issues == ()


@pytest.mark.parametrize("declared", ["KUNDEN", "Ｋｕｎｄｅｎ", "kun\u200bden"])
def test_form_path_normalisation_reports_both_spellings_once(tmp_path, declared):
    root = workspace(tmp_path, f"Form: {declared}/ Record Library per customer")
    router(root / "kunden", "# Customers")
    issue, = validate(root).issues
    assert issue.code == "topology.form_invalid"
    assert repr(declared + "/") in issue.message and "on-disk 'kunden/'" in issue.message
    assert "use the on-disk spelling" in issue.message


def test_prose_form_line_in_record_router_is_ignored(tmp_path):
    root = workspace(tmp_path)
    router(root / "records/customer", "Form: schriftlich (§ 126 BGB)")
    assert validate(root).issues == ()


@pytest.mark.parametrize("link", ['[x](rule.md "title")', '[x](<rule.md> "title")', '[x](../grundlagen/rule.md)', '[x](HTTPS://example.invalid)\n[x](rule.md)'])
def test_title_reference_same_level_and_uppercase_scheme_links(tmp_path, link):
    root = workspace(tmp_path, "Form: grundlagen/ Knowledge Bundle per topic")
    router(root / "grundlagen", link)
    (root / "grundlagen/rule.md").touch()
    assert validate(root).issues == ()


def test_root_absolute_link_is_not_judged(tmp_path):
    root = workspace(tmp_path)
    with (root / "CONTEXT.md").open("a") as handle:
        handle.write("\n[x](/missing/absolute.md)\n")
    assert validate(root).issues == ()


@pytest.mark.parametrize("target", ["bad%00file.md", "x" * 300, "%FF"])
def test_bad_links_are_unresolved_without_aborting(tmp_path, target):
    root = workspace(tmp_path, "Form: grundlagen/ Knowledge Bundle per topic")
    router(root / "grundlagen", f"[x]({target})\n[rule](rule.md)")
    (root / "grundlagen/rule.md").touch()
    issue, = validate(root).issues
    assert issue.code == "topology.shape"
    assert "does not resolve; correct or remove it" in issue.message


def test_link_pattern_is_linear_on_40000_openers():
    from time import perf_counter
    from impacts_protocol.topology import _links
    start = perf_counter()
    assert _links("](" * 40000) == []
    assert perf_counter() - start < 1


@pytest.mark.parametrize("depth", [2, 3])
def test_analyse_definition_exemption_at_any_depth(tmp_path, depth):
    root = workspace(tmp_path, "Form: analyse/ Context Map per capture")
    router(root / "analyse", "[capture](capture/)")
    definition = root / "analyse/capture"
    for _ in range(depth - 2):
        definition /= "nested"
    write_hauptprozess(definition)
    assert validate(root).issues == ()


@pytest.mark.parametrize("home", ["records/instance", "tools/implementation", "jobs/process"])
def test_definitions_found_at_depth_three_even_in_code_and_pipeline(tmp_path, home):
    top = home.split('/')[0]
    form = {"records": "Record Library per case", "tools": "Tool", "jobs": "Pipeline per job"}[top]
    root = workspace(tmp_path, f"Form: {top}/ {form}")
    router(root / home, "# Instance")
    write_hauptprozess(root / home / "hidden")
    issue, = validate(root).issues
    assert (issue.code, issue.path) == ("topology.shape", home + "/hidden/CONTEXT.md")
    assert issue.message == "Hauptprozess definition outside hauptprozesse/; report it to the owner, whose confirming commit moves it into hauptprozesse/; a candidate goes under analyse/"


def test_older_pin_first_text_line_says_not_judged(tmp_path, capsys):
    root = workspace(tmp_path)
    write_context(root / "CONTEXT.md", {"type": "workspace", "protocol": "v0.3.0"})
    assert main(["validate", str(root)]) == 0
    assert "workspace not judged" in capsys.readouterr().out.splitlines()[0]


@pytest.mark.parametrize("operation", ["iterdir", "is_file", "is_dir"])
def test_unreadable_entry_does_not_hide_sibling_findings(tmp_path, monkeypatch, operation):
    root = workspace(tmp_path, "Form: grundlagen/ Knowledge Bundle per topic")
    router(root / "grundlagen", "Form: blocked/ Knowledge Bundle per topic\n[blocked](blocked/)")
    router(root / "grundlagen/blocked", "# Blocked")
    (root / "grundlagen/loose.md").touch()
    original = getattr(Path, operation)
    blocked = root / "grundlagen/blocked"
    def guarded(path, *args, **kwargs):
        if path == blocked:
            raise PermissionError("synthetic denied")
        return original(path, *args, **kwargs)
    monkeypatch.setattr(Path, operation, guarded)
    issues = validate(root).issues
    assert any(issue.code == "topology.shape" and issue.path == "grundlagen/blocked" and "cannot be read: synthetic denied; restore read access" in issue.message for issue in issues)
    assert any(issue.code == "topology.shape" and issue.path == "grundlagen/loose.md" and "is not linked from" in issue.message for issue in issues)
    assert not any(issue.code == "structure.level" for issue in issues)


def test_unreadable_definition_child_does_not_abort_scan(tmp_path, monkeypatch):
    root = workspace(tmp_path, "Form: tools/ Tool")
    router(root / "tools/blocked", "# Blocked")
    write_hauptprozess(root / "tools/good/deep")
    original = Path.iterdir
    def guarded(path):
        if path == root / "tools/blocked":
            raise PermissionError("synthetic denied")
        return original(path)
    monkeypatch.setattr(Path, "iterdir", guarded)
    issues = validate(root).issues
    assert any(issue.code == "topology.shape" and issue.path == "tools/blocked" and "restore read access" in issue.message for issue in issues)
    assert any(issue.code == "topology.shape" and issue.path == "tools/good/deep/CONTEXT.md" and "report it to the owner" in issue.message for issue in issues)


def test_missing_form_message_names_all_next_homes(tmp_path):
    root = workspace(tmp_path, "")
    (root / "records/case.md").touch()
    issue, = validate(root).issues
    assert issue.code == "topology.form_missing"
    assert issue.message == "records/ has no Form line; add `Form: records/ <form> per <unit>` as a plain unindented line in the root CONTEXT.md; if it has no form, move its content to the case, record or Vorgang it serves or leave it to Git history; only a person may hold it"


def test_declared_symlink_names_regular_directory_repair(tmp_path):
    root = workspace(tmp_path, "Form: alias/ Record Library per case")
    (root / "alias").symlink_to("records", target_is_directory=True)
    issue, = validate(root).issues
    assert issue.code == "topology.form_invalid"
    assert issue.message == "alias/ is missing or a symlink; create a regular directory or correct its Form path"


def test_mixed_instance_message_splits_record_kinds(tmp_path):
    root = workspace(tmp_path)
    router(root / "records/one", "# Instance")
    for name in ("a.md", "b.md"):
        (root / "records" / name).touch()
    issue, = validate(root).issues
    assert issue.code == "topology.shape"
    assert issue.message == "one is a folder among the instance files of records/; split folders and files into separate record kinds, each with one shape"


def test_way_one_table_in_kind_router_beside_earned_folders(tmp_path):
    root = workspace(tmp_path)
    router(root / "records", "| Subject | Stage |\n|---|---|\n| small-1 | open |\n| [big](big/) | open |")
    router(root / "records/big", "# Big subject")
    assert validate(root).valid
    (root / "records/table.md").write_text("| Subject | Stage |\n")
    issue, = validate(root).issues
    assert issue.message == "table.md is a file among the instance folders of records/; if it is the kind's table, move it into records/CONTEXT.md; otherwise move it to the instance or record kind it belongs to"


def test_normalised_form_alias_does_not_add_duplicate_or_missing(tmp_path):
    root = workspace(tmp_path, "Form: kunden/ Record Library per customer\nForm: KUNDEN/ Record Library per customer")
    router(root / "kunden", "# Customers")
    issue, = validate(root).issues
    assert issue.code == "topology.form_invalid"
    assert issue.message == "Form path 'KUNDEN/' differs from on-disk 'kunden/'; use the on-disk spelling"


def test_definition_scan_reads_type_only_from_frontmatter(tmp_path):
    root = workspace(tmp_path, "Form: tools/ Tool")
    router(root / "tools/implementation/ordinary", "# Example\ntype: hauptprozess\n```yaml\ntype: hauptprozess\n```")
    assert validate(root).issues == ()



def test_multiline_inline_code_hides_forms_and_links(tmp_path):
    root = workspace(tmp_path)
    with (root / "CONTEXT.md").open("a") as handle:
        handle.write("\n``example\nForm: missing/ Tool\n[x](missing.md)\n``\n")
    assert validate(root).issues == ()



def test_readme_named_record_folder_still_registers_a_unit(tmp_path):
    root = workspace(tmp_path, "Form: records/ Record Library per case\nForm: grundlagen/ Knowledge Bundle per topic")
    router(root / "records/readme", "# Case")
    router(root / "grundlagen", "[Rule](readme.md)")
    (root / "grundlagen/readme.md").touch()
    issue, = validate(root).issues
    assert issue.code == "topology.shape"
    assert "has the name of record records/readme;" in issue.message


def test_loose_file_in_process_home_names_the_move(tmp_path):
    root = workspace(tmp_path, "Form: records/ Record Library per subject\nForm: prozesse/ Pipeline per job")
    router(root / "prozesse/anlage", "# Process")
    (root / "prozesse/notiz.md").touch()
    issue, = validate(root).issues
    assert issue.message == "notiz.md is loose in process home prozesse/; move it into its process folder or out of the process home"


def test_context_map_entry_with_a_record_name_is_valid(tmp_path):
    # akten/ sorts before analyse/, so the record unit is known when analyse/ is checked.
    root = workspace(tmp_path, "Form: records/ Record Library per subject\nForm: akten/ Record Library per case\nForm: analyse/ Context Map per capture")
    (root / "akten/fall-alpha").mkdir(parents=True)
    (root / "akten/fall-alpha/akte.md").touch()
    router(root / "analyse", "[alpha](fall-alpha.md)")
    (root / "analyse/fall-alpha.md").touch()
    assert validate(root).valid


NFC, NFD = "vertr\u00e4ge", "vertra\u0308ge"


@pytest.mark.parametrize(("home", "form"), [("grundlagen", "Knowledge Bundle per topic"), ("analyse", "Context Map per capture")])
def test_decomposed_file_linked_composed_is_linked(tmp_path, home, form):
    root = workspace(tmp_path, f"Form: records/ Record Library per subject\nForm: {home}/ {form}")
    router(root / home, f"[contracts]({NFC}.md)")
    (root / home / f"{NFD}.md").touch()
    assert validate(root).valid


def test_decomposed_folder_with_composed_form_path_is_entered(tmp_path):
    root = workspace(tmp_path, "Form: records/ Record Library per subject\nForm: grundlagen/ Knowledge Bundle per topic")
    router(root / "grundlagen", f"Form: {NFC}/ Knowledge Bundle per contract\n[contracts]({NFC}/)")
    router(root / "grundlagen" / NFD, "[rule](rule.md)")
    (root / "grundlagen" / NFD / "rule.md").touch()
    (root / "grundlagen" / NFD / "loose.md").touch()
    paths = [issue.path for issue in validate(root).issues]
    assert len(paths) == 1 and paths[0].endswith("loose.md")


def test_case_difference_in_form_path_is_still_reported(tmp_path):
    root = workspace(tmp_path, "Form: records/ Record Library per subject\nForm: grundlagen/ Knowledge Bundle per topic")
    router(root / "grundlagen", "Form: Vertraege/ Knowledge Bundle per contract\n[c](vertraege/)")
    router(root / "grundlagen/vertraege", "# contracts")
    messages = [issue.message for issue in validate(root).issues]
    assert any("differs from on-disk 'vertraege/'" in m for m in messages)


@pytest.mark.parametrize("target", ["nowhere.md", "geist.md"], ids=["dangling", "self_loop"])
def test_linked_broken_symlink_is_a_finding(tmp_path, target):
    root = workspace(tmp_path, "Form: records/ Record Library per subject\nForm: grundlagen/ Knowledge Bundle per topic")
    router(root / "grundlagen", "[ghost](geist.md)")
    (root / "grundlagen/geist.md").symlink_to(target)
    assert validate(root).issues


def test_locate_matches_composed_against_decomposed_listing(tmp_path, monkeypatch):
    from impacts_protocol import topology
    folder = tmp_path / "level"
    folder.mkdir()
    stored = folder / NFD
    stored.touch()
    real_exists = Path.exists
    monkeypatch.setattr(Path, "exists", lambda self: False if self.name == NFC else real_exists(self))
    assert topology._locate(folder, NFC) == stored


@pytest.mark.parametrize("definition", ['[r]: rule.md', '[^r]: rule.md', '[r]: missing.md "title"'])
def test_x1_reference_definitions_do_not_link_entries(tmp_path, definition):
    root = workspace(tmp_path, "Form: grundlagen/ Knowledge Bundle per topic")
    router(root / "grundlagen", '[x][r]\n' + definition)
    (root / "grundlagen/rule.md").touch()
    issue, = validate(root).issues
    assert (issue.code, issue.message) == ("topology.shape", "rule.md is not linked from grundlagen/CONTEXT.md; link it")


def test_x2_record_kind_is_not_a_unit_but_instances_are(tmp_path):
    root = workspace(tmp_path, "Form: records/ Record Library per kind\nForm: grundlagen/ Knowledge Bundle per topic")
    router(root / "records", "Form: articles/ Record Library per article")
    router(root / "records/articles", "# Articles")
    for name in ("A-1002.md", "A-1003.md"):
        (root / "records/articles" / name).touch()
    router(root / "grundlagen", "[kind](articles.md)\n[instance](A-1002.md)")
    for name in ("articles.md", "A-1002.md"):
        (root / "grundlagen" / name).touch()
    issue, = validate(root).issues
    assert issue.code == "topology.shape"
    assert issue.message == "grundlagen/A-1002.md has the name of record records/articles/A-1002.md; if it holds that record's material, move it there; otherwise rename it"


@pytest.mark.parametrize("name", ["analyse\u200b", "ａｎａｌｙｓｅ", "Analyse"])
def test_x3_context_map_requires_exact_analyse_name(tmp_path, name):
    root = workspace(tmp_path, f"Form: {name}/ Context Map per capture")
    router(root / name, "# Captures")
    issue, = validate(root).issues
    assert (issue.code, issue.message) == ("topology.form_invalid", f"{name}/ is a Context Map outside analyse/; Context Map lives only in analyse/; move it there or use the parent's form")


@pytest.mark.parametrize("name", ["records\u200b", "grundlagen\u200b", "capabilities\u200b"])
def test_x3_fixed_homes_use_exact_disk_names(tmp_path, name):
    root = workspace(tmp_path, f"Form: {name}/ Tool")
    router(root / name, "# Code")
    assert validate(root).issues == ()


def test_x4_gitignored_entries_skipped_at_root_and_all_depths(tmp_path):
    import subprocess
    root = workspace(tmp_path, "Form: grundlagen/ Knowledge Bundle per topic\nForm: tools/ Tool")
    subprocess.run(["git", "init", "-q", str(root)], check=True)
    (root / ".gitignore").write_text("dist/\nbuild/\n*.tmp\n")
    router(root / "grundlagen", "Form: nested/ Knowledge Bundle per topic\n[nested](nested/)")
    router(root / "grundlagen/nested", "# Rules")
    for home in ("dist", "tools/build", "grundlagen/build", "grundlagen/nested/build"):
        router(root / home, "---\ntype: hauptprozess\n---")
    (root / "grundlagen/nested/scratch.tmp").touch()
    assert validate(root).issues == ()
    tracked = root / "grundlagen/tracked.tmp"
    tracked.touch()
    subprocess.run(["git", "-C", str(root), "add", "-f", "grundlagen/tracked.tmp"], check=True)
    issue, = validate(root).issues
    assert (issue.code, issue.message) == ("topology.shape", "tracked.tmp is not linked from grundlagen/CONTEXT.md; link it")


def test_x4_git_failure_skips_nothing(tmp_path, monkeypatch):
    import subprocess
    from impacts_protocol.topology import check_topology
    root = workspace(tmp_path, "")
    (root / "records/item.md").touch()
    calls = []
    def unavailable(command, **kwargs):
        calls.append(command)
        raise subprocess.CalledProcessError(1, command)
    monkeypatch.setattr(subprocess, "run", unavailable)
    issues, _, _ = check_topology(root, r"human:[^:\s][^\s]*")
    assert len(calls) == 1
    assert calls[0] == ["git", "-C", str(root), "ls-files", "--others", "--ignored", "--exclude-standard", "--directory", "-z"]
    issue, = issues
    assert issue.code == "topology.form_missing" and issue.message.startswith("records/ has no Form line;")


@pytest.mark.parametrize("value", ["Checkliste, vom Kunden unterschrieben", "Tooling notes", "Knowledge Bundle draft", "child/ Checkliste, unterschrieben", "Pipeline draft"])
def test_x5_whole_form_value_required_below_root(tmp_path, value):
    root = workspace(tmp_path, "Form: grundlagen/ Knowledge Bundle per topic")
    router(root / "grundlagen", "Form: " + value)
    assert validate(root).issues == ()


@pytest.mark.parametrize("value", ["Check", "Capability", "Tool", "Pipeline per job", "none: pending", "child/ Check", "child/ Pipeline per job", "child/ none: pending"])
def test_x5_root_only_tokens_below_root_still_reported(tmp_path, value):
    root = workspace(tmp_path, "Form: grundlagen/ Knowledge Bundle per topic")
    router(root / "grundlagen", "Form: " + value)
    issue, = validate(root).issues
    assert (issue.code, issue.message) == ("topology.form_invalid", "top-level lines live only in the root CONTEXT.md; move this line there or use the parent's form")


@pytest.mark.parametrize(("home", "form"), [("analyse", "Context Map per capture"), ("jobs", "Pipeline per job")])
def test_x6_entry_routers_are_not_self_declarations(tmp_path, home, form):
    root = workspace(tmp_path, f"Form: {home}/ {form}")
    router(root / home, "[entry](entry/)")
    router(root / home / "entry", "Form: Knowledge Bundle per topic\nForm: Checkliste/ Knowledge Bundle per item\n[x](missing.md)")
    assert validate(root).issues == ()


@pytest.mark.parametrize("link", ["[x](Entwurf(final).md)", r"[x](Entwurf\(final\).md)", "[x](Entwurf%28final%29.md)", "[x](Entwurf(final).md (title))", "[x](<Entwurf(final).md> (title))"])
def test_x7_parentheses_in_destinations_and_titles(tmp_path, link):
    root = workspace(tmp_path, "Form: grundlagen/ Knowledge Bundle per topic")
    router(root / "grundlagen", link)
    (root / "grundlagen/Entwurf(final).md").touch()
    assert validate(root).issues == ()


@pytest.mark.parametrize("value", ["knowledge bundle per topic", "Knowledge  Bundle per topic", "Knowledge Bundle pro topic", "Knowledge\tBundle per topic"])
def test_x8_readable_path_invalid_form_names_folder(tmp_path, value):
    root = workspace(tmp_path, f"Form: grundlagen/ {value}")
    (root / "grundlagen/rule.md").touch()
    issue, = validate(root).issues
    assert (issue.code, issue.message) == ("topology.form_invalid", f"Form line for grundlagen/ is not valid: {value!r}; write a form with its unit, `Capability`, `Tool` or `Check` alone, or a held row with reason and decided by human:<id>")


def test_x9_rejected_sublevel_has_no_second_finding(tmp_path):
    root = workspace(tmp_path, "Form: grundlagen/ Knowledge Bundle per topic")
    router(root / "grundlagen", "Form: child/ Record Library per case")
    router(root / "grundlagen/child", "# Child")
    issue, = validate(root).issues
    assert (issue.code, issue.message) == ("topology.form_invalid", "grundlagen/child/ is a Record Library under the Knowledge Bundle grundlagen/; declare it as a Knowledge Bundle or move it")


def test_x10_missing_form_names_exact_plain_line(tmp_path):
    root = workspace(tmp_path, "")
    router(root / "plans", "# Plans")
    issue, = validate(root).issues
    assert (issue.code, issue.message) == ("topology.form_missing", "plans/ has no Form line; add `Form: plans/ <form> per <unit>` as a plain unindented line in the root CONTEXT.md; if it has no form, move its content to the case, record or Vorgang it serves or leave it to Git history; only a person may hold it")


@pytest.mark.parametrize("target", ["RULE.md", "ｒｕｌｅ.md", "ru\u2060le.md"])
def test_x11_alias_link_names_disk_spelling(tmp_path, target):
    root = workspace(tmp_path, "Form: grundlagen/ Knowledge Bundle per topic")
    router(root / "grundlagen", f"[rule]({target})")
    (root / "grundlagen/rule.md").touch()
    issue, = validate(root).issues
    assert (issue.code, issue.message) == ("topology.shape", f"rule.md is linked as {target!r}; use the on-disk spelling")


def test_x11_folder_alias_includes_entry_guidance(tmp_path):
    root = workspace(tmp_path, "Form: grundlagen/ Knowledge Bundle per topic")
    router(root / "grundlagen", "Form: topic/ Knowledge Bundle per topic\n[topic](TOPIC/CONTEXT.md)")
    router(root / "grundlagen/topic", "# Topic")
    issue, = validate(root).issues
    assert (issue.code, issue.message) == ("topology.shape", "topic is linked as 'TOPIC/CONTEXT.md'; use the on-disk spelling; link the entry itself, not a file inside it")


def test_x12_invalid_line_names_exact_code_choices(tmp_path):
    root = workspace(tmp_path, "Form: tools/ Tool.")
    (root / "tools/code.py").touch()
    issue, = validate(root).issues
    assert (issue.code, issue.message) == ("topology.form_invalid", "Form line for tools/ is not valid: 'Tool.'; write a form with its unit, `Capability`, `Tool` or `Check` alone, or a held row with reason and decided by human:<id>")


@pytest.mark.parametrize("name", ["bad\tname.md", "bad\nname.md", "bad\rname.md", "bad\x85name.md"])
def test_x13_control_characters_cannot_split_findings(tmp_path, name):
    from impacts_protocol.topology import check_topology
    root = workspace(tmp_path, "Form: grundlagen/ Knowledge Bundle per topic")
    router(root / "grundlagen", "# Rules")
    (root / "grundlagen" / name).touch()
    issues, _, _ = check_topology(root, r"human:[^:\s][^\s]*")
    issue, = issues
    escaped = repr(name)[1:-1]
    assert (issue.code, issue.path, issue.message) == ("topology.shape", f"grundlagen/{escaped}", f"{escaped} is not linked from grundlagen/CONTEXT.md; link it")


@pytest.mark.parametrize("name", ["\u20602026-11-16-plan.md", "2026\u201111\u201116-plan.md"])
def test_x14_format_and_dash_characters_do_not_hide_dates(tmp_path, name):
    root = workspace(tmp_path, "Form: grundlagen/ Knowledge Bundle per topic")
    router(root / "grundlagen", f"[plan]({name})")
    (root / "grundlagen" / name).touch()
    issue, = validate(root).issues
    assert (issue.code, issue.message) == ("topology.shape", f"{name} is dated work; move it to its case, its Vorgang or Git history; a rule's validity date goes inside the file or after its name")


def test_x14_soft_hyphen_does_not_hide_record_name(tmp_path):
    root = bundle_beside_cases(tmp_path)
    (root / "grundlagen/fall-alpha/CONTEXT.md").unlink()
    (root / "grundlagen/fall-alpha").rmdir()
    name = "fall-al\u00adpha.md"
    (root / "grundlagen" / name).touch()
    router(root / "grundlagen", f"[case]({name})\n[rule](rule.md)")
    issue, = validate(root).issues
    assert (issue.code, issue.message) == ("topology.shape", f"grundlagen/{name} has the name of record records/fall-alpha; if it holds that record's material, move it there; otherwise rename it")


@pytest.mark.parametrize("record_file", [False, True])
def test_x15_first_dot_ends_file_unit_name(tmp_path, record_file):
    root = workspace(tmp_path, "Form: records/ Record Library per case\nForm: grundlagen/ Knowledge Bundle per topic")
    record = "A-1002.tar.gz" if record_file else "A-1002"
    if record_file:
        for name in (record, "other.md"):
            (root / "records" / name).touch()
    else:
        router(root / "records" / record, "# Case")
    router(root / "grundlagen", "[case](A-1002.tar.gz)")
    (root / "grundlagen/A-1002.tar.gz").touch()
    issue, = validate(root).issues
    assert (issue.code, issue.message) == ("topology.shape", f"grundlagen/A-1002.tar.gz has the name of record records/{record}; if it holds that record's material, move it there; otherwise rename it")


@pytest.mark.parametrize("separator", ["\x85", "\u2028", "\u2029", "\v", "\f"])
def test_x16a_body_lines_split_on_cr_and_lf_only(separator):
    # Core's frontmatter reader may still split on these; that is a stated limit (fd, 10414f1 gate).
    from impacts_protocol.topology import body_lines
    assert not any("rule.md" in line for line in body_lines(f"```\nexample{separator}```\n[x](rule.md)\n```"))


@pytest.mark.parametrize("damage", ["id: one\nid: two", "name: [unclosed", "x: " + "[" * 3000])
@pytest.mark.parametrize("type_value", ["hauptprozess", "'hauptprozess'", '"hauptprozess"'])
def test_x16b_broken_frontmatter_still_exposes_definition(tmp_path, damage, type_value):
    from impacts_protocol.topology import check_topology
    root = workspace(tmp_path, "Form: tools/ Tool")
    router(root / "tools/notes", f"---\ntype: {type_value}\n{damage}\n---")
    issues, _, _ = check_topology(root, r"human:[^:\s][^\s]*")
    issue, = issues
    assert (issue.code, issue.path, issue.message) == ("topology.shape", "tools/notes/CONTEXT.md", "Hauptprozess definition outside hauptprozesse/; report it to the owner, whose confirming commit moves it into hauptprozesse/; a candidate goes under analyse/")


def test_x16c_unresolved_links_cache_directory_listing(tmp_path, monkeypatch):
    from impacts_protocol.topology import Topology, _locate
    folder = tmp_path / "level"
    folder.mkdir()
    (folder / "rule.md").touch()
    state = Topology(tmp_path, r"human:.*")
    original, listings = Path.iterdir, []
    def counted(path):
        listings.append(path)
        return original(path)
    monkeypatch.setattr(Path, "iterdir", counted)
    for index in range(1540):
        assert _locate(folder, f"missing-{index}.md", state) is None
    assert listings == [folder]


def test_x16c_1540_unresolved_links_stay_under_five_seconds(tmp_path):
    from time import perf_counter
    from impacts_protocol.topology import check_topology
    root = workspace(tmp_path, "Form: grundlagen/ Knowledge Bundle per topic")
    router(root / "grundlagen", "\n".join(f"[x](missing-{i}.md)" for i in range(1540)))
    for index in range(1540):
        (root / "grundlagen" / f"rule-{index}.md").touch()
    start = perf_counter()
    issues, _, _ = check_topology(root, r"human:[^:\s][^\s]*")
    assert perf_counter() - start < 5
    assert len(issues) == 3080
    assert all(issue.code == "topology.shape" for issue in issues)
    assert sum("does not resolve; correct or remove it" in issue.message for issue in issues) == 1540
    assert sum("is not linked from grundlagen/CONTEXT.md; link it" in issue.message for issue in issues) == 1540


def test_x4_ignored_router_and_declared_directory_are_not_read(tmp_path):
    import subprocess
    from impacts_protocol.topology import check_topology
    root = workspace(tmp_path, "Form: tools/ Tool\nForm: dist/ Unknown")
    subprocess.run(["git", "init", "-q", str(root)], check=True)
    (root / ".gitignore").write_text("dist/\ntools/notes/CONTEXT.md\n")
    router(root / "dist", "# Build")
    router(root / "tools/notes", "---\ntype: hauptprozess\nid: broken\nid: duplicate\n---")
    issues, _, _ = check_topology(root, r"human:[^:\s][^\s]*")
    assert issues == []


def test_case_different_deep_link_is_a_finding(tmp_path):
    root = workspace(tmp_path, "Form: records/ Record Library per subject\nForm: grundlagen/ Knowledge Bundle per topic")
    router(root / "grundlagen", "[topic](topic/) [deep](topic/Regel.md)")
    router(root / "grundlagen/topic", "Form: Knowledge Bundle per rule\n[rule](regel.md)")
    (root / "grundlagen/topic/regel.md").touch()
    messages = [issue.message for issue in validate(root).issues]
    assert messages == ["Link 'topic/Regel.md' differs from the on-disk spelling 'grundlagen/topic/regel.md'; use the on-disk spelling"]


def test_e2_broken_symlink_entry_names_itself(tmp_path):
    root = workspace(tmp_path, "Form: records/ Record Library per subject\nForm: grundlagen/ Knowledge Bundle per topic")
    router(root / "grundlagen", "[a](a.md)")
    (root / "grundlagen/a.md").symlink_to("missing.md")
    messages = [issue.message for issue in validate(root).issues if issue.path == "grundlagen/a.md"]
    assert messages == ["a.md is a broken symlink; remove it or restore its target"]


def test_e3_no_break_space_after_root_path_is_accepted(tmp_path):
    root = workspace(tmp_path, "Form: records/ Record Library per subject\nForm: grundlagen/\u00a0Knowledge Bundle per topic")
    router(root / "grundlagen", "# Rules")
    assert validate(root).valid


def test_e3_root_line_without_folder_is_quoted(tmp_path):
    root = workspace(tmp_path, "Form: records/ Record Library per subject\nForm: Knowledge Bundle per topic")
    messages = [issue.message for issue in validate(root).issues]
    assert "Root Form line 'Knowledge Bundle per topic' names no folder; write Form: <folder>/ <form> per <unit>" in messages


def test_e4_unit_with_slash_is_a_self_declaration(tmp_path):
    root = workspace(tmp_path, "Form: records/ Record Library per subject\nForm: grundlagen/ Knowledge Bundle per topic")
    router(root / "grundlagen", "[norms](normen/)")
    router(root / "grundlagen/normen", "Form: Knowledge Bundle per Norm/ Regel")
    assert validate(root).valid


def test_e5_unreadable_router_is_one_finding(tmp_path):
    root = workspace(tmp_path, "Form: records/ Record Library per subject\nForm: grundlagen/ Knowledge Bundle per topic")
    (root / "grundlagen").mkdir(exist_ok=True)
    (root / "grundlagen/CONTEXT.md").write_bytes(b"---\ntype: \xff\n---\n")
    assert len([issue for issue in validate(root).issues if "cannot be read" in issue.message]) == 1


def test_init_gitignore_keeps_office_leftovers_out_of_levels(tmp_path):
    import subprocess
    root = workspace(tmp_path, "Form: records/ Record Library per subject\nForm: grundlagen/ Knowledge Bundle per topic")
    subprocess.run(["git", "init", "-q", str(root)], check=True)
    router(root / "grundlagen", "[rule](rule.md)")
    for name in ("rule.md", "Thumbs.db", "desktop.ini", "~$rule.docx"):
        (root / "grundlagen" / name).touch()
    assert validate(root).valid


def test_table_beside_instance_folders_moves_into_the_router(tmp_path):
    root = workspace(tmp_path)
    (root / "records/one").mkdir()
    (root / "records/one/akte.md").touch()
    (root / "records/two").mkdir()
    (root / "records/two/akte.md").touch()
    (root / "records/table.md").touch()
    issue, = validate(root).issues
    assert issue.message == "table.md is a file among the instance folders of records/; if it is the kind's table, move it into records/CONTEXT.md; otherwise move it to the instance or record kind it belongs to"
