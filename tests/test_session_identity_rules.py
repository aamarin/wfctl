"""The three session-identity rules, each expressed as a check rather than prose.

`session-identity-comes-from-the-caller` and `no-hardcoded-agent` both forbid
something — naming a host's variable, deriving the identity, reading the answer
out of the log by hand — and a rule that only forbids has nothing that goes red
when it is broken. `a-rule-is-expressed-as-a-check` asks for the check to live in
an artifact the work already produces, which is what these are.

One file for three rules rather than three files for one test each: they share a
subject and a failure, and splitting them would put each rule where nobody looks
for the other two.
"""
from __future__ import annotations

import re
from pathlib import Path

import pytest

SOURCE = Path(__file__).resolve().parent.parent / "wfctl"
SKILLS = SOURCE / "agents"

# Spellings a host is known to use, plus the shape a new one would take. Matched
# as a pattern rather than a list because the point is not these three names —
# it is that wfctl never reads *any* variable it did not define, and a fourth
# host appearing must fail this without anyone remembering to add it.
_HOST_SESSION_VAR = re.compile(
    r"\b(?!WFCTL_)[A-Z][A-Z0-9]*(?:_[A-Z0-9]+)*_SESSION(?:_ID)?\b"
)


def _python_sources() -> list[Path]:
    return sorted(SOURCE.rglob("*.py"))


def test_no_host_session_variable_is_named_in_source() -> None:
    """wfctl stores an opaque value; naming a host's variable would derive one.

    The record's own argument is that a wrong guess about the host becomes a
    mapping to fix rather than a design to redo — which holds only while the
    mapping lives outside wfctl. One `os.environ.get("CLAUDE_CODE_SESSION_ID")`
    added as a convenience fallback would move it inside, and nothing else here
    would notice: every behavioural test would go on passing, because the value
    it returns is a perfectly good identity.
    """
    offenders = [
        f"{path.relative_to(SOURCE)}:{n}: {line.strip()}"
        for path in _python_sources()
        for n, line in enumerate(path.read_text().splitlines(), 1)
        if _HOST_SESSION_VAR.search(line)
    ]
    assert not offenders, "wfctl reads a session variable it does not own:\n" + "\n".join(
        offenders
    )


def test_start_session_names_no_host_variable(shipped_skill: Path) -> None:
    """FR-013 and `no-hardcoded-agent`: committed config names no host.

    The skill is committed, so a variable named in it would ship to every
    project that installs wfctl and be wrong in all but one of them. The
    `${VAR:+--flag "$VAR"}` shape is what `--agent` already uses for the same
    reason, and it is also what makes the unset case a no-op rather than a flag
    carrying an empty string.
    """
    text = (shipped_skill / "skills" / "start-session" / "SKILL.md").read_text()

    assert '${WFCTL_SESSION_ID:+--session-id "$WFCTL_SESSION_ID"}' in text
    assert not _HOST_SESSION_VAR.search(text)


def test_no_skill_reads_the_event_log_for_session_state(shipped_skill: Path) -> None:
    """FR-011: the session answer comes from wfctl, never from a hand-rolled read.

    A skill that greps `events.jsonl` for `start` lines is a second inference
    path over the same artifact, and `pipeline-state-is-one-payload` rejects that
    for the reason it is rejected everywhere else — the two drift, and the one
    nobody tests is the one that stays wrong.

    `start-session`'s stop-kind read is allowed because it asks a different
    question: which *kind* of stop the last session recorded, which decides a
    trunk branch's row and which no field on the payload carries.
    """
    allowed = {"start-session", "worktree-handoff", "using-wfctl"}
    offenders = [
        f"{path.relative_to(shipped_skill)}:{n}: {line.strip()}"
        for path in sorted(shipped_skill.rglob("*.md"))
        for n, line in enumerate(path.read_text().splitlines(), 1)
        if "events.jsonl" in line
        and not any(f"/{name}/" in str(path) for name in allowed)
    ]
    assert not offenders, (
        "a shipped skill reads the event log directly; ask wfctl instead:\n"
        + "\n".join(offenders)
    )


@pytest.fixture
def shipped_skill() -> Path:
    """The committed source tree, not an installed `.agents/`.

    `.agents/` is gitignored and rewritten by `install-skills`, so a check that
    read it would pass or fail on whichever wheel last ran — which is the
    failure `AGENTS.md` describes for `doctor` in this repo, and it would make
    these rules assertions about the developer's machine.
    """
    return SKILLS
