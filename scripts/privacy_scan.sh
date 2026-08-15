#!/usr/bin/env bash
set -euo pipefail

"${PYTHON:-python3}" - <<'PY'
import re
import sys
from pathlib import Path

ROOT = Path(".")
SKIP_DIRS = {".git", ".internal", ".mypy_cache", ".pytest_cache", ".ruff_cache", "build", "dist", "__pycache__"}
SKIP_SUFFIXES = {".pyc", ".whl", ".gz", ".zip"}
PATTERN = re.compile(
    r"(/Users/|/private/|/tmp/|"
    r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}|"
    r"API[_ -]?key|password|secret|token|BEGIN [A-Z ]*PRIVATE|sk-[A-Za-z0-9]{20,})",
    re.IGNORECASE,
)

matches = []
for path in sorted(ROOT.rglob("*")):
    if not path.is_file():
        continue
    if any(part in SKIP_DIRS for part in path.parts):
        continue
    if path.as_posix() == "scripts/privacy_scan.sh":
        continue
    if path.suffix in SKIP_SUFFIXES:
        continue
    try:
        text = path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        continue
    for line_number, line in enumerate(text.splitlines(), start=1):
        if PATTERN.search(line):
            matches.append(f"{path}:{line_number}: {line}")

if matches:
    print("Privacy scan found possible private material.")
    print("\n".join(matches))
    sys.exit(1)

print("No private patterns found.")
PY
