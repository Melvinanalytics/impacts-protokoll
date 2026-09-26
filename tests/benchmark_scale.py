"""Explicit file-count characterization; no timing threshold or concurrency claim.

Run from complete source with the test extra installed. Setup and initial hashing
are outside timed intervals. Each validation uses a fresh interpreter but retains
the operating system's file cache. Results describe this workload and machine only.
"""

import argparse
import hashlib
from importlib.metadata import version
import json
import os
from pathlib import Path
import platform
import statistics
import subprocess
import sys
from tempfile import TemporaryDirectory
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "src"))

from impacts_protocol import surface_hash
from tests.c_owner_support import committed_workspace, make_attempt, write_run
from tests.support import git, read_context, replace_context


def source_identity() -> dict[str, str]:
    paths = [*sorted((ROOT / "src/impacts_protocol").glob("*.py")),
             *sorted((ROOT / "02_protocol/schemas").glob("*.json")),
             ROOT / "pyproject.toml", Path(__file__).resolve(),
             ROOT / "tests/support.py", ROOT / "tests/c_owner_support.py"]
    return {path.relative_to(ROOT).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest()
            for path in paths}


def measure(base: Path, count: int, repetitions: int) -> dict:
    root, _ = committed_workspace(base)
    step = root / "applications/video/produktion/start/CONTEXT.md"
    definition = read_context(step)
    definition["eingaben"] = ["input/items"]
    replace_context(step, definition)
    git(root, "add", "applications")
    git(root, "commit", "-qm", "declare aggregate input")
    revision = git(root, "rev-parse", "HEAD:applications/video")
    run = root / "vorgaenge/video-001"
    attempt = make_attempt(run, "start", 1)
    (attempt / "input/items").mkdir()
    payload = b"synthetic scale input\n"
    for index in range(count):
        (attempt / "input/items" / f"item-{index:06}.txt").write_bytes(payload)
    digest = surface_hash(attempt, ["input/items"])
    write_run(root, "video-001", revision, [{
        "arbeitsschritt_ref": "arbeitsschritt:start", "versuch": 1,
        "status": "aktiv", "eingabe_hash": digest,
    }])
    environment = {**os.environ, "PYTHONPATH": str(ROOT / "src"),
                   "PYTHONDONTWRITEBYTECODE": "1"}
    observations = []
    for _ in range(repetitions):
        start = time.perf_counter()
        result = subprocess.run(
            [sys.executable, "-m", "impacts_protocol.cli", "validate", str(root)],
            env=environment, capture_output=True, text=True, timeout=300,
        )
        elapsed = time.perf_counter() - start
        if result.returncode or result.stdout or result.stderr:
            raise RuntimeError(f"Validation changed: {result.returncode}: {result.stdout} {result.stderr}")
        observations.append(elapsed)
    return {"input_files": count, "input_bytes": count * len(payload),
            "application_files": 4, "runs": 1, "attempts": 1,
            "surface_digest": digest, "seconds": observations,
            "median_seconds": statistics.median(observations)}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sizes", nargs="+", type=int, default=[1000, 10000, 100000])
    parser.add_argument("--repetitions", type=int, default=3)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.repetitions < 3 or not args.sizes or any(size < 1 for size in args.sizes):
        parser.error("positive file counts and at least three repetitions required")
    commit = git(ROOT, "rev-parse", "HEAD")
    dirty = git(ROOT, "status", "--porcelain")
    sources = source_identity()
    results = []
    with TemporaryDirectory(prefix="impacts-scale-") as directory:
        for size in args.sizes:
            result = measure(Path(directory) / str(size), size, args.repetitions)
            results.append(result)
            print(json.dumps(result), flush=True)
    if source_identity() != sources:
        raise RuntimeError("Measured source changed during the benchmark; discard this round")
    report = {"source_commit": commit, "working_tree_changes": dirty.splitlines(),
              "source_sha256": sources,
              "package_metadata_version": version("impacts-protocol"),
              "dependencies": {name: version(name) for name in ("PyYAML", "jsonschema", "referencing")},
              "python": platform.python_version(), "os": platform.system(),
              "machine": platform.machine(), "repetitions": args.repetitions,
              "workload": "one active run; fixed Application; aggregate raw-byte input hashing",
              "cache": "fresh interpreter; OS file cache retained",
              "claim_limit": "descriptive scale only; no before/after or concurrent-writer guarantee",
              "results": results}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
