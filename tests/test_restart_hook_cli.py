"""`wfctl hook session-restart`, as the harness runs it (#371).

`test_restart_decide.py` holds the rules. This file holds the wiring around them:
the stdin and stdout contract in `contracts/hook-session-restart.md`, the event
the hook writes, the worker it starts, the directory it must not create, and the
fast path that keeps typer out of every reply end.
"""
from __future__ import annotations

import io
import json
import os
import stat
import subprocess
import sys
import time
from pathlib import Path

import pytest

from wfctl import _restart
from wfctl._restart import (
    CLEAR_TEXT,
    DEFAULT_THRESHOLD,
    END_TEXT,
    START_TEXT,
    THRESHOLD_ENV,
    amend_summary_for_late_events,
    run_hook,
)

REPO = Path(__file__).resolve().parent.parent


def _transcript(path: Path, tokens: int) -> Path:
    path.write_text(json.dumps({"message": {"usage": {
        "input_tokens": tokens, "cache_read_input_tokens": 0,
        "cache_creation_input_tokens": 0,
    }}}) + "\n")
    return path


@pytest.fixture
def repo(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    root = tmp_path / "repo"
    root.mkdir()
    subprocess.run(["git", "init", "-q", str(root)], check=True)
    monkeypatch.setenv("WFCTL_BRANCH", "371-x")
    monkeypatch.delenv("WFCTL_STATE_DIR", raising=False)
    monkeypatch.delenv(THRESHOLD_ENV, raising=False)
    monkeypatch.setenv("XDG_STATE_HOME", str(tmp_path / "xdg"))
    return root.resolve()


def _payload(repo: Path, transcript: Path, session: str = "S") -> bytes:
    return json.dumps({
        "session_id": session, "transcript_path": str(transcript), "cwd": str(repo),
    }).encode()


def _state(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, events: list[dict] = ()) -> Path:  # type: ignore[assignment]
    state = tmp_path / "state"
    state.mkdir(exist_ok=True)
    (state / "events.jsonl").write_text("".join(json.dumps(e) + "\n" for e in events))
    monkeypatch.setenv("WFCTL_STATE_DIR", str(state))
    return state


def _events(state: Path) -> list[dict]:
    return [json.loads(line) for line in (state / "events.jsonl").read_text().splitlines()]


# --- in-process: the path from payload to effect ------------------------------

def test_under_the_threshold_prints_nothing_and_creates_no_state_dir(
    repo: Path, tmp_path: Path
) -> None:
    """Most reply ends, in repos wfctl may never have run in. A directory created
    here is one per branch anyone ever replied on."""
    t = _transcript(tmp_path / "t.jsonl", DEFAULT_THRESHOLD - 1)
    assert run_hook(_payload(repo, t), os.environ) is None
    assert not (tmp_path / "xdg").exists()


def test_over_the_threshold_on_a_branch_wfctl_never_ran_on_decides_nothing(
    repo: Path, tmp_path: Path
) -> None:
    """With no log to remember the decision in, every reply end would plan the
    restart again. Nothing is the only answer that cannot repeat."""
    t = _transcript(tmp_path / "t.jsonl", DEFAULT_THRESHOLD)
    spawned: list[dict] = []
    assert run_hook(_payload(repo, t), os.environ, spawned.append, lambda _: "h") is None
    assert spawned == []
    assert not (tmp_path / "xdg").exists()


def test_over_the_threshold_records_the_decision_and_starts_the_worker(
    repo: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    state = _state(tmp_path, monkeypatch)
    t = _transcript(tmp_path / "t.jsonl", DEFAULT_THRESHOLD + 5)
    spawned: list[dict] = []

    out = run_hook(_payload(repo, t), os.environ, spawned.append, lambda root: "371-x")

    assert out is None
    [event] = _events(state)
    assert {k: event[k] for k in ("event", "session", "decision", "occupancy", "threshold", "handle")} == {
        "event": "session-restart", "session": "S", "decision": "end",
        "occupancy": DEFAULT_THRESHOLD + 5, "threshold": DEFAULT_THRESHOLD,
        "handle": "371-x",
    }
    [plan] = spawned
    assert plan["texts"] == [END_TEXT]
    assert plan["handle"] == "371-x"
    assert plan["state_dir"] == str(state)
    assert plan["parent"] == os.getpid()


def test_a_spawn_that_raises_is_recorded_as_a_send_that_never_ran(
    repo: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A worker that never started writes no send event of its own. Left
    unrecorded, `decide()` reads the decision with no send as "ambiguous, check
    again" on every later reply end — a silent, unbounded wedge with no report
    (#371 ledger). The hook must record the failure itself."""
    state = _state(tmp_path, monkeypatch)
    t = _transcript(tmp_path / "t.jsonl", DEFAULT_THRESHOLD + 5)

    def boom(_: dict) -> None:
        raise OSError("could not fork")

    out = run_hook(_payload(repo, t), os.environ, boom, lambda root: "371-x")

    assert out is None
    [_, send] = _events(state)
    assert {k: send[k] for k in ("event", "session", "text", "exit")} == {
        "event": "session-restart-send", "session": "S", "text": END_TEXT, "exit": -1,
    }

    # The next reply end reports rather than repeating the same silent decision.
    out = run_hook(_payload(repo, t), os.environ, boom, lambda root: "371-x")
    assert out is not None
    assert json.loads(out) == {
        "systemMessage": f"session restart never sent {END_TEXT} (workmux exited -1) — run it yourself"
    }


def test_a_landed_handoff_starts_the_clear_and_start_session(
    repo: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _state(tmp_path, monkeypatch, [
        {"event": "session-restart", "session": "S", "decision": "end"},
        {"event": "session-restart-send", "session": "S", "text": END_TEXT, "exit": 0},
        {"event": "end", "continued": True},
    ])
    t = _transcript(tmp_path / "t.jsonl", DEFAULT_THRESHOLD + 5)
    spawned: list[dict] = []
    run_hook(_payload(repo, t), os.environ, spawned.append, lambda root: "371-x")
    assert [p["texts"] for p in spawned] == [[CLEAR_TEXT, START_TEXT]]


# --- write state before clear: a late notify action reaches the summary ------

def test_a_push_recorded_after_the_handoff_is_folded_in_before_the_clear(
    repo: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The traced defect (#371 ledger): the push was recorded eight seconds after
    `wfctl end` wrote the summary, in the same turn, and `/clear` would otherwise
    discard the only record of it. The verb was `wfctl notify push` then and is
    `wfctl report-action push` now; what the test pins is the event either one
    writes, which is why the rename did not reach the assertions below."""
    state = _state(tmp_path, monkeypatch, [
        {"event": "session-restart", "session": "S", "decision": "end"},
        {"event": "session-restart-send", "session": "S", "text": END_TEXT, "exit": 0},
        {"ts": "2026-09-15T14:24:30Z", "event": "end", "continued": True},
        {"ts": "2026-09-15T14:24:38Z", "event": "notify-action", "action": "push"},
    ])
    (state / "session-summary.md").write_text("# Session Summary\n\nNo push mentioned.\n")
    t = _transcript(tmp_path / "t.jsonl", DEFAULT_THRESHOLD + 5)
    spawned: list[dict] = []

    run_hook(_payload(repo, t), os.environ, spawned.append, lambda root: "371-x")

    assert [p["texts"] for p in spawned] == [[CLEAR_TEXT, START_TEXT]]
    summary = (state / "session-summary.md").read_text()
    assert "No push mentioned." in summary
    assert "## Recorded After This Summary Was Written" in summary
    assert "2026-09-15T14:24:38Z — push" in summary


def test_a_declined_line_from_an_old_log_is_not_folded_in(
    repo: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """`--declined` went with the grant it was a decline of (#384). A log written
    before then can still carry the line; the handoff does not grow a section for
    a fact about authority the run no longer has a way to hold."""
    state = _state(tmp_path, monkeypatch, [
        {"event": "session-restart", "session": "S", "decision": "end"},
        {"event": "session-restart-send", "session": "S", "text": END_TEXT, "exit": 0},
        {"ts": "2026-09-15T14:24:30Z", "event": "end", "continued": True},
        {"ts": "2026-09-15T14:24:38Z", "event": "notify-declined",
         "action": "issue-close", "reason": "partial progress only"},
    ])
    original = "# Session Summary\n"
    (state / "session-summary.md").write_text(original)
    t = _transcript(tmp_path / "t.jsonl", DEFAULT_THRESHOLD + 5)

    run_hook(_payload(repo, t), os.environ, lambda _: None, lambda root: "371-x")

    assert (state / "session-summary.md").read_text() == original


def test_no_late_events_leaves_the_summary_untouched(
    repo: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    state = _state(tmp_path, monkeypatch, [
        {"event": "session-restart", "session": "S", "decision": "end"},
        {"event": "session-restart-send", "session": "S", "text": END_TEXT, "exit": 0},
        {"event": "end", "continued": True},
    ])
    original = "# Session Summary\n\nnothing new.\n"
    (state / "session-summary.md").write_text(original)
    t = _transcript(tmp_path / "t.jsonl", DEFAULT_THRESHOLD + 5)

    run_hook(_payload(repo, t), os.environ, lambda _: None, lambda root: "371-x")

    assert (state / "session-summary.md").read_text() == original


def test_amend_with_no_summary_file_is_a_silent_no_op(tmp_path: Path) -> None:
    """Nothing to amend, and the restart still has to clear — this must never
    be the reason a reply end raises."""
    events = [
        {"event": "end"},
        {"ts": "2026-09-15T14:24:38Z", "event": "notify-action", "action": "push"},
    ]
    amend_summary_for_late_events(tmp_path, events, 0)
    assert not (tmp_path / "session-summary.md").exists()


@pytest.mark.parametrize(
    "events, handle, expected",
    [
        (
            [{"event": "session-restart", "session": "S", "decision": "end"},
             {"event": "session-restart-send", "session": "S", "text": END_TEXT, "exit": 0}],
            "371-x",
            "session restart held: /end-session recorded no stop — context not cleared",
        ),
        ([], None, "session restart skipped: no workmux pane for {repo}"),
        (
            [{"event": "session-restart", "session": "S", "decision": "clear"},
             {"ts": "2026-09-15T12:33:03Z", "event": "session-restart-send",
              "session": "S", "text": CLEAR_TEXT, "exit": 0}],
            "371-x",
            "session restart sent /clear at 12:33Z and this session is still here — "
            "run /clear yourself, or /end-session first",
        ),
        (
            [{"event": "session-restart", "session": "S", "decision": "clear"},
             {"event": "session-restart-send", "session": "S", "text": CLEAR_TEXT, "exit": 1}],
            "371-x",
            "session restart never sent /clear (workmux exited 1) — run it yourself",
        ),
    ],
    ids=["hold", "skip", "not-taken-sent", "not-taken-never-sent"],
)
def test_each_report_is_one_system_message_and_starts_nothing(
    repo: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
    events: list[dict], handle: str | None, expected: str,
) -> None:
    """`systemMessage` is the channel the person sees (#298); anything else on
    stdout is a hook error in the pane."""
    state = _state(tmp_path, monkeypatch, events)
    t = _transcript(tmp_path / "t.jsonl", DEFAULT_THRESHOLD + 5)
    spawned: list[dict] = []

    out = run_hook(_payload(repo, t), os.environ, spawned.append, lambda root: handle)

    assert out is not None
    assert json.loads(out) == {"systemMessage": expected.format(repo=repo)}
    assert spawned == []
    assert _events(state)[-1]["decision"] in ("hold", "skip", "not-taken")


@pytest.mark.parametrize("stdin", [b"", b"not json", b"[1, 2]", b'{"session_id": 3}', b"\xff\xfe"])
def test_a_payload_it_cannot_read_decides_nothing(stdin: bytes) -> None:
    assert run_hook(stdin, os.environ) is None


def test_hook_main_exits_zero_and_prints_nothing_when_the_hook_raises(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Exit 2 on `Stop` blocks the stop. A bug here would turn every reply end
    into a loop in the pane this hook types into."""
    def boom(*_: object, **__: object) -> str:
        raise RuntimeError("bug")

    class Piped:
        buffer = io.BytesIO(b"{}")

        def isatty(self) -> bool:
            return False

    monkeypatch.setattr(_restart, "run_hook", boom)
    monkeypatch.setattr(sys, "stdin", Piped())
    assert _restart.hook_main() == 0
    assert capsys.readouterr().out == ""


# --- as a process: the fast path and the detach -------------------------------

def _entry(*args: str, stdin: bytes = b"", env: dict | None = None) -> subprocess.CompletedProcess[bytes]:
    code = (
        "import sys\n"
        f"sys.argv = ['wfctl', *{list(args)!r}]\n"
        "from wfctl import _entry\n"
        "try:\n"
        "    _entry.main()\n"
        "finally:\n"
        "    loaded = sorted(m for m in ('typer', 'rich', 'wfctl.cli') if m in sys.modules)\n"
        "    sys.stderr.write('LOADED=' + ','.join(loaded) + '\\n')\n"
    )
    return subprocess.run(
        [sys.executable, "-c", code], input=stdin, capture_output=True, cwd=REPO,
        env=env,
    )


def test_the_exact_argv_takes_the_fast_path_and_loads_no_cli() -> None:
    """The saving is typer and rich on every reply end. Asserted on what got
    imported, as the guard's test does, because a timing assertion flakes."""
    result = _entry("hook", "session-restart", stdin=b"{}")
    assert result.returncode == 0, result.stderr
    assert result.stdout == b""
    assert b"LOADED=\n" in result.stderr


def test_the_hook_exits_before_the_worker_sends(
    repo: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The ordering the detached worker exists for, observed end to end: a stub
    `workmux` records when the send ran, and it must be after the hook process
    had already exited."""
    state = _state(tmp_path, monkeypatch)
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    log = tmp_path / "sends.log"
    stub = bin_dir / "workmux"
    stub.write_text(
        "#!/bin/sh\n"
        'if [ "$1" = list ]; then\n'
        f"  printf '[{{\"handle\": \"371-x\", \"path\": \"{repo}\"}}]'\n"
        "  exit 0\n"
        "fi\n"
        f'python3 -c \'import json,sys,time; print(json.dumps({{"argv": sys.argv[1:], "t": time.time()}}))\' "$@" >> "{log}"\n'
    )
    stub.chmod(stub.stat().st_mode | stat.S_IEXEC)
    env = {**os.environ, "PATH": f"{bin_dir}:{os.environ['PATH']}"}
    t = _transcript(tmp_path / "t.jsonl", DEFAULT_THRESHOLD + 5)

    result = _entry("hook", "session-restart", stdin=_payload(repo, t), env=env)
    hook_exited = time.time()
    assert result.returncode == 0, result.stderr
    assert _events(state)[0]["decision"] == "end"

    # Until a whole line is there, not until the file is: the stub's `>>` creates
    # the file before the line that goes in it, and under a loaded suite the read
    # lands in between.
    deadline = time.time() + 15
    while not (log.exists() and log.read_text().endswith("\n")) and time.time() < deadline:
        time.sleep(0.1)
    [line] = [json.loads(x) for x in log.read_text().splitlines()]
    assert line["argv"] == ["send", "371-x", END_TEXT]
    assert line["t"] > hook_exited

    deadline = time.time() + 5
    while len(_events(state)) < 2 and time.time() < deadline:
        time.sleep(0.1)
    assert [(e["event"], e["text"], e["exit"]) for e in _events(state)[1:]] == [
        ("session-restart-send", END_TEXT, 0)
    ]


def test_run_by_hand_on_a_terminal_prints_usage_instead_of_hanging() -> None:
    """A read to EOF on a terminal looks like a hang until Ctrl-D (#385)."""
    import pty

    primary, secondary = pty.openpty()
    try:
        code = (
            "import sys\n"
            "sys.argv = ['wfctl', 'hook', 'session-restart']\n"
            "from wfctl import _entry\n"
            "_entry.main()\n"
        )
        result = subprocess.run(
            [sys.executable, "-c", code], stdin=secondary, capture_output=True,
            cwd=REPO, timeout=10,
        )
    finally:
        os.close(primary)
        os.close(secondary)
    assert result.returncode == 0
    assert b"reads a Claude Code Stop payload on stdin" in result.stderr
