"""WP15: parser-labels.md inventories finite labels parsed from readable Markdown bodies.

Constants are extracted from their parser owners. Literal inventories are pinned
inside their consuming functions; generic Markdown grammar and arbitrary values
(paths, IDs, source headings supplied by callers) are not finite labels.
"""
import ast
from collections import defaultdict
import json
from pathlib import Path
import re

from impacts_protocol.view import project

ROOT = Path(__file__).resolve().parents[1]
PROJECT = 'src/impacts_protocol/view/project.py'
COLD = '06_evaluations/cold-walk/check.py'


def literal(path, name, function=None):
    tree = ast.parse((ROOT / path).read_text())
    scope = next(n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef) and n.name == function) if function else tree
    for node in ast.walk(scope):
        if isinstance(node, ast.Assign) and any(isinstance(t, ast.Name) and t.id == name for t in node.targets):
            return ast.literal_eval(node.value)
    raise AssertionError((path, function, name))


def inventory():
    found = defaultdict(set)
    def add(labels, path, function):
        for label in labels:
            found[label.casefold()].add(f'{path}:{function}')
    for names, function in [('JOB', 'step_refs'), ('AUTHORITY', 'step_refs'), ('FLOW', 'step_refs'),
                            ('PROCESSING', 'step_refs'), ('SHEET', 'sheet_parts'), ('EXECUTION', 'execution'),
                            ('LABELS', 'labels'), ('MARK', 'answer'), ('SEPARATION', 'minimize'),
                            ('BASIS', 'minimize'), ('MOVE_NAMES', 'minimize'), ('DATA_KINDS', 'source_kinds')]:
        add(getattr(project, names), PROJECT, function)
    for names in project.SUBTITLE.values():
        add(names, PROJECT, 'annotate')
    for names in project.NAMES.values():
        add(names, PROJECT, '_scopes')
    for shapes in project.HEADS.values():
        for shape in shapes:
            add(shape, PROJECT, '_shaped')
    add(project.OWNER_LABELS, PROJECT, 'step_owners')
    add([project.REMOVED], PROJECT, 'necessity')
    add(literal(COLD, 'recognized', '_fields'), COLD, '_fields')
    # Literal labels in regexes or small loops; test below checks their owning code.
    groups = [
        ("src/impacts_protocol/validator.py", "_declared_stores", ["Ablage:"]),
        (PROJECT, 'source_kinds', ['Quell-Eingabe', 'Datenart']),
        ('src/impacts_protocol/view/selection.py', 'record_stages', ['Stage']),
        (COLD, '_hauptprozess_call', ['Aufruf-ID', 'Capability-Pfad', 'Capability-Revision', 'Operation']),
        (COLD, '_hauptprozess_source', ['Quell-Eingabe', 'Herkunft', 'Ursprung', 'Stand', 'Erforderliche Kontrolle']),
        (COLD, '_check_loop_bounds', ['Loop bound']),
        (COLD, '_hauptprozess_handoff', ['Bei Route']),
        (COLD, '_execute_capability', ['Operation']),
        (COLD, 'walk', ['Befund: fehlt']),
        ('06_evaluations/cold-walk/beispiel/capabilities/vollstaendigkeitsgrad/run.py', 'calculate', ['Pflichtfelder']),
        ('06_evaluations/offer-walk/run.py', 'bound_inputs', ['Bei Route']),
    ]
    for path, function, names in groups:
        # Find literal labels even when their spelling is embedded in a regex.
        tree = ast.parse((ROOT / path).read_text())
        owner = next(n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef) and n.name == function)
        source = ast.get_source_segment((ROOT / path).read_text(), owner)
        for name in names:
            assert name in source, (path, function, name)
        add(names, path, function)
    # The page also recognizes source headings/executors and optional capture metadata.
    page_path = 'src/impacts_protocol/view/page.html'
    page = (ROOT / page_path).read_text()
    add(project.SUBJECT_HEADINGS, 'src/impacts_protocol/view/selection.py', 'subject_record')
    assert 'SUBJECT_HEADINGS' in (ROOT / 'src/impacts_protocol/view/selection.py').read_text()
    assert 'VOCABULARY.headings' in page and 'VOCABULARY.execution' in page and 'VOCABULARY.owners' in page
    add(project.PAGE_HEADINGS, page_path, 'headingText')
    add(project.EXECUTION, page_path, 'workstepSheet')
    add(project.OWNER_LABELS, page_path, 'workstepSheet')
    # Fixed placeholders in the offer blank are Markdown labels, not field inference.
    renderer = (ROOT / '06_evaluations/offer-walk/run.py').read_text().split('def fill_offer(', 1)[1].split('def open_offer(', 1)[0]
    for key in ('offer_id', 'version', 'customer_id', 'request_ref', 'positions', 'total'):
        assert key in renderer
        add(['{{' + key + '}}'], '06_evaluations/offer-walk/run.py', 'fill_offer')
    return dict(found)



def spellings():
    """Preserve exact spelling for case-sensitive interfaces, including data-kind values."""
    names = ['Ablage:', 'Quell-Eingabe', 'Datenart', 'Subject', 'Gegenstand', 'Stage', 'Aufruf-ID',
             'Capability-Pfad', 'Capability-Revision', 'Operation', 'Herkunft', 'Ursprung',
             'Stand', 'Erforderliche Kontrolle', 'Loop bound', 'Bei Route', 'Befund: fehlt',
             'Pflichtfelder']
    names += list(project.DATA_KINDS)
    names += list(literal(COLD, 'recognized', '_fields'))
    return {name.casefold(): name for name in names}

def test_every_parsed_label_has_exactly_one_table_entry_and_no_entry_is_unread():
    text = (ROOT / '02_protocol/impacts-architect/references/parser-labels.md').read_text()
    table = text.split('### Parser-consumed labels\n', 1)[1].split('\n## ', 1)[0]
    rows = re.findall(r'^\| ([^|]+) \| ([^|]+) \| ([^|]+) \| (.*?) \|$', table, re.M)
    assert len(rows) == len({meaning for meaning, _, _, _ in rows}), 'duplicate meanings'
    actual = {}
    for _, english, german, readers in rows:
        for language, cell in [('EN', english), ('DE', german)]:
            if readers.startswith('EN: '):
                english_refs, german_refs = readers[4:].split('; DE: ', 1)
                refs = english_refs if language == 'EN' else german_refs
            else:
                refs = readers
            for label in re.findall(r'`([^`]+)`', cell):
                assert label.casefold() not in actual, 'duplicate labels'
                assert label == spellings().get(label.casefold(), label.casefold())
                actual[label.casefold()] = set(re.findall(r'`([^`]+:[^`]+)`', refs))
    assert actual == inventory()
