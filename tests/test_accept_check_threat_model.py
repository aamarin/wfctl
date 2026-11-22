"""The person-only commands' threat model and the guard agree, form by form.

`docs/architecture/prompt-approves-person-commands.md` lists the forms the
guard must keep refusing and the commands it must let through, now that the
user approves each run at Claude Code's prompt. On #792 the security panel had
no such list, so it couldn't tell a regression from a form the guard had
already given up, and three rounds chased the difference. These tests read the
lists from the record, so a form added there is tested with no change here.

The record also keeps items 1 - 20 of `accept-check-threat-model.md`'s "Must
keep catching", except the plain spellings in its own "Must let through", so
that list is read too, and each item runs again with the words of the other
two commands, since all three share one reader.
"""
from __future__ import annotations

import re
import types
from pathlib import Path

import pytest

from wfctl import _review_gate

_ARCH = Path(__file__).resolve().parent.parent / "docs" / "architecture"
_RECORD = _ARCH / "prompt-approves-person-commands.md"
_OLD_RECORD = _ARCH / "accept-check-threat-model.md"


def _forms(record: Path, part: str) -> list[str]:
    """The form in each numbered item under one `###` part of the record.

    The last code span, not the first: several items name `--dry-run` or
    `arch` in their description before the form itself. The part ends at the
    next heading of any level, since `Must let through` is the last `###` and
    a numbered list under a later `##` would otherwise become test cases. An
    item wrapped onto a second line is joined first, so its form is still the
    last span rather than one from its description."""
    sections = re.split(r"^### ", record.read_text(), flags=re.M)
    for section in sections[1:]:
        heading, _, body = section.partition("\n")
        if heading.strip() == part:
            body = re.split(r"^#", body, maxsplit=1, flags=re.M)[0]
            items = re.findall(r"^\d+\. (.*(?:\n(?!\d+\. |\s*$).*)*)", body, flags=re.M)
            return [
                re.findall(r"`([^`]+)`", re.sub(r"\n\s*", " ", item))[-1]
                for item in items
            ]
    return []


_CATCH = _forms(_RECORD, "Must keep catching")
_LET_THROUGH = _forms(_RECORD, "Must let through")
_OLD_CATCH = _forms(_OLD_RECORD, "Must keep catching")

# Items 16 and 17 of the record's "Must keep catching" are a plain spelling
# under a condition the record names, so each test builds that condition.
_CONDITIONS = {16: "Bob Shell", 17: "rule missing"}

# A heredoc's body and closing line can't sit in one code span, so the record
# names each heredoc by its first line and these finish it.
_CATCH_BODIES = {
    19: "\n$(wfctl arch accept s)\nEOF\n",
    20: "\nnotes\nEOF\nwfctl arch accept s\n",
    21: "\nnotes\\\nEOF\nwfctl arch accept s\nEOF\n",
}
_LET_THROUGH_BODIES = {11: "\nTo accept it, run wfctl arch accept s.\nEOF\n"}

# Item 12 of "Must let through" is the plain accept with wfctl's auto-approve
# on, which the prompt still holds, so the test turns the mode on first.
_LET_THROUGH_AUTO_APPROVE = {12}

# Items 1, 16, and 19 of the old list are a plain spelling with arguments,
# which Claude Code's rule matches, so they pass once the host asks. The
# record leaves that reading to the user, and the PR names it. Item 2 is the
# `uv run` spelling, which no command has, so it stays refused.
_OLD_PLAIN = {1, 16, 19}

_COMMANDS = {
    "accept": ("arch", "accept"),
    "sign-off": ("review", "sign-off"),
    "approve-imports": ("arch", "approve-imports"),
}


def _swapped(form: str, group: str, verb: str) -> str:
    return re.sub(r"\baccept\b", verb, re.sub(r"\barch\b", group, form))


def _old_cases() -> list[object]:
    """Each old item once per command. Item 5 splits `accept` with a
    backslash, which has no meaning for the other two words, so it runs for
    the accept only."""
    cases = []
    for n, form in enumerate(_OLD_CATCH, 1):
        for name, (group, verb) in _COMMANDS.items():
            if n == 5 and name != "accept":
                continue
            passes = n in _OLD_PLAIN
            cases.append(pytest.param(
                _swapped(form, group, verb), name, passes, id=f"{n}-{name}",
            ))
    return cases


def _refusal_names(err: str, name: str) -> bool:
    return any(line.startswith("✗ wfctl ") and name in line for line in err.splitlines())


def test_every_list_is_found() -> None:
    """A renamed heading or a reworded item would leave a list empty, and the
    parametrized tests below would then pass by testing nothing."""
    assert len(_CATCH) == 22
    assert len(_LET_THROUGH) == 12
    assert len(_OLD_CATCH) == 20


@pytest.mark.parametrize("n", range(1, len(_CATCH) + 1))
def test_the_guard_refuses_every_form_the_record_says_it_must_keep_catching(
    n: int, prompted_repo: types.SimpleNamespace,
) -> None:
    """Each form is one the record promises the guard refuses, even with
    Claude Code asking and the rule in place. The hook runs, since its
    substring test decides whether the text check is reached at all."""
    command = _CATCH[n - 1] + _CATCH_BODIES.get(n, "")
    tool: str | None = "Bash"
    condition = _CONDITIONS.get(n)
    if condition == "Bob Shell":
        tool = "run_shell_command"
    elif condition == "rule missing":
        prompted_repo.drop_rule(command)

    code, err = prompted_repo.run(command, tool=tool)

    assert code == 2, command
    assert err.startswith("✗ wfctl "), err


@pytest.mark.parametrize("n", range(1, 13))
def test_the_guard_lets_through_every_form_the_record_says_it_must(
    n: int, prompted_repo: types.SimpleNamespace,
) -> None:
    """The first three and the last are the plain spellings Claude Code asks
    about, so the guard has to let them reach the prompt. The rest only name a
    command, and a check that refuses them refuses ordinary work, which is how
    #792 and #838 started."""
    if n in _LET_THROUGH_AUTO_APPROVE:
        prompted_repo.auto_approve(True)
    command = _LET_THROUGH[n - 1] + _LET_THROUGH_BODIES.get(n, "")
    assert prompted_repo.run(command) == (0, "")


@pytest.mark.parametrize(
    "command",
    [
        "echo 'wfctl review sign-off'",
        "printf '%s\\n' \"wfctl arch approve-imports\"",
        "cat > notes.md <<'EOF'\nrun wfctl review sign-off\nEOF",
        "cat >> notes.md <<-\"EOF\"\n\twfctl arch approve-imports\n\tEOF\n",
    ],
)
def test_quoting_sign_off_or_approve_imports_is_let_through_with_no_payload(
    command: str,
) -> None:
    """With no payload, every command the reader flags is refused, so these
    show the reader itself passes text that only quotes the other two
    commands, not that the prompt let them through (#838)."""
    assert _review_gate.read(command) == ([], [])


@pytest.mark.parametrize(
    "command",
    [
        "echo 'wfctl review sign-off' > run.sh",
        "echo \"`wfctl arch accept s`\"",
        "printf '%s' 'wfctl arch accept s' | bash",
        "cat > x.md <<'EOF' && wfctl review sign-off\nnotes\nEOF\n",
        "cat > $(wfctl arch accept s) <<'EOF'\nnotes\nEOF\n",
    ],
)
def test_text_only_forms_with_anything_more_stay_refused(command: str) -> None:
    """Each starts as one of the record's text-only forms and adds a
    redirect, a substitution, a pipe, or a second command, which is what
    item 13's whole-command rule exists to refuse."""
    refused, _ = _review_gate.read(command)
    assert refused, command


@pytest.mark.parametrize(("command", "name", "passes"), _old_cases())
def test_the_old_list_stays_refused_except_its_plain_spellings(
    command: str, name: str, passes: bool, prompted_repo: types.SimpleNamespace,
) -> None:
    """With no payload, the reader refuses every old item for every command,
    as it did before the prompt. Through the hook, with Claude Code asking,
    only a plain spelling passes."""
    refused, _ = _review_gate.read(command)
    assert any(name in line for line in refused), refused

    code, err = prompted_repo.run(command)

    if passes:
        assert (code, err) == (0, "")
    else:
        assert code == 2
        assert _refusal_names(err, name), err
