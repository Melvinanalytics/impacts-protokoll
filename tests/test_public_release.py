"""Check the existing release allowlist; this neither exports nor approves a release."""
from pathlib import Path, PurePosixPath
import posixpath
import re
import tomllib
from urllib.parse import unquote, urlsplit

import pytest

ROOT = Path(__file__).resolve().parents[1]

# One allowlist for the release surface.
PUBLIC_PATHS = (
    '.gitignore', 'AGENTS.md', 'CONTEXT.md', 'LICENSE', 'README.md', 'FIRST-WIN.md', 'pyproject.toml',
    '02_protocol/', '06_evaluations/', 'src/', 'tests/',
)


def export_files(root):
    files = {}
    for entry in PUBLIC_PATHS:
        path = root / entry
        assert path.exists(), f'Missing allowlisted path: {entry}'
        candidates = path.rglob('*') if path.is_dir() else [path]
        for candidate in candidates:
            assert not candidate.is_symlink(), f'Symlink in export: {candidate.relative_to(root)}'
            if not candidate.is_file() or '__pycache__' in candidate.parts or candidate.suffix == '.pyc':
                continue
            relative = candidate.relative_to(root).as_posix()
            files[relative] = candidate.read_text(encoding='utf-8')
    # Remove the source-only design-record navigation row on export.
    files['CONTEXT.md'] = '\n'.join(line for line in files['CONTEXT.md'].splitlines() if '| Design record:' not in line)
    return files


def prose(text):
    return re.sub(r'^(`{3,}|~{3,})[^\n]*\n.*?^\1\s*$', '', text, flags=re.M | re.S)


def anchors(text):
    found = set(re.findall(r'<a\s+(?:id|name)=["\x27]([^"\x27]+)', text))
    counts = {}
    for title in re.findall(r'^#{1,6}\s+(.+?)\s*#*$', prose(text), re.M):
        title = re.sub(r'\[([^\]]+)\]\([^)]*\)', r'\1', title).replace('`', '').lower()
        slug = re.sub(r'[^\w\- ]', '', title).replace(' ', '-')
        count = counts.get(slug, 0)
        counts[slug] = count + 1
        found.add(slug + (f'-{count}' if count else ''))
    return found


def link_issues(files):
    """Check inline Markdown references using only the selected artifact's paths."""
    directories = {str(parent) for name in files for parent in PurePosixPath(name).parents}
    issues = []
    for name, text in files.items():
        if not name.endswith('.md'):
            continue
        for target in re.findall(r'\[[^\]\n]*\]\(([^)\n]+)\)', prose(text)):
            target = target.split(' "', 1)[0].strip('<> ')
            url = urlsplit(target)
            if url.scheme in {'http', 'https', 'mailto'}:
                continue
            if url.scheme or url.netloc or unquote(url.path).startswith('/'):
                issues.append((name, target, 'nonportable reference'))
                continue
            resolved = posixpath.normpath(posixpath.join(posixpath.dirname(name), unquote(url.path))) if url.path else name
            if resolved not in files and resolved not in directories:
                issues.append((name, target, 'target outside export'))
            elif url.fragment and resolved.endswith('.md') and unquote(url.fragment) not in anchors(files[resolved]):
                issues.append((name, target, 'missing anchor'))
    return issues


def test_public_markdown_references_resolve_inside_the_allowlisted_export():
    assert link_issues(export_files(ROOT)) == []


def test_public_docs_contain_no_workstation_paths():
    for name, text in export_files(ROOT).items():
        if name.endswith('.md'):
            assert not re.search(r'/Users/|/home/|/var/folders/|file://', text), name


@pytest.mark.parametrize('target', [
    '../research/private.md', '/Users/example/private.md', 'file:///tmp/private.md',
    '../../outside.md', 'included.md#missing',
])
def test_an_omitted_or_nonportable_target_or_missing_anchor_blocks_reference_closure(target):
    files = {'docs/README.md': f'[reference]({target})', 'docs/included.md': '# Present\n'}
    assert len(link_issues(files)) == 1


def test_export_links_support_relative_paths_unicode_aliases_and_duplicate_headings():
    files = {'README.md': '[one](docs/guide.md#überblick-1) [two](docs/guide.md#legacy) [dir](docs/)',
             'docs/guide.md': '# Überblick\n# Überblick\n<a id="legacy"></a>\n'}
    assert link_issues(files) == []


def test_export_excludes_all_private_documentation_and_handovers():
    paths = export_files(ROOT)
    assert all(not p.startswith('docs/') for p in paths)
    assert all(not p.startswith('v03_') for p in paths)
    assert set(PUBLIC_PATHS) == {'.gitignore', 'AGENTS.md', 'CONTEXT.md', 'LICENSE', 'README.md', 'FIRST-WIN.md', 'pyproject.toml', '02_protocol/', '06_evaluations/', 'src/', 'tests/'}


@pytest.mark.parametrize("path", ["README.md", "02_protocol/translations/de.md"])
def test_current_entry_instructions_match_distribution_version(path):
    version = tomllib.loads((ROOT / "pyproject.toml").read_text())["project"]["version"]
    text = (ROOT / path).read_text()
    release_tags = re.findall(r"releases/tag/v([^/)\s]+)", text)
    clone_tags = re.findall(r"git clone --branch v(\S+)", text)
    wheel_versions = re.findall(r"impacts_protocol-([^-\s]+)-py3-none-any\.whl", text)
    assert release_tags and wheel_versions
    assert set(release_tags + clone_tags + wheel_versions) == {version}
