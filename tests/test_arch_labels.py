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


# --- the shapes `_labels` reads, and the three it must not -------------------
#
# A second review panel, run over the first panel's own fixes, found six ways
# `_labels` read a drawing wrongly (#294 is the general form: a panel's fixes
# are the least-reviewed code in a branch). Four are shapes this repository's
# own records already use, so the check was silently blind to them rather than
# theoretically incomplete.


def test_an_edge_label_between_pipes_is_read() -> None:
    """`A -->|text| B` is mermaid's edge-label syntax and the shape this
    repository's records reach for most — `the-author-declares-the-diagram-kind`
    carries four. They were read as nothing at all, so VR-007 compared a
    drawing against the prose while ignoring most of what the drawing said."""
    assert _arch._labels("A -->|invented shibboleth| B") == ["invented shibboleth"]
    assert _arch._labels("A --x|never inferred| B") == ["never inferred"]


def test_a_bare_pipe_is_not_an_edge_label() -> None:
    """The fix for the test above, written as a bare `|text|`, reads every cell
    wall of an ASCII box or table as a label — which is the one thing R-004
    fixed the mechanism's limit at: an ASCII drawing yields nothing rather than
    a false comparison. The arrow is required, and required to be adjacent."""
    assert _arch._labels("| left side | --> | right side |") == []
    assert _arch._labels("| a | b | c |") == []


def test_a_bare_subgraph_title_is_read() -> None:
    """`subgraph agent` names a grouping, and `session-state-is-re-derived`
    titles both of its subgraphs this way. A title written as `subgraph a["x"]`
    is already read as a bracketed label, so only the bare form was missing."""
    assert _arch._labels("subgraph Storage Layer\nend") == ["Storage Layer"]
    assert _arch._labels('subgraph author["the record\'s author"]') == [
        "the record's author"
    ]


def test_a_comment_line_yields_no_label() -> None:
    """Mermaid ignores a `%%` line whatever it contains, so a commented-out
    edge is not in the picture. Reading one produced a warning about a label
    no reader of the rendered diagram can see."""
    assert _arch._labels("%% A --> B: invented shibboleth") == []


def test_a_class_attachment_is_not_a_transition_label() -> None:
    """`:::` attaches a CSS class. Read as a transition label it yields
    `::critical` — a token that by construction appears in no record's prose,
    so it warned every time and could never be resolved."""
    assert _arch._labels("A --> B:::critical") == []


def test_a_mixed_transition_label_stays_one_label() -> None:
    """`A --> B: known "x"` is one label. A bare-quote scan running first takes
    `"x"` out of it and leaves `known` behind as a second, so one label became
    two findings — the same defect the quoted-transition test above pins, from
    the side the earlier fix did not reach."""
    assert _arch._labels('A --> B: known "invented shibboleth"') == [
        'known "invented shibboleth"'
    ]


def test_a_rounded_or_circular_node_label_is_read() -> None:
    """`A(text)` and `A((text))` are mermaid's rounded and circular nodes, and
    neither the bracket nor the quote scan sees an unquoted one — so a drawing
    built from them compared as though it named nothing. Raised by the review
    on the PR, after the panel's six."""
    assert _arch._labels("A(invented shibboleth)") == ["invented shibboleth"]
    assert _arch._labels("A((circle label))") == ["circle label"]


def test_a_parenthesised_aside_is_not_its_own_label() -> None:
    """The node id must be adjacent to the paren, for the reason the arrow must
    be adjacent to the pipe: a bare `(text)` is an aside, and a transition label
    may contain one. Matching it loose splits `A --> B: refuses (silently)` into
    two labels — the same defect the mixed-quote fix above closed."""
    assert _arch._labels("A --> B: refuses (silently)") == ["refuses (silently)"]
    assert _arch._labels('A["text (aside)"] --> B') == ["text (aside)"]


def test_a_bracket_inside_a_quoted_node_label_does_not_end_it() -> None:
    """`["Use [cache]"]` is a legal quoted label carrying a bracket. The
    bracketed pattern stopped at the inner `]`, yielding the fragment
    `"Use [cache` — a warning naming a label nobody wrote."""
    assert _arch._labels('A["Use [cache]"] --> B') == ["Use [cache]"]


def test_every_sequence_message_arrow_is_read() -> None:
    """A `sequenceDiagram` draws its messages with `->>`, `->`, `-x` and `-)`,
    solid or dotted, and the label follows the `:`. Only `-->` was read, so a
    `sequence` record (#495) had its solid messages skipped and could name a
    step its prose never mentions with no warning."""
    for arrow in ["->>", "-->>", "->", "-x", "--x", "-)", "--)"]:
        assert _arch._labels(f"agent{arrow}wfctl: run step") == ["run step"], arrow


def test_a_participant_alias_is_read_and_its_id_is_not() -> None:
    """`participant R as renderer` renders as "renderer"; the `R` before `as`
    is an id nobody reading the drawing sees, so comparing it would warn about
    a word that is not in the picture."""
    assert _arch._labels("participant R as renderer") == ["renderer"]
    assert _arch._labels('actor A as "the agent"') == ["the agent"]


# --- the failure row a sequence drawing carries (#495) ----------------------


def _sequence(status: str, drawing: str) -> str:
    return (
        f"---\nstatus: {status}\ndiagram: sequence\n---\n\n# A decision\n\n"
        "## Decision\n\nThe renderer polls and wfctl answers.\n\n"
        f"## Boundary\n\n```mermaid\nsequenceDiagram\n{drawing}\n```\n\n"
        "## Log\n\n- 2026-03-14  proposed    — x\n"
    )


def test_a_sequence_with_no_step_that_fails_is_warned(tmp_path: Path) -> None:
    """The kind exists to show what is left when a step fails partway, so a
    happy-path-only drawing has drawn the half it was not added for."""
    path = _write(
        tmp_path, "a-decision",
        _sequence("proposed", "  renderer->>wfctl: polls\n  wfctl-->>renderer: answers"),
    )

    findings = _arch.validate([_arch.parse_record(path)])

    assert any(
        f.level == "warning" and "no step that fails" in f.message for f in findings
    )


@pytest.mark.parametrize("failure", [
    "  alt wfctl answers\n  wfctl-->>renderer: answers\n  else wfctl fails\n"
    "  wfctl-->>renderer: nothing\n  end",
    "  opt the poll fails\n  renderer->>renderer: polls again\n  end",
    "  break wfctl fails\n  wfctl-->>renderer: nothing\n  end",
    "  critical wfctl answers\n  wfctl-->>renderer: answers\n  end",
    "  wfctl--xrenderer: answers",
])
def test_any_drawn_failure_path_satisfies_it(tmp_path: Path, failure: str) -> None:
    path = _write(
        tmp_path, "a-decision",
        _sequence("proposed", f"  renderer->>wfctl: polls\n{failure}"),
    )

    findings = _arch.validate([_arch.parse_record(path)])

    assert not [f for f in findings if "no step that fails" in f.message]


def test_the_failure_row_is_not_asked_of_other_kinds_or_of_accepted_records(
    tmp_path: Path,
) -> None:
    """A `state` drawing follows one thing through its states and owes no
    failure row, and an accepted record's body is frozen, so a finding against
    it names work nobody is allowed to do — VR-007's reason for `proposed` only."""
    happy = "  renderer->>wfctl: polls\n  wfctl-->>renderer: answers"
    accepted = _write(tmp_path, "accepted-one", _sequence("accepted", happy))
    state = _write(
        tmp_path, "state-one",
        _sequence("proposed", happy).replace("diagram: sequence", "diagram: state"),
    )

    findings = _arch.validate([_arch.parse_record(accepted), _arch.parse_record(state)])

    assert not [f for f in findings if "no step that fails" in f.message]


def test_a_commented_out_failure_block_does_not_count(tmp_path: Path) -> None:
    """Mermaid ignores a `%%` line, so a failure path written there is not in
    the picture a reader sees."""
    path = _write(
        tmp_path, "a-decision",
        _sequence("proposed", "  renderer->>wfctl: polls\n  %% alt wfctl fails"),
    )

    findings = _arch.validate([_arch.parse_record(path)])

    assert any("no step that fails" in f.message for f in findings)


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
