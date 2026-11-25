"""Tests for accepting a record as the user's sign-off on its SVG drawing (#769).

Before #740, a record's drawing sat in its body, where the rule against
editing an accepted record covered it. An SVG under `drawings/` sits outside
the record, so anyone can change it after acceptance. Accepting a record now
writes each SVG's fingerprint on the `accepted` Log line, `wfctl doctor` warns
when a file no longer matches, and accepting again writes a `redrawn` line
that clears the warning.

Line wording is typed here rather than read from the module, because the
wording is the contract (`contracts/cli.md`).
"""
from __future__ import annotations

import hashlib
import re
from pathlib import Path

import pytest
from typer.testing import CliRunner

from wfctl.arch import _records as _arch
from wfctl.arch._drawing import fingerprint
from wfctl.cli import app

runner = CliRunner()

pytestmark = pytest.mark.usefixtures("ask_rules_installed")

_SVG = (
    '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 400 100">'
    '<text x="10" y="20">writes the file</text></svg>\n'
)
_MOVED = _SVG.replace('x="10"', 'x="20"')
_SEQUENCE_SVG = (
    '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 400 100">'
    '<text x="10" y="20">writes the file</text>'
    '<line class="arrow failing-step" x1="0" y1="0" x2="10" y2="0"/></svg>\n'
)
_FENCE = "```mermaid\nflowchart LR\n  A --> B\n```\n"
_PROPOSED_LOG = "- 2026-03-14  proposed    — x"


def _svg(root: Path, name: str = "a-data-flow.svg", text: str = _SVG) -> Path:
    path = root / "drawings" / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(text.encode())
    return path


def _record(
    root: Path,
    slug: str = "a",
    status: str = "proposed",
    *,
    diagram: str = "data-flow",
    boundary: str = "![the flow](drawings/a-data-flow.svg)\n",
    log: str = _PROPOSED_LOG,
) -> Path:
    root.mkdir(parents=True, exist_ok=True)
    path = root / f"{slug}.md"
    path.write_text(
        f"---\nstatus: {status}\ndiagram: {diagram}\n---\n\n# {slug}\n\n"
        f"## Decision\n\nThe tool writes the file.\n\n"
        f"## Boundary\n\n{boundary}\n## Log\n\n{log}\n"
    )
    return path


def _arch_root(agent_dir: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    root = agent_dir.parent / "docs" / "architecture"
    monkeypatch.setenv("WFCTL_ARCH_DIR", str(root))
    # The real accept refuses without a terminal (FR-024), and CliRunner
    # is never one.
    monkeypatch.setattr("wfctl.cli._at_terminal", lambda: True)
    return root


def _sha(text: str) -> str:
    return hashlib.sha256(text.encode()).hexdigest()[:12]


def _warnings(root: Path) -> list[str]:
    return [f.message for f in _arch.validate(_arch.load_records(root))]


def _accept(slug: str = "a", agreed: str = "the walkthrough") -> str:
    result = runner.invoke(app, ["arch", "accept", slug, "--agreed", agreed])
    assert result.exit_code == 0, result.output
    return result.output


def _log_lines(path: Path) -> list[str]:
    return [line for line in path.read_text().splitlines() if line.startswith("- ")]


# --- the fingerprint on the accepted line (T030) ------------------------------


def test_the_accepted_line_ends_with_the_svgs_link_and_fingerprint(
    agent_dir: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The fingerprint says which version of the drawing the user agreed to.
    Without it, doctor has nothing to compare the file against later."""
    root = _arch_root(agent_dir, monkeypatch)
    _svg(root)
    path = _record(root)

    _accept()

    assert _log_lines(path)[-1].endswith(
        f"accepted    — the walkthrough · drawing drawings/a-data-flow.svg sha256:{_sha(_SVG)}"
    )


def test_a_multi_kind_record_gets_one_fingerprint_per_svg_in_heading_order(
    agent_dir: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Heading order, so the line reads in the same order as the record and
    a reader can match each fingerprint to the drawing above it."""
    root = _arch_root(agent_dir, monkeypatch)
    _svg(root, "a-state.svg", _MOVED)
    _svg(root, "a-data-flow.svg")
    path = _record(
        root,
        diagram="[state, data-flow]",
        boundary=(
            "### state\n\n![s](drawings/a-state.svg)\n\n"
            "### data-flow\n\n![d](drawings/a-data-flow.svg)\n"
        ),
    )

    _accept()

    assert _log_lines(path)[-1].endswith(
        f" · drawing drawings/a-state.svg sha256:{_sha(_MOVED)}"
        f" · drawing drawings/a-data-flow.svg sha256:{_sha(_SVG)}"
    )


def test_a_fence_records_accepted_line_is_unchanged(
    agent_dir: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A fence sits in the record's body, which the frozen-body rule already
    covers, so its line has nothing to add and keeps today's shape."""
    root = _arch_root(agent_dir, monkeypatch)
    path = _record(root, boundary=_FENCE)

    _accept()

    assert re.fullmatch(r"- \d{4}-\d{2}-\d{2}  accepted    — the walkthrough", _log_lines(path)[-1])


def test_crlf_and_lf_copies_of_one_svg_get_the_same_fingerprint(tmp_path: Path) -> None:
    """Git's `core.autocrlf` can rewrite line endings on checkout. Hashing
    the raw bytes would warn about a drawing nobody changed."""
    lf = tmp_path / "lf.svg"
    crlf = tmp_path / "crlf.svg"
    lf.write_bytes(b"<svg>\n<text>a</text>\n</svg>\n")
    crlf.write_bytes(b"<svg>\r\n<text>a</text>\r\n</svg>\r\n")

    assert fingerprint(lf) == fingerprint(crlf)
    assert re.fullmatch(r"[0-9a-f]{12}", fingerprint(lf))


# --- doctor's warning (T031) ---------------------------------------------------


def _accepted(root: Path, svg_text: str = _SVG, **kw: object) -> Path:
    """An accepted record whose Log carries the fingerprint of `svg_text`."""
    log = (
        f"{_PROPOSED_LOG}\n- 2026-11-20  accepted    — the walkthrough · drawing "
        f"drawings/a-data-flow.svg sha256:{_sha(svg_text)}"
    )
    return _record(root, status="accepted", log=log, **kw)  # type: ignore[arg-type]


_CHANGED = (
    "drawing drawings/a-data-flow.svg changed since it was accepted — look at it, "
    'then run wfctl arch accept --agreed "<where>" -- a'
)


def test_the_warning_quotes_a_slug_a_person_would_paste(tmp_path: Path) -> None:
    """The security panel on #769 found the remedy printing the slug bare,
    while the design gate's remedy for the same command quotes it and puts it
    after `--`. A slug is a file name, so a space or a leading `-` would split
    or turn into a flag when the line is pasted."""
    from wfctl import arch as _arch

    _svg(tmp_path, text=_MOVED)
    path = _accepted(tmp_path)
    odd = path.with_name("-x y.md")
    path.rename(odd)

    findings = _arch.validate(_arch.load_records(tmp_path), None)

    assert any("-- '-x y'" in f.message for f in findings), findings


def test_doctor_warns_when_an_accepted_records_svg_changed(tmp_path: Path) -> None:
    """The warning is the point of the fingerprint. Without it, an edit
    nobody looked at would replace the drawing the user agreed to."""
    _svg(tmp_path, text=_MOVED)
    _accepted(tmp_path)

    assert _warnings(tmp_path) == [_CHANGED]


def test_doctor_is_quiet_when_the_svg_matches_its_fingerprint(tmp_path: Path) -> None:
    _svg(tmp_path)
    _accepted(tmp_path)

    assert _warnings(tmp_path) == []


def test_doctor_is_quiet_when_no_log_line_names_the_svg(tmp_path: Path) -> None:
    """A record accepted before fingerprints existed carries none. Warning
    there would flag every such record for a drawing nobody changed."""
    _svg(tmp_path, text=_MOVED)
    _record(tmp_path, status="accepted", log=f"{_PROPOSED_LOG}\n- 2026-11-20  accepted    — x")

    assert _warnings(tmp_path) == []


def test_doctor_reads_the_last_line_naming_the_svg(tmp_path: Path) -> None:
    """A `redrawn` line signs off the new drawing. Reading the first line
    instead would keep warning after the user signed off."""
    _svg(tmp_path, text=_MOVED)
    log = (
        f"{_PROPOSED_LOG}\n"
        f"- 2026-11-20  accepted    — x · drawing drawings/a-data-flow.svg sha256:{_sha(_SVG)}\n"
        f"- 2026-11-21  redrawn     — y · drawing drawings/a-data-flow.svg sha256:{_sha(_MOVED)}"
    )
    _record(tmp_path, status="accepted", log=log)

    assert _warnings(tmp_path) == []


def test_a_citation_holding_the_drawing_marker_still_reads_the_right_link(
    tmp_path: Path,
) -> None:
    """The citation is free text a person writes, and the sign-off pattern
    matches from the first ` · drawing ` it meets. Read as the link, a
    citation holding one left doctor quiet about a changed SVG."""
    _svg(tmp_path, text=_MOVED)
    log = (
        f"{_PROPOSED_LOG}\n- 2026-11-20  accepted    — see · drawing review thread · drawing "
        f"drawings/a-data-flow.svg sha256:{_sha(_SVG)}"
    )
    _record(tmp_path, status="accepted", log=log)

    assert _warnings(tmp_path) == [_CHANGED]


def test_doctor_warns_about_an_accepted_records_drawing_problem(tmp_path: Path) -> None:
    """A deleted SVG leaves an accepted record pointing at nothing. The
    problem line names it, and no fingerprint comparison runs on top."""
    _accepted(tmp_path)

    assert _warnings(tmp_path) == ["drawing links drawings/a-data-flow.svg, which doesn't exist"]


@pytest.mark.parametrize("status", ["superseded", "retired"])
def test_doctor_is_quiet_about_an_ended_records_drawing(tmp_path: Path, status: str) -> None:
    """An ended record's drawing no longer binds anything, so a warning
    would name work nobody will do."""
    _svg(tmp_path, text=_MOVED)
    log = (
        f"{_PROPOSED_LOG}\n"
        f"- 2026-11-20  accepted    — x · drawing drawings/a-data-flow.svg sha256:{_sha(_SVG)}"
    )
    _record(tmp_path, status=status, log=log)

    assert [w for w in _warnings(tmp_path) if "drawing" in w] == []


# --- the redraw (T032) ---------------------------------------------------------


def test_accepting_a_changed_record_appends_a_redrawn_line_and_clears_the_warning(
    agent_dir: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The warning needs a way to clear, or it becomes noise the user learns
    to ignore. A redraw keeps the status and the original acceptance date,
    since the decision didn't change."""
    root = _arch_root(agent_dir, monkeypatch)
    _svg(root, text=_MOVED)
    path = _accepted(root)
    before = path.read_text()

    output = _accept(agreed="layout check")

    assert "✓ a: drawing signed off" in output
    lines = _log_lines(path)
    assert re.fullmatch(
        r"- \d{4}-\d{2}-\d{2}  redrawn     — layout check · drawing "
        rf"drawings/a-data-flow\.svg sha256:{_sha(_MOVED)}",
        lines[-1],
    )
    assert lines[-1] in output
    record = _arch.parse_record(path)
    assert record.status == "accepted"
    assert _arch.accepted_on(record) == "2026-11-20"
    assert path.read_text().startswith(before.rstrip("\n"))
    assert _warnings(root) == []


def test_a_redraw_writes_the_line_for_an_svg_with_no_fingerprint(
    agent_dir: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A record accepted before fingerprints existed gets one by accepting
    again. Otherwise its drawing could never be signed off."""
    root = _arch_root(agent_dir, monkeypatch)
    _svg(root)
    path = _record(root, status="accepted", log=f"{_PROPOSED_LOG}\n- 2026-11-20  accepted    — x")

    _accept()

    assert _log_lines(path)[-1].endswith(f"sha256:{_sha(_SVG)}")
    assert " redrawn " in _log_lines(path)[-1]


def test_a_redraw_is_refused_when_the_sequence_svg_dropped_its_failing_step(
    agent_dir: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A redraw reruns every acceptance check. Otherwise a layout fix could
    drop the failing step that acceptance required, and the sign-off would
    approve a drawing acceptance refuses."""
    root = _arch_root(agent_dir, monkeypatch)
    _svg(root, text=_SVG)
    path = _accepted(root, svg_text=_SEQUENCE_SVG, diagram="sequence")
    before = path.read_text()

    result = runner.invoke(app, ["arch", "accept", "a", "--agreed", "x"])

    assert result.exit_code == 1
    assert 'a sequence drawing with no step that fails: add class="failing-step"' in result.output
    assert path.read_text() == before


def test_accepting_a_matching_record_refuses_as_it_did_before(
    agent_dir: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A second `accepted` or `redrawn` line with nothing changed would claim
    a sign-off nobody needed, so the old refusal still applies."""
    root = _arch_root(agent_dir, monkeypatch)
    _svg(root)
    path = _accepted(root)
    before = path.read_text()

    result = runner.invoke(app, ["arch", "accept", "a", "--agreed", "x"])

    assert result.exit_code == 1
    assert "a is already accepted (2026-11-20). Nothing to do." in result.output
    assert path.read_text() == before


def test_a_dry_run_on_a_changed_record_says_it_would_sign_off_and_writes_nothing(
    agent_dir: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The agent's only form of the command is the dry run, so it has to say
    which row the real run would take."""
    root = _arch_root(agent_dir, monkeypatch)
    _svg(root, text=_MOVED)
    path = _accepted(root)
    before = path.read_text()

    result = runner.invoke(app, ["arch", "accept", "--dry-run", "--", "a"])

    assert result.exit_code == 0, result.output
    assert "a: drawing would be signed off — dry run, nothing written." in result.output
    assert path.read_text() == before


def test_a_redraw_with_no_terminal_under_claude_code_cites_the_prompt(
    agent_dir: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A redraw signs off a new drawing the same way an accept signs off the
    first one, so the user's yes at the prompt stands in for the citation."""
    root = _arch_root(agent_dir, monkeypatch)
    monkeypatch.setattr("wfctl.cli._at_terminal", lambda: False)
    monkeypatch.setenv("CLAUDECODE", "1")
    _svg(root, text=_MOVED)
    path = _accepted(root)

    result = runner.invoke(app, ["arch", "accept", "a"])

    assert result.exit_code == 0, result.output
    assert "✓ a: drawing signed off" in result.output
    assert "  redrawn     — approved at the permission prompt · drawing " in _log_lines(path)[-1]
