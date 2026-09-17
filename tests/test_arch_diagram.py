"""Tests for `Record.diagram` and the declared-kind vocabulary (#109).

`status` and `diagram` share a parser but not a normalisation rule: an
unrecognised status excludes the record from the projection, and an
unrecognised diagram has no safe direction to fold into, so it survives
parsing verbatim and VR-006 is what names it (data-model.md, R-001).
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


def test_the_three_kinds_are_the_ones_the_template_names() -> None:
    """FR-012's vocabulary is `wfctl`'s own, held against the template
    elsewhere (T020) — this pins the constant itself so that test has
    something fixed to compare against."""
    assert _arch.DIAGRAM_KINDS == ("data-flow", "component", "state")


@pytest.mark.parametrize("kind", ["data-flow", "component", "state"])
def test_a_declared_kind_is_read_back(tmp_path: Path, kind: str) -> None:
    """FR-001: the author's own value comes back unchanged."""
    path = _write(
        tmp_path, "a-decision", f"---\nstatus: proposed\ndiagram: {kind}\n---\n\n# X\n"
    )

    assert _arch.parse_record(path).diagram == kind


def test_an_absent_diagram_reads_as_empty_not_a_default(tmp_path: Path) -> None:
    """FR-002. A record written before this feature declares no kind, and
    nothing here should make it look like it declared one."""
    path = _write(tmp_path, "a-decision", "---\nstatus: proposed\n---\n\n# X\n")

    assert _arch.parse_record(path).diagram == ""


def test_a_value_outside_the_set_survives_parsing_verbatim(tmp_path: Path) -> None:
    """The behaviour that differs from `status`. Folding `dataflow` to `""`
    would report "declares no kind" against a file whose author wrote the
    key — a true sentence about the wrong problem."""
    path = _write(
        tmp_path, "a-decision", "---\nstatus: proposed\ndiagram: dataflow\n---\n\n# X\n"
    )

    record = _arch.parse_record(path)

    assert record.diagram == "dataflow"
    assert record.status == "proposed"  # unaffected — a different key entirely


# --- VR-006 (T019) -----------------------------------------------------------


def test_an_unrecognised_diagram_is_an_error_finding(tmp_path: Path) -> None:
    """VR-003's shape reused for a fourth kind of malformed record: the value
    is wrong, and a reader has to be told which value and where."""
    path = _write(
        tmp_path, "a-decision", "---\nstatus: proposed\ndiagram: dataflow\n---\n\n# X\n"
    )
    record = _arch.parse_record(path)

    findings = _arch.validate([record])

    assert any(
        f.level == "error" and f.slug == "a-decision" and "dataflow" in f.message
        for f in findings
    )


def test_an_absent_diagram_is_not_a_vr006_finding(tmp_path: Path) -> None:
    """"" is "not declared", not "declared wrong" — VR-006 names a value the
    author wrote, not the absence of one (which `accept_blockers` covers)."""
    path = _write(tmp_path, "a-decision", "---\nstatus: proposed\n---\n\n# X\n")

    findings = _arch.validate([_arch.parse_record(path)])

    assert findings == []


@pytest.mark.parametrize("kind", ["data-flow", "component", "state"])
def test_a_recognised_diagram_is_not_a_vr006_finding(tmp_path: Path, kind: str) -> None:
    path = _write(
        tmp_path, "a-decision", f"---\nstatus: proposed\ndiagram: {kind}\n---\n\n# X\n"
    )

    findings = _arch.validate([_arch.parse_record(path)])

    assert findings == []


def test_vr006_fires_on_an_accepted_record_too(tmp_path: Path) -> None:
    """VR-005 freezes an accepted record's body; it does not freeze its
    frontmatter against a check that reads the frontmatter, and a misspelled
    kind is wrong whatever the status."""
    path = _write(
        tmp_path, "a-decision", "---\nstatus: accepted\ndiagram: dataflow\n---\n\n# X\n"
    )

    findings = _arch.validate([_arch.parse_record(path)])

    assert any(f.level == "error" and f.slug == "a-decision" for f in findings)
