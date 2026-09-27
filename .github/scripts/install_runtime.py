#!/usr/bin/env python3
"""Install this checkout with its hash-locked Linux CPython 3.11 dependencies.

Scope: CPython 3.11 on Linux x86_64 with glibc 2.17 or newer. The recipe pins
dependency wheel bytes and uses this checkout's source. Record its Git commit.
Python, pip, publisher identity, and build provenance are outside this boundary.
"""

from __future__ import annotations

import os
from pathlib import Path
import platform
import re
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[2]
LOCK = ROOT / ".github/runtime-linux-cp311-x86_64.txt"


def check_target() -> None:
    if sys.version_info[:2] != (3, 11) or platform.python_implementation() != "CPython":
        raise SystemExit("install recipe supports CPython 3.11 only")
    if sys.prefix == sys.base_prefix:
        raise SystemExit("install recipe must run inside a disposable virtual environment")
    if platform.system() != "Linux" or platform.machine().lower() not in {"x86_64", "amd64"}:
        raise SystemExit("install recipe supports Linux x86_64 only")
    libc, version = platform.libc_ver()
    match = re.fullmatch(r"(\d+)\.(\d+)(?:\.\d+)?", version)
    if libc != "glibc" or match is None or tuple(map(int, match.groups())) < (2, 17):
        raise SystemExit("install recipe requires glibc 2.17 or newer")


def run() -> None:
    check_target()
    if not LOCK.is_file():
        raise SystemExit(f"hash lock is missing: {LOCK}")

    # Ignore ambient pip configuration so an extra index or find-links source
    # cannot act as an unapproved fallback. The only dependency index is PyPI.
    env = {key: value for key, value in os.environ.items() if not key.upper().startswith("PIP_")}
    env["PIP_CONFIG_FILE"] = os.devnull
    subprocess.run(
        [
            sys.executable, "-m", "pip", "install", "--disable-pip-version-check",
            "--index-url", "https://pypi.org/simple", "--only-binary=:all:",
            "--require-hashes", "--force-reinstall", "-r", str(LOCK),
        ],
        cwd=ROOT,
        env=env,
        check=True,
    )
    subprocess.run(
        [
            sys.executable, "-m", "pip", "install", "--disable-pip-version-check",
            "--no-deps", "--no-build-isolation", "--force-reinstall", "--editable", str(ROOT),
        ],
        cwd=ROOT,
        env=env,
        check=True,
    )


if __name__ == "__main__":
    run()
