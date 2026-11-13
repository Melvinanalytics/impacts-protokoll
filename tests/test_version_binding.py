"""Synthetic version selection: only the matching major/minor is judged."""
import json

import pytest

from impacts_protocol import validate
from impacts_protocol.cli import main
from impacts_protocol.model import NotJudged
from impacts_protocol.view import site_model
from tests.support import (
    committed_workspace, make_attempt, entry_active, read_context,
    replace_context, write_vorgang,
)


def run_fixture(tmp_path):
    root, revision = committed_workspace(tmp_path)
    attempt = make_attempt(root / 'vorgaenge' / 'old', 'start', 1, input_bytes='synthetic')
    vorgang = write_vorgang(root, 'old', revision, [entry_active('start', 1, attempt)])
    return root, revision, vorgang


@pytest.mark.parametrize('recorded,judged', [
    ('v0.5.0', True), ('v0.5.99', True), ('v0.6.0', False),
    ('v0.4.1', False), ('v1.4.0', False),
])
def test_selection_compares_major_and_minor(tmp_path, recorded, judged):
    root, _, vorgang = run_fixture(tmp_path)
    path = vorgang / 'CONTEXT.md'
    meta = read_context(path)
    meta['protocol'] = recorded
    meta['laufpfad'][0]['eingabe_hash'] = 'sha256:' + '0' * 64
    replace_context(path, meta)
    report = validate(root, release='v0.5.0')
    newer = recorded in {"v0.6.0", "v1.4.0"}
    assert bool(report.issues) is (judged or newer)
    if newer:
        assert [i.code for i in report.issues] == ["binding.revision"]
    assert bool(report.not_judged) is not judged
    if not judged:
        assert report.not_judged == (NotJudged('vorgaenge/old/CONTEXT.md', recorded, 'v0.5.0'),)


def test_legacy_skip_and_current_judgment_in_one_run(tmp_path, capsys):
    root, revision, vorgang = run_fixture(tmp_path)
    path = vorgang / 'CONTEXT.md'
    meta = read_context(path)
    del meta['protocol']
    # Presence in any item is enough, even with an unusable revision and other malformed entries.
    meta['hauptprozess_revision'] = 'old-format'
    meta['laufpfad'] = [None, {'eingabe_hash': None}]
    replace_context(path, meta)
    report = validate(root)
    assert report.valid and len(report.not_judged) == 1
    assert main(['validate', str(root)]) == 0
    assert capsys.readouterr().out == (
        'impacts validate v0.5.0 against pin v0.5.0: 1 Hauptprozesse, 1 Teilprozesse, '
        '2 Arbeitsschritte, 0 Vorgänge, 0 Versuche judged; 1 Vorgänge not judged; 0 definition trees outside hauptprozesse/\n'
        'not judged under v0.5.0: vorgaenge/old/CONTEXT.md (records none)\n'
    )
    assert main(['validate', str(root), '--json']) == 0
    assert json.loads(capsys.readouterr().out)['not_judged'] == [
        {'path': 'vorgaenge/old/CONTEXT.md', 'protocol': None}]
    attempt = make_attempt(root / 'vorgaenge' / 'current', 'start', 1, input_bytes='synthetic')
    entry = entry_active('start', 1, attempt)
    entry['eingabe_hash'] = 'sha256:' + '0' * 64
    write_vorgang(root, 'current', revision, [entry])
    report = validate(root)
    assert len(report.not_judged) == 1
    assert report.issues and all(i.path.startswith('vorgaenge/current/') for i in report.issues)
    assert main(['validate', str(root)]) == 1


def test_current_without_protocol_is_version_missing(tmp_path):
    root, _, vorgang = run_fixture(tmp_path)
    path = vorgang / 'CONTEXT.md'
    meta = read_context(path)
    del meta['protocol']
    replace_context(path, meta)
    report = validate(root)
    assert not report.not_judged
    assert [i.message for i in report.issues] == ['protocol pin missing; add protocol: v0.5.0 to the frontmatter']


@pytest.mark.parametrize('recorded', [None, 4, '', '0.4.0', 'v0.4', 'v0.4.0-rc1', 'v0.04.0', 'v0.4.0\n'])
def test_malformed_explicit_version_cannot_skip_judgment(tmp_path, recorded):
    root, _, vorgang = run_fixture(tmp_path)
    path = vorgang / 'CONTEXT.md'
    meta = read_context(path)
    meta['protocol'] = recorded
    replace_context(path, meta)
    report = validate(root)
    assert report.issues and not report.not_judged


def test_workspace_pin_required_and_well_formed(tmp_path):
    root, _, _ = run_fixture(tmp_path)
    path = root / 'CONTEXT.md'
    meta = read_context(path)
    assert meta['protocol'] == 'v0.5.0'
    del meta['protocol']
    replace_context(path, meta)
    missing = validate(root)
    assert not missing.valid
    assert [(issue.code, issue.message) for issue in missing.issues] == [('schema.invalid', 'protocol pin missing; add protocol: v0.5.0 to the frontmatter')]
    meta['protocol'] = 'v0.4'
    replace_context(path, meta)
    assert not validate(root).valid


def test_viewer_excludes_not_judged_from_valid_and_failed_counts(tmp_path):
    root, _, vorgang = run_fixture(tmp_path)
    path = vorgang / 'CONTEXT.md'
    meta = read_context(path)
    meta['protocol'] = 'v0.3.32'
    meta['hauptprozess_revision'] = 'old-format'
    replace_context(path, meta)
    pages = site_model(root)
    model = pages['v-old.html']
    assert model['not_judged']['protocol'] == 'v0.3.32'
    assert model['issues'] == [] and 'nodes' not in model
    overview = pages['index.html']
    assert overview['population']['vorgaenge_not_judged'] == 1
    assert overview['population']['vorgaenge_refused'] == 0
    assert overview['unassigned'][0]['not_judged'] == model['not_judged']


@pytest.mark.parametrize('language,label', [('en', 'not judged'), ('de', 'nicht beurteilt')])
def test_viewer_renders_not_judged_page_and_overview(tmp_path, language, label):
    from impacts_protocol.view.write import page_html
    from tests.test_view import render_page, text_content

    root, _, vorgang = run_fixture(tmp_path)
    path = vorgang / 'CONTEXT.md'
    meta = read_context(path)
    del meta['protocol']
    meta['laufpfad'][0]['eingabe_hash'] = 'legacy'
    meta['hauptprozess_revision'] = 'legacy'
    replace_context(path, meta)
    pages = site_model(root)
    for name in ['v-old.html', 'index.html']:
        html = page_html({**pages[name], 'language': language})
        text = text_content(render_page(tmp_path, html)['sheet']).lower()
        assert label in text


@pytest.mark.parametrize('pin', ['v0.3.31', 'v7.0.0'])
def test_mismatched_workspace_pin_skips_every_descendant(tmp_path, capsys, pin):
    root, _, _ = run_fixture(tmp_path)
    replace_context(root / 'CONTEXT.md', {'type': 'workspace', 'protocol': pin})
    (root / 'hauptprozesse/video/CONTEXT.md').write_text('invalid definition')
    (root / 'vorgaenge/old/CONTEXT.md').write_text('invalid Vorgang')
    report = validate(root)
    assert report.valid
    assert report.not_judged == (NotJudged('CONTEXT.md', pin, 'v0.5.0'),)
    assert main(['validate', str(root)]) == 0
    assert capsys.readouterr().out == (
        f'impacts validate v0.5.0 against pin {pin}: 0 Hauptprozesse, 0 Teilprozesse, '
        '0 Arbeitsschritte, 0 Vorgänge, 0 Versuche judged; 0 Vorgänge not judged; 0 definition trees outside hauptprozesse/; workspace not judged\n'
        f'workspace not judged under v0.5.0: pinned {pin}\n'
    )
    assert main(['validate', str(root), '--json']) == 0
    assert json.loads(capsys.readouterr().out)['not_judged'] == [{'path': 'CONTEXT.md', 'protocol': pin}]


def test_missing_workspace_pin_is_one_issue_even_with_broken_descendants(tmp_path):
    root, _, _ = run_fixture(tmp_path)
    replace_context(root / 'CONTEXT.md', {'type': 'workspace'})
    (root / 'hauptprozesse/video/CONTEXT.md').write_text('invalid definition')
    (root / 'vorgaenge/old/CONTEXT.md').write_text('invalid Vorgang')
    report = validate(root)
    assert not report.not_judged
    assert [(i.code, i.message) for i in report.issues] == [('schema.invalid', 'protocol pin missing; add protocol: v0.5.0 to the frontmatter')]


def test_previous_minor_workspace_pin_is_not_judged_even_without_form_lines(tmp_path, capsys):
    root, _, _ = run_fixture(tmp_path)
    replace_context(root / 'CONTEXT.md', {'type': 'workspace', 'protocol': 'v0.4.1'})
    (root / 'unformed').mkdir()
    (root / 'unformed/notes.md').write_text('no Form line declares this folder')
    report = validate(root)
    assert report.release == 'v0.5.0' and report.pin == 'v0.4.1'
    assert report.valid and not report.issues
    assert report.not_judged == (NotJudged('CONTEXT.md', 'v0.4.1', 'v0.5.0'),)
    assert main(['validate', str(root)]) == 0
    assert capsys.readouterr().out.endswith('workspace not judged under v0.5.0: pinned v0.4.1\n')
