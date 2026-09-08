"""The refusal as a check rather than as prose two skills have to read (#280).

`a-rule-is-expressed-as-a-check` decides which of the two a rule ships as, and
asks one question of the rule: is a violation visible in an artifact the work
already produces? Here it is — the tracker changed — so the gate belongs where
every tracker write funnels through, not only in the skills that are supposed to
know better. An agent that never opened `end-session/SKILL.md` still cannot
comment, label or open an issue on a feature nobody granted.

What is *not* gated matters as much. Reads reach nobody. Closing an issue is the
irreversible row, which no grant reaches, so consulting a grant for it would
refuse the one actor allowed to do it.
"""
from __future__ import annotations

import json
import types
from pathlib import Path

from wfctl import _tracker
from wfctl._session import NotifyGrant, record_notify_resolved

NOTIFYING = ["comment", "create", "label"]


def _backend(root: Path, marker: Path) -> None:
    """A backend whose every verb records that it ran, so "refused" is provable.

    Asserting on the exit code alone would pass against a gate that printed the
    refusal and ran the command anyway — which is the only failure worth catching
    here, because the notification is what cannot be taken back.
    """
    (root / ".wf-skills-manifest.json").write_text(json.dumps({"tracker": "fake"}))
    trackers = root / ".agents" / "trackers"
    trackers.mkdir(parents=True, exist_ok=True)
    argv = ["sh", "-c", f"echo ran >> {marker}"]
    (trackers / "fake.json").write_text(json.dumps({"verbs": {
        "comment": argv, "create": argv, "label": argv,
        "close": argv, "view": argv, "list": argv,
    }}))


def _ran(marker: Path) -> int:
    return len(marker.read_text().splitlines()) if marker.exists() else 0


def _grant(agent_dir: Path, granted: bool, source: str) -> None:
    record_notify_resolved(agent_dir, NotifyGrant(granted, source))


def test_an_ungranted_run_cannot_reach_the_notifying_verbs(
    storyctl_dir: types.SimpleNamespace, tmp_path: Path,
) -> None:
    """The default, and the assertion is that the backend never ran.

    An exit code says the caller was told no; the marker file says nobody was
    notified. Only the second is the property this feature is about.
    """
    marker = tmp_path / "ran.log"
    _backend(storyctl_dir.repo_root, marker)
    for verb in NOTIFYING:
        code = _tracker.dispatch(
            storyctl_dir.agent_dir, storyctl_dir.repo_root, verb, {"id": "418"},
        )
        assert code == 1, verb
    assert _ran(marker) == 0


def test_a_granted_run_reaches_them(
    storyctl_dir: types.SimpleNamespace, tmp_path: Path,
) -> None:
    """Asserted from the granted side, which is the half that would otherwise
    pass on a gate that refuses everything unconditionally."""
    marker = tmp_path / "ran.log"
    _backend(storyctl_dir.repo_root, marker)
    _grant(storyctl_dir.agent_dir, True, "local")
    for verb in NOTIFYING:
        assert _tracker.dispatch(
            storyctl_dir.agent_dir, storyctl_dir.repo_root, verb, {"id": "418"},
        ) == 0, verb
    assert _ran(marker) == len(NOTIFYING)


def test_reads_are_never_gated(
    storyctl_dir: types.SimpleNamespace, tmp_path: Path,
) -> None:
    """Looking at an issue tells nobody. Gating reads would break `status` and
    the label read itself, which resolves the grant in the first place."""
    marker = tmp_path / "ran.log"
    _backend(storyctl_dir.repo_root, marker)
    for verb in ("view", "list"):
        assert _tracker.dispatch(
            storyctl_dir.agent_dir, storyctl_dir.repo_root, verb, {"id": "418"},
        ) == 0, verb
    assert _ran(marker) == 2


def test_closing_an_issue_is_not_gated_on_the_grant(
    storyctl_dir: types.SimpleNamespace, tmp_path: Path,
) -> None:
    """Its absence from the gated set is the decision, not an oversight.

    Closing is the irreversible row and no grant reaches it, so consulting one
    here would refuse the human who is the only actor allowed to do it — and
    wfctl cannot tell a human from an agent anyway. What keeps the row safe is
    that nothing ever grants it, never that this function refuses it.
    """
    marker = tmp_path / "ran.log"
    _backend(storyctl_dir.repo_root, marker)
    assert _tracker.dispatch(
        storyctl_dir.agent_dir, storyctl_dir.repo_root, "close",
        {"id": "418", "comment": "done"},
    ) == 0
    assert _ran(marker) == 1


def test_the_refusal_names_why_and_how_to_lift_it(
    storyctl_dir: types.SimpleNamespace, tmp_path: Path, capsys,
) -> None:
    """A refusal that does not say what would change it sends the reader looking.

    The source is carried through because the five refused states are not one
    event, and a tracker that could not be reached is not a person saying no.
    """
    marker = tmp_path / "ran.log"
    _backend(storyctl_dir.repo_root, marker)
    _grant(storyctl_dir.agent_dir, False, "unreadable")
    _tracker.dispatch(
        storyctl_dir.agent_dir, storyctl_dir.repo_root, "comment", {"id": "418"},
    )
    out = capsys.readouterr().out
    assert "--allow-notify" in out
    assert "authority:notify" in out
    assert "unreadable" in out

    # Nothing wrapped. Rich breaks at the terminal width, and a remedy split
    # across a wrap arrives as a fragment — the reader sees "or the" on its own
    # line and has to reassemble the command. Asserted against the rendered
    # output rather than the source strings, because the markup is not what
    # wraps.
    assert all(len(line) < 80 for line in out.splitlines()), out


def test_a_refusal_is_told_apart_from_a_backend_that_cannot_do_it(
    storyctl_dir: types.SimpleNamespace, tmp_path: Path,
) -> None:
    """Exit 0 already means "nothing was configured for this", and a session must
    not fail for it. A refusal is the opposite fact — something was configured
    and the run may not use it — so it cannot share that code, or a caller would
    report the tracker updated when nobody was told anything."""
    root = storyctl_dir.repo_root
    (root / ".wf-skills-manifest.json").write_text(json.dumps({"tracker": "fake"}))
    trackers = root / ".agents" / "trackers"
    trackers.mkdir(parents=True, exist_ok=True)
    (trackers / "fake.json").write_text(json.dumps({"verbs": {"list": ["true"]}}))

    assert _tracker.dispatch(
        storyctl_dir.agent_dir, root, "comment", {"id": "418"},
    ) == 0

    _backend(root, tmp_path / "ran.log")
    assert _tracker.dispatch(
        storyctl_dir.agent_dir, root, "comment", {"id": "418"},
    ) == 1
