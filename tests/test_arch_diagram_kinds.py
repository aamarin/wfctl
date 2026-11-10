"""Tests for a record that declares more than one diagram kind (#738).

A record's `diagram` field takes a list, such as `[data-flow, sequence]`, and
each kind gets its drawing under its own `### <kind>` heading in `## Boundary`.
`test_arch_accept_drawing.py` covers the one-kind rules as they stood before;
this file covers the list, the drawing for each kind, the four new refusals,
and the doctor warnings that arrive while a record is still proposed.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest
from typer.testing import CliRunner

from wfctl.arch import _records as _arch
from wfctl.cli import app

_FIXTURES = Path(__file__).parent / "fixtures" / "one-kind-records"


def test_every_one_kind_record_gets_the_acceptance_result_it_got_before_lists() -> None:
    """SC-004: a record declaring one kind is checked exactly as before.

    The fixtures are copies of every one-kind record on `main` when #738
    branched, with the `accept_blockers` and `validate` result each one gave
    before `_records.py` learned about lists. They're copies rather than the
    live `docs/architecture/` folder, so a record accepted or added later
    doesn't change what this test compares. A change that moved any one of the
    41 results would mean a one-kind record now passes or fails differently,
    which is the regression this test exists to catch.

    It compares `accept_problems`, not `accept_blockers` alone, against what
    `accept_blockers` gave before lists. Before lists, nothing else refused a
    record, so a kind refusal that now fires on a one-kind record fails here.
    """
    expected = json.loads((_FIXTURES / "expected.json").read_text())
    records = _arch.load_records(_FIXTURES)

    assert {r.slug for r in records} == set(expected)
    for record in records:
        got = {
            "accept_blockers": _arch.accept_problems(record),
            "validate": [[f.level, f.message] for f in _arch.validate([record])],
        }
        assert got == expected[record.slug], record.slug


# --- helpers -------------------------------------------------------------

runner = CliRunner()

_FLOW = "```mermaid\nflowchart LR\n  A --> B\n```\n"
_SEQ = (
    "```mermaid\nsequenceDiagram\n  A->>B: ask\n"
    "  alt B is down\n    B--xA: no answer\n  end\n```\n"
)
_SEQ_HAPPY_ONLY = "```mermaid\nsequenceDiagram\n  A->>B: ask\n  B-->>A: answer\n```\n"


def _write(
    root: Path,
    slug: str = "a-decision",
    *,
    diagram: str | None = "[data-flow, sequence]",
    boundary: str = f"### data-flow\n\n{_FLOW}\n### sequence\n\n{_SEQ}\n",
    status: str = "proposed",
    log: bool = True,
) -> Path:
    root.mkdir(parents=True, exist_ok=True)
    front = f"---\nstatus: {status}\n"
    if diagram is not None:
        front += f"diagram: {diagram}\n"
    text = f"{front}---\n\n# {slug}\n\n## Decision\n\nA and B.\n\n## Boundary\n\n{boundary}\n"
    if log:
        text += "## Log\n\n- 2026-11-10  proposed    — x\n"
    path = root / f"{slug}.md"
    path.write_text(text)
    return path


def _read(root: Path, slug: str = "a-decision") -> _arch.Record:
    return _arch.parse_record(root / f"{slug}.md")


def _arch_root(agent_dir: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    root = agent_dir.parent / "docs" / "architecture"
    monkeypatch.setenv("WFCTL_ARCH_DIR", str(root))
    return root


def _dry_run(slug: str = "a-decision") -> tuple[int, str]:
    result = runner.invoke(app, ["arch", "accept", "--dry-run", "--", slug])
    return result.exit_code, result.output


# --- T027: reading the list ---------------------------------------------


@pytest.mark.parametrize(
    ("value", "kinds"),
    [
        ("sequence", ("sequence",)),
        ("[data-flow, sequence]", ("data-flow", "sequence")),
        ("[ data-flow ,sequence, ]", ("data-flow", "sequence")),
        ("[]", ()),
        ("", ()),
        (None, ()),
    ],
)
def test_kinds_reads_one_kind_a_bracket_list_or_nothing(
    tmp_path: Path, value: str | None, kinds: tuple[str, ...]
) -> None:
    """`[]`, an empty value, and a missing field all read as not declared. A
    reader that took `[]` as a kind named `[]` would refuse the record for an
    unknown kind instead of asking the author to declare one."""
    _write(tmp_path, diagram=value)

    assert _read(tmp_path).kinds == kinds


def test_diagram_stays_the_verbatim_value(tmp_path: Path) -> None:
    """Doctor's unknown-kind finding quotes the value, and a one-kind record's
    existing refusal quotes it too. Normalising `diagram` would change what
    those lines print for a record that never used a list."""
    _write(tmp_path, diagram="[data-flow, sequence]")

    assert _read(tmp_path).diagram == "[data-flow, sequence]"


# --- T028: a drawing for each kind --------------------------------------


def test_a_one_kind_record_passes_drawn_directly_under_boundary(tmp_path: Path) -> None:
    _write(tmp_path, diagram="data-flow", boundary=_FLOW)
    record = _read(tmp_path)

    assert _arch.accept_blockers(record) == []
    assert _arch.kind_refusals(record) == []


def test_a_one_kind_record_passes_drawn_under_its_kind_heading(tmp_path: Path) -> None:
    """FR-010: an author who learned the `### <kind>` form from a two-kind
    record and used it on a one-kind record isn't refused for it."""
    _write(tmp_path, diagram="data-flow", boundary=f"### data-flow\n\n{_FLOW}")
    record = _read(tmp_path)

    assert _arch.accept_blockers(record) == []
    assert _arch.kind_refusals(record) == []


def test_a_two_kind_record_with_both_drawings_passes(tmp_path: Path) -> None:
    _write(tmp_path)
    record = _read(tmp_path)

    assert _arch.accept_blockers(record) == []
    assert _arch.kind_refusals(record) == []
    assert _arch.acceptable(record)


@pytest.mark.parametrize("between", ["", "### Key\n\nA solid edge is a call.\n\n"])
def test_a_kind_heading_with_no_fence_is_not_lent_the_next_kinds_drawing(
    tmp_path: Path, between: str
) -> None:
    """A subsection ends at the next `###` heading of any text, so a
    `### data-flow` with nothing under it can't reach past `### Key` and count
    the sequence drawing as its own. That swap is what the headings exist to
    catch."""
    _write(tmp_path, boundary=f"### data-flow\n\n{between}### sequence\n\n{_SEQ}")

    problems = [r.problem for r in _arch.kind_refusals(_read(tmp_path))]

    assert problems == ["declares a data-flow diagram but doesn't draw one"]


def test_a_fence_above_the_first_heading_counts_for_no_kind(tmp_path: Path) -> None:
    """In a two-kind record nothing says which kind an unheaded drawing is, so
    it can't stand in for either."""
    _write(tmp_path, boundary=f"{_FLOW}\n### sequence\n\n{_SEQ}")

    problems = [r.problem for r in _arch.kind_refusals(_read(tmp_path))]

    assert problems == ["declares a data-flow diagram but doesn't draw one"]


def test_a_kind_heading_matches_whatever_its_case(tmp_path: Path) -> None:
    _write(tmp_path, boundary=f"### Data-Flow\n\n{_FLOW}\n###  Sequence \n\n{_SEQ}")

    assert _arch.kind_refusals(_read(tmp_path)) == []


# --- T029: the refusals, as printed --------------------------------------


def test_a_missing_drawing_is_refused_with_the_kind_and_the_fix(
    agent_dir: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """SC-003: the refusal alone tells the author which drawing is missing and
    what to add, with no other reading needed."""
    root = _arch_root(agent_dir, monkeypatch)
    _write(root, boundary=f"### data-flow\n\n{_FLOW}")

    code, output = _dry_run()

    assert code == 1
    assert output == (
        "✗ a-decision declares a sequence diagram but doesn't draw one.\n"
        "  Fix: under '## Boundary', add a '### sequence' heading with a mermaid\n"
        "  sequenceDiagram, including the step that fails (an alt block or a -x message).\n"
        "\n"
        "  docs/architecture/a-decision.md\n"
    )


def test_a_repeated_kind_is_refused(
    agent_dir: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root = _arch_root(agent_dir, monkeypatch)
    _write(root, diagram="[state, state]", boundary=f"### state\n\n{_FLOW}")

    code, output = _dry_run()

    assert code == 1
    assert output == (
        "✗ a-decision declares state twice.\n"
        "  Fix: list each kind once in 'diagram:'.\n"
        "\n"
        "  docs/architecture/a-decision.md\n"
    )


def test_a_heading_for_an_undeclared_kind_is_refused(
    agent_dir: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The declaration and the drawings disagree, and wfctl can't tell which
    one the author meant, so it names both ways out."""
    root = _arch_root(agent_dir, monkeypatch)
    _write(root, boundary=f"### data-flow\n\n{_FLOW}\n### sequence\n\n{_SEQ}\n"
           f"### component\n\n{_FLOW}")

    code, output = _dry_run()

    assert code == 1
    assert output == (
        "✗ a-decision draws a '### component' heading, but 'diagram:' doesn't "
        "declare\ncomponent.\n"
        "  Fix: add component to the list, or remove the heading.\n"
        "\n"
        "  docs/architecture/a-decision.md\n"
    )


def test_an_unknown_kind_in_a_list_is_refused_by_name(
    agent_dir: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root = _arch_root(agent_dir, monkeypatch)
    _write(root, diagram="[data-flow, flow]", boundary=f"### data-flow\n\n{_FLOW}")

    code, output = _dry_run()

    assert code == 1
    assert output == (
        "✗ a-decision declares 'flow', which is not a diagram kind.\n"
        "  Fix: use data-flow, component, state, or sequence.\n"
        "\n"
        "  docs/architecture/a-decision.md\n"
    )


def test_a_two_kind_record_with_nothing_drawn_gets_one_refusal_per_kind(
    agent_dir: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The existing `no drawing` line would say the same thing a third time,
    so it's left out for a record that declares more than one kind."""
    root = _arch_root(agent_dir, monkeypatch)
    _write(root, boundary="Nothing drawn yet.\n")

    code, output = _dry_run()

    assert code == 1
    assert "no drawing" not in output
    assert "declares a data-flow diagram but doesn't draw one." in output
    assert "declares a sequence diagram but doesn't draw one." in output


def test_an_old_blocker_prints_its_block_before_the_new_refusals(
    agent_dir: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """R-013: the existing block keeps its shape and comes first, so a
    one-kind record's output doesn't change and a reader meets the familiar
    block before the new lines."""
    root = _arch_root(agent_dir, monkeypatch)
    _write(root, boundary=f"### data-flow\n\n{_FLOW}", log=False)

    code, output = _dry_run()

    assert code == 1
    assert output == (
        "✗ a-decision cannot be accepted yet.\n"
        "    no '## Log' section to append to\n"
        "✗ a-decision declares a sequence diagram but doesn't draw one.\n"
        "  Fix: under '## Boundary', add a '### sequence' heading with a mermaid\n"
        "  sequenceDiagram, including the step that fails (an alt block or a -x message).\n"
        "\n"
        "  docs/architecture/a-decision.md\n"
    )


def test_the_failure_step_rule_applies_to_the_sequence_drawing_in_a_list(
    tmp_path: Path,
) -> None:
    """FR-014: declaring a second kind isn't a way around the rule that a
    sequence drawing shows the step that fails."""
    _write(tmp_path, boundary=f"### data-flow\n\n{_FLOW}\n### sequence\n\n{_SEQ_HAPPY_ONLY}")
    record = _read(tmp_path)

    assert _arch.accept_blockers(record) == [
        "a sequence drawing with no step that fails: add an alt, opt, break "
        "or critical block, or a lost message (-x)"
    ]
    assert not _arch.acceptable(record)


def test_a_two_kind_record_with_both_drawings_passes_the_dry_run(
    agent_dir: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root = _arch_root(agent_dir, monkeypatch)
    _write(root)

    code, output = _dry_run()

    assert code == 0, output
    assert "would be accepted" in output


def test_accept_refuses_a_new_refusal_for_a_caller_that_isnt_the_cli(
    tmp_path: Path,
) -> None:
    """`accept` owns the invariant, so a caller that skips the CLI's checks
    still can't write an acceptance onto a record missing a drawing."""
    path = _write(tmp_path, boundary=f"### data-flow\n\n{_FLOW}")
    before = path.read_text()

    with pytest.raises(ValueError, match="doesn't draw one"):
        _arch.accept(_read(tmp_path), "2026-11-10", "on #738")
    assert path.read_text() == before


# --- T030: what doctor reports -------------------------------------------


def test_doctor_warns_a_proposed_record_about_each_problem(tmp_path: Path) -> None:
    """FR-015: the warning arrives while the record is still being written, so
    the refusal at acceptance isn't the first anyone hears of it."""
    _write(
        tmp_path,
        diagram="[sequence, state, state]",
        boundary=f"### state\n\n{_FLOW}\n### component\n\n{_FLOW}",
    )

    findings = [(f.level, f.message) for f in _arch.validate([_read(tmp_path)])]

    assert findings == [
        ("warning", "declares state twice"),
        ("warning", "declares a sequence diagram but doesn't draw one"),
        ("warning", "draws a '### component' heading, but 'diagram:' doesn't declare component"),
    ]


def test_doctor_checks_the_labels_in_every_drawing_of_a_list(tmp_path: Path) -> None:
    """The label check once read only the first drawing under `## Boundary`, so
    a label under the second kind's heading was never compared against the
    record. Four reviewers of #738 found it, the same gap the failure-step
    rule had before it read each kind's drawing."""
    second = "```mermaid\nflowchart LR\n  A[walrus] --> B\n```\n"
    _write(
        tmp_path,
        diagram="[data-flow, component]",
        boundary=f"### data-flow\n\n{_FLOW}\n### component\n\n{second}",
    )

    warnings = [f.message for f in _arch.validate([_read(tmp_path)]) if f.level == "warning"]

    assert warnings == ["drawing label 'walrus' appears nowhere else in the record"]


def test_doctor_says_nothing_new_about_an_accepted_record(tmp_path: Path) -> None:
    """An accepted record was ruled on by a person, and its body is frozen, so
    a warning would name work nobody will do."""
    _write(tmp_path, status="accepted", boundary=f"### data-flow\n\n{_FLOW}")

    assert _arch.validate([_read(tmp_path)]) == []


@pytest.mark.parametrize("status", ["proposed", "accepted"])
def test_an_unknown_kind_is_an_error_on_every_status_named_per_kind(
    tmp_path: Path, status: str
) -> None:
    _write(
        tmp_path, status=status, diagram="[data-flow, flow]",
        boundary=f"### data-flow\n\n{_FLOW}",
    )

    errors = [f.message for f in _arch.validate([_read(tmp_path)]) if f.level == "error"]

    assert errors == ["declares diagram 'flow', which is not a diagram kind"]


def test_doctor_prints_the_warning_in_the_existing_finding_shape(
    agent_dir: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root = _arch_root(agent_dir, monkeypatch)
    _write(root, boundary=f"### data-flow\n\n{_FLOW}")

    result = runner.invoke(app, ["doctor"])

    assert "⚠ a-decision: declares a sequence diagram but doesn't draw one\n" in result.output
