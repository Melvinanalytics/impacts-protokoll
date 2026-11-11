"""W1 A+N+F: synthetic execution and byte-binding counterexamples."""
import hashlib

import pytest

from impacts_protocol import file_references, validate
from tests.support import (
    HUMAN, committed_workspace, entry_active, entry_completed, git, make_attempt,
    read_context, replace_context, write_vorgang, write_workstep,
)


def issue_codes(root):
    return {issue.code for issue in validate(root).issues}


def pair(tmp_path):
    root, revision = committed_workspace(tmp_path)
    case = root / 'vorgaenge/test'
    first = make_attempt(case, 'start', 1, input_bytes='source', output_bytes='result')
    second = make_attempt(case, 'pruefen', 1, input_bytes='review')
    a = entry_completed('start', 1, first, 'weiter')
    b = entry_active('pruefen', 1, second)
    b['gelesen'] = [dict(ref, eingabe='input/auftrag.md') for ref in file_references(root, ['vorgaenge/test/start/001/output/ergebnis.md'])]
    write_vorgang(root, 'test', revision, [a, b])
    return root, case, a, b


def test_successor_references_completed_output_without_copy(tmp_path):
    root, case, _, _ = pair(tmp_path)
    assert validate(root).valid
    assert [p.name for p in (case / 'pruefen/001').iterdir()] == ['output']
    assert not list(case.glob('*/*/input'))


@pytest.mark.parametrize('mutation,code', [('tamper', 'binding.reference_digest'), ('remove', 'binding.reference_missing')])
def test_referenced_working_tree_file_must_match(tmp_path, mutation, code):
    root, case, _, _ = pair(tmp_path)
    path = case / 'start/001/output/ergebnis.md'
    if mutation == 'tamper':
        path.write_text('changed')
    else:
        path.unlink()
    assert code in issue_codes(root)


def test_versioned_source_reads_recorded_blob_after_edit_or_removal(tmp_path):
    root, _, a, _ = pair(tmp_path)
    reference = a['gelesen'][0]
    path = root / reference['pfad']
    path.write_text('later revision')
    assert validate(root).valid
    path.unlink()
    assert validate(root).valid


def test_commit_without_reference_path_is_rejected(tmp_path):
    root, case, a, b = pair(tmp_path)
    a['gelesen'][0]['pfad'] = 'grundlagen/absent.md'
    replace_context(case / 'CONTEXT.md', dict(read_context(case / 'CONTEXT.md'), laufpfad=[a, b]))
    assert 'binding.reference_missing' in issue_codes(root)


def test_attempt_rejects_input_directory(tmp_path):
    root, case, _, _ = pair(tmp_path)
    (case / 'pruefen/001/input').mkdir()
    assert 'structure.attempt_child' in issue_codes(root)


@pytest.mark.parametrize('numbers,expected', [([1, 3], 'execution.attempt_sequence'), ([1, 1], 'execution.attempt_duplicate'), ([2], 'execution.attempt_sequence')])
def test_attempt_sequence(tmp_path, numbers, expected):
    root, revision = committed_workspace(tmp_path)
    write_workstep(root / 'hauptprozesse/video/produktion', 'start', routes={'again': 'arbeitsschritt:start', 'end': 'end:done', 'review': 'arbeitsschritt:pruefen'})
    git(root, 'add', 'hauptprozesse')
    git(root, 'commit', '-qm', 'Synthetic loop')
    revision = git(root, 'rev-parse', 'HEAD:hauptprozesse/video')
    entries = []
    case = root / 'vorgaenge/sequence'
    for index, number in enumerate(numbers):
        path = make_attempt(case, 'start', number, input_bytes='source', output_bytes='result')
        entry = entry_completed('start', number, path, 'again') if index < len(numbers)-1 else entry_active('start', number, path)
        entries.append(entry)
    write_vorgang(root, 'sequence', revision, entries)
    assert expected in issue_codes(root)
    if expected == 'execution.attempt_duplicate':
        assert sum(i.code == expected for i in validate(root).issues) == 1
        assert 'execution.attempt_sequence' not in issue_codes(root)


def test_attempt_999_accepted_and_1000_rejected(tmp_path):
    root, revision = committed_workspace(tmp_path)
    write_workstep(root / 'hauptprozesse/video/produktion', 'start', routes={'again': 'arbeitsschritt:start', 'end': 'end:done', 'review': 'arbeitsschritt:pruefen'})
    git(root, 'add', 'hauptprozesse')
    git(root, 'commit', '-qm', 'Synthetic loop')
    revision = git(root, 'rev-parse', 'HEAD:hauptprozesse/video')
    case = root / 'vorgaenge/limit'
    entries = []
    for number in range(1, 1000):
        path = case / 'start' / f'{number:03}' / 'output/ergebnis.md'
        path.parent.mkdir(parents=True)
        path.write_bytes(b'fixed')
        entries.append({'arbeitsschritt_ref': 'arbeitsschritt:start', 'nummer': number,
                        'status': 'abgeschlossen', 'gewaehlte_route': 'again' if number < 999 else 'end',
                        'gelesen': [{'eingabe': 'input/auftrag.md', 'ablage': 'synthetic-store', 'schluessel': 'key', 'sha256': 'sha256:'+'0'*64}],
                        'geschrieben': file_references(root, [path.relative_to(root).as_posix()])})
    write_vorgang(root, 'limit', revision, entries)
    assert validate(root).valid, validate(root).issues
    entries[-1]['gewaehlte_route'] = 'again'
    entries.append(dict(entries[-1], nummer=1000, status='aktiv'))
    entries[-1].pop('gewaehlte_route')
    entries[-1].pop('geschrieben')
    write_vorgang(root, 'limit', revision, entries)
    assert 'execution.attempt_limit' in issue_codes(root)


@pytest.mark.parametrize('start,predecessor,valid', [('pruefen', True, True), ('start', True, True), ('pruefen', False, False)])
def test_predecessor_start_including_not_judged_legacy(tmp_path, start, predecessor, valid):
    root, revision = committed_workspace(tmp_path)
    old = root / 'vorgaenge/old/CONTEXT.md'
    from tests.support import write_context
    write_context(old, {'type': 'vorgang', 'protocol': 'v0.3.31', 'laufpfad': [
        {'arbeitsschritt_ref': 'arbeitsschritt:pruefen', 'versuch': 1, 'status': 'wartend', 'eingabe_hash': 'legacy'}]})
    case = root / 'vorgaenge/new'
    path = make_attempt(case, start, 1, input_bytes='source')
    write_vorgang(root, 'new', revision, [entry_active(start, 1, path)])
    if predecessor:
        meta = read_context(case / 'CONTEXT.md')
        meta['vorgaenger'] = 'vorgaenge/old/CONTEXT.md'
        replace_context(case / 'CONTEXT.md', meta)
    assert validate(root).valid is valid
    assert len(validate(root).not_judged) == 1


@pytest.mark.parametrize('value', ['vorgaenge/absent/CONTEXT.md', 'vorgaenge/new/CONTEXT.md', '../outside/CONTEXT.md'])
def test_predecessor_path_must_resolve_to_another_vorgang(tmp_path, value):
    root, case, _, _ = pair(tmp_path)
    meta = read_context(case / 'CONTEXT.md')
    meta['vorgaenger'] = value.replace('/new/', '/test/')
    replace_context(case / 'CONTEXT.md', meta)
    assert not validate(root).valid


def test_open_producer_cannot_supply_a_reference_even_with_correct_digest(tmp_path):
    root, case, a, b = pair(tmp_path)
    a['status'] = 'aktiv'
    a.pop('geschrieben')
    a.pop('gewaehlte_route')
    replace_context(case / 'CONTEXT.md', dict(read_context(case / 'CONTEXT.md'), laufpfad=[a, b]))
    assert 'binding.reference_missing' in issue_codes(root)


def test_reference_from_a_completed_predecessor_vorgang_needs_no_copy(tmp_path):
    root, case, a, b = pair(tmp_path)
    meta = read_context(case / 'CONTEXT.md')
    write_vorgang(root, 'consumer', meta['hauptprozess_revision'].removeprefix('git-tree:'),
                  [dict(a, nummer=1, status='aktiv', gelesen=b['gelesen'])])
    consumer = root / 'vorgaenge/consumer'
    updated = read_context(consumer / 'CONTEXT.md')
    updated['laufpfad'][0].pop('geschrieben')
    updated['laufpfad'][0].pop('gewaehlte_route')
    (consumer / 'start/001/output').mkdir(parents=True)
    replace_context(consumer / 'CONTEXT.md', updated)
    assert validate(root).valid
    assert not list(consumer.glob('*/*/input'))


@pytest.mark.parametrize('key', ['unknown-key', 'opaque\0key', 'x' * 256])
def test_external_store_reference_is_shape_only(tmp_path, key):
    root, case, a, b = pair(tmp_path)
    a['gelesen'] = [{'eingabe': 'input/auftrag.md', 'ablage': 'unavailable-synthetic-store', 'schluessel': key, 'sha256': 'sha256:'+'f'*64}]
    replace_context(case / 'CONTEXT.md', dict(read_context(case / 'CONTEXT.md'), laufpfad=[a, b]))
    assert validate(root).valid
    a['gelesen'][0].pop('schluessel')
    replace_context(case / 'CONTEXT.md', dict(read_context(case / 'CONTEXT.md'), laufpfad=[a, b]))
    assert 'schema.invalid' in issue_codes(root)


@pytest.mark.parametrize('source', ['tracked', 'untracked', 'normalized'])
def test_external_store_key_cannot_name_a_working_tree_file(tmp_path, source):
    root, case, a, b = pair(tmp_path)
    key = a['gelesen'][0]['pfad']
    if source != 'tracked':
        key = 'grundlagen/uncommitted.md'
        (root / key).parent.mkdir(parents=True, exist_ok=True)
        (root / key).write_text('Synthetic uncommitted source')
    if source == 'normalized':
        key = 'grundlagen/../' + key
    a['gelesen'] = [{'eingabe': 'input/auftrag.md', 'ablage': 'synthetic-store',
                     'schluessel': key, 'sha256': 'sha256:' + 'f' * 64}]
    replace_context(case / 'CONTEXT.md', dict(read_context(case / 'CONTEXT.md'), laufpfad=[a, b]))
    report = validate(root)
    assert [i.code for i in report.issues] == ['binding.reference_missing']
    assert f'External-store key {key!r} resolves to a working-tree file' in report.issues[0].message
    assert report.external_references_not_verified == 1


def test_external_store_count_across_judged_vorgaenge_and_cli(tmp_path, capsys):
    import json
    from impacts_protocol.cli import main

    root, case, a, b = pair(tmp_path)
    reference = {'eingabe': 'input/auftrag.md', 'ablage': 'synthetic-store',
                 'schluessel': 'unknown-object', 'sha256': 'sha256:' + 'f' * 64}
    a['gelesen'] = [reference]
    replace_context(case / 'CONTEXT.md', dict(read_context(case / 'CONTEXT.md'), laufpfad=[a, b]))
    revision = read_context(case / 'CONTEXT.md')['hauptprozess_revision'].removeprefix('git-tree:')
    for name in ('current', 'legacy'):
        path = make_attempt(root / 'vorgaenge' / name, 'start', 1, input_bytes='Synthetic count source')
        entry = entry_active('start', 1, path)
        entry['gelesen'] = [reference]
        context = write_vorgang(root, name, revision, [entry]) / 'CONTEXT.md'
        if name == 'legacy':
            replace_context(context, dict(read_context(context), protocol='v0.3.32'))
    report = validate(root)
    assert report.valid, report.issues
    assert len(report.not_judged) == 1
    assert report.external_references_not_verified == 2
    assert main(['validate', str(root), '--json']) == 0
    assert json.loads(capsys.readouterr().out)['external_references_not_verified'] == 2
    assert main(['validate', str(root)]) == 0
    assert '2 references in external stores not verified by Core' in capsys.readouterr().out.splitlines()
    current = root / 'vorgaenge/current/CONTEXT.md'
    metadata = read_context(current)
    metadata.pop('protocol')
    replace_context(current, metadata)
    report = validate(root)
    assert not report.valid
    assert report.external_references_not_verified == 2
    replace_context(root / 'CONTEXT.md', {'type': 'workspace', 'protocol': 'v0.3.32'})
    assert validate(root).external_references_not_verified == 0


def test_completed_attempt_must_inventory_every_output(tmp_path):
    root, case, _, _ = pair(tmp_path)
    (case / 'start/001/output/extra.md').write_text('additional output')
    assert 'binding.reference_missing' in issue_codes(root)


@pytest.mark.parametrize('directory', ['grundlagen', 'records'])
def test_versioned_source_unicode_name_is_read_as_raw_git_path(tmp_path, directory):
    root, case, a, b = pair(tmp_path)
    relative = directory + '/quelle-ä.md'
    path = root / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(b'immutable\0binary')
    git(root, 'add', directory)
    git(root, 'commit', '-qm', 'Synthetic Unicode source')
    a['gelesen'] = [{**file_references(root, [relative])[0], 'eingabe': 'input/auftrag.md', 'revision': 'git-commit:' + git(root, 'rev-parse', 'HEAD')}]
    replace_context(case / 'CONTEXT.md', dict(read_context(case / 'CONTEXT.md'), laufpfad=[a, b]))
    assert validate(root).valid


@pytest.mark.parametrize('field,value', [('sha256', 'sha256:'+'0'*64+'\n'), ('revision', 'git-commit:'+'0'*40+'\n'), ('pfad', 'grundlagen/source.md\n')])
def test_reference_tokens_have_exact_boundaries(tmp_path, field, value):
    root, case, a, b = pair(tmp_path)
    a['gelesen'][0][field] = value
    replace_context(case / 'CONTEXT.md', dict(read_context(case / 'CONTEXT.md'), laufpfad=[a, b]))
    assert 'schema.invalid' in issue_codes(root)


@pytest.mark.parametrize('revision_key', ['hauptprozess_revision', 'application_revision'])
def test_predecessor_completed_position_uses_its_own_definition(tmp_path, revision_key):
    root, case, a, _ = pair(tmp_path)
    original = read_context(case / 'CONTEXT.md')['hauptprozess_revision']
    # Legacy predecessor ended its recorded list after start; its old route leads to pruefen.
    from tests.support import write_context
    write_context(root / 'vorgaenge/old/CONTEXT.md', {
        'type': 'vorgang', 'protocol': 'v0.3.31', revision_key: original,
        'laufpfad': [{'arbeitsschritt_ref': 'arbeitsschritt:start', 'versuch': 1,
                     'status': 'abgeschlossen', 'gewaehlte_route': 'weiter', 'eingabe_hash': 'legacy'}]})
    # A later definition gives the same route key another target.
    path = root / 'hauptprozesse/video/produktion/start/CONTEXT.md'
    meta = read_context(path)
    meta['routen'] = {'weiter': 'arbeitsschritt:start', 'review': 'arbeitsschritt:pruefen'}
    replace_context(path, meta)
    git(root, 'add', 'hauptprozesse')
    git(root, 'commit', '-qm', 'Synthetic changed route')
    revision = git(root, 'rev-parse', 'HEAD:hauptprozesse/video')
    target = root / 'vorgaenge/new'
    attempt = make_attempt(target, 'pruefen', 1, input_bytes='source')
    write_vorgang(root, 'new', revision, [entry_active('pruefen', 1, attempt)])
    meta = read_context(target / 'CONTEXT.md')
    meta['vorgaenger'] = 'vorgaenge/old/CONTEXT.md'
    replace_context(target / 'CONTEXT.md', meta)
    assert validate(root).valid, validate(root).issues


def test_quellen_is_an_ordinary_attempt_step(tmp_path):
    root, revision = committed_workspace(tmp_path)
    app = root / 'hauptprozesse/video'
    write_workstep(app / 'produktion', 'quellen', routes={'next': 'arbeitsschritt:start'})
    hp = read_context(app / 'CONTEXT.md')
    hp['einstieg_ref'] = 'arbeitsschritt:quellen'
    replace_context(app / 'CONTEXT.md', hp)
    git(root, 'add', 'hauptprozesse')
    git(root, 'commit', '-qm', 'Synthetic reserved-name collision')
    revision = git(root, 'rev-parse', 'HEAD:hauptprozesse/video')
    case = root / 'vorgaenge/collision'
    attempt = make_attempt(case, 'quellen', 1, input_bytes='source')
    write_vorgang(root, 'collision', revision, [entry_active('quellen', 1, attempt)])
    assert validate(root).valid, validate(root).issues
    draft = attempt / 'output/draft.md'
    draft.write_text('Synthetic open output of ordinary quellen step')
    git(root, 'add', 'vorgaenge/collision/quellen/001/output')
    git(root, 'commit', '-qm', 'Synthetic committed quellen draft')
    meta = read_context(case / 'CONTEXT.md')
    meta['laufpfad'][0]['gelesen'] = [{
        **file_references(root, [draft.relative_to(root).as_posix()])[0],
        'eingabe': 'input/auftrag.md', 'revision': 'git-commit:' + git(root, 'rev-parse', 'HEAD')}]
    replace_context(case / 'CONTEXT.md', meta)
    assert 'binding.reference_missing' in issue_codes(root)


def test_commit_anchor_cannot_disguise_an_open_attempt_output_as_a_source(tmp_path):
    root, case, a, b = pair(tmp_path)
    git(root, 'add', 'vorgaenge/test/start/001/output')
    git(root, 'commit', '-qm', 'Synthetic committed draft')
    a['status'] = 'aktiv'
    a.pop('geschrieben')
    a.pop('gewaehlte_route')
    b['gelesen'][0]['revision'] = 'git-commit:' + git(root, 'rev-parse', 'HEAD')
    replace_context(case / 'CONTEXT.md', dict(read_context(case / 'CONTEXT.md'), laufpfad=[a, b]))
    assert 'binding.reference_missing' in issue_codes(root)


def test_reference_to_fifo_is_rejected_without_opening_it(tmp_path):
    import os
    if not hasattr(os, 'mkfifo'):
        pytest.skip('FIFO creation requires POSIX')
    root, case, _, _ = pair(tmp_path)
    path = case / 'start/001/output/ergebnis.md'
    path.unlink()
    os.mkfifo(path)
    assert 'binding.reference_missing' in issue_codes(root)


def test_declared_inputs_require_a_nonempty_recorded_reference_list(tmp_path):
    root, case, a, b = pair(tmp_path)
    a['gelesen'] = []
    replace_context(case / 'CONTEXT.md', dict(read_context(case / 'CONTEXT.md'), laufpfad=[a, b]))
    report = validate(root)
    assert [(i.code, 'minItems: 1' in i.message) for i in report.issues] == [('schema.invalid', True)]


@pytest.mark.parametrize('child', ['_cache', '_other', '_quellen-backup'])
def test_other_underscore_prefixed_vorgang_children_are_rejected(tmp_path, child):
    root, case, _, _ = pair(tmp_path)
    (case / child).mkdir()
    assert any(i.code == 'execution.attempt' and 'underscore-prefixed' in i.message for i in validate(root).issues)


def test_predecessor_last_step_must_exist_in_successor_definition(tmp_path):
    from tests.support import write_context
    root, case, _, _ = pair(tmp_path)
    write_context(root / 'vorgaenge/old/CONTEXT.md', {
        'type': 'vorgang', 'protocol': 'v0.3.31',
        'laufpfad': [{'arbeitsschritt_ref': 'arbeitsschritt:absent', 'status': 'aktiv'}]})
    meta = read_context(case / 'CONTEXT.md')
    meta['vorgaenger'] = 'vorgaenge/old/CONTEXT.md'
    replace_context(case / 'CONTEXT.md', meta)
    assert any('Predecessor position is outside' in i.message for i in validate(root).issues)


def test_capture_home_is_flat(tmp_path):
    root, case, _, _ = pair(tmp_path)
    (case / '_quellen/start/001').mkdir(parents=True)
    assert any(i.code == 'execution.attempt' and '_quellen must be flat' in i.message for i in validate(root).issues)
