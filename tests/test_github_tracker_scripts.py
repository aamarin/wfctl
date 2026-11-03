"""The two GitHub scripts behind the session report's `Parent` and `PR` lines.

Each runs against a fake `gh` on PATH, so the tests reach no network. The fake
answers with a canned exit code, stdout, and stderr, and applies `--jq` with
the real `jq`, which is what `gh` does with its built-in copy.
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
from pathlib import Path

import pytest

from wfctl import _tracker

_SCRIPTS = Path(_tracker.__file__).parent / "agents" / "trackers"

_FAKE_GH = r"""#!/usr/bin/env bash
expr=""
while [[ $# -gt 0 ]]; do
  if [[ "$1" == "--jq" ]]; then expr="$2"; shift; fi
  shift
done
[[ -n "${FAKE_STDERR:-}" ]] && printf '%s\n' "$FAKE_STDERR" >&2
if [[ "${FAKE_EXIT:-0}" != 0 ]]; then
  [[ -n "${FAKE_STDOUT:-}" ]] && printf '%s\n' "$FAKE_STDOUT"
  exit "$FAKE_EXIT"
fi
printf '%s' "$FAKE_STDOUT" | jq -r "$expr"
"""

pytestmark = pytest.mark.skipif(shutil.which("jq") is None, reason="needs jq to stand in for gh's --jq")


def _run(tmp_path: Path, script: str, arg: str, *, exit: int = 0, stdout: str = "", stderr: str = "") -> subprocess.CompletedProcess:
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir(exist_ok=True)
    gh = bin_dir / "gh"
    gh.write_text(_FAKE_GH)
    gh.chmod(0o755)
    env = {
        **os.environ,
        "PATH": f"{bin_dir}{os.pathsep}{os.environ['PATH']}",
        "FAKE_EXIT": str(exit), "FAKE_STDOUT": stdout, "FAKE_STDERR": stderr,
    }
    return subprocess.run(
        ["bash", str(_SCRIPTS / script), arg], capture_output=True, text=True, env=env,
    )


# --- github-issue-parent.sh ---


def test_parent_prints_the_number_and_title(tmp_path: Path) -> None:
    result = _run(tmp_path, "github-issue-parent.sh", "432",
                  stdout=json.dumps({"number": 619, "title": "Epic: Faster session start"}))
    assert result.returncode == 0
    assert result.stdout == "#619 Epic: Faster session start\n"


def test_a_404_saying_no_parent_prints_nothing(tmp_path: Path) -> None:
    result = _run(tmp_path, "github-issue-parent.sh", "432", exit=1,
                  stdout='{"message":"No parent issue found","status":"404"}',
                  stderr="gh: No parent issue found (HTTP 404)")
    assert result.returncode == 0
    assert result.stdout == ""


def test_any_other_404_fails_instead_of_reporting_no_parent(tmp_path: Path) -> None:
    """GitHub also answers 404 for a repository the token can't read. Reading
    that as no parent would print `Parent: none` for a lookup that never
    reached the issue."""
    result = _run(tmp_path, "github-issue-parent.sh", "432", exit=1,
                  stdout='{"message":"Not Found","status":"404"}',
                  stderr="gh: Not Found (HTTP 404)")
    assert result.returncode == 1
    assert result.stdout == ""


# --- github-change-branch.sh ---


def _pr(number: int, *, fork: bool = False, state: str | None = "SUCCESS", threads: tuple = ()) -> dict:
    rollup = {"state": state} if state else None
    return {
        "number": number, "title": f"PR {number}", "isCrossRepository": fork,
        "commits": {"nodes": [{"commit": {"statusCheckRollup": rollup}}]},
        "reviewThreads": {"nodes": [{"isResolved": r} for r in threads]},
    }


def _graphql(*prs: dict) -> str:
    return json.dumps({"data": {"repository": {"pullRequests": {"nodes": list(prs)}}}})


def test_branch_prints_the_pr_with_checks_and_unresolved_threads(tmp_path: Path) -> None:
    result = _run(tmp_path, "github-change-branch.sh", "432-x",
                  stdout=_graphql(_pr(712, state="FAILURE", threads=(False, True, False))))
    assert result.returncode == 0
    assert result.stdout == "#712 PR 712 · checks: failing · 2 unresolved review threads\n"


@pytest.mark.parametrize(("state", "word"), [
    ("SUCCESS", "passing"), ("ERROR", "failing"), ("PENDING", "pending"),
    ("EXPECTED", "pending"), (None, "none"), ("SOMETHING_NEW", "something_new"),
])
def test_every_check_state_maps_to_a_word(tmp_path: Path, state: str | None, word: str) -> None:
    result = _run(tmp_path, "github-change-branch.sh", "432-x", stdout=_graphql(_pr(1, state=state)))
    assert f"· checks: {word} ·" in result.stdout


def test_one_unresolved_thread_is_singular(tmp_path: Path) -> None:
    result = _run(tmp_path, "github-change-branch.sh", "432-x", stdout=_graphql(_pr(1, threads=(False,))))
    assert result.stdout.endswith("· 1 unresolved review thread\n")


def test_a_forks_pr_from_a_branch_of_the_same_name_is_dropped(tmp_path: Path) -> None:
    """GitHub matches a head branch by name alone, so a fork's PR would
    otherwise be reported as this branch's."""
    result = _run(tmp_path, "github-change-branch.sh", "432-x",
                  stdout=_graphql(_pr(9, fork=True), _pr(712)))
    assert result.stdout.startswith("#712 ")


def test_no_open_pr_prints_nothing(tmp_path: Path) -> None:
    for answer in (_graphql(), _graphql(_pr(9, fork=True))):
        result = _run(tmp_path, "github-change-branch.sh", "432-x", stdout=answer)
        assert result.returncode == 0
        assert result.stdout == ""


def test_a_failed_call_exits_non_zero(tmp_path: Path) -> None:
    result = _run(tmp_path, "github-change-branch.sh", "432-x", exit=1, stderr="gh: HTTP 502")
    assert result.returncode != 0
