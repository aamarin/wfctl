"""What `status` says about the grant, in every state and never nothing (#280).

`auto_approve` prints a line only when it is on, because absence is its default
and a notice about the ordinary case is noise. This one cannot copy that. A
wfctl that says nothing when the answer is *refused* is indistinguishable from a
wfctl too old to have heard of the question, and this repo already lives with
that confusion between its two installed copies — which is what FR-003 is about.
"""
from __future__ import annotations

import json
import types

from typer.testing import CliRunner

from wfctl._session import NotifyGrant, record_notify_resolved
from wfctl.cli import _NOTIFY_LINES, _notify_line, app

runner = CliRunner()

REFUSALS = ["unset", "deny", "unreadable", "corrupt", "trunk"]


def _resolve(agent_dir, source: str, granted: bool = False) -> None:
    record_notify_resolved(agent_dir, NotifyGrant(granted, source), "418-storyctl")


def _payload() -> dict:
    return json.loads(runner.invoke(app, ["status", "--json"]).output)


def test_both_keys_are_present_and_false_in_every_refused_state(
    storyctl_dir: types.SimpleNamespace,
) -> None:
    """FR-004. Present-and-false, never omitted.

    A consumer that reads a missing key as false cannot tell a refusal from a
    wfctl that predates the question, so the two must not look alike on the
    wire. Asserted per source rather than once, because the verdict is shared
    and the source is the part that varies.
    """
    for source in REFUSALS:
        _resolve(storyctl_dir.agent_dir, source)
        payload = _payload()
        assert payload["notify"] is False, source
        assert payload["notify_source"] == source


def test_the_granted_payload_names_where_the_authority_came_from(
    storyctl_dir: types.SimpleNamespace,
) -> None:
    """FR-005 on the wire. A bare boolean cannot say which surface answered, and
    the two can disagree — a reader resolving a surprise needs to know which."""
    _resolve(storyctl_dir.agent_dir, "label", granted=True)
    assert _payload() | {"notify": True, "notify_source": "label"} == _payload()

    _resolve(storyctl_dir.agent_dir, "local", granted=True)
    assert _payload()["notify_source"] == "local"


def test_a_payload_with_no_resolution_recorded_still_carries_both_keys(
    storyctl_dir: types.SimpleNamespace,
) -> None:
    """The state a branch is in before `wfctl start` has ever run on it.

    Refused is the honest answer there rather than a fallback — nobody has
    granted anything to a feature nobody has opened a session on — and the keys
    are present for the same reason they are present everywhere else.
    """
    payload = _payload()
    assert payload["notify"] is False
    assert payload["notify_source"] == "unset"


def test_status_prints_a_line_in_every_state_and_never_silence(
    storyctl_dir: types.SimpleNamespace,
) -> None:
    """FR-003. The failure this guards is a refusal that looks like an old wfctl.

    `NO_COLOR` is pinned by `conftest.py`; without it rich colorizes on the
    terminal and these assertions become machine-dependent.
    """
    for source in REFUSALS + ["label", "local"]:
        _resolve(storyctl_dir.agent_dir, source, granted=source in ("label", "local"))
        output = runner.invoke(app, ["status"]).output
        assert _notify_line(source, "418") in output, source


def test_the_refusals_are_distinguishable_from_each_other(
    storyctl_dir: types.SimpleNamespace,
) -> None:
    """Five sources, five lines. They resolve identically and are not one event:
    only two of them are anybody's decision, and filing a failed read as a person
    withholding authority is what FR-015 exists to prevent."""
    lines = {_notify_line(source, "418") for source in REFUSALS}
    assert len(lines) == len(REFUSALS)
    assert all(line.startswith("will not notify anyone") for line in lines)


def test_every_line_fits_on_one_terminal_line(
    storyctl_dir: types.SimpleNamespace,
) -> None:
    """The property the whole wording was chosen for, and the one a longer line
    silently destroys.

    `status` is glanced at. Rich wraps at the terminal width, so a line a few
    characters too long arrives as two — and the second half, read alone, is a
    fragment. The trunk wording was rewritten once already for exactly this: it
    named the rule in full, wrapped at 80, and stopped being scannable.

    72 rather than 80: the console adds no prefix here, but a line sitting one
    character inside the limit is a line the next edit breaks.
    """
    for source, line in _NOTIFY_LINES.items():
        assert len(line) <= 72, (source, len(line))
    assert len(_notify_line("label", "9999")) <= 72


def test_the_granted_line_names_the_issue_the_label_is_on(
    storyctl_dir: types.SimpleNamespace,
) -> None:
    """"You allowed it on the issue" without saying which issue sends the reader
    looking for it. The other granted surface has no issue to name."""
    assert "#418" in _notify_line("label", "418")
    assert _notify_line("local", "418") == _NOTIFY_LINES["local"]


def test_an_unknown_source_reads_as_refused_rather_than_as_nothing(
    storyctl_dir: types.SimpleNamespace,
) -> None:
    """A verdict this renderer has not been taught still has a safe rendering.
    Falling through to silence would reintroduce exactly what FR-003 forbids."""
    assert _notify_line("something-new", "418") == _NOTIFY_LINES["unset"]


def test_no_tracker_stderr_reaches_the_console(
    storyctl_dir: types.SimpleNamespace,
) -> None:
    """`status` is glanced at and has to stay one line; an unbounded stderr wraps
    and stops being scannable. The detail belongs to the event log, which is
    opened by someone already debugging."""
    stderr = "gh: HTTP 401 Bad credentials\nrun `gh auth login`\nsee: https://x/y"
    record_notify_resolved(
        storyctl_dir.agent_dir, NotifyGrant(False, "unreadable", stderr), "418-storyctl"
    )
    output = runner.invoke(app, ["status"]).output
    assert _NOTIFY_LINES["unreadable"] in output
    assert "401" not in output
    assert "gh auth login" not in output


def test_a_second_start_that_resolved_the_same_answer_appends_nothing(
    storyctl_dir: types.SimpleNamespace,
) -> None:
    """`/start-session` runs `wfctl start` on every handoff, so an unconditional
    append would grow the log with lines repeating the previous one.

    The first resolution is still written even when it finds nothing — "nobody
    has opened a session here" and "a session asked and was told no" are the same
    verdict and not the same fact, and only the log can tell them apart.
    """
    runner.invoke(app, ["start"])
    after_first = (storyctl_dir.agent_dir / "events.jsonl").read_text()
    assert "notify-resolved" in after_first

    runner.invoke(app, ["start"])
    assert (storyctl_dir.agent_dir / "events.jsonl").read_text() == after_first


def test_a_changed_answer_is_recorded_on_a_later_start(
    storyctl_dir: types.SimpleNamespace,
) -> None:
    """The other half of the rule above, and the one that would fail silently.

    Suppressing the repeat must not suppress a change: a label added between
    sessions, or a flag typed on a session that was already open, is exactly the
    event worth having in the log.
    """
    from wfctl._session import grant_notify

    runner.invoke(app, ["start"])
    grant_notify(storyctl_dir.agent_dir, "granted", "418-storyctl")
    runner.invoke(app, ["start"])

    log = (storyctl_dir.agent_dir / "events.jsonl").read_text().splitlines()
    resolved = [json.loads(x) for x in log if '"notify-resolved"' in x]
    assert [r["source"] for r in resolved] == ["unset", "local"]
    assert resolved[-1]["granted"] is True


def test_status_on_the_trunk_says_so_before_any_session_has_started(
    storyctl_dir: types.SimpleNamespace, monkeypatch,
) -> None:
    """The one place the read-back answer is not the right one.

    Nothing has resolved anything on a fresh trunk, so the recorded answer is the
    `unset` default — which rendered as "nobody has allowed it for this work" and
    sent the reader looking for the flag that would fix it. There is none, and
    the trunk line exists to say so. `on_trunk` is a local git call, so the
    round-trip argument that keeps the label read out of `status` does not reach
    this one.
    """
    import subprocess

    trunk = subprocess.run(
        ["git", "-C", str(storyctl_dir.repo_root), "branch", "--show-current"],
        capture_output=True, text=True, check=True,
    ).stdout.strip()
    monkeypatch.setenv("WFCTL_BRANCH", trunk)

    assert _NOTIFY_LINES["trunk"] in runner.invoke(app, ["status"]).output
    assert _payload()["notify_source"] == "trunk"
    assert _payload()["notify"] is False


def test_start_records_the_answer_the_rest_of_the_run_reads_back(
    storyctl_dir: types.SimpleNamespace,
) -> None:
    """FR-014's "once" is `wfctl start`, and this is the round trip.

    Resolving on each command instead would put a tracker call inside every
    `wfctl status` — dozens a session, all returning the same answer. The
    assertion is that `status` reports what `start` decided, without deciding
    anything itself.
    """
    result = runner.invoke(app, ["start"])
    assert _NOTIFY_LINES["unset"] in result.output

    log = (storyctl_dir.agent_dir / "events.jsonl").read_text().splitlines()
    resolved = [json.loads(line) for line in log if "notify-resolved" in line]
    assert resolved[-1]["granted"] is False
    assert resolved[-1]["source"] == "unset"
    assert _payload()["notify_source"] == "unset"
