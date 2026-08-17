"""Assert an installed wfctl actually carries the vendored trees.

Run with the interpreter of a *clean, non-editable* install, from the repo root:

    rm -rf build dist wfctl.egg-info
    uv build --wheel
    uv venv /tmp/wheel-env
    VIRTUAL_ENV=/tmp/wheel-env uv pip install dist/*.whl
    /tmp/wheel-env/bin/python .github/scripts/check_wheel_contents.py

The `rm -rf` matters locally and is why CI, on a fresh checkout, does not need it.
`build_py` copies with `update=1`, so a `chmod` — which leaves mtime alone — is
skipped and the wheel keeps the stale mode; and `wfctl.egg-info/SOURCES.txt`
re-includes files a narrowed `package-data` glob no longer matches. Both make a
deliberately broken build come out green.

The test suite cannot make this check. It runs against the source tree, where
`wfctl/agents/` and `wfctl/specify/` are present and executable whether or not
the wheel ships them — so a broken `[tool.setuptools.package-data]` glob is
invisible until a user installs and gets nothing. An *editable* install has the
same blind spot, which is why the instructions above build and install a wheel
rather than running `uv sync`.

The comparison is against `git ls-files`, not a hardcoded list: the question is
whether everything committed as bundle content survived packaging, and a list
maintained by hand would answer a different, staler question. Which files are
executable comes from git too, for the same reason — see the parse below.
"""
from __future__ import annotations

import os
import subprocess
import sys
from importlib.resources import files
from pathlib import Path

from wfctl._bundle import TREES

installed_root = Path(str(files("wfctl")))
repo_root = Path(__file__).resolve().parents[2]

if installed_root == repo_root / "wfctl":
    sys.exit(
        f"FAIL: wfctl resolved to the source tree at {installed_root}.\n"
        "  This check only means something against a clean wheel install — run it\n"
        "  with the venv's interpreter, from a directory that is not the repo root."
    )

listing = subprocess.run(
    ["git", "-C", str(repo_root), "ls-files", "-sz", *(f"wfctl/{tree}" for tree in TREES)],
    capture_output=True,
    text=True,
    check=True,
).stdout.split("\0")

# `-s` so the mode comes from git rather than from the filename. Every executable
# in the tree today ends in `.sh`, but that is upstream's habit, not a rule — an
# executable helper named anything else would ship 644 straight through a suffix
# check, which is the failure this whole job exists to catch.
#
# `-z` for the record separator, and the tab git puts before the path: together
# they keep a path containing a space or a non-ASCII character in one piece,
# where splitting on whitespace tears it in two and C-quoting mangles it.
tracked = {}
for record in listing:
    if not record:
        continue
    metadata, _, relative = record.partition("\t")
    tracked[relative] = metadata.split()[0]

# A vacuous pass is the failure mode this check exists to prevent, so the empty
# case is an error rather than "nothing to verify".
if not tracked:
    sys.exit(f"FAIL: git tracks no files under {', '.join(f'wfctl/{t}' for t in TREES)}")

missing = []
not_executable = []
for relative, mode in tracked.items():
    target = installed_root / Path(relative).relative_to("wfctl")
    if not target.is_file():
        missing.append(relative)
    elif mode == "100755" and not os.stat(target).st_mode & 0o111:
        # A wheel preserves whatever mode git recorded, so a file committed 755
        # arriving 644 means packaging dropped it — and every speckit command
        # shells out to these, so the runtime breaks at the first invocation.
        not_executable.append(relative)

if missing or not_executable:
    for relative in missing:
        print(f"  MISSING: {relative}", file=sys.stderr)
    for relative in not_executable:
        print(f"  NOT EXECUTABLE: {relative}", file=sys.stderr)
    sys.exit(
        f"FAIL: {len(missing)} missing, {len(not_executable)} not executable "
        f"out of {len(tracked)} tracked bundle files, in {installed_root}"
    )

print(f"OK: {len(tracked)} bundled files present and correctly moded in {installed_root}")
