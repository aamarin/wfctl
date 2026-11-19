"""The accept check's threat model and the guard agree, form by form.

`docs/architecture/accept-check-threat-model.md` lists the forms the guard
must keep refusing and the ordinary commands it must let through. On #792 the
security panel had no such list, so it couldn't tell a regression from a form
the guard had already given up, and three rounds chased the difference. These
tests read the lists from the record, so a form added there is tested with no
change here, and a change to the guard that breaks one fails here.
"""
import json
import re
from pathlib import Path

import pytest

from wfctl import _review_gate
from wfctl.guard import _hook

_RECORD = (
    Path(__file__).resolve().parent.parent
    / "docs" / "architecture" / "accept-check-threat-model.md"
)


def _forms(part: str) -> list[str]:
    """The form in each numbered item under one `###` part of the record.

    The last code span, not the first: several items name `--dry-run` or
    `arch` in their description before the form itself. The part ends at the
    next heading of any level, since `Must let through` is the last `###` and
    a numbered list under a later `##` would otherwise become test cases. An
    item wrapped onto a second line is joined first, so its form is still the
    last span rather than one from its description."""
    sections = re.split(r"^### ", _RECORD.read_text(), flags=re.M)
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


_CATCH = _forms("Must keep catching")
_LET_THROUGH = _forms("Must let through")


def _hook_run(command: str, cwd: Path, capsys: pytest.CaptureFixture[str]) -> tuple[int, str]:
    payload = {"tool_input": {"command": command}, "cwd": str(cwd)}
    code = _hook.worktree_guard(json.dumps(payload).encode())
    return code, capsys.readouterr().err


def test_both_lists_in_the_record_are_found() -> None:
    """A renamed heading or a reworded item would leave a list empty, and the
    parametrized tests below would then pass by testing nothing."""
    assert _CATCH
    assert _LET_THROUGH


@pytest.mark.parametrize("command", _CATCH)
def test_the_guard_refuses_every_form_the_record_says_it_must_keep_catching(
    command: str, tmp_path: Path, capsys: pytest.CaptureFixture[str],
) -> None:
    """Each form is one the record promises the guard refuses. The hook runs
    too, since its substring test decides whether the text check is reached
    at all, and a form that skips it gets through however well `read` reads."""
    refused, _ = _review_gate.read(command)
    assert _review_gate.ACCEPT_REFUSAL in refused

    code, err = _hook_run(command, tmp_path, capsys)
    assert code == 2
    assert _review_gate.ACCEPT_REFUSAL in err


@pytest.mark.parametrize("command", _LET_THROUGH)
def test_the_guard_lets_through_every_form_the_record_says_it_must(
    command: str, tmp_path: Path, capsys: pytest.CaptureFixture[str],
) -> None:
    """A text check that's too broad refuses commit messages and searches that
    only name the command, which is how #792 started. Each form here is
    ordinary work the record says the accept check leaves alone."""
    refused, _ = _review_gate.read(command)
    assert _review_gate.ACCEPT_REFUSAL not in refused

    code, err = _hook_run(command, tmp_path, capsys)
    assert code == 0, err
    assert _review_gate.ACCEPT_REFUSAL not in err
