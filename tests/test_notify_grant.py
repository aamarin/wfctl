"""Who may tell people outside the repo, resolved once per run (#280).

Four states reach the same verdict — refused — and the tests here are mostly
about keeping them apart. Nobody granted it, someone turned it off, the stored
answer is unreadable, and the tracker could not be reached all mean the run does
not notify anyone; only the last two are failures, and filing either as a person
withholding authority is what FR-015 exists to prevent.

The grant is asserted from the *granted* side wherever the assertion would
otherwise pass against the default. A refusal test that never wrote a grant is a
test that passes on a resolver returning False unconditionally.
"""
from __future__ import annotations

import json
import types
from pathlib import Path

from wfctl._session import (
    NOTIFY_LABEL,
    NOTIFY_NAME,
    grant_notify,
    notify_grant,
    record_notify_action,
)


def _events(agent_dir: Path) -> list[dict]:
    log = agent_dir / "events.jsonl"
    return [json.loads(line) for line in log.read_text().splitlines()] if log.exists() else []


def _tracker(root: Path, labels: list[str] | None) -> None:
    """Point the repo at a backend whose `labels` verb is whatever we hand it.

    A shell command standing in for `gh` rather than a patched function: the
    read builds argv from the repo's own config and runs it, and a mock would
    skip the half of that this feature actually added. `None` declares a backend
    that does not implement the verb at all, which is how a tracker says it
    cannot answer.
    """
    (root / ".wf-skills-manifest.json").write_text(json.dumps({"tracker": "fake"}))
    trackers = root / ".agents" / "trackers"
    trackers.mkdir(parents=True, exist_ok=True)
    verbs = {} if labels is None else {"labels": labels}
    (trackers / "fake.json").write_text(json.dumps({"verbs": verbs}))


def _trunk(root: Path) -> str:
    """What the resolver itself would call the trunk, not what git checked out.

    Asking git for the current branch would pin the test to whatever
    `init.defaultBranch` happens to be on the machine running it; a repo whose
    default is neither main, master nor dev has no trunk as far as
    `_trunk_branch` is concerned, and the assertion below would then be about a
    branch the code never recognised.
    """
    from wfctl._paths import _trunk_branch

    trunk = _trunk_branch(root)
    assert trunk is not None, "fixture repo has no branch the resolver calls trunk"
    return trunk.rpartition("/")[2]


# --- the grid in data-model.md -------------------------------------------------

def test_nothing_granted_anywhere_is_unset_rather_than_denied(
    storyctl_dir: types.SimpleNamespace,
) -> None:
    """The default, and the distinction the whole file turns on.

    A missing label says nothing, not no. Collapsing `unset` into `deny` would
    make an ungranted feature indistinguishable from one somebody switched off,
    and only one of those is a decision anyone made.
    """
    root = storyctl_dir.repo_root
    got = notify_grant(storyctl_dir.agent_dir, root, "418-storyctl", "418")
    assert got.granted is False
    assert got.source == "unset"


def test_the_label_grants_when_no_local_answer_exists(
    storyctl_dir: types.SimpleNamespace,
) -> None:
    root = storyctl_dir.repo_root
    _tracker(root, ["printf", f"bug\n{NOTIFY_LABEL}\n"])
    got = notify_grant(storyctl_dir.agent_dir, root, "418-storyctl", "418")
    assert got.granted is True
    assert got.source == "label"


def test_a_local_deny_beats_a_present_label(
    storyctl_dir: types.SimpleNamespace,
) -> None:
    """The one cell of the grid where the two surfaces disagree.

    Written from the granted side on purpose: with no label configured this
    passes whatever the resolver does with `denied`.
    """
    root = storyctl_dir.repo_root
    _tracker(root, ["printf", f"{NOTIFY_LABEL}\n"])
    grant_notify(storyctl_dir.agent_dir, "denied")
    got = notify_grant(storyctl_dir.agent_dir, root, "418-storyctl", "418")
    assert got.granted is False
    assert got.source == "deny"


def test_a_local_grant_needs_no_second_opinion(
    storyctl_dir: types.SimpleNamespace,
) -> None:
    """Granted locally resolves without asking the tracker anything.

    The tracker here would fail if it were consulted, which is the assertion:
    FR-014 buys one round-trip per run and the common paths spend none.
    """
    root = storyctl_dir.repo_root
    _tracker(root, ["false"])
    grant_notify(storyctl_dir.agent_dir, "granted")
    got = notify_grant(storyctl_dir.agent_dir, root, "418-storyctl", "418")
    assert got.granted is True
    assert got.source == "local"


def test_a_backend_that_cannot_list_labels_falls_back_rather_than_failing(
    storyctl_dir: types.SimpleNamespace,
) -> None:
    """Declining the verb is how a backend says it cannot answer, and it is not
    a failure — the repo still grants through the local command (FR-012).

    The distinction this pins is between *nothing was asked* and *the answer did
    not arrive*: only the second is an unreadable grant, and reporting the first
    as one would file a tracker that never had the feature as a tracker that
    broke.
    """
    root = storyctl_dir.repo_root
    _tracker(root, None)
    got = notify_grant(storyctl_dir.agent_dir, root, "418-storyctl", "418")
    assert got.granted is False
    assert got.source == "unset"

    grant_notify(storyctl_dir.agent_dir, "granted")
    assert notify_grant(storyctl_dir.agent_dir, root, "418-storyctl", "418").source == "local"


def test_a_label_is_matched_whole_and_never_as_a_substring(
    storyctl_dir: types.SimpleNamespace,
) -> None:
    """One label per line, compared exactly. A backend listing a neighbouring
    label whose name contains this one must not grant it."""
    root = storyctl_dir.repo_root
    _tracker(root, ["printf", f"{NOTIFY_LABEL}-proposed\nneeds-{NOTIFY_LABEL}\n"])
    got = notify_grant(storyctl_dir.agent_dir, root, "418-storyctl", "418")
    assert got.granted is False
    assert got.source == "unset"


def test_no_tracker_configured_leaves_the_grant_expressible(
    storyctl_dir: types.SimpleNamespace,
) -> None:
    """FR-012 — the local surface still answers where there is no label to read."""
    root = storyctl_dir.repo_root
    grant_notify(storyctl_dir.agent_dir, "granted")
    got = notify_grant(storyctl_dir.agent_dir, root, "418-storyctl", None)
    assert got.granted is True
    assert got.source == "local"


# --- reads that failed, which are not reads that said no -----------------------

def test_an_unreachable_tracker_is_unreadable_and_not_absent(
    storyctl_dir: types.SimpleNamespace,
) -> None:
    """FR-015. The read decides the whole run, so it must not read as a refusal.

    The detail carries the backend's stderr because the console line for this
    state is fixed; this is the only place the underlying error survives.
    """
    root = storyctl_dir.repo_root
    _tracker(root, ["sh", "-c", "echo 'HTTP 401 Bad credentials' >&2; exit 1"])
    got = notify_grant(storyctl_dir.agent_dir, root, "418-storyctl", "418")
    assert got.granted is False
    assert got.source == "unreadable"
    assert "401" in (got.detail or "")


def test_invalid_utf8_in_the_stored_grant_reads_as_corrupt(
    storyctl_dir: types.SimpleNamespace,
) -> None:
    """One of the three shapes `auto_approve` guards, and the reason it uses
    `ValueError`: an invalid byte raises `UnicodeDecodeError`, not `OSError`."""
    (storyctl_dir.agent_dir / NOTIFY_NAME).write_bytes(b'{"state": "\xff"}')
    got = notify_grant(storyctl_dir.agent_dir, storyctl_dir.repo_root, "418-storyctl", None)
    assert got.granted is False
    assert got.source == "corrupt"


def test_a_json_scalar_where_an_object_was_expected_reads_as_corrupt(
    storyctl_dir: types.SimpleNamespace,
) -> None:
    """`null`, `3` and `[]` all parse and have no `.get` — the shape that bites."""
    (storyctl_dir.agent_dir / NOTIFY_NAME).write_text("3")
    got = notify_grant(storyctl_dir.agent_dir, storyctl_dir.repo_root, "418-storyctl", None)
    assert got.granted is False
    assert got.source == "corrupt"


def test_a_missing_file_is_unset_and_a_corrupt_one_is_not(
    storyctl_dir: types.SimpleNamespace,
) -> None:
    """Where this reader parts company with `auto_approve`, which folds the two
    together because both mean False to it. Here absent leaves the label free to
    answer and corrupt does not, so they cannot be one source."""
    root, agent_dir = storyctl_dir.repo_root, storyctl_dir.agent_dir
    _tracker(root, ["printf", f"{NOTIFY_LABEL}\n"])
    assert notify_grant(agent_dir, root, "418-storyctl", "418").source == "label"
    (agent_dir / NOTIFY_NAME).write_text("{")
    assert notify_grant(agent_dir, root, "418-storyctl", "418").source == "corrupt"


def test_an_unknown_state_string_is_corrupt_rather_than_unset(
    storyctl_dir: types.SimpleNamespace,
) -> None:
    """Something wrote the file. Reading a typo the way an absent file reads
    would let it fall through to the label and grant on a value nobody meant."""
    (storyctl_dir.agent_dir / NOTIFY_NAME).write_text(json.dumps({"state": "grantd"}))
    got = notify_grant(storyctl_dir.agent_dir, storyctl_dir.repo_root, "418-storyctl", None)
    assert got.granted is False
    assert got.source == "corrupt"


def test_a_malformed_labels_verb_does_not_raise(
    storyctl_dir: types.SimpleNamespace,
) -> None:
    """"Never raises" is the documented posture, and a config that parsed is not
    a config that is well-formed.

    `"labels": 3` reached the argv comprehension and took `wfctl start` down with
    a TypeError traceback — on a branch whose only fault was a typo in a file
    nothing validates at load time. A raise here breaks `status`, `start`,
    `resume` and `end` for that branch at once, which is why every other reader
    in this module guards its shape.
    """
    import json

    root = storyctl_dir.repo_root
    (root / ".wf-skills-manifest.json").write_text(json.dumps({"tracker": "fake"}))
    trackers = root / ".agents" / "trackers"
    trackers.mkdir(parents=True, exist_ok=True)
    (trackers / "fake.json").write_text(json.dumps({"verbs": {"labels": 3}}))

    got = notify_grant(storyctl_dir.agent_dir, root, "418-storyctl", "418")
    assert got.granted is False
    assert got.source == "unreadable"


def test_notify_grant_never_raises_on_a_directory_where_the_file_should_be(
    storyctl_dir: types.SimpleNamespace,
) -> None:
    """A raise here breaks `status`, `start`, `resume` and `end` at once."""
    (storyctl_dir.agent_dir / NOTIFY_NAME).mkdir()
    got = notify_grant(storyctl_dir.agent_dir, storyctl_dir.repo_root, "418-storyctl", None)
    assert got.granted is False


def test_a_branch_with_no_issue_key_is_unset_not_a_failed_read(
    storyctl_dir: types.SimpleNamespace,
) -> None:
    """`extract_issue_key` returns the string "unknown", never None.

    So a `is None` guard alone was dead code: every keyless branch asked the
    tracker about an issue called "unknown", got a refusal, and had it filed as a
    tracker that could not be reached. An absent key is not a failed read, and
    conflating them is what FR-015 forbids. The tracker here would fail if it
    were consulted, which is the assertion — it must not be.
    """
    root = storyctl_dir.repo_root
    _tracker(root, ["false"])
    got = notify_grant(storyctl_dir.agent_dir, root, "hotfix-typo", "unknown")
    assert got.granted is False
    assert got.source == "unset"
    assert got.detail is None


def test_a_repo_with_no_nameable_trunk_does_not_blame_the_tracker(
    storyctl_dir: types.SimpleNamespace, tmp_path: Path,
) -> None:
    """Its own source, because the reader may have no tracker at all.

    Filed as `unreadable` this printed "couldn't reach the issue tracker" in a
    repo with nothing configured — the same false cause the `corrupt` split
    already corrected once, in the one case the argument was not applied to.
    """
    import subprocess

    root = tmp_path / "develop-only"
    root.mkdir()
    subprocess.run(["git", "init", "-q", "-b", "develop", str(root)], check=True)
    for k, v in (("user.email", "t@t.com"), ("user.name", "T")):
        subprocess.run(["git", "-C", str(root), "config", k, v], check=True)
    (root / "README.md").write_text("x\n")
    subprocess.run(["git", "-C", str(root), "add", "-A"], check=True)
    subprocess.run(
        ["git", "-C", str(root), "commit", "-qm", "init"], check=True,
        capture_output=True,
    )

    got = notify_grant(storyctl_dir.agent_dir, root, "99-thing", None)
    assert got.granted is False
    assert got.source == "unknown-trunk"


# --- FR-008: bounded by the feature branch -------------------------------------

def test_a_grant_written_on_the_trunk_branch_is_still_refused(
    storyctl_dir: types.SimpleNamespace,
) -> None:
    """Asserted from the granted side, which is the only side that can fail.

    Against the default this passes on a resolver that ignores the branch
    entirely. The behaviour is correct today by construction — the state dir is
    per-branch — and this is what keeps it correct when that changes.
    """
    root = storyctl_dir.repo_root
    grant_notify(storyctl_dir.agent_dir, "granted")
    assert notify_grant(storyctl_dir.agent_dir, root, "418-storyctl", None).granted is True

    got = notify_grant(storyctl_dir.agent_dir, root, _trunk(root), None)
    assert got.granted is False
    assert got.source == "trunk"


def test_a_label_does_not_grant_on_the_trunk_branch_either(
    storyctl_dir: types.SimpleNamespace,
) -> None:
    """The other surface, through the same gate. Nothing on `main`, under any
    switch — so the check has to sit above both, not inside one."""
    root = storyctl_dir.repo_root
    _tracker(root, ["printf", f"{NOTIFY_LABEL}\n"])
    got = notify_grant(storyctl_dir.agent_dir, root, _trunk(root), "418")
    assert got.granted is False
    assert got.source == "trunk"


def test_the_resolution_grid_end_to_end(
    storyctl_dir: types.SimpleNamespace,
) -> None:
    """Every cell of `data-model.md`'s grid, in one place.

    Written as a table because the property that matters is the *shape*: the
    local answer decides two of the three rows outright, and only an unset local
    file lets the label speak. Asserted cell by cell rather than by spot checks,
    because the two disagreeing cells are the ones a reader will come here to
    look up.
    """
    root, agent_dir = storyctl_dir.repo_root, storyctl_dir.agent_dir
    grid = [
        # local state, label present, expected verdict, expected source
        (None,      False, False, "unset"),
        (None,      True,  True,  "label"),
        ("granted", False, True,  "local"),
        ("granted", True,  True,  "local"),
        ("denied",  False, False, "deny"),
        ("denied",  True,  False, "deny"),
    ]
    for local, labelled, granted, source in grid:
        (agent_dir / NOTIFY_NAME).unlink(missing_ok=True)
        if local is not None:
            grant_notify(agent_dir, local)
        _tracker(root, ["printf", f"{NOTIFY_LABEL}\n"] if labelled else ["printf", ""])

        got = notify_grant(agent_dir, root, "418-storyctl", "418")
        assert (got.granted, got.source) == (granted, source), (local, labelled)


# --- the writes ----------------------------------------------------------------

def test_granting_writes_the_file_and_the_event(
    storyctl_dir: types.SimpleNamespace,
) -> None:
    """Two writes for two questions. The file holds one value and is
    overwritten, so it cannot answer *when was this given* — and that question
    is what makes a grant nobody made legible afterwards."""
    agent_dir = storyctl_dir.agent_dir
    grant_notify(agent_dir, "granted")

    stored = json.loads((agent_dir / NOTIFY_NAME).read_text())
    assert stored["state"] == "granted"
    assert stored["source"] == "local"
    assert stored["at"].endswith("Z")

    events = [e for e in _events(agent_dir) if e["event"] == "notify-grant"]
    assert events == [{**events[0], "event": "notify-grant", "state": "granted",
                       "source": "local"}]


def test_granting_leaves_the_neighbouring_mode_file_untouched(
    storyctl_dir: types.SimpleNamespace,
) -> None:
    """FR-006, and the whole argument for a second file rather than a second key.

    A shared file would make this a read-merge-write, and a partly-corrupt one
    would then need a meaning nobody has decided on.
    """
    from wfctl._session import MODE_NAME, auto_approve, grant_auto_approve

    agent_dir = storyctl_dir.agent_dir
    grant_auto_approve(agent_dir, True)
    before = (agent_dir / MODE_NAME).read_text()

    grant_notify(agent_dir, "denied")

    assert (agent_dir / MODE_NAME).read_text() == before
    assert auto_approve(agent_dir) is True


def test_regranting_overwrites_the_value_and_appends_a_second_event(
    storyctl_dir: types.SimpleNamespace,
) -> None:
    agent_dir = storyctl_dir.agent_dir
    grant_notify(agent_dir, "granted")
    grant_notify(agent_dir, "denied")

    assert json.loads((agent_dir / NOTIFY_NAME).read_text())["state"] == "denied"
    states = [e["state"] for e in _events(agent_dir) if e["event"] == "notify-grant"]
    assert states == ["granted", "denied"]


# --- the report ----------------------------------------------------------------

def test_recording_an_action_appends_without_rewriting_what_is_there(
    storyctl_dir: types.SimpleNamespace,
) -> None:
    """FR-010's destination. Append-only is the property that makes the log the
    required one — it survives a session that does not end cleanly."""
    agent_dir = storyctl_dir.agent_dir
    grant_notify(agent_dir, "granted")
    record_notify_action(agent_dir, "issue-create")
    record_notify_action(agent_dir, "push")

    kinds = [e["event"] for e in _events(agent_dir)]
    assert kinds == ["notify-grant", "notify-action", "notify-action"]
    actions = [e for e in _events(agent_dir) if e["event"] == "notify-action"]
    assert [a["action"] for a in actions] == ["issue-create", "push"]


def test_a_malformed_earlier_line_does_not_break_the_append(
    storyctl_dir: types.SimpleNamespace,
) -> None:
    """The log is written by every command, so a truncated final write is a
    state the next append has to survive rather than one it may assume away."""
    agent_dir = storyctl_dir.agent_dir
    (agent_dir / "events.jsonl").write_text('{"event": "start"\n')
    record_notify_action(agent_dir, "issue-create")

    lines = (agent_dir / "events.jsonl").read_text().splitlines()
    assert lines[0] == '{"event": "start"'
    assert json.loads(lines[1])["action"] == "issue-create"


def test_an_unreadable_grant_carries_what_the_tracker_said(
    storyctl_dir: types.SimpleNamespace,
) -> None:
    """The console line is fixed, so the log is the only place the cause lives.
    Someone opening it already knows the run refused; what they need is whether
    it was auth, network, or a missing scope.

    Carried on the resolution rather than on an event of its own. A second event
    held the same string and sat outside the dedupe, so the one state that
    repeats across starts was the only one that grew the log.
    """
    root = storyctl_dir.repo_root
    _tracker(root, ["sh", "-c", "echo 'HTTP 401 Bad credentials' >&2; exit 1"])
    got = notify_grant(storyctl_dir.agent_dir, root, "418-storyctl", "418")
    assert got.source == "unreadable"
    assert "401" in (got.detail or "")
