"""Concrete counterexamples from the rejected v0.3.28 candidate."""
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

from impacts_protocol.view import blocks, project, read, selection, working_language, write, run
from tests.support import git, write_application
from tests.test_view import TEMPLATE_EN, TEMPLATE_DE, _ist_workspace, _workspace, elements, render_page, text_content


@pytest.mark.parametrize('tail', ['    ', '\t', '    \n    '])
def test_trailing_indented_blank_line_keeps_valid_application_readable(tmp_path, tail):
    root = write_application(tmp_path / 'video')
    path = root / 'produktion/start/CONTEXT.md'
    path.write_text(path.read_text() + '\n## Extra\n' + tail)
    from impacts_protocol.validator import validate
    assert validate(root).valid
    assert not selection.application_page(root)['issues']


def test_case_alias_output_cannot_mutate_workspace(tmp_path):
    root = _workspace(tmp_path)
    alias = root.with_name(root.name.upper())
    if not alias.exists() or not alias.samefile(root):
        pytest.skip('filesystem is case-sensitive; case alias unavailable')
    before = sorted(str(p.relative_to(root)) for p in root.rglob('*'))
    with pytest.raises(SystemExit, match='overlap'):
        write.write_site(alias / 'out1', root, {'index.html': {'language': 'de'}}, False)
    assert sorted(str(p.relative_to(root)) for p in root.rglob('*')) == before


def test_missing_output_parent_has_readable_error(tmp_path):
    source = tmp_path / 'source'; source.mkdir()
    with pytest.raises(SystemExit, match='parent'):
        write.write_site(tmp_path / 'missing/out', source, {'index.html': {}}, False)


@pytest.mark.parametrize('target', ['arbeitsschritt:start/missing', 'arbeitsschritt:start.md', 'arbeitsschritt:start_foo'])
def test_move_target_never_matches_id_prefix(target):
    assert project.TARGET.findall(target) == []
    assert project.TARGET.findall('→ arbeitsschritt:start, arbeitsschritt:pruefen.') == ['start', 'pruefen']


def test_whitespace_code_removal_marker(tmp_path):
    text = TEMPLATE_DE.read_text().replace('`entfaellt`', '`  entfaellt  `')
    root = _ist_workspace(tmp_path, {'antrag.md': text})
    rows = selection.workspace_site(root)['i-antrag.html']['necessity']['rows']
    assert any(r['move']['removed'] for r in rows)


def test_backtick_run_finishes_without_quadratic_search():
    code = "from impacts_protocol.view.blocks import spans; s='`'*32768; assert ''.join(x[1] for x in spans(s))==s"
    env = dict(os.environ, PYTHONPATH=str(Path(__file__).resolve().parents[1] / 'src'))
    result = subprocess.run([sys.executable, '-c', code], env=env, timeout=3, capture_output=True)
    assert result.returncode == 0, result.stderr.decode()


def test_workspace_language_ignores_fenced_example(tmp_path):
    (tmp_path / 'CONTEXT.md').write_text('---\ntype: workspace\n---\n\n```md\nWorking language: de\n```\n\nWorking language: en\n')
    assert working_language(tmp_path) == 'en'


def test_git_replacement_does_not_change_view_snapshot(tmp_path):
    root = _workspace(tmp_path)
    old = git(root, 'rev-parse', 'HEAD')
    path = root / 'applications/video/produktion/start/CONTEXT.md'
    path.write_text(path.read_text() + '\n## Inputs\n\nActual newer content.\n')
    git(root, 'commit', '-qam', 'new source')
    current = git(root, 'rev-parse', 'HEAD')
    before = selection.workspace_site(root)
    git(root, 'replace', current, old)
    assert selection.workspace_site(root) == before


@pytest.mark.parametrize('value', ['!!set {alpha: null, beta: null}', '&a [*a]'])
def test_non_json_metadata_is_refused_without_rendering_arbitrary_repr(tmp_path, value):
    path = tmp_path / 'ist.md'; path.write_text('---\ntype: ist-prozess\nvalue: ' + value + '\n---\n# Source\n')
    with pytest.raises(read.Unreadable):
        read.read_file(path, 'ist.md')


def test_shared_alias_collections_do_not_expand_into_large_pages(tmp_path):
    lines = ['a: &a [one, two, three]']
    for i, key in enumerate('bcdefgh', 1):
        previous = 'abcdefgh'[i-1]; lines.append(f'{key}: &{key} [*{previous}, *{previous}, *{previous}, *{previous}]')
    path = tmp_path / 'ist.md';path.write_text('---\ntype: ist-prozess\n'+'\n'.join(lines)+'\n---\n# Source\n')
    with pytest.raises(read.Unreadable):
        read.read_file(path, 'ist.md')


def test_reported_prose_retains_mockup_without_visible_evidence_word(tmp_path):
    root = write_application(tmp_path / 'video')
    path = root / 'produktion/start/CONTEXT.md'
    path.write_text(path.read_text() + '\n## Inputs\n\nSource says so (`reported`). Checked (`verified`).\n')
    model = {**selection.application_page(root), 'language': 'de'}
    sheet = render_page(tmp_path, write.page_html(model), '#arbeitsschritt:start')['sheet']
    inputs = next(e for e in elements(sheet) if e['attrs'].get('id') == 's-inputs')
    assert 'Beleg' not in text_content(inputs)
    assert 'Source says so .' in text_content(inputs) or 'Source says so.' in text_content(inputs)
    assert any(e['tagName']=='BUTTON' and e['attrs'].get('class')=='source-ref' for e in elements(inputs))


def test_application_output_cannot_add_folder_to_workspace_applications(tmp_path):
    from impacts_protocol.view import run
    root = _workspace(tmp_path)
    before = sorted(str(p.relative_to(root)) for p in root.rglob('*'))
    with pytest.raises(SystemExit, match='overlap'):
        run(root / 'applications/video', root / 'applications/out')
    assert sorted(str(p.relative_to(root)) for p in root.rglob('*')) == before


@pytest.mark.skipif(not hasattr(os, 'mkfifo'), reason='FIFO unavailable')
def test_workspace_language_skips_parent_fifo(tmp_path):
    os.mkfifo(tmp_path / 'CONTEXT.md')
    child = tmp_path / 'child'; child.mkdir()
    code = "from pathlib import Path;from impacts_protocol.view import working_language;assert working_language(Path(__import__('sys').argv[1])) is None"
    env = dict(os.environ, PYTHONPATH=str(Path(__file__).resolve().parents[1] / 'src'))
    result = subprocess.run([sys.executable, '-c', code, str(child)], env=env, timeout=3, capture_output=True)
    assert result.returncode == 0, result.stderr.decode()


@pytest.mark.parametrize('language,template,expected', [('en',TEMPLATE_EN,'reported'),('de',TEMPLATE_DE,'berichtet')])
def test_status_labels_follow_selected_language(tmp_path,language,template,expected):
 root=_ist_workspace(tmp_path,{'source.md':template.read_text()})
 model={**selection.workspace_site(root)['i-source.html'],'language':language}
 sheet=render_page(tmp_path,write.page_html(model))['sheet'];header=next(e for e in elements(sheet) if e['tagName']=='HEADER')
 assert expected in text_content(header)
 if language=='en': assert 'berichtet' not in text_content(header)

@pytest.mark.parametrize('bad',['arbeitsschritt:start/missing','arbeitsschritt:start.md'])
def test_malformed_target_is_kept_whole_in_visible_move(tmp_path,bad):
 text=TEMPLATE_DE.read_text().replace('Trennung aufheben: Eingang legt die Fallakte direkt an (`hypothesis`)', 'Proposal; '+bad)
 root=_ist_workspace(tmp_path,{'source.md':text});model={**selection.workspace_site(root)['i-source.html'],'language':'de'}
 sheet=render_page(tmp_path,write.page_html(model))['sheet'];row=next(e for e in elements(sheet) if e['attrs'].get('class')=='nrow')
 assert bad in text_content(row['children'][-1])

@pytest.mark.parametrize('value',['.nan','.inf','-.inf'])
def test_nonfinite_yaml_is_refused_before_json(tmp_path,value):
 p=tmp_path/'ist.md';p.write_text('---\ntype: ist-prozess\nvalue: '+value+'\n---\n# Source\n')
 with pytest.raises(read.Unreadable):read.read_file(p,'ist.md')

def test_finite_yaml_stays_readable(tmp_path):
 p=tmp_path/'ist.md';p.write_text('---\ntype: ist-prozess\nvalue: 1.5\n---\n# Source\n')
 assert read.read_file(p,'ist.md')['meta']['value']==1.5

@pytest.mark.parametrize('workspace',[False,True])
def test_application_without_git_preserves_declared_workspace_boundary(tmp_path,monkeypatch,workspace):
 root=_workspace(tmp_path) if workspace else write_application(tmp_path/'video')
 source=root/'applications/video' if workspace else root
 original=selection.subprocess.run
 def missing_git(args,*a,**kw):
  if args[0]=='git':raise FileNotFoundError('git is unavailable')
  return original(args,*a,**kw)
 monkeypatch.setattr(selection.subprocess,'run',missing_git)
 assert run(source,tmp_path/'outside-view')==0
 if workspace:
  with pytest.raises(SystemExit,match='overlap'):run(source,root/'applications/out')
