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
import os
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


def test_a_slash_free_command_can_never_be_refused() -> None:
    """`_hook` skips this function entirely for a command with no "/" in it.

    That early-out is what removes two git subprocesses from the majority of
    Bash calls (#135), and it is sound only while every refusal needs a `/` —
    `_ABS_PATH` is anchored on one. The cases above all contain a `/`, so none
    of them pins it: this is the one that fails if `refusal()` ever learns to
    judge a relative path without the early-out being revisited.
    """
    for command in ("rm -rf ..", "ls", "uv run pytest", "cd ..", "make clean"):
        assert not refuses(command), command


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


# The spec root as pfms lays it out: `specs-trunk` checked out beside the main
# checkout, so `git worktree list` names it and every feature worktree's
# `FEATURE_DIR` lands inside it.
STORE = "/Users/dev/project-specs"
ROOTS_WITH_STORE = [*ROOTS, STORE]


def refuses_with_store(command: str) -> bool:
    return _guard.refusal(command, HERE, ROOTS_WITH_STORE, shared=[STORE]) is not None


@pytest.mark.parametrize("command", [
    f"mkdir -p {STORE}/129-cross-worktree-guard/reviews",
    f"cat > {STORE}/129-cross-worktree-guard/reviews/a.md <<'EOF'\nx\nEOF",
    f"echo done > {STORE}/129-cross-worktree-guard/reviews/a.md",
    f'mkdir -p "{STORE}/129-cross-worktree-guard/reviews"',
])
def test_a_write_under_the_spec_root_is_allowed(command: str) -> None:
    """`feature-paths` hands every feature worktree a `FEATURE_DIR` here.

    Refusing it meant one wfctl component told the agent where to write and the
    other blocked the write, pointing at a handoff to a session the store never
    has. Each row is a form `fanning-out-code-review` or #359 reaches for.
    """
    assert not refuses_with_store(command)


def test_the_spec_root_is_a_peer_when_nobody_names_it() -> None:
    """The exemption comes from the caller, never from the root's shape.

    Without it the store is one more worktree, which is exactly how a repo with
    no spec root configured has always behaved.
    """
    command = f"mkdir -p {STORE}/129-cross-worktree-guard/reviews"
    assert _guard.refusal(command, HERE, ROOTS_WITH_STORE) is not None


def test_naming_the_spec_root_leaves_a_peer_refusal_unchanged() -> None:
    """A peer feature worktree is the boundary the guard exists for.

    Byte-identical rather than merely refused, so the exemption cannot quietly
    reword the handoff a peer still needs.
    """
    command = f"uv run pytest {OTHER}/tests"
    before = _guard.refusal(command, HERE, ROOTS)
    assert before is not None
    assert _guard.refusal(command, HERE, ROOTS_WITH_STORE, shared=[STORE]) == before


def test_a_read_under_the_spec_root_is_still_allowed() -> None:
    """The exemption only ever removes refusals, and reads had none to remove."""
    assert not refuses_with_store(f"cat {STORE}/129-cross-worktree-guard/spec.md")
    assert not refuses_with_store(f"git -C {STORE} log --oneline")


@pytest.mark.parametrize("slot", ["spec", "state"])
@pytest.mark.parametrize("spec_root", [MAIN, f"{MAIN}/wt", "/Users/dev", f"{MAIN}/wt/.."])
def test_a_shared_root_covering_a_worktree_is_not_honoured(spec_root: str, slot: str) -> None:
    """A shared root declared too broadly cannot open the worktrees it covers.

    `"spec_root": "."` in the main checkout's manifest names the main checkout,
    and `"wt"` names the directory every feature worktree sits in. Honoured,
    either would turn `rm -rf` on a peer into an allowed write, so the guard
    refuses exactly as it would with no spec root at all. `WFCTL_STATE_DIR` set
    to the main checkout is the same mistake from the state side, and the
    second slot pins that the rule is applied to every root, not the first.
    """
    shared = [spec_root, None] if slot == "spec" else [None, spec_root]
    for command in (f"rm -rf {MAIN}/wfctl", f"rm -rf {OTHER}/src", f"rm -rf {MAIN}/wt"):
        before = _guard.refusal(command, HERE, ROOTS)
        assert before is not None, command
        assert _guard.refusal(command, HERE, ROOTS, shared=shared) == before, command


def test_the_main_checkout_is_never_the_spec_root() -> None:
    """With worktrees kept beside the checkout rather than inside it, the main
    checkout holds no other root, so only its place in the list says it is code.
    `git worktree list` prints the main worktree first."""
    main, here = "/Users/dev/project", "/Users/dev/project-wt/129-cross-worktree-guard"
    roots = [main, here]
    command = f"rm -rf {main}/wfctl"
    assert _guard.refusal(command, here, roots, shared=[main]) == _guard.refusal(
        command, here, roots
    )


@pytest.mark.parametrize("store, roots", [
    (STORE, ROOTS_WITH_STORE),
    (f"{MAIN}/specs", ROOTS),
], ids=["store-beside-checkout", "store-inside-checkout"])
@pytest.mark.parametrize("command", [
    "rm -rf {s}/../project/wfctl",
    "rm -rf {s}/..",
    "rm -rf {s}/../",
    "rm -rf {s}/x/../..",
    "rm -rf {s}/..:",
    "mv {s}/.. /tmp/gone",
])
def test_a_path_that_climbs_out_of_a_shared_root_is_not_exempt(
    command: str, store: str, roots: list[str],
) -> None:
    """`..` is text to this module, so the prefix alone would exempt it.

    A trailing `..` was the spelling that got through: the strip that drops a
    sentence's closing `.` turned `<store>/..` into the store itself, and
    `rm -rf <main>/specs/..` deleted the main checkout and every worktree in it.
    A climbing path is exempt from nothing, so its refusal is the one it gets
    with no shared root named at all.
    """
    command = command.format(s=store)
    before = _guard.refusal(command, HERE, roots)
    assert before is not None
    assert _guard.refusal(command, HERE, roots, shared=[store]) == before


@pytest.mark.parametrize("store, roots", [
    (STORE, ROOTS_WITH_STORE),
    (f"{MAIN}/specs", ROOTS),
], ids=["store-beside-checkout", "store-inside-checkout"])
@pytest.mark.parametrize("command", [
    "rm -rf {s}/{{x,..}}/project/wfctl",
    "rm -rf {s}/'..'/project/wfctl",
    'rm -rf {s}/".."/project/wfctl',
    "rm -rf {s}/\\../project/wfctl",
    "rm -rf {s}/$UP/project/wfctl",
    'rm -rf "{s}/a b/../../project/wfctl"',
    "rm -rf {s}/a\\ b/../../project/wfctl",
])
def test_a_path_the_shell_rewrites_is_not_exempt(
    command: str, store: str, roots: list[str],
) -> None:
    """The shell sees a `..` the text hides. `_ABS_PATH` stops at a quote, so
    `<store>/'..'/x` arrived as `<store>/` and was exempt, and a brace or a
    variable can expand to anywhere. Each row is a write above the store that
    was refused before the exemption existed and has to stay refused."""
    command = command.format(s=store)
    before = _guard.refusal(command, HERE, roots)
    assert before is not None
    assert _guard.refusal(command, HERE, roots, shared=[store]) == before


@pytest.mark.parametrize("command", [
    f"rm -rf {HERE}/..",
    f"rm -rf {HERE}/../",
    f"rm -rf {HERE}/x/../..",
    f"rm -rf {HERE}/../105-mypy-cold-venv/src",
    f"rm -rf {HERE}/'..'/105-mypy-cold-venv/src",
    f"mv {HERE}/.. /tmp/gone",
])
def test_a_path_that_climbs_out_of_this_worktree_is_judged_where_it_lands(command: str) -> None:
    """`<here>/..` starts with this session's own root, and the strip that drops
    a sentence's closing `.` turned it into that root, so `rm -rf <here>/..`
    deleted the directory holding every feature worktree. A path that names
    this worktree and lands in another one is a write to the other one."""
    assert _guard.refusal(command, HERE, ROOTS) is not None


def test_a_path_that_climbs_within_this_worktree_is_still_its_own() -> None:
    """Resolving `..` adds a refusal only where the path lands elsewhere."""
    assert _guard.refusal(f"rm -rf {HERE}/x/../y", HERE, ROOTS) is None
    assert _guard.refusal(f"cat {HERE}/../105-mypy-cold-venv/README.md", HERE, ROOTS) is None


def test_a_symlink_in_the_store_exempts_nothing(tmp_path: Path) -> None:
    """A link in the store pointing at a peer is a write to the peer. The text
    starts with the store, so only the filesystem can say where it lands, and a
    glob reaching the link is the same write: `realpath` reads the `*` as a name
    and lands in the store, while the shell expands it to the link."""
    main, store, peer = (str(tmp_path.resolve() / n) for n in ("p", "p-specs", "p/wt/b"))
    here = f"{main}/wt/a"
    for d in (here, peer, store):
        os.makedirs(d)
    os.symlink(peer, f"{store}/link")
    roots = [main, here, store, peer]

    for command in (
        f"rm -rf {store}/link/src",
        f"rm -rf {store}/link*/src",
        f"rm -rf {store}/l?nk/src",
        f"rm -rf {store}/[l]ink/src",
    ):
        before = _guard.refusal(command, here, roots)
        assert before is not None, command
        assert _guard.refusal(command, here, roots, shared=[store]) == before, command
    assert _guard.refusal(f"rm -rf {store}/a/src", here, roots, shared=[store]) is None


def test_a_shared_root_is_compared_where_it_resolves(tmp_path: Path) -> None:
    """A root declared as `<main>/wt/../specs`, or through a symlink, names the
    store, so a write to the store's own spelling is exempt. A path is compared
    resolved, and a root left as declared would match none of them. And a root
    declared as a symlink to the main checkout is the main checkout, which is
    never honoured."""
    assert not _guard.refusal(
        f"mkdir -p {MAIN}/specs/129", HERE, ROOTS, shared=[f"{MAIN}/wt/../specs"],
    )

    main, store = (str(tmp_path.resolve() / n) for n in ("p", "p-specs"))
    here = f"{main}/wt/a"
    for d in (here, store):
        os.makedirs(d)
    os.symlink(store, tmp_path / "store-link")
    os.symlink(main, tmp_path / "main-link")
    roots = [main, here, store]
    assert not _guard.refusal(
        f"mkdir -p {store}/129", here, roots, shared=[str(tmp_path / "store-link")],
    )

    command = f"rm -rf {main}/src"
    before = _guard.refusal(command, here, roots)
    assert before is not None
    assert _guard.refusal(command, here, roots, shared=[str(tmp_path / "main-link")]) == before


def test_a_path_that_climbs_back_into_a_shared_root_is_exempt() -> None:
    """Normalising cuts both ways: a `..` that lands inside the store is a
    write to the store."""
    assert not refuses_with_store(f"mkdir -p {STORE}/a/../129-cross-worktree-guard")
    assert not refuses_with_store(f"touch {STORE}/./129/a.md")


@pytest.mark.parametrize("command", [
    f"cd {STORE}",
    f"pushd {STORE}/129-cross-worktree-guard",
    f"cd {STORE}/129-cross-worktree-guard && rm -rf ../../project/wfctl",
    f"builtin cd {STORE} && rm -rf ../project/wfctl",
    f"command cd {STORE} && rm -rf ../project/wfctl",
    f"X=1 cd {STORE} && rm -rf ../project/wfctl",
    f'bash -c "cd {STORE} && rm -rf ../project/wfctl"',
])
def test_changing_directory_into_a_shared_root_is_still_refused(command: str) -> None:
    """The hook reads `here` from the session's working directory. After a `cd`
    into the store, the store is this session's own worktree as far as the
    guard can tell, and the real one is refused with a handoff to itself. The
    `cd` refusal was also all that stopped the relative `rm` in the later rows,
    and a wrapper or an assignment in front of the `cd` hid it from that."""
    before = _guard.refusal(command, HERE, ROOTS_WITH_STORE)
    assert before is not None
    assert _guard.refusal(command, HERE, ROOTS_WITH_STORE, shared=[STORE]) == before


@pytest.mark.parametrize("store, roots", [
    (STORE, ROOTS_WITH_STORE),
    (f"{MAIN}/specs", ROOTS),
], ids=["store-beside-checkout", "store-inside-checkout"])
@pytest.mark.parametrize("command", [
    # A separator or a substitution inside the path, which the quote-blind
    # split cut in two so that each half passed on its own.
    "rm -rf {s}/$(echo ..)/project/wfctl",
    "rm -rf {s}/`echo ..`/project/wfctl",
    'rm -rf "{s}/$(echo ..)/project/wfctl"',
    "rm -rf {s}/$(echo ..)/project/wt/105-mypy-cold-venv/src",
    'rm -rf "{s}/a;b/../../project/wfctl"',
    'rm -rf "{s}/a|b/../../project/wfctl"',
    'rm -rf "{s}/a\nb/../../project/wfctl"',
    "rm -rf {s}/a\\;/../../project/wfctl",
    'mkdir -p "{s}/a;" && rm -rf "{s}/a;/../../project/src"',
    "rm -rf $P{s}/x",
    "cat > {s}/x <<EOF\n$(rm -rf /Users/dev/project/wfctl)\nEOF",
    # A verb the text does not show, or one that changes directory.
    "G=git; $G -C {s} reset --hard HEAD",
    "X=cd; $X {s} && rm -rf ../project/wfctl",
    "env /usr/bin/git -C {s} reset --hard HEAD",
    "env -C {s} rm -rf ../project/src",
    "make -C {s} -f ../project/Makefile clean",
    "uv --directory {s} sync",
    "find {s} -maxdepth 0 -execdir rm -rf project/src ;",
    "cd .. && rm -rf wt/105-mypy-cold-venv/src > {s}/log",
    "rm -rf {s}/x ../project/wt/105-mypy-cold-venv/src",
    "mkdir -p {s}/x && rm -rf ../105-mypy-cold-venv/src",
    "mkdir -p {s}/x && echo x > ../105-mypy-cold-venv/evil.py",
    # A comment the shell skips and this parser would not.
    "mkdir -p {s}/x # <<':'\nrm -rf /Users/dev/project/wt/105-mypy-cold-venv/src\n:",
    # git pointed somewhere the path does not name, or changing shared state.
    'git -C {s} --git-dir="$GIT_DIR" commit -m x',
    "git -C {s} --work-tree=../project checkout -- x",
    "git -C {s} -c core.worktree=/Users/dev/project commit -m x",
    "git -C {s} -c core.hooksPath=/tmp/h commit -m x",
    "git --git-dir={s}/.git commit -m x",
    "git -C {s} worktree remove --force ../project/wt/105-mypy-cold-venv",
    "git -C {s} config core.hooksPath /tmp/h",
    "git -C {s} update-ref -d HEAD",
    # A repository, or a link, made inside the store.
    "mkdir -p {s}/.git",
    'echo "gitdir: /Users/dev/project/.git" > {s}/.git',
    "printf x > {s}/.GIT",
    "ln -s ../project/src {s}/l && echo x > {s}/l/evil.py",
    "cp -s /Users/dev/project/src {s}/l",
])
def test_a_construct_the_exemption_cannot_follow_is_judged_as_if_nothing_were_shared(
    command: str, store: str, roots: list[str],
) -> None:
    """Every row got through an exemption that trusted all but the known tricks,
    found across four review rounds. The two `$(echo ..)` rows reach the main
    checkout's source and a peer worktree, and need nothing on disk. Each was
    refused before the exemption existed and has to stay refused, with the
    same message, so none of them can quietly reword the handoff either."""
    command = command.format(s=store)
    before = _guard.refusal(command, HERE, roots)
    assert before is not None
    assert _guard.refusal(command, HERE, roots, shared=[store]) == before
    assert _guard.refusal(command, HERE, roots, shared=[store], committable=[store]) == before


@pytest.mark.parametrize("command", [
    f"bash {STORE}/x.sh",
    f"python {STORE}/evil.py",
    f"sh < {STORE}/x.sh",
    f"uv run pytest > {STORE}/129/out.txt",
])
def test_running_from_a_shared_root_is_not_writing_to_it(command: str) -> None:
    """The store is shared between every feature worktree, so a file one writes
    there is a file another would run. The exemption is for writing, and a
    verb not on its list declines it, even where all it does with the store is
    redirect into it: `uv run pytest > <store>/out` is the cost of that."""
    before = _guard.refusal(command, HERE, ROOTS_WITH_STORE)
    assert before is not None
    assert _guard.refusal(command, HERE, ROOTS_WITH_STORE, shared=[STORE]) == before


@pytest.mark.parametrize("command", [
    f"cat > {STORE}/129/reviews/a.md <<'EOF'\nit's done; see $(x) and `y` in /Users/dev\nEOF",
    f"cat > {STORE}/129/a.md <<-'EOF'\n\tbody\n\tEOF",
    f"echo 'specs(129): a; b | c # d' > {STORE}/129/note.md",
    f"cat {OTHER}/README.md && mkdir -p {STORE}/129/reviews",
    f"cp /tmp/h.md {STORE}/129/ 2>&1 && git -C {STORE} status --short",
])
def test_the_forms_a_spec_write_takes_stay_exempt(command: str) -> None:
    """Parsing quotes properly is what lets the allowlist stay strict without
    refusing the ordinary forms. A quoted here-document's body is data, so its
    apostrophe and `$(` are the shell's business, not the guard's, and a
    separator or a `#` inside quotes is part of the text."""
    assert not refuses_with_store(command)


def test_a_relative_shared_root_exempts_nothing(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    """`WFCTL_SPEC_DIR` is read raw, and a relative value resolves against the
    hook process's directory rather than the session's, so the store it would
    name is a guess. Here the guess is right, and it is still not honoured."""
    monkeypatch.chdir(tmp_path)
    main, store = str(tmp_path / "p"), str(tmp_path / "p-specs")
    here = f"{main}/wt/a"
    roots = [main, here, store]
    command = f"mkdir -p {store}/129"
    assert _guard.refusal(command, here, roots, shared=[store]) is None
    assert _guard.refusal(command, here, roots, shared=["p-specs"]) is not None
    assert _guard.refusal(command, here, roots, shared=["~/p-specs"]) is not None


def test_a_spec_root_inside_the_main_checkout_is_exempt() -> None:
    """A spec root need not be a worktree of its own.

    Declared as `specs/` in the main checkout's manifest, it is an ordinary
    gitignored directory there, so the main checkout owns it and every write from
    a feature worktree used to read as a write to the main checkout.
    """
    shared = f"{MAIN}/specs"
    command = f"mkdir -p {shared}/129-cross-worktree-guard/reviews"
    assert _guard.refusal(command, HERE, ROOTS) is not None
    assert _guard.refusal(command, HERE, ROOTS, shared=[shared]) is None
    assert _guard.refusal(f"rm -rf {MAIN}/wfctl", HERE, ROOTS, shared=[shared]) is not None


@pytest.mark.parametrize("command", [
    "git -C {s} add 129",
    "git -C {s} add {s}/129/reviews/a.md",
    "git -C {s} commit -m 'specs(129): reviews'",
    "git -C {s} add 129 && git -C {s} commit -m 'specs(129): reviews'",
    "git -C {s} commit -m x && git -C {s} log --oneline -1",
])
def test_a_commit_into_a_root_that_takes_commits_is_exempt(command: str) -> None:
    """Committing a feature's specs is the step #359 adds, and it runs from the
    feature worktree. Once the caller has found that a commit there lands on a
    branch of the store's own, the commit is a write to the store like any
    other."""
    command = command.format(s=STORE)
    assert _guard.refusal(command, HERE, ROOTS_WITH_STORE) is not None
    assert _guard.refusal(
        command, HERE, ROOTS_WITH_STORE, shared=[STORE], committable=[STORE],
    ) is None


@pytest.mark.parametrize("store, roots", [
    (STORE, ROOTS_WITH_STORE),
    (f"{MAIN}/specs", ROOTS),
], ids=["store-beside-checkout", "store-inside-checkout"])
def test_a_commit_into_a_root_git_has_not_vouched_for_is_refused(
    store: str, roots: list[str],
) -> None:
    """Which branch a commit lands on is decided by files inside the store, so
    the text alone never earns the exemption. With the store a plain
    `<main>/specs` the commit lands on the main checkout's branch, and the
    refusal says so instead of offering a handoff to a session the store does
    not have."""
    message = _guard.refusal(f"git -C {store} commit -m x", HERE, roots, shared=[store])
    assert message is not None
    assert "would not land on a branch of its own" in message
    assert "workmux send" not in message


@pytest.mark.parametrize("command", [
    "git -C {s}/129 commit -m x",
    "git -C {s} -C /Users/dev/project commit -m x",
    "git --work-tree {s} commit -m x",
    "git -C {s} reset --hard HEAD",
    "git -C {s} push origin HEAD",
    "command git -C {s} commit -m x",
    "/usr/bin/git -C {s} commit -m x",
    "GIT_DIR=/Users/dev/project/.git git -C {s} commit -m x",
    'git -C {s} commit -m "$(date)"',
    "mkdir -p {s}/129 && git -C {s} add 129",
    "cp -r /tmp/x/. {s}/ && git -C {s} add 129",
    "git -C {s} add 129 && rm -rf {s}/129",
    "git -C {s} commit -m x > /Users/dev/project/wfctl/log",
    "git -C {s} log -1 > {s}/l && git -C {s} commit -m x",
])
def test_a_commit_is_exempt_only_written_plainly_and_alone(command: str) -> None:
    """The caller asked git about the store as it stood before the command ran.
    A write in the same command could replace the store's `.git` first, as the
    `cp -r /tmp/x/.` row does without ever naming it, so nothing but reads may
    sit beside a commit. A `-C` below the root could hold a `.git` of its own
    the caller never asked about, and every other spelling moves the repository
    or runs something."""
    command = command.format(s=STORE)
    assert _guard.refusal(
        command, HERE, ROOTS_WITH_STORE, shared=[STORE], committable=[STORE],
    ) is not None


def test_a_peer_write_beside_a_commit_is_reported_as_the_peer_write() -> None:
    """A refused command can carry a commit and a peer write at once, and the
    peer write is the one a handoff fixes. Reporting the commit instead tells
    the agent to respell a command whose real problem it never hears about."""
    command = f"git -C {STORE} commit -m x && rm -rf {OTHER}/src"
    message = _guard.refusal(
        command, HERE, ROOTS_WITH_STORE, shared=[STORE], committable=[STORE],
    )
    assert message is not None
    assert "workmux send 105-mypy-cold-venv" in message


def test_a_commit_into_a_store_outside_every_worktree_is_still_judged() -> None:
    """A spec repository of its own sits outside every worktree, so no owner
    makes a commit there a trespass. Its `.git` can still be replaced to name
    the main checkout's, and then only the caller's answer says so."""
    store = "/Users/dev/elsewhere-specs"
    command = f"git -C {store} commit -m x"
    assert _guard.refusal(command, HERE, ROOTS, shared=[store], committable=[store]) is None
    message = _guard.refusal(command, HERE, ROOTS, shared=[store])
    assert message is not None
    assert "would not land on a branch of its own" in message


def test_a_root_that_is_not_shared_takes_no_commits() -> None:
    """`committable` narrows the exemption and never widens it: a peer the
    caller wrongly vouched for is still a peer."""
    command = f"git -C {OTHER} commit -m x"
    before = _guard.refusal(command, HERE, ROOTS)
    assert before is not None
    assert _guard.refusal(command, HERE, ROOTS, shared=[STORE], committable=[OTHER]) == before


def _store_layout(tmp_path: Path) -> tuple[Path, Path, Path]:
    """The main checkout, a spec store beside it, and a feature worktree."""
    main = git_repo(tmp_path / "project")
    store = tmp_path / "project-specs"
    feature = main / "wt" / "129-cross-worktree-guard"
    for branch, path in (("specs-trunk", store), ("129-cross-worktree-guard", feature)):
        subprocess.run(
            ["git", "-C", str(main), "worktree", "add", "-b", branch, str(path)],
            check=True, capture_output=True,
        )
    return main, store, feature


def _hook(cwd: Path, command: str) -> Result:
    payload = json.dumps({"cwd": str(cwd), "tool_input": {"command": command}})
    return runner.invoke(app, ["hook", "worktree-guard"], input=payload)


def test_the_hook_allows_the_spec_root_the_main_checkout_declares(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The pfms reproduction, end to end against `git worktree list`.

    The declaration sits in the main checkout's manifest, which is the only place
    a fresh feature worktree can find it, so this also holds the hook to the same
    resolution `feature-paths` uses rather than a copy of it.
    """
    monkeypatch.delenv("WFCTL_SPEC_DIR", raising=False)
    main, store, feature = _store_layout(tmp_path)
    (main / ".wf-skills-manifest.json").write_text(json.dumps({"spec_root": str(store)}))

    assert _hook(feature, f"mkdir -p {store}/129-cross-worktree-guard/reviews").exit_code == 0
    assert _hook(feature, f"git -C {store} log --oneline").exit_code == 0
    (store / "129.md").write_text("x\n")
    assert _hook(feature, f"git -C {store} add 129.md").exit_code == 0
    assert _hook(feature, f"git -C {store} commit -m x").exit_code == 0

    peer = _hook(feature, f"rm -rf {main}/README.md")
    assert peer.exit_code == 2
    assert "workmux send project " in (peer.stderr or peer.output)


def test_the_hook_honours_the_spec_dir_override(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    """`WFCTL_SPEC_DIR` moves `FEATURE_DIR`, so it has to move the exemption too."""
    _, store, feature = _store_layout(tmp_path)
    monkeypatch.setenv("WFCTL_SPEC_DIR", str(store))

    assert _hook(feature, f"mkdir -p {store}/129-cross-worktree-guard").exit_code == 0


def test_the_hook_refuses_the_store_when_no_spec_root_is_declared(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    """With nothing declared the spec root is `<worktree>/specs`, and the store
    beside the checkout is a peer like any other: the behaviour before #365."""
    monkeypatch.delenv("WFCTL_SPEC_DIR", raising=False)
    _, store, feature = _store_layout(tmp_path)

    refused = _hook(feature, f"mkdir -p {store}/129-cross-worktree-guard")
    assert refused.exit_code == 2
    assert "workmux send project-specs" in (refused.stderr or refused.output)


def test_an_unreadable_manifest_refuses_rather_than_raising(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    """`spec_root` raises on a malformed manifest, which is right for a command
    and wrong for a hook on every Bash call. Unresolvable means no exemption, so
    the guard falls back to what it did before rather than to a traceback."""
    monkeypatch.delenv("WFCTL_SPEC_DIR", raising=False)
    main, store, feature = _store_layout(tmp_path)
    (main / ".wf-skills-manifest.json").write_text("{not json")

    refused = _hook(feature, f"mkdir -p {store}/129-cross-worktree-guard")
    assert refused.exit_code == 2
    assert "workmux send project-specs" in (refused.stderr or refused.output)


def test_the_spec_root_and_the_state_root_are_exempt_together() -> None:
    """Both are handed to the guard at once, and one that could not be resolved
    must not cost the other its exemption."""
    state = f"{MAIN}/.state/wfctl/project"
    spec = f"mkdir -p {STORE}/129-cross-worktree-guard/reviews"
    handoff = f"cp /tmp/h.md {state}/130-child/session-summary.md"

    def refused(command: str, shared: list[str | None]) -> bool:
        return _guard.refusal(command, HERE, ROOTS_WITH_STORE, shared=shared) is not None

    assert refused(handoff, [])
    assert not refused(spec, [STORE, state])
    assert not refused(handoff, [STORE, state])
    assert not refused(spec, [STORE, None])
    assert not refused(handoff, [None, state])
    assert refused(f"rm -rf {OTHER}/src", [STORE, state])


def test_the_hook_allows_a_handoff_into_a_state_root_inside_the_main_checkout(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    """`XDG_STATE_HOME` can put the state root inside a repo, and inside the main
    checkout the main checkout owns it, so a feature worktree's handoff read as a
    write to the main checkout. The child branch's dir is the case that needs the
    whole project exempt: a handoff writes it before the branch exists."""
    monkeypatch.delenv("WFCTL_SPEC_DIR", raising=False)
    monkeypatch.delenv("WFCTL_STATE_DIR", raising=False)
    main, _, feature = _store_layout(tmp_path)
    monkeypatch.setenv("XDG_STATE_HOME", str(main / ".state"))
    child = main / ".state" / "wfctl" / "project" / "130-child"

    assert _hook(feature, f"mkdir -p {child}").exit_code == 0
    assert _hook(feature, f"cp /tmp/h.md {child}/session-summary.md").exit_code == 0
    assert _hook(feature, f"rm -rf {main}/README.md").exit_code == 2


def test_the_hook_honours_the_state_dir_override(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    """`WFCTL_STATE_DIR` names one state dir, so that dir is exempt and its
    neighbours in the same checkout are not."""
    monkeypatch.delenv("WFCTL_SPEC_DIR", raising=False)
    main, _, feature = _store_layout(tmp_path)
    monkeypatch.setenv("WFCTL_STATE_DIR", str(main / ".state"))

    assert _hook(feature, f"touch {main}/.state/events.jsonl").exit_code == 0
    assert _hook(feature, f"touch {main}/.other/events.jsonl").exit_code == 2


def test_the_hook_refuses_a_commit_once_the_store_points_at_the_main_checkout(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A store whose `.git` file was replaced to name the main checkout's
    repository commits onto the main checkout's branch, though every word of
    the command still names the store. Only git can say so."""
    monkeypatch.delenv("WFCTL_SPEC_DIR", raising=False)
    main, store, feature = _store_layout(tmp_path)
    (main / ".wf-skills-manifest.json").write_text(json.dumps({"spec_root": str(store)}))
    assert _hook(feature, f"git -C {store} commit -m x").exit_code == 0

    (store / ".git").write_text(f"gitdir: {main / '.git'}\n")
    refused = _hook(feature, f"git -C {store} commit -m x")
    assert refused.exit_code == 2
    assert "would not land on a branch of its own" in (refused.stderr or refused.output)


def test_the_hook_refuses_a_commit_into_a_plain_spec_folder_in_the_main_checkout(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A `specs/` with no repository of its own is part of the main checkout, so
    a commit there lands on the main checkout's branch. Writing there stays
    allowed."""
    monkeypatch.setenv("WFCTL_SPEC_DIR", str(tmp_path / "project" / "specs"))
    main, _, feature = _store_layout(tmp_path)
    (main / "specs").mkdir()

    assert _hook(feature, f"mkdir -p {main}/specs/129").exit_code == 0
    refused = _hook(feature, f"git -C {main}/specs commit -m x")
    assert refused.exit_code == 2
    assert "would not land on a branch of its own" in (refused.stderr or refused.output)


def test_the_hook_allows_a_commit_into_a_spec_repository_nested_in_the_main_checkout(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A spec root that is a repository of its own takes its own commits,
    wherever it sits, so nesting it inside the main checkout costs nothing."""
    main, _, feature = _store_layout(tmp_path)
    specs = git_repo(main / "specs")
    monkeypatch.setenv("WFCTL_SPEC_DIR", str(specs))
    (specs / "129.md").write_text("x\n")

    assert _hook(feature, f"git -C {specs} add 129.md").exit_code == 0
    assert _hook(feature, f"git -C {specs} commit -m x").exit_code == 0


def test_the_hook_refuses_a_commit_into_a_store_with_a_detached_head(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A commit on a detached head lands on no branch, so it is not on the
    store's own branch either."""
    main, store, feature = _store_layout(tmp_path)
    monkeypatch.setenv("WFCTL_SPEC_DIR", str(store))
    subprocess.run(["git", "-C", str(store), "checkout", "--detach"], check=True, capture_output=True)

    assert _hook(feature, f"git -C {store} commit -m x").exit_code == 2


def test_the_hook_refuses_a_commit_once_the_store_points_at_a_peer(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A `.git` naming a feature worktree's admin dir commits onto that
    feature's branch, which the feature worktree has checked out."""
    main, store, feature = _store_layout(tmp_path)
    monkeypatch.setenv("WFCTL_SPEC_DIR", str(store))
    admin = main / ".git" / "worktrees" / feature.name
    (store / ".git").write_text(f"gitdir: {admin}\n")

    assert _hook(feature, f"git -C {store} commit -m x").exit_code == 2


def test_the_hook_never_lets_the_state_root_take_commits(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Nothing commits handoffs. A state root inside a repository of its own,
    such as a dotfiles checkout over `~/.local/state`, would otherwise pass the
    same check a spec repository passes."""
    monkeypatch.delenv("WFCTL_SPEC_DIR", raising=False)
    monkeypatch.delenv("WFCTL_STATE_DIR", raising=False)
    main, _, feature = _store_layout(tmp_path)
    monkeypatch.setenv("XDG_STATE_HOME", str(main / ".state"))
    state = git_repo(main / ".state" / "wfctl" / "project")

    assert _hook(feature, f"touch {state}/129.md").exit_code == 0
    assert _hook(feature, f"git -C {state} commit -m x").exit_code == 2
