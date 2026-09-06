"""Tests for `wfctl._reply` and the `Stop` hook that runs it.

The detector is the first thing in this repo that judges prose, so what these
assert is the *boundary* it draws, not that it fires. A check that flags a reply
the reader asked for gets switched off, and then the rule it enforces is back to
having nothing behind it — which is the whole of #212. So every "does not flag"
case here is load-bearing in a way the "flags" cases are not.

The four pairs the issue names as its own acceptance criteria are the first four
tests, phrased as it phrased them.
"""
from __future__ import annotations

import json
from pathlib import Path

from typer.testing import CliRunner

from wfctl import _reply
from wfctl.cli import app

runner = CliRunner()

BARE = "file an issue for it"


def test_a_markdown_heading_is_flagged_and_a_bold_lead_in_is_not() -> None:
    """The rule forbids `##`/`###` outright, and names the bold lead-in as what
    replaces them — so a check that flagged both would flag the fix."""
    assert _reply.findings("### Findings\nyes.", BARE)
    assert not _reply.findings("**Findings** yes.", BARE)


def test_a_counted_lead_in_is_flagged_and_a_counted_fact_is_not() -> None:
    """The issue's own pair. `Three things worth flagging:` announces a list that
    the answer did not need; `Three reviewers reported` is a sentence that
    happens to start with a number, and flagging it would make every factual
    count a violation."""
    assert _reply.findings("Three things worth flagging:\n- a\n- b", BARE)
    assert not _reply.findings("Three reviewers reported the same bug.", BARE)


def test_a_reply_that_ran_long_with_nothing_asking_for_it_is_flagged() -> None:
    """Q3, and the only finding that looks at length at all."""
    found = _reply.findings("word " * 300, BARE)
    assert any(line.startswith("Q3") for line in found)


def test_the_same_long_reply_is_not_flagged_when_the_prompt_asked_for_depth() -> None:
    """The skill's rule 3 is that depth is opted into by the words asked. A check
    that flagged this would contradict the rule it enforces, and the reader would
    be right to disable it — which is the failure #212 is about, one level up."""
    assert not _reply.findings("word " * 300, "thoughts?")


def test_every_finding_names_the_check_the_reader_already_agreed_to() -> None:
    """The signal has to read as their own pre-send check, not as a script
    scolding them — an AC in its own right, because the fix is only obvious when
    the reader can see which question caught it."""
    found = _reply.findings("### H\nThree things:\n" + "word " * 300, BARE)
    assert len(found) == 3
    assert [line.split(" ")[0] for line in found] == ["Q4", "rule", "Q3"]


def test_a_fenced_block_is_content_not_voice() -> None:
    """A reply quoting a SKILL.md excerpt or a `doctor` run carries headings and
    counted lines that are not the author's. Flagging them would fire hardest on
    the replies that did the most work."""
    quoted = "```\n### Failure modes\nThree things worth flagging:\n```\nyes."
    assert not _reply.findings(quoted, BARE)


def test_a_fenced_block_does_not_count_toward_the_length_signal() -> None:
    """Rule 6 exempts a drawing. A three-hundred-line diff is not three hundred
    lines of prose, and counting it would turn the check into the word budget the
    issue rules out."""
    assert not _reply.findings("done.\n```\n" + "code " * 400 + "\n```\n", BARE)


def test_an_unclosed_fence_drops_its_tail_rather_than_scanning_it() -> None:
    """A reply cut off mid-block leaves one fence marker. Matching pairs would
    match nothing and scan the code as prose."""
    assert not _reply.findings("done.\n```\n### still code\n", BARE)


# --- the hook ---------------------------------------------------------------


def _transcript(tmp_path: Path, turns: list[dict]) -> Path:
    path = tmp_path / "transcript.jsonl"
    path.write_text("\n".join(json.dumps(t) for t in turns) + "\n")
    return path


def _user(text: str) -> dict:
    return {"type": "user", "message": {"role": "user", "content": text}}


def _assistant(text: str = "", tool: bool = False) -> dict:
    content: list[dict] = []
    if text:
        content.append({"type": "text", "text": text})
    if tool:
        content.append({"type": "tool_use", "id": "t", "name": "Bash", "input": {}})
    return {"type": "assistant", "message": {"role": "assistant", "content": content}}


def _run(transcript: Path | str) -> str:
    return runner.invoke(
        app, ["hook", "response-shape"],
        input=json.dumps({"transcript_path": str(transcript)}),
    ).output


def test_the_hook_reports_what_the_last_reply_broke(tmp_path: Path) -> None:
    path = _transcript(tmp_path, [_user(BARE), _assistant("Three things worth flagging:")])
    assert "counted lead-in" in json.loads(_run(path))["systemMessage"]


def test_the_hook_says_nothing_when_the_reply_is_clean(tmp_path: Path) -> None:
    """Most turns. Silence is what keeps the loud ones worth reading — a line on
    every turn is the third reminder in a stack of three that already lost."""
    path = _transcript(tmp_path, [_user(BARE), _assistant("Filed #213.")])
    assert _run(path) == ""


def test_narration_between_tool_calls_is_not_the_terminal_reply(tmp_path: Path) -> None:
    """The reader receives what was written after the last tool call. Counting the
    running commentary before it would flag a session for text the pre-send check
    was never about, and would dominate the word count."""
    path = _transcript(tmp_path, [
        _user(BARE),
        _assistant("Three things worth flagging:", tool=True),
        _assistant("Filed #213."),
    ])
    assert _run(path) == ""


def test_a_tool_result_does_not_start_a_new_turn(tmp_path: Path) -> None:
    """Tool results arrive as `user` records. Treating one as a prompt would
    replace the reader's words with a command's output, and the depth the reader
    asked for would be invisible to the length signal."""
    path = _transcript(tmp_path, [
        _user("thoughts?"),
        _assistant("", tool=True),
        {"type": "user", "message": {"role": "user", "content": [
            {"type": "tool_result", "tool_use_id": "t", "content": "ok"}]}},
        _assistant("word " * 300),
    ])
    assert _run(path) == ""


def test_a_transcript_that_is_not_there_is_not_an_error(tmp_path: Path) -> None:
    """This runs at the end of every turn. A hook that fails is a per-turn error
    in a session that was otherwise fine — `_hook_user_prompt`'s posture, for the
    same reason."""
    assert _run(tmp_path / "gone.jsonl") == ""


def test_a_payload_this_hook_cannot_read_describes_no_reply(tmp_path: Path) -> None:
    """A newer agent's payload, or none at all. Every field is checked because the
    alternative is a traceback at the end of a turn that had nothing wrong."""
    for payload in ["", "not json", "[]", "{}", '{"transcript_path": 7}']:
        result = runner.invoke(app, ["hook", "response-shape"], input=payload)
        assert result.exit_code == 0, payload
        assert result.output == "", payload


def test_a_line_this_hook_cannot_parse_does_not_stop_the_scan(tmp_path: Path) -> None:
    """Transcripts are appended to live, so the last line can be a partial write."""
    path = _transcript(tmp_path, [_user(BARE), _assistant("Three things worth flagging:")])
    path.write_text(path.read_text() + '{"type": "assist')
    assert "counted lead-in" in json.loads(_run(path))["systemMessage"]
