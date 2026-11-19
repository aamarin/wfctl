"""Tests for the guard's review check (`wfctl/_review_gate.py`).

Each test pipes a hook payload into `_hook.worktree_guard` and reads the exit
code and stderr, the same way the host does. The repository is real: a bare
`origin`, a `main` checkout, and worktrees on `604-x` and `630-x`. `gh` is a
stub on `PATH` that answers `gh repo view` and `gh pr view` from a table each
test sets.
"""
from __future__ import annotations

import json
import os
import shlex
import subprocess
import sys
import time
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

import pytest

from wfctl import _review, _review_config, _review_gate
from wfctl.guard import _hook
from wfctl._paths import resolve_agent_dir

REPO = Path(__file__).resolve().parent.parent
THIS_REPO = "acme/widgets"

_STUB = """\
#!{python}
import json, os, sys, time
table = json.load(open(os.environ["GH_STUB"]))
with open(os.environ["GH_STUB"] + ".calls", "a") as log:
    log.write(json.dumps(sys.argv[1:]) + "\\n")
if table.get("hang"):
    time.sleep(30)
if table.get("fail"):
    print("HTTP 502: Bad Gateway", file=sys.stderr)
    sys.exit(1)
args = sys.argv[1:]
if args[:2] == ["repo", "view"]:
    print(json.dumps({{"nameWithOwner": table["repo"]}}))
    sys.exit(0)
if args[:2] == ["pr", "view"]:
    rest, words = [], iter(args[2:])
    for word in words:
        if word in ("-R", "--json"):
            next(words)
        elif not word.startswith("-"):
            rest.append(word)
    found = table["prs"].get(rest[0] if rest else "")
    if found is None:
        print("no pull requests found", file=sys.stderr)
        sys.exit(1)
    print(json.dumps(found))
    sys.exit(0)
print("unknown command", file=sys.stderr)
sys.exit(1)
"""


def git(cwd: Path, *args: str) -> str:
    return subprocess.run(
        ["git", "-C", str(cwd), *args], check=True, capture_output=True, text=True,
    ).stdout.strip()


def commit(repo: Path, name: str) -> str:
    (repo / name).write_text(f"{name}\n")
    git(repo, "add", name)
    git(repo, "commit", "-q", "-m", f"add {name}")
    return git(repo, "rev-parse", "HEAD")


@dataclass
class Repos:
    tmp: Path
    main: Path
    feature: Path
    other: Path
    table: Path

    def gh(self, **table: object) -> None:
        current = json.loads(self.table.read_text())
        self.table.write_text(json.dumps({**current, **table}))

    def gh_calls(self) -> list[list[str]]:
        log = Path(f"{self.table}.calls")
        return [json.loads(line) for line in log.read_text().splitlines()] if log.exists() else []

    def complete(self, root: Path, branch: str, only: str | None = None) -> None:
        """Run every review group, or only `only`, to completion on `branch`.

        The groups are the ones the guard requires plus the working tree's, the
        list `wfctl review start` accepts (FR-010a)."""
        agent_dir = resolve_agent_dir(root, branch)
        head = git(root, "rev-parse", "HEAD")
        required = _review_config.required_at(root, head, "refs/remotes/origin/main")[0]
        names = {g.name for g in required}
        groups = [*required, *(g for g in _review_config.load(root)[0] if g.name not in names)]
        for group in groups:
            if only is not None and group.name != only:
                continue
            started = _review.start(root, agent_dir, group, cap=9)
            if started.run is None:
                continue
            for rid in started.expected:
                (started.run.path / f"{rid}.md").write_text(
                    f"Reviewed: {started.head[:7]}\n\nNo findings.\n\nVerdict: Approve\n"
                )
            assert _review.check(agent_dir, group.name).complete


@pytest.fixture
def repos(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Repos:
    """`main` with one commit, and worktrees on `604-x` and `630-x`, each one
    commit past it and pushed.

    `origin/HEAD` is set by hand because a clone of an empty bare repository
    doesn't record it, and `trunk_branch` reads it first. Every variable the
    `agent_dir` and `storyctl_dir` fixtures in `conftest.py` set is cleared, or
    a test would judge the branch the variable names and refuse for the wrong
    reason.
    """
    origin = tmp_path / "origin.git"
    subprocess.run(["git", "init", "-q", "--bare", "-b", "main", str(origin)], check=True)
    main = tmp_path / "widgets"
    subprocess.run(["git", "init", "-q", "-b", "main", str(main)], check=True)
    for key, val in (("user.email", "test@test.com"), ("user.name", "Test")):
        git(main, "config", key, val)
    commit(main, "init")
    git(main, "remote", "add", "origin", str(origin))
    git(main, "push", "-q", "-u", "origin", "main")
    git(main, "symbolic-ref", "refs/remotes/origin/HEAD", "refs/remotes/origin/main")
    worktrees = []
    for branch in ("604-x", "630-x"):
        path = tmp_path / branch
        git(main, "worktree", "add", "-q", "-b", branch, str(path), "main")
        commit(path, f"{branch}.txt")
        git(path, "push", "-q", "origin", branch)
        worktrees.append(path)

    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    stub = bin_dir / "gh"
    stub.write_text(_STUB.format(python=sys.executable))
    stub.chmod(0o755)
    table = tmp_path / "gh.json"
    table.write_text(json.dumps({
        "repo": THIS_REPO,
        "prs": {
            "630": {"headRefName": "630-x", "headRefOid": git(worktrees[1], "rev-parse", "HEAD")},
        },
    }))
    monkeypatch.setenv("PATH", f"{bin_dir}{os.pathsep}{os.environ['PATH']}")
    monkeypatch.setenv("GH_STUB", str(table))
    for name in ("WFCTL_BRANCH", "WFCTL_STATE_DIR", "WFCTL_REPO_ROOT", "WFCTL_SPEC_DIR"):
        monkeypatch.delenv(name, raising=False)
    monkeypatch.setenv("XDG_STATE_HOME", str(tmp_path / "xdg"))
    return Repos(tmp_path, main, worktrees[0], worktrees[1], table)


Guard = Callable[..., tuple[int, str]]

MONEY = {"group": "money-rules", "reviewers": [{"name": "claude", "count": 1}]}


def amend(root: Path) -> None:
    """Fold `wfctl.json` into the branch's one commit, so the guard reads it
    from the head as CI does."""
    git(root, "add", "wfctl.json")
    git(root, "commit", "-q", "--amend", "--no-edit")


def on_main(repos: Repos, config: str) -> None:
    """Commit `config` as `wfctl.json` on `main` and push it, so
    `origin/main` lists it and the feature branches don't."""
    (repos.main / "wfctl.json").write_text(config)
    git(repos.main, "add", "wfctl.json")
    git(repos.main, "commit", "-q", "-m", "config")
    git(repos.main, "push", "-q", "origin", "main")


@pytest.fixture
def guard(capsys: pytest.CaptureFixture[str]) -> Guard:
    """Run one payload through the guard and return its exit code and stderr."""

    def run(command: str, cwd: Path | str | None) -> tuple[int, str]:
        payload: dict[str, object] = {"tool_input": {"command": command}}
        if cwd is not None:
            payload["cwd"] = str(cwd)
        code = _hook.worktree_guard(json.dumps(payload).encode())
        return code, capsys.readouterr().err

    return run


def lines(err: str) -> list[str]:
    return [line for line in err.splitlines() if line.startswith("✗")]


# --- judging (T021) ----------------------------------------------------------------


def test_a_reviewed_branch_opens_its_pull_request(repos: Repos, guard: Guard) -> None:
    """The check's whole job is to stand aside once every group has reviewed
    the head, so a reviewed branch has to pass silently."""
    repos.complete(repos.feature, "604-x")

    assert guard("gh pr create --fill", repos.feature) == (0, "")


def test_an_unreviewed_branch_is_refused_with_its_commits_under_each_group(
    repos: Repos, guard: Guard,
) -> None:
    """The refusal is what the agent acts on, so it has to name every group
    and every commit, in run order, including a group the repository added."""
    (repos.feature / "wfctl.json").write_text(json.dumps({"review": {"groups": [
        {"group": "money-rules", "reviewers": [{"name": "claude", "count": 1}]},
    ]}}))
    amend(repos.feature)
    head = git(repos.feature, "rev-parse", "HEAD")[:7]

    code, err = guard("gh pr create --fill", repos.feature)

    assert code == 2
    assert err == (
        "✗ 604-x has commits no review covered:\n"
        f"  security     {head} add 604-x.txt\n"
        f"  code         {head} add 604-x.txt\n"
        f"  money-rules  {head} add 604-x.txt\n"
        "  Run the review groups (wfctl review start <group>), or ask a person to run\n"
        "  `wfctl review sign-off` in their own terminal.\n"
    )


def test_a_fix_the_code_group_commits_is_unreviewed_for_security(
    repos: Repos, guard: Guard,
) -> None:
    """US3 scenario 7. Every group has to review the newest commit, or the code
    group's fixes would reach `main` without a security review."""
    repos.complete(repos.feature, "604-x", only="security")
    fix = commit(repos.feature, "fix.txt")
    repos.complete(repos.feature, "604-x", only="code")

    code, err = guard("gh pr create --fill", repos.feature)

    assert code == 2
    assert f"  security  {fix[:7]} add fix.txt" in err
    assert "code " not in err


def test_a_sign_off_allows_the_head_it_covers_and_not_a_commit_after_it(
    repos: Repos, guard: Guard,
) -> None:
    """US3 scenarios 4 and 5. A sign-off covers the commits that existed when a
    person read them, never one added later."""
    agent_dir = resolve_agent_dir(repos.feature, "604-x")
    _review.sign_off(agent_dir, git(repos.feature, "rev-parse", "HEAD"))
    assert guard("gh pr create --fill", repos.feature) == (0, "")

    later = commit(repos.feature, "later.txt")
    code, err = guard("gh pr create --fill", repos.feature)

    assert code == 2
    assert f"security  {later[:7]} add later.txt" in err
    assert "add 604-x.txt" not in err


def test_an_ancestor_test_answering_no_is_an_answer_not_an_error(
    repos: Repos, guard: Guard,
) -> None:
    """`merge-base --is-ancestor` exits 1 to say no. Read as a failure, a
    sign-off on another line of history would turn every check into the error
    refusal instead of listing the commits."""
    agent_dir = resolve_agent_dir(repos.feature, "604-x")
    _review.sign_off(agent_dir, git(repos.other, "rev-parse", "HEAD"))

    code, err = guard("gh pr create --fill", repos.feature)

    assert code == 2
    assert "has commits no review covered" in err
    assert "failed" not in err


def test_a_half_written_record_gives_the_error_refusal_naming_the_file(
    repos: Repos, guard: Guard,
) -> None:
    """US3 scenario 6. A broken record read as missing would look like a branch
    nobody reviewed, and read as reviewed it would let anything through."""
    repos.complete(repos.feature, "604-x")
    record = resolve_agent_dir(repos.feature, "604-x") / "reviews/security/last-reviewed.json"
    record.write_text('{"sha": ')

    code, err = guard("gh pr create --fill", repos.feature)

    assert code == 2
    assert err.startswith(f"✗ the review check failed: can't read {record}")


def test_an_unreadable_review_config_gives_the_error_refusal(
    repos: Repos, guard: Guard,
) -> None:
    """Without the config the check can't know which groups to ask about, and
    guessing the defaults would skip a group the repository added."""
    (repos.feature / "wfctl.json").write_text("{not json")
    amend(repos.feature)
    head = git(repos.feature, "rev-parse", "HEAD")[:7]

    code, err = guard("gh pr create --fill", repos.feature)

    assert code == 2
    assert (
        f"✗ the review check failed: can't read the review config: wfctl.json at {head}: "
        "not valid JSON"
    ) in err


def test_a_group_the_branch_removed_is_still_required(repos: Repos, guard: Guard) -> None:
    """FR-010. A branch whose `wfctl.json` drops a group the trunk lists would
    otherwise pass the guard and then fail CI, which requires the trunk's
    groups."""
    on_main(repos, json.dumps({"review": {"groups": [MONEY]}}))
    repos.complete(repos.feature, "604-x", only="security")
    repos.complete(repos.feature, "604-x", only="code")

    code, err = guard("gh pr create --fill", repos.feature)

    assert code == 2
    head = git(repos.feature, "rev-parse", "HEAD")[:7]
    assert err.splitlines()[1:2] == [f"  money-rules  {head} add 604-x.txt"]


def test_a_group_only_in_the_uncommitted_file_is_not_required(
    repos: Repos, guard: Guard,
) -> None:
    """A user can try a new group before it's enforced. Until it's committed,
    CI doesn't require it, so the guard doesn't either."""
    (repos.feature / "wfctl.json").write_text(json.dumps({"review": {"groups": [MONEY]}}))
    repos.complete(repos.feature, "604-x", only="security")
    repos.complete(repos.feature, "604-x", only="code")

    assert guard("gh pr create --fill", repos.feature) == (0, "")


def test_a_broken_review_key_on_the_trunk_names_the_trunk(repos: Repos, guard: Guard) -> None:
    """The fix is a PR against the trunk, so the refusal names the trunk's
    file rather than the one in the working tree, which reads fine."""
    on_main(repos, json.dumps({"review": []}))
    repos.complete(repos.feature, "604-x")

    code, err = guard("gh pr create --fill", repos.feature)

    assert code == 2
    assert (
        "✗ the review check failed: can't read the review config: wfctl.json at "
        "origin/main: review must be an object"
    ) in err


def test_no_trunk_branch_gives_the_error_refusal(repos: Repos, guard: Guard) -> None:
    """With no trunk the check can't find where the branch started, so it can't
    say which commits are the branch's own."""
    (repos.feature / "wfctl.json").write_text(json.dumps({"trunk": "nope"}))

    code, err = guard("gh pr create --fill", repos.feature)

    assert code == 2
    assert "✗ the review check failed: can't find the trunk branch; set trunk in wfctl.json" in err


def test_an_invalid_cap_on_the_branch_fails_the_guard_like_any_review_setting(
    repos: Repos, guard: Guard,
) -> None:
    """`review.rounds` goes through the same load as every other `review`
    setting, so a value the check can't use is an error refusal and never a
    quiet default. The guard reads the branch's `wfctl.json` as committed,
    the way CI does, so the bad value is committed here."""
    (repos.feature / "wfctl.json").write_text(json.dumps({"review": {"rounds": -1}}))
    git(repos.feature, "add", "wfctl.json")
    git(repos.feature, "commit", "-q", "-m", "bad cap")

    code, err = guard("gh pr create --fill", repos.feature)

    assert code == 2
    assert "review.rounds must be a whole number of 0 or more" in err


def test_a_branch_that_names_another_trunk_still_has_its_commits_counted(
    repos: Repos, guard: Guard,
) -> None:
    """The guard reads the trunk from the default branch. A branch that points
    `trunk` at its own head would otherwise hide every commit from the check."""
    git(repos.feature, "branch", "loose", "HEAD")
    (repos.feature / "wfctl.json").write_text(json.dumps({"trunk": "loose"}))

    code, err = guard("gh pr create --fill", repos.feature)

    assert code == 2
    assert "604-x.txt" in err


def test_the_main_checkout_still_merges_a_reviewed_branch_with_origin_head_set(
    repos: Repos, guard: Guard,
) -> None:
    repos.complete(repos.other, "630-x")

    assert guard("gh pr merge 630", repos.main) == (0, "")


def test_any_other_error_after_a_match_refuses_naming_it(
    repos: Repos, guard: Guard, monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A bug in the check must not become a pass. The guard's worktree check
    allows on error, and copying that here would let every bug through."""

    def broken(*args: object, **kwargs: object) -> object:
        raise RuntimeError("disk on fire")

    monkeypatch.setattr(_review, "unreviewed", broken)

    code, err = guard("gh pr create --fill", repos.feature)

    assert code == 2
    assert "✗ the review check failed: disk on fire" in err


def test_only_the_error_refusal_names_the_persons_own_terminal(
    repos: Repos, guard: Guard,
) -> None:
    """A sign-off can't get past a broken check, so the error refusal names the
    one way out. A judged refusal points at the review groups instead, and
    naming the terminal there would invite skipping them."""
    _, judged = guard("gh pr create --fill", repos.feature)
    _, failed = guard("gh pr create --fill", None)

    assert "A sign-off\n  won't get past this. A person can run the same command" in failed
    assert "where this hook doesn't run" in failed
    assert "where this hook doesn't run" not in judged


def test_an_echo_that_quotes_gh_pr_create_is_refused_on_an_unreviewed_branch(
    repos: Repos, guard: Guard,
) -> None:
    """The match is on the text by design (spec Edge Cases), so `bash -c` and
    a full path to `gh` are caught too. The cost is one confusing refusal."""
    code, err = guard('echo "gh pr create"', repos.feature)

    assert code == 2
    assert "has commits no review covered" in err


def test_text_after_the_pull_request_command_doesnt_count(
    repos: Repos, guard: Guard,
) -> None:
    """Nothing after the command can change what it already did, so a trailing
    `&& echo done` is judged as the command alone."""
    repos.complete(repos.feature, "604-x")

    assert guard("gh pr create --fill && echo done", repos.feature) == (0, "")


def test_gh_pr_new_is_judged_as_gh_pr_create(repos: Repos, guard: Guard) -> None:
    """`new` is `gh`'s built-in second name for `create`."""
    code, err = guard("gh pr new --fill", repos.feature)

    assert code == 2
    assert "has commits no review covered" in err


def test_gh_pr_merge_with_no_argument_judges_the_current_branchs_pull_request(
    repos: Repos, guard: Guard,
) -> None:
    """A merge is judged at `headRefOid`, the commit GitHub would merge, which
    can differ from the local head."""
    repos.complete(repos.feature, "604-x")
    pushed = git(repos.feature, "rev-parse", "HEAD")
    commit(repos.feature, "local-only.txt")
    repos.gh(prs={"": {"headRefName": "604-x", "headRefOid": pushed}})

    assert guard("gh pr merge --squash", repos.feature) == (0, "")
    assert ["pr", "view", "--json", "headRefName,headRefOid"] in repos.gh_calls()


# --- matching (T022) ---------------------------------------------------------------


@pytest.mark.parametrize("command", [
    f"gh -R {THIS_REPO} pr merge 630",
    f"gh -R={THIS_REPO} pr merge 630",
    f"gh -R{THIS_REPO} pr merge 630",
    f"gh --repo {THIS_REPO} pr merge 630",
    f"gh --repo={THIS_REPO} pr merge 630",
    f"gh pr -R {THIS_REPO} merge 630",
    f"gh pr -R={THIS_REPO} merge 630",
    f"gh pr -R{THIS_REPO} merge 630",
    f"gh pr --repo {THIS_REPO} merge 630",
    f"gh pr --repo={THIS_REPO} merge 630",
])
def test_an_r_flag_before_pr_or_the_verb_is_still_matched(
    repos: Repos, guard: Guard, command: str,
) -> None:
    """FR-012. `gh` accepts `-R` in both places and in three spellings, and
    each one missed is a merge the check never sees."""
    code, err = guard(command, repos.main)

    assert code == 2
    assert "630-x has commits no review covered" in err


@pytest.mark.parametrize("command", [
    "GH pr merge 630", "Gh pr merge 630", "/opt/homebrew/bin/Gh pr merge 630",
])
def test_the_program_name_matches_in_any_case(
    repos: Repos, guard: Guard, command: str,
) -> None:
    """macOS finds programs without regard to case, so `GH` runs `gh`."""
    code, err = guard(command, repos.main)

    assert code == 2
    assert "630-x has commits no review covered" in err


def test_a_gh_api_create_in_upper_case_is_matched(guard: Guard, tmp_path: Path) -> None:
    """The same case rule for the `gh api` form."""
    code, err = guard("GH api repos/{owner}/{repo}/pulls -f head=x -f base=main", tmp_path)

    assert code == 2
    assert "open the pull request with gh pr create" in err


@pytest.mark.parametrize("endpoint", ["merge", "merge-async"])
def test_the_api_merge_endpoints_are_judged_as_that_pull_request(
    repos: Repos, guard: Guard, endpoint: str,
) -> None:
    """Both endpoints merge, so both are judged like `gh pr merge 630`."""
    code, err = guard(f"gh api -X PUT repos/{{owner}}/{{repo}}/pulls/630/{endpoint}", repos.main)

    assert code == 2
    assert "630-x has commits no review covered" in err


@pytest.mark.parametrize("command", [
    "gh api repos/{owner}/{repo}/pulls -f head=630-x -f base=main",
    "gh api repos/{owner}/{repo}/pulls -fhead=x -fbase=main",
    "gh api repos/{owner}/{repo}/pulls --field=head=x",
    "gh api -XPOST repos/{owner}/{repo}/pulls",
    "gh api -X POST repos/{owner}/{repo}/pulls/",
    'gh api "repos/{owner}/{repo}/pulls?x=1" --raw-field head=x',
])
def test_a_gh_api_create_is_refused_every_time(
    repos: Repos, guard: Guard, command: str,
) -> None:
    """The branch a create acts on sits in its body, and judging the current
    branch instead would let another branch's pull request open unreviewed."""
    repos.complete(repos.feature, "604-x")

    code, err = guard(command, repos.feature)

    assert code == 2
    assert lines(err) == [
        "✗ open the pull request with gh pr create so the review check can judge its branch",
    ]


@pytest.mark.parametrize(("mutation", "verb"), [
    ("createPullRequest", "create"),
    ("mergePullRequest", "merge"),
    ("enablePullRequestAutoMerge", "merge"),
    ("enqueuePullRequest", "merge"),
])
def test_a_graphql_mutation_is_refused_naming_the_gh_pr_command(
    repos: Repos, guard: Guard, mutation: str, verb: str,
) -> None:
    """A merge queue merges too, so `enqueuePullRequest` is on the list."""
    repos.complete(repos.feature, "604-x")

    code, err = guard(f"gh api graphql -f query='mutation {{ {mutation}(input: {{}}) }}'",
                      repos.feature)

    assert code == 2
    assert f"with gh pr {verb} so the review check can judge its branch" in err


@pytest.mark.parametrize("command", [
    'gh api "$URL" --input body.json',
    'gh api "repos/{owner}/{repo}/pulls/$N/merge" -X PUT',
])
def test_a_write_to_a_variable_api_path_is_refused(
    repos: Repos, guard: Guard, command: str,
) -> None:
    """The check can't read which endpoint a variable path names, and one of
    them merges."""
    repos.complete(repos.feature, "604-x")

    code, err = guard(command, repos.feature)

    assert code == 2
    assert lines(err) == [
        "✗ write the gh api path out plainly; the check can't read where it writes",
    ]


def test_a_read_through_a_variable_api_path_is_not_matched(guard: Guard, tmp_path: Path) -> None:
    """A read can't open or merge a pull request, and the agent reads review
    comments this way."""
    assert guard('gh api "repos/{owner}/{repo}/pulls/$N/comments"', tmp_path) == (0, "")


@pytest.mark.parametrize("command", [
    "gh api graphql -F query=@mutation.graphql",
    "gh api graphql --input q.json",
])
def test_a_graphql_query_from_a_file_is_refused(
    repos: Repos, guard: Guard, command: str,
) -> None:
    """The mutation sits in a file the check doesn't read."""
    repos.complete(repos.feature, "604-x")

    code, err = guard(command, repos.feature)

    assert code == 2
    assert lines(err) == [
        "✗ put the GraphQL query in the command; the check doesn't read files",
    ]


@pytest.mark.parametrize("command", [
    "gh api /graphql --input m.json",
    "gh api /graphql -F query=@m.graphql",
    "gh api https://api.github.com/graphql --input m.json",
])
def test_a_graphql_query_from_a_file_is_refused_at_any_spelling_of_the_endpoint(
    guard: Guard, tmp_path: Path, command: str,
) -> None:
    """`/graphql` and a full URL reach the same endpoint as `graphql`, and a
    mutation kept in a file is invisible to the mutation-name check. Found by
    security reviewer s2 on #638's own panel."""
    code, err = guard(command, tmp_path)

    assert code == 2
    assert lines(err) == [
        "✗ put the GraphQL query in the command; the check doesn't read files",
    ]


@pytest.mark.parametrize("command", [
    "gh api repos/{owner}/{repo}/pulls/630/comments",
    "gh api repos/{owner}/{repo}/pulls",
    "gh version",
    "gh help pr",
    "rg 'gh pr' wfctl/",
    'git commit -m "run `gh pr` first"',
])
def test_commands_that_cant_open_or_merge_are_not_matched(
    guard: Guard, tmp_path: Path, command: str,
) -> None:
    """These run all the time while a branch is unreviewed. A closing quote or
    backtick glued to `pr` is dropped before the word is read."""
    assert guard(command, tmp_path) == (0, "")


@pytest.mark.parametrize("command", [
    "wfctl review sign-off",
    "uv run wfctl review signoff",
    "wfctl review sign_off",
    "wfctl review --verbose sign-off",
])
def test_every_sign_off_spelling_is_refused(guard: Guard, tmp_path: Path, command: str) -> None:
    """FR-013. The hook exists to stop the agent from signing off for a person."""
    code, err = guard(command, tmp_path)

    assert code == 2
    assert err == (
        "✗ wfctl review sign-off is for a person to run in their own terminal, not an agent.\n"
    )


def test_a_command_with_no_gh_merge_or_sign_never_reaches_the_review_check(
    guard: Guard, monkeypatch: pytest.MonkeyPatch,
) -> None:
    """FR-016. The guard runs before every Bash call, so a command that can't
    match pays a substring test and nothing else: no import, no git call."""
    monkeypatch.delitem(sys.modules, "wfctl._review_gate", raising=False)

    def no_subprocess(*args: object, **kwargs: object) -> object:
        raise AssertionError("the review check ran a subprocess")

    monkeypatch.setattr(subprocess, "run", no_subprocess)

    assert guard("ls -la", None) == (0, "")
    assert "wfctl._review_gate" not in sys.modules


# --- gh's command words (T023) -----------------------------------------------------


@pytest.mark.parametrize("command", [
    "gh pr $(git push -q) create", "gh pr 'merge' 630", "gh pr m* 630",
])
def test_an_unplain_verb_after_pr_is_refused(
    repos: Repos, guard: Guard, command: str,
) -> None:
    """R6 pattern 8. The check can't tell whether a word it can't read opens or
    merges a pull request, so it refuses on a reviewed branch too."""
    repos.complete(repos.feature, "604-x")

    code, err = guard(command, repos.feature)

    assert code == 2
    assert "✗ write gh's command words out plainly; the check can't read them" in lines(err)


@pytest.mark.parametrize(("command", "word"), [
    ("gh stack merge", "stack"),
    ("gh stack submit", "stack"),
    ("gh co 630", "co"),
    ("gh copilot", "copilot"),
    ("gh agent-task", "agent-task"),
    ('gh "$X" merge 630', '"$X'),
    ("rg 'gh (pr|api)' wfctl/", "(pr|api)"),
    ('git commit -m "the gh CLI"', "CLI"),
])
def test_a_word_off_the_list_of_ghs_own_commands_is_refused(
    repos: Repos, guard: Guard, command: str, word: str,
) -> None:
    """An extension such as `gh stack merge` merges a whole stack, and every
    extension or alias adds a word the check has never seen, so it lists the
    words it knows instead."""
    repos.complete(repos.feature, "604-x")

    code, err = guard(command, repos.feature)

    assert code == 2
    assert (
        f"✗ run gh {word} in your own terminal; the check knows only gh's own commands"
        in lines(err)
    )


@pytest.mark.parametrize("command", [
    "gh pr --squash=true merge 630",
    f"gh -R {THIS_REPO} -R owner/other pr merge 630",
    "gh -R $(git push -q; echo a/b) pr merge 630",
    "gh -R 'owner/repo' pr merge 630",
    "gh --version",
    "gh --help",
])
def test_a_flag_before_the_verb_other_than_one_plain_r_is_refused(
    repos: Repos, guard: Guard, command: str,
) -> None:
    """`gh` reads a verb's flags before the verb, so `gh pr --squash=true merge`
    merges. Three plan reviews each found one more spelling, so the check
    allows the one it can read and refuses the rest."""
    repos.complete(repos.feature, "604-x")

    code, err = guard(command, repos.feature)

    assert code == 2
    assert (
        "✗ move flags after the verb, and write -R as OWNER/REPO; "
        "the check reads only one plain -R before pr or the verb"
    ) in lines(err)


def test_r_with_an_equals_sign_is_read_without_it(repos: Repos, guard: Guard) -> None:
    """`gh` reads `-R=owner/repo` as `owner/repo`, so the check compares that."""
    repos.complete(repos.other, "630-x")

    assert guard(f"gh -R={THIS_REPO} pr merge 630", repos.main) == (0, "")


def test_one_r_before_pr_and_one_after_the_verb_count_as_two(
    repos: Repos, guard: Guard,
) -> None:
    """The check would have to guess which one `gh` uses."""
    code, err = guard(f"gh -R {THIS_REPO} pr merge -R owner/other 630", repos.main)

    assert code == 2
    assert lines(err) == ["✗ name the repository once; the check can't tell which -R gh uses"]


# --- shape (T024) ------------------------------------------------------------------


@pytest.mark.parametrize(("command", "name"), [
    ("git commit -am fix && git push && gh pr create --fill", "gh pr create"),
    ("cd ../x && gh pr create", "gh pr create"),
    ("git switch other; gh pr create", "gh pr create"),
    ('bash -c "git push && gh pr create"', "gh pr create"),
    ("gh pr create --fill && gh pr merge 630", "gh pr merge"),
])
def test_a_pull_request_command_after_another_command_is_refused(
    repos: Repos, guard: Guard, command: str, name: str,
) -> None:
    """The check reads the branch before any of the text runs, so an earlier
    commit, push, or `cd` changes what the pull request command acts on after
    it was judged. Quoted separators count, since `bash -c` runs them."""
    repos.complete(repos.feature, "604-x")

    code, err = guard(command, repos.feature)

    assert code == 2
    assert lines(err) == [
        f"✗ run {name} on its own; the check judges the branch before anything "
        "earlier in the command runs",
    ]


@pytest.mark.parametrize("command", [
    'gh pr create --fill --title "$(git push -q && echo t)"',
    "gh pr create --title `git push -q`",
    "gh pr create --body-file <(git push -q)",
    "gh pr create --fill >(cat)",
])
def test_a_substitution_in_the_pull_request_command_is_refused(
    repos: Repos, guard: Guard, command: str,
) -> None:
    """The shell runs a substitution before `gh` starts, so it can push a commit
    the check never saw, with no separator before the match."""
    repos.complete(repos.feature, "604-x")

    code, err = guard(command, repos.feature)

    assert code == 2
    assert lines(err) == [
        "✗ run gh pr create without a substitution; the shell runs it after the check "
        "has judged the branch",
    ]


@pytest.mark.parametrize("command", [
    "GIT_DIR=../630-x/.git gh pr create",
    "GIT_WORK_TREE=../630-x gh pr create",
    "GH_REPO=owner/other gh pr create",
    "NO_COLOR=1 gh pr create",
    "env -C ../630-x gh pr create",
])
def test_an_environment_prefix_or_env_before_the_command_is_refused(
    repos: Repos, guard: Guard, command: str,
) -> None:
    """The check's own `git` and `gh` calls don't see the prefix, so it would
    judge this branch while `gh` acts on another."""
    repos.complete(repos.feature, "604-x")

    code, err = guard(command, repos.feature)

    assert code == 2
    assert lines(err) == [
        "✗ run gh pr create without an environment prefix or env; the check can't see "
        "where it points gh",
    ]


@pytest.mark.parametrize("command", [
    "/usr/bin/env -C ../630-x gh pr create --fill",
    "\\env -C ../630-x gh pr create --fill",
])
def test_env_by_its_path_is_an_environment_prefix(
    repos: Repos, guard: Guard, command: str,
) -> None:
    """`/usr/bin/env -C` moves `gh` to another worktree as `env -C` does.
    Found by code reviewer c2 on #638's own panel."""
    repos.complete(repos.feature, "604-x")

    code, err = guard(command, repos.feature)

    assert code == 2
    assert "without an environment prefix or env" in err


# --- arguments (T025) --------------------------------------------------------------


@pytest.mark.parametrize("command", [
    "gh pr merge -s 630",
    "gh pr merge --subject=fix 630",
    "gh pr merge -tfix 630",
    "gh pr merge -sd 630",
    "gh pr merge -st fix 630",
])
def test_merge_flags_in_every_spelling_still_find_the_pull_request(
    repos: Repos, guard: Guard, command: str,
) -> None:
    """Short flags group the way `gh` reads them, and a misread value would
    look up the wrong pull request."""
    code, err = guard(command, repos.main)

    assert code == 2
    assert "630-x has commits no review covered" in err
    assert ["pr", "view", "630", "--json", "headRefName,headRefOid"] in repos.gh_calls()


@pytest.mark.parametrize("command", [
    "gh pr merge -sx 630",
    "gh pr merge 630 631",
    "gh pr merge --frobnicate 630",
    "gh pr merge 'unclosed 630",
])
def test_a_merge_the_check_cant_read_is_refused(
    repos: Repos, guard: Guard, command: str,
) -> None:
    """A command the rule can't read never falls back to the current branch,
    which could be reviewed while the pull request named isn't."""
    code, err = guard(command, repos.main)

    assert code == 2
    assert "✗ can't read the pull request this command names" in lines(err)


@pytest.mark.parametrize("command", [
    "gh pr merge 630 --help",
    "gh pr merge 630 -h",
    "gh pr merge 630 --squash --help=false",
    "gh pr create --fill --help=0",
    "gh pr merge 630 -tx> --help",
    "gh pr merge 630 --subject=x> --help",
    "gh pr merge 630 <<< --help",
    "gh pr merge 630 >! --help",
])
def test_help_is_judged_like_any_other_flag(
    repos: Repos, guard: Guard, command: str,
) -> None:
    """Allowing a command as help, since `gh` prints help and does nothing
    else, let a `--help` the shell drops or redirects carry a merge past the
    check unjudged. Reviewers on #638's own panel found `--help=false`, a
    `# --help` comment, and six redirection spellings, one round after
    another, so help gets no exception at all."""
    code, err = guard(command, repos.main)

    assert code == 2
    assert err.startswith("✗")


def test_help_on_a_reviewed_pull_request_is_allowed(repos: Repos, guard: Guard) -> None:
    """Judged like any other command, help passes once the branch is reviewed."""
    repos.complete(repos.other, "630-x")

    assert guard("gh pr merge 630 --help", repos.main) == (0, "")


@pytest.mark.parametrize("command", [
    "gh pr merge 631&>/dev/null",
    "gh pr merge 631>&2",
    "gh pr merge 631> /dev/null",
    "gh pr merge 630 <> x",
])
def test_a_redirection_the_check_cant_read_is_refused(
    repos: Repos, guard: Guard, command: str,
) -> None:
    """A pattern loose enough to take `631&>/dev/null` as a redirection dropped
    the PR number the shell still passes to `gh`, and the merge was judged as
    this branch's own. Found by security reviewer s3 on #638's own panel."""
    repos.complete(repos.feature, "604-x")

    code, err = guard(command, repos.feature)

    assert code == 2
    assert "redirections as words of their own" in err


@pytest.mark.parametrize("command", [
    "gh pr merge 630 -t $X",
    "gh pr merge 630 ${x:+ --help }",
])
def test_an_unquoted_variable_in_the_arguments_is_refused(
    repos: Repos, guard: Guard, command: str,
) -> None:
    """The shell splits an unquoted variable into words, so `-t $X` can carry a
    second pull request the check never read."""
    code, err = guard(command, repos.main)

    assert code == 2
    assert "without an unquoted variable" in err


@pytest.mark.parametrize(("command", "refusal"), [
    ("gh api 2>/dev/null graphql -F query=@m.graphql", "put the GraphQL query in the command"),
    ("gh api >/dev/null repos/o/r/pulls --input body.json", "open the pull request with gh pr create"),
    ('gh api -X PUT >/dev/null "$U"', "write the gh api path out plainly"),
])
def test_a_redirection_before_the_api_path_is_not_read_as_the_path(
    guard: Guard, tmp_path: Path, command: str, refusal: str,
) -> None:
    """Taken as the path, a redirection turned every `gh api` refusal off.
    Found by security reviewer s3 on #638's own panel."""
    code, err = guard(command, tmp_path)

    assert code == 2
    assert refusal in err


@pytest.mark.parametrize("command", [
    'git commit -m "gh api calls are read only when they write"',
    "gh api repos/o/r/pulls?state=open",
    'rg -n "gh api [a-z]+/"',
    'echo "gh api <x>"',
    "gh api repos/o/r/issues/1/comments # first page",
    "gh api repos/o/r/issues/1/comments --input - <<'EOF'",
    'gh api repos/o/r/issues/1/comments -f body=x <<< "ignored"',
])
def test_a_gh_api_read_or_a_plain_write_is_not_refused_for_its_shape(
    guard: Guard, tmp_path: Path, command: str,
) -> None:
    """Every `gh api` call once went through the reader that refuses a glob, a
    comment, or an odd redirection, so a query string, a search for the words
    `gh api`, and a commit message mentioning it were all refused. A read
    can't open or merge a pull request. Found by code reviewers on #638's own
    panel, round 2."""
    assert guard(command, tmp_path) == (0, "")


@pytest.mark.parametrize(("command", "refusal"), [
    ("gh api -X PUT repos/o/r/pulls/63?/merge", "without a brace or a glob"),
    ("gh api repos/o/r/issues -f title=x # -X GET", "without a # comment"),
    ("gh api -X POST repos/o/r/issues 631&>/dev/null", "redirections as words of their own"),
])
def test_a_gh_api_write_still_refuses_a_shape_the_check_cant_read(
    guard: Guard, tmp_path: Path, command: str, refusal: str,
) -> None:
    """A write is what can open or merge a pull request, so a write keeps the
    strict reader that reads won't."""
    code, err = guard(command, tmp_path)

    assert code == 2
    assert refusal in err


@pytest.mark.parametrize("command", [
    "gh pr merge 630 # --help",
    "gh pr merge #630 --help",
    "gh pr new --fill # -h",
])
def test_a_shell_comment_in_the_command_is_refused(
    repos: Repos, guard: Guard, command: str,
) -> None:
    """The shell drops a comment and `shlex` keeps it, so a `# --help` the check
    read as help never reached `gh`, and the merge ran unjudged. Found by code
    reviewer c3 on #638's own panel."""
    code, err = guard(command, repos.main)

    assert code == 2
    assert "without a # comment" in err


@pytest.mark.parametrize("command", [
    "gh pr merge --squash -t {fix,631}",
    "gh pr merge 630 -t {x,--auto}",
    "gh pr create --fill --title {a,--head=640-y}",
    "gh pr merge 63*",
])
def test_a_brace_or_glob_in_the_arguments_is_refused(
    repos: Repos, guard: Guard, command: str,
) -> None:
    """The shell turns `{fix,631}` into two words after the check read one, so
    a merge judged as this branch's own could merge PR 631. Found by code
    reviewer c1 on #638's own panel."""
    code, err = guard(command, repos.main)

    assert code == 2
    assert "without a brace or a glob" in err


def test_a_quoted_hash_or_brace_is_an_ordinary_argument(repos: Repos, guard: Guard) -> None:
    """Quoted, neither reaches the shell as anything but text, and a title that
    starts with `#12` is common."""
    repos.complete(repos.other, "630-x")

    assert guard('gh pr merge 630 -t "#12 fix {a,b}"', repos.main) == (0, "")


@pytest.mark.parametrize("command", [
    "gh pr merge 630 --squash 2>&1",
    "gh pr merge 630 --squash 2>/dev/null",
    "gh pr merge 630 --squash 2>&1 | tail -5",
    "gh pr merge 630 --squash > /tmp/out.txt",
    "gh pr merge 630 --squash </dev/null",
])
def test_a_redirection_is_not_read_as_an_argument(
    repos: Repos, guard: Guard, command: str,
) -> None:
    """Redirecting output is ordinary, and reading `2>&1` as a separator and a
    stray argument refused it on every branch with a message that named
    neither. Found by code reviewer c2 on #638's own panel."""
    repos.complete(repos.other, "630-x")

    assert guard(command, repos.main) == (0, "")


def test_a_pull_request_url_naming_another_repository_is_refused(
    repos: Repos, guard: Guard,
) -> None:
    """A URL names a repository the same as `-R` does, and from the `main`
    checkout it would otherwise be judged against this repository's records.
    Found by code reviewer c1 on #638's own panel."""
    code, err = guard("gh pr merge https://github.com/other/repo/pull/5", repos.main)

    assert code == 2
    assert lines(err) == ["✗ the URL names another repository; its reviews aren't here"]


def test_auto_merge_is_refused(repos: Repos, guard: Guard) -> None:
    """GitHub would merge later, at a head the check never judged."""
    repos.complete(repos.feature, "604-x")

    code, err = guard("gh pr merge --auto", repos.feature)

    assert code == 2
    assert lines(err) == ["✗ auto-merge would merge a head this check never judged"]


# --- other repositories, other branches, and where the check reads (T026) ---------


@pytest.mark.parametrize("command", [
    "gh pr -R owner/other merge 630",
    "gh -R owner/other pr merge 630",
    "gh pr -Rowner/other merge 630",
    "gh pr -R github.com/owner/other merge 630",
    f"gh pr -R ghe.example.com/{THIS_REPO} merge 630",
])
def test_r_naming_another_repository_is_refused(
    repos: Repos, guard: Guard, command: str,
) -> None:
    """That repository's reviews aren't kept here. A host other than
    `github.com` is another server, whatever the path says."""
    code, err = guard(command, repos.main)

    assert code == 2
    assert lines(err) == ["✗ -R names another repository; its reviews aren't here"]


def test_r_naming_this_repository_on_github_com_is_judged(repos: Repos, guard: Guard) -> None:
    """The host is dropped before comparing."""
    repos.complete(repos.other, "630-x")

    assert guard(f"gh pr -R github.com/{THIS_REPO} merge 630", repos.main) == (0, "")


def test_an_api_path_naming_another_repository_is_refused(
    repos: Repos, guard: Guard,
) -> None:
    """The `{owner}/{repo}` placeholders mean this repository and are judged;
    anything else names one whose reviews aren't here."""
    repos.complete(repos.other, "630-x")

    code, err = guard("gh api -X PUT repos/owner/other/pulls/630/merge", repos.main)
    assert code == 2
    assert lines(err) == ["✗ the path names another repository; its reviews aren't here"]

    assert guard("gh api -X PUT repos/{owner}/{repo}/pulls/630/merge", repos.main) == (0, "")


def test_a_head_owner_other_than_this_one_is_refused(repos: Repos, guard: Guard) -> None:
    """A fork's branch can share a name with a reviewed branch on `origin`."""
    repos.complete(repos.other, "630-x")

    code, err = guard("gh pr create --head forkowner:630-x", repos.main)
    assert code == 2
    assert lines(err) == ["✗ --head names another owner's branch; its reviews aren't here"]

    assert guard("gh pr create --head acme:630-x", repos.main) == (0, "")


def test_a_head_is_judged_at_the_commit_origin_holds(repos: Repos, guard: Guard) -> None:
    """FR-012a. The pull request opens at GitHub's copy of the branch, so a
    local commit that wasn't pushed doesn't count either way."""
    repos.complete(repos.other, "630-x")
    commit(repos.other, "unpushed.txt")

    assert guard("gh pr create --head 630-x", repos.main) == (0, "")


def test_a_head_is_judged_at_its_own_ref_not_one_that_ends_the_same(
    repos: Repos, guard: Guard,
) -> None:
    """`ls-remote` matches a ref by its end, so `a/refs/heads/630-x` is listed
    too and sorts first. Found by code reviewer c3 on #638's own panel."""
    repos.complete(repos.other, "630-x")
    decoy = commit(repos.feature, "decoy.txt")
    git(repos.feature, "push", "-q", "origin", f"{decoy}:refs/heads/a/refs/heads/630-x")

    assert guard("gh pr create --head 630-x", repos.main) == (0, "")


def test_a_trunk_that_is_the_judged_branch_is_refused(repos: Repos, guard: Guard) -> None:
    """With `trunk` set to the branch itself, every commit on it reads as
    already on the trunk and nothing is unreviewed. A `wfctl.json` edit made
    with a file tool is all it takes, and no Bash hook sees that. Found by
    code reviewer c1 on #638's own panel."""
    (repos.feature / "wfctl.json").write_text(json.dumps({"trunk": "604-x"}))

    code, err = guard("gh pr create --fill", repos.feature)

    assert code == 2
    assert lines(err) == [
        "✗ the trunk branch is 604-x, the branch this command acts on; check trunk in wfctl.json",
    ]


@pytest.mark.parametrize("command", ["gh pr merge 630", "gh pr create --head 630-x"])
@pytest.mark.parametrize("reviewed", [True, False])
def test_a_feature_worktree_cant_act_on_another_branchs_pull_request(
    repos: Repos, guard: Guard, command: str, reviewed: bool,
) -> None:
    """US3 scenario 10. A worktree opens and merges only its own pull request,
    and the person orchestrates from the `main` checkout."""
    if reviewed:
        repos.complete(repos.other, "630-x")

    code, err = guard(command, repos.feature)

    assert code == 2
    assert lines(err) == [
        "✗ run this from the checkout on main; a worktree opens and merges only its own "
        "branch's pull request",
    ]


def test_the_main_checkout_judges_another_branch_by_its_own_records(
    repos: Repos, guard: Guard,
) -> None:
    """US3 scenario 8. `trunk_branch` returns `origin/main`, and without the
    prefix stripped every merge from the `main` checkout would refuse."""
    code, err = guard("gh pr merge 630", repos.main)
    assert code == 2
    assert "630-x has commits no review covered" in err

    repos.complete(repos.other, "630-x")
    assert guard("gh pr merge 630", repos.main) == (0, "")


@pytest.mark.parametrize("trouble", ["fail", "missing", "unknown-commit"])
def test_a_lookup_that_fails_gives_the_error_refusal(
    repos: Repos, guard: Guard, trouble: str,
) -> None:
    """US3 scenario 9. Without the pull request's branch the check has nothing
    to judge, and guessing the current branch would judge the wrong one."""
    if trouble == "fail":
        repos.gh(fail=True)
    elif trouble == "missing":
        repos.gh(prs={})
    else:
        repos.gh(prs={"630": {"headRefName": "630-x", "headRefOid": "f" * 40}})

    code, err = guard("gh pr merge 630", repos.main)

    assert code == 2
    assert err.startswith("✗ the review check failed: ")
    assert "where this hook doesn't run" in err


def test_a_lookup_that_hangs_gives_the_error_refusal(
    repos: Repos, guard: Guard, monkeypatch: pytest.MonkeyPatch,
) -> None:
    """If the host killed the hook at its own timeout, the hook would exit
    without code 2 and the command would run."""
    monkeypatch.setattr(_review_gate, "TIMEOUT", 0.5)
    repos.gh(hang=True)

    code, err = guard("gh pr merge 630", repos.main)

    assert code == 2
    assert err.startswith("✗ the review check failed: gh pr view timed out after 0.5s")


def test_judging_another_branch_creates_no_state_directory(
    repos: Repos, guard: Guard,
) -> None:
    """A hook reader leaves no empty directory behind for a branch nobody ran
    wfctl on."""
    state = resolve_agent_dir(repos.main, "630-x", create=False)

    guard("gh pr merge 630", repos.main)

    assert not state.exists()


def test_a_state_dir_override_refuses_judging_another_branch(
    repos: Repos, guard: Guard, monkeypatch: pytest.MonkeyPatch,
) -> None:
    """R5. The override names one branch's directory, and reading it for
    another would judge that branch against the wrong records."""
    monkeypatch.setenv("WFCTL_STATE_DIR", str(repos.tmp / "pinned"))

    code, err = guard("gh pr merge 630", repos.main)

    assert code == 2
    assert "WFCTL_STATE_DIR names one branch's state directory" in err


def test_a_branch_override_naming_another_branch_than_the_cwd_is_refused(
    repos: Repos, guard: Guard, monkeypatch: pytest.MonkeyPatch,
) -> None:
    """FR-012c. The check reads the branch from the session's directory, and
    the override would otherwise name it without reading `cwd`."""
    repos.complete(repos.other, "630-x")
    monkeypatch.setenv("WFCTL_BRANCH", "630-x")

    code, err = guard("gh pr create --fill", repos.feature)

    assert code == 2
    assert "WFCTL_BRANCH names 630-x, but" in err
    assert "the override names a different branch from the session's directory" in err


def test_the_payload_cwd_decides_the_branch_not_the_hooks_own_directory(
    repos: Repos, guard: Guard, monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A session started in the `main` checkout can `cd` into a worktree. Judged
    from the hook's own directory, its pull request would be judged as
    `main`'s."""
    monkeypatch.chdir(repos.main)

    code, err = guard("gh pr create --fill", repos.other)

    assert code == 2
    assert "630-x has commits no review covered" in err


@pytest.mark.parametrize("cwd", [None, "outside"])
def test_a_match_with_no_working_directory_gives_the_error_refusal(
    repos: Repos, guard: Guard, cwd: str | None,
) -> None:
    """With no session directory the check can't know which branch the command
    acts on."""
    where = None if cwd is None else repos.tmp / "bin"

    code, err = guard("gh pr create --fill", where)

    assert code == 2
    assert err.startswith("✗ the review check failed: ")
    assert "working directory" in err


# --- wrong refusals the spec accepts (T027) ---------------------------------------


def test_a_field_before_an_api_merge_path_reads_as_an_environment_prefix(
    repos: Repos, guard: Guard,
) -> None:
    """Spec Edge Cases. `merge_method=merge` before the path looks like a
    `NAME=value` prefix. Writing the path first is judged."""
    repos.complete(repos.other, "630-x")

    code, err = guard(
        "gh api -f merge_method=merge repos/{owner}/{repo}/pulls/630/merge -X PUT", repos.main,
    )
    assert code == 2
    assert "✗ run gh api without an environment prefix or env" in err

    assert guard(
        "gh api repos/{owner}/{repo}/pulls/630/merge -X PUT -f merge_method=merge", repos.main,
    ) == (0, "")


def test_colon_placeholders_read_as_another_repository(repos: Repos, guard: Guard) -> None:
    """Spec Edge Cases. Only the `{owner}/{repo}` placeholders mean this
    repository."""
    repos.complete(repos.other, "630-x")

    code, err = guard("gh api -X PUT repos/:owner/:repo/pulls/630/merge", repos.main)
    assert code == 2
    assert "the path names another repository" in err

    assert guard("gh api -X PUT repos/{owner}/{repo}/pulls/630/merge", repos.main) == (0, "")


def test_a_comment_reply_through_a_variable_path_is_refused(
    guard: Guard, tmp_path: Path,
) -> None:
    """Spec Edge Cases. A write to a variable path could be a merge. Writing the
    id out isn't matched."""
    code, err = guard(
        'gh api "repos/{owner}/{repo}/pulls/comments/$ID/replies" -f body=x', tmp_path,
    )
    assert code == 2
    assert "write the gh api path out plainly" in err

    assert guard(
        'gh api "repos/{owner}/{repo}/pulls/comments/123/replies" -f body=x', tmp_path,
    ) == (0, "")


def test_a_search_quoting_both_commands_is_refused(
    repos: Repos, guard: Guard, tmp_path: Path,
) -> None:
    """Spec Edge Cases. Two rules fire on `grep "gh pr create\\|gh pr merge"`:
    the plain-verb rule reads `create\\|gh` as the verb, and the separator rule
    sees the quoted `|` before the second match. Only the first is asserted as
    present, since both lines print."""
    repos.complete(repos.feature, "604-x")

    code, err = guard('grep "gh pr create\\|gh pr merge" wfctl/', repos.feature)
    assert code == 2
    assert "✗ write gh's command words out plainly; the check can't read them" in lines(err)

    code, err = guard("rg 'gh pr.*merge'", repos.feature)
    assert code == 2
    assert "run gh pr.*merge in your own terminal" in err

    assert guard('grep "pr create" wfctl/', tmp_path) == (0, "")


def test_naming_gh_before_using_it_is_refused(guard: Guard, tmp_path: Path) -> None:
    """Spec Edge Cases. In `which gh && gh pr view`, the word after the first
    `gh` is `&&`."""
    code, err = guard("which gh && gh pr view", tmp_path)
    assert code == 2
    assert "run gh && in your own terminal" in err

    assert guard("which gh", tmp_path) == (0, "")


def test_a_commit_message_quoting_a_variable_command_word_is_refused(
    guard: Guard, tmp_path: Path,
) -> None:
    """Spec Edge Cases. A message read from a file isn't in the command."""
    code, err = guard("git commit -m 'run gh \"$X\" merge 630'", tmp_path)
    assert code == 2
    assert "the check knows only gh's own commands" in err

    assert guard("git commit -F /tmp/message.txt", tmp_path) == (0, "")


# --- relay (T045) ------------------------------------------------------------------


def test_a_relay_whose_report_quotes_refused_commands_is_allowed(
    repos: Repos, guard: Guard,
) -> None:
    """R8. A security report quotes the commands the check refuses, and it has
    to arrive word for word, so it travels in a file the check doesn't read."""
    report = repos.tmp / "s2.md"
    report.write_text("gh pr create\npulls/630/merge\nreview sign-off\n")

    assert guard(
        f'wfctl relay s2 --reason "write denied" --from {report}', repos.feature,
    ) == (0, "")


# --- the real process (T020 item 7) ------------------------------------------------


def test_the_hook_process_refuses_an_unreviewed_branch_and_allows_a_reviewed_one(
    repos: Repos,
) -> None:
    """The independent test, through `_entry.py`, so the fast path that skips
    `typer` reaches the review check too."""

    def hook(command: str) -> subprocess.CompletedProcess[str]:
        payload = json.dumps({"tool_input": {"command": command}, "cwd": str(repos.feature)})
        return subprocess.run(
            [sys.executable, "-c", "from wfctl._entry import main; main()",
             "hook", "worktree-guard"],
            input=payload, capture_output=True, text=True, cwd=REPO,
        )

    refused = hook("gh pr create --fill")
    assert refused.returncode == 2
    assert "604-x has commits no review covered" in refused.stderr

    repos.complete(repos.feature, "604-x")
    allowed = hook("gh pr create --fill")
    assert (allowed.returncode, allowed.stderr) == (0, "")


# --- review notes written by hand (US5) ------------------------------------------


NOTES_REFUSAL = (
    "✗ wfctl writes review notes itself when a run completes or a person signs off.\n"
    "  To send a note that didn't reach origin, run `wfctl store reviews`.\n"
)


@pytest.mark.parametrize("verb", ["add", "append", "edit", "copy", "merge", "remove", "prune"])
@pytest.mark.parametrize("form", [
    "git notes {verb} -m 'reviewed by code' HEAD",
    "git notes --ref x {verb} HEAD",
    "git notes --ref=wfctl-review {verb} HEAD",
    "git -c core.notesRef=x notes {verb} HEAD",
    "GIT_NOTES_REF=x git notes {verb} HEAD",
    "cd sub && git -C . notes {verb} HEAD",
])
def test_every_notes_write_is_refused_whichever_ref_it_names(
    guard: Guard, tmp_path: Path, verb: str, form: str,
) -> None:
    """CI trusts any note it finds, so a note an agent writes by hand passes a
    PR nobody reviewed. The rule never asks which ref a write targets, since
    git has three ways to name one (`627-guard-blocks-note-writes.md`)."""
    assert guard(form.format(verb=verb), tmp_path) == (2, NOTES_REFUSAL)


@pytest.mark.parametrize("command", [
    "git push origin refs/notes/wfctl-review",
    "git push origin 'refs/notes/*:refs/notes/*'",
    "git push --mirror origin",
    "git fetch origin && git push origin +refs/notes/x:refs/notes/x",
    "git push origin notes/wfctl-review",
    "git push origin 'refs/*:refs/*'",
    "git push origin '+*:*'",
])
def test_a_push_of_any_notes_ref_is_refused(guard: Guard, tmp_path: Path, command: str) -> None:
    """A note written by hand only matters once it reaches `origin`, and
    `--mirror` pushes every ref, notes included. git resolves the short
    `notes/wfctl-review`, and a wildcard over `refs/` pushes the notes ref
    without naming it."""
    assert guard(command, tmp_path) == (2, NOTES_REFUSAL)


@pytest.mark.parametrize("command", [
    "git update-ref refs/notes/wfctl-review 1234567",
    "git fetch . HEAD:refs/notes/wfctl-review",
])
def test_writing_the_notes_ref_without_git_notes_is_refused(
    guard: Guard, tmp_path: Path, command: str,
) -> None:
    """`update-ref` and a fetch from the repository itself each write the
    notes ref without `git notes`, and `wfctl store reviews` then pushes what
    they wrote."""
    assert guard(command, tmp_path) == (2, NOTES_REFUSAL)


@pytest.mark.parametrize("command", [
    "git -c remote.origin.push='+refs/notes/*:refs/notes/*' push origin",
    "git config remote.origin.push '+refs/*:refs/*'",
    "git config --add remote.origin.mirror true",
    "git config remote.origin.MIRROR true",
    "git config remote.origin.Push '+refs/*:refs/*'",
])
def test_configuring_what_a_plain_push_carries_is_refused(
    guard: Guard, tmp_path: Path, command: str,
) -> None:
    """A remote's `push` or `mirror` setting makes a plain `git push` carry
    the notes ref, and the push names no notes ref for the rule above to
    see."""
    assert guard(command, tmp_path) == (2, NOTES_REFUSAL)


@pytest.mark.parametrize("command", [
    "git notes --ref=wfctl-review show HEAD",
    "git notes list",
    "git log --notes=wfctl-review -3",
    "git push origin HEAD",
    "git log --oneline --notes",
    "git push origin 'refs/heads/*:refs/heads/*'",
    "git update-ref refs/heads/x HEAD",
    "git commit -m 'document remote.origin.push'",
    "git fetch origin",
])
def test_reading_notes_and_a_plain_push_are_allowed(
    guard: Guard, tmp_path: Path, command: str,
) -> None:
    """A person checks what was reviewed with these, and a plain push names
    no notes ref."""
    assert guard(command, tmp_path) == (0, "")


@pytest.mark.parametrize("command", ["git notes list", "git push --mirror origin"])
def test_a_command_holding_notes_or_mirror_reaches_the_review_check(
    guard: Guard, monkeypatch: pytest.MonkeyPatch, command: str,
) -> None:
    """The hook's substring test is what lets a command reach the check, and
    neither command holds `gh`, `merge`, or `sign` (FR-022)."""
    seen: list[str] = []
    monkeypatch.setattr(_review_gate, "refusal", lambda text, cwd: seen.append(text))

    guard(command, None)

    assert seen == [command]


@pytest.mark.parametrize("command", [
    "wfctl arch approve-imports",
    "uv run wfctl arch approve-imports",
    "wfctl arch approve_imports",
    "wfctl arch --verbose approve-imports",
])
def test_every_approve_imports_spelling_is_refused(
    guard: Guard, tmp_path: Path, command: str,
) -> None:
    """FR-015. Only the user approves an addition the import check reads, so
    an agent running the command is refused the same way the person-only
    review command is."""
    code, err = guard(command, tmp_path)

    assert code == 2
    assert err == (
        "✗ wfctl arch approve-imports is for a person to run in their own terminal, "
        "not an agent.\n"
    )


def test_an_unrelated_arch_command_is_allowed(guard: Guard, tmp_path: Path) -> None:
    assert guard("wfctl arch context", tmp_path) == (0, "")


# --- wfctl arch accept (#769) ------------------------------------------------------

_ACCEPT_TEXT = (
    "✗ wfctl arch accept is for a person to run in their own terminal, not an agent. "
    "An agent can run it with --dry-run."
)


def test_the_accept_refusal_names_the_dry_run_an_agent_may_use() -> None:
    """The refusal is the only place an agent learns that `--dry-run` is
    allowed, so the text has to carry it."""
    assert _review_gate.ACCEPT_REFUSAL == _ACCEPT_TEXT


@pytest.mark.parametrize("command", [
    "wfctl arch accept x --agreed y",
    "uv run wfctl arch accept x --agreed y",
])
def test_an_accept_without_dry_run_is_refused(command: str) -> None:
    """Accepting a record is the person's decision. Without the refusal an
    agent could flip a `proposed` record to `accepted` by itself."""
    refused, _ = _review_gate.read(command)

    assert _review_gate.ACCEPT_REFUSAL in refused


def test_an_accept_with_dry_run_is_allowed() -> None:
    """`--dry-run` writes nothing, and the agent needs it to preview what
    accepting would change, so it can't be refused with the real command."""
    refused, _ = _review_gate.read("wfctl arch accept --dry-run -- x")

    assert _review_gate.ACCEPT_REFUSAL not in refused


def test_a_dry_run_on_one_accept_doesnt_cover_a_second_accept_after_a_separator() -> None:
    """A whole-command search for `--dry-run` would let a real accept ride
    behind a harmless one, so each separated part is judged on its own."""
    refused, _ = _review_gate.read(
        "wfctl arch accept --dry-run -- a; wfctl arch accept b --agreed x"
    )

    assert _review_gate.ACCEPT_REFUSAL in refused


def test_dry_run_inside_a_quoted_argument_is_not_the_flag() -> None:
    """`--dry-run` has to be a whole shell word. Inside a quoted `--agreed`
    reason it is only text, and the accept still writes."""
    refused, _ = _review_gate.read('wfctl arch accept b --agreed "after a --dry-run"')

    assert _review_gate.ACCEPT_REFUSAL in refused


@pytest.mark.parametrize("command", [
    "wfctl arch accept s --agreed x # --dry-run",
    "wfctl arch accept s --agreed --dry-run",
    "wfctl arch accept s --agreed x > --dry-run",
    "wfctl arch accept s --agreed x 2>> --dry-run",
    "wfctl arch accept -- --dry-run",
    "echo $(wfctl arch accept s --agreed x) --dry-run",
    'wfctl "arch" accept s --agreed x',
    "wfctl arch 'accept' s --agreed x",
    '"$(command -v wfctl)" arch accept s --agreed x',
    "$WFCTL arch accept s --agreed x",
    'bash -c "wfctl arch accept s --agreed x" --dry-run',
    "script -q /dev/null wfctl arch accept s --agreed x # --dry-run",
    "wfctl arch \\\naccept s --agreed x",
    "wfctl \\\narch accept s --agreed x",
    "wfctl arch acc\\ept s --agreed x",
    'wfctl ar""ch accept s --agreed x',
    'script -q /dev/null wfctl arch accep"t" s --agreed x',
    "A=accept; wfctl arch $A s --agreed x",
    'C="arch accept"; script -q /dev/null wfctl $C s --agreed x',
    "A=$(printf ar%sh c); B=$(printf acc%spt e); wfctl $A $B s --agreed x",
    'script -q /dev/null wfctl "$(printf ar)ch" "$(printf acc)ept" s --agreed x',
    "script -q /dev/null bash -c 'wfctl${IFS}arch${IFS}accept s --agreed x'",
    "WFCTL arch accept s --agreed x",
    "~/.local/bin/wf?tl arch accept s --agreed x",
    "wfctl arch accept s --agreed x >! --dry-run",
    "wfctl arch accept s --agreed x >>| --dry-run",
    "wfctl arch accept s --agreed x {fd}> --dry-run",
])
def test_a_dry_run_the_shell_never_hands_to_wfctl_doesnt_open_the_accept(
    command: str,
) -> None:
    """The security and code panels on #769 got a real accept past a check
    that looked for `--dry-run` anywhere in the words and for `wfctl arch
    accept` in the raw text. Each form here writes the record while the text
    holds the flag or hides the command: behind quotes, a backslash, a line
    continuation, a variable that builds one or both words, another case, a
    glob, or a zsh redirect. A pseudo-terminal then satisfies the terminal
    check behind the guard."""
    refused, _ = _review_gate.read(command)

    assert _review_gate.ACCEPT_REFUSAL in refused


@pytest.mark.parametrize("command", [
    "wfctl arch accept s --agreed x --dry-run",
    "wfctl arch accept --dry-run s",
    "git commit -m 'arch: accept the record'",
    "wfctl arch context # then accept",
    'C="arch accept"; wfctl $C s --agreed x --dry-run',
    "wfctl relay s3 --reason r --from $FILE",
    "echo $HOME $PATH $USER",
])
def test_a_dry_run_wfctl_reads_as_the_flag_still_opens_the_accept(command: str) -> None:
    """Tightening the match mustn't refuse the dry run agents are told to use,
    or text that only mentions the command."""
    refused, _ = _review_gate.read(command)

    assert _review_gate.ACCEPT_REFUSAL not in refused


@pytest.mark.parametrize("command", [
    'bash -c "true; WFCTL arch accept s --agreed x"',
    'bash -c "true; $(command -v wfctl) arch accept s --agreed x"',
    'bash -c "true; wf?tl arch accept s --agreed x"',
    'bash -c "true # note\nwfctl arch accept s --agreed x"',
    'bash -c "env wfctl arch accept s --agreed x"',
    'python -c "import wfctl.cli as c; c.app()" arch accept s --agreed x',
    "wfctl {arch,} accept s --agreed x",
    "bash -c 'wfctl {arch,} accept s --agreed x'",
    "wfctl {ar,}ch {acc,}ept s --agreed x",
    'git commit -m "`wfctl arch accept s --agreed x` ran"',
    'git commit -m "see $(wfctl arch accept s --agreed x)"',
    "for r in a b; do wfctl $C $r --agreed x; done",
    "cat <<EOF\nit's\nEOF\nWFCTL arch accept s --agreed x",
    "echo 'wfctl arch accept s --agreed x' | sh",
    "printf '%s\\n' 'wfctl arch accept s' | /bin/bash",
    "awk 'BEGIN{system(\"wfctl arch accept s --agreed x\")}'",
    "perl -e 'system(\"wfctl arch accept s --agreed x\")'",
    "wfctl arch accept s --agreed x 2>e\r--dry-run",
])
def test_an_accept_behind_a_quoted_separator_or_a_brace_is_refused(command: str) -> None:
    """The code panel on #769 got these past a check that split the text at
    `;`, `&`, `|`, and newlines before reading words. That split broke a
    quoted `bash -c` script in two, and neither half parsed, so a fallback
    pattern that wanted the lowercase name read the command instead. `{arch,}`
    is `arch` to bash, and a backtick or `$(…)` runs inside a double-quoted
    commit message. The security panel's next round found that reading other
    quoted words as prose let a script piped into `sh`, and an interpreter's
    `system("wfctl …")`, through, and that splitting words at a carriage
    return, which the shell keeps inside a word, read a redirect's file name
    as `--dry-run`."""
    refused, _ = _review_gate.read(command)

    assert _review_gate.ACCEPT_REFUSAL in refused


@pytest.mark.parametrize("command", [
    'grep -n wfctl "$f"',
    "rg wfctl $HOME",
    "for f in *.py; do grep wfctl $f; done",
    "echo $HOME wfctl $PATH",
    'wfctl arch accept s --agreed "a; b" --dry-run',
])
def test_text_that_only_names_the_accept_command_is_not_refused(command: str) -> None:
    """The code panel on #769 found the guard refusing commit messages,
    release notes, and greps that only mention `wfctl arch accept` or search
    for `wfctl`, with advice to add `--dry-run` that fits none of them. A
    quoted word is prose unless it follows `-c` or a shell, and a text tool
    such as grep never runs the name it is handed. Text that spells out all
    three words is refused unless one program that only reads text holds
    them, as `test_text_that_spells_out_the_accept_is_refused` says."""
    refused, _ = _review_gate.read(command)

    assert _review_gate.ACCEPT_REFUSAL not in refused


@pytest.mark.parametrize("command", [
    "echo `wfctl x`",
    'echo "run `wfctl status` now"',
    'git commit -m "use `wfctl doctor` first"',
    'git commit -m "use `wfctl` first"',
    'git commit -m "`wfctl x y` first"',
    'git commit -m "run `wfctl arch context` first"',
    "gh api -X POST repos/o/r/pulls/1/comments/2/replies"
    ' -f body="Agreed. Run `wfctl install-config`"',
    "gh project list --owner o --format json"
    """ --jq '.projects[] | select(.title=="wfctl") | {number,id}'""",
])
def test_a_backticked_wfctl_command_that_isnt_the_accept_is_not_refused(
    command: str,
) -> None:
    """The 771 worktree's session was refused on 2026-11-17 for a `gh api`
    review reply that formatted `wfctl install-config` as code. The backtick
    that closes the substitution sits in the last word, as in `` status` ``,
    and the guard read that word as an expansion that could hold `arch
    accept`. The same reply without the backticks went through. The jq
    filter was refused in #792's own session, since a brace later in the
    quoted filter counted as an expansion in the same word as the name."""
    refused, _ = _review_gate.read(command)

    assert _review_gate.ACCEPT_REFUSAL not in refused


@pytest.mark.parametrize("command", [
    "cp /private/tmp/claude-501/-Users-andremarin-Development-wfctl/d4c079aa/scratchpad/"
    '790-handoff.md "$(wfctl state-dir --branch 790-fork-review-checkout)/session-summary.md"',
    'cp a/wfctl/x "$(wfctl state-dir)/y"',
])
def test_a_path_through_a_wfctl_folder_before_a_substitution_is_not_refused(
    command: str,
) -> None:
    """A session on `main` was refused on 2026-11-17 for copying a handoff from
    its scratchpad into the state dir, which `worktree-handoff` tells it to
    do. The scratchpad path contains `wfctl` because the repo folder is named
    that, and the guard read the folder as the program and the quoted
    substitution after it as `arch accept`. A program path ends in its name,
    so a folder named `wfctl` partway through a path doesn't run it."""
    refused, _ = _review_gate.read(command)

    assert _review_gate.ACCEPT_REFUSAL not in refused


@pytest.mark.parametrize("command", [
    "echo `wfctl $C`",
    "echo `wfctl$C`",
    'git commit -m "`wfctl $C` ran"',
    'git commit -m "`wfctl $X accept` ran"',
    'git commit -m "`wfctl arch $Y` ran"',
    "echo `wfctl arch accept s --agreed x`",
    "/usr/local/bin/wfctl $C s --agreed x",
    "/x/wfctl/../bin/wfctl $C s --agreed x",
    "a/wfctl/$C s --agreed x",
    "'x`' wfctl `printf \"arch accept\"` s --agreed x",
    "script -q /dev/null 'x`' wfctl `printf arch` accept s --agreed x",
    '"$(command -v wfctl)" $C s --agreed x',
    '"$(command -v wfctl)"$C s --agreed x',
    '"wfctl"$C s --agreed x',
    '"$(command -v wfctl 2>/dev/null)"$C s --agreed x',
    '"$(command -v wfctl )"$C s --agreed x',
    '"`command -v wfctl `"$C s --agreed x',
    '"$(echo wfctl )"$C s --agreed x',
    '"${W:-$(command -v wfctl )}"$C s --agreed x',
    '"/tmp/wfctl x/bin/wfctl"$C s --agreed x',
    '"/tmp/wfctl x/bin/"wf?tl$C s --agreed x',
    '"$(command -v wfctl 2>/dev/null)" $C s --agreed x',
    '"$(command -v wfctl || echo /x/y)" $C s --agreed x',
    "bash -c '\"$(command -v wfctl 2>/dev/null)\" $C s --agreed x'",
    "script -q /dev/null bash -c '\"$(command -v wfctl )\"$C s --agreed x'",
    "$(dirname /usr/local/bin/wfctl/x) $C s --agreed x",
    '$(echo "wfctl "$C) s --agreed x',
    "$(command -v wfctl) $C s --agreed x",
    '"$(which wfctl)" $C s --agreed x',
    "$(command -v wfctl) $C",
    '"${W:-wfctl}" $C s --agreed x',
    "{wfctl,} $C s --agreed x",
    "wfctl* $C s --agreed x",
    "~/.local/bin/wfctl* $C s --agreed x",
    "uv run wfctl* $C s --agreed x",
    "bash -c '\"$(command -v wfctl)\" $C s --agreed x'",
    'bash -c "wfctl* \\$C s --agreed x"',
    'script -q /dev/null "$(command -v wfctl)" $C s --agreed x',
    'eval "\\"\\$(command -v wfctl)\\" $C s --agreed x"',
    'env -S "wfctl $C" s --agreed x',
])
def test_an_expansion_beside_a_backticked_or_pathed_wfctl_is_still_refused(
    command: str,
) -> None:
    """The #792 fix stopped reading a closing backtick as an expansion and a
    folder named `wfctl` as the program. These forms keep a variable that
    can hold `arch accept` where the shell would hand it to wfctl, so the
    fix has to leave each one refused. Two put a literal backtick in an
    earlier word, which pairing backticks across words would read as the
    opener, so the real substitution after the name would read as its
    closer. The security panel on #792 got the rest past a first version
    that counted the next word only when the name ended its own word, and
    that skipped a quoted word holding whitespace. The name doesn't end
    `$(command -v wfctl)`, `{wfctl,}`, or `wfctl*`, and a quoted
    substitution is the program, not one prose argument. Its second round
    got the `2>/dev/null` and trailing-space forms past both narrowings,
    which read a slash or a space inside a substitution as literal text,
    and a space before a later path segment past the jq filter's fix.

    Every form here builds `arch accept` at run time, so the guard refuses
    it on a best-effort basis (`guard-catches-literal-accept.md`). If a
    change has to stop refusing one to clear a false refusal, delete its
    line here, as long as the literal forms below stay refused."""
    refused, _ = _review_gate.read(command)

    assert _review_gate.ACCEPT_REFUSAL in refused


@pytest.mark.parametrize("command", [
    "env wfctl arch accept s --agreed x",
    "env A=1 wfctl arch accept s --agreed x",
    "sudo wfctl arch accept s --agreed x",
    "/usr/local/bin/wfctl arch accept s --agreed x",
    "./.venv/bin/wfctl arch accept s --agreed x",
    "sh -c 'wfctl arch accept s --agreed x'",
    "zsh -c 'wfctl arch accept s --agreed x'",
    "ssh host 'wfctl arch accept s --agreed x'",
    "ssh host wfctl arch accept s --agreed x",
    "eval 'wfctl arch accept s --agreed x'",
    "echo 'wfctl arch accept s --agreed x' | bash",
    "$(wfctl arch accept s --agreed x)",
    "script -q /dev/null wfctl arch accept s --agreed x",
    "script -q /dev/null uv run wfctl arch accept s --agreed x",
    "script -q /dev/null bash -c 'wfctl arch accept s --agreed x'",
    'x="$(uv run wfctl arch accept s --agreed x)"',
    'x="$(env wfctl arch accept s --agreed x)"',
    'x="$(cd /tmp && wfctl arch accept s --agreed x)"',
    'x="$(true; wfctl arch accept s --agreed x)"',
    "script -q /dev/null bash -c"
    " 'x=\"$(env wfctl arch accept s --agreed x >/dev/tty)\"'",
    "script -q /dev/null bash -c"
    " 'echo $(uv run wfctl arch accept s --agreed x >/dev/tty)'",
    "bash -c 'script -q /dev/null wfctl arch accept s --agreed x'",
    'echo "$(script -q /dev/null wfctl arch accept s --agreed x)"',
    "bash -c 'sudo -u root wfctl arch accept s --agreed x'",
    "bash -c 'timeout -s KILL 5 wfctl arch accept s --agreed x'",
    "ssh host 'sudo -u root wfctl arch accept s --agreed x'",
    "tmux new 'script -q /dev/null wfctl arch accept s --agreed x'",
    "echo \"$(echo ')' && wfctl arch accept s --agreed x)\"",
    "x=\"$(echo ')' ; script -q /dev/null wfctl arch accept s --agreed x)\"",
    'echo "$(echo \\) ; wfctl arch accept s --agreed x)"',
    'echo "$(case a in a) wfctl arch accept s --agreed x;; esac)"',
    'echo "#"; wfctl arch accept s --agreed x',
    "echo '#x' && wfctl arch accept s --agreed x",
    "git commit -m '# heading' && wfctl arch accept s --agreed x",
    "echo $'\\'' ; script -q /dev/null wfctl arch accept s --agreed x #'",
    "echo $'\\'' \"' #\"; wfctl arch accept s --agreed x",
    "bash <<'EOF'\nwfctl arch accept s --agreed x\nEOF",
    "cat <<'EOF' | sh\nwfctl arch accept s --agreed x\nEOF",
    "x=\"$(bash <<'EOF'\nwfctl arch accept s --agreed x\nEOF\n)\"",
    "ssh -t host bash -c \"'wfctl arch accept s --agreed x'\"",
    "screen -X stuff 'wfctl arch accept s --agreed x\\n'",
    "osascript -e 'tell app \"Terminal\" to do script \"wfctl arch accept s --agreed x\"'",
    "echo \"$(echo $'\\')' ; script -q /dev/null wfctl arch accept s --agreed x)\"",
    "x=\"$(cat <<'EOF'\nmsg\nEOF\nscript -q /dev/null wfctl arch accept s --agreed x\nEOF\n)\"",
    "echo $$'\\' ; script -q /dev/null wfctl arch accept s --agreed x #'",
    "source <(echo 'wfctl arch accept s --agreed x')",
    ". /dev/stdin <<< 'wfctl arch accept s --agreed x'",
    "bash -c \"$(echo 'wfctl arch accept s --agreed x')\"",
    "git rebase -x 'wfctl arch accept s --agreed x' HEAD~1",
    "git submodule foreach 'wfctl arch accept s --agreed x'",
    "sudo -s wfctl arch accept s --agreed x",
    "echo 'wfctl arch accept s --agreed x' | at now",
    "echo 'wfctl arch accept s --agreed x' | tmux load-buffer - && tmux paste-buffer",
    "WFCTL arch accept s --agreed x",
])
def test_every_literal_form_the_record_names_is_refused(command: str) -> None:
    """`guard-catches-literal-accept.md` promises that the guard refuses the
    accept typed as literal words, whether it's run through a runner or a
    path, inside a script, inside a substitution, or under a pseudo-terminal.
    Other tests cover some of these forms, and this list fills in the rest,
    so a narrowing that lets one through fails here rather than in review.
    The security panel on #792 found the substitution forms after a runner
    or a separator allowed, since the guard read only the word that opened
    a substitution as the start of a command. Under `script`, a redirect to
    `/dev/tty` gives the accept a terminal. Its fifth round found two more
    gaps. Inside a script the name had to start a command, so a runner that
    takes a value, such as `sudo -u root`, or `script`'s own arguments hid
    it. And a `)` that was quoted, escaped, or ended a `case` pattern closed
    a substitution's body early. Its sixth round found that a quoted word
    starting with `#` read as a comment, which hid every command after it,
    though the shell starts a comment only at an unquoted `#`. The seventh
    round found that the fix misread `$'\\''`, an escaped quote, as a quote
    running to the end of the line, so a later `#` hid the accept. It also
    found ssh joining its arguments into one remote script, and `screen` and
    `osascript` typing a string into a terminal. A heredoc fed to a shell is
    still a script. The eighth round found three more quoting and heredoc
    misreads, and a list of programs that run a string as a script, such as
    `source`, `at`, and `git rebase -x`. Each round found forms the last
    one missed, so the guard now refuses the literal words anywhere in the
    command, unless one program that only reads text holds them."""
    refused, _ = _review_gate.read(command)

    assert _review_gate.ACCEPT_REFUSAL in refused


@pytest.mark.parametrize("command", [
    "env -S 'wfctl arch accept s --agreed x'",
    "env --split-string='wfctl arch accept s --agreed x'",
    'env -S "wfctl $C" s --agreed x',
    "tmux new-window 'wfctl arch accept s --agreed x'",
    "parallel ::: 'wfctl arch accept s --agreed x'",
    "/usr/bin/env -S 'wfctl arch accept s --agreed x'",
    "unbuffer env -S 'wfctl arch accept s --agreed x'",
    "env -S'wfctl arch accept s --agreed x'",
    "env -iS 'wfctl arch accept s --agreed x'",
    "env -vS 'wfctl arch accept s --agreed x'",
    "env --split 'wfctl arch accept s --agreed x'",
    "env --split='wfctl arch accept s --agreed x'",
    "env -S '-u HOME wfctl arch accept s --agreed x'",
    "script -q /dev/null env -S '-u HOME wfctl arch accept s --agreed x'",
    "script -q /dev/null bash -c '/usr/bin/env -S \"wfctl arch accept s --agreed x\"'",
    "env -S '-P /bin wfctl arch accept s --agreed x'",
    "env -S 'sudo -u root wfctl arch accept s --agreed x'",
    "wm send w 'wfctl arch accept s --agreed x'",
    "workmux send w 'wfctl arch accept s --agreed x'",
    "tmux display -p '#(script -q /dev/null wfctl arch accept s --agreed x)'",
    "tmux set-buffer 'wfctl arch accept s --agreed x'",
    "tmux new-session -d \\; new-window 'wfctl arch accept s --agreed x'",
    "tmux new-session -d ';' run-shell 'wfctl arch accept s --agreed x'",
    "tmux new-session -d \";\" send-keys 'wfctl arch accept s --agreed x' Enter",
])
def test_an_accept_handed_to_a_program_that_runs_its_string_is_refused(
    command: str,
) -> None:
    """The security panel on #792 found that `env -S`, `tmux`, and
    `parallel` each split a quoted string and run it as a command line, and
    the guard read that string as prose. Each one ran the real accept on
    `main` with the guard's approval. Its next round found the first fix
    matched only a bare `env` before a bare `-S`, so env's path, another
    wrapper before it, a clustered or attached `-S`, the shortened
    `--split`, and a string that starts with env's own options all got
    through. A later round found `-P` taking a value inside the string, and
    `wm send`, which types its string into another pane's shell the way
    `tmux send-keys` does. The round after that found two tmux gaps. The
    subcommands the guard had read as text run theirs: `display` expands
    `#(…)` through a shell, and a stored buffer runs once it's pasted. And
    tmux's own `\\;` split the command, so the part after it no longer read
    as tmux's."""
    refused, _ = _review_gate.read(command)

    assert _review_gate.ACCEPT_REFUSAL in refused


@pytest.mark.parametrize("command", [
    'tmux new-window -n "build logs"',
    'env -S "PATH=/usr/bin" git status',
    "echo env -S 'wfctl status'",
    "git commit -m \"env -S 'wfctl status' is caught\"",
    "git commit -m 'single-quoted $( then; wfctl status) prose'",
    "tmux capture-pane -p -t w | grep -n 'wfctl status'",
    'git commit -m "$(date) see wfctl status (and more)"',
    "git commit -m \"$(cat <<'EOF'\nfix: x\n\nwfctl status; then wfctl doctor\nEOF\n)\"",
    "gh pr create --title t --body \"$(cat <<'EOF'\n## Summary\n\n"
    "run wfctl status && wfctl doctor\nEOF\n)\"",
    "bash -c 'echo wfctl status is for a person'",
    "bash -c 'git commit -m \"wfctl status is for a person\"'",
])
def test_a_string_handed_to_a_running_program_without_the_accept_is_not_refused(
    command: str,
) -> None:
    """Reading those strings as scripts mustn't refuse one that doesn't run
    the accept. CodeRabbit on #797 found `echo env -S '…'` refused, since
    the check looked for `env` anywhere before `-S` rather than as the
    program, and `echo` only prints the string. The fifth security round
    found three more: the env reading inside a quoted message, a `$(` inside
    single quotes, where the shell runs nothing, and `tmux` reading every
    quoted word in a pipeline as a script, though tmux never reads its input
    as one. The seventh round found a heredoc message, the usual way an
    agent passes a commit message or PR body, refused when a line named the
    accept, since each line of the substitution's body read as a command."""
    refused, _ = _review_gate.read(command)

    assert _review_gate.ACCEPT_REFUSAL not in refused


@pytest.mark.parametrize("command", [
    "git commit -m \"$(cat <<'EOF'\nfix: x\n\nwfctl arch accept is for a person\nEOF\n)\"",
    "rg 'wfctl arch accept' docs/",
    "tmux capture-pane -p -t w | grep -n 'wfctl arch accept'",
    "echo env -S 'wfctl arch accept s --agreed x'",
])
def test_text_that_spells_out_the_accept_is_refused(command: str) -> None:
    """Eight security rounds on #792 each found a shell form that hid the
    literal accept from the guard's reading of the command. So the guard
    refuses the literal words anywhere in the text, unless one program that
    only reads text holds them, as
    `test_a_program_that_only_reads_text_may_name_the_accept` says. Each
    command here falls outside that: a substitution, a reader such as `rg`
    that can run a program, a pipeline, or `echo`, whose output a later
    stage could run."""
    refused, _ = _review_gate.read(command)

    assert _review_gate.ACCEPT_REFUSAL in refused


@pytest.mark.parametrize("command", [
    'git commit -m "To sign off, run wfctl arch accept on the record again"',
    "uv run towncrier create 769.change.md --content 'run wfctl arch accept on it again'",
    'grep -rn "wfctl arch accept" wfctl/',
    'git commit -m "wfctl arch accept --dry-run previews the write"',
    "towncrier create 792.change.md --content 'wfctl arch accept s --agreed x'",
    "git commit -m 'run `wfctl arch accept` on the record again'",
    "grep -rn '`wfctl arch accept`' docs/",
    "towncrier create 792.change.md --content 'run `wfctl arch accept` again'",
])
def test_a_program_that_only_reads_text_may_name_the_accept(command: str) -> None:
    """`accept-check-threat-model.md` lists a commit message, a grep, and a
    release note naming the full command as forms the guard must let
    through, and #792 refused all three. None of these programs runs its
    arguments, so the words in them run nothing. The code review found the
    backticked forms still refused, since a later reading took a backtick
    inside single quotes as a substitution, though the shell runs nothing
    there."""
    refused, _ = _review_gate.read(command)

    assert _review_gate.ACCEPT_REFUSAL not in refused


@pytest.mark.parametrize("command", [
    "git -c core.editor='wfctl arch accept s --agreed x' commit",
    "GIT_EDITOR='wfctl arch accept s --agreed x' git commit",
    "git commit -m 'wfctl arch accept'; wfctl arch accept s --agreed x",
    "git commit -m 'wfctl arch accept' && wfctl arch accept s --agreed x",
    "git commit -m 'wfctl arch accept'\nwfctl arch accept s --agreed x",
    'git commit -m "see `wfctl arch accept s --agreed x`"',
    'git commit -m "see $(wfctl arch accept s --agreed x)"',
    "grep x *(e:'wfctl arch accept s --agreed x':)",
    "grep 'wfctl arch accept' | sh",
    "grep 'wfctl arch accept' >(sh)",
    "git rebase -x 'wfctl arch accept s --agreed x'",
    "rg --pre 'wfctl arch accept s --agreed x' x",
    "grep --filter='*:wfctl arch accept s --agreed x' x f",
    "grep --pager='wfctl arch accept s --agreed x' x",
    "git commit -m x --trailer 'k=wfctl arch accept s --agreed x'",
    "git commit -m x --trai 'k=wfctl arch accept s --agreed x'",
    "git commit -m x --tr='k=wfctl arch accept s --agreed x'",
    "git commit -m 'unclosed wfctl arch accept s",
])
def test_a_text_reader_does_not_excuse_a_command_that_runs_the_accept(
    command: str,
) -> None:
    """Letting a program that only reads text name the accept is the
    narrowing the #792 security rounds kept breaking, so each way around it
    is pinned: an option or assignment that makes git run a program, a
    second command, a substitution inside double quotes, a zsh glob
    qualifier, which runs code, a pipe or process substitution into a
    shell, a reader left off the list because it runs a program, and text
    the shell can't split. The security review of that change added two
    more: ugrep, which Claude Code runs as `grep`, runs a program through
    `--filter` or `--pager`, and git runs one for a `--trailer` key when
    config sets a command for it. The next round found git taking `--trai`
    as `--trailer`, since git accepts any unique prefix of a long option."""
    refused, _ = _review_gate.read(command)

    assert _review_gate.ACCEPT_REFUSAL in refused


@pytest.mark.parametrize("name", ["$X", "wf?tl", "./wfctl.sh", "wfctlx"])
def test_a_dry_run_not_spelled_out_does_not_excuse_a_literal_accept(
    name: str,
) -> None:
    """Security run 009 on #792 found the literal-words check counted every
    dry run against the literal hits, including one whose name isn't spelled
    `wfctl` and so was never a hit. That dry run cancelled a real accept
    quoted into a script the guard can't read, here `git rebase -x` under a
    pseudo-terminal."""
    command = (
        "X=wfctl; git rebase -x 'script -q /dev/null "
        + " ".join(["wfctl", "arch", "accept"])
        + f" rec' HEAD~1; {name} arch accept y --dry-run"
    )
    refused, _ = _review_gate.read(command)

    assert _review_gate.ACCEPT_REFUSAL in refused


@pytest.mark.parametrize("between", [
    ("2>/dev/null", ""), ("", "2>/dev/null"), ("", ">&2"), ("", "&>x"),
    ("", "2>&1"), ("", "<&0"), ("", "2> /dev/null"), ("--", ""), ("", "--"),
])
@pytest.mark.parametrize("wrap", ["{}", "bash -c '{}'", "script -q /dev/null {}"])
def test_a_redirection_or_double_dash_between_the_words_is_refused(
    between: tuple[str, str], wrap: str,
) -> None:
    """Security run 009 on #792 found the literal words got past every
    reading once a redirection or `--` sat between them. The shell drops the
    redirection, and wfctl's parser drops the `--`, so wfctl still runs the
    accept, and `2>/dev/null` leaves the terminal check satisfied."""
    first, second = between
    words = ["wfctl", first, "arch", second, "accept", "rec"]
    command = wrap.format(" ".join(w for w in words if w))

    refused, _ = _review_gate.read(command)

    assert _review_gate.ACCEPT_REFUSAL in refused


@pytest.mark.parametrize("between", [
    ("", "2>'/tmp/a b'"), ("", '>"a b"'), ("", "2>/tmp/a\\ b"), ("", ">\\;"),
    ("", "<<< 'a b'"), ("", "> >(cat)"), ("2>'a b'", ""), ("", '>"a;b"'),
    ("", '>"a|b"'), ("", '>"a<b"'), ("", '>"a(b"'), ("", "&>'a b'"),
    ("", "{fd}>'a b'"),
])
@pytest.mark.parametrize("wrap", ["{}", "env {}", "script -q /dev/null {}"])
def test_a_quoted_or_spaced_redirection_target_between_the_words_is_refused(
    between: tuple[str, str], wrap: str,
) -> None:
    """Security run 010 on #792 found the redirection fix read only a target
    with no space or shell character in it. With the quotes removed, a target
    such as `'a b'` left a fragment between the words, so the literal accept
    went through, and under `script` it had a terminal too."""
    first, second = between
    words = ["wfctl", first, "arch", second, "accept", "rec"]
    command = wrap.format(" ".join(w for w in words if w))

    refused, _ = _review_gate.read(command)

    assert _review_gate.ACCEPT_REFUSAL in refused


@pytest.mark.parametrize("dry_run", [
    "wfctl arch > 'a b' {} r --dry-run",
    "wfctl arch 2>a\\;b {} r --dry-run",
    "wfctl arch 2>'a(b' {} r --dry-run",
])
def test_a_dry_run_with_a_quoted_redirection_does_not_excuse_a_literal_accept(
    dry_run: str,
) -> None:
    """Security run 010 on #792 found a dry run with a quoted redirection
    target between the words counted as a dry run, while the literal-words
    check never counted it as a hit. It cancelled a real accept quoted into
    `git rebase -x`."""
    accept = " ".join(["wfctl", "arch", "accept"])
    command = (
        f"git rebase -x '{accept} r --agreed x' HEAD~1; "
        + dry_run.format("accept")
    )

    refused, _ = _review_gate.read(command)

    assert _review_gate.ACCEPT_REFUSAL in refused


@pytest.mark.parametrize("target", [
    "2>/tmp/{w}", ">{w}", "<<{w}", "> {w}", '2> "/tmp/{w} x"',
])
@pytest.mark.parametrize("wrap", [
    "{}", "env {}", "uv run {}", "script -q /dev/null {}", "bash -c '{}'",
    "git rebase -x '{}' HEAD~1",
])
def test_a_redirection_target_holding_the_name_is_refused(
    target: str, wrap: str,
) -> None:
    """Security run 011 on #792 found the literal-words check stopped its gap
    at any `wfctl`, even one inside a redirection target such as `>wfctl`.
    No hit was counted, and nothing else read the command, so the accept
    went through, under `script` with a terminal too."""
    w = "wfctl"
    words = [w, "arch", target.format(w=w), "accept", "rec"]
    command = wrap.format(" ".join(words))

    refused, _ = _review_gate.read(command)

    assert _review_gate.ACCEPT_REFUSAL in refused


def test_a_dry_run_whose_target_spells_the_name_does_not_excuse_an_accept() -> None:
    """Security run 011 on #792 found the dry-run count read shell words,
    which keep a quote nested in the other kind, while the hit count read the
    text with every quote removed. A target such as `"wf'ctl"` became the
    name for one count and not the other, so the dry run cancelled a real
    accept elsewhere."""
    accept = " ".join(["wfctl", "arch", "accept"])
    command = (
        "wfctl arch 2>\"wf'ctl\" accept r --dry-run; "
        f"git rebase -x 'script -q /dev/null {accept} r --agreed x' HEAD~1"
    )

    refused, _ = _review_gate.read(command)

    assert _review_gate.ACCEPT_REFUSAL in refused


@pytest.mark.parametrize("runner", [
    "python3 -c 'import os,sys; os.system(sys.argv[1])'",
    "unbuffer sh -c '$1' x",
    "perl -e 'system $ARGV[0]'",
])
def test_a_quoted_accept_followed_by_a_bare_dry_run_is_refused(runner: str) -> None:
    """Security run 011 on #792 found a quoted argument holding the whole
    accept, followed by the bare words `arch accept --dry-run`, read as one
    dry run whose name was the quoted argument. The dry run cancelled the
    only literal hit, so a runner the guard doesn't know ran the accept."""
    accept = " ".join(["wfctl", "arch", "accept"])
    command = f"{runner} '{accept} r' arch accept --dry-run"

    refused, _ = _review_gate.read(command)

    assert _review_gate.ACCEPT_REFUSAL in refused


@pytest.mark.parametrize("word", ["arch", "review"])
def test_many_repeated_words_are_read_in_linear_time(word: str) -> None:
    """Security run 011 on #792 found 16,000 `arch >` words after one name
    took 27 seconds. The approve-imports and sign-off patterns each restarted
    their scan to the end of the text at every `arch` or `review`."""
    command = "echo wfctl > " + f"{word} > " * 16000
    started = time.monotonic()

    _review_gate.read(command)

    assert time.monotonic() - started < 2


def test_help_piped_into_a_search_for_the_accept_word_is_not_refused() -> None:
    """Security run 011 on #792 found `--help` opened the gap the literal
    check allows for `--`, so the search after the pipe read as the third
    word. `--help` is an option, not the `--` that ends them."""
    command = "uv run wfctl arch --help | grep -A3 accept"

    refused, _ = _review_gate.read(command)

    assert _review_gate.ACCEPT_REFUSAL not in refused


def test_a_literal_accept_padded_with_many_names_is_read_in_linear_time() -> None:
    """The literal-words check lets any text that starts with a redirection
    sit between the words, so a command holding the name thousands of times
    must not rescan the text after each one."""
    command = "echo " + "wfctl > " * 8000 + "arch"
    started = time.monotonic()

    _review_gate.read(command)

    assert time.monotonic() - started < 2


def test_a_dry_run_with_a_redirection_between_the_words_still_passes() -> None:
    """The literal-words check now reads past a redirection between the
    words, so the dry run it excuses has to be read the same way, or the
    preview an agent is told to run would be refused."""
    command = " ".join(["wfctl", "arch", "2>/dev/null", "accept", "rec", "--dry-run"])

    refused, _ = _review_gate.read(command)

    assert _review_gate.ACCEPT_REFUSAL not in refused


def test_a_dry_run_flag_taken_as_a_heredoc_delimiter_is_refused() -> None:
    """Security run 009 on #792 found `2<<- --dry-run` read as a dry run.
    The shell takes `--dry-run` as the heredoc's delimiter, so wfctl never
    gets the flag and accepts the record."""
    command = " ".join(["wfctl", "arch", "accept", "rec", "2<<-", "--dry-run"])

    refused, _ = _review_gate.read(command)

    assert _review_gate.ACCEPT_REFUSAL in refused


def test_a_long_case_substitution_is_read_in_linear_time() -> None:
    """The security panel on #792 found that reading a `$(case …)` body
    recounted every `case` and `esac` at each `)`, so a 60 KB command took
    13 seconds in a hook that runs before every command."""
    command = "echo \"$(case a in " + "a) b;; " * 8000 + "esac) arch\""
    started = time.monotonic()

    _review_gate.read(command)

    assert time.monotonic() - started < 2
    refused, _ = _review_gate.read(command)

    assert _review_gate.ACCEPT_REFUSAL not in refused


@pytest.mark.parametrize("command", [
    "wfctl issue create --title t --body 'The template asks for"
    " `wfctl owns \"did the check pass?\"`. The fix edits"
    " `architecture-decisions/SKILL.md`.'",
    "git commit -m 'run wfctl doctor, then read `docs/a.md`'",
    "git commit -m 'the `x` section. wfctl checks `y` and `z`'",
])
def test_prose_naming_wfctl_before_a_later_path_and_backtick_is_not_refused(
    command: str,
) -> None:
    """A session on #792 was refused on 2026-11-18 for filing an issue whose
    body quoted `wfctl owns "…"` and later named a file path in backticks.
    The rule for one word holding the name and an expansion keeps the whole
    word when a slash comes after a space, since `"/tmp/wfctl x/bin/wfctl"$C`
    starts the path to wfctl again. A slash anywhere later in a body met
    that test, so the backtick around the file name counted as an expansion
    after the name. Now the path's last segment before the expansion has to
    name wfctl, with no space in it. The same body formatted a section name
    as code before naming wfctl, and any backtick before the name read as an
    open substitution, so an even count now reads as closed."""
    refused, _ = _review_gate.read(command)

    assert _review_gate.ACCEPT_REFUSAL not in refused


def test_an_accept_the_shell_cant_split_is_refused() -> None:
    """An unclosed quote leaves the flag unreadable, and the guard refuses
    what it can't read rather than guess it holds `--dry-run`."""
    refused, _ = _review_gate.read('wfctl arch accept x --agreed "unclosed')

    assert _review_gate.ACCEPT_REFUSAL in refused


def test_a_commit_message_with_arch_and_accept_apart_is_not_refused() -> None:
    """R-013 keeps the pattern to consecutive `wfctl arch accept` words,
    tighter than the sign-off pattern, because commit messages about the
    accept command are routine."""
    refused, _ = _review_gate.read('git commit -m "arch: accept the record"')

    assert _review_gate.ACCEPT_REFUSAL not in refused


def test_the_hook_refuses_an_accept_though_the_command_holds_no_other_trigger(
    guard: Guard, tmp_path: Path,
) -> None:
    """`wfctl arch accept x --agreed y` holds none of `gh`, `merge`, `sign`,
    or `approve`, so the hook's substring test has to include `accept` or the
    text pass never runs."""
    code, err = guard("wfctl arch accept x --agreed y", tmp_path)

    assert code == 2
    assert err == _ACCEPT_TEXT + "\n"


@pytest.mark.parametrize("command", [
    "wfctl arch acc\\ept x --agreed y",
    "A=acc'ept'; wfctl arch $A x --agreed y",
    "wfctl {ar,}ch {acc,}ept x --agreed y",
    "wfctl ar\\\nch ac\\\ncept x --agreed y",
    "script -q /dev/null wfctl ar\\\nch ac\\\ncept x --agreed y",
])
def test_the_hook_reaches_the_accept_check_when_the_word_accept_is_split(
    guard: Guard, tmp_path: Path, command: str,
) -> None:
    """The hook's substring test runs before the text pass. A test on the raw
    text for `accept` let `acc\\ept` skip the text pass entirely, however
    well `_accepts` reads it."""
    code, err = guard(command, tmp_path)

    assert code == 2
    assert _ACCEPT_TEXT in err


@pytest.mark.parametrize("glued", [
    "wfctl arch>/dev/null accept rec",
    "wfctl arch 2>/dev/null accept>/dev/null rec",
    "wfctl arch</dev/null accept rec",
    "wfctl arch>&2 accept rec",
    "wfctl arch> /tmp/x accept rec",
])
@pytest.mark.parametrize("wrap", [
    "{}", "env {}", "script -q /dev/null {}", "bash -c '{}'",
    "{} <<X\nit's\nX",
])
def test_a_redirection_attached_to_a_word_of_the_accept_is_refused(
    glued: str, wrap: str,
) -> None:
    """CodeRabbit on #797 found `arch>/dev/null` hid the accept from both
    readings. The shell ends the word `arch` at the `>`, but the split kept
    them as one word, and the text search wanted a space after `arch`. The
    heredoc holding an apostrophe is text `shlex` can't split, so only the
    text search reads it."""
    command = wrap.format(glued)

    refused, _ = _review_gate.read(command)

    assert _review_gate.ACCEPT_REFUSAL in refused


def test_a_dry_run_with_a_redirection_attached_to_arch_still_passes() -> None:
    """Both readings now end `arch` at an attached redirection, so the dry
    run has to be read the same way, or the preview would be refused."""
    command = " ".join(["wfctl", "arch>/dev/null", "accept", "rec", "--dry-run"])

    refused, _ = _review_gate.read(command)

    assert _review_gate.ACCEPT_REFUSAL not in refused


@pytest.mark.parametrize("command", [
    "eval wfctl arch accept x \\# --dry-run",
    "eval wfctl arch accept x '#' --dry-run",
    "echo wfctl arch accept x \\# --dry-run | sh",
    'echo wfctl arch accept x "#" --dry-run | sh',
    "{ echo wfctl arch accept x \\# --dry-run; } | sh",
    "watch wfctl arch accept x \\# --dry-run",
    "wfctl arch accept rec --agreed one\\ #two --dry-run",
])
def test_a_dry_run_after_a_quoted_hash_is_refused(command: str) -> None:
    """Code run 001 on #792 found a quoted or escaped `#` before the flag
    let the accept through once comments were read on the raw text. A shell
    that reads the words again, such as `eval` or `sh`, takes the `#` as a
    comment and drops `--dry-run`. The guard can't always tell which shell
    reads the words last, so a dry run after any word holding `#` is no
    dry run."""
    refused, _ = _review_gate.read(command)

    assert _review_gate.ACCEPT_REFUSAL in refused


@pytest.mark.parametrize("command", [
    "(wfctl arch accept x)# --dry-run",
    "() { wfctl arch accept x } --dry-run",
    "(wfctl arch accept x) --dry-run",
])
def test_a_dry_run_past_a_closing_group_is_refused(command: str) -> None:
    """Code run 001 on #792 found two ways a group hides the flag from
    wfctl. A `#` after a subshell's `)` starts a comment, and zsh gives the
    words after an anonymous function's `}` to the function."""
    refused, _ = _review_gate.read(command)

    assert _review_gate.ACCEPT_REFUSAL in refused


@pytest.mark.parametrize("sink", [
    "unbuffer -p sh", "source /dev/stdin", ". /dev/stdin", "busybox sh", "tcsh",
])
def test_a_dry_run_echoed_into_any_reader_is_refused(sink: str) -> None:
    """Security run 014 on #792 found a dry run counted wherever the name
    appeared, even as `echo`'s argument, so piping it into a shell the guard
    doesn't list ran the accept. Only a dry run that runs wfctl counts."""
    command = f"echo wfctl arch accept x --dry-run | cut -d' ' -f1-4 | {sink}"

    refused, _ = _review_gate.read(command)

    assert _review_gate.ACCEPT_REFUSAL in refused


@pytest.mark.parametrize("sink", [
    "tcsh", "source /dev/stdin", "unbuffer -p zsh", "busybox sh",
])
def test_a_dry_run_in_a_heredoc_body_is_refused(sink: str) -> None:
    """Security run 015 on #792 found the split reads each heredoc line as
    a command, so a body line that runs wfctl counted as a dry run, while
    `cut` dropped the flag before the reader ran the words."""
    command = (
        "cut -d' ' -f1-4 <<'EOF' | " + sink
        + "\nwfctl arch accept r --dry-run\nEOF"
    )

    refused, _ = _review_gate.read(command)

    assert _review_gate.ACCEPT_REFUSAL in refused


@pytest.mark.parametrize("command", [
    "nice -n 5 wfctl arch accept x --dry-run",
    "( wfctl arch accept x --dry-run )",
    "time wfctl arch accept x --dry-run",
    "uv run wfctl arch accept x --dry-run",
    "wfctl arch accept --dry-run -- slug",
    "wfctl arch accept x --agreed 'fix(guard)' --dry-run",
])
def test_a_dry_run_that_runs_wfctl_still_passes(command: str) -> None:
    """A dry run counts where wfctl is the command the shell runs, after a
    runner or keyword, and a citation ending in `)` is still a citation."""
    refused, _ = _review_gate.read(command)

    assert _review_gate.ACCEPT_REFUSAL not in refused


def test_a_dry_run_piped_into_a_shell_is_refused() -> None:
    """Code run 001 on #792 found a pipeline stage could cut the flag off
    before the shell ran the words. A dry run gets no excuse when a shell
    in the command can read another command's output."""
    command = "echo wfctl arch accept x --dry-run | cut -d' ' -f1-4 | sh"

    refused, _ = _review_gate.read(command)

    assert _review_gate.ACCEPT_REFUSAL in refused


def test_a_command_built_only_from_ansi_c_escapes_reaches_the_accept_check(
    guard: Guard, tmp_path: Path,
) -> None:
    """Code run 001 on #792 found the hook's quick check never sent a
    command written only in `$'…'` escapes to the guard, so decoding them
    there did nothing."""
    command = "$'\\x77fctl' $'\\x61rch' $'\\x61ccept' x --agreed y"

    code, err = guard(command, tmp_path)

    assert code == 2
    assert _ACCEPT_TEXT in err


def test_a_dry_run_after_a_redirection_to_a_file_named_dash_passes() -> None:
    """CodeRabbit on #797 found `2>-` read as an operator waiting for its
    target, so the `--dry-run` after it read as that target. The shell
    redirects to a file named `-`, and wfctl gets the flag. Only `<<-` is an
    operator that ends in a dash."""
    command = " ".join(
        ["wfctl", "arch", "accept", "rec", "--agreed", "x", "2>-", "--dry-run"]
    )

    refused, _ = _review_gate.read(command)

    assert _review_gate.ACCEPT_REFUSAL not in refused


@pytest.mark.parametrize("command", [
    "wfctl arch accept rec --agreed x< --dry-run >&0",
    "wfctl arch accept rec --agreed x<> --dry-run >&0",
    "wfctl arch accept rec --agreed x>> --dry-run",
    "wfctl arch accept rec> --dry-run",
    "wfctl arch accept rec --agreed=y> --dry-run",
    "wfctl arch accept rec --agreed y >a> --dry-run",
    "wfctl arch accept<a< --dry-run rec --agreed y >&0",
    "wfctl arch accept>x< --dry-run rec",
    "wfctl arch accept>a> --dry-run rec",
    "wfctl arch accept --agreed <f --dry-run x",
    "wfctl arch accept x --agreed >f --dry-run",
    "wfctl arch accept x --agreed > f --dry-run",
    "wfctl arch accept x --agreed 2>/dev/null --dry-run",
    "wfctl arch accept x --agreed<f --dry-run",
    "uv run wfctl arch accept x --agreed <f --dry-run",
    "wfctl arch accept rec '>' --agreed --dry-run",
    'wfctl arch accept rec ">" --agreed --dry-run',
    "wfctl arch accept rec \\> --agreed --dry-run",
    "wfctl arch accept rec '2>' --agreed --dry-run",
    "wfctl arch accept 'rec<' --agreed --dry-run",
    "wfctl arch accept rec<f --agreed --dry-run",
    "wfctl arch accept rec</dev/tty --agreed --dry-run",
    "wfctl arch accept rec x>f --agreed --dry-run",
    "wfctl arch accept rec --x>b --agreed --dry-run",
    "wfctl arch accept rec 'a>b' --agreed --dry-run",
    'wfctl arch accept rec "a<b" --agreed --dry-run',
    "uv run wfctl arch accept rec>/dev/null --agreed --dry-run",
    "wfctl arch accept<a>b --agreed --dry-run",
    "xargs -I--dry-run wfctl arch accept rec --dry-run < in",
    "xargs -J--dry-run wfctl arch accept rec --dry-run < in",
])
def test_a_dry_run_the_word_before_it_or_xargs_takes_away_is_refused(
    command: str,
) -> None:
    """Security run 019 on #792 found two ways the flag never reaches wfctl.
    A redirection attached to the word before it, as in `x<`, makes
    `--dry-run` the file it opens. `xargs -I--dry-run` swaps the flag for
    each input line. A symlink named `--dry-run` pointing at the user's
    terminal then satisfies the terminal check behind the guard. Code run
    005 found the same redirection attached to `accept` itself, as in
    `accept<a<`. Security run 020 found a redirection between `--agreed`
    and the flag, which the shell removes, so wfctl reads `--dry-run` as the
    citation. Code run 006 found the fix for that skipped `--agreed` itself
    as a redirection's target, after a quoted `'>'` the split can't tell
    from an operator, or after `rec<f`, which holds its own target."""
    refused, _ = _review_gate.read(command)

    assert _review_gate.ACCEPT_REFUSAL in refused


@pytest.mark.parametrize("command", [
    "wfctl arch accept rec --agreed y >f --dry-run",
    "wfctl arch accept rec --agreed y > f --dry-run",
    "wfctl arch accept rec --agreed y 2>/dev/null --dry-run",
    "wfctl arch accept rec --agreed x 2>- --dry-run",
    "wfctl arch accept<a>b rec --dry-run",
    "uv run wfctl arch accept rec --agreed y >f --dry-run",
])
def test_a_dry_run_with_a_redirection_after_the_citation_still_passes(
    command: str,
) -> None:
    """Reading past redirections to find the word before `--dry-run` must
    not refuse a dry run whose citation comes before the redirection, since
    wfctl still gets the flag. Code run 006 found the refusing side had
    tests and this side had none."""
    refused, _ = _review_gate.read(command)

    assert _review_gate.ACCEPT_REFUSAL not in refused


@pytest.mark.parametrize("command", [
    ">/dev/null wfctl arch accept rec --dry-run",
    "> /dev/null wfctl arch accept rec --dry-run",
    "2>/dev/null uv run wfctl arch accept rec --dry-run",
    "wfctl arch accept rec --agreed review>/dev/null --dry-run",
    "wfctl arch accept rec --agreed 'a>b' --dry-run",
    "wfctl arch accept rec --agreed 'issue {draft}' --dry-run",
    "wfctl arch accept rec --agreed 'see (a b)' --dry-run",
    "wfctl arch accept rec --agreed '|' --dry-run",
    "wfctl arch accept rec --agreed 'a; b' --dry-run",
    "wfctl arch accept rec --agreed a\\&b --dry-run",
    "wfctl >wfctl arch accept rec --dry-run",
    "wfctl arch accept rec --agreed '|' --dry-run >ox",
])
def test_a_dry_run_wfctl_gets_whole_passes(command: str) -> None:
    """CodeRabbit found each of these refused on #797, though bash hands
    wfctl `--dry-run` as its own flag in every one. A redirection before
    wfctl isn't the program, an inline target such as `review>/dev/null`
    takes no next word, a quoted `}`, `)`, or separator is part of the
    citation, and a target named `wfctl` shares the dry run's `arch
    accept` rather than starting a second one. CodeRabbit's re-review found
    that a stand-in character anywhere in the text turned the
    quoted-separator reading off for all of it."""
    refused, _ = _review_gate.read(command)

    assert _review_gate.ACCEPT_REFUSAL not in refused


@pytest.mark.parametrize("command", [
    ">x wfctl arch accept rec",
    "A=1 >x wfctl arch accept rec --dry-run",
    ">x xargs -I--dry-run wfctl arch accept rec --dry-run",
    "wfctl arch accept rec --agreed rec>! --dry-run",
    "wfctl arch accept rec --agreed rec>> --dry-run",
    "wfctl arch accept rec --agreed x } --dry-run",
    "wfctl arch accept rec --agreed x | cat --dry-run",
    "wfctl arch accept rec --agreed x ; echo --dry-run",
    "wfctl >wfctl arch accept rec --dry-run; wfctl arch accept other",
    "wfctl arch accept rec --agreed 'a\ue000' --dry-run; wfctl arch accept r",
    "wfctl arch accept rec --agreed '\ue000' --dry-run \ue000 wfctl arch accept r",
    "wfctl arch accept rec >& --dry-run",
    "wfctl arch accept rec 2>& --dry-run",
    "wfctl arch accept rec 2>&1& --dry-run",
    "wfctl arch accept rec 2>&1 & wfctl arch accept r --dry-run",
    'wfctl arch accept rec --agreed "issue 792 comment"\\>&1 --dry-run',
    "wfctl arch accept rec \\>&1 --dry-run",
    "wfctl arch accept rec 2\\>&1 --dry-run",
    "wfctl arch accept rec x\\>&1 --dry-run",
    'wfctl arch accept rec --agreed "x" \\<&0 --dry-run',
    "wfctl arch accept rec '>'&1 --dry-run",
    'wfctl arch accept rec ">"&1 --dry-run',
    "wfctl arch accept rec >&! --dry-run",
    "wfctl arch accept rec 2>&! --dry-run",
    "wfctl arch accept rec >>&! --dry-run",
    "wfctl arch accept rec /dev/fd/<->& x --dry-run",
    "wfctl arch accept rec /dev/fd/<->&1 x --dry-run",
    "wfctl arch accept s --agreed x --dry-run 2>&1",
    "wfctl arch accept s --agreed x --dry-run &>/dev/null",
    "xargs -I--dry-run <<<x &>/dev/null wfctl arch accept rec --dry-run",
    "xargs -I--dry-run <<<x &>>/dev/null wfctl arch accept rec --dry-run",
    "xargs -I--dry-run <<<x &>! /dev/null wfctl arch accept rec --dry-run",
    "xargs -I--dry-run <<<x &> /dev/null wfctl arch accept rec --dry-run",
    "xargs -a f -I--dry-run &>/dev/null wfctl arch accept rec --dry-run",
    "git -c alias.arch='!f(){ script -q /dev/null wfctl arch $1 $2; }; f'"
    " >&wfctl arch accept rec --dry-run",
    "true >&! wfctl arch accept rec --dry-run",
    "> >(sh) echo wfctl $A",
    ">>(sh) echo wfctl $A",
])
def test_the_dry_runs_cleared_for_coderabbit_keep_their_neighbors_refused(
    command: str,
) -> None:
    """Each fix for the dry runs above sits next to a form that must stay
    refused: a redirection before wfctl with no dry run, with an
    assignment, or with `xargs`, a target that is still waiting, such as
    after zsh's `>!`, a `}` or separator the shell acts on, and a second
    accept the shared match must not excuse.
    A typed stand-in character must not come back from the split as a
    separator. A `>&` with nothing attached still opens `--dry-run` as its
    file, and the `&` after `2>&1` still ends the command. Security runs 022
    and 023 found three ways past a rule that read the `&` after a `>` as
    part of a redirection: an escaped or quoted `>`, as in `x\\>&1`, zsh's
    `>&!`, which opens `--dry-run` as its file, and the `>` closing zsh's
    `<->` glob. In each, the shell runs the accept without the flag. Security
    run 024 found that counting commands past the `&` of `&>` or `>&`, so a
    trailing `2>&1` could pass, let a program before that `&` run the
    accept: `xargs` swapping out `--dry-run`, or a git alias passing on only
    two of its words. A dry run with any `&` redirection is refused until
    #821 reads them. Security run 021 found the redirection skip read past a
    process substitution such as `> >(sh)`, which made `echo` the program
    and let a name built at run time through."""
    refused, _ = _review_gate.read(command)

    assert _review_gate.ACCEPT_REFUSAL in refused


def test_a_heredoc_cat_only_prints_is_not_read_for_the_words_in_order() -> None:
    """CodeRabbit found on #797 that an apostrophe in a quoted `cat`
    heredoc made the split fail, and the fallback then refused a message
    that only mentioned wfctl, arch, and accept in that order. `cat` prints
    a quoted heredoc as it is, so the body runs nothing."""
    command = (
        "cat <<'EOF'\n"
        "wfctl status shows arch state. Only accept reviewed changes. It's documented.\n"
        "EOF"
    )

    refused, _ = _review_gate.read(command)

    assert _review_gate.ACCEPT_REFUSAL not in refused


@pytest.mark.parametrize("command", [
    "cat <<'EOF' | sh\nwfctl > /tmp/research arch accept rec\nEOF\necho it's",
    "sh -c \"\ncat <<'EOF'\nwfctl > /tmp/research arch accept rec\nEOF\n\" | sh\necho it's",
    "while true; do\ncat <<'EOF'\nwfctl > /tmp/research arch accept rec\nEOF\ndone | sh\necho it's",
    "{\ncat <<'EOF'\nwfctl > /tmp/research arch accept rec\nEOF\n} > f; bash f; echo it's",
    "cat <<EOF\nwfctl > /tmp/research arch accept rec\nEOF\necho it's",
    "cat <<'EOF'\nwfctl > /tmp/research arch accept rec\necho it's",
    "hash -p /bin/sh cat\ncat <<'EOF'\nwfctl > /tmp/o 2> /tmp/research arch accept rec\nit's\nEOF",
    "hash cat=/bin/sh\ncat <<'EOF'\nwfctl > /tmp/o 2> /tmp/research arch accept rec\nit's\nEOF",
    "alias cat=sh\ncat <<'EOF'\nwfctl > /tmp/o 2> /tmp/research arch accept rec\nit's\nEOF",
    "functions[cat]=sh\ncat <<'EOF'\nwfctl > /tmp/o 2> /tmp/research arch accept rec\nit's\nEOF",
    "export PATH=/tmp/x:$PATH\ncat <<'EOF'\nwfctl > /tmp/o 2> /tmp/research arch accept rec\nit's\nEOF",
])
def test_a_heredoc_whose_body_a_shell_could_read_keeps_its_words(command: str) -> None:
    """A heredoc body is left out of the words-in-order reading only when
    the text holds nothing but printed heredocs. Security run 021 on #792
    found an earlier line could make `cat` a shell with no pipe or group,
    through `hash`, an alias, zsh's `functions`, or a new `PATH`, and bash
    then ran the body's accept with no `--dry-run`. A pipe, a group, a
    `cat` inside a quoted script, an unquoted delimiter, or a missing
    closing line keeps the body in too. The end-to-end refusal can come
    from another check, so the reading is asserted on its own."""
    runnable = _review_gate._runnable(command)

    assert _review_gate._in_order(runnable)
    assert _review_gate.ACCEPT_REFUSAL in _review_gate.read(command)[0]


@pytest.mark.parametrize("command", [
    "cat =(wfctl arch accept rec) --dry-run",
    "cat =(script -q /dev/null wfctl arch accept rec) --dry-run",
    "echo x; cat =(wfctl arch accept rec) --dry-run",
])
def test_a_zsh_file_substitution_does_not_get_the_dry_run_excuse(command: str) -> None:
    """Security run 013 on #792 found zsh's `=(…)` wasn't read as a
    substitution. zsh runs its body and gives `--dry-run` to `cat`, so the
    dry run excused a real accept, under `script` with a terminal too."""
    refused, _ = _review_gate.read(command)

    assert _review_gate.ACCEPT_REFUSAL in refused


def test_an_array_assignment_is_not_read_as_a_substitution() -> None:
    """zsh reads `=(` as a substitution only at the start of a word, so a
    citation such as `a=(x)` leaves a dry run excused."""
    command = "wfctl arch accept rec --agreed 'a=(x)' --dry-run"

    refused, _ = _review_gate.read(command)

    assert _review_gate.ACCEPT_REFUSAL not in refused


def test_a_redirect_target_naming_wfctl_counts_its_dry_run_once() -> None:
    """Security run 013 on #792 found `wfctl >wfctl arch accept x --dry-run`
    counted as two dry runs, one at each name, against one literal match.
    The spare cancelled a real accept in a `bash -c` script the split
    couldn't read, and bash ran it."""
    hidden = "bash -c \"cat <<EOF\ndon't\nEOF\nwfctl >/dev/null arch accept rec\""
    command = "wfctl >wfctl arch accept x --dry-run; " + hidden

    refused, _ = _review_gate.read(command)

    assert _review_gate.ACCEPT_REFUSAL in refused


def test_an_unreadable_script_holding_the_literal_words_is_refused() -> None:
    """A nested word the split can't read was skipped, so a literal accept
    in it counted only in the text search, where a dry run elsewhere could
    cancel it. The guard can't tell what such a script runs, so the words
    alone refuse it.

    The command as a whole is refused earlier, for holding two commands, so
    the end-to-end check alone would pass with the unreadable branch gone.
    The first assertion pins that the outer split reads the text and hands
    the script on as unreadable."""
    script = "cat <<EOF\ndon't\nEOF\nwfctl arch accept rec"
    command = "wfctl arch accept x --dry-run; bash -c " + shlex.quote(script)

    within = _review_gate._commands_within(_review_gate._commands(command))
    refused, _ = _review_gate.read(command)

    assert (_review_gate._UNREADABLE_DEPTH, [script]) in within
    assert _review_gate.ACCEPT_REFUSAL in refused


@pytest.mark.parametrize("name", [
    "$'\\u0077fctl'", "$'\\U00000077fctl'", "$'wf\\u0063tl'",
])
def test_a_unicode_escape_spelling_the_name_is_refused(name: str) -> None:
    """Reading `$'…'` as the string the shell makes of it removed the `$`
    that had made an undecoded escape read as an expansion. Hex and octal
    were decoded, but `\\u` and `\\U` weren't, so the name went unseen."""
    command = f"{name} arch accept rec --agreed x"

    refused, _ = _review_gate.read(command)

    assert _review_gate.ACCEPT_REFUSAL in refused


@pytest.mark.parametrize("command", [
    "wfctl 2> arch arch accept x; echo \\",
    "wfctl 2> arch arch accept x\ncat <<EOF\nit's\nEOF",
    "script -q /dev/null wfctl 2> arch arch accept x\ncat <<EOF\nit's\nEOF",
    "wfctl arch >> accept accept x; echo \\",
])
def test_a_redirection_target_spelling_the_next_word_is_refused(command: str) -> None:
    """Security run 016 on #792 found the text search took a redirection's
    target, a file named `arch`, as the `arch` word, so it counted no hit.
    When the split couldn't read the text either, such as with a trailing
    backslash, the accept went through, under `script` with a terminal."""
    refused, _ = _review_gate.read(command)

    assert _review_gate.ACCEPT_REFUSAL in refused


@pytest.mark.parametrize("runner", ["", "uv run ", "script -q /dev/null "])
@pytest.mark.parametrize("redirects", [
    "> /tmp/o 2> /tmp/research", ">/tmp/o 2>/tmp/research", "-- > /tmp/x.arch",
])
def test_unreadable_text_holding_the_words_in_order_is_refused(
    runner: str, redirects: str,
) -> None:
    """Security run 017 on #792 found the text search stopped at `arch`
    inside a redirection target such as `/tmp/research`, so it counted no
    hit. When the split couldn't read the text either, nothing else did,
    and the accept went through. Text the split can't read is now refused
    whenever the three words appear in order as words."""
    command = (
        f"{runner}wfctl {redirects} arch accept rec\ncat <<EOF\nit's\nEOF"
    )

    refused, _ = _review_gate.read(command)

    assert _review_gate.ACCEPT_REFUSAL in refused


@pytest.mark.parametrize("definition", [
    'wfctl() { script -q /dev/null wfctl -- "${@:1:3}"; }; ',
    "function wfctl { command wfctl -- \"${@:1:3}\"; }; ",
    "function g wfctl { script -q /dev/null command wfctl -- \"${@:1:3}\"; }; ",
    "alias wfctl='script -q /dev/null wfctl --'; ",
    "alias -g wfctl='script -q /dev/null wfctl --'; ",
    "alias -- wfctl='script -q /dev/null wfctl --'; ",
    "functions[wfctl]='script -q /dev/null command wfctl ${@:#--dry-run}'; ",
    "TRAPDEBUG(){ script -q /dev/null ${=ZSH_DEBUG_CMD% --dry-run}; }\n",
    "trap 'script -q /dev/null ${BASH_COMMAND% --dry-run}' DEBUG; ",
    "functions[wfctl]='script -q /dev/null command wfctl ${@:#--dry-run}' ",
])
def test_a_dry_run_after_another_command_is_refused(definition: str) -> None:
    """Security run 017 and code run 004 on #792 found an earlier command
    can put code between the typed words and wfctl, such as a function, an
    alias, zsh's `functions[wfctl]=`, or a `DEBUG` trap, and drop
    `--dry-run`. Each list of those forms missed one, so a dry run counts
    only as the whole command line, with no assignment in front of it."""
    command = definition + "wfctl arch accept x --dry-run"

    refused, _ = _review_gate.read(command)

    assert _review_gate.ACCEPT_REFUSAL in refused


def test_a_script_nested_past_the_split_depth_is_refused() -> None:
    """A word still holding whitespace at the deepest level the split reads
    is a script the guard can't see into, so the literal words in it refuse
    the command, the same as text the split can't read.

    The command as a whole is refused earlier, for running a shell, so the
    end-to-end check alone would pass with the depth limit gone. The first
    assertion pins that the outer split reads the text and hands the
    innermost script on as unreadable."""
    innermost = "wfctl 2> arch arch accept x"
    command = innermost
    for _ in range(4):
        command = "bash -c " + shlex.quote(command)

    within = _review_gate._commands_within(_review_gate._commands(command))
    refused, _ = _review_gate.read(command)

    assert (_review_gate._UNREADABLE_DEPTH, [innermost]) in within
    assert _review_gate.ACCEPT_REFUSAL in refused


@pytest.mark.parametrize("command", [
    "echo wfctl >" + "a" * 20000 + " search",
    "echo wfctl " + "a>" * 10000 + " search",
    "echo search # " + "a" * 20000,
])
def test_one_long_word_is_read_in_linear_time(command: str) -> None:
    """Code run 002 on #792 found a single long word made two patterns
    quadratic: the gap after a redirection rescanned the word it had just
    taken, and the comment search started its leading `\\S*` at every
    character. A heredoc writing a 15 KB page took 5.5 seconds."""
    started = time.monotonic()

    _review_gate.read(command)

    assert time.monotonic() - started < 2


def test_many_names_with_no_accept_are_read_in_linear_time() -> None:
    """CodeRabbit on #797 found each name rebuilt the text before it to ask
    whether a substitution was open, so a long command naming wfctl many
    times took quadratic time in a hook that runs before every command."""
    command = "true " + "wfctl " * 20000 + "arch"
    started = time.monotonic()

    refused, _ = _review_gate.read(command)

    assert time.monotonic() - started < 2
    assert _review_gate.ACCEPT_REFUSAL not in refused
