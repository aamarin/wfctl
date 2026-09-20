"""`wfctl status --json` writes bytes that parse whatever standard output is
attached to (US1, FR-001).

`console.print_json` styles from what it believes it is attached to —
`FORCE_COLOR` settles that belief regardless of an actual terminal, and a real
pty settles it the same way with no environment variable at all. Both reach
the corruption `test_cli_status.py`'s `CliRunner`-based tests never see: a
non-tty buffer never makes `console` believe it is a terminal in the first
place.
"""
from __future__ import annotations

import json
import os
import pty
import subprocess
import sys
from pathlib import Path

import pytest


def _wfctl() -> str:
    """The console script installed beside this interpreter — the one `uv run
    wfctl` resolves to, so the subprocess exercises the checkout under test
    rather than whatever `wfctl` happens to be first on `PATH`."""
    return str(Path(sys.executable).parent / "wfctl")


@pytest.fixture
def repo(tmp_path: Path) -> Path:
    subprocess.run(["git", "init", "-q", str(tmp_path)], check=True)
    subprocess.run(
        ["git", "-C", str(tmp_path), "config", "user.email", "test@test.com"],
        check=True,
    )
    subprocess.run(
        ["git", "-C", str(tmp_path), "config", "user.name", "Test"], check=True,
    )
    return tmp_path


def _env(**overrides: str) -> dict[str, str]:
    env = dict(os.environ)
    env["WFCTL_BRANCH"] = "423-x"
    env["WFCTL_STATE_DIR"] = overrides.pop("WFCTL_STATE_DIR", "")
    env.update(overrides)
    return env


def test_raw_stdout_parses_with_color_forced_on(repo: Path, tmp_path: Path) -> None:
    state_dir = tmp_path / "state"
    state_dir.mkdir()
    env = _env(FORCE_COLOR="3", WFCTL_STATE_DIR=str(state_dir))

    result = subprocess.run(
        [_wfctl(), "status", "--json"], cwd=repo, env=env, capture_output=True,
    )

    assert b"\x1b" not in result.stdout, result.stdout
    json.loads(result.stdout)


def test_raw_stdout_parses_under_a_pty(repo: Path, tmp_path: Path) -> None:
    state_dir = tmp_path / "state"
    state_dir.mkdir()
    env = _env(WFCTL_STATE_DIR=str(state_dir))

    master, slave = pty.openpty()
    proc = subprocess.Popen(
        [_wfctl(), "status", "--json"], cwd=repo, env=env,
        stdout=slave, stderr=subprocess.PIPE,
    )
    os.close(slave)
    chunks = []
    while True:
        try:
            chunk = os.read(master, 4096)
        except OSError:
            break
        if not chunk:
            break
        chunks.append(chunk)
    proc.wait()
    os.close(master)
    raw = b"".join(chunks)

    assert b"\x1b" not in raw, raw
    json.loads(raw)
