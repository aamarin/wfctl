"""Tests for the drawing gate at acceptance (#109, User Story 1).

`test_arch_accept.py` covers the console surface of `accept` as it stood
before this feature; these cover the new refusal and what it changes about
`acceptable`. A record with a drawing and a declared kind accepts exactly as
one with neither section ever existed, which is what the second scenario
below is for — a regression here would be silent otherwise.
"""
from __future__ import annotations

from pathlib import Path

import pytest
from typer.testing import CliRunner

from wfctl import _arch
from wfctl.cli import app

runner = CliRunner()

_BOUNDARY = (
    "## Boundary\n\n```mermaid\nflowchart LR\n  A --> B\n```\n\n"
)


def _record(
    root: Path,
    slug: str,
    status: str = "proposed",
    *,
    diagram: str = "",
    boundary: str = "",
    log: str = "- 2026-03-14  proposed    — x",
) -> Path:
    root.mkdir(parents=True, exist_ok=True)
    path = root / f"{slug}.md"
    front = f"---\nstatus: {status}\n"
    if diagram:
        front += f"diagram: {diagram}\n"
    front += "---\n\n"
    path.write_text(f"{front}# {slug}\n\n{boundary}## Log\n\n{log}\n")
    return path


def _arch_root(agent_dir: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    root = agent_dir.parent / "docs" / "architecture"
    monkeypatch.setenv("WFCTL_ARCH_DIR", str(root))
    return root


# --- scenario 1: no drawing, refused, file unchanged --------------------


def test_a_record_with_no_drawing_is_refused_and_the_file_is_unchanged(
    agent_dir: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root = _arch_root(agent_dir, monkeypatch)
    path = _record(root, "a-decision")
    before = path.read_text()

    result = runner.invoke(app, ["arch", "accept", "a-decision", "--agreed", "on #109"])

    assert result.exit_code == 1
    assert "no drawing" in result.output
    assert path.read_text() == before


# --- scenario 2: a drawing and a kind accepts as it does today ----------


def test_a_record_with_a_drawing_and_a_kind_accepts(
    agent_dir: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root = _arch_root(agent_dir, monkeypatch)
    _record(root, "a-decision", diagram="state", boundary=_BOUNDARY)

    result = runner.invoke(app, ["arch", "accept", "a-decision", "--agreed", "on #109"])

    assert result.exit_code == 0
    assert "a-decision is accepted" in result.output


# --- scenario 3: an accepted record with no drawing is never re-read -----


def test_an_accepted_record_with_no_drawing_is_never_touched(
    agent_dir: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """FR-006, SC-002. The five records accepted before this feature existed
    carry no `## Boundary`, and the gate must not reach for them."""
    root = _arch_root(agent_dir, monkeypatch)
    path = _record(root, "already-in-force", status="accepted", log="- 2026-01-01  accepted    — x")
    before = path.read_text()

    assert _arch.acceptable(_arch.parse_record(path)) is False

    result = runner.invoke(app, ["arch", "accept", "already-in-force", "--agreed", "x"])

    assert result.exit_code == 1
    assert "already accepted" in result.output
    assert "drawing" not in result.output
    assert path.read_text() == before


# --- scenario 4: the promotable listing excludes a record accept would refuse --


def test_the_promotable_listing_excludes_a_record_with_no_drawing(
    agent_dir: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """FR-007. The listing's own suggested command must not fail."""
    root = _arch_root(agent_dir, monkeypatch)
    _record(root, "no-drawing")
    _record(root, "has-drawing", diagram="state", boundary=_BOUNDARY)

    result = runner.invoke(app, ["arch", "accept"])

    assert "has-drawing" in result.output
    assert "no-drawing" not in result.output


# --- the two kind refusals (T011) ----------------------------------------


def test_a_drawing_with_no_declared_kind_is_refused_and_names_the_three_values(
    agent_dir: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root = _arch_root(agent_dir, monkeypatch)
    path = _record(root, "a-decision", boundary=_BOUNDARY)
    before = path.read_text()

    result = runner.invoke(app, ["arch", "accept", "a-decision", "--agreed", "on #109"])

    assert result.exit_code == 1
    assert "no declared kind" in result.output
    for kind in _arch.DIAGRAM_KINDS:
        assert kind in result.output
    assert path.read_text() == before


def test_a_kind_outside_the_set_is_refused_and_names_the_three_values(
    agent_dir: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root = _arch_root(agent_dir, monkeypatch)
    path = _record(root, "a-decision", diagram="dataflow", boundary=_BOUNDARY)
    before = path.read_text()

    result = runner.invoke(app, ["arch", "accept", "a-decision", "--agreed", "on #109"])

    assert result.exit_code == 1
    assert "'dataflow' is not a diagram kind" in result.output
    for kind in _arch.DIAGRAM_KINDS:
        assert kind in result.output
    assert path.read_text() == before


def test_a_record_with_no_drawing_and_no_kind_reports_the_drawing_first(
    agent_dir: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """FR-005. Adding a kind to a record with nothing drawn fixes nothing, so
    the ordering the reader sees has to put the drawing first."""
    root = _arch_root(agent_dir, monkeypatch)
    _record(root, "a-decision")

    result = runner.invoke(app, ["arch", "accept", "a-decision", "--agreed", "on #109"])

    drawing_at = result.output.index("no drawing")
    kind_at = result.output.index("no declared kind")
    assert drawing_at < kind_at
