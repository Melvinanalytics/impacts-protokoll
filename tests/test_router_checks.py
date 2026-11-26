"""Router contracts of v0.8.0: sections, size, table contracts, unindexed links and links in definitions."""
from pathlib import Path

import pytest

from impacts_protocol import validate
from .support import write_hauptprozess
from .test_topology import SECTIONS, ignoring, router, workspace


def codes(root):
    return [(issue.code, issue.path) for issue in validate(root).issues]


def three_entries(folder):
    """Return links to three synthetic files of a level."""
    folder.mkdir(parents=True, exist_ok=True)
    for name in ("a.md", "b.md", "c.md"):
        (folder / name).write_text("synthetic\n")
    return "[a](a.md)\n[b](b.md)\n[c](c.md)\n"


# B: level routers carry Overview and What to load

@pytest.mark.parametrize("form,folder", [
    ("Record Library per subject", "records"), ("Knowledge Bundle per topic", "grundlagen"), ("Context Map per capture", "analyse")])
def test_level_router_without_sections_is_a_navigation_finding(tmp_path, form, folder):
    root = workspace(tmp_path, f"Form: {folder}/ {form}" if folder != "records" else "Form: records/ Record Library per subject")
    links = three_entries(root / folder)
    (root / folder / "CONTEXT.md").write_text("# Level\n\n## Overview\n\n" + links)
    issue, = validate(root).issues
    assert (issue.code, issue.path) == ("topology.router_sections", f"{folder}/CONTEXT.md")
    assert "'What to load'" in issue.message and "'Overview'" not in issue.message


@pytest.mark.parametrize("headings", ["## What to load\n## Overview", "## Was laden\n\n### Übersicht", "# Overview\n# What to load ##"])
def test_level_router_sections_accept_template_spellings(tmp_path, headings):
    root = workspace(tmp_path)
    (root / "records" / "CONTEXT.md").write_text(f"# Records\n\n{headings}\n")
    assert validate(root).valid


@pytest.mark.parametrize("hidden", ["```\n## Overview\n## What to load\n```", "<!--\n## Overview\n## What to load\n-->", "Overview\nWhat to load"])
def test_sections_in_code_comments_or_prose_do_not_count(tmp_path, hidden):
    root = workspace(tmp_path)
    links = three_entries(root / "records")
    (root / "records" / "CONTEXT.md").write_text(f"# Records\n\n{hidden}\n\n{links}")
    assert codes(root) == [("topology.router_sections", "records/CONTEXT.md")]


@pytest.mark.parametrize("headings", ["## What To Load\n## OVERVIEW", "## WAS LADEN\n## übersicht"])
def test_section_headings_are_case_folded(tmp_path, headings):
    root = workspace(tmp_path)
    links = three_entries(root / "records")
    (root / "records" / "CONTEXT.md").write_text(f"# Records\n\n{headings}\n\n{links}")
    assert validate(root).valid


@pytest.mark.parametrize("count", [0, 1, 2, 3])
def test_sections_are_required_at_any_entry_count(tmp_path, count):
    root = workspace(tmp_path, "Form: records/ Record Library per subject\nForm: grundlagen/ Knowledge Bundle per topic")
    names = [f"rule-{i}.md" for i in range(count)]
    for name in names:
        (root / "grundlagen" / name).write_text("synthetic\n")
    (root / "grundlagen" / "CONTEXT.md").write_text("# Foundations\n\n" + "".join(f"[{n}]({n})\n" for n in names))
    assert codes(root) == [("topology.router_sections", "grundlagen/CONTEXT.md")]


def test_root_pipeline_and_instance_routers_need_no_sections(tmp_path):
    root = workspace(tmp_path, "Form: records/ Record Library per subject\nForm: ablauf/ Pipeline per process")
    (root / "ablauf" / "erster").mkdir(parents=True)
    (root / "ablauf" / "CONTEXT.md").write_text("# Processes\n\n[erster](erster/)\n")
    (root / "ablauf" / "erster" / "CONTEXT.md").write_text("# First\n")
    router(root / "records", f"# Records\n\n{SECTIONS}\n\n[one](one/)")
    (root / "records" / "one").mkdir()
    (root / "records" / "one" / "CONTEXT.md").write_text("# One\n")
    assert validate(root).valid


# D: router size

@pytest.mark.parametrize("size,finding", [(24_000, False), (24_001, True)])
def test_root_router_size_limit_is_24000_bytes(tmp_path, size, finding):
    root = workspace(tmp_path)
    context = root / "CONTEXT.md"
    text = context.read_text()
    context.write_text(text + "x" * (size - len(text.encode())))
    found = codes(root)
    assert found == ([("topology.router_size", "CONTEXT.md")] if finding else [])


def test_router_size_message_names_bytes_and_split(tmp_path):
    root = workspace(tmp_path, "Form: records/ Record Library per subject\nForm: grundlagen/ Knowledge Bundle per topic")
    (root / "grundlagen" / "CONTEXT.md").write_text(f"# Foundations\n\n{SECTIONS}\n" + "y" * 30_000)
    issue, = validate(root).issues
    assert issue.code == "topology.router_size"
    assert "grundlagen/CONTEXT.md has 30,0" in issue.message and "declared Knowledge Bundle sub-levels" in issue.message


def test_record_library_router_that_links_every_instance_has_no_size_cap(tmp_path):
    root = workspace(tmp_path)
    lines = []
    for index in range(260):
        name = f"lot-{index:04d}-synthetic-tender-with-a-long-name"
        (root / "records" / name).mkdir()
        (root / "records" / name / "CONTEXT.md").write_text("# Lot\n")
        lines.append(f"| [{name}/]({name}/) | synthetic lot {index} | open |")
    router_text = f"# Lots\n\n{SECTIONS}\n\n| Entry | What | State |\n|---|---|---|\n" + "\n".join(lines) + "\n"
    (root / "records" / "CONTEXT.md").write_text(router_text)
    assert len(router_text.encode()) > 24_000
    assert validate(root).valid


def test_capability_routers_are_measured_but_process_definitions_are_not(tmp_path):
    root = workspace(tmp_path, "Form: capabilities/ Capability")
    (root / "capabilities" / "rechner" / "deep").mkdir(parents=True)
    (root / "capabilities" / "rechner" / "CONTEXT.md").write_text("z" * 24_001)
    (root / "capabilities" / "rechner" / "deep" / "CONTEXT.md").write_text("z" * 24_001)
    write_hauptprozess(root / "hauptprozesse" / "video")
    step = next((root / "hauptprozesse" / "video").rglob("start/CONTEXT.md"))
    step.write_text(step.read_text() + "\n" + "w" * 24_001 + "\n")
    assert codes(root) == [("topology.router_size", "capabilities/rechner/CONTEXT.md")]


# E: opt-in table contracts

CONTRACT = '<!-- impacts:table-contract heading="Overview" columns="Entry, Stage" -->'


def contract_router(root, header):
    (root / "records" / "one").mkdir()
    (root / "records" / "CONTEXT.md").write_text(
        f"# Records\n\n{CONTRACT}\n\n## What to load\n\n## Overview\n\nText before the table.\n\n{header}\n|---|---|---|\n| [one](one/) | open | tool |\n")


def test_table_contract_satisfied_passes(tmp_path):
    root = workspace(tmp_path)
    contract_router(root, "| Entry | Stage | Writer |")
    assert validate(root).valid


def test_renamed_contract_column_fails(tmp_path):
    root = workspace(tmp_path)
    contract_router(root, "| Entry | Status | Writer |")
    issue, = validate(root).issues
    assert (issue.code, issue.path) == ("topology.table_contract", "records/CONTEXT.md")
    assert issue.message == "required machine-written table columns Stage under 'Overview' are missing; restore the header columns expected by workspace tools"


@pytest.mark.parametrize("body", [
    "## Overview\n\nNo table here.\n\n## Other\n\n| Entry | Stage |\n|---|---|\n",
    "## Elsewhere\n\n| Entry | Stage |\n|---|---|\n",
])
def test_contract_needs_its_heading_and_a_table_in_that_section(tmp_path, body):
    root = workspace(tmp_path)
    (root / "records" / "CONTEXT.md").write_text(f"# Records\n\n{CONTRACT}\n\n## What to load\n\n{body}")
    found = codes(root)
    assert ("topology.table_contract", "records/CONTEXT.md") in found


@pytest.mark.parametrize("marker", ["```\n" + CONTRACT + "\n```", "`" + CONTRACT + "`"])
def test_marker_in_code_declares_nothing(tmp_path, marker):
    root = workspace(tmp_path)
    (root / "records" / "CONTEXT.md").write_text(f"# Records\n\n{marker}\n\n{SECTIONS}\n")
    assert validate(root).valid


def test_malformed_marker_is_a_finding(tmp_path):
    root = workspace(tmp_path)
    (root / "records" / "CONTEXT.md").write_text(f"# Records\n\n<!-- impacts:table-contract heading=Overview -->\n\n{SECTIONS}\n")
    issue, = validate(root).issues
    assert issue.code == "topology.table_contract" and "malformed" in issue.message


def test_root_router_contract_is_checked(tmp_path):
    root = workspace(tmp_path)
    with (root / "CONTEXT.md").open("a") as handle:
        handle.write('\n<!-- impacts:table-contract heading="Runs" columns="Run" -->\n\n## Runs\n\n| Date |\n|---|\n')
    assert codes(root) == [("topology.table_contract", "CONTEXT.md")]


# F: links to unindexed directories

def test_deeper_unindexed_folder_linked_from_level_router_fails(tmp_path):
    root = workspace(tmp_path)
    (root / "records" / "one" / "raw").mkdir(parents=True)
    (root / "records" / "one" / "raw" / "scan.md").touch()
    (root / "records" / "CONTEXT.md").write_text(f"# Records\n\n{SECTIONS}\n\n[one](one/)\n[raw scans](one/raw/)\n")
    issue, = validate(root).issues
    assert (issue.code, issue.path) == ("topology.link_unindexed", "records/CONTEXT.md")
    assert "one/raw/" in issue.message


def test_instance_folder_of_the_routers_own_level_passes(tmp_path):
    root = workspace(tmp_path)
    (root / "records" / "one").mkdir()
    (root / "records" / "one" / "scan.md").touch()
    (root / "records" / "CONTEXT.md").write_text(f"# Records\n\n{SECTIONS}\n\n[one/](one/)\n")
    assert validate(root).valid


@pytest.mark.parametrize("index", ["CONTEXT.md", "README.md"])
def test_indexed_deeper_folder_passes(tmp_path, index):
    root = workspace(tmp_path)
    (root / "records" / "one" / "raw").mkdir(parents=True)
    (root / "records" / "one" / "raw" / index).write_text("# Raw\n")
    (root / "records" / "CONTEXT.md").write_text(f"# Records\n\n{SECTIONS}\n\n[one](one/)\n[raw](one/raw/)\n")
    assert validate(root).valid


def test_root_link_into_code_home_is_exempt(tmp_path):
    root = workspace(tmp_path, "Form: tools/ Tool")
    (root / "tools" / "sub").mkdir(parents=True)
    (root / "tools" / "sub" / "run.py").touch()
    with (root / "CONTEXT.md").open("a") as handle:
        handle.write("\n[tools](tools/) and [sub](tools/sub/)\n")
    assert validate(root).valid


def test_root_link_to_unindexed_deeper_folder_fails(tmp_path):
    root = workspace(tmp_path)
    (root / "records" / "one").mkdir()
    (root / "records" / "one" / "scan.md").touch()
    (root / "records" / "CONTEXT.md").write_text(f"# Records\n\n{SECTIONS}\n\n[one](one/)\n")
    with (root / "CONTEXT.md").open("a") as handle:
        handle.write("\n[first record](records/one/)\n")
    assert codes(root) == [("topology.link_unindexed", "CONTEXT.md")]


# C: links in definition bodies

def definition(tmp_path):
    root = workspace(tmp_path)
    write_hauptprozess(root / "hauptprozesse" / "video")
    step = next((root / "hauptprozesse" / "video").rglob("start/CONTEXT.md"))
    return root, step


def test_broken_link_in_arbeitsschritt_body_is_a_finding(tmp_path):
    root, step = definition(tmp_path)
    step.write_text(step.read_text() + "\nSee [the rule](../../../../grundlagen/missing.md) and [here](#nowhere).\n")
    found = codes(root)
    path = step.relative_to(root).as_posix()
    assert found == [("topology.link_broken", path), ("topology.link_broken", path)]


def test_resolving_links_in_definition_bodies_pass(tmp_path):
    root, step = definition(tmp_path)
    (root / "records" / "CONTEXT.md").write_text(f"# Records\n\n{SECTIONS}\n")
    heading = "## Inputs"
    step.write_text(step.read_text() + f"\n{heading}\n\nSee [records](../../../../records/CONTEXT.md#overview) and [inputs](#inputs).\n")
    assert validate(root).valid


def test_definition_link_leaving_the_workspace_is_a_finding(tmp_path):
    root, step = definition(tmp_path)
    (tmp_path / "outside.md").write_text("synthetic")
    step.write_text(step.read_text() + "\n[source](../../../../../../outside.md)\n")
    issue, = validate(root).issues
    assert issue.code == "topology.link_broken" and "leaves the workspace" in issue.message


def test_definition_link_to_a_path_git_ignores_is_a_finding(tmp_path):
    root, step = definition(tmp_path)
    ignoring(root, "*.local.md\n")
    (root / "notes.local.md").write_text("synthetic\n")
    step.write_text(step.read_text() + "\n[notes](../../../../notes.local.md)\n")
    issue, = validate(root).issues
    assert (issue.code, issue.path) == ("topology.link_broken", step.relative_to(root).as_posix())
    assert "Git ignores" in issue.message


def test_unparseable_definition_adds_no_link_finding(tmp_path):
    root, step = definition(tmp_path)
    step.write_text("---\ntype: [unclosed\n---\n[x](missing.md)\n")
    assert not [issue for issue in validate(root).issues if issue.code.startswith("topology.")]


def test_archived_definition_folder_is_not_link_checked(tmp_path):
    root, step = definition(tmp_path)
    archive = step.parents[2] / "_archive"
    archive.mkdir()
    (archive / "CONTEXT.md").write_text("[gone](missing.md)\n")
    assert not [issue for issue in validate(root).issues if issue.code.startswith("topology.")]


# Review fixes

@pytest.mark.parametrize("target", ["../hauptprozesse/", "../vorgaenge/", "../vorgaenge/case-1/start/"])
def test_links_into_core_folders_are_not_unindexed(tmp_path, target):
    root = workspace(tmp_path)
    (root / "vorgaenge" / "case-1" / "start").mkdir(parents=True)
    (root / "records" / "CONTEXT.md").write_text(f"# Records\n\n{SECTIONS}\n\n[core]({target})\n")
    assert not [issue for issue in validate(root).issues if issue.code == "topology.link_unindexed"]


def test_sibling_level_folder_without_index_is_unindexed(tmp_path):
    root = workspace(tmp_path, "Form: records/ Record Library per subject\nForm: grundlagen/ Knowledge Bundle per topic")
    (root / "grundlagen" / "CONTEXT.md").write_text(f"# Foundations\n\n{SECTIONS}\n")
    (root / "records" / "one").mkdir()
    (root / "records" / "one" / "scan.md").touch()
    (root / "records" / "CONTEXT.md").write_text(f"# Records\n\n{SECTIONS}\n\n[one](one/)\n")
    with (root / "grundlagen" / "CONTEXT.md").open("a") as handle:
        handle.write("\n[record one](../records/one/)\n")
    assert codes(root) == [("topology.link_unindexed", "grundlagen/CONTEXT.md")]


def test_index_detection_is_case_exact(tmp_path):
    root = workspace(tmp_path)
    (root / "records" / "one" / "raw").mkdir(parents=True)
    (root / "records" / "one" / "raw" / "readme.md").write_text("# lower-case readme\n")
    (root / "records" / "CONTEXT.md").write_text(f"# Records\n\n{SECTIONS}\n\n[one](one/)\n[raw](one/raw/)\n")
    assert codes(root) == [("topology.link_unindexed", "records/CONTEXT.md")]


def test_commented_out_table_does_not_satisfy_a_contract(tmp_path):
    root = workspace(tmp_path)
    (root / "records" / "CONTEXT.md").write_text(
        f"# Records\n\n{CONTRACT}\n\n## What to load\n\n## Overview\n\n<!--\n| Entry | Stage |\n|---|---|\n-->\n")
    assert codes(root) == [("topology.table_contract", "records/CONTEXT.md")]


def test_commented_out_heading_does_not_satisfy_a_contract(tmp_path):
    root = workspace(tmp_path)
    (root / "records" / "CONTEXT.md").write_text(
        f"# Records\n\n{CONTRACT}\n\n## What to load\n\n<!--\n## Overview\n\n| Entry | Stage |\n|---|---|\n-->\n\n## Overview\n\nNo table.\n")
    assert codes(root) == [("topology.table_contract", "records/CONTEXT.md")]


def test_escaped_pipe_in_header_cell_is_one_column(tmp_path):
    root = workspace(tmp_path)
    (root / "records" / "CONTEXT.md").write_text(
        '# Records\n\n<!-- impacts:table-contract heading="Overview" columns="Entry, A|B" -->\n\n'
        "## What to load\n\n## Overview\n\n| Entry | A\\|B |\n|---|---|\n")
    assert validate(root).valid


def test_every_section_with_the_contract_heading_is_checked(tmp_path):
    root = workspace(tmp_path)
    (root / "records" / "CONTEXT.md").write_text(
        f"# Records\n\n{CONTRACT}\n\n## What to load\n\n## Overview\n\n| Entry | Stage |\n|---|---|\n\n## Overview\n\n| Entry | Status |\n|---|---|\n")
    issue, = validate(root).issues
    assert issue.code == "topology.table_contract"
    assert "Stage" in issue.message and "section 2 of 2" in issue.message


def test_anchor_matches_across_unicode_normal_forms(tmp_path):
    root = workspace(tmp_path, "Form: records/ Record Library per subject\nForm: grundlagen/ Knowledge Bundle per topic")
    decomposed = "Übersicht"
    (root / "grundlagen" / "CONTEXT.md").write_text(f"# Foundations\n\n{SECTIONS}\n\n## {decomposed} Regeln\n\n[here](#übersicht-regeln)\n")
    assert validate(root).valid


def test_sections_match_across_unicode_normal_forms(tmp_path):
    root = workspace(tmp_path)
    (root / "records" / "CONTEXT.md").write_text("# Records\n\n## Was laden\n\n## Übersicht\n")
    assert validate(root).valid


def test_one_blocking_rule_for_validator_and_viewer():
    from impacts_protocol.model import Issue
    from impacts_protocol.topology import blocks_vorgaenge
    assert blocks_vorgaenge(Issue("topology.shape", "ablauf/erster", "x"))
    assert not blocks_vorgaenge(Issue("topology.link_missing", "stray.md", "x"))
    assert not blocks_vorgaenge(Issue("topology.router_size", "CONTEXT.md", "x"))
    assert not blocks_vorgaenge(Issue("structure.level", "hauptprozesse/video", "x"))
    assert not blocks_vorgaenge(Issue("binding.revision", "vorgaenge/a/CONTEXT.md", "x"))


# Second review round

def test_comment_opener_in_inline_code_does_not_hide_the_contract_table(tmp_path):
    root = workspace(tmp_path)
    (root / "records" / "CONTEXT.md").write_text(
        f"# Records\n\n{CONTRACT}\n\nWrite `<!--` to start a comment.\n\n## What to load\n\n## Overview\n\n| Entry | Stage |\n|---|---|\n")
    assert validate(root).valid


def test_comment_opener_in_a_fence_does_not_hide_sections_or_links(tmp_path):
    root = workspace(tmp_path)
    (root / "records" / "one").mkdir()
    (root / "records" / "one" / "scan.md").touch()
    (root / "records" / "CONTEXT.md").write_text(f"# Records\n\n```html\n<!-- example\n```\n\n{SECTIONS}\n\n[one](one/)\n")
    assert validate(root).valid


def test_comment_opener_in_a_fence_does_not_hide_anchors(tmp_path):
    root = workspace(tmp_path, "Form: records/ Record Library per subject\nForm: grundlagen/ Knowledge Bundle per topic")
    (root / "grundlagen" / "CONTEXT.md").write_text(f"# Foundations\n\n```\n<!-- example\n```\n\n{SECTIONS}\n\n## Rules\n\n[rules](#rules)\n")
    assert validate(root).valid


def test_fence_inside_a_comment_does_not_hide_the_rest(tmp_path):
    root = workspace(tmp_path)
    (root / "records" / "CONTEXT.md").write_text(f"# Records\n\n<!--\n```\n-->\n\n{SECTIONS}\n")
    assert validate(root).valid


def test_escaped_pipe_in_marker_column(tmp_path):
    root = workspace(tmp_path)
    (root / "records" / "CONTEXT.md").write_text(
        '# Records\n\n<!-- impacts:table-contract heading="Overview" columns="Entry, A\\|B" -->\n\n'
        "## What to load\n\n## Overview\n\n| Entry | A\\|B |\n|---|---|\n")
    assert validate(root).valid


def test_workspace_path_with_dot_dot_gives_the_same_findings(tmp_path):
    root = workspace(tmp_path)
    (root / "hauptprozesse").mkdir(exist_ok=True)
    (root / "records" / "CONTEXT.md").write_text(f"# Records\n\n{SECTIONS}\n\n[core](../hauptprozesse/)\n[gone](missing.md)\n")
    (root.parent / "zz").mkdir()
    detour = root.parent / "zz" / ".." / root.name
    assert [(i.code, i.path) for i in validate(detour).issues] == [(i.code, i.path) for i in validate(root).issues] == [("topology.link_broken", "records/CONTEXT.md")]


# Third review round

def test_link_to_a_declared_file_kind_level_without_router_passes(tmp_path):
    root = workspace(tmp_path, "Form: records/ Record Library per kind\nForm: grundlagen/ Knowledge Bundle per topic")
    (root / "records" / "people").mkdir()
    (root / "records" / "people" / "anna.md").write_text("synthetic\n")
    (root / "records" / "CONTEXT.md").write_text(f"# Records\n\n{SECTIONS}\n\nForm: people/ Record Library per person\n[people](people/)\n")
    (root / "grundlagen" / "CONTEXT.md").write_text(f"# Foundations\n\n{SECTIONS}\n\n[people](../records/people/)\n")
    assert validate(root).valid


def test_symlinked_index_does_not_count(tmp_path):
    root = workspace(tmp_path)
    (root / "records" / "one" / "raw").mkdir(parents=True)
    (root / "records" / "one" / "raw" / "scan.md").touch()
    (tmp_path / "elsewhere.md").write_text("# outside\n")
    (root / "records" / "one" / "raw" / "README.md").symlink_to(tmp_path / "elsewhere.md")
    (root / "records" / "CONTEXT.md").write_text(f"# Records\n\n{SECTIONS}\n\n[one](one/)\n[raw](one/raw/)\n")
    assert ("topology.link_unindexed", "records/CONTEXT.md") in codes(root)


def test_prose_with_a_pipe_above_a_rule_is_no_table(tmp_path):
    root = workspace(tmp_path)
    (root / "records" / "CONTEXT.md").write_text(
        f"# Records\n\n{CONTRACT}\n\n## What to load\n\n## Overview\n\nSee state A | B\n---\n\n| Entry | Stage |\n|---|---|\n")
    assert validate(root).valid


def test_tight_cell_keeps_its_escaped_pipe(tmp_path):
    root = workspace(tmp_path)
    (root / "records" / "CONTEXT.md").write_text(
        '# Records\n\n<!-- impacts:table-contract heading="Overview" columns="Entry, A\\|" -->\n\n'
        "## What to load\n\n## Overview\n\n|Entry|A\\||\n|---|---|\n")
    assert validate(root).valid


def test_multiline_inline_code_with_comment_opener_hides_nothing(tmp_path):
    root = workspace(tmp_path)
    (root / "records" / "CONTEXT.md").write_text(
        f"# Records\n\n{CONTRACT}\n\nWrite `x\n<!-- y` to start.\n\n## What to load\n\n## Overview\n\n| Entry | Stage |\n|---|---|\n")
    assert validate(root).valid


def test_unclosed_fence_inside_a_comment_hides_no_contract(tmp_path):
    root = workspace(tmp_path)
    (root / "records" / "CONTEXT.md").write_text(
        f"# Records\n\n<!--\n```markdown\nold\n-->\n\n{CONTRACT}\n\n## What to load\n\n## Overview\n\n| Entry | Status |\n|---|---|\n")
    assert codes(root) == [("topology.table_contract", "records/CONTEXT.md")]


def test_contract_attributes_in_either_order(tmp_path):
    root = workspace(tmp_path)
    (root / "records" / "CONTEXT.md").write_text(
        '# Records\n\n<!-- impacts:table-contract columns="Entry, Stage" heading="Overview" -->\n\n'
        "## What to load\n\n## Overview\n\n| Entry | Status |\n|---|---|\n")
    issue, = validate(root).issues
    assert issue.code == "topology.table_contract" and "Stage" in issue.message and "malformed" not in issue.message


def test_contract_in_a_pipeline_home_and_process_router_is_checked(tmp_path):
    root = workspace(tmp_path, "Form: records/ Record Library per subject\nForm: ablauf/ Pipeline per process")
    (root / "ablauf" / "erster").mkdir(parents=True)
    (root / "ablauf" / "CONTEXT.md").write_text(f"# Processes\n\n{CONTRACT}\n\n## Overview\n\n| Entry | Status |\n|---|---|\n\n[erster](erster/)\n")
    (root / "ablauf" / "erster" / "CONTEXT.md").write_text(f"# First\n\n{CONTRACT}\n\n## Overview\n\n| Entry | Status |\n|---|---|\n")
    assert codes(root) == [("topology.table_contract", "ablauf/CONTEXT.md"), ("topology.table_contract", "ablauf/erster/CONTEXT.md")]


# Fourth review round

@pytest.mark.parametrize("after", ["<!-- maintainer: run `impacts validate` -->", "```\nimpacts `date`\n```", "## Notes\n\nRun `date`."])
def test_unmatched_backtick_pairs_no_code_span_across_a_block(tmp_path, after):
    """A code span lives in one paragraph: a stray backtick never pairs with one past a blank
    line, a fence or a heading, so it hides no heading, link or comment."""
    root = workspace(tmp_path, "Form: records/ Record Library per subject\nForm: grundlagen/ Knowledge Bundle per topic")
    links = three_entries(root / "grundlagen")
    (root / "grundlagen" / "CONTEXT.md").write_text(
        f"# Foundations\n\nPrices use the foot mark 5` for feet.\n\n{SECTIONS}\n\n{links}\n{after}\n")
    assert codes(root) == []


def test_unmatched_backtick_before_a_heading_line_keeps_the_heading():
    from impacts_protocol.topology import body_lines
    assert list(body_lines("Price 5` per item.\n## Overview\nUse `x`.\n"))[1] == "## Overview"


@pytest.mark.parametrize("spelling", ["relative", "absolute"])
def test_held_folder_stays_held_under_a_relative_root(tmp_path, monkeypatch, spelling):
    root = workspace(tmp_path, "Form: legacy/ none: synthetic hold; decided by human:fixture")
    write_hauptprozess(root / "legacy" / "old")
    monkeypatch.chdir(tmp_path)
    report = validate(Path("workspace") if spelling == "relative" else root)
    assert report.valid and report.not_judged == ()


def test_ignored_level_router_draws_the_same_findings_as_on_a_clone(tmp_path):
    root = workspace(tmp_path, "Form: records/ Record Library per subject\nForm: grundlagen/ Knowledge Bundle per topic")
    links = three_entries(root / "grundlagen")
    (root / "grundlagen" / "CONTEXT.md").write_text(f"# Foundations\n\n{SECTIONS}\n\n{links}")
    ignoring(root, "grundlagen/CONTEXT.md\n")
    local = codes(root)
    (root / "grundlagen" / "CONTEXT.md").unlink()
    assert local == codes(root) and ("topology.router_sections", "grundlagen/CONTEXT.md") not in local


def test_ignored_folder_with_a_decomposed_name_is_absent(tmp_path):
    import unicodedata
    root = workspace(tmp_path)
    for name in (unicodedata.normalize("NFD", "notiz-ü"), "notiz-plain"):
        (root / name).mkdir()
        (root / name / "a.md").write_text("synthetic\n")
    with (root / "CONTEXT.md").open("a") as handle:
        handle.write(f"\n[n]({unicodedata.normalize('NFC', 'notiz-ü')}/a.md)\n[p](notiz-plain/a.md)\n")
    ignoring(root, "notiz-*/\n")
    ignored = [issue for issue in validate(root).issues if "Git ignores" in issue.message]
    assert codes(root) == [("topology.link_broken", "CONTEXT.md")] * 2 and len(ignored) == 2


def test_unlinked_symlink_entry_is_not_covered_by_its_linked_target(tmp_path):
    root = workspace(tmp_path, "Form: records/ Record Library per subject\nForm: grundlagen/ Knowledge Bundle per topic")
    (root / "grundlagen" / "r0000.md").write_text("synthetic\n")
    (root / "grundlagen" / "zz-alias.md").symlink_to("r0000.md")
    (root / "grundlagen" / "CONTEXT.md").write_text(f"# Foundations\n\n{SECTIONS}\n\n[r](r0000.md)\n")
    assert codes(root) == [("topology.link_missing", "grundlagen/zz-alias.md")]


@pytest.mark.parametrize("sections,anchor", [
    ("  ## What to load\n\n  ## Overview", "#what-to-load"),
    ("## What to load\n\n## `Overview`", "#overview"),
    ("## what to load\n\n## overview", "#overview")])
def test_one_heading_reading_for_sections_anchors_and_contracts(tmp_path, sections, anchor):
    root = workspace(tmp_path, "Form: records/ Record Library per subject\nForm: grundlagen/ Knowledge Bundle per topic")
    links = three_entries(root / "grundlagen")
    (root / "grundlagen" / "CONTEXT.md").write_text(
        f"# Foundations\n\n{CONTRACT.replace('Stage', 'Note')}\n\n{sections}\n\n| Entry | Note |\n|---|---|\n\n{links}\n[load]({anchor})\n")
    assert codes(root) == []


def test_stray_backtick_and_comment_in_one_paragraph_is_a_stated_limit():
    """As in CommonMark, the code span opened first wins inside its paragraph, so a comment
    after a stray backtick in the same paragraph opens no comment; CONTRIBUTING states it."""
    from impacts_protocol.topology import body_lines
    assert "[l](l.md)" in list(body_lines("Price 5` per item\n<!-- note `x`\n[l](l.md)\n-->\n"))


# Final review round

def test_knowledge_bundle_size_finding_advises_sub_levels(tmp_path):
    root = workspace(tmp_path, "Form: records/ Record Library per subject\nForm: grundlagen/ Knowledge Bundle per topic")
    (root / "grundlagen" / "CONTEXT.md").write_text(f"# Foundations\n\n{SECTIONS}\n" + "y" * 30_000)
    issue, = validate(root).issues
    assert issue.code == "topology.router_size"
    assert "split it into declared Knowledge Bundle sub-levels" in issue.message and "sibling files" not in issue.message


def test_root_and_code_size_findings_advise_linked_files(tmp_path):
    root = workspace(tmp_path, "Form: records/ Record Library per subject\nForm: capabilities/ Capability")
    (root / "capabilities" / "rechner").mkdir(parents=True)
    (root / "capabilities" / "rechner" / "CONTEXT.md").write_text("z" * 24_001)
    issue, = validate(root).issues
    assert "move detail into linked sibling files" in issue.message


def test_context_map_router_that_links_every_capture_has_no_size_cap(tmp_path):
    root = workspace(tmp_path, "Form: records/ Record Library per subject\nForm: analyse/ Context Map per capture")
    (root / "analyse").mkdir()
    lines = []
    for index in range(3):
        (root / "analyse" / f"capture-{index}.md").write_text("synthetic\n")
        lines.append(f"- [capture {index}](capture-{index}.md)")
    (root / "analyse" / "CONTEXT.md").write_text(f"# Captures\n\n{SECTIONS}\n\n" + "\n".join(lines) + "\n\n" + "w" * 30_000 + "\n")
    assert validate(root).valid


def test_unclosed_backtick_across_blank_lines_hides_no_form_line(tmp_path):
    root = workspace(tmp_path, "Form: records/ Record Library per subject\nForm: grundlagen/ Knowledge Bundle per topic")
    context = root / "CONTEXT.md"
    text = context.read_text()
    context.write_text(text.replace("Form: records/", "A stray ` backtick.\n\nForm: records/", 1))
    (root / "grundlagen" / "CONTEXT.md").write_text(f"# Foundations\n\n{SECTIONS}\n")
    assert validate(root).valid


def test_readme_among_instance_folders_is_not_an_entry(tmp_path):
    root = workspace(tmp_path)
    for name in ("one", "two"):
        (root / "records" / name).mkdir()
        (root / "records" / name / "source.md").write_text("synthetic\n")
    (root / "records" / "README.md").write_text("# About these records\n")
    (root / "records" / "CONTEXT.md").write_text(f"# Records\n\n{SECTIONS}\n\n[one/](one/)\n[two/](two/)\n")
    assert validate(root).valid
