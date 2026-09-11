"""Local controlled quotation handover; trusted selection, never a general answer judge."""
from dataclasses import dataclass
import hashlib
import json
from pathlib import Path, PurePosixPath
import re
import shutil
import subprocess
from tempfile import mkdtemp, NamedTemporaryFile


@dataclass(frozen=True)
class Section:
    path: str
    heading: str
    anchor: str | None = None


@dataclass(frozen=True)
class Input:
    path: str
    origin: str
    # A synthetic local access policy supplied by the harness, never the writer.
    permitted: bool = True


@dataclass(frozen=True)
class Contract:
    task: str
    revision: str
    language: str
    target: Path
    sources: tuple[tuple[Path, bytes], ...]
    sections: tuple[bytes, ...]
    inputs: tuple[tuple[Input, Path, bytes], ...]
    operational: bool


def _relative(value: str) -> str:
    if (not isinstance(value, str) or not value or '\\' in value
            or any(ord(c) < 32 for c in value)
            or any(p in {'', '.', '..'} for p in value.split('/'))
            or PurePosixPath(value).is_absolute()):
        raise ValueError('unsafe relative path')
    return value


def _safe(root: Path, relative: str) -> Path:
    path = root
    for component in _relative(relative).split('/'):
        path /= component
        if path.is_symlink():
            raise ValueError('symlink is outside the local parser contract')
    return path


def _git(root: Path, *args: str) -> bytes:
    result = subprocess.run(['git', '--no-replace-objects', '--literal-pathspecs', '-C', str(root), *args], capture_output=True)
    if result.returncode:
        raise ValueError('pinned Git source unavailable')
    return result.stdout


def _source(root: Path, revision: str, relative: str) -> bytes:
    _safe(root, relative)
    entries = _git(root, 'ls-tree', '-z', revision, '--', relative).split(b'\0')
    if len(entries) != 2 or entries[1] or b'\t' not in entries[0]:
        raise ValueError('pinned source must be one regular file')
    metadata, name = entries[0].split(b'\t', 1)
    mode, kind, oid = metadata.split()
    if mode not in {b'100644', b'100755'} or kind != b'blob' or name.decode('utf-8') != relative:
        raise ValueError('pinned source must be one regular file')
    return _git(root, 'cat-file', 'blob', oid.decode('ascii'))


def extract(source: bytes, section: Section) -> bytes:
    """Exact UTF-8/LF ATX section, including its adjacent explicit anchor if present."""
    try:
        text = source.decode('utf-8')
    except UnicodeDecodeError as error:
        raise ValueError('source is not UTF-8') from error
    if not text.endswith('\n') or '\r' in text or '\x00' in text:
        raise ValueError('source requires LF and a final newline')
    lines = source.splitlines(keepends=True)
    headings = []
    anchors = []
    fence = None
    pending = None
    for index, raw in enumerate(lines):
        line = raw.decode('utf-8').rstrip('\n')
        marker = re.fullmatch(r' {0,3}(`{3,}|~{3,})(.*)', line)
        if fence:
            if marker and marker[1][0] == fence[0] and len(marker[1]) >= len(fence) and not marker[2].strip():
                fence = None
            continue
        if marker:
            fence = marker[1]
            pending = None
            continue
        anchor = re.fullmatch(r'<a id="([^"<>]+)"></a>', line)
        if anchor:
            anchors.append(anchor[1])
            if pending:
                raise ValueError('multiple adjacent anchors are unsupported')
            pending = (index, anchor[1])
            continue
        prose = re.sub(r'(`+).*?\1', '', line)
        if re.search(r'<[A-Za-z!/?]', prose):
            raise ValueError('HTML outside an explicit anchor is unsupported')
        heading = re.fullmatch(r'(#{1,6}) ([^#\s].*?)(?: +#+)?', line)
        if heading:
            headings.append((index, len(heading[1]), heading[2], pending))
            pending = None
        elif line.strip():
            if pending or re.match(r' {0,3}(?:#{1,6}\s|<a\b|=+\s*$|-+\s*$)', line):
                raise ValueError('unsupported heading or anchor shape')
            pending = None
        elif pending:
            raise ValueError('explicit anchor must be adjacent to its heading')
    if fence or pending:
        raise ValueError('unclosed fence or unattached anchor')
    matches = [h for h in headings if h[2] == section.heading]
    if len(matches) != 1:
        raise ValueError('missing or duplicate heading')
    selected = matches[0]
    attached = selected[3]
    if section.anchor is not None:
        if anchors.count(section.anchor) != 1 or not attached or attached[1] != section.anchor:
            raise ValueError('missing, duplicate or mismatched anchor')
    elif attached:
        raise ValueError('explicit anchor must be declared')
    begin = attached[0] if attached else selected[0]
    end = next((h[0] for h in headings if h[0] > selected[0] and h[1] <= selected[1]), len(lines))
    # An anchor immediately preceding the next heading belongs to that next section.
    next_heading = next((h for h in headings if h[0] == end), None)
    if next_heading and next_heading[3]:
        end = next_heading[3][0]
    return b''.join(lines[begin:end])


def bind(repository: Path, revision: str, sections: tuple[Section, ...], *, task: str,
         language: str, staging: Path, target: Path, declared_inputs: tuple[str, ...] = (),
         inputs: tuple[Input, ...] = (), operational: bool = False) -> Contract:
    """Harness fixes scope before candidate generation. Staging is outside reached attempts.

    declared_inputs comes from the bound workstep's eingaben, including provenance;
    inputs supplies its approved source mappings. Neither argument is writer-selected.
    """
    if language not in {'en', 'de'} or not task.strip() or not sections:
        raise ValueError('task, language and source selection required')
    if not re.fullmatch(r'(?:[0-9a-f]{40}|[0-9a-f]{64})', revision):
        raise ValueError('exact commit pin required')
    if repository.is_symlink() or _git(repository, 'cat-file', '-t', revision).strip() != b'commit':
        raise ValueError('exact commit pin required')
    if len(set(sections)) != len(sections):
        raise ValueError('duplicate source selection')
    names = tuple(item.path for item in inputs)
    if (len(set(declared_inputs)) != len(declared_inputs) or len(set(names)) != len(names)
            or set(names) != set(declared_inputs) or (operational != bool(inputs))):
        raise ValueError('independent declared-input inventory mismatch')
    if any(type(item.permitted) is not bool or not re.fullmatch(r'[\w./-]+', item.path) for item in inputs):
        raise ValueError('input identifiers and synthetic access policy are unsupported')
    if staging.exists() or staging.is_symlink() or target.is_symlink():
        raise ValueError('binding requires new safe staging and a safe target')
    source_names = tuple(dict.fromkeys(s.path for s in sections))
    originals = {p: _source(repository, revision, p) for p in source_names}
    clauses = tuple(extract(originals[s.path], s) for s in sections)
    values = tuple((item, _source(repository, revision, item.origin)) for item in inputs)
    staging.parent.mkdir(parents=True, exist_ok=True)
    temporary = Path(mkdtemp(prefix='.answer-bind-', dir=staging.parent))
    try:
        provenance = {}
        for name, payload in [(f'protocol/{p}', b) for p, b in originals.items()] + [(f'case/{i.path}', b) for i, b in values]:
            path = _safe(temporary, name)
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(payload)
            origin = name.removeprefix('protocol/') if name.startswith('protocol/') else next(i.origin for i, _ in values if 'case/' + i.path == name)
            provenance[name] = {'revision': revision, 'origin': origin, 'sha256': hashlib.sha256(payload).hexdigest()}
        (temporary / 'provenance.json').write_text(json.dumps(provenance, ensure_ascii=False, sort_keys=True) + '\n', encoding='utf-8')
        temporary.rename(staging)
    except Exception:
        shutil.rmtree(temporary)
        raise
    sources = tuple((staging / 'protocol' / p, b) for p, b in originals.items())
    sources += ((staging / 'provenance.json', (staging / 'provenance.json').read_bytes()),)
    return Contract(task, revision, language, target, sources, clauses,
                    tuple((i, staging / 'case' / i.path, b) for i, b in values), operational)


def _read_bound(path: Path, expected: bytes) -> bytes:
    # Parent links cannot redirect an immutable bound surface.
    if any(p.is_symlink() for p in (path, *path.parents)):
        raise ValueError('bound path is a symlink')
    try:
        actual = path.read_bytes()
    except OSError as error:
        raise ValueError('bound source unavailable') from error
    if actual != expected:
        raise ValueError('bound source changed')
    return actual


def _fields(payload: bytes, names: tuple[str, ...]) -> None:
    def unique(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValueError('duplicate structured field')
            result[key] = value
        return result
    try:
        value = json.loads(payload.decode('utf-8'), object_pairs_hook=unique)
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise ValueError('invalid structured fields') from error
    if not isinstance(value, dict) or set(value) != {'inputs'} or not isinstance(value['inputs'], list):
        raise ValueError('exact structured fields required')
    rows = value['inputs']
    if any(not isinstance(row, dict) or set(row) != {'path'} or not isinstance(row['path'], str) for row in rows):
        raise ValueError('only input paths are writer-supplied')
    actual = tuple(row['path'] for row in rows)
    if len(set(actual)) != len(actual) or set(actual) != set(names):
        raise ValueError('independent declared-input inventory mismatch')


def render(contract: Contract, fields: bytes | None = None) -> bytes:
    """Source clauses remain exact; all supported case findings are computed locally."""
    for path, expected in contract.sources:
        _read_bound(path, expected)
    if fields is not None:
        if not contract.operational:
            raise ValueError('pure explanation has no case fields')
        _fields(fields, tuple(i.path for i, _, _ in contract.inputs))
    de = contract.language == 'de'
    heading = '# Gebundene Quellenaussagen\n\n' if de else '# Bound source statements\n\n'
    payload = heading.encode() + b'\n'.join(contract.sections)
    if contract.operational:
        rows = ['\n## Synthetischer lokaler Eingabecheck\n' if de else '\n## Synthetic local input check\n']
        for item, path, expected in contract.inputs:
            # This test policy proves only local fixture access, never remote credentials.
            if item.permitted:
                _read_bound(path, expected)
                finding = 'lesbar; Bytes entsprechen der Quelle' if de else 'readable; bytes match the source'
            else:
                finding = 'Zugriff fehlt; abhängigen Geschäftsschritt nicht öffnen' if de else 'access missing; keep dependent business step unopened'
            rows.append(f'- {item.path}: {finding}.\n')
        payload += ''.join(rows).encode('utf-8')
    return payload


def equality(contract: Contract, candidate: bytes) -> str:
    expected = render(contract)
    if not isinstance(candidate, bytes) or candidate != expected:
        raise ValueError('whole output differs from trusted rendering')
    return hashlib.sha256(candidate).hexdigest()


def deliver(contract: Contract, candidate: Path, *, action_revision: str | None = None) -> dict:
    """One local delivery path, also used for retries. No business transition or approval.

    action_revision models a declared same-revision freshness rule; it is not a
    generic freshness oracle or authority check. Callers enforce any real effect.
    """
    if action_revision is not None and action_revision != contract.revision:
        raise ValueError('current-action revision check failed')
    if candidate.is_symlink() or any(p.is_symlink() for p in contract.target.parents):
        raise ValueError('unsafe delivery path')
    payload = candidate.read_bytes()
    digest = equality(contract, payload)
    target = contract.target
    if target.is_symlink():
        raise ValueError('unsafe delivery path')
    if target.exists():
        equality(contract, target.read_bytes())
    else:
        target.parent.mkdir(parents=True, exist_ok=True)
        with NamedTemporaryFile(dir=target.parent, delete=False) as stream:
            stage = Path(stream.name)
            stream.write(payload)
        try:
            equality(contract, stage.read_bytes())
            stage.replace(target)
        finally:
            stage.unlink(missing_ok=True)
        equality(contract, target.read_bytes())
    return {'target': str(target), 'sha256': digest, 'revision': contract.revision,
            'local_inputs_pass': contract.operational and all(i.permitted for i, _, _ in contract.inputs)}
