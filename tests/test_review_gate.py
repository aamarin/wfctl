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
import subprocess
import sys
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

import pytest

from wfctl import _hook, _review, _review_config, _review_gate
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
        """Run every review group, or only `only`, to completion on `branch`."""
        agent_dir = resolve_agent_dir(root, branch)
        for group in _review_config.load(root)[0]:
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

    code, err = guard("gh pr create --fill", repos.feature)

    assert code == 2
    assert "✗ the review check failed: can't read the review config: wfctl.json" in err


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
    quiet default."""
    (repos.feature / "wfctl.json").write_text(json.dumps({"review": {"rounds": -1}}))

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
