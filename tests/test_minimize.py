"""WP19 executable counterexamples to the ordered Minimize prose rule.

Rule: 02_protocol/impacts-method.md#minimize. Capture contract:
02_protocol/impacts-architect/templates/ist-prozess.md. These synthetic answers
establish only projection behavior, never permission to remove work.
"""
from copy import deepcopy
from pathlib import Path

import pytest

from impacts_protocol.view import blocks, project, selection, write
from tests.test_view import render_page, text_content

ROOT = Path(__file__).resolve().parents[1]


def capture(work='Yes', coordination='No', failure='No', duplicate='No', excess='No',
            basis='Recipient acceptance', proposal='Keep'):
    row = {'answers': [project.answer(blocks.spans(a)) for a in (work, coordination, failure, duplicate, excess)],
           'serves': {'ids': ['C1'], 'unknown': []}, 'move': {'spans': blocks.spans(proposal)}}
    conditions = {'C1': {'status': 'found', 'cells': [blocks.spans('Condition'), blocks.spans(basis), []]}}
    return row, conditions


CASES = [
    {'failure': 'Yes'},
    {'duplicate': 'Yes'},
    {'work': 'No'},
    {'coordination': 'Yes, today only'},
    {'basis': 'Own rule, open'},
    {'excess': 'Yes'},
    {'coordination': 'Yes, required'},
    {},
]


def test_function_is_pinned_to_every_row_of_the_prose_table():
    prose = (ROOT / '02_protocol/impacts-method.md').read_text().split('## Minimize\n', 1)[1]
    table = prose.split('| Answers |', 1)[1].split('\n\n', 1)[0]
    assert tuple(line.split('|')[1].strip() for line in table.splitlines()[2:]) == project.MINIMIZE_ROWS
    for number, line in enumerate(table.splitlines()[2:], 1):
        move = line.split('|')[2].strip()
        name = project._prefix(move, {key: key for key in sorted(project.MOVE_NAMES, key=len, reverse=True)})
        assert number in project.MOVE_NAMES[name]
    for number, kwargs in enumerate(CASES, 1):
        move = table.splitlines()[number + 1].split('|')[2].strip()
        row, conditions = capture(**kwargs, proposal=move)
        assert project.minimize(row, conditions) == {'row': number, 'reason': None, 'mismatch': False}


@pytest.mark.parametrize('later', range(1, 8))
def test_order_respected_when_multiple_rows_apply(later):
    # Add an earlier failure to each otherwise reachable later row.
    row, conditions = capture(**{**CASES[later], 'failure': 'Yes'})
    assert project.minimize(row, conditions)['row'] == 1
    row['answers'][2] = project.answer(blocks.spans('No'))
    row['answers'][3] = project.answer(blocks.spans('Yes'))
    assert project.minimize(row, conditions)['row'] == 2


@pytest.mark.parametrize(('kwargs', 'blocked'), [
    ({'failure': 'Open', 'duplicate': 'Yes'}, 1),
    ({'duplicate': 'Open'}, 2),
    ({'work': 'Open'}, 3),
    ({'coordination': 'Yes', 'excess': 'Yes'}, 4),
    ({'basis': 'Own rule; owner undecided', 'excess': 'Yes'}, 5),
    ({'excess': 'Open', 'coordination': 'Yes, required'}, 6),
])
def test_unknown_earlier_premise_never_falls_through(kwargs, blocked):
    row, conditions = capture(**kwargs)
    actual = project.minimize(row, conditions)
    assert actual['row'] is None
    assert actual['reason'] == project.MINIMIZE_ROWS[blocked - 1]
    assert not actual['mismatch']



@pytest.mark.parametrize(('kwargs', 'expected'), [
    ({'coordination': 'Yes, today only', 'basis': 'Own rule, open', 'excess': 'Yes'}, 4),
    ({'coordination': 'Yes, required', 'basis': 'Own rule, open', 'excess': 'Yes'}, 5),
    ({'coordination': 'Yes, required', 'excess': 'Yes'}, 6),
    ({'coordination': 'Yes, required'}, 7),
])
def test_later_row_precedence(kwargs, expected):
    row, conditions = capture(**kwargs)
    assert project.minimize(row, conditions)['row'] == expected

def test_conditions_missing_ambiguous_or_unknown_block_at_row_five():
    row, conditions = capture()
    for status in ['ambiguous', 'missing']:
        changed = deepcopy(conditions)
        changed['C1']['status'] = status
        assert project.minimize(row, changed)['reason'] == project.MINIMIZE_ROWS[4]
    row['serves']['ids'] = []
    assert project.minimize(row, {})['row'] is None
    row['serves'].update(ids=['C1'], unknown=['C2'])
    assert project.minimize(row, conditions)['row'] is None


def test_owner_confirmation_and_german_prefixes():
    row, conditions = capture(basis='Own rule, confirmed')
    assert project.minimize(row, conditions)['row'] == 8
    row, conditions = capture(work='Ja', coordination='Ja, erforderlich', failure='Nein',
                              duplicate='Nein', excess='Nein', basis='Eigene Regel, offen')
    assert project.minimize(row, conditions)['row'] == 5
    conditions['C1']['cells'][1] = blocks.spans('Eigene Regel, bestätigt')
    assert project.minimize(row, conditions)['row'] == 7
    row['answers'][1] = project.answer(blocks.spans('Ja, nur heute'))
    assert project.minimize(row, conditions)['row'] == 4


def test_mismatches_compare_move_names_without_guessing_free_prose():
    for proposal, mismatch in [('Correct the earlier contribution', True), ('Behalten', False),
                               ('Keep', False), ('Trim the output', True), ('Remove', True),
                               ('Some different wording', False), ('Minimize row 1', False), ('Minimize Zeile 1', False)]:
        row, conditions = capture(proposal=proposal)
        assert project.minimize(row, conditions)['mismatch'] is mismatch


def test_projection_and_actual_page_display_mismatch_and_unknown(tmp_path):
    template = (ROOT / '02_protocol/impacts-architect/templates/ist-prozess.md').read_text()
    template = template.replace('Remove the separation: intake writes the case record directly',
                                'Keep: intake writes the case record directly')
    path = tmp_path / 'capture.md'
    path.write_text(template)
    model = selection.ist_page(path, 'capture.md')
    # Legacy free text cannot be inferred as a required/today-only separation.
    assert model['necessity']['rows'][0]['minimize']['row'] is None
    sheet = render_page(tmp_path, write.page_html({**model, 'language': 'en'}))['sheet']
    assert 'Not computable:' in text_content(sheet)
    path.write_text(template.replace('Yes; separated only by the email channel', 'Yes, today only; separated only by the email channel'))
    model = selection.ist_page(path, 'capture.md')
    assert model['necessity']['rows'][0]['minimize'] == {'row': 4, 'reason': None, 'mismatch': True}
    sheet = render_page(tmp_path, write.page_html({**model, 'language': 'en'}))['sheet']
    assert 'Minimize row 4 · Proposal differs' in text_content(sheet)




def test_move_name_specificity_and_keep_ambiguity():
    for proposal, mismatch in [('Remove the separation', False), ('Remove', True), ('Keep', True)]:
        row, conditions = capture(coordination='Yes, today only', proposal=proposal)
        assert project.minimize(row, conditions)['mismatch'] is mismatch
    for proposal in ['Keep', 'Behalten']:
        for kwargs in [CASES[1], CASES[6], CASES[7]]:
            row, conditions = capture(**kwargs, proposal=proposal)
            assert not project.minimize(row, conditions)['mismatch']

def test_open_evidence_blocks_but_irrelevant_unknown_does_not():
    row, conditions = capture(failure='Yes (`open`)', duplicate='Yes')
    assert project.minimize(row, conditions)['reason'] == project.MINIMIZE_ROWS[0]
    row, conditions = capture(work='Open', coordination='Yes, today only')
    assert project.minimize(row, conditions)['row'] == 4
    row, conditions = capture(work='Yes', coordination='Open')
    assert project.minimize(row, conditions)['reason'] == project.MINIMIZE_ROWS[3]

def test_source_kind_is_declared_not_inferred_and_values_match_authority():
    prose = (ROOT / '02_protocol/impacts-architect/references/formwahl.md').read_text().split('| Data kind |', 1)[1]
    rows = prose.split('\n\n', 1)[0].splitlines()[2:]
    assert {line.split('|')[1].strip() for line in rows} == project.DATA_KINDS
    node = {'sections': blocks.document('## Inputs\n- Quell-Eingabe: `records/in.md`\n- Datenart: `Received source`\n', 1)[2]}
    assert project.source_kinds(node) == [{'input': 'records/in.md', 'kind': 'Received source'}]
    node = {'sections': blocks.document('## Inputs\n- Datenart: `invented`\n', 1)[2]}
    assert project.source_kinds(node) == [{'input': None, 'kind': None}]


def test_generated_source_requirement_blocks_carry_the_kind():
    for language in ('', 'de/'):
        template = (ROOT / '02_protocol/templates' / language / 'arbeitsschritt.md').read_text()
        sections = blocks.document(template.split('---', 2)[2], 1)[2]
        assert project.source_kinds({'sections': sections})[0]['kind'] == 'Foundations'


@pytest.mark.parametrize('name', project.MOVE_NAMES)
def test_every_move_prefix_is_taught_and_compares_the_proposal(name):
    sources = [ROOT / '02_protocol/impacts-method.md',
               ROOT / '02_protocol/impacts-architect/templates/ist-prozess.md',
               ROOT / '02_protocol/impacts-architect/templates/de/ist-prozess.md']
    moves = [line.split('|')[-3].strip().casefold()
             for path in sources for line in path.read_text().splitlines()
             if line.startswith('|') and len(line.split('|')) == 5]
    # Method rows have three cells; capture rows have eight. Only the move cell counts.
    moves += [line.split('|')[-2].strip().casefold()
              for path in sources[1:] for line in path.read_text().splitlines()
              if line.startswith('|') and len(line.split('|')) == 10]
    assert any(move.startswith(name) for move in moves), name
    for number, kwargs in enumerate(CASES, 1):
        row, conditions = capture(**kwargs, proposal=name)
        assert project.minimize(row, conditions)['mismatch'] == (number not in project.MOVE_NAMES[name])


@pytest.mark.parametrize('basis', project.BASIS)
def test_every_condition_basis_is_taught_in_capture_templates(basis):
    text = '\n'.join((ROOT / '02_protocol/impacts-architect/templates' / language / 'ist-prozess.md').read_text()
                     for language in ('', 'de'))
    assert basis in text.casefold()
