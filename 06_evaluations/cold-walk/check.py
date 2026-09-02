#!/usr/bin/env python3
"""Walk one synthetic Vorgang through loop, wait and human gate with the public API."""

from dataclasses import dataclass
from pathlib import Path
import shutil
import subprocess
from tempfile import TemporaryDirectory

import yaml

from impacts_protocol import init_workspace, surface_hash, validate
from impacts_protocol.io import load_frontmatter

BEISPIEL = Path(__file__).resolve().parent / "beispiel" / "applications" / "prueffall"
APPLICATION = "prueffall"
VORGANG = "prueffall-001"
SYNTHETIC_REVIEWER = "human:beispiel-pruefer"
SYNTHETIC_TIME = "2026-09-02T10:00:00+02:00"


@dataclass(frozen=True)
class State:
    label: str
    valid: bool
    codes: tuple[str, ...]


@dataclass(frozen=True)
class WalkResult:
    routers: tuple[str, ...]
    states: tuple[State, ...]
    mutation_codes: frozenset[str]
    import_state: State
    import_oid_equal: bool

    @property
    def valid(self) -> bool:
        return (
            all(state.valid for state in self.states)
            and "hash.mismatch" in self.mutation_codes
            and self.import_state.valid
            and self.import_oid_equal
        )


class Harness:
    """The smallest harness: attempt folders, hashes, Laufpfad, nothing else."""

    def __init__(self, root: Path, revision: str):
        self.root = root
        self.revision = revision
        self.run_root = root / "vorgaenge" / VORGANG
        self.laufpfad: list[dict] = []
        self.steps = {
            path.parent.name: load_frontmatter(path)
            for path in (root / "applications" / APPLICATION).glob(
                "hauptprozess/teilprozesse/*/arbeitsschritte/*/CONTEXT.md"
            )
        }

    def attempt(self, slug: str, versuch: int) -> Path:
        return self.run_root / "arbeitsschritte" / slug / f"{versuch:03d}"

    def open(self, slug: str, versuch: int, inputs: dict[str, str]) -> dict:
        attempt = self.attempt(slug, versuch)
        _write_files(attempt, inputs)
        entry = {
            "arbeitsschritt_ref": f"arbeitsschritt:{slug}",
            "versuch": versuch,
            "status": "aktiv",
            "eingabe_hash": surface_hash(attempt, self.steps[slug]["eingaben"]),
        }
        self.laufpfad.append(entry)
        self._write()
        return entry

    def wait(self, entry: dict, ausloeser: str, continuation_ref: str) -> None:
        entry["status"] = "wartend"
        entry["wiedereinstieg"] = {"ausloeser": ausloeser, "continuation_ref": continuation_ref}
        self._write()

    def close(
        self, entry: dict, outputs: dict[str, str], route: str, freigabe: dict | None = None
    ) -> None:
        slug = entry["arbeitsschritt_ref"].removeprefix("arbeitsschritt:")
        attempt = self.attempt(slug, entry["versuch"])
        _write_files(attempt, outputs)
        entry.pop("wiedereinstieg", None)
        entry["status"] = "abgeschlossen"
        entry["gewaehlte_route"] = route
        entry["ausgabe_hash"] = surface_hash(attempt, self.steps[slug]["ausgaben"])
        if freigabe is not None:
            entry["freigabe"] = freigabe
        self._write()

    def advance(
        self,
        entry: dict,
        outputs: dict[str, str],
        route: str,
        next_slug: str,
        next_versuch: int,
        next_inputs: dict[str, str],
    ) -> dict:
        """Close one attempt and open its successor in one write; the protocol allows no state between."""
        self.close(entry, outputs, route)
        return self.open(next_slug, next_versuch, next_inputs)

    def state(self, label: str) -> State:
        report = validate(self.root)
        return State(label, report.valid, tuple(sorted({issue.code for issue in report.issues})))

    def _write(self) -> None:
        metadata = {
            "type": "vorgang",
            "id": f"vorgang:{VORGANG}",
            "application_revision": f"git-tree:{self.revision}",
            "laufpfad": self.laufpfad,
        }
        frontmatter = yaml.safe_dump(metadata, allow_unicode=True, sort_keys=False).rstrip()
        self.run_root.mkdir(parents=True, exist_ok=True)
        (self.run_root / "CONTEXT.md").write_text(
            f"---\n{frontmatter}\n---\n\n# Prüffall 001\n\nSynthetischer Lauf des Cold Walk.\n",
            encoding="utf-8",
        )


def walk(base: Path) -> WalkResult:
    """Initialize, commit, bind and run the synthetic Vorgang; then mutate one input."""
    root = init_workspace(Path(base) / "workspace")
    shutil.copytree(BEISPIEL, root / "applications" / APPLICATION)
    _git(root, "init", "-q", "-b", "main")
    _git(root, "config", "user.email", "cold-walk@example.invalid")
    _git(root, "config", "user.name", "Cold Walk")
    _git(root, "add", ".")
    _git(root, "commit", "-q", "-m", "application prueffall")
    revision = _git(root, "rev-parse", f"HEAD:applications/{APPLICATION}")

    harness = Harness(root, revision)
    states = []

    entry = harness.open("pruefen", 1, {"input/antrag.md": "Antrag ohne Geburtsdatum\n"})
    states.append(harness.state("pruefen 001 aktiv"))

    entry = harness.advance(
        entry,
        {"output/pruefbericht.md": "Befund: Geburtsdatum fehlt\n"},
        "klaerung",
        "nachfordern",
        1,
        {"input/pruefbericht.md": "Befund: Geburtsdatum fehlt\n"},
    )
    states.append(harness.state("nachfordern 001 aktiv nach klaerung"))

    harness.wait(entry, "unterlagen-nachgereicht", "records/antrag-001")
    states.append(harness.state("nachfordern 001 wartend"))

    entry = harness.advance(
        entry,
        {"output/nachforderung.md": "Bitte Geburtsdatum nachreichen\n"},
        "nachgereicht",
        "pruefen",
        2,
        {"input/antrag.md": "Antrag mit Geburtsdatum\n"},
    )
    states.append(harness.state("pruefen 002 aktiv nach nachgereicht"))

    entry = harness.advance(
        entry,
        {"output/pruefbericht.md": "Befund: vollständig\n"},
        "bestanden",
        "entscheiden",
        1,
        {"input/pruefbericht.md": "Befund: vollständig\n"},
    )
    states.append(harness.state("entscheiden 001 aktiv nach bestanden human-gate"))

    harness.close(
        entry,
        {"output/entscheidung.md": "Entscheidung: bewilligt, Begründung: Befund vollständig\n"},
        "freigegeben",
        freigabe={"by": SYNTHETIC_REVIEWER, "at": SYNTHETIC_TIME},
    )
    states.append(harness.state("entscheiden 001 abgeschlossen freigegeben end:entschieden"))

    (harness.attempt("pruefen", 1) / "input" / "antrag.md").write_text("Antrag manipuliert\n", encoding="utf-8")
    mutation = frozenset(issue.code for issue in validate(root).issues)

    import_state, import_oid_equal = _import_into_second_repository(base, root, revision)
    return WalkResult(tuple(_router_chain(root)), tuple(states), mutation, import_state, import_oid_equal)


def _import_into_second_repository(base: Path, source: Path, revision: str) -> tuple[State, bool]:
    """Byte-copy the committed Application into a second workspace; the tree oid must not change."""
    kunde = init_workspace(Path(base) / "kunde")
    target = kunde / "applications" / APPLICATION
    target.mkdir()
    source_commit = _git(source, "rev-parse", "HEAD")
    archive = subprocess.run(
        ["git", "-C", str(source), "archive", "--format=tar", f"{source_commit}:applications/{APPLICATION}"],
        stdout=subprocess.PIPE,
        check=True,
    ).stdout
    subprocess.run(["tar", "-x", "-C", str(target)], input=archive, check=True)
    _git(kunde, "init", "-q", "-b", "main")
    _git(kunde, "config", "user.email", "cold-walk@example.invalid")
    _git(kunde, "config", "user.name", "Cold Walk")
    _git(kunde, "add", ".")
    _git(kunde, "commit", "-q", "-m", f"import applications/{APPLICATION} from {source.name}@{source_commit[:12]} (tree {revision})")
    imported = _git(kunde, "rev-parse", f"HEAD:applications/{APPLICATION}")
    harness = Harness(kunde, imported)
    harness.open("pruefen", 1, {"input/antrag.md": "Antrag im Kundenrepository\n"})
    return harness.state("import prueffall in zweites repository"), imported == revision


def main() -> int:
    """Run the walk in a disposable repository and report every state."""
    with TemporaryDirectory(prefix="impacts-cold-walk-") as directory:
        result = walk(Path(directory))
    for router in result.routers:
        print(f"ROUTER {router}")
    for state in result.states:
        verdict = "PASS" if state.valid else "FAIL " + ", ".join(state.codes)
        print(f"STATE {state.label}: {verdict}")
        if state.label.endswith("human-gate"):
            print(
                f"STOP Human Gate: arbeitsschritt:entscheiden wartet auf freigabe. "
                f"Der Walk setzt eine synthetische Freigabe durch {SYNTHETIC_REVIEWER}."
            )
    fired = "hash.mismatch" in result.mutation_codes
    print(f"MUTATION input geändert: {'hash.mismatch' if fired else 'nicht erkannt'}")
    import_verdict = "PASS" if result.import_state.valid else "FAIL " + ", ".join(result.import_state.codes)
    print(f"STATE {result.import_state.label}: {import_verdict}")
    print(f"IMPORT tree oid gleich in zweitem Repository: {'ja' if result.import_oid_equal else 'nein'}")
    print("PASS cold walk" if result.valid else "FAIL cold walk")
    return 0 if result.valid else 1


def _router_chain(root: Path) -> list[str]:
    application = root / "applications" / APPLICATION
    process = application / "hauptprozess"
    entry = load_frontmatter(process / "CONTEXT.md")["einstieg_ref"].removeprefix("arbeitsschritt:")
    step = next(process.glob(f"teilprozesse/*/arbeitsschritte/{entry}/CONTEXT.md"))
    chain = [
        root / "CONTEXT.md",
        application / "CONTEXT.md",
        process / "CONTEXT.md",
        step.parent.parent.parent / "CONTEXT.md",
        step,
    ]
    return [path.relative_to(root).as_posix() for path in chain]


def _write_files(attempt: Path, files: dict[str, str]) -> None:
    for relative, content in files.items():
        path = attempt / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")


def _git(root: Path, *args: str) -> str:
    return subprocess.check_output(["git", "-C", str(root), *args], text=True).strip()


if __name__ == "__main__":
    raise SystemExit(main())
