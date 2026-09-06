"""Tests for `wfctl._shape` and the two commands that run it.

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

from wfctl import _shape
from wfctl.cli import app

runner = CliRunner()

BARE = "file an issue for it"


def test_a_markdown_header_is_flagged_and_a_bold_lead_in_is_not() -> None:
    """The rule forbids markdown headers outright, and names the bold lead-in as
    what replaces them — so a check that flagged both would flag the fix."""
    assert _shape.findings("### Findings\nyes.", BARE)
    assert not _shape.findings("**Findings** yes.", BARE)


def test_every_header_level_is_flagged_not_only_the_two_the_issue_names() -> None:
    """SKILL.md:410 is "a reply is not a document — no markdown headers in it";
    `##` and `###` are its examples, not the closed set. `#### Findings` is the
    same drift one level deeper, and a check that reports it clean is the failure
    this issue is about."""
    for level in ("#", "##", "###", "####", "#####", "######"):
        assert _shape.findings(f"{level} Findings\nyes.", BARE), level


def test_four_spaces_of_indent_is_a_code_block_not_a_header() -> None:
    """Markdown's own limit: a header may be indented up to three spaces, and at
    four the line is an indented code block. Without the limit a shell snippet
    pasted without a fence reports as document furniture."""
    assert _shape.findings("   ### Findings\nyes.", BARE)
    assert not _shape.findings("    # rm -rf build\nyes.", BARE)


def test_a_counted_lead_in_is_flagged_and_a_counted_fact_is_not() -> None:
    """The issue's own pair. `Three things worth flagging:` announces a list that
    the answer did not need; `Three reviewers reported` is a sentence that
    happens to start with a number, and flagging it would make every factual
    count a violation."""
    assert _shape.findings("Three things worth flagging:\n- a\n- b", BARE)
    assert not _shape.findings("Three reviewers reported the same bug.", BARE)


def test_a_reply_that_ran_long_with_nothing_asking_for_it_is_flagged() -> None:
    """Q3, and the only finding that looks at length at all."""
    found = _shape.findings("word " * 300, BARE)
    assert any(line.startswith("Q3") for line in found)


def test_the_same_long_reply_is_not_flagged_when_the_prompt_asked_for_depth() -> None:
    """The skill's rule 3 is that depth is opted into by the words asked. A check
    that flagged this would contradict the rule it enforces, and the reader would
    be right to disable it — which is the failure #212 is about, one level up."""
    assert not _shape.findings("word " * 300, "thoughts?")


def test_every_finding_names_the_check_the_reader_already_agreed_to() -> None:
    """The signal has to read as their own pre-send check, not as a script
    scolding them — an AC in its own right, because the fix is only obvious when
    the reader can see which question caught it."""
    found = _shape.findings("### H\nThree things:\n" + "word " * 300, BARE)
    assert len(found) == 3
    assert [line.split(" ")[0] for line in found] == ["Q4", "rule", "Q3"]


def test_a_fenced_block_is_content_not_voice() -> None:
    """A reply quoting a SKILL.md excerpt or a `doctor` run carries headings and
    counted lines that are not the author's. Flagging them would fire hardest on
    the replies that did the most work."""
    quoted = "```\n### Failure modes\nThree things worth flagging:\n```\nyes."
    assert not _shape.findings(quoted, BARE)


def test_a_colon_inside_inline_code_does_not_make_a_lead_in() -> None:
    """The colon is the discriminator, so a colon that belongs to something being
    quoted is not one. This line is a sentence about two branches, and it was the
    only rule-6 false positive across ninety transcripts."""
    quoted = "Two unrelated branches show `[origin/main: gone]` in the listing"
    assert not _shape.findings(quoted, BARE)


def test_a_markdown_table_does_not_count_toward_the_length_signal() -> None:
    """`_prose` drops fences because rule 6 exempts a drawing — and the skill's
    own form-selection table makes a markdown table the drawing it asks for most
    often. Counting its rows fired a third of the length findings on the shape
    the rule recommends."""
    table = "done.\n\n| a | b |\n|---|---|\n" + "| word | word |\n" * 200
    assert not _shape.findings(table, BARE)


def test_a_fenced_block_does_not_count_toward_the_length_signal() -> None:
    """Rule 6 exempts a drawing. A three-hundred-line diff is not three hundred
    lines of prose, and counting it would turn the check into the word budget the
    issue rules out."""
    assert not _shape.findings("done.\n```\n" + "code " * 400 + "\n```\n", BARE)


def test_a_quoted_fence_inside_a_wider_one_is_still_inside_it() -> None:
    """A fence closes only on the same character, no shorter, with no info string
    — CommonMark's rule. Splitting on the marker instead treats the quoted
    ```-block's opening as the close, and every heading and counted lead-in in
    the quotation then reports as a violation of the rule being quoted. This
    repo's own skills are written this way."""
    quoting = (
        "Here is what the rule forbids:\n"
        "````\n"
        "```\n"
        "### Findings\n"
        "Three things worth flagging:\n"
        "```\n"
        "````\n"
        "That is the whole rule.\n"
    )
    assert not _shape.findings(quoting, BARE)


def test_depth_is_asked_for_in_whatever_form_the_word_takes() -> None:
    """`detail` matched only its bare singular while every neighbour matched a
    stem, so "give me a detailed response" read as a prompt that asked for
    nothing — a false positive on an explicit request, which is the error this
    list is deliberately over-broad to avoid."""
    for asked in ("give me a detailed response", "provide all details",
                  "elaborate on this", "elaborating is fine"):
        assert not _shape.findings("word " * 300, asked), asked


def test_an_unclosed_fence_drops_its_tail_rather_than_scanning_it() -> None:
    """A reply cut off mid-block leaves one fence marker. Matching pairs would
    match nothing and scan the code as prose."""
    assert not _shape.findings("done.\n```\n### still code\n", BARE)


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


def _run(transcript: Path) -> str:
    return runner.invoke(
        app, ["hook", "response-shape"],
        input=json.dumps({"transcript_path": str(transcript)}),
    ).output


def test_the_finding_reaches_the_model_not_the_terminal(tmp_path: Path) -> None:
    """`systemMessage` is not wired for `Stop` in the Claude Code this was built
    against: across seven runs in one session the hook produced a finding twice
    and neither reached the reader. `additionalContext` is the channel that
    works, and it reaches the agent that wrote the reply, in time to shape the
    next one. Both are emitted, so a version that wires the other up costs no
    change — but the model-facing one is the load-bearing key."""
    path = _transcript(tmp_path, [_user(BARE), _assistant("Three things worth flagging:")])
    out = json.loads(_run(path))
    assert out["hookSpecificOutput"]["hookEventName"] == "Stop"
    assert "counted lead-in" in out["hookSpecificOutput"]["additionalContext"]
    assert out["hookSpecificOutput"]["additionalContext"] == out["systemMessage"]


def test_the_report_carries_the_finding_before_the_instruction(tmp_path: Path) -> None:
    """An instruction to re-read the skill is, on its own, the fourth reminder in
    a stack of three that already lost — which is #212. The finding is what makes
    it a correction instead, so it goes first and the pointer follows it."""
    path = _transcript(tmp_path, [_user(BARE), _assistant("Three things worth flagging:")])
    message = json.loads(_run(path))["systemMessage"]
    assert message.index("counted lead-in") < message.index("Re-read the skill")
    assert "/conversation-response-shape" in message


def test_the_handed_over_reply_is_preferred_to_the_walked_one(tmp_path: Path) -> None:
    """`Stop` now hands the finished reply over as `last_assistant_message`, so
    the transcript walk is a fallback rather than the only source. The walk stays
    because the depth gate needs the prompt, and no field carries that."""
    path = _transcript(tmp_path, [_user(BARE), _assistant("Filed #213.")])
    result = runner.invoke(app, ["hook", "response-shape"], input=json.dumps({
        "transcript_path": str(path),
        "last_assistant_message": "Three things worth flagging:",
    }))
    assert "counted lead-in" in json.loads(result.output)["systemMessage"]


def test_a_handed_over_reply_that_is_empty_falls_back_to_the_walk(tmp_path: Path) -> None:
    """An older Claude Code sends no such field, and a newer one can send an
    empty string. Neither is evidence that the reply was empty."""
    path = _transcript(tmp_path, [_user(BARE), _assistant("Three things worth flagging:")])
    for handed in ("", "   ", None, 7):
        result = runner.invoke(app, ["hook", "response-shape"], input=json.dumps({
            "transcript_path": str(path), "last_assistant_message": handed,
        }))
        assert "counted lead-in" in result.output, handed


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


def test_a_record_the_reader_did_not_type_does_not_become_the_prompt(
    tmp_path: Path,
) -> None:
    """A quarter of turn boundaries are machine-written `user` records — an
    injected `SKILL.md` body, a slash-command expansion, an `[Image: …]` stub, a
    subagent completion. Taking one as the prompt throws the reader's own words
    away, and it fails in both directions: a skill body is thousands of words of
    `review` and `analyse`, an image stub is none of them."""
    for machine in (
        {"type": "user", "isMeta": True,
         "message": {"role": "user", "content": "Base directory for this skill: /x"}},
        {"type": "user", "promptSource": "system",
         "message": {"role": "user", "content": "<task-notification>done</task-notification>"}},
    ):
        path = _transcript(tmp_path, [
            _user("thoughts?"),
            _assistant("", tool=True),
            machine,
            _assistant("word " * 300),
        ])
        assert _run(path) == "", machine


def test_a_transcript_that_is_not_there_is_not_an_error(tmp_path: Path) -> None:
    """This runs at the end of every turn. A hook that fails is a per-turn error
    in a session that was otherwise fine — `_hook_user_prompt`'s posture, for the
    same reason."""
    assert _run(tmp_path / "gone.jsonl") == ""


def test_a_payload_this_hook_cannot_read_describes_no_reply() -> None:
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


# --- the PR-body surface ----------------------------------------------------


REJECTED = """```
  1. directory named 567-*  ------------------------------ none
  2. issue-key glob "567"   ------------------------------ none
  3. NEW  a delivery.md whose grouping map names 567
          555-taxonomy-redesign  claims 567 ------------- resolved
  4. ancestor branches, nearest first
          562-transaction-balance      -> specs/562-...
                                         BEFORE: returned it
                                         AFTER: its map claims 575
                                            and 576, not 567 - a decomposed
                                            feature that had its chance to
                                            name us and did not. Skipped.
```
"""

ACCEPTED = """```
BEFORE                                   AFTER
$ wfctl status                           $ wfctl status
brainstorm   *                           brainstorm   *
implement    *  46/46 done               implement    *  5/64 done
                 ^                                        ^
     feature 562's task list,                 feature 555's task list
```
"""


def test_the_drawing_the_reader_rejected_is_flagged() -> None:
    """PR #208's second drawing, verbatim. The reader called it "noisy and
    confusing"; SKILL.md:322 names the fault exactly — tabular content aligned by
    hand, with a cell that outgrew its header."""
    found = _shape.body_findings(REJECTED)
    assert len(found) == 1
    assert "SKILL.md:322" in found[0]
    assert "name us and did not. Skipped." in found[0]


def test_the_drawing_the_reader_accepted_is_not_flagged() -> None:
    """The same PR body's first drawing, which nobody objected to. It is hand
    aligned too — two columns is the form-selection table's most frequent row —
    so alignment alone would have flagged the fix along with the fault."""
    assert not _shape.body_findings(ACCEPTED)


def test_headers_are_a_reply_rule_and_not_a_pr_body_rule() -> None:
    """SKILL.md:429 scopes the header rule to the reply: headers are "correct,
    and usually required" in a PR body, and the repository's own template is
    built out of them. A check that applied the whole skill to both surfaces
    would flag every description this project asks for."""
    body = "## Summary\n\nIt works.\n"
    assert _shape.findings(body, BARE)
    assert not _shape.body_findings(body)


def test_check_body_names_the_file_it_cannot_read() -> None:
    result = runner.invoke(app, ["check-body", "/nonexistent/body.md"])
    assert result.exit_code == 1
    assert "body.md" in result.output


def test_check_body_exits_one_on_a_finding_and_zero_without(tmp_path: Path) -> None:
    """Exit 1 so the finding is hard to walk past. It gates nothing — nothing
    runs this but the author."""
    bad = tmp_path / "bad.md"
    bad.write_text(REJECTED)
    good = tmp_path / "good.md"
    good.write_text(ACCEPTED)
    assert runner.invoke(app, ["check-body", str(bad)]).exit_code == 1
    assert runner.invoke(app, ["check-body", str(good)]).exit_code == 0
