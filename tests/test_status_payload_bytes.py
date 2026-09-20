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
import shutil
import subprocess
from pathlib import Path

import pytest

from wfctl._contract import wfctl_binary


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
        [wfctl_binary(), "status", "--json"], cwd=repo, env=env, capture_output=True,
    )

    assert b"\x1b" not in result.stdout, result.stdout
    json.loads(result.stdout)


def test_raw_stdout_parses_under_a_pty(repo: Path, tmp_path: Path) -> None:
    state_dir = tmp_path / "state"
    state_dir.mkdir()
    env = _env(WFCTL_STATE_DIR=str(state_dir))

    master, slave = pty.openpty()
    proc = subprocess.Popen(
        [wfctl_binary(), "status", "--json"], cwd=repo, env=env,
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


def test_raw_stdout_keeps_non_ascii_bytes_as_utf8() -> None:
    """A blocked step's remedy carries a real em dash (`_block_remedy`) —
    `json.dumps`' default `ensure_ascii=True` would escape it to `\\u2014`
    instead of writing raw UTF-8, a byte-level regression `console.print_json`
    never had until the swap to a bare `sys.stdout.write` (FR-001)."""
    from wfctl._contract import fixture_states

    env = fixture_states()["blocked"]
    try:
        result = subprocess.run(
            [wfctl_binary(), "status", "--json"], cwd=env.repo_root,
            env={**os.environ, "WFCTL_STATE_DIR": str(env.agent_dir)},
            capture_output=True, check=True,
        )
    finally:
        shutil.rmtree(env.repo_root, ignore_errors=True)

    assert "—".encode() in result.stdout, result.stdout
    assert b"\\u2014" not in result.stdout
    json.loads(result.stdout)


def test_piping_into_a_closed_reader_exits_clean_not_a_traceback(
    repo: Path, tmp_path: Path,
) -> None:
    """The exact shell shape the handoff reproduced this with: `wfctl status
    --json | head -c 1` used to raise `BrokenPipeError` as an uncaught
    traceback once `console.print_json`'s swallowed handling was lost in the
    swap to a bare `sys.stdout.write`."""
    state_dir = tmp_path / "state"
    state_dir.mkdir()
    env = _env(WFCTL_STATE_DIR=str(state_dir))

    proc = subprocess.run(
        ["bash", "-c", 'set -o pipefail; "$0" status --json | head -c 1 >/dev/null', wfctl_binary()],
        cwd=repo, env=env, capture_output=True, timeout=5,
    )

    assert proc.returncode == 0, proc.stderr
    assert b"BrokenPipeError" not in proc.stderr
    assert b"Traceback" not in proc.stderr
