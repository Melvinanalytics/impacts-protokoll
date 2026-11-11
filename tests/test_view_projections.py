"""W5 derived projections: Core execution state and linked record stages only."""
from copy import deepcopy
import json
from pathlib import Path

from jsonschema import Draft202012Validator

from impacts_protocol.view import project, selection, write
from tests.test_view import _workspace, render_page, text_content
from tests.support import read_context, write_context


def test_execution_projection_delegates_to_core(monkeypatch):
    calls = []
    sentinel = object()

    def core(*args, **kwargs):
        calls.append((args, kwargs))
        return sentinel

    monkeypatch.setattr(project, 'derive_progress', core)
    nodes = [{'kind': 'hauptprozess', 'meta': {'leistung': {'erreicht': ['end:ok']}}},
             {'kind': 'arbeitsschritt', 'id': 'arbeitsschritt:a', 'meta': {'routen': {}}}]
    entries = [{'status': 'wartend'}]
    assert project.phases(nodes, entries, superseded=True) is sentinel
    assert calls == [((entries, {'arbeitsschritt:a': {'routen': {}}}, {'erreicht': ['end:ok']}),
                      {'superseded': True})]


def projections(tmp_path):
    root = _workspace(tmp_path)
    model = selection.single_vorgang(root / 'vorgaenge/video-001/CONTEXT.md')
    assert not model['issues']
    return root, model


def test_due_list_uses_core_wait_state_and_sorts_instants(tmp_path):
    _, base = projections(tmp_path)
    pages = {}
    for name, status, due in [('later', 'wartend', '2026-11-10T09:30:00+00:00'),
                              ('first', 'wartend', '2026-11-10T10:00:00+01:00'),
                              ('missing', 'wartend', None), ('superseded', 'superseded', None),
                              ('ended', 'beendet', None), ('stopped', 'abgebrochen', None),
                              ('between', 'zwischen', None), ('active', 'aktiv', None)]:
        m = deepcopy(base)
        # Contradictory raw status is deliberate: only Core's result selects open waits.
        m['view']['status'] = status
        m['vorgang']['meta']['laufpfad'][-1]['status'] = 'aktiv'
        m['vorgang']['meta']['laufpfad'][-1]['wiedereinstieg'] = {'faellig': due}
        pages[name] = m
    pages['refused'] = {'kind': 'vorgang', 'issues': ['bad']}
    pages['old'] = {'kind': 'vorgang', 'issues': [], 'not_judged': {'protocol': 'v0.3.32'}}
    rows = project.due_list(pages)
    assert [r['page'] for r in rows] == ['first', 'later', 'missing']
    assert rows[-1]['missing_due'] is True
    assert rows[0]['step'] == base['view']['current']


def test_step_queues_keep_revision_status_and_unopened_successor(tmp_path):
    _, base = projections(tmp_path)
    pages = {}
    for name, status in [('a', 'aktiv'), ('w', 'wartend'), ('z', 'zwischen'),
                         ('end', 'beendet'), ('stop', 'abgebrochen'), ('old', 'superseded')]:
        m = deepcopy(base)
        m['view'].update(status=status, nummer=None if status == 'zwischen' else 1)
        pages[name] = m
    other = deepcopy(pages['a'])
    other['selection']['revision'] = 'git-tree:' + 'f' * 40
    pages['other-revision'] = other
    pages['refused'] = {'kind': 'vorgang', 'issues': ['bad']}
    pages['unjudged'] = {'kind': 'vorgang', 'issues': [], 'not_judged': {'protocol': None}}
    queues = project.step_queues(pages)
    current = next(q for q in queues if q['revision'] == base['selection']['revision']
                   and q['step'] == 'arbeitsschritt:pruefen')
    assert [(r['page'], r['status'], r['nummer']) for r in current['vorgaenge']] == [
        ('a', 'aktiv', 1), ('w', 'wartend', 1), ('z', 'zwischen', None)]
    assert all(not q['vorgaenge'] for q in queues if q['step'] == 'arbeitsschritt:start')
    assert next(q for q in queues if q['revision'] == other['selection']['revision']
                and q['step'] == 'arbeitsschritt:pruefen')['vorgaenge'][0]['page'] == 'other-revision'


def test_funnel_counts_record_addresses_not_runs_or_execution(tmp_path):
    root, base = projections(tmp_path)
    path = root / 'vorgaenge/video-001/CONTEXT.md'
    record = root / 'records/lot.md'
    record.write_text('Stage: submitted\n')
    write_context(path, read_context(path), '## Subject\n\n[Lot](../../records/lot.md)\n')
    model = selection.single_vorgang(path)
    assert model['subject'] == {'record': 'records/lot.md', 'stage': 'submitted'}
    ended = deepcopy(model)
    ended['view']['status'] = 'beendet'
    second = deepcopy(model)
    second['subject'] = {'record': 'records/lot.md#second', 'stage': 'lost'}
    rows = project.funnel({'first': model, 'same': ended, 'second': second, 'unlinked': base})
    assert rows == [{'stage': 'lost', 'count': 1, 'records': ['records/lot.md#second']},
                    {'stage': 'submitted', 'count': 1, 'records': ['records/lot.md']}]
    # A stage conflict is a gap; execution success never resolves it.
    ended['subject']['stage'] = 'awarded'
    assert project.funnel({'first': model, 'same': ended})[0]['stage'] == 'open'
    record.write_text('Stage: submitted\nStage: awarded\n')
    assert selection.subject_record(path, root)['stage'] == 'open'


def test_overview_renders_views_and_gate_none_is_schema_impossible(tmp_path):
    root, _ = projections(tmp_path)
    overview = selection.workspace_site(root)['index.html']
    assert overview['step_queues'] and overview['due_list'] == []
    rendered = render_page(tmp_path, write.page_html({**overview, 'language': 'en'}))
    text = text_content(rendered['sheet'])
    assert 'Due list' in text and 'Subject stages' in text and 'Queues per Arbeitsschritt' in text
    schema = json.loads(Path('02_protocol/schemas/arbeitsschritt.schema.json').read_text())
    gate = schema['properties']['gate']
    assert gate == {'const': 'human'}
    assert 'gate' not in schema['required']
    assert Draft202012Validator(gate).is_valid('human')
    assert not Draft202012Validator(gate).is_valid('none')
    page = Path('src/impacts_protocol/view/page.html').read_text()
    assert 'gate === "none"' not in page and 'const STATUS =' not in page


def test_record_only_funnel_uses_stage_lines_and_anchored_rows(tmp_path):
    root, _ = projections(tmp_path)
    (root / 'records/unlinked.md').write_text('Stage: candidate\n')
    (root / 'records/lots.md').write_text(
        '| ID | Stage |\n|---|---|\n'
        '| <a id="A"></a> A | submitted |\n'
        '| <a id="B"></a> B | lost |\n'
        '| <a id="C"></a> C | awarded |\n'
        '| <a id="C"></a> C | awarded |\n')
    (root / 'records/ignored.md').symlink_to(root / 'records/unlinked.md')
    rows = selection.workspace_site(root)['index.html']['funnel']
    assert rows == [
        {'stage': 'candidate', 'count': 1, 'records': ['records/unlinked.md']},
        {'stage': 'lost', 'count': 1, 'records': ['records/lots.md#B']},
        {'stage': 'open', 'count': 1, 'records': ['records/lots.md#C']},
        {'stage': 'submitted', 'count': 1, 'records': ['records/lots.md#A']}]


def test_record_change_during_generation_refuses_output(tmp_path, monkeypatch):
    root, _ = projections(tmp_path)
    record = root / 'records/unlinked.md'
    record.write_text('Stage: candidate\n')
    original = selection.vorgang_page

    def changing(*args, **kwargs):
        model = original(*args, **kwargs)
        record.write_text('Stage: submitted\n')
        return model

    monkeypatch.setattr(selection, 'vorgang_page', changing)
    import pytest
    with pytest.raises(SystemExit, match='a record or HEAD changed'):
        selection.workspace_site(root)
