"""Assert `install-skills` puts the shipped bundle into a repo byte for byte.

The end-to-end half of the wheel job. Run with the interpreter of a *clean,
non-editable* install, from anywhere but the repo root:

    uv build --wheel
    uv venv /tmp/wheel-env
    VIRTUAL_ENV=/tmp/wheel-env uv pip install dist/*.whl
    git init /tmp/scratch-repo
    cd /tmp/scratch-repo && /tmp/wheel-env/bin/wfctl install-skills --yes
    /tmp/wheel-env/bin/python .github/scripts/check_installed_tree.py /tmp/scratch-repo

`check_wheel_contents.py` asks whether the wheel *carries* the trees. This asks
whether the command copies them out intact, which is a different failure: a
target pair pointing at a directory that no longer exists installs nothing and
still exits 0, and `shutil.copy2` preserving the exec bit is a property of the
call, not of the wheel.

Target pairs are imported rather than restated. Restating them here would mean a
repointed source is compared against the string this file happens to hold, so the
check would pass on exactly the change that breaks the install.
"""
from __future__ import annotations

import filecmp
import os
import sys
from pathlib import Path

from wfctl._bundle import BUNDLE_ROOT
from wfctl.cli import _BASE_TARGETS, _RUNTIME_TARGETS

if len(sys.argv) != 2:
    sys.exit(f"usage: {Path(sys.argv[0]).name} <installed-repo-root>")

repo_root = Path(sys.argv[1]).resolve()
source_root = Path(__file__).resolve().parents[2]

if BUNDLE_ROOT == source_root / "wfctl":
    sys.exit(
        f"FAIL: wfctl resolved to the source tree at {BUNDLE_ROOT}.\n"
        "  Comparing the source tree against a copy of itself proves nothing about\n"
        "  the wheel — run this with the venv's interpreter, outside the repo root."
    )

failures: list[str] = []
compared = 0

# Only the layers a bare `install-skills` writes. Agent layers copy the same
# sources to more destinations, and the config sources are seed-once — neither
# adds a way for this comparison to fail that these two do not already cover.
for source_rel, dest_rel in [*_BASE_TARGETS, *_RUNTIME_TARGETS]:
    source = BUNDLE_ROOT / source_rel
    dest = repo_root / dest_rel
    if not source.is_dir():
        failures.append(f"NO SOURCE: {source_rel} is not a directory in {BUNDLE_ROOT}")
        continue
    if not dest.is_dir():
        failures.append(f"NOT INSTALLED: {dest_rel} — nothing copied to {dest}")
        continue

    for shipped in sorted(p for p in source.rglob("*") if p.is_file()):
        relative = shipped.relative_to(source)
        installed = dest / relative
        compared += 1
        if not installed.is_file():
            failures.append(f"MISSING: {dest_rel}/{relative}")
        elif not filecmp.cmp(shipped, installed, shallow=False):
            failures.append(f"DIFFERS: {dest_rel}/{relative}")
        elif os.stat(shipped).st_mode & 0o111 and not os.stat(installed).st_mode & 0o111:
            # `shutil.copy2` carries the mode across; `shutil.copy` would not.
            # Every speckit skill shells out to `.specify/scripts/*.sh`, so losing
            # the bit here breaks them at the first invocation with a bare
            # "permission denied" and no hint that the install is what did it.
            failures.append(f"NOT EXECUTABLE: {dest_rel}/{relative}")

# An empty comparison is the failure this exists to catch, not a pass.
if not compared:
    failures.append(f"NOTHING COMPARED: no files under any source in {BUNDLE_ROOT}")

if failures:
    for line in failures:
        print(f"  {line}", file=sys.stderr)
    sys.exit(f"FAIL: {len(failures)} problem(s) across {compared} installed files")

print(f"OK: {compared} files installed into {repo_root} byte-identical, modes intact")
