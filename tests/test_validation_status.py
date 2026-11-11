"""Status reports retain judged scope, repair locations and binding boundaries."""
import json
import shutil

import pytest

from impacts_protocol import validate
from impacts_protocol.cli import main
from impacts_protocol.model import Issue, RULES
from tests.support import (
    committed_workspace, entry_active, make_attempt, read_context, replace_context,
    write_context, write_vorgang,
)
from tests.test_attempt_references import pair


@pytest.mark.parametrize("family", [*RULES, "future"])
@pytest.mark.parametrize("rule", ["", "02_protocol/binding.md#execution"])
def test_every_issue_has_a_rule_even_without_an_explicit_anchor(family, rule):
    issue = Issue(f"{family}.synthetic", "CONTEXT.md", "Synthetic defect; restore the expected value", rule)
    assert issue.rule
    assert "#" in issue.rule
    if rule:
        assert issue.rule == rule


@pytest.mark.parametrize("reference_index", [0, 1])
def test_status_counts_header_and_external_pointer(tmp_path, capsys, reference_index):
    root, case, first, second = pair(tmp_path)
    pointer = {"eingabe": "input/auftrag.md", "ablage": "synthetic-store",
               "schluessel": "synthetic-key", "sha256": "sha256:" + "0" * 64}
    first["gelesen"] = first["gelesen"][:reference_index] + [pointer]
    replace_context(case / "CONTEXT.md", dict(read_context(case / "CONTEXT.md"), laufpfad=[first, second]))
    report = validate(root)
    assert report.valid, report.issues
    expected = {"hauptprozess": 1, "teilprozess": 1, "arbeitsschritt": 2, "vorgang": 1, "versuch": 2}
    assert report.judged == expected
    assert main(["validate", str(root)]) == 0
    assert capsys.readouterr().out.splitlines()[0] == (
        "impacts validate v0.4.1 against pin v0.4.1: 1 Hauptprozesse, 1 Teilprozesse, "
        "2 Arbeitsschritte, 1 Vorgänge, 2 Versuche judged; 0 Vorgänge not judged; 0 definition trees outside hauptprozesse/"
    )
    assert main(["validate", str(root), "--json"]) == 0
    data = json.loads(capsys.readouterr().out)
    assert data["judged"] == expected
    assert data["release"] == data["pin"] == "v0.4.1"
    assert data["superseded"] == []
    assert data["external_references"] == [{"vorgang": "vorgaenge/test/CONTEXT.md", "pointer": f"/laufpfad/0/gelesen/{reference_index}"}]
    assert data["external_references_not_verified"] == 1


def test_excluded_definition_trees_are_reported_without_judging_or_following_links(tmp_path, capsys):
    root, _ = committed_workspace(tmp_path)
    for home in ("analyse", "applications", "other"):
        shutil.copytree(root / "hauptprozesse/video", root / home / "video")
        # Invalid definition content must remain outside judgment.
        (root / home / "video/produktion/start/CONTEXT.md").write_text("broken")
    write_context(root / "notes/ordinary/CONTEXT.md", {"type": "teilprozess"})
    (root / "linked").symlink_to(root / "analyse", target_is_directory=True)
    report = validate(root)
    assert report.valid, report.issues
    assert len(report.not_judged) == 3
    assert report.judged == {"hauptprozess": 1, "teilprozess": 1, "arbeitsschritt": 2, "vorgang": 0, "versuch": 0}
    assert main(["validate", str(root), "--json"]) == 0
    data = json.loads(capsys.readouterr().out)
    assert data["not_judged_counts"] == {"vorgang": 0, "definition_tree": 3}
    assert main(["validate", str(root)]) == 0
    assert "0 Vorgänge not judged; 3 definition trees outside hauptprozesse/" in capsys.readouterr().out.splitlines()[0]
    assert data["not_judged"] == [
        {"path": f"{home}/video/CONTEXT.md", "protocol": None,
         "reason": "definition tree outside hauptprozesse/, not bindable"}
        for home in ("analyse", "applications", "other")
    ]
    replace_context(root / "CONTEXT.md", {"type": "workspace", "protocol": "v0.3.31"})
    old = validate(root)
    assert old.valid and len(old.not_judged) == 1
    assert not any(old.judged.values())


@pytest.mark.parametrize("status", ["aktiv", "wartend"])
@pytest.mark.parametrize("remove_attempt", [False, True])
@pytest.mark.parametrize("empty_written", [False, True])
def test_unfinished_attempt_survives_missing_empty_directories(tmp_path, status, remove_attempt, empty_written):
    root, case, first, second = pair(tmp_path)
    attempt = case / "pruefen/001"
    second["status"] = status
    if empty_written:
        second["geschrieben"] = []
    if status == "wartend":
        second["wiedereinstieg"] = {"ausloeser": "Synthetic response",
                                   "continuation_ref": "vorgaenge/test/start/001/output/ergebnis.md"}
    replace_context(case / "CONTEXT.md", dict(read_context(case / "CONTEXT.md"), laufpfad=[first, second]))
    (attempt / "output").rmdir()
    if remove_attempt:
        attempt.rmdir()
        attempt.parent.rmdir()
    assert validate(root).valid, validate(root).issues
    # Absent output cannot satisfy completion.
    second.update(status="abgeschlossen", gewaehlte_route="freigegeben", geschrieben=[])
    second.pop("wiedereinstieg", None)
    replace_context(case / "CONTEXT.md", dict(read_context(case / "CONTEXT.md"), laufpfad=[first, second]))
    assert not validate(root).valid


@pytest.mark.parametrize("start", ["start", "pruefen"])
def test_successor_can_restart_at_entry_or_waiting_predecessor_position(tmp_path, start, capsys):
    root, case, first, second = pair(tmp_path)
    second["status"] = "wartend"
    second["wiedereinstieg"] = {"ausloeser": "Synthetic response",
                               "continuation_ref": "vorgaenge/test/start/001/output/ergebnis.md"}
    replace_context(case / "CONTEXT.md", dict(read_context(case / "CONTEXT.md"), laufpfad=[first, second]))
    revision = read_context(case / "CONTEXT.md")["hauptprozess_revision"].removeprefix("git-tree:")
    attempt = make_attempt(root / "vorgaenge/restart", start, 1, input_bytes="source")
    write_vorgang(root, "restart", revision, [entry_active(start, 1, attempt)])
    context = root / "vorgaenge/restart/CONTEXT.md"
    replace_context(context, dict(read_context(context), vorgaenger="vorgaenge/test/CONTEXT.md"))
    report = validate(root)
    assert report.valid, report.issues
    assert report.superseded == ("vorgaenge/test/CONTEXT.md",)
    assert main(["validate", str(root), "--json"]) == 0
    assert json.loads(capsys.readouterr().out)["superseded"] == ["vorgaenge/test/CONTEXT.md"]


def test_missing_pin_names_the_fix_and_rule(tmp_path, capsys):
    root, _ = committed_workspace(tmp_path)
    replace_context(root / "CONTEXT.md", {"type": "workspace"})
    assert main(["validate", str(root)]) == 1
    lines = capsys.readouterr().out.splitlines()
    assert "against pin none" in lines[0]
    assert lines[1] == (
        "schema.invalid: CONTEXT.md: protocol pin missing; add protocol: v0.4.1 to the frontmatter "
        "(02_protocol/binding.md#validation-issue-codes)"
    )


def test_referenced_file_errors_group_under_referring_vorgang(tmp_path):
    root, case, _, _ = pair(tmp_path)
    referenced = case / "start/001/output/ergebnis.md"
    referenced.write_text("changed")
    issues = validate(root).issues
    assert issues
    assert all(issue.path == "vorgaenge/test/CONTEXT.md" and issue.rule for issue in issues)
    assert all("vorgaenge/test/start/001/output/ergebnis.md" in issue.message for issue in issues)


def test_all_emitted_rule_anchors_resolve_in_protocol_docs():
    import ast
    from pathlib import Path
    import re

    root = Path(__file__).resolve().parents[1]
    rules = set(RULES.values()) | {Issue("unknown.synthetic", "x", "x").rule}
    for source in (root / "src/impacts_protocol").rglob("*.py"):
        for node in ast.walk(ast.parse(source.read_text())):
            if isinstance(node, ast.Call):
                for keyword in node.keywords:
                    if keyword.arg == "rule":
                        rules.add(ast.literal_eval(keyword.value))
    for rule in rules:
        document, anchor = rule.split("#", 1)
        path = root / document
        assert path.is_file(), rule
        text = path.read_text()
        headings = re.findall(r"^#{1,6} +(.+?) *#* *$", text, re.M)
        anchors = {re.sub(r"[^\w\- ]", "", heading.lower()).replace(" ", "-") for heading in headings}
        assert anchor in anchors, rule


@pytest.mark.parametrize("declaration,valid", [
    ("Ablage: synthetic-store Offline system", True),
    ("Ablage:\t synthetic-store", True),
    ("Ablage: synthetic-store", True),
    ("", False),
    ("- Ablage: synthetic-store Offline system", False),
    ("Ablage: Synthetic-store Offline system", False),
    ("Ablage:synthetic-store", False),
    (" Ablage: synthetic-store", False),
    ("```text\nAblage: synthetic-store\n```", False),
    ("~~~~\nAblage: synthetic-store\n~~~\nAblage: synthetic-store\n~~~~", False),
    ("    Ablage: synthetic-store", False),
])
@pytest.mark.parametrize("field", ["gelesen", "geschrieben"])
def test_external_store_requires_exact_root_body_declaration(tmp_path, declaration, valid, field):
    root, case, first, second = pair(tmp_path)
    write_context(root / "CONTEXT.md", {"type": "workspace", "protocol": "v0.4.0"}, declaration)
    pointer = {"ablage": "synthetic-store", "schluessel": "unavailable-object", "sha256": "sha256:" + "a" * 64}
    if field == "gelesen":
        first[field] = [dict(pointer, eingabe="input/auftrag.md")]
    else:
        second[field] = [pointer]  # Open attempts also carry checked store names.
    replace_context(case / "CONTEXT.md", dict(read_context(case / "CONTEXT.md"), laufpfad=[first, second]))
    report = validate(root)
    if field == "geschrieben":
        assert not report.valid  # Output schema and open-attempt rules remain enforced.
    else:
        assert report.valid is valid, report.issues
    assert report.external_references_not_verified == 1
    index = 0 if field == "gelesen" else 1
    assert report.external_references == (
        {"vorgang": "vorgaenge/test/CONTEXT.md", "pointer": f"/laufpfad/{index}/{field}/0"},
    )
    if not valid:
        missing = [issue for issue in report.issues if issue.code == "binding.reference_missing"]
        assert len(missing) == 1
        assert "'synthetic-store'" in missing[0].message
        assert "declare 'Ablage: synthetic-store <location>' in the workspace root router" in missing[0].message


@pytest.mark.parametrize("code,anchor", [
    ("process.gate", "decision-results-and-auslöser"),
    ("process.no_end", "hauptprozess-tree-rules"),
    ("process.unreachable", "hauptprozess-tree-rules"),
    ("process.future", "execution"),
])
def test_process_rules_select_specific_anchor_or_family_fallback(code, anchor):
    assert Issue(code, "CONTEXT.md", "Synthetic defect").rule == f"02_protocol/binding.md#{anchor}"


def test_undeclared_store_issue_names_each_reference_position(tmp_path):
    root, case, first, second = pair(tmp_path)
    write_context(root / "CONTEXT.md", {"type": "workspace", "protocol": "v0.4.0"}, "")
    pointer = {"ablage": "synthetic-store", "schluessel": "unavailable-object", "sha256": "sha256:" + "a" * 64}
    first["gelesen"] = [dict(pointer, eingabe="input/auftrag.md"), dict(pointer, eingabe="input/auftrag.md", schluessel="other")]
    replace_context(case / "CONTEXT.md", dict(read_context(case / "CONTEXT.md"), laufpfad=[first, second]))
    messages = [issue.message for issue in validate(root).issues if "undeclared" in issue.message]
    assert [message.split(":")[0] for message in messages] == ["/laufpfad/0/gelesen/0", "/laufpfad/0/gelesen/1"]
