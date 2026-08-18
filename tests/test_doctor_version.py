"""Tests for doctor's tool-freshness check — release tags and branch drift.

Every test here carries `real_version_check`. Without it, conftest's autouse
fixture replaces `_check_wfctl_version` with `lambda: 0` and the test passes
while exercising the stub — green, and proving nothing. That is the single
easiest mistake to make in this file.
"""
from __future__ import annotations

import json
import subprocess

import pytest

UPSTREAM = "https://github.com/aamarin/wfctl.git"
FORK = "https://github.com/someone/wfctl.git"

# Two 40-char shas that differ in their first 7, so the abbreviated forms in the
# report are distinguishable at a glance when an assertion fails.
BUILT = "d8688f6eec75c2a8eac3a94f3fc44e25041d22a9"
TIP = "271bb2c9dc903722f9e6264efd34516a2970d8ed"


def _plain(s: str) -> str:
    """Strip ANSI so assertions don't break on rich's number highlighting."""
    import re
    return re.sub(r"\x1b\[[0-9;]*m", "", s)


def _direct_url(url: str = UPSTREAM, commit: str = BUILT, requested_revision: str = "") -> str:
    """A PEP 610 payload shaped like the ones uv and pip actually write.

    Recorded from real `pip` and `uv` installs rather than invented: `vcs_info`
    present means a source-control install, `requested_revision` means the user
    pinned, and `dir_info` means a checkout.
    The shapes with no `vcs_info` at all are spelled out at their use sites,
    since each is a different top-level shape rather than a variation on this one.
    """
    vcs = {"vcs": "git", "commit_id": commit}
    if requested_revision:
        vcs["requested_revision"] = requested_revision
    return json.dumps({"url": url, "vcs_info": vcs})


@pytest.fixture
def build(monkeypatch: pytest.MonkeyPatch):
    """Stub the installed distribution's metadata and version.

    Returns a setter so each test states only what it cares about.
    """
    def _set(direct_url: str | None, version: str = "0.14.0") -> None:
        import importlib.metadata

        class _Dist:
            def read_text(self, name: str) -> str | None:
                return direct_url if name == "direct_url.json" else None

        # `_wfctl_version` is the codebase's single choke point for the running
        # version and the documented place to patch; the metadata call is only
        # stubbed for `_installed_build`, which reads a file rather than a version.
        monkeypatch.setattr("wfctl.cli._wfctl_version", lambda: version)
        monkeypatch.setattr(importlib.metadata, "distribution", lambda name: _Dist())

    return _set


def _ls_remote(
    *,
    branch: str = "master",
    tip: str | None = TIP,
    tags: tuple[str, ...] = ("v0.13.0", "v0.14.0"),
    fail: bool = False,
):
    """A `subprocess.run` stand-in returning one `ls-remote --symref` response.

    Records every URL it was asked about, so a test can assert how many
    repositories were consulted and which — the observable half of the rule that
    tags come from upstream while the branch comes from the recorded origin.
    """
    calls: list[str] = []

    def run(argv, **kwargs):
        if "ls-remote" not in argv:
            return subprocess.CompletedProcess(argv, 0, stdout="", stderr="")
        url = next((a for a in argv if a.startswith(("http", "git+", "file:"))), "")
        calls.append(url)
        if fail:
            return subprocess.CompletedProcess(argv, 128, stdout="", stderr="no route")
        out = ""
        if tip is not None:
            out += f"ref: refs/heads/{branch}\tHEAD\n{tip}\tHEAD\n"
        out += "".join(f"{'0' * 40}\trefs/tags/{t}\n" for t in tags)
        return subprocess.CompletedProcess(argv, 0, stdout=out, stderr="")

    run.calls = calls  # type: ignore[attr-defined]
    return run


# --- what the build says about itself ---------------------------------------


@pytest.mark.real_version_check
def test_installed_build_reads_a_vcs_install(build) -> None:
    """A source-control install yields the URL and commit it was built from."""
    from wfctl.cli import _installed_build

    build(_direct_url())
    assert _installed_build() == (UPSTREAM, BUILT, False)


@pytest.mark.real_version_check
def test_installed_build_reads_a_fork(build) -> None:
    """The URL is whatever was recorded — the check must not assume upstream."""
    from wfctl.cli import _installed_build

    build(_direct_url(url=FORK))
    assert _installed_build() == (FORK, BUILT, False)


@pytest.mark.real_version_check
def test_a_pin_keeps_its_origin(build) -> None:
    """A pin suppresses the branch comparison — it does not erase the origin.

    Collapsing the two lost the url, and a lost url means the remedy falls back
    to upstream: a fork user told to overwrite their build with someone else's.
    """
    from wfctl.cli import _installed_build

    build(_direct_url(url=FORK, requested_revision="v0.13.0"))
    assert _installed_build() == (FORK, BUILT, True)


# --- what the remote says right now -----------------------------------------


@pytest.mark.real_version_check
def test_remote_state_parses_branch_tip_and_tags(monkeypatch: pytest.MonkeyPatch) -> None:
    """One response carries all three: branch name, its tip, and the tags."""
    from wfctl.cli import _remote_state

    monkeypatch.setattr(subprocess, "run", _ls_remote())
    state = _remote_state(UPSTREAM)
    assert state is not None
    branch, tip, tags = state
    assert (branch, tip) == ("master", TIP)
    assert set(tags) == {"v0.13.0", "v0.14.0"}


@pytest.mark.real_version_check
def test_remote_state_follows_a_renamed_default_branch(monkeypatch: pytest.MonkeyPatch) -> None:
    """The branch name is read from the symref, never assumed.

    A rename from master to main must need no code change.
    """
    from wfctl.cli import _remote_state

    monkeypatch.setattr(subprocess, "run", _ls_remote(branch="main"))
    state = _remote_state(UPSTREAM)
    assert state is not None
    assert state[0] == "main"


@pytest.mark.real_version_check
def test_remote_state_never_combines_refs_with_head(monkeypatch: pytest.MonkeyPatch) -> None:
    """`--refs` drops everything outside refs/, HEAD included.

    Combined with `--symref HEAD` the two cancel: git returns tags only, the
    branch half reads as unreachable, and doctor reports a warning forever. The
    stub in this file honours whatever flags it is handed, so only asserting on
    the argv catches it — this regression shipped green through twenty tests and
    was caught by running the real binary.
    """
    seen: list[list[str]] = []

    def spy(argv, **kwargs):
        seen.append(list(argv))
        return _ls_remote()(argv, **kwargs)

    monkeypatch.setattr(subprocess, "run", spy)
    from wfctl.cli import _remote_state

    _remote_state(UPSTREAM)
    assert seen and "--symref" in seen[0]
    assert "--refs" not in seen[0]


@pytest.mark.real_version_check
def test_remote_state_terminates_options_before_the_url(monkeypatch: pytest.MonkeyPatch) -> None:
    """The url is untrusted input and must never be read as a git option.

    `direct_url.json` is a file this process does not own. git honours
    `--upload-pack=<command>` wherever it appears in argv, so without a `--`
    terminator a recorded url could run a command on every doctor invocation —
    and doctor runs at every session start. Asserting on argv rather than on
    behaviour because the stub cannot execute anything: the ordering *is* the
    security property.
    """
    seen: list[list[str]] = []

    def spy(argv, **kwargs):
        seen.append(list(argv))
        return _ls_remote()(argv, **kwargs)

    monkeypatch.setattr(subprocess, "run", spy)
    from wfctl.cli import _remote_state

    _remote_state("--upload-pack=nope")
    argv = seen[0]
    assert "--" in argv, "no option terminator: a leading-dash url is read as a git option"
    assert argv.index("--") < argv.index("--upload-pack=nope")


@pytest.mark.real_version_check
def test_remote_state_ignores_annotated_tag_dereferences(monkeypatch: pytest.MonkeyPatch) -> None:
    """Dropping `--refs` lets `^{}` rows through; they must not become versions."""
    from wfctl.cli import _remote_state

    def with_peeled(argv, **kwargs):
        out = (
            f"ref: refs/heads/master\tHEAD\n{TIP}\tHEAD\n"
            f"{'0' * 40}\trefs/tags/v0.14.0\n{'1' * 40}\trefs/tags/v0.14.0^{{}}\n"
        )
        return subprocess.CompletedProcess(argv, 0, stdout=out, stderr="")

    monkeypatch.setattr(subprocess, "run", with_peeled)
    state = _remote_state(UPSTREAM)
    assert state is not None
    assert set(state[2]) == {"v0.14.0"}


@pytest.mark.real_version_check
def test_remote_state_is_none_when_unreachable(monkeypatch: pytest.MonkeyPatch) -> None:
    """A failed query is distinguishable from a repo that simply has no tags.

    Rendering them alike would let "couldn't look" read as "looked, all clear".
    """
    from wfctl.cli import _remote_state

    monkeypatch.setattr(subprocess, "run", _ls_remote(fail=True))
    assert _remote_state(UPSTREAM) is None


@pytest.mark.real_version_check
def test_remote_state_tolerates_a_repo_with_no_tags(monkeypatch: pytest.MonkeyPatch) -> None:
    """No tags is a valid answer, not a failure: the branch half still works."""
    from wfctl.cli import _remote_state

    monkeypatch.setattr(subprocess, "run", _ls_remote(tags=()))
    state = _remote_state(UPSTREAM)
    assert state is not None
    assert state[1] == TIP
    assert state[2] == []


# --- the report -------------------------------------------------------------


def _report(capsys) -> str:
    return _plain(capsys.readouterr().out)


@pytest.mark.real_version_check
def test_drift_is_reported_with_both_commits_and_a_remedy(
    build, monkeypatch: pytest.MonkeyPatch, capsys
) -> None:
    """The whole point: a build behind its branch says so, and how to fix it."""
    from wfctl.cli import _check_wfctl_version

    build(_direct_url())
    monkeypatch.setattr(subprocess, "run", _ls_remote())
    rc = _check_wfctl_version()
    out = _report(capsys)

    assert rc == 1
    assert "latest release" in out
    assert "build behind master — d8688f6 → 271bb2c" in out
    assert "bundled skills are from this build too" in out
    assert f"reinstall: uv tool install --force {UPSTREAM}" in out


@pytest.mark.real_version_check
def test_drift_report_states_no_commit_count(
    build, monkeypatch: pytest.MonkeyPatch, capsys
) -> None:
    """ls-remote proves difference, never distance — claim only what is known.

    Two commit ids cannot yield a count of commits between them; printing one
    would need a second API call to decorate a line that is already actionable.
    """
    import re

    from wfctl.cli import _check_wfctl_version

    build(_direct_url())
    monkeypatch.setattr(subprocess, "run", _ls_remote())
    _check_wfctl_version()
    assert not re.search(r"\d+\s+commits?", _report(capsys))


@pytest.mark.real_version_check
def test_at_tip_prints_todays_line_unchanged(
    build, monkeypatch: pytest.MonkeyPatch, capsys
) -> None:
    """The unremarkable case stays byte-identical, so existing readers don't shift."""
    from wfctl.cli import _check_wfctl_version

    build(_direct_url(commit=TIP))
    monkeypatch.setattr(subprocess, "run", _ls_remote())
    rc = _check_wfctl_version()

    assert rc == 0
    assert _report(capsys).strip() == "✓ wfctl 0.14.0 — latest"


@pytest.mark.real_version_check
def test_a_newer_release_suppresses_the_drift_line(
    build, monkeypatch: pytest.MonkeyPatch, capsys
) -> None:
    """One remedy per report: the upgrade re-resolves the branch anyway.

    Two upgrade instructions in one report is one more than anyone acts on.
    """
    from wfctl.cli import _check_wfctl_version

    build(_direct_url(), version="0.9.0")
    monkeypatch.setattr(subprocess, "run", _ls_remote())
    rc = _check_wfctl_version()
    out = _report(capsys)

    assert rc == 1
    assert "0.14.0 available" in out
    assert "build behind" not in out


# --- shapes that cannot drift, and forks ------------------------------------


@pytest.mark.parametrize(
    ("name", "payload"),
    [
        ("no_metadata_file", None),
        ("editable_checkout", json.dumps({"url": "file:///w/wfctl", "dir_info": {"editable": True}})),
        ("deliberate_pin", _direct_url(requested_revision="v0.13.0")),
        ("unreadable_metadata", "{not json"),
    ],
)
@pytest.mark.real_version_check
def test_shapes_that_cannot_drift_are_skipped_silently(
    name, payload, build, monkeypatch: pytest.MonkeyPatch, capsys
) -> None:
    """Four shapes, one outcome — no drift line, no warning, exit 0.

    None of these can drift against a branch, so a report about one would be
    noise, and noise trains the reader to skip the line that matters.
    """
    from wfctl.cli import _check_wfctl_version

    build(payload)
    monkeypatch.setattr(subprocess, "run", _ls_remote())
    rc = _check_wfctl_version()
    out = _report(capsys)

    assert rc == 0
    assert "build behind" not in out
    assert "⚠" not in out
    assert out.strip() == "✓ wfctl 0.14.0 — latest"


@pytest.mark.real_version_check
def test_an_upstream_install_still_costs_one_query(
    build, monkeypatch: pytest.MonkeyPatch, capsys
) -> None:
    """The ordinary install pays exactly the network cost it paid before."""
    from wfctl.cli import _check_wfctl_version

    build(_direct_url())
    fake = _ls_remote()
    monkeypatch.setattr(subprocess, "run", fake)
    _check_wfctl_version()
    capsys.readouterr()

    assert fake.calls == [UPSTREAM]


@pytest.mark.real_version_check
def test_a_pending_release_spares_a_fork_the_second_query(
    build, monkeypatch: pytest.MonkeyPatch, capsys
) -> None:
    """A query whose answer cannot change the outcome is never made.

    The release verdict outranks the branch one, so once an upgrade is being
    prescribed the fork's branch tip is irrelevant — and asking for it would be a
    network round trip spent on a result the report discards.
    """
    from wfctl.cli import _check_wfctl_version

    build(_direct_url(url=FORK), version="0.9.0")
    fake = _ls_remote()
    monkeypatch.setattr(subprocess, "run", fake)
    _check_wfctl_version()
    capsys.readouterr()

    assert fake.calls == [UPSTREAM]


@pytest.mark.real_version_check
def test_a_fork_asks_upstream_for_tags_and_the_fork_for_its_branch(
    build, monkeypatch: pytest.MonkeyPatch, capsys
) -> None:
    """A fork is authoritative about its own branch, never about releases.

    A fork's tag list freezes at fork time, so reading releases from it would
    report "latest" straight through an upstream release.
    """
    from wfctl.cli import _check_wfctl_version

    build(_direct_url(url=FORK))
    fake = _ls_remote()
    monkeypatch.setattr(subprocess, "run", fake)
    _check_wfctl_version()
    capsys.readouterr()

    assert fake.calls == [UPSTREAM, FORK]


@pytest.mark.real_version_check
def test_every_remedy_names_the_fork_not_upstream(
    build, monkeypatch: pytest.MonkeyPatch, capsys
) -> None:
    """Never tell a fork user to install someone else's lineage.

    Both remedies are checked, because the upgrade line predates this feature and
    hardcoded upstream — following it would have replaced a fork build silently.
    """
    from wfctl.cli import _check_wfctl_version

    build(_direct_url(url=FORK))
    monkeypatch.setattr(subprocess, "run", _ls_remote())
    _check_wfctl_version()
    assert f"reinstall: uv tool install --force {FORK}" in _report(capsys)

    build(_direct_url(url=FORK), version="0.9.0")
    monkeypatch.setattr(subprocess, "run", _ls_remote())
    _check_wfctl_version()
    out = _report(capsys)
    assert f"upgrade: uv tool install --upgrade {FORK}" in out
    assert UPSTREAM not in out


# --- one warning line, naming what could not run ----------------------------


@pytest.mark.real_version_check
def test_a_pinned_fork_is_told_to_upgrade_from_its_own_fork(
    build, monkeypatch: pytest.MonkeyPatch, capsys
) -> None:
    """The same holds for pinned installs — the shape that first broke it.

    A pin skips the branch comparison, which is right, but the release check
    still runs and still prints a remedy. If the pin also discarded the origin,
    that remedy named upstream and following it would swap a fork user onto a
    different lineage.
    """
    from wfctl.cli import _check_wfctl_version

    build(_direct_url(url=FORK, requested_revision="v0.13.0"), version="0.9.0")
    monkeypatch.setattr(subprocess, "run", _ls_remote())
    assert _check_wfctl_version() is True
    out = _report(capsys)

    assert f"upgrade: uv tool install --upgrade {FORK}" in out
    assert UPSTREAM not in out


@pytest.mark.real_version_check
def test_both_queries_failing_reports_one_warning(
    build, monkeypatch: pytest.MonkeyPatch, capsys
) -> None:
    from wfctl.cli import _check_wfctl_version

    build(_direct_url())
    monkeypatch.setattr(subprocess, "run", _ls_remote(fail=True))
    rc = _check_wfctl_version()
    out = _report(capsys)

    assert rc == 0
    assert out.count("⚠") == 1
    assert "couldn't check releases or branch" in out


@pytest.mark.real_version_check
def test_a_failed_branch_query_is_named_not_dropped(
    build, monkeypatch: pytest.MonkeyPatch, capsys
) -> None:
    """Silence here would read as "no drift", which is the defect itself.

    A fork whose remote is gone is the reachable case — upstream answers for
    tags, the fork does not answer for its branch.
    """
    from wfctl.cli import _check_wfctl_version

    build(_direct_url(url=FORK))

    def only_upstream(argv, **kwargs):
        if "ls-remote" in argv and FORK in argv:
            return subprocess.CompletedProcess(argv, 128, stdout="", stderr="gone")
        return _ls_remote()(argv, **kwargs)

    monkeypatch.setattr(subprocess, "run", only_upstream)
    rc = _check_wfctl_version()
    out = _report(capsys)

    assert rc == 0
    assert out.count("⚠") == 1
    assert "couldn't check branch drift" in out
    assert "latest release" in out


@pytest.mark.real_version_check
def test_known_drift_still_exits_nonzero_when_the_tag_query_fails(
    build, monkeypatch: pytest.MonkeyPatch, capsys
) -> None:
    """Two rules collide here, and the actionable verdict wins.

    "A failed query exits zero" and "drift exits non-zero" both apply when the
    tag query fails while the branch query proves drift — reachable on any fork
    install, where the two are separate queries. Exiting zero would bury a stale
    build that was positively identified, over an unrelated failure, which is the
    silent false negative this whole check exists to remove. So the drift carries
    the exit code and the failure is folded into the one warning line.
    """
    from wfctl.cli import _check_wfctl_version

    build(_direct_url(url=FORK))

    def only_fork(argv, **kwargs):
        if "ls-remote" in argv and UPSTREAM in argv:
            return subprocess.CompletedProcess(argv, 128, stdout="", stderr="down")
        return _ls_remote()(argv, **kwargs)

    monkeypatch.setattr(subprocess, "run", only_fork)
    assert _check_wfctl_version() is True
    out = _report(capsys)

    assert out.count("⚠") == 1
    assert "couldn't check releases" in out
    assert "build behind master" in out


@pytest.mark.real_version_check
def test_no_origin_and_no_releases_reports_one_warning(
    build, monkeypatch: pytest.MonkeyPatch, capsys
) -> None:
    """The fourth warning variant: nothing recorded locally, nothing reachable."""
    from wfctl.cli import _check_wfctl_version

    build(None)
    monkeypatch.setattr(subprocess, "run", _ls_remote(fail=True))
    assert _check_wfctl_version() is False
    out = _report(capsys)

    assert out.count("⚠") == 1
    assert "couldn't check releases (offline?)" in out
    assert "branch" not in out


@pytest.mark.real_version_check
def test_a_failed_tag_query_still_reports_the_branch_verdict(
    build, monkeypatch: pytest.MonkeyPatch, capsys
) -> None:
    """The mirror case: the half that ran is stated inside the same warning line."""
    from wfctl.cli import _check_wfctl_version

    build(_direct_url(url=FORK, commit=TIP))

    def only_fork(argv, **kwargs):
        if "ls-remote" in argv and UPSTREAM in argv:
            return subprocess.CompletedProcess(argv, 128, stdout="", stderr="gone")
        return _ls_remote()(argv, **kwargs)

    monkeypatch.setattr(subprocess, "run", only_fork)
    rc = _check_wfctl_version()
    out = _report(capsys)

    assert rc == 0
    assert out.count("⚠") == 1
    assert "couldn't check releases" in out
    assert "build matches branch tip" in out


# --- the release comparison, as originally covered --------------------------
#
# Moved here from test_install_skills.py, where they lived only because doctor's
# whole surface used to be tested in one file. They predate the branch check and
# are kept as-is in intent: the release verdict on its own, with the build at the
# tip so nothing else can influence the outcome.


# --- invariants over the whole input space ----------------------------------
#
# The cases above assert exact output for one state each. The bugs that survived
# them all lived in a *combination* — a fork that was also pinned, a fork whose
# two queries failed independently — where each half was tested and the product
# was not. Enumerating every product with exact expected output would be
# unreadable and would rot; asserting a few properties that must hold across all
# of them is neither, and is what catches this class.

_SHAPES = {
    "upstream": _direct_url(),
    "upstream_at_tip": _direct_url(commit=TIP),
    "fork": _direct_url(url=FORK),
    "fork_at_tip": _direct_url(url=FORK, commit=TIP),
    "pinned_upstream": _direct_url(requested_revision="v0.13.0"),
    "pinned_fork": _direct_url(url=FORK, requested_revision="v0.13.0"),
    "editable": json.dumps({"url": "file:///w/wfctl", "dir_info": {"editable": True}}),
    "no_metadata": None,
    "malformed": "{not json",
}

_FAILURES = {
    "none": (),
    "upstream_down": (UPSTREAM,),
    "fork_down": (FORK,),
    "all_down": (UPSTREAM, FORK),
}


def _selective_failure(*dead: str):
    """`ls-remote` that fails only for the named repositories."""

    def run(argv, **kwargs):
        if "ls-remote" in argv and any(d in argv for d in dead):
            return subprocess.CompletedProcess(argv, 128, stdout="", stderr="down")
        return _ls_remote()(argv, **kwargs)

    return run


@pytest.mark.parametrize("shape", sorted(_SHAPES))
@pytest.mark.parametrize("failure", sorted(_FAILURES))
@pytest.mark.parametrize("version", ["0.9.0", "0.14.0"])
@pytest.mark.real_version_check
def test_report_invariants_hold_for_every_combination(
    shape, failure, version, build, monkeypatch: pytest.MonkeyPatch, capsys
) -> None:
    """Five properties that must hold whatever the install and whatever fails.

    Each maps to a requirement, and each is violated by a defect that reached
    code review with the exact-output tests all green.
    """
    from wfctl.cli import _check_wfctl_version

    payload = _SHAPES[shape]
    build(payload, version=version)
    monkeypatch.setattr(subprocess, "run", _selective_failure(*_FAILURES[failure]))

    rc = _check_wfctl_version()
    out = _report(capsys)
    # rich wraps at the console width, so a long url arrives split across lines.
    squashed = "".join(out.split())

    # Never two competing remedies in one report.
    assert not ("available" in out and "build behind" in out), out

    # At most one warning line, ever.
    assert out.count("⚠") <= 1, out

    # A printed remedy names the recorded origin, or upstream only when
    # nothing was recorded. This is the one that caught the pinned-fork defect.
    if "uv tool install" in out:
        # Derived from the payload, not the case name: a name-based guess is a
        # second source of truth about the same fact, and gets them out of step.
        expected = FORK if payload and FORK in payload else UPSTREAM
        assert "".join(expected.split()) in squashed, out
        if expected == FORK:
            assert "".join(UPSTREAM.split()) not in squashed, out

    # The exit code tracks whether anything actionable was found,
    # not whether a query happened to fail.
    assert rc == ("⬆" in out), (rc, out)

    # The data proves difference, never distance.
    import re

    assert not re.search(r"\d+\s+commits?", out), out


@pytest.mark.real_version_check
def test_release_upgrade_is_reported(build, monkeypatch: pytest.MonkeyPatch, capsys) -> None:
    from wfctl.cli import _check_wfctl_version

    build(_direct_url(commit=TIP), version="0.9.0")
    monkeypatch.setattr(subprocess, "run", _ls_remote(tags=("v0.9.0", "v0.10.0")))
    assert _check_wfctl_version() is True
    assert "0.10.0 available" in _report(capsys)


@pytest.mark.real_version_check
def test_release_current_is_reported(build, monkeypatch: pytest.MonkeyPatch, capsys) -> None:
    from wfctl.cli import _check_wfctl_version

    build(_direct_url(commit=TIP), version="0.10.0")
    monkeypatch.setattr(subprocess, "run", _ls_remote(tags=("v0.9.0", "v0.10.0")))
    assert _check_wfctl_version() is False
    assert "latest" in _report(capsys)
