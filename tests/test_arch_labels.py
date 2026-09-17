"""Tests for VR-007 — a drawing label that shares no content word with the rest
of the record (#109, User Story 3).

The mechanism is measured, not argued: research R-004 ran three candidate
comparisons over this repository's own `## Boundary` corpus and kept the one
that fired once over four records rather than 43 or 18. These tests pin the
kept mechanism's behaviour; the corpus run itself is `T030`'s job, below.
"""
from __future__ import annotations

from pathlib import Path

import pytest

from wfctl import _arch


def _write(root: Path, slug: str, body: str) -> Path:
    root.mkdir(parents=True, exist_ok=True)
    path = root / f"{slug}.md"
    path.write_text(body)
    return path


def _record(status: str, boundary: str, extra_prose: str = "") -> str:
    return (
        f"---\nstatus: {status}\ndiagram: state\n---\n\n# A decision\n\n"
        f"## Decision\n\n{extra_prose}\n\n"
        f"## Boundary\n\n{boundary}\n\n"
        "## Log\n\n- 2026-03-14  proposed    — x\n"
    )


# --- scenario 1: only words the record already uses — nothing reported ------


def test_a_drawing_using_only_words_the_record_uses_reports_nothing(
    tmp_path: Path,
) -> None:
    body = _record(
        "proposed",
        '```mermaid\nflowchart LR\n  A["the tracker backend"] --> B["a request"]\n```',
        extra_prose="The tracker backend answers a request.",
    )
    path = _write(tmp_path, "a-decision", body)

    findings = _arch.validate([_arch.parse_record(path)])

    assert findings == []


# --- scenario 2: a label appearing nowhere else is reported -----------------


def test_a_label_appearing_nowhere_else_is_reported_with_the_label_and_the_record(
    tmp_path: Path,
) -> None:
    body = _record(
        "proposed",
        '```mermaid\nflowchart LR\n  A["a wholly invented shibboleth"] --> B["x"]\n```',
        extra_prose="Nothing here mentions that concept at all.",
    )
    path = _write(tmp_path, "a-decision", body)

    findings = _arch.validate([_arch.parse_record(path)])

    warnings = [f for f in findings if f.level == "warning"]
    assert len(warnings) == 1
    assert warnings[0].slug == "a-decision"
    assert "shibboleth" in warnings[0].message


# --- scenario 3: a reported record still accepts (FR-008) -------------------


def test_a_record_with_a_reported_label_still_accepts(tmp_path: Path) -> None:
    body = _record(
        "proposed",
        '```mermaid\nflowchart LR\n  A["a wholly invented shibboleth"] --> B["x"]\n```',
    )
    path = _write(tmp_path, "a-decision", body)

    record = _arch.parse_record(path)

    assert _arch.acceptable(record) is True
    assert _arch.accept_blockers(record) == []


# --- scope (T027) -------------------------------------------------------------


@pytest.mark.parametrize("status", ["accepted", "superseded", "rejected", "retired"])
def test_vr007_fires_on_proposed_only(tmp_path: Path, status: str) -> None:
    """R-005: the three ended statuses exclude themselves on the check's own
    purpose, and `accepted` is FR-006's exclusion — a body VR-005 already
    freezes.

    Filtered to the label-check's own wording rather than "no warnings at
    all": `superseded` with no successor is VR-002's own warning, unrelated to
    this feature and legitimately still fired.
    """
    body = _record(
        status,
        '```mermaid\nflowchart LR\n  A["a wholly invented shibboleth"] --> B["x"]\n```',
    )
    path = _write(tmp_path, "a-decision", body)

    findings = _arch.validate([_arch.parse_record(path)])

    assert not [f for f in findings if "shibboleth" in f.message]


def test_a_quoted_transition_label_is_read_once_not_twice(tmp_path: Path) -> None:
    """`A --> B: "x"` is caught by the bare-quote scan; the colon scan that
    follows it must not read the same text a second time out of what the
    quote scan left behind, or one label produces two near-identical findings
    — one of them carrying stray `"` characters in its message."""
    body = _record(
        "proposed",
        '```mermaid\nstateDiagram-v2\n  A --> B: "a wholly invented shibboleth"\n```',
        extra_prose="Nothing here mentions that concept at all.",
    )
    path = _write(tmp_path, "a-decision", body)

    findings = _arch.validate([_arch.parse_record(path)])

    warnings = [f for f in findings if f.level == "warning"]
    assert len(warnings) == 1
    assert warnings[0].message.count("shibboleth") == 1


def test_an_unreadable_ascii_drawing_produces_no_finding(tmp_path: Path) -> None:
    """Research R-004's stated limit: the check reads bracketed or quoted
    labels. An ASCII box drawing yields none, and the check compares nothing
    rather than inventing a false one."""
    body = _record(
        "proposed",
        "```\n+-----------+     +-----------+\n"
        "| left side | --> | right side |\n"
        "+-----------+     +-----------+\n```",
    )
    path = _write(tmp_path, "a-decision", body)

    findings = _arch.validate([_arch.parse_record(path)])

    assert not [f for f in findings if f.level == "warning"]


# --- the corpus run (T030) ---------------------------------------------------


def test_the_corpus_of_proposed_records_stays_at_or_below_the_calibrated_ceiling() -> None:
    """SC-004. Repeated here rather than trusted from research.md, because the
    corpus a repository holds moves — records get written and accepted — and a
    regression in the mechanism should fail this test before it fails a
    person's judgment in `wfctl doctor` output (T031).
    """
    from wfctl._paths import arch_root

    root = arch_root(Path(__file__).resolve().parents[1])
    records = [r for r in _arch.load_records(root) if r.status == "proposed"]
    findings = _arch.validate(records)
    warnings = [f for f in findings if f.level == "warning"]

    assert len(warnings) <= 2, [f.message for f in warnings]
