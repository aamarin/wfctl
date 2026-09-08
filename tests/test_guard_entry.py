"""The guard reaches its decision without importing `wfctl.cli`.

`tests/test_worktree_guard.py` calls `_guard.refusal` directly, so it passes
whether or not the fast path in `wfctl/_entry.py` is wired up at all — and it
would have passed on the version of this branch where the console script still
pointed at `cli:app`. These tests are about the wiring, not the decision.

The saving is not asserted. A timing assertion in CI is a flake generator, and
the number that matters is a benchmark quoted in the PR (#135), run on one
machine, warm. What *is* mechanical is which modules got imported, and that is
the thing that would silently regress: adding a top-level `from wfctl import
cli` anywhere on this path costs 47 ms and breaks no other test.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parent.parent


def _run(code: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "-c", code], capture_output=True, text=True, cwd=REPO
    )


def test_the_guard_path_never_imports_typer_or_rich() -> None:
    """The whole point of #135, and the only part of it a test can hold.

    Asserted on `sys.modules` after the call rather than on elapsed time: the
    cost was two imports, so their absence is the durable form of the claim.
    """
    payload = json.dumps({"cwd": str(REPO), "tool_input": {"command": "git status"}})
    result = _run(
        "import sys, json\n"
        "from wfctl._hook import worktree_guard\n"
        f"worktree_guard({payload!r})\n"
        "loaded = {m for m in ('typer', 'rich', 'wfctl.cli') if m in sys.modules}\n"
        "print(sorted(loaded))\n"
    )

    assert result.returncode == 0, result.stderr
    assert result.stdout.strip() == "[]", (
        f"the guard path imported {result.stdout.strip()} — #135 exists to avoid it"
    )


def test_a_command_with_no_path_asks_git_nothing(monkeypatch: pytest.MonkeyPatch) -> None:
    """Option 1: the early-out must sit above `worktree_roots`, not below it.

    Written against the subprocess rather than the return value because both
    orderings return 0 here — putting the check after the git calls is a change
    that costs the saving and passes every other assertion in this file.
    """
    calls: list[str] = []

    import wfctl._hook as hook

    monkeypatch.setattr(hook, "worktree_roots", lambda cwd: calls.append(cwd) or ("", []))
    payload = json.dumps({"cwd": str(REPO), "tool_input": {"command": "ls -la"}})
    assert hook.worktree_guard(payload) == 0

    assert calls == [], "a command with no '/' reached the git subprocesses"


def test_a_command_naming_a_path_still_resolves_worktrees(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The other half of the same boundary.

    Without this, deleting the early-out's condition entirely — `return 0` for
    every command — passes the test above and disables the guard.
    """
    calls: list[str] = []

    import wfctl._hook as hook

    monkeypatch.setattr(hook, "worktree_roots", lambda cwd: calls.append(cwd) or ("", []))
    payload = json.dumps({"cwd": str(REPO), "tool_input": {"command": "cat /etc/hosts"}})
    assert hook.worktree_guard(payload) == 0

    assert calls == [str(REPO)]


def test_a_flag_on_the_subcommand_falls_through_to_typer() -> None:
    """`hook worktree-guard --help` must reach typer, not the fast path.

    The dispatcher matches the full argv rather than a prefix. A prefix match
    would swallow any flag added to the subcommand later and answer as though it
    were absent — and it would hang here, because the fast path reads stdin.
    """
    # The installed console script, because that is what `_entry:main` is wired
    # to — importing and calling it in-process would bypass the argv dispatch
    # this test is about.
    wfctl = Path(sys.executable).parent / "wfctl"
    if not wfctl.exists():  # pragma: no cover - editable install always has it
        pytest.skip("console script not installed in this environment")

    result = subprocess.run(
        [str(wfctl), "hook", "worktree-guard", "--help"],
        capture_output=True,
        text=True,
        cwd=REPO,
        stdin=subprocess.DEVNULL,
        timeout=60,
    )

    assert result.returncode == 0, result.stderr
    assert "worktree" in result.stdout.lower()


def test_the_console_script_resolves_to_the_dispatcher() -> None:
    """The wiring that carries the whole saving, and the quietest thing to lose.

    Every other test here passes with `wfctl = "wfctl.cli:app"` restored: the
    modules still exist, the decision is unchanged, `--help` still works. Only
    the 48 ms comes back, and nothing else in the suite would notice.
    """
    import tomllib

    with (REPO / "pyproject.toml").open("rb") as fh:
        scripts = tomllib.load(fh)["project"]["scripts"]

    assert scripts["wfctl"] == "wfctl._entry:main", (
        "pointing the console script back at cli:app restores typer and rich "
        "on the guard's path — see #135"
    )


def _through_the_dispatcher(payload: bytes) -> subprocess.CompletedProcess[bytes]:
    """`_entry.main` with the guard's own argv, in a process that reads real stdin.

    Not the installed console script: that is generated at install time, so in a
    stale environment it still resolves to `cli:app` and answers identically —
    the test would pass for the wrong reason. Setting `sys.argv` reaches the same
    dispatch without depending on when anyone last ran `uv sync`.
    """
    return subprocess.run(
        [
            sys.executable,
            "-c",
            "import sys; sys.argv = ['wfctl', 'hook', 'worktree-guard']; "
            "from wfctl._entry import main; main()",
        ],
        input=payload,
        capture_output=True,
        cwd=REPO,
        timeout=60,
    )


def test_the_dispatcher_refuses_a_cross_worktree_command() -> None:
    """The assembled path, which no other test in the repo executes.

    `test_worktree_guard.py` drives the typer door, and this module's other
    tests call `worktree_guard` in-process or exercise the fall-through. So
    dropping the `raise` in `_entry.main` disables the guard for every consumer
    while the whole suite stays green — this is the test that goes red.
    """
    here, roots = __import__("wfctl._hook", fromlist=["x"]).worktree_roots(str(REPO))
    other = next((r for r in roots if r.rstrip("/") != here.rstrip("/")), None)
    if other is None:  # pragma: no cover - the dev checkout always has siblings
        pytest.skip("needs a second worktree to cross into")

    payload = json.dumps(
        {"cwd": here, "tool_input": {"command": f"rm -rf {other}/build"}}
    ).encode()
    result = _through_the_dispatcher(payload)

    assert result.returncode == 2, result.stderr.decode()
    assert b"another worktree" in result.stderr


def test_undecodable_stdin_is_swallowed_rather_than_raised() -> None:
    """Reading stdin as text in the caller puts the decode outside the guard.

    The `except UnicodeDecodeError` in `worktree_guard` is there for the read,
    not for `json.loads` — which cannot raise it on a `str`. Hand the guard text
    and that arm goes dead: an undecodable payload leaves as a traceback and
    exit 1 where it used to exit 0 in silence, which is a hook error printed
    over work that had nothing wrong with it.
    """
    result = _through_the_dispatcher(b"\xff\xfe\x00not json")

    assert result.returncode == 0, result.stderr.decode()
    assert result.stderr == b""
