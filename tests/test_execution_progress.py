"""W3/W4: one execution table, readable decisions, record stages and slot coverage."""
import pytest

from impacts_protocol import validate
from impacts_protocol.model import derive_progress
from impacts_protocol.view import selection, write
from tests.support import (
    HUMAN, committed_workspace, entry_completed, make_attempt, read_context,
    replace_context, write_context, write_vorgang,
)
from tests.test_view import render_page, text_content

STEPS = {
    'arbeitsschritt:a': {'routen': {'next': 'arbeitsschritt:b', 'stop': 'end:no'}},
    'arbeitsschritt:b': {'routen': {'yes': 'end:yes', 'back': 'arbeitsschritt:a'}},
}


@pytest.mark.parametrize('last,status,current,end,achieved', [
    ({'status': 'aktiv'}, 'aktiv', 'arbeitsschritt:a', None, None),
    ({'status': 'wartend'}, 'wartend', 'arbeitsschritt:a', None, None),
    ({'status': 'abgeschlossen', 'gewaehlte_route': 'next'}, 'zwischen', 'arbeitsschritt:b', None, None),
    ({'status': 'abgeschlossen', 'gewaehlte_route': 'stop'}, 'beendet', None, 'end:no', False),
    ({'status': 'abgebrochen'}, 'abgebrochen', None, None, False),
    ({'status': 'beendet'}, 'open', None, None, 'open'),
    ({'status': 'abgeschlossen', 'gewaehlte_route': 'missing'}, 'open', None, None, 'open'),
])
def test_core_progress_table(last, status, current, end, achieved):
    progress = derive_progress([dict(last, arbeitsschritt_ref='arbeitsschritt:a', nummer=1)], STEPS,
                               {'erreicht': ['end:yes']})
    assert (progress['status'], progress['current'], progress['ended'], progress['erreicht']) == (status, current, end, achieved)


def test_achievement_and_superseded_are_distinct():
    entry = {'arbeitsschritt_ref': 'arbeitsschritt:b', 'nummer': 1,
             'status': 'abgeschlossen', 'gewaehlte_route': 'yes'}
    assert derive_progress([entry], STEPS, {})['erreicht'] == 'open'
    assert derive_progress([entry], STEPS, {'erreicht': ['end:yes']})['erreicht'] is True
    current = dict(entry, status='aktiv')
    found = derive_progress([current], STEPS, {}, superseded=True)
    assert found['status'] == 'superseded' and found['current'] is None
    assert derive_progress([], STEPS, {})['status'] == 'open'


def prepared(tmp_path):
    root, revision = committed_workspace(tmp_path)
    attempt = make_attempt(root / 'vorgaenge/test', 'start', 1, input_bytes='source', output_bytes='result')
    entry = entry_completed('start', 1, attempt, 'weiter')
    case = write_vorgang(root, 'test', revision, [entry])
    return root, case, entry


def test_between_steps_is_valid_and_view_uses_core(tmp_path):
    root, case, _ = prepared(tmp_path)
    assert validate(root).valid
    model = selection.single_vorgang(case / 'CONTEXT.md')
    assert model['view']['status'] == 'zwischen'
    assert model['stand']['kind'] == 'next'
    assert model['stand']['nummer'] is None


@pytest.mark.parametrize('fault', [None, 'route', 'wait', 'approval', 'output'])
def test_owner_can_end_at_an_ordinary_step_but_must_record_decision(tmp_path, fault):
    root, case, entry = prepared(tmp_path)
    entry.update(status='abgebrochen', freigabe=HUMAN)
    entry.pop('gewaehlte_route')
    if fault == 'route': entry['gewaehlte_route'] = 'weiter'
    if fault == 'wait': entry['wiedereinstieg'] = {'ausloeser': 'event', 'continuation_ref': 'source'}
    if fault == 'approval': entry.pop('freigabe')
    if fault == 'output': entry.pop('geschrieben')
    replace_context(case / 'CONTEXT.md', dict(read_context(case / 'CONTEXT.md'), laufpfad=[entry]))
    assert validate(root).valid is (fault is None)
    if fault is None:
        model = selection.single_vorgang(case / 'CONTEXT.md')
        assert model['view']['status'] == 'abgebrochen'
        assert model['stand']['kind'] == 'stopped' and model['stand']['erreicht'] is False
        for language, label in [('en', 'Stopped by owner'), ('de', 'Durch Eigentümer abgebrochen')]:
            model['language'] = language
            assert label in text_content(render_page(tmp_path, write.page_html(model))['head'])


def test_retired_stufen_is_rejected(tmp_path):
    root, _, _ = prepared(tmp_path)
    hp = root / 'hauptprozesse/video/CONTEXT.md'
    replace_context(hp, dict(read_context(hp), stufen={'stand:short-listed': 10}))
    assert any(i.code == 'schema.invalid' and 'stufen' in i.message for i in validate(root).issues)


@pytest.mark.parametrize('fault', ['uncovered', 'unknown'])
def test_completed_input_slot_coverage_rejects_gaps(tmp_path, fault):
    root, case, entry = prepared(tmp_path)
    entry['gelesen'][0]['eingabe'] = 'input/unknown.md' if fault == 'unknown' else 'input/auftrag.md'
    if fault == 'uncovered':
        entry['gelesen'][0].pop('eingabe')
    replace_context(case / 'CONTEXT.md', dict(read_context(case / 'CONTEXT.md'), laufpfad=[entry]))
    assert 'binding.reference_missing' in {i.code for i in validate(root).issues}


@pytest.mark.parametrize('body,expected', [('Stage: submitted\n', 'submitted'),
    ('Stage: submitted\nStage: awarded\n', 'open'), ('Outcome: awarded\n', 'open')])
def test_view_reads_subject_stage_without_inference(tmp_path, body, expected):
    root, case, _ = prepared(tmp_path)
    record = root / 'records/lot.md'
    record.write_text('Identity: lot-A\n' + body)
    meta = read_context(case / 'CONTEXT.md')
    write_context(case / 'CONTEXT.md', meta, '## Subject\n\n[Lot](../../records/lot.md)\n')
    model = selection.single_vorgang(case / 'CONTEXT.md')
    assert model['stand']['stufe'] == expected
    assert model['view']['status'] == 'zwischen'


def test_table_row_is_a_subject_record(tmp_path):
    root, case, _ = prepared(tmp_path)
    (root / 'records/lots.md').write_text('| Identity | Stage | Decisions |\n|---|---|---|\n| <a id="A"></a>lot-A | short-listed | selection-11 |\n')
    write_context(case / 'CONTEXT.md', read_context(case / 'CONTEXT.md'), '## Subject\n\n[Lot](../../records/lots.md#A)\n')
    assert selection.single_vorgang(case / 'CONTEXT.md')['stand']['stufe'] == 'short-listed'


@pytest.mark.parametrize('successor_kind', ['judged', 'not-judged', 'invalid'])
def test_only_a_judged_successor_supersedes(tmp_path, successor_kind):
    from tests.support import entry_active
    root, case, _ = prepared(tmp_path)
    revision = read_context(case / 'CONTEXT.md')['hauptprozess_revision'].removeprefix('git-tree:')
    attempt = make_attempt(root / 'vorgaenge/restart', 'pruefen', 1, input_bytes='source')
    successor = write_vorgang(root, 'restart', revision, [entry_active('pruefen', 1, attempt)])
    meta = read_context(successor / 'CONTEXT.md')
    meta['vorgaenger'] = 'vorgaenge/test/CONTEXT.md'
    if successor_kind == 'not-judged': meta['protocol'] = 'v0.3.31'
    if successor_kind == 'invalid': meta['laufpfad'][0]['gelesen'] = []
    replace_context(successor / 'CONTEXT.md', meta)
    model = selection.single_vorgang(case / 'CONTEXT.md')
    assert model['stand']['kind'] == ('superseded' if successor_kind == 'judged' else 'next')


def test_one_subject_crosses_offer_and_study_without_an_award_gate(tmp_path):
    from impacts_protocol import file_references, init_workspace
    from tests.support import git
    root = init_workspace(tmp_path / 'chain')
    record = root / 'records/lots/A/CONTEXT.md'
    record.parent.mkdir(parents=True)
    record.write_text('Identity: lot-A\nStage: awarded\nVorgänge: offer-A, study-A\nCommitments: study order citing award.md\nDecisions: [selection-11](../../decisions/selection-11.md)\nOutcome: award.md, received 2026-11-11, synthetic\n')
    (root / 'records/lots/kind.md').write_text('Identity rule: issuer and lot ID. Stage words: short-listed, offered, awarded, studied.\n')
    decision = root / 'records/decisions/selection-11.md'
    decision.parent.mkdir(parents=True)
    decision.write_text('Synthetic selection-11. Customer, 2026-11-10: yes for lots A and B, no for C. Cites round-11 line A.\n')
    for identity in ('B', 'C'):
        other = root / f'records/lots/{identity}/CONTEXT.md'
        other.parent.mkdir(parents=True)
        other.write_text(f'Identity: lot-{identity}\nStage: short-listed\nDecisions: [selection-11](../../decisions/selection-11.md)\n')
    assert not (root / 'records/lots/D').exists()
    round_record = root / 'records/rounds/round-11.md'
    round_record.parent.mkdir(parents=True)
    preferences = root / 'records/preferences.md'
    preferences.write_text('Synthetic selection rule.\n')
    import hashlib
    round_record.write_text('Synthetic code run, 2026-11-10. Candidates A, B, C and rejected D. Sent lines: A, B, C.\n'
                            'Input: records/preferences.md; sha256:' + hashlib.sha256(preferences.read_bytes()).hexdigest() + '\n')
    award = root / 'records/lots/A/award.md'
    award.write_text('Synthetic received award from outside buyer for lot A, 2026-11-11.\n')
    for name, slots in [('offer', ['records/rounds/round-11.md', 'records/decisions/selection-11.md']),
                        ('study', ['material/offer.md', 'records/lots/A/award.md'])]:
        hp = root / 'hauptprozesse' / name
        write_context(hp / 'CONTEXT.md', {'type': 'hauptprozess', 'id': f'hauptprozess:{name}',
            'leistung': {'ergebnis': name, 'kennzahl': 'lead time', 'abnahme': ['checked delivery'], 'erreicht': ['end:delivered']},
            'einstieg_ref': 'arbeitsschritt:deliver'}, '# Synthetic ' + name)
        write_context(hp / 'work/CONTEXT.md', {'type': 'teilprozess', 'id': 'teilprozess:work', 'ergebnis': name})
        write_context(hp / 'work/deliver/CONTEXT.md', {'type': 'arbeitsschritt', 'id': 'arbeitsschritt:deliver',
            'eingaben': slots, 'ausgaben': ['output/result.md'], 'pruefung': 'delivery checked', 'routen': {'done': 'end:delivered'}},
            'Auslöser: customer yes citing round line A.' if name == 'offer' else 'Auslöser: received award; bind delivered offer and award source.')
    git(root, 'init', '-b', 'main')
    git(root, '-c', 'user.name=Fixture', '-c', 'user.email=fixture@example.invalid', 'add', '.')
    git(root, '-c', 'user.name=Fixture', '-c', 'user.email=fixture@example.invalid', 'commit', '-qm', 'Synthetic chain')
    commit = 'git-commit:' + git(root, 'rev-parse', 'HEAD')
    def source(path): return dict(file_references(root, [path])[0], revision=commit)
    outputs = {}
    for name, inputs in [('offer', [source('records/rounds/round-11.md'), source('records/decisions/selection-11.md')]),
                         ('study', None)]:
        if inputs is None:
            inputs = [dict(outputs['offer'], eingabe='material/offer.md'), source('records/lots/A/award.md')]
        result = root / f'vorgaenge/{name}-a/deliver/001/output/result.md'
        result.parent.mkdir(parents=True)
        result.write_text('Synthetic checked ' + name + ' delivery.\n')
        outputs[name] = file_references(root, [result.relative_to(root).as_posix()])[0]
        revision = git(root, 'rev-parse', f'HEAD:hauptprozesse/{name}')
        case = write_vorgang(root, name + '-a', revision, [{'arbeitsschritt_ref': 'arbeitsschritt:deliver', 'nummer': 1,
            'status': 'abgeschlossen', 'gelesen': inputs, 'geschrieben': [outputs[name]], 'gewaehlte_route': 'done'}])
        write_context(case / 'CONTEXT.md', read_context(case / 'CONTEXT.md'), '## Subject\n\n[Lot A](../../records/lots/A/CONTEXT.md)\n')
    assert validate(root).valid, validate(root).issues
    for name in ('offer', 'study'):
        model = selection.single_vorgang(root / f'vorgaenge/{name}-a/CONTEXT.md')
        assert model['stand']['stufe'] == 'awarded'
        assert model['stand']['erreicht'] is True


@pytest.mark.parametrize('gate', [False, True])
def test_owner_end_does_not_require_unfinished_job_outputs(tmp_path, gate):
    from impacts_protocol import file_references
    from tests.support import entry_active
    root, case, previous = prepared(tmp_path)
    if gate:
        attempt = make_attempt(case, 'pruefen', 1, input_bytes='review packet')
        entry = entry_active('pruefen', 1, attempt)
        entries = [previous, entry]
    else:
        attempt = case / 'start/001'
        (attempt / 'output/ergebnis.md').unlink()
        entry = previous
        entry.pop('gewaehlte_route')
        entries = [entry]
    decision = attempt / 'output/owner-decision.md'
    decision.write_text('Synthetic owner decision: discontinue the current obligation before completing this job.\n')
    entry.update(status='abgebrochen', freigabe=HUMAN,
                 geschrieben=file_references(root, [decision.relative_to(root).as_posix()]))
    replace_context(case / 'CONTEXT.md', dict(read_context(case / 'CONTEXT.md'), laufpfad=entries))
    assert validate(root).valid, validate(root).issues
