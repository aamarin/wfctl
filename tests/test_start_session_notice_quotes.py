"""`start-session` routes on words `doctor` prints, so the words are a contract.

The repair reference that step 1 opens on a non-green `doctor` tells the two
dim `ℹ` notices apart by quoting a fragment of each: delete nothing on one,
install the agent layer on the other. Nothing else
distinguishes them: they share a marker and both leave the exit code alone.
Reword either notice in `cli.py` and the routing stops discriminating without
failing anything — the skill still reads well, and an agent following it finds
no rule for the line on screen. That is #254's defect one indirection over, and
it is visible in artifacts this repo already produces, which is what
`a-rule-is-expressed-as-a-check` asks of a rule before it ships as prose.
"""
import re
from importlib.resources import files
from pathlib import Path

import pytest

# Resolved through `files("wfctl")` for the same reason as
# `test_skill_cross_references`: conftest's autouse `bundle` fixture repoints
# `install.BUNDLE_ROOT` at a fake tree, and the real shipped pair is the subject.
_WFCTL = Path(str(files("wfctl")))
# The quotes sit with the rest of the repair guidance, in the file a session
# opens only when `doctor` prints something other than a ✓.
_REPAIR = _WFCTL / "agents" / "skills" / "start-session" / "references" / "doctor-repair.md"

# Both notices are built from adjacent string literals, so the fragment a reader
# sees on one line of output spans two lines of source. Joining the seams is what
# lets one substring check stand in for running the command.
_SEAM = re.compile(r'"\s*\n\s*f?"')

# The fragment the reference quotes of each notice, verbatim.
_QUOTED = (
    "not on record under a directory wfctl installs into",
    "no agent layer — .agents/ only",
)


def test_the_repair_reference_quotes_the_words_doctor_actually_prints() -> None:
    source = _SEAM.sub("", (_WFCTL / "cli.py").read_text())
    absent = [fragment for fragment in _QUOTED if fragment not in source]
    assert not absent, f"quoted in start-session, not printed by doctor: {absent}"


def test_the_repair_reference_still_quotes_both_notices() -> None:
    if not _REPAIR.is_file():
        pytest.fail(f"start-session ships no repair reference at {_REPAIR}")
    reference = _REPAIR.read_text()
    absent = [fragment for fragment in _QUOTED if fragment not in reference]
    assert not absent, f"doctor prints it, start-session no longer routes on it: {absent}"
