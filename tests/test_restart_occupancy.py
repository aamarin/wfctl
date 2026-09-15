"""How full the window is, read from a Claude transcript (#371).

The restart's whole trigger. A wrong reading either never restarts a full pane
or restarts one that had room, so each failure shape here is one the transcript
really produces: tool-result lines with no usage, a torn final append, a record
written by an older harness.
"""
from __future__ import annotations

import json
from pathlib import Path

from wfctl._restart import occupancy


def _usage(inp: int, read: int = 0, created: int = 0) -> str:
    return json.dumps({
        "type": "assistant",
        "message": {"usage": {
            "input_tokens": inp,
            "cache_read_input_tokens": read,
            "cache_creation_input_tokens": created,
            "output_tokens": 999,
        }},
    })


def test_the_last_usage_record_wins_and_is_not_summed(tmp_path: Path) -> None:
    """Each record already describes the whole window. Summing — the obvious
    reading of "tokens used" — counts the same context once per turn and would
    restart a pane at a fraction of the threshold."""
    t = tmp_path / "t.jsonl"
    t.write_text("\n".join([
        _usage(10, 1000, 50),
        json.dumps({"type": "user", "message": {"content": "tool result"}}),
        _usage(20, 150000, 60),
        json.dumps({"type": "user", "message": {"content": "no usage here"}}),
    ]) + "\n")
    assert occupancy(t) == 20 + 150000 + 60


def test_output_tokens_are_not_part_of_the_window(tmp_path: Path) -> None:
    """Output becomes input on the next turn and is counted there; counting it
    here would read one reply ahead of the window."""
    t = tmp_path / "t.jsonl"
    t.write_text(_usage(1, 2, 3) + "\n")
    assert occupancy(t) == 6


def test_a_torn_final_line_does_not_lose_the_reading(tmp_path: Path) -> None:
    """The harness appends while the hook reads; a half-written last line must
    leave the previous complete record as the answer."""
    t = tmp_path / "t.jsonl"
    t.write_text(_usage(5, 100000) + "\n" + '{"type": "assistant", "mess')
    assert occupancy(t) == 100005


def test_every_unreadable_transcript_is_none_not_zero(tmp_path: Path) -> None:
    """None is "cannot tell", which decides nothing. Zero would read as an empty
    window — the same outcome today, and the wrong fact for any reader that ever
    compares against a floor."""
    missing = tmp_path / "missing.jsonl"
    no_usage = tmp_path / "no-usage.jsonl"
    no_usage.write_text(json.dumps({"type": "user", "message": {"content": "hi"}}) + "\n")
    garbage = tmp_path / "garbage.jsonl"
    garbage.write_text("not json\n[1, 2]\n")
    odd = tmp_path / "odd.jsonl"
    odd.write_text(
        json.dumps({"message": {"usage": "lots"}}) + "\n"
        + json.dumps({"message": {"usage": {"input_tokens": "12"}}}) + "\n"
    )

    for path in (missing, no_usage, garbage, odd):
        assert occupancy(path) is None, path.name
