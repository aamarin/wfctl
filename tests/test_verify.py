"""Tests for the definition of done: config, run, record, and staleness.

Exists because `implement` used to report complete on the strength of a file the
implementing agent wrote (#69). Every test here asserts on something wfctl
derives itself — an exit code it collected, a sha it read from git — never on an
artifact the agent under test could have produced.

`NO_COLOR` is pinned globally in `conftest.py`; output assertions below rely on
it and do not set it again.
"""
from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest

from wfctl import _verify


def _write_config(root: Path, payload: str) -> None:
    (root / _verify.CONFIG_PATH).write_text(payload)


# --- load_config: every row of contracts/wfctl-json.md -----------------------

def test_absent_config_is_not_an_error(repo_root: Path) -> None:
    """No wfctl.json means no definition of done — the degrade path (FR-002).

    Reported as "nothing configured", never as a problem: a repo that has not
    adopted the feature must see no change at all.
    """
    assert _verify.load_config(repo_root) == ([], [])


@pytest.mark.parametrize(
    "payload",
    ['{}', '{"verify": []}', '{"verify": [], "future": 1}'],
    ids=["empty-object", "empty-list", "unknown-keys-ignored"],
)
def test_config_shapes_that_mean_nothing_configured(repo_root: Path, payload: str) -> None:
    """Three ways of saying the same thing, all of which must degrade quietly."""
    _write_config(repo_root, payload)
    assert _verify.load_config(repo_root) == ([], [])


def test_one_command_loads(repo_root: Path) -> None:
    _write_config(repo_root, '{"verify": [["pytest", "-q"]]}')
    assert _verify.load_config(repo_root) == ([["pytest", "-q"]], [])


def test_commands_keep_their_declared_order(repo_root: Path) -> None:
    """Order is part of the definition; the record compares by exact equality."""
    _write_config(repo_root, '{"verify": [["a"], ["b"], ["c"]]}')
    commands, errs = _verify.load_config(repo_root)
    assert commands == [["a"], ["b"], ["c"]]
    assert errs == []


@pytest.mark.parametrize(
    "payload",
    [
        '{"verify": "pytest -q"}',
        '{"verify": ["pytest -q"]}',
        '{"verify": [[]]}',
        '{"verify": [["pytest", 3]]}',
        '{"verify": [["ok"], "bad"]}',
        'not json at all',
        '[1, 2, 3]',
    ],
    ids=["string-not-list", "string-element", "empty-argv", "non-string-token",
         "one-good-one-bad", "unparseable", "top-level-not-object"],
)
def test_malformed_config_reports_and_yields_no_commands(repo_root: Path, payload: str) -> None:
    """A half-valid config is not a definition of done.

    Every rejection returns zero commands alongside the problem. Returning the
    parseable half would run a definition of done nobody declared.
    """
    _write_config(repo_root, payload)
    commands, errs = _verify.load_config(repo_root)
    assert commands == []
    assert errs


def test_a_string_command_is_rejected_not_split(repo_root: Path) -> None:
    """Splitting on whitespace is how shell syntax gets in (FR-010).

    The message names the fix, because the reason is not obvious to someone who
    just wants their test command to run.
    """
    _write_config(repo_root, '{"verify": ["pytest && rm -rf /tmp/x"]}')
    commands, errs = _verify.load_config(repo_root)
    assert commands == []
    assert "argv" in errs[0]


def test_an_explicit_shell_is_allowed(repo_root: Path) -> None:
    """The repository may ask for a shell — what it may not do is get one by accident."""
    _write_config(repo_root, '{"verify": [["sh", "-c", "pytest && echo done"]]}')
    commands, errs = _verify.load_config(repo_root)
    assert commands == [["sh", "-c", "pytest && echo done"]]
    assert errs == []


# --- the record --------------------------------------------------------------

def _record(**over: object) -> dict:
    base = {
        "command": [["pytest", "-q"]], "exit": 0, "failed": [],
        "sha": "a" * 40, "dirty": False, "inconclusive": False,
        "at": "2026-08-25T00:00:00Z",
    }
    base.update(over)
    return base


def test_record_round_trips(tmp_path: Path) -> None:
    _verify.write_record(tmp_path, _record())
    assert _verify.load_record(tmp_path) == _record()


def test_absent_record_is_none(tmp_path: Path) -> None:
    assert _verify.load_record(tmp_path) is None


@pytest.mark.parametrize(
    "content",
    ["", "{", "null", "[]", '{"exit": 0}'],
    ids=["empty", "truncated", "json-null", "json-list", "missing-fields"],
)
def test_unusable_record_reads_as_absent(tmp_path: Path, content: str) -> None:
    """Never verified is the safe direction, and it is also the true one.

    A record we cannot fully interpret must not certify anything. Partial trust
    is how a verdict outlives the thing it described.
    """
    _verify.record_path(tmp_path).write_text(content)
    assert _verify.load_record(tmp_path) is None


def test_write_replaces_rather_than_merges(tmp_path: Path) -> None:
    """A run's record is the whole truth about that run, not a patch on the last."""
    _verify.write_record(tmp_path, _record(exit=1, failed=[["pytest", "-q"]]))
    _verify.write_record(tmp_path, _record())
    loaded = _verify.load_record(tmp_path)
    assert loaded is not None and loaded["exit"] == 0 and loaded["failed"] == []


# --- code identity -----------------------------------------------------------

def _commit(root: Path, name: str = "f.txt", body: str = "x") -> None:
    (root / name).write_text(body)
    subprocess.run(["git", "-C", str(root), "add", "-A"], check=True, capture_output=True)
    subprocess.run(
        ["git", "-C", str(root), "commit", "-m", "c"], check=True, capture_output=True
    )


def test_clean_tree_reads_clean(repo_root: Path) -> None:
    _commit(repo_root)
    sha, dirty = _verify.code_identity(repo_root)
    assert len(sha) == 40
    assert dirty is False


def test_modified_tracked_file_reads_dirty(repo_root: Path) -> None:
    _commit(repo_root)
    (repo_root / "f.txt").write_text("changed")
    _, dirty = _verify.code_identity(repo_root)
    assert dirty is True


def test_untracked_file_reads_dirty(repo_root: Path) -> None:
    """A new source file is untracked until added (spec Assumptions).

    Excluding untracked files would let brand-new, never-verified code sit inside
    a passing verdict — the failure this whole feature removes, one layer down.
    """
    _commit(repo_root)
    (repo_root / "brand_new.py").write_text("def f(): ...\n")
    _, dirty = _verify.code_identity(repo_root)
    assert dirty is True


def test_commit_moves_the_sha(repo_root: Path) -> None:
    _commit(repo_root)
    first, _ = _verify.code_identity(repo_root)
    _commit(repo_root, body="y")
    second, _ = _verify.code_identity(repo_root)
    assert first != second


def test_repo_with_no_commits_yields_an_empty_sha(repo_root: Path) -> None:
    """Nothing to verify against yet, and an empty sha never matches a later read."""
    sha, _ = _verify.code_identity(repo_root)
    assert sha == ""


# --- run_verification --------------------------------------------------------

def _script(root: Path, name: str, body: str) -> list[str]:
    """A tiny python command, so these tests need no shell and no fixtures on PATH."""
    (root / name).write_text(body)
    return ["python3", str(root / name)]


def test_every_command_runs_even_after_one_fails(repo_root: Path) -> None:
    """FR-013: one run reports every problem, not just the first.

    Stopping early would make a user re-run to discover the next failure, and
    each re-run costs the full suite.
    """
    a = _script(repo_root, "a.py", "open('a.ran','w').write('1')\n")
    b = _script(repo_root, "b.py", "import sys; open('b.ran','w').write('1'); sys.exit(1)\n")
    c = _script(repo_root, "c.py", "open('c.ran','w').write('1')\n")
    code, failed = _verify.run_verification(repo_root, [a, b, c])
    assert code == 1
    assert failed == [b]
    assert all((repo_root / f"{n}.ran").exists() for n in "abc")


def test_failures_are_collected_in_declared_order(repo_root: Path) -> None:
    a = _script(repo_root, "a.py", "import sys; sys.exit(1)\n")
    b = _script(repo_root, "b.py", "pass\n")
    c = _script(repo_root, "c.py", "import sys; sys.exit(2)\n")
    code, failed = _verify.run_verification(repo_root, [a, b, c])
    assert code == 1
    assert failed == [a, c]


def test_all_passing_yields_exit_zero_and_no_failures(repo_root: Path) -> None:
    ok = _script(repo_root, "ok.py", "pass\n")
    assert _verify.run_verification(repo_root, [ok, ok]) == (0, [])


def test_shell_metacharacters_are_literal_arguments(repo_root: Path) -> None:
    """FR-010: argv, never a shell string.

    The command writes its own argv to disk. If a shell had interpreted the
    tokens, the substitution would have run and the recorded argument would not
    be the literal text.
    """
    prog = _script(
        repo_root, "argv.py",
        "import sys, json; open('argv.json','w').write(json.dumps(sys.argv[1:]))\n",
    )
    payload = ["$(touch pwned)", "`touch pwned2`", "; touch pwned3"]
    code, failed = _verify.run_verification(repo_root, [prog + payload])
    assert (code, failed) == (0, [])
    assert json.loads((repo_root / "argv.json").read_text()) == payload
    assert not any((repo_root / f"pwned{s}").exists() for s in ("", "2", "3"))


def test_a_missing_executable_is_a_failed_command(repo_root: Path, capsys) -> None:
    """FR-023. A typo in wfctl.json must not surface as a traceback.

    It is also not "no definition of done" — reporting complete because the
    checker is absent is the exact failure this feature removes.
    """
    ok = _script(repo_root, "ok.py", "pass\n")
    missing = ["definitely-not-a-real-binary-69"]
    code, failed = _verify.run_verification(repo_root, [ok, missing])
    assert code == 1
    assert failed == [missing]
    assert "definitely-not-a-real-binary-69" in capsys.readouterr().out


def test_commands_run_from_the_repository_root(repo_root: Path, tmp_path: Path) -> None:
    """Not the caller's cwd — otherwise a relative path in the config resolves differently
    depending on where the user happened to be standing."""
    prog = _script(repo_root, "cwd.py", "import os; open('cwd.txt','w').write(os.getcwd())\n")
    _verify.run_verification(repo_root, [prog])
    written = (repo_root / "cwd.txt").read_text()
    assert Path(written).resolve() == repo_root.resolve()


# --- perform: record, event, interruption, CLI -------------------------------

@pytest.fixture
def verify_repo(repo_root: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """A committed repo with a state dir, ready for `perform`."""
    _commit(repo_root)
    state = repo_root / ".wfctl-state"
    state.mkdir()
    monkeypatch.setenv("WFCTL_STATE_DIR", str(state))
    monkeypatch.setenv("WFCTL_BRANCH", "69-machine-checked-done")
    monkeypatch.setenv("WFCTL_REPO_ROOT", str(repo_root))
    return state


def test_a_passing_run_records_the_commands_it_ran(verify_repo: Path, repo_root: Path) -> None:
    """The record stores the definition, not only the verdict.

    Without it, a config change would leave a green record certifying a
    definition of done nobody declared any more.
    """
    ok = _script(repo_root, "ok.py", "pass\n")
    _write_config(repo_root, json.dumps({"verify": [ok]}))
    assert _verify.perform(verify_repo, repo_root) == 0
    rec = _verify.load_record(verify_repo)
    assert rec is not None
    assert rec["command"] == [ok] and rec["exit"] == 0 and rec["failed"] == []
    assert rec["inconclusive"] is False


def test_a_failing_run_names_every_failed_command(verify_repo: Path, repo_root: Path) -> None:
    bad = _script(repo_root, "bad.py", "import sys; sys.exit(1)\n")
    ok = _script(repo_root, "ok.py", "pass\n")
    _write_config(repo_root, json.dumps({"verify": [ok, bad]}))
    assert _verify.perform(verify_repo, repo_root) == 1
    rec = _verify.load_record(verify_repo)
    assert rec is not None and rec["failed"] == [bad]


def test_interruption_writes_nothing_and_preserves_the_previous_record(
    verify_repo: Path, repo_root: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """FR-017. A record that exists is proof a run completed.

    Written incrementally, a record interrupted after two of three passing
    commands reads as an unqualified pass — the exact shape of claim this feature
    exists to stop trusting.
    """
    _verify.write_record(verify_repo, _record(sha="old" + "0" * 37))
    before = _verify.record_path(verify_repo).read_bytes()

    ok = _script(repo_root, "ok.py", "pass\n")
    _write_config(repo_root, json.dumps({"verify": [ok, ok, ok]}))

    calls = {"n": 0}
    real = subprocess.run

    def interrupt_on_second(*args: object, **kw: object):
        if args and isinstance(args[0], list) and args[0][:1] == ["python3"]:
            calls["n"] += 1
            if calls["n"] == 2:
                raise KeyboardInterrupt
        return real(*args, **kw)  # type: ignore[arg-type]

    monkeypatch.setattr(subprocess, "run", interrupt_on_second)
    with pytest.raises(KeyboardInterrupt):
        _verify.perform(verify_repo, repo_root)

    assert _verify.record_path(verify_repo).read_bytes() == before


def test_every_run_reruns_every_command(verify_repo: Path, repo_root: Path) -> None:
    """FR-018: no resume. A prior pass is never reused to skip work."""
    counter = _script(
        repo_root, "count.py",
        "from pathlib import Path\n"
        "p = Path('runs'); p.write_text(str(int(p.read_text()) + 1 if p.exists() else 1))\n",
    )
    _write_config(repo_root, json.dumps({"verify": [counter]}))
    _verify.perform(verify_repo, repo_root)
    _verify.perform(verify_repo, repo_root)
    assert (repo_root / "runs").read_text() == "2"


def test_a_failing_then_passing_run_leaves_two_distinguishable_events(
    verify_repo: Path, repo_root: Path
) -> None:
    """SC-008: the history shows a verdict earned over attempts, not just the last one."""
    bad = _script(repo_root, "bad.py", "import sys; sys.exit(1)\n")
    ok = _script(repo_root, "ok.py", "pass\n")
    _write_config(repo_root, json.dumps({"verify": [bad]}))
    _verify.perform(verify_repo, repo_root)
    _write_config(repo_root, json.dumps({"verify": [ok]}))
    _verify.perform(verify_repo, repo_root)

    events = [
        json.loads(line)
        for line in (verify_repo / "events.jsonl").read_text().splitlines()
        if '"verify"' in line
    ]
    assert [e["exit"] for e in events] == [1, 0]
    assert events[0]["failed"] and not events[1]["failed"]


def test_no_definition_of_done_exits_zero(verify_repo: Path, repo_root: Path, capsys) -> None:
    """FR-019. An unconditional caller — a setup hook, a shared CI step — must not
    break on a repository that has not adopted the feature."""
    assert _verify.perform(verify_repo, repo_root) == 0
    assert "No definition of done configured" in capsys.readouterr().out


def test_a_malformed_config_exits_one_without_running_anything(
    verify_repo: Path, repo_root: Path, capsys
) -> None:
    """FR-012. Never silently treated as absent: silent degradation is
    indistinguishable from the defect."""
    _write_config(repo_root, '{"verify": ["pytest -q"]}')
    assert _verify.perform(verify_repo, repo_root) == 1
    assert _verify.load_record(verify_repo) is None
    assert "wfctl.json" in capsys.readouterr().out


def test_a_dirty_tree_warns_at_the_point_of_running(
    verify_repo: Path, repo_root: Path, capsys
) -> None:
    """Said when it happens, not discovered from a status line later."""
    ok = _script(repo_root, "ok.py", "pass\n")
    _write_config(repo_root, json.dumps({"verify": [ok]}))
    (repo_root / "f.txt").write_text("uncommitted")
    assert _verify.perform(verify_repo, repo_root) == 0
    out = capsys.readouterr().out
    assert "verified" in out and "uncommitted changes" in out


def test_a_tree_that_changes_mid_run_is_inconclusive(
    verify_repo: Path, repo_root: Path, capsys
) -> None:
    """FR-016. The verdict describes a mixture of two states, so it describes neither.

    Reported as its own outcome rather than as a pass or a failure, because
    neither capture supports either.
    """
    mutate = _script(repo_root, "mutate.py", "open('sneaky.txt','w').write('x')\n")
    _write_config(repo_root, json.dumps({"verify": [mutate]}))
    # Commit first: identity is (sha, dirty), and `dirty` is a boolean, so a
    # change made to an already-dirty tree leaves the pair unchanged and reads as
    # conclusive. That is sound rather than a gap — a dirty record never reports
    # complete — but it means this test only says anything from a clean tree.
    subprocess.run(["git", "-C", str(repo_root), "add", "-A"], check=True, capture_output=True)
    subprocess.run(
        ["git", "-C", str(repo_root), "commit", "-m", "scripts"],
        check=True, capture_output=True,
    )
    assert _verify.perform(verify_repo, repo_root) == 1
    rec = _verify.load_record(verify_repo)
    assert rec is not None and rec["inconclusive"] is True
    assert "inconclusive" in capsys.readouterr().out
