"""The worktree guard asks before a lone git command in the spec root (#882).

`docs/architecture/guard-asks-in-spec-root.md` lists the forms the guard must
keep refusing, the ones it gives up to the prompt, and the ones it must let
through. These tests read the lists from the record and run each form through
the hook against a real layout, so a form added there is tested with no change
here, and the hook output Claude Code reads is what gets checked.

pfms ran a wrapper script that turned the guard's refusal into an `ask`. The
wrapper read as a missing guard to `install-skills` and `doctor`, which asked to
add the guard on every `wm add`. These tests hold the guard to the wrapper's
behavior, minus the parts the record tightens: auto mode and a host that can't
ask get the refusal.
"""
from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path

import pytest
from typer.testing import CliRunner, Result

from tests.conftest import git_repo
from wfctl.cli import app

runner = CliRunner()

_RECORD = (
    Path(__file__).resolve().parent.parent
    / "docs" / "architecture" / "guard-asks-in-spec-root.md"
)


def _forms(part: str) -> list[str]:
    """The form in each numbered item under one `###` part of the record, as
    the last code span of the item, with a wrapped item joined first."""
    for section in re.split(r"^### ", _RECORD.read_text(), flags=re.M)[1:]:
        heading, _, body = section.partition("\n")
        if heading.strip() == part:
            body = re.split(r"^#", body, maxsplit=1, flags=re.M)[0]
            items = re.findall(r"^\d+\. (.*(?:\n(?!\d+\. |\s*$).*)*)", body, flags=re.M)
            return [
                re.findall(r"`([^`]+)`", re.sub(r"\n\s*", " ", item))[-1]
                for item in items
            ]
    return []


_CATCH = _forms("Must keep catching")
_ACCEPTS = _forms("Accepts")
_LET_THROUGH = _forms("Must let through")

# Items 14 - 16 of "Must keep catching" are the lone command under a host or
# mode that won't ask, and item 12 needs the spec root inside the main checkout.
_CATCH_PAYLOAD = {
    14: {"tool_name": "Bash", "permission_mode": "auto"},
    15: {"tool_name": "run_shell_command", "permission_mode": "default"},
    16: {"tool_name": "Bash"},
}
_CATCH_IN_MAIN = {12}

# Items 1 - 4 of "Must let through" ask, and the rest run with no prompt.
_LET_THROUGH_ASKS = {1, 2, 3, 4}

_PROMPTING = {"tool_name": "Bash", "permission_mode": "default"}


class _Layout:
    """The main checkout, a spec store beside it on `specs-trunk`, this
    feature's worktree, and a peer's, with the record's paths mapped onto
    them."""

    def __init__(self, tmp_path: Path, spec_root_in_main: bool = False) -> None:
        self.main = git_repo(tmp_path / "repo")
        self.store = tmp_path / "repo-specs"
        self.here = self.main / "wt" / "882-wrapped-guard-reads-missing"
        self.peer = self.main / "wt" / "peer"
        for branch, path in (
            ("specs-trunk", self.store),
            ("882-wrapped-guard-reads-missing", self.here),
            ("peer", self.peer),
        ):
            subprocess.run(
                ["git", "-C", str(self.main), "worktree", "add", "-b", branch, str(path)],
                check=True, capture_output=True,
            )
        # The remote-tracking branch a fetch from `origin` would leave, which a
        # rebase upstream has to resolve to before the guard asks.
        subprocess.run(
            ["git", "-C", str(self.store), "update-ref",
             "refs/remotes/origin/specs-trunk", "HEAD"],
            check=True, capture_output=True,
        )
        (self.store / "882").mkdir()
        (self.store / "882" / "spec.md").write_text("x\n")
        (self.main / "specs").mkdir()
        root = self.main / "specs" if spec_root_in_main else self.store
        (self.main / ".wf-skills-manifest.json").write_text(
            json.dumps({"spec_root": str(root)})
        )

    def command(self, form: str) -> str:
        # One pass, so a substituted path is never matched again. A relative
        # path climbing out of the store lands beside it, so `../repo` names
        # the main checkout and is kept relative.
        paths = {
            "../repo/": f"../{self.main.name}/",
            "/repo-specs": str(self.store),
            "/repo/wt/peer": str(self.peer),
            "/repo/": f"{self.main}/",
        }
        pattern = "|".join(re.escape(p) for p in paths)
        return re.sub(pattern, lambda m: paths[m.group()], form)

    def hook(self, form: str, extra: dict[str, str] | None = None) -> Result:
        payload = {
            "cwd": str(self.here),
            "tool_input": {"command": self.command(form)},
            **(_PROMPTING if extra is None else extra),
        }
        return runner.invoke(app, ["hook", "worktree-guard"], input=json.dumps(payload))


def _asks(result: Result) -> bool:
    if result.exit_code != 0 or not result.stdout.strip():
        return False
    out = json.loads(result.stdout)["hookSpecificOutput"]
    return out["hookEventName"] == "PreToolUse" and out["permissionDecision"] == "ask"


@pytest.fixture(autouse=True)
def _no_spec_override(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("WFCTL_SPEC_DIR", raising=False)
    monkeypatch.delenv("CLAUDE_PROJECT_DIR", raising=False)


def test_every_list_is_found() -> None:
    """A renamed heading would turn every parametrized test below into zero
    cases, which pytest reports as a pass."""
    assert len(_CATCH) == 32
    assert len(_ACCEPTS) == 3
    assert len(_LET_THROUGH) == 7


@pytest.mark.parametrize("n", range(1, len(_CATCH) + 1))
def test_every_form_the_record_must_keep_catching_is_refused(
    tmp_path: Path, n: int,
) -> None:
    """Each item is a form that would let a write nobody saw reach the
    prompt, or a host that would run the `ask` with no prompt. Exit 2 with no
    `ask` on stdout is the refusal Claude Code reads."""
    layout = _Layout(tmp_path, spec_root_in_main=n in _CATCH_IN_MAIN)
    result = layout.hook(_CATCH[n - 1], _CATCH_PAYLOAD.get(n))
    assert result.exit_code == 2, result.output
    assert not result.stdout.strip()


@pytest.mark.parametrize("n", range(1, len(_ACCEPTS) + 1))
def test_every_form_the_record_accepts_reaches_the_prompt(
    tmp_path: Path, n: int,
) -> None:
    """The record gives these up to the user's yes. If one starts being
    refused, the record and the guard disagree, and the record says which
    is right."""
    assert _asks(_Layout(tmp_path).hook(_ACCEPTS[n - 1]))


@pytest.mark.parametrize("n", range(1, len(_LET_THROUGH) + 1))
def test_every_form_the_record_lets_through_runs_or_asks(
    tmp_path: Path, n: int,
) -> None:
    """The first four are the commands the pfms wrapper turned into a prompt.
    The last three ran with no prompt before #882, and asking for them now
    would put a prompt on every spec commit."""
    result = _Layout(tmp_path).hook(_LET_THROUGH[n - 1])
    if n in _LET_THROUGH_ASKS:
        assert _asks(result), result.output
    else:
        assert result.exit_code == 0, result.output
        assert not result.stdout.strip()


def test_the_prompt_names_the_spec_root(tmp_path: Path) -> None:
    """The reason is what Claude Code shows beside the command, so it says
    why the guard didn't run it unasked."""
    layout = _Layout(tmp_path)
    out = json.loads(layout.hook("git -C /repo-specs push").stdout)["hookSpecificOutput"]
    assert str(layout.store) in out["permissionDecisionReason"]
    assert "add" in out["permissionDecisionReason"]


@pytest.mark.parametrize("extra,line,mode", [
    ({"tool_name": "Bash", "permission_mode": "auto"}, "auto mode", True),
    ({"tool_name": "Bash", "permission_mode": "bypassPermissions"}, "bypassPermissions mode", True),
    ({"tool_name": "Bash"}, "didn't say which permission mode", True),
    ({"tool_name": "run_shell_command", "permission_mode": "default"}, "can't ask", False),
])
def test_a_host_that_wont_ask_is_told_which_mode_would(
    tmp_path: Path, extra: dict[str, str], line: str, mode: bool,
) -> None:
    """The first version appended this line to the generic refusal, which still
    told the agent to hand off to a store that has no session. The user never
    learned that the default mode, or their own terminal, would run it. Bob
    Shell has no mode that asks, so its line names none."""
    result = _Layout(tmp_path).hook("git -C /repo-specs push", extra)
    assert result.exit_code == 2
    err = result.stderr or result.output
    assert line in err
    assert "own terminal" in err
    assert ("default" in err) is mode
    assert "workmux send" not in err


@pytest.mark.parametrize("form", [
    "git -C /repo-specs push origin specs-trunk",
    "git -C /repo-specs pull --rebase origin specs-trunk",
    "git -C /repo-specs reset --hard",
    "git -C /repo-specs rebase origin/main",
])
def test_a_spec_root_command_off_the_list_is_shown_the_forms_that_ask(
    tmp_path: Path, form: str,
) -> None:
    """An explicit refspec is what an agent writes first. With the generic
    refusal it was told to hand off to the store, which has no session, and
    nothing said that a bare `push` would have reached the prompt, so it kept
    trying other spellings."""
    result = _Layout(tmp_path).hook(form)
    assert result.exit_code == 2
    err = result.stderr or result.output
    assert "push [origin]" in err
    assert "rebase [origin/specs-trunk |" in err
    assert "workmux send" not in err


@pytest.mark.parametrize("ref", ["refs/tags/origin/specs-trunk", "refs/heads/origin/specs-trunk"])
def test_a_rebase_upstream_shadowed_by_a_local_ref_is_refused(
    tmp_path: Path, ref: str,
) -> None:
    """git reads `origin/specs-trunk` as a tag or a local branch of that name
    before the remote branch, and any worktree can create one with no prompt.
    Pointed at `main`, it would turn the routine rebase into one that brings
    the code's history into the store."""
    layout = _Layout(tmp_path)
    subprocess.run(
        ["git", "-C", str(layout.main), "update-ref", ref, "main"],
        check=True, capture_output=True,
    )
    result = layout.hook("git -C /repo-specs rebase origin/specs-trunk")
    assert not _asks(result)
    assert result.exit_code == 2
    err = result.stderr or result.output
    # git names no single ref when a local one shares the remote branch's name.
    assert "as no single ref" in err
    assert "rename or delete" in err
    # The forms list would name the command just refused as one that asks.
    assert "push [origin]" not in err


def test_a_rebase_before_the_first_fetch_is_told_to_fetch(tmp_path: Path) -> None:
    """With no remote-tracking branch yet, git reads the upstream as nothing,
    and the forms list would tell the agent to run the same rebase again."""
    layout = _Layout(tmp_path)
    subprocess.run(
        ["git", "-C", str(layout.store), "update-ref", "-d", "refs/remotes/origin/specs-trunk"],
        check=True, capture_output=True,
    )
    result = layout.hook("git -C /repo-specs rebase origin/specs-trunk")
    assert result.exit_code == 2
    err = result.stderr or result.output
    assert "as no single ref" in err
    assert "fetch origin" in err


@pytest.mark.parametrize("form", [
    "git -C /repo-specs commit -m x && git -C /repo-specs push",
    "git -C /repo-specs pull --rebase && git -C /repo-specs push",
    "git -C /repo-specs push 2>&1 | tail -3",
    "git -C /repo-specs push 2>/dev/null",
    "git -C /repo-specs -c x=y push",
])
def test_a_chained_spec_root_git_command_is_told_to_run_it_alone(
    tmp_path: Path, form: str,
) -> None:
    """These are the forms an agent writes first, and each got the generic
    refusal, which says to hand off to a store that has no session. Nothing
    told the agent that the same push written on its own would reach the
    prompt. They stay refused, since the user can't approve a chain whose
    other half they never see."""
    result = _Layout(tmp_path).hook(form)
    assert result.exit_code == 2
    err = result.stderr or result.output
    assert "written on its own" in err
    assert "workmux send" not in err


@pytest.mark.parametrize("form", [
    "git -C /repo/wt/peer/specs push",
    "git -C /repo/wt/peer/specs commit -m x",
])
def test_a_spec_root_inside_a_peer_worktree_takes_no_git_command(
    tmp_path: Path, form: str,
) -> None:
    """A review read `committable` as checking only folders below the root for
    being the top of their checkout, so a spec root set to `<peer>/specs`
    would ask before a push onto that feature's branch. `owns_branch` refuses
    it first, because the peer's own checkout counts as another worktree with
    the branch. This pins that, so a change to either check can't open it."""
    layout = _Layout(tmp_path)
    (layout.peer / "specs").mkdir()
    (layout.main / ".wf-skills-manifest.json").write_text(
        json.dumps({"spec_root": str(layout.peer / "specs")})
    )
    result = layout.hook(form)
    assert not _asks(result)
    assert result.exit_code == 2


def test_a_spec_root_command_that_reaches_a_peer_isnt_shown_the_forms_that_ask(
    tmp_path: Path,
) -> None:
    """The list of forms that ask is advice to reword the command. For one that
    writes into another feature's worktree, rewording isn't the fix, so it keeps
    the guard's ordinary cross-worktree refusal."""
    result = _Layout(tmp_path).hook("git -C /repo-specs mv a /repo/wt/peer/b")
    assert result.exit_code == 2
    err = result.stderr or result.output
    assert "another worktree" in err
    assert "push [origin]" not in err


def test_a_review_module_that_wont_import_refuses_instead_of_asking(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The ask path is the only place a plain push in the spec root imports
    `_review_gate`. If that import raised out of the hook, the hook would exit
    1, the host would read it as a failed hook, and the push would run with
    no prompt."""
    import sys

    monkeypatch.setitem(sys.modules, "wfctl._review_gate", None)
    result = _Layout(tmp_path).hook("git -C /repo-specs push")
    assert result.exit_code == 2
    assert "couldn't tell whether Claude Code will ask you" in (result.stderr or result.output)
