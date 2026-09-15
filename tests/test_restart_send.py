"""The session restart's sender (#371).

A stub `workmux` on `PATH` stands in for the pane: it appends its argv and the
time it ran to a file, and exits with whatever the test asks. Timings come in on
the plan, so a worker that waits two seconds in a pane waits milliseconds here.
"""
from __future__ import annotations

import json
import stat
import subprocess
import threading
import time
from pathlib import Path

import pytest

from wfctl import _restart_send
from wfctl._restart import CLEAR_TEXT, END_TEXT, START_TEXT


@pytest.fixture
def workmux(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    """Install a stub `workmux`; return a function that sets its behaviour and a
    reader for what it logged."""
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    log = tmp_path / "workmux.log"
    script = bin_dir / "workmux"

    def configure(exit_code: int = 0, sleep: float = 0.0) -> Path:
        script.write_text(
            "#!/bin/sh\n"
            f'python3 -c \'import json,sys,time; print(json.dumps({{"argv": sys.argv[1:], "t": time.time()}}))\' "$@" >> "{log}"\n'
            f"sleep {sleep}\n"
            f"exit {exit_code}\n"
        )
        script.chmod(script.stat().st_mode | stat.S_IEXEC)
        return log

    monkeypatch.setenv("PATH", f"{bin_dir}:{__import__('os').environ['PATH']}")
    return configure


def _lines(log: Path) -> list[dict]:
    return [json.loads(line) for line in log.read_text().splitlines()] if log.exists() else []


def _events(state_dir: Path) -> list[dict]:
    return [json.loads(line) for line in (state_dir / "events.jsonl").read_text().splitlines()]


def _plan(state_dir: Path, texts: list[str], parent: int, **timings: float) -> dict:
    return {
        "parent": parent, "handle": "371-x", "session": "S",
        "state_dir": str(state_dir), "texts": texts,
        "wait_cap": 5.0, "settle": 0.0, "gap": 0.0, "timeout": 5.0, **timings,
    }


def _exited_pid() -> int:
    proc = subprocess.Popen(["true"])
    proc.wait()
    return proc.pid


def test_the_worker_waits_for_its_parent_to_exit_before_the_first_send(
    tmp_path: Path, workmux
) -> None:
    """The reason the worker exists. A send issued while the `Stop` hook still
    runs lands in a pane that counts the hook as a task in progress — on Codex
    `/clear` was refused, then the hook was killed with the pending send."""
    log = workmux()
    parent = subprocess.Popen(["sleep", "0.4"])
    exited_at: list[float] = []

    def reap() -> None:
        parent.wait()
        exited_at.append(time.time())

    # Reaped by a thread so the pid really disappears; an unreaped child stays a
    # zombie that `kill(pid, 0)` still finds, and the worker would wait its cap.
    threading.Thread(target=reap).start()
    _restart_send.run(_plan(tmp_path, [END_TEXT], parent.pid))

    [line] = _lines(log)
    assert line["argv"] == ["send", "371-x", END_TEXT]
    assert exited_at and line["t"] >= exited_at[0]


def test_each_send_is_recorded_in_order_with_its_exit(tmp_path: Path, workmux) -> None:
    """The next reply end reads these to tell "sent and did not take" from
    "never sent"; without them it could only see that a send was planned."""
    log = workmux()
    _restart_send.run(_plan(tmp_path, [CLEAR_TEXT, START_TEXT], _exited_pid()))

    assert [line["argv"][2] for line in _lines(log)] == [CLEAR_TEXT, START_TEXT]
    assert [(e["event"], e["session"], e["text"], e["exit"]) for e in _events(tmp_path)] == [
        ("session-restart-send", "S", CLEAR_TEXT, 0),
        ("session-restart-send", "S", START_TEXT, 0),
    ]


def test_a_failed_send_is_recorded_and_stops_the_plan(tmp_path: Path, workmux) -> None:
    """A `/start-session` typed after a `/clear` that never went would run inside
    the session the clear was meant to end."""
    log = workmux(exit_code=3)
    _restart_send.run(_plan(tmp_path, [CLEAR_TEXT, START_TEXT], _exited_pid()))

    assert len(_lines(log)) == 1
    assert [(e["text"], e["exit"]) for e in _events(tmp_path)] == [(CLEAR_TEXT, 3)]


def test_a_hung_workmux_is_recorded_as_minus_one(tmp_path: Path, workmux) -> None:
    """A detached process nobody watches must not be able to wait forever."""
    workmux(sleep=5)
    started = time.monotonic()
    _restart_send.run(_plan(tmp_path, [END_TEXT], _exited_pid(), timeout=0.3))

    assert time.monotonic() - started < 3
    assert [(e["text"], e["exit"]) for e in _events(tmp_path)] == [(END_TEXT, -1)]


def test_main_exits_zero_on_a_plan_it_cannot_read() -> None:
    """Nobody reads its exit code or its output, and a traceback from a detached
    process goes nowhere useful."""
    assert _restart_send.main(["not json"]) == 0
    assert _restart_send.main([]) == 0
