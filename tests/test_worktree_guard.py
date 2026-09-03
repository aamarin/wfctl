"""Tests for `wfctl._guard` — the cross-worktree guard's decision.

No fixtures and no worktrees. The module takes the roots as arguments precisely
so the decision table can be asserted as a function call; building the eight
worktrees these cases describe would cost more than the code under test.

`HERE` and `OTHER` are siblings under `MAIN`, which is the shape `.workmux.yaml`
produces (`worktree_dir: wt`). `AGENT` is the other shape the repo has today —
a worktree nested under a dotted directory inside the main checkout — and it is
here because the naive `startswith(repo_root)` check the issue sketched allows
every command aimed at it.
"""
from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest
from typer.testing import CliRunner, Result

from tests.conftest import git_repo
from wfctl import _guard
from wfctl.cli import app

runner = CliRunner()

MAIN = "/Users/dev/project"
HERE = "/Users/dev/project/wt/129-cross-worktree-guard"
OTHER = "/Users/dev/project/wt/105-mypy-cold-venv"
AGENT = "/Users/dev/project/.claude/worktrees/agent-7"
ROOTS = [MAIN, HERE, OTHER, AGENT]


def refuses(command: str) -> bool:
    return _guard.refusal(command, HERE, ROOTS) is not None


@pytest.mark.parametrize("command", [
    f"cat {OTHER}/AGENTS.md",
    f"head -50 {OTHER}/wfctl/cli.py",
    f"grep -rn 'def refusal' {OTHER}/wfctl",
    f"ls -la {OTHER}",
    f"diff {HERE}/pyproject.toml {OTHER}/pyproject.toml",
    f"wc -l {OTHER}/wfctl/cli.py",
    f"find {OTHER} -name '*.py'",
    f"git -C {OTHER} log --oneline -20",
    f"git -C {OTHER} diff main",
    f"git -C {OTHER} status --short",
    f"git -C {OTHER} rev-parse HEAD",
])
def test_reading_another_worktree_is_allowed(command: str) -> None:
    """Reads across the boundary are ordinary review work, not the failure.

    Comparing two branches and reading what a sibling changed are why the check
    had to be an allowlist of read verbs: a denylist written to stop `sed -i`
    stops these too, and then the guard costs more than it saves.
    """
    assert not refuses(command)


@pytest.mark.parametrize("command", [
    f"sed -i '' 's/a/b/' {OTHER}/pyproject.toml",
    f"rm -rf {OTHER}/.venv",
    f"mv {OTHER}/a {OTHER}/b",
    f"touch {OTHER}/new.py",
    f"tee {OTHER}/out.txt",
    f"python -c 'open(\"{OTHER}/f\", \"w\")'",
])
def test_mutating_another_worktree_is_refused(command: str) -> None:
    """The verbs the guard exists for, and the ones it has never heard of.

    `touch` and `python` are not in any denylist because there is no denylist —
    they are refused for the same reason a verb invented tomorrow is, which is
    the property the allowlist buys.
    """
    assert refuses(command)


@pytest.mark.parametrize("command", [
    f"cd {OTHER} && uv run mypy wfctl/",
    f"uv run --directory {OTHER} pytest -q",
    f"make -C {OTHER} test",
    f"(cd {OTHER}; pytest)",
])
def test_running_in_another_worktree_is_refused(command: str) -> None:
    """Executing is not reading, though `uv run mypy` looks harmless.

    It writes a `.venv`, builds the package and reports a result about a branch
    this session is not on — the exact sequence in #129's second failure.
    """
    assert refuses(command)


def test_a_read_that_redirects_is_refused() -> None:
    """`>` is a write whose target this module will not try to resolve.

    Refusing the whole command is the safe direction and costs a redirect into
    the session's *own* tree, which is rare enough to pay for not parsing shell.
    """
    assert refuses(f"cat {OTHER}/a.txt > {HERE}/b.txt")


def test_stderr_redirection_is_not_a_write() -> None:
    """`2>&1` and `>/dev/null` appear in half the read commands anyone writes.

    Caught once by treating every `>` as a write, and once more by splitting
    segments on a lone `&`, which turned `2>&1` into a segment starting `1`.
    """
    assert not refuses(f"git -C {OTHER} log 2>&1 | head -20")
    assert not refuses(f"ls {OTHER} 2>/dev/null")


def test_every_stage_of_a_pipeline_must_read() -> None:
    """An allowlisted verb at the front does not license what follows it."""
    assert not refuses(f"cat {OTHER}/f | grep x | wc -l")
    assert refuses(f"cat {OTHER}/f | tee {OTHER}/g")


def test_find_may_not_run_or_delete() -> None:
    """`find` is allowlisted and carries its own way out.

    Without the action check, `find <other> -delete` passes a check on the verb
    alone — an allowlist with a documented bypass in it.
    """
    assert not refuses(f"find {OTHER} -name '*.py'")
    assert refuses(f"find {OTHER} -name '*.pyc' -delete")
    assert refuses(f"find {OTHER} -name '*.py' -exec rm {{}} +")


def test_a_background_separator_still_splits_segments() -> None:
    """`&` is a command separator, and dropping it hid a mutation behind `echo`.

    Found in review: excluding `&` to protect `2>&1` made `echo hi & rm -rf
    <other>` a single segment whose verb is `echo`, so the whole command was
    allowed — a false allow in exactly the class the guard exists to stop.
    """
    assert refuses(f"echo hi & rm -rf {OTHER}/wfctl")
    assert refuses(f"cat {OTHER}/a & sed -i '' s/a/b/ {OTHER}/b")


def test_an_arrow_inside_a_quoted_pattern_is_not_a_redirect() -> None:
    """Grepping a sibling for `=>` is the read this module promises to keep.

    Found in review: treating every `>` as a redirect refused it, and with the
    wrong reason attached. A real redirect follows whitespace or a descriptor.
    """
    assert not refuses(f"grep -rn '=>' {OTHER}/src")
    assert not refuses(f"grep -n 'a->b' {OTHER}/f.c")
    assert not refuses(f"cat {OTHER}/f >> /dev/null")
    assert refuses(f"cat {OTHER}/f >> {HERE}/log")


def test_workmux_run_is_not_covered_by_the_handoff() -> None:
    """`workmux run` is "run a command in a worktree's window" — the refused verb.

    Found in review: allowlisting workmux wholesale let the escape hatch carry
    arbitrary execution into another worktree, which makes the allowlist
    self-defeating. Lifecycle verbs stay, because managing worktrees from
    anywhere is correct.
    """
    assert refuses(f"workmux run other 'rm -rf {OTHER}/.venv'")
    assert not refuses(f"workmux remove other {OTHER}")
    assert not refuses(f"workmux path other {OTHER}")


def test_a_redirect_needs_no_space_in_front_of_it() -> None:
    """`echo pwned><other>/f` is a write, and requiring whitespace missed it.

    A regression from the first review round: tightening the redirect check to
    stop `grep '=>'` being read as one required a preceding whitespace or file
    descriptor, which shell does not. The segment's verb then read as `echo` and
    the write went through — a false allow introduced while fixing a false
    refusal, which is the hazard in tightening any of these.
    """
    assert refuses(f"echo pwned>{OTHER}/file")
    assert refuses(f"echo pwned>>{OTHER}/file")
    assert refuses(f"wc -l {OTHER}/f>{OTHER}/out")


def test_both_spellings_of_redirecting_every_stream() -> None:
    """`&>` and `>&` are writes; `2>&1` and `>&2` duplicate a descriptor.

    The `&` exemption exists for the second pair and has to check what follows
    it — a path means the first pair, which is a write to that path.
    """
    assert refuses(f"echo hi &> {OTHER}/out")
    assert refuses(f"echo hi >& {OTHER}/out")
    assert not refuses(f"git -C {OTHER} log >&2")


def test_a_redirect_to_dev_null_is_exact() -> None:
    """The exemption is `/dev/null`, not anything starting with it."""
    assert not refuses(f"cat {OTHER}/f >/dev/null")
    assert refuses(f"cat {OTHER}/f >/dev/null.evil")


def test_a_command_substitution_is_judged_on_its_own_verb() -> None:
    """`echo $(rm -rf <other>)` runs `rm`, whatever the outer verb is.

    Distinct from the documented indirection gap, where the path never appears
    in the text at all. Here it does, the trespass is found, and only the verb
    check was failing open.
    """
    assert refuses(f"echo $(rm -rf {OTHER})")
    assert refuses(f"echo `rm -rf {OTHER}`")
    assert refuses(f"cat {OTHER}/x.txt $(touch {OTHER}/y)")


def test_a_local_segment_is_not_judged_by_a_remote_one() -> None:
    """Compound commands are ordinary, and each half deserves its own verdict.

    `uv run pytest && cat <other>/README.md` was refused with "`uv` is not a
    read command" — about a segment that never leaves this worktree. Judging the
    whole command against a trespass found anywhere in it refuses the local half
    for the sake of the remote one.
    """
    assert not refuses(f"uv run pytest && cat {OTHER}/README.md")
    assert not refuses(f"cat {OTHER}/a.txt && echo done > /tmp/local.log")
    assert not refuses(f"long-build & cat {OTHER}/x")
    # The remote half is still judged, which is the half that matters.
    assert refuses(f"uv run pytest && rm -rf {OTHER}/x")


def test_git_is_decided_by_subcommand() -> None:
    """`git -C <other>` reads and writes through the same entry point.

    `worktree add` is #129's *first* failure: a worktree created outside workmux
    never runs `post_create`, so it comes up with no skills and no tmux target,
    both silently.
    """
    assert not refuses(f"git -C {OTHER} show HEAD:AGENTS.md")
    assert not refuses(f"git -C {MAIN} worktree list")
    assert refuses(f"git -C {OTHER} worktree add {MAIN}/wt/new-thing")
    assert refuses(f"git -C {OTHER} checkout main")
    assert refuses(f"git -C {OTHER} commit -am wip")


def test_workmux_is_the_handoff_and_stays_allowed() -> None:
    """Refusing workmux would block the escape hatch the refusal recommends."""
    assert not refuses("workmux send 105-mypy-cold-venv 'run mypy'")
    assert not refuses("workmux add 131-something")


def test_the_session_own_worktree_is_never_the_boundary() -> None:
    """The guard fires on the *other* worktree, not on any absolute path.

    Nested roots are why this needs longest-prefix ownership: every path in this
    worktree also starts with the main checkout's root, so a first-match lookup
    would refuse every command the session runs on its own files.
    """
    assert not refuses(f"uv run pytest {HERE}/tests -q")
    assert not refuses(f"sed -i '' 's/a/b/' {HERE}/wfctl/cli.py")
    assert not refuses("uv run pytest -q")


def test_the_main_checkout_is_another_worktree() -> None:
    """Writing to the main checkout from a branch worktree is the same failure.

    It is where the naive check is weakest — every worktree path starts with the
    main root, so `startswith(repo_root)` reads the main checkout as home.
    """
    assert refuses(f"sed -i '' 's/a/b/' {MAIN}/pyproject.toml")
    assert not refuses(f"cat {MAIN}/pyproject.toml")


def test_worktrees_outside_wt_are_caught() -> None:
    """The roots come from `git worktree list`, not from a `/wt/` pattern.

    Eighteen `.claude/worktrees/agent-*` exist in this repo today. A path regex
    misses every one of them, and they sit *inside* the main checkout, so the
    prefix check reads them as ordinary subdirectories.
    """
    assert refuses(f"rm -rf {AGENT}/wfctl")
    assert not refuses(f"cat {AGENT}/AGENTS.md")


def test_the_refusal_names_the_path_the_session_and_the_handoff() -> None:
    """Exit 2 feeds this back to the model, so it is the whole user interface.

    A refusal that does not say where to go instead produces the retry loop the
    guard exists to prevent — the agent tries the same thing a different way.
    """
    message = _guard.refusal(f"uv run pytest {OTHER}/tests", HERE, ROOTS)
    assert message is not None
    assert OTHER in message
    assert HERE in message
    assert "workmux send 105-mypy-cold-venv" in message
    assert "`uv` is not a read command" in message


def test_a_command_naming_no_worktree_is_never_examined() -> None:
    """The verb allowlist only applies once a boundary is crossed.

    Otherwise the guard becomes an allowlist for every Bash call in the session,
    which is a different feature and a much worse one.
    """
    assert not refuses("rm -rf /tmp/scratch")
    assert not refuses("uv run ruff check wfctl/")


def test_no_worktree_information_means_no_refusal() -> None:
    """`git` failing must not block work — a guard is not a gate on git working."""
    assert _guard.refusal(f"rm -rf {OTHER}", "", []) is None


def test_the_hook_blocks_with_exit_2_against_real_worktrees(tmp_path: Path) -> None:
    """The end-to-end shape, against `git worktree list` rather than a fixed list.

    Exit 2 is the load-bearing detail and the only code that does the job: it
    blocks the call *and* hands stderr to the model, so the agent reads the
    reason. Exit 1 does not refuse at all — the tool call proceeds through the
    normal permission flow — so getting this wrong fails open, silently.
    """
    main = git_repo(tmp_path / "project")
    other = tmp_path / "project" / "wt" / "105-mypy-cold-venv"
    subprocess.run(
        ["git", "-C", str(main), "worktree", "add", "-b", "other", str(other)],
        check=True, capture_output=True,
    )

    def run(command: str) -> Result:
        payload = json.dumps({"cwd": str(main), "tool_input": {"command": command}})
        return runner.invoke(app, ["hook", "worktree-guard"], input=payload)

    blocked = run(f"uv run pytest {other}/tests")
    assert blocked.exit_code == 2
    assert "another worktree" in (blocked.stderr or blocked.output)

    assert run(f"cat {other}/README.md").exit_code == 0
    assert run("workmux send 105-mypy-cold-venv 'go'").exit_code == 0
