"""Tests for `wfctl arch accept <slug> --dry-run` (#498, User Story 2).

The dry run is the fix line the design gate hands back, so it has to say exactly
what `accept` would say. Most tests here compare the two commands' output rather
than asserting a sentence: the promise is that the rehearsal and the real thing
agree, and a copied sentence would keep passing after they stopped agreeing.
"""
from __future__ import annotations

from pathlib import Path

import pytest
from typer.testing import CliRunner

from wfctl import _arch
from tests.conftest import write_record
from wfctl.cli import app

runner = CliRunner()

_BOUNDARY = "## Boundary\n\n```mermaid\nflowchart LR\n  A --> B\n```\n\n"


def _arch_root(agent_dir: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    root = agent_dir.parent / "docs" / "architecture"
    monkeypatch.setenv("WFCTL_ARCH_DIR", str(root))
    return root


def _tree(root: Path) -> dict[Path, bytes]:
    return {p: p.read_bytes() for p in sorted(root.rglob("*")) if p.is_file()}


def test_a_dry_run_lists_every_blocker_in_order_and_exits_1(
    agent_dir: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A record with no drawing and no kind has two blockers, and an author fixing
    them one run at a time would meet the second only after the first. The output
    is `accept`'s own, line for line."""
    root = _arch_root(agent_dir, monkeypatch)
    record = write_record(root, "a-decision")
    blockers = _arch.accept_blockers(next(iter(_arch.load_records(root))))
    assert len(blockers) == 2, "guards the premise: two blockers to order"

    dry = runner.invoke(app, ["arch", "accept", "a-decision", "--dry-run"])
    real = runner.invoke(app, ["arch", "accept", "a-decision", "--agreed", "on #498"])

    assert dry.exit_code == 1
    assert dry.output.index(blockers[0]) < dry.output.index(blockers[1])
    assert dry.output == real.output
    assert record.read_text().startswith("---\nstatus: proposed\n")


def test_a_dry_run_of_a_passing_record_exits_0_without_a_citation(
    agent_dir: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The rehearsal runs before anyone has agreed to anything, so asking for a
    citation would refuse the one run the design gate sends an author to make."""
    root = _arch_root(agent_dir, monkeypatch)
    write_record(root, "a-decision", diagram="component", boundary=_BOUNDARY)

    result = runner.invoke(app, ["arch", "accept", "a-decision", "--dry-run"])

    assert result.exit_code == 0
    assert "✓ a-decision would be accepted — dry run, nothing written." in result.output


def test_a_dry_run_writes_nothing_whether_it_passes_or_fails(
    agent_dir: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A rehearsal that wrote a status or a log line would be an acceptance nobody
    agreed to, which is the transition `a-human-accepts-a-decision` keeps for a
    person. The whole arch root is compared, not one file, so a stray write
    anywhere under it shows up."""
    root = _arch_root(agent_dir, monkeypatch)
    write_record(root, "a-failing")
    write_record(root, "a-passing", diagram="component", boundary=_BOUNDARY)
    before = _tree(root)

    failing = runner.invoke(app, ["arch", "accept", "a-failing", "--dry-run"])
    passing = runner.invoke(
        app, ["arch", "accept", "a-passing", "--dry-run", "--agreed", "on #498"]
    )

    assert (failing.exit_code, passing.exit_code) == (1, 0)
    assert _tree(root) == before


@pytest.mark.parametrize("status", ["accepted", "rejected", "superseded", "retired"])
def test_a_dry_run_of_a_record_that_is_not_proposed_refuses_as_accept_does(
    agent_dir: Path, monkeypatch: pytest.MonkeyPatch, status: str
) -> None:
    """Each status gets its own sentence from `accept`, since the next action
    differs by status. A dry run that said "would be accepted" of an accepted
    record would send the author to run a command that then refuses."""
    root = _arch_root(agent_dir, monkeypatch)
    write_record(root, "a-decision", status, diagram="component", boundary=_BOUNDARY)

    dry = runner.invoke(app, ["arch", "accept", "a-decision", "--dry-run"])
    real = runner.invoke(app, ["arch", "accept", "a-decision", "--agreed", "on #498"])

    assert dry.exit_code == 1
    assert dry.output == real.output


@pytest.mark.parametrize("slug", ["", "a-decisoin", "nothing-like-it"])
def test_a_dry_run_with_no_slug_or_an_unknown_one_refuses_as_accept_does(
    agent_dir: Path, monkeypatch: pytest.MonkeyPatch, slug: str
) -> None:
    """The three refusals that come before any record is found: no slug, a near
    miss with suggestions, and a slug close to nothing with the listing."""
    root = _arch_root(agent_dir, monkeypatch)
    write_record(root, "a-decision", diagram="component", boundary=_BOUNDARY)

    dry = runner.invoke(app, ["arch", "accept", slug, "--dry-run"])
    real = runner.invoke(app, ["arch", "accept", slug, "--agreed", "on #498"])

    assert dry.exit_code == 1
    assert dry.output == real.output


@pytest.mark.parametrize("agreed", ["<where>", "on #498\nand elsewhere", "   "])
def test_a_dry_run_refuses_a_citation_accept_would_refuse(
    agent_dir: Path, monkeypatch: pytest.MonkeyPatch, agreed: str
) -> None:
    """A citation is optional under `--dry-run` and still checked when given. A
    rehearsal that took `<where>` would pass the author straight into a refusal on
    the real run, which is the disagreement the dry run exists to rule out. A
    blank citation is one the rehearsal once took, reading it as no citation."""
    root = _arch_root(agent_dir, monkeypatch)
    write_record(root, "a-decision", diagram="component", boundary=_BOUNDARY)

    dry = runner.invoke(app, ["arch", "accept", "a-decision", "--dry-run", "--agreed", agreed])
    real = runner.invoke(app, ["arch", "accept", "a-decision", "--agreed", agreed])

    assert dry.exit_code == 1
    assert dry.output == real.output
