"""Necessity ratchet over the protocol tree: known finding identities may only shrink.

Rule home: [Necessity](../02_protocol/impacts-method.md#necessity). The checks report
P2 (tracked files with identical bytes outside the allowlist), P5 (files under
02_protocol, src, 06_evaluations and tests with no inbound reference), P9 (history
markers in 02_protocol definition files) and P10 (retired names from retired_names.md in
protocol Markdown and the root guides). `necessity_ceilings.json` records known
finding identities; new findings and stale baseline entries fail. Counts are derived.
`docs/` and `.git` are outside the tree.
"""
import ast
import hashlib
from functools import lru_cache
import json
import posixpath
import re
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
CEILINGS = Path(__file__).with_name("necessity_ceilings.json")
EXCLUDED_ROOTS = ("docs/", ".git/")
READER_SCOPE = ("02_protocol/", "src/", "06_evaluations/", "tests/")
ENTRY_NAMES = {"AGENTS.md", "CONTEXT.md", "README.md", "pyproject.toml", "LICENSE", "conftest.py", "__init__.py"}
TOKEN = re.compile(r"[\w.\-/]+")
HISTORY_WORD = re.compile(r"\b(previously|formerly|historisch\w*|bisherig\w*|früher\w*)\b", re.IGNORECASE)
ONTOLOGY = "02_protocol/ontology.md"
RETIRED_NAMES = "tests/retired_names.md"
# The Protocol vocabulary glosses each level once in English; P10 exempts only that exact cell, once.
VOCABULARY_GLOSSES = {"`hauptprozess`": "Main process", "`teilprozess`": "Subprocess",
                      "`arbeitsschritt`": "Workstep", "`vorgang`": "Process instance"}
ROOT_DOCS = ("README.md", "CONTRIBUTING.md", "FIRST-WIN.md", "AGENTS.md", "CONTEXT.md")
DATED_HEADING = re.compile(r"^#+ .*(\d{4}-\d{2}-\d{2}|\d{1,2}\.\d{1,2}\.\d{4}|\bv\d+\.\d+)", re.MULTILINE)


def tracked_files(root: Path) -> dict[str, bytes]:
    """Tracked and new unignored files present on disk; docs/ and .git excluded."""
    try:
        listing = subprocess.run(
            ["git", "-C", str(root), "ls-files", "-z", "--cached", "--others", "--exclude-standard"],
            check=True, capture_output=True,
        ).stdout
    except (OSError, subprocess.CalledProcessError):
        pytest.skip("necessity checks need a Git checkout")
    paths = sorted({path for path in listing.decode().split("\0") if path and not path.startswith(EXCLUDED_ROOTS)})
    return {path: (root / path).read_bytes() for path in paths if (root / path).is_file()}


def duplicate_blobs(files: dict[str, bytes], allowlist: set[str]) -> list[str]:
    """P2: non-empty files whose bytes equal another file's, outside the allowlist."""
    groups: dict[str, list[str]] = {}
    for path, content in files.items():
        if content:
            groups.setdefault(hashlib.sha256(content).hexdigest(), []).append(path)
    return sorted(path for group in groups.values() if len(group) > 1 for path in group if path not in allowlist)


def _text(content: bytes) -> str | None:
    try:
        return content.decode("utf-8")
    except UnicodeDecodeError:
        return None


def _module_paths(source: str) -> set[str]:
    """Path suffixes of the modules a Python file imports, e.g. `impacts_protocol/hashing.py`."""
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return set()
    suffixes: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            modules = [alias.name for alias in node.names]
        elif isinstance(node, ast.ImportFrom) and node.module:
            modules = [node.module] + [f"{node.module}.{alias.name}" for alias in node.names]
        else:
            continue
        for module in modules:
            base = module.replace(".", "/")
            suffixes.update({f"{base}.py", f"{base}/__init__.py"})
    return suffixes


def unreferenced_files(files: dict[str, bytes], tree_readers: dict[str, str] | None = None) -> list[str]:
    """P5: files in the reader scope that no other file names by path, unique filename or import.

    A mention of a folder does not count as a reference to the files in it. Only a folder
    in `tree_readers`, whose files a named reader loads by enumeration, covers its files.
    """
    tree_readers = tree_readers or {}
    tails: dict[str, set[str]] = {}
    for path in files:
        parts = path.split("/")
        for start in range(len(parts)):
            tails.setdefault("/".join(parts[start:]), set()).add(path)
    referenced: set[str] = set()
    for source, content in files.items():
        text = _text(content)
        if text is None:
            continue
        hits: set[str] = set()
        for token in TOKEN.findall(text):
            token = token.rstrip(".")
            if token.startswith("impacts_protocol."):
                hits.update(tails.get(token.replace(".", "/") + ".py", ()))
            if "." not in token and "/" not in token:
                continue
            relative = posixpath.normpath(posixpath.join(posixpath.dirname(source), token))
            for candidate in (relative, posixpath.normpath(token.lstrip("/"))):
                if candidate in files:
                    hits.add(candidate)
            matches = tails.get(token.lstrip("./"), set())
            if "/" in token.lstrip("./") or len(matches) == 1:
                hits.update(matches)
        if source.endswith(".py"):
            for suffix in _module_paths(text):
                hits.update(tails.get(suffix, ()))
        referenced.update(hits - {source})
    return sorted(
        path for path in files
        if path.startswith(READER_SCOPE)
        and path not in referenced
        and not path.startswith(tuple(tree_readers))
        and posixpath.basename(path) not in ENTRY_NAMES
        and not re.fullmatch(r"test_.*\.py", posixpath.basename(path))
    )


def _history_occurrences(files: dict[str, bytes]):
    for path, content in sorted(files.items()):
        if not (path.startswith("02_protocol/") and path.endswith(".md")):
            continue
        text = _text(content) or ""
        for kind, pattern in (("word", HISTORY_WORD), ("heading", DATED_HEADING)):
            seen: dict[str, int] = {}
            for match in pattern.finditer(text):
                line = text.count("\n", 0, match.start()) + 1
                source_line = text.splitlines()[line - 1]
                normalized = " ".join(source_line.split())
                digest = hashlib.sha256(normalized.encode("utf-8")).hexdigest()
                seen[digest] = seen.get(digest, 0) + 1
                identity = f"{path}|{kind}|sha256:{digest}|{seen[digest]}"
                yield identity, f"{path}:{line}: {match.group(0).strip()}"


def history_markers(files: dict[str, bytes]) -> list[str]:
    """P9 diagnostics retain current line numbers for the human reader."""
    return sorted(detail for _identity, detail in _history_occurrences(files))


def history_marker_ids(files: dict[str, bytes]) -> list[str]:
    """Same violation survives unrelated line insertions and whitespace changes."""
    return sorted(identity for identity, _detail in _history_occurrences(files))


def retired_names(table: str) -> list[tuple[str, str]]:
    """Read every old spelling and its replacement from the test-owned table."""
    names = []
    for line in table.splitlines():
        if not line.startswith("|"):
            continue
        _, cell, replacement, _ = line.split("|")
        cell, replacement = cell.strip(), replacement.strip()
        if cell and not set(cell) <= {"-"} and cell != "Retired name":
            names.extend((name.strip(), replacement) for name in cell.split(","))
    assert names, "Retired-name fixture must contain names and replacements"
    assert all(name and replacement for name, replacement in names)
    assert len(names) == len({name for name, _ in names}), "Duplicate retired name"
    return names


def _retired_occurrences(files: dict[str, bytes]):
    names = retired_names(files[RETIRED_NAMES].decode("utf-8"))
    glosses = dict(VOCABULARY_GLOSSES)
    # Lowercase names also match at a sentence start; a capitalized name matches only as written,
    # so machine tokens such as `hauptprozess_revision` or `hauptprozesse/` stay outside the check.
    patterns = [(name, replacement, re.compile(rf"(?<![\w/`])(?:{re.escape(name)}{'|' + re.escape(name[0].upper() + name[1:]) if name[0].islower() else ''})(?![\w/`])"))
                for name, replacement in names]
    scope = {path: content for path, content in files.items()
             if (path.startswith("02_protocol/") and path.endswith(".md")) or path in ROOT_DOCS}
    for path, content in sorted(scope.items()):
        text = _text(content) or ""
        seen: dict[str, int] = {}
        for line_number, line in enumerate(text.splitlines(), 1):
            cells = line.split("|")
            if path == ONTOLOGY and len(cells) > 3 and glosses.get(cells[1].strip()) == cells[2].strip():
                del glosses[cells[1].strip()]
                line = "|".join(cells[:2] + cells[3:])
            for name, replacement, pattern in patterns:
                for match in pattern.finditer(line):
                    digest = hashlib.sha256(" ".join(line.split()).encode("utf-8")).hexdigest()
                    key = f"{name}|{digest}"
                    seen[key] = seen.get(key, 0) + 1
                    yield f"{path}|{name}|sha256:{digest}|{seen[key]}", f"{path}:{line_number}: {match.group(0)} -> {replacement}"


def retired_name_ids(files: dict[str, bytes]) -> list[str]:
    return sorted(identity for identity, _detail in _retired_occurrences(files))


@lru_cache(maxsize=1)
def _committed_baseline() -> dict:
    """Compare with committed HEAD; this does not authenticate a committed rewrite."""
    try:
        revision = subprocess.check_output(["git", "-C", str(ROOT), "rev-parse", "HEAD"], text=True).strip()
        raw = subprocess.check_output(["git", "-C", str(ROOT), "show", f"{revision}:tests/necessity_ceilings.json"])
    except (OSError, subprocess.CalledProcessError):
        pytest.skip("necessity baseline comparison needs committed Git history")
    return json.loads(raw)


def _committed_findings(metric: str) -> set[str] | None:
    """None before a metric's first commit: its baseline enters together with its detector."""
    committed = _committed_baseline()["known_findings"]
    return set(committed[metric]) if metric in committed else None


def _ratchet(metric: str, findings: list[str]) -> None:
    baseline = json.loads(CEILINGS.read_text(encoding="utf-8"))["known_findings"][metric]
    assert isinstance(baseline, list) and all(isinstance(item, str) and item for item in baseline)
    assert len(baseline) == len(set(baseline)), "Baseline contains duplicate finding identities"
    assert len(findings) == len(set(findings)), "Detector returned duplicate finding identities"
    known, actual = set(baseline), set(findings)
    committed = _committed_findings(metric)
    expansion = known - committed if committed is not None else set()
    assert not expansion, f"{metric}: baseline may only shrink from committed HEAD; added {sorted(expansion)}"
    new, removed = actual - known, known - actual
    print(f"{metric}: {len(actual)} known findings", *sorted(actual), sep="\n  ")
    assert not new, f"{metric}: new findings {sorted(new)}"
    assert not removed, f"{metric}: remove stale baseline entries {sorted(removed)}"


@pytest.fixture(scope="module")
def files():
    return tracked_files(ROOT)


def test_p2_duplicate_blobs_do_not_rise(files):
    allowlist = set(json.loads(CEILINGS.read_text(encoding="utf-8"))["duplicate_allowlist"])
    _ratchet("duplicate_blobs", duplicate_blobs(files, allowlist))


def test_p5_files_without_reader_do_not_rise(files):
    tree_readers = json.loads(CEILINGS.read_text(encoding="utf-8"))["tree_readers"]
    _ratchet("unreferenced_files", unreferenced_files(files, tree_readers))


def test_p9_history_markers_do_not_rise(files):
    _ratchet("history_markers", history_marker_ids(files))


def test_p10_retired_names_do_not_rise(files):
    for _identity, detail in _retired_occurrences(files):
        print(detail)
    _ratchet("retired_names", retired_name_ids(files))


def test_detectors_find_planted_defects():
    planted = {
        "02_protocol/rule.md": b"# Rule\n\nPreviously the rule read otherwise. See [other](other.md).\n\n## Changes 2026-01-01\n",
        "02_protocol/other.md": b"Same bytes.\n",
        "src/pkg/used.py": b"VALUE = 1\n",
        "src/pkg/orphan.py": b"Same bytes.\n",
        "tests/test_x.py": b"from pkg import used\n",
        "tests/CONTEXT.md": b"Helpers live in src/pkg/ and tests/.\n",
        "tests/helper_orphan.py": b"X = 2\n",
        "06_evaluations/orphan.md": b"no reader\n",
    }
    assert duplicate_blobs(planted, set()) == ["02_protocol/other.md", "src/pkg/orphan.py"]
    assert duplicate_blobs(planted, {"src/pkg/orphan.py"}) == ["02_protocol/other.md"]
    assert unreferenced_files(planted, {"06_evaluations/": "a named reader"}) == [
        "02_protocol/rule.md", "src/pkg/orphan.py", "tests/helper_orphan.py",
    ]
    assert unreferenced_files(planted) == [
        "02_protocol/rule.md", "06_evaluations/orphan.md", "src/pkg/orphan.py", "tests/helper_orphan.py",
    ]
    assert [finding.split(": ")[1] for finding in history_markers(planted)] == ["Previously", "## Changes 2026-01-01"]


@pytest.mark.parametrize("metric", ["duplicate_blobs", "unreferenced_files", "history_markers", "retired_names"])
def test_atomic_ratchet_rejects_replacement_and_retires_removed_findings(tmp_path, monkeypatch, metric):
    path = tmp_path / "baseline.json"
    monkeypatch.setattr(sys.modules[__name__], "CEILINGS", path)
    monkeypatch.setattr(sys.modules[__name__], "_committed_findings", lambda _metric: {"old-a", "old-b"})

    def record(values):
        path.write_text(json.dumps({"known_findings": {metric: values}}), encoding="utf-8")

    record(["old-a", "old-b"])
    _ratchet(metric, ["old-a", "old-b"])
    with pytest.raises(AssertionError, match="new findings"):
        _ratchet(metric, ["old-a", "new-c"])
    with pytest.raises(AssertionError, match="stale baseline"):
        _ratchet(metric, ["old-a"])
    record(["old-a"])
    _ratchet(metric, ["old-a"])
    record(["old-a", "new-c"])
    with pytest.raises(AssertionError, match="baseline may only shrink"):
        _ratchet(metric, ["old-a", "new-c"])


def test_history_identity_survives_line_shift_but_not_replacement():
    path = "02_protocol/rule.md"
    old = {path: b"# Rule\n\nPreviously alpha.\n"}
    shifted = {path: b"# Rule\n\nCurrent introduction.\n\nPreviously alpha.\n"}
    replaced = {path: b"# Rule\n\nPreviously beta.\n"}
    assert history_marker_ids(old) == history_marker_ids(shifted)
    assert history_marker_ids(old) != history_marker_ids(replaced)
    assert len(history_marker_ids({path: b"Previously alpha.\nPreviously alpha.\n"})) == 2


def test_retired_names_skip_tokens_and_paths_but_report_replacements():
    planted = {
        RETIRED_NAMES: (ROOT / RETIRED_NAMES).read_bytes(),
        "02_protocol/rule.md": (
            "One Application here.\n`hauptprozess_revision` and `hauptprozesse/` are tokens.\n"
            "`Application` and examples/Application/file.md are excluded.\n"
            "Thin run starts a line.\n"
        ).encode(),
    }
    found = list(_retired_occurrences(planted))
    assert [identity.split("|")[:2] for identity, _ in found] == [
        ["02_protocol/rule.md", "Application"], ["02_protocol/rule.md", "thin run"],
    ]
    assert [detail for _, detail in found] == [
        "02_protocol/rule.md:1: Application -> Hauptprozess",
        "02_protocol/rule.md:4: Thin run -> Vorgang",
    ]


def test_retired_names_exempt_only_the_sanctioned_vocabulary_gloss_once():
    ontology = (
        "| Machine term | English meaning | Boundary |\n|---|---|---|\n"
        "| `arbeitsschritt` | Workstep | used by a workstep |\n"
        "| `arbeitsschritt` | Workstep | job |\n"
        "| Capability | Application | operation |\n"
    )
    found = sorted(identity.split("|")[1] for identity in retired_name_ids({
        ONTOLOGY: ontology.encode(), RETIRED_NAMES: (ROOT / RETIRED_NAMES).read_bytes(),
    }))
    assert found == ["Application", "workstep", "workstep"]


def test_retired_name_table_in_active_ontology_is_not_exempt(capsys):
    planted = {
        RETIRED_NAMES: (ROOT / RETIRED_NAMES).read_bytes(),
        ONTOLOGY: b'<a id="retired-names"></a>\n| Application | Hauptprozess |\n',
    }
    with pytest.raises(AssertionError, match="new findings"):
        test_p10_retired_names_do_not_rise(planted)
    assert "Application -> Hauptprozess" in capsys.readouterr().out
