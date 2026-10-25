"""The three session-identity rules, each expressed as a check rather than prose.

`session-identity-from-named-agent` and `no-hardcoded-agent` both forbid
something — naming a host's variable outside wfctl's one table, deriving the
identity, reading the answer out of the log by hand — and a rule that only
forbids has nothing that goes red when it is broken.
`a-rule-is-expressed-as-a-check` asks for the check to live in an artifact the
work already produces, which is what these are.

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
# it is that wfctl reads no host variable outside its agent table, and a fourth
# host appearing anywhere else must fail this without anyone remembering to add it.
_HOST_SESSION_VAR = re.compile(
    r"\b(?!WFCTL_)[A-Z][A-Z0-9]*(?:_[A-Z0-9]+)*_SESSION(?:_ID)?\b"
)


def _python_sources() -> list[Path]:
    return sorted(SOURCE.rglob("*.py"))


def _is_table_entry(path: Path, line: str) -> bool:
    from wfctl._session import AGENT_SESSION_VARIABLES

    return path.name == "_session.py" and any(
        line.strip() == f'"{agent}": "{variable}",'
        for agent, variable in AGENT_SESSION_VARIABLES.items()
    )


def test_host_session_variables_are_named_only_in_the_agent_table() -> None:
    """`session-identity-from-named-agent` lets wfctl name a host's variable in
    one place, keyed by the agent `WFCTL_AGENT` names.

    A second place is a probe. One `os.environ.get(...)` of a host variable added
    elsewhere as a convenience fallback would read it whatever agent the developer
    named, which is the nested-agent mistake the record rejects. Nothing else here
    would notice: every behavioural test would go on passing, because the value it
    returns is a perfectly good identity.
    """
    offenders = [
        f"{path.relative_to(SOURCE)}:{n}: {line.strip()}"
        for path in _python_sources()
        for n, line in enumerate(path.read_text().splitlines(), 1)
        if _HOST_SESSION_VAR.search(line) and not _is_table_entry(path, line)
    ]
    assert not offenders, "wfctl reads a session variable it does not own:\n" + "\n".join(
        offenders
    )


def test_start_session_names_no_host_variable(shipped_skill: Path) -> None:
    """FR-013 and `no-hardcoded-agent`: committed config names no host.

    The skill is committed, so a variable named in it would ship to every
    project that installs wfctl and be wrong in all but one of them. The
    `${VAR:+--flag "$VAR"}` shape is what `--agent` already uses for the same
    reason. The skill leaves the identity to the environment variable, so it
    names no host and the unset case is a no-op.
    """
    text = (shipped_skill / "skills" / "start-session" / "SKILL.md").read_text()

    assert "wfctl start && wfctl doctor" in text
    assert not _HOST_SESSION_VAR.search(text)


def test_start_session_line_passes_no_shell_expanded_flag(shipped_skill: Path) -> None:
    """The line an agent pastes into the user's shell must not split on `${VAR:+…}`.

    The old line carried `${WFCTL_SESSION_ID:+--session-id "$WFCTL_SESSION_ID"}`.
    zsh does not word-split a parameter expansion, so with the variable set
    `wfctl start` received the single argument `--session-id abc` and exited 2,
    and nobody saw it because the variable was unset everywhere it was tried
    (#537). `wfctl start` reads the variable through typer's `envvar`, so the
    flag was never needed.
    """
    text = (shipped_skill / "skills" / "start-session" / "SKILL.md").read_text()
    command_lines = [
        ln for ln in text.splitlines()
        if re.match(r"\s*(uv run )?wfctl start\b", ln)
    ]

    assert command_lines
    assert not [ln for ln in command_lines if ":+" in ln or "--session-id" in ln]


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
