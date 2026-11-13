"""Synthetic walk file binding. Logical input names resolve to recorded references."""
from hashlib import sha256
from pathlib import Path
import subprocess
import re

from impacts_protocol import file_references as raw_references
from impacts_protocol.io import load_frontmatter


def source_home(attempt: Path) -> Path:
    workspace = attempt.parents[3]
    (workspace / "records").mkdir(exist_ok=True)
    router = workspace / "CONTEXT.md"
    declaration = "Form: records/ Record Library per source record"
    if declaration not in router.read_text():
        with router.open("a") as handle:
            handle.write("\n" + declaration + "\n")
    return workspace / "records" / attempt.parents[1].name / attempt.parent.name / attempt.name


def input_file(attempt: Path, relative: str | Path) -> Path:
    relative = str(relative)
    for label in ("input", "material"):
        if f"/{label}/" in relative or relative.endswith(f"/{label}"):
            prefix, _, tail = relative.partition(f"/{label}")
            return input_file(attempt / prefix, label + tail)
    label = relative.split("/", 1)[0]
    if label not in ("input", "material"):
        return attempt / relative
    tail = relative.removeprefix(label).lstrip("/")
    context = attempt.parent.parent / 'CONTEXT.md'
    if context.is_file() and tail:
        meta = load_frontmatter(context)
        for entry in meta.get('laufpfad', []):
            if entry.get('arbeitsschritt_ref') == 'arbeitsschritt:' + attempt.parent.name and entry.get('nummer') == int(attempt.name):
                target = f"arbeitsschritt:{attempt.parent.name}:{relative}"
                tree = meta.get('hauptprozess_revision', '').removeprefix('git-tree:')
                lines = subprocess.run(['git', '-C', str(attempt.parents[3]), 'grep', '-h', '-F', target, tree, '--', '*CONTEXT.md'], text=True, capture_output=True).stdout
                sources = re.findall(r'`(output/[^` ]+) -> ' + re.escape(target) + r'`', lines)
                for ref in entry.get('gelesen', []):
                    path = ref.get('pfad', '')
                    if 'revision' not in ref and (path.endswith('/' + tail) or any(path.endswith('/' + source) for source in sources)):
                        return attempt.parents[3] / path
    return source_home(attempt) / tail


def references(attempt: Path, declared: list[str]) -> list[dict]:
    root = attempt.parents[3]
    (attempt / "output").mkdir(parents=True, exist_ok=True)
    result = []
    for name in declared:
        path = input_file(attempt, name)
        relative = path.relative_to(root).as_posix()
        records = raw_references(root, [relative])
        if path.is_relative_to(source_home(attempt)):
            subprocess.run(['git', '-C', str(root), 'add', '--', relative], check=True, capture_output=True)
            subprocess.run(['git', '-C', str(root), '-c', 'user.name=Synthetic fixture', '-c', 'user.email=fixture@example.invalid', 'commit', '--only', '--allow-empty', '-qm', 'Bind synthetic record', '--', relative], check=True, capture_output=True)
            commit = subprocess.check_output(['git', '-C', str(root), 'log', '-1', '--format=%H', '--', relative], text=True).strip()
            for ref in records:
                ref['revision'] = 'git-commit:' + commit
                ref['eingabe'] = name
        if name.startswith(("input/", "material/")):
            for ref in records:
                ref['eingabe'] = name
        result.extend(records)
    return result


def content_digest(payload: bytes) -> str:
    return sha256(payload).hexdigest()


def git(root: Path, *args: str) -> str:
    return subprocess.check_output(["git", "-C", str(root), *args], text=True).strip()
