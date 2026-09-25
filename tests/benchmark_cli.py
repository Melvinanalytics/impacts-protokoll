"""Explicit local before/after CLI benchmark; no timing threshold is asserted.

Example: python3.14 tests/benchmark_cli.py --base SOURCE --candidate SOURCE \
    --output /tmp/impacts-benchmark.json

Both SOURCE paths must be complete checkouts. Setup is outside measured intervals.
Fresh means a new Python interpreter, not a cleared operating-system file cache.
"""

import argparse
from collections import Counter
import hashlib
from importlib import metadata
import json
import os
from pathlib import Path
import platform
import shlex
import shutil
import statistics
import subprocess
import sys
from tempfile import TemporaryDirectory
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "src"))
from impacts_protocol import init_workspace, surface_hash
from tests.support import git, read_context, replace_context, write_application, write_context, write_workstep


def _history_fixture(base: Path, commits: int, blobs: int, mode: str) -> Path:
    root = init_workspace(base / f"history-{commits}-{blobs}-{mode}")
    application = write_application(root / "applications" / "video")
    steps = ["start"] + [f"extra-{index:03}" for index in range(blobs)] + ["pruefen"]
    if blobs:
        production = application / "produktion"
        start = production / "start" / "CONTEXT.md"
        metadata = read_context(start)
        metadata["routen"] = {"weiter": f"arbeitsschritt:{steps[1]}"}
        replace_context(start, metadata)
    for index in range(blobs):
        next_step = steps[index + 2]
        write_workstep(application / "produktion", steps[index + 1],
                       routes={"weiter": f"arbeitsschritt:{next_step}"})
    git(root, "init", "-b", "main")
    git(root, "config", "user.email", "benchmark@example.invalid")
    git(root, "config", "user.name", "Benchmark")
    git(root, "add", ".")
    git(root, "commit", "-m", "initial")
    revisions = [git(root, "rev-parse", "HEAD:applications/video")]
    marker = application / "CONTEXT.md"
    original = marker.read_text(encoding="utf-8")
    for number in range(1, commits):
        marker.write_text(original + f"\nrevision {number:04}\n", encoding="utf-8")
        git(root, "add", "applications")
        git(root, "commit", "-m", f"revision {number:04}")
        revisions.append(git(root, "rev-parse", "HEAD:applications/video"))

    selected = [revisions[0]]
    if mode == "same":
        selected = [revisions[0]] * 10
    elif mode == "distinct":
        selected = [revisions[index * (commits - 1) // 9] for index in range(10)]
    for number, revision in enumerate(selected, 1):
        run = root / "vorgaenge" / f"video-{number:03}"
        entries = []
        for step in steps:
            attempt = run / step / "001"
            (attempt / "input").mkdir(parents=True)
            (attempt / "output").mkdir()
            (attempt / "input" / "auftrag.md").write_text("Eingabe", encoding="utf-8")
            (attempt / "output" / "ergebnis.md").write_text("Ausgabe", encoding="utf-8")
            entry = {"arbeitsschritt_ref": f"arbeitsschritt:{step}", "versuch": 1,
                     "status": "abgeschlossen", "eingabe_hash": surface_hash(attempt, ["input/auftrag.md"]),
                     "gewaehlte_route": "freigegeben" if step == "pruefen" else "weiter",
                     "ausgabe_hash": surface_hash(attempt, ["output/ergebnis.md"])}
            if step == "pruefen":
                entry["freigabe"] = {"by": "human:benchmark", "at": "2026-08-30T10:00:00+02:00"}
            entries.append(entry)
        write_context(run / "CONTEXT.md", {
            "type": "vorgang", "id": f"vorgang:video-{number:03}",
            "application_revision": f"git-tree:{revision}",
            "laufpfad": entries,
        }, "# Synthetic benchmark run")
    return root


def _yaml_fixture(base: Path) -> tuple[Path, Path]:
    root = init_workspace(base / "yaml-workspace")
    application = write_application(root / "applications" / "video")
    # Many schema-valid string items exercise YAML mapping and scalar construction.
    path = application / "CONTEXT.md"
    lines = path.read_text(encoding="utf-8").splitlines()
    extra = "\n".join(f"  - 'Acceptance item {index:04}: checked'" for index in range(2000))
    start = lines.index("  abnahme:")
    end = start + 1
    while end < len(lines) and lines[end].startswith("  - "):
        end += 1
    lines[start:end] = ["  abnahme:", extra]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return root, path


def _size(root: Path) -> dict:
    files = [path for path in root.rglob("*") if path.is_file() and ".git" not in path.parts]
    return {"files": len(files), "bytes": sum(path.stat().st_size for path in files)}


def _cases(base: Path, selected: list[str] | None) -> dict:
    small = init_workspace(base / "small")
    attempt = base / "attempt"
    attempt.mkdir()
    (attempt / "input.txt").write_bytes(b"synthetic benchmark\n")
    yaml_root, yaml_file = _yaml_fixture(base)
    cases = {
        "help": {"argv": ["--help"], "size": _size(small)},
        "template": {"argv": ["template", "arbeitsschritt"], "size": _size(small)},
        "init": {"argv": ["init", "{target}"], "size": _size(small)},
        "hash": {"argv": ["hash", str(attempt), "input.txt"], "size": _size(attempt)},
        "validate-small": {"argv": ["validate", str(small)], "size": _size(small)},
        "validate-yaml": {"argv": ["validate", str(yaml_root)], "size": _size(yaml_root)},
        "yaml-direct": {"yaml": str(yaml_file), "size": _size(yaml_root)},
    }
    for commits, blobs, mode in [(21, 0, "old"), (121, 0, "old"),
                                  (121, 0, "same"), (121, 0, "distinct"),
                                  (121, 20, "old"), (121, 20, "distinct")]:
        name = f"history-{commits}-{blobs}-{mode}"
        if selected is not None and name not in selected:
            continue
        root = _history_fixture(base, commits, blobs, mode)
        cases[name] = {
            "argv": ["validate", str(root)], "size": _size(root),
            "commits": commits, "blobs": blobs, "runs": 10 if mode != "old" else 1,
        }
    return cases


def _run(source: Path, case: dict, target: Path, trace: Path | None, wrapper: Path | None) -> dict:
    environment = os.environ.copy()
    environment["PYTHONPATH"] = str(source / "src")
    environment["PYTHONDONTWRITEBYTECODE"] = "1"
    if trace is not None:
        environment["PATH"] = str(wrapper) + os.pathsep + environment["PATH"]
        environment["IMPACTS_BENCH_GIT_TRACE"] = str(trace)
    if "yaml" in case:
        code = ("from impacts_protocol.io import load_frontmatter; "
                "import hashlib,json,sys,time; "
                "start=time.perf_counter_ns(); value=load_frontmatter(__import__('pathlib').Path(sys.argv[1])); "
                "elapsed=time.perf_counter_ns()-start; "
                "print(json.dumps({'elapsed_ns':elapsed,'digest':hashlib.sha256(repr(value).encode()).hexdigest()}))")
        command = [sys.executable, "-c", code, case["yaml"]]
    else:
        command = [sys.executable, "-m", "impacts_protocol.cli", *(
            str(target) if arg == "{target}" else arg for arg in case["argv"])]
    started = time.perf_counter_ns()
    process = subprocess.run(command, cwd=target.parent, env=environment, capture_output=True)
    elapsed = time.perf_counter_ns() - started
    stdout = process.stdout.decode("utf-8", errors="replace")
    stderr = process.stderr.decode("utf-8", errors="replace")
    if "yaml" in case and process.returncode == 0:
        normalized = (json.loads(stdout)["digest"], stderr)
    else:
        normalized = (stdout.replace(str(target), "<TARGET>"), stderr.replace(str(target), "<TARGET>"))
    return {"seconds": elapsed / 1e9, "parser_seconds": json.loads(stdout)["elapsed_ns"] / 1e9 if "yaml" in case and process.returncode == 0 else None,
            "exit": process.returncode, "stdout": normalized[0], "stderr": normalized[1],
            "command": command}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base", type=Path, required=True)
    parser.add_argument("--candidate", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--repetitions", type=int, default=10)
    parser.add_argument("--case", action="append", help="Select case; repeat option for several cases")
    args = parser.parse_args()
    if args.repetitions < 10:
        parser.error("at least 10 repetitions required")
    for source in (args.base, args.candidate):
        if not (source / "src/impacts_protocol/cli.py").is_file():
            parser.error(f"source checkout missing: {source}")
    args.base = args.base.resolve()
    args.candidate = args.candidate.resolve()
    git_path = shutil.which("git")
    with TemporaryDirectory(prefix="impacts-benchmark-") as directory:
        base = Path(directory)
        cases = _cases(base, args.case)
        names = args.case or list(cases)
        if any(name not in cases for name in names):
            parser.error(f"unknown case; choose from {list(cases)}")
        wrapper = base / "bin"
        wrapper.mkdir()
        executable = wrapper / "git"
        executable.write_text(f'#!/bin/sh\nprintf "%s\\n" "$*" >> "$IMPACTS_BENCH_GIT_TRACE"\nexec {shlex.quote(git_path)} "$@"\n')
        executable.chmod(0o755)
        evidence = {
            "environment": {"python": sys.version, "git": subprocess.check_output([git_path, "--version"], text=True).strip(),
                            "platform": platform.platform(), "dependencies": {name: metadata.version(name) for name in ("PyYAML", "jsonschema", "referencing")},
                            "clock": "time.perf_counter_ns; fresh interpreter, OS cache not cleared"},
            "sources": {label: {"path": str(path.resolve()), "revision": subprocess.check_output([git_path, "-C", str(path), "rev-parse", "HEAD"], text=True).strip(),
                               "dirty": bool(subprocess.check_output([git_path, "-C", str(path), "status", "--porcelain"], text=True).strip())}
                        for label, path in (("base", args.base), ("candidate", args.candidate))},
            "repetitions": args.repetitions, "cases": {},
        }
        for name in names:
            case = cases[name]
            records = {"base": [], "candidate": []}
            for index in range(args.repetitions):
                for label in (("base", "candidate") if index % 2 == 0 else ("candidate", "base")):
                    source = getattr(args, label)
                    target = base / f"init-{name}-{index}-{label}"
                    result = _run(source, case, target, None, None)
                    records[label].append(result)
                left, right = records["base"][-1], records["candidate"][-1]
                if (left["exit"], left["stdout"], left["stderr"]) != (right["exit"], right["stdout"], right["stderr"]):
                    raise AssertionError(f"{name} repetition {index}: behavior differs: {left!r} versus {right!r}")
                if left["exit"] != 0:
                    raise AssertionError(f"{name}: unexpected exit {left['exit']}: {left['stderr']}")
            counts = {}
            for label in ("base", "candidate"):
                trace = base / f"trace-{name}-{label}.txt"
                instrumented = _run(getattr(args, label), case, base / f"instrumented-{name}-{label}", trace, wrapper)
                if (instrumented["exit"], instrumented["stdout"], instrumented["stderr"]) != (
                    records[label][0]["exit"], records[label][0]["stdout"], records[label][0]["stderr"]
                ):
                    raise AssertionError(f"{name}: instrumented behavior differs")
                commands = trace.read_text().splitlines() if trace.exists() else []
                def verb(line):
                    parts = line.split()
                    while parts:
                        if parts[0] == "-C":
                            parts = parts[2:]
                        elif parts[0].startswith("-"):
                            parts = parts[1:]
                        else:
                            return parts[0]
                    return "<unknown>"
                counts[label] = {"total": len(commands), "by_command": dict(Counter(verb(line) for line in commands)), "raw": commands}
            summaries = {}
            for label in ("base", "candidate"):
                timings = [record["seconds"] for record in records[label]]
                parser_timings = [record["parser_seconds"] for record in records[label] if record["parser_seconds"] is not None]
                summaries[label] = {"raw_seconds": timings, "median_seconds": statistics.median(timings),
                                    "spread_seconds": max(timings) - min(timings),
                                    "parser_raw_seconds": parser_timings,
                                    "parser_median_seconds": statistics.median(parser_timings) if parser_timings else None,
                                    "git_processes_instrumented": counts[label],
                                    "exit": records[label][0]["exit"], "stdout_sha256": hashlib.sha256(records[label][0]["stdout"].encode()).hexdigest(),
                                    "command": records[label][0]["command"]}
            evidence["cases"][name] = {"fixture": {key: value for key, value in case.items() if key != "argv" and key != "yaml"}, "results": summaries}
            print(f"{name}: base {summaries['base']['median_seconds']:.4f}s, candidate {summaries['candidate']['median_seconds']:.4f}s; git {counts['base']['total']}/{counts['candidate']['total']}", flush=True)
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(json.dumps(evidence, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
