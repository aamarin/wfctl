"""What `doctor` says about a record filed at the wrong level (#419).

The rule was prose in `software-design-decisions` and a line on a checklist,
and it names the failure in its own words: a binding decision filed under
`design/` is invisible to `wfctl arch context`, so it binds nothing while
looking like it does. Nothing verified it, and nothing could — `load_records`
globs one level, so the misfiled record is not reported wrong by any existing
reader, it is simply absent.

The half that cannot be written as a fixture is the one that matters most: a
check firing on correctly-placed records gets ignored and then removed. So the
last test here runs the real thing over this repository's own arch root, which
is the gate `doctor-owns-the-placement-verdict` rests on.
"""
from __future__ import annotations

from importlib.resources import files
from pathlib import Path

import pytest
from typer.testing import CliRunner

from wfctl._arch import LEVEL_2_SECTION, LEVEL_3_SECTION
from wfctl._paths import DESIGN_DIR
from wfctl.cli import _check_record_placement, app


runner = CliRunner()

_SKILLS = Path(str(files("wfctl"))) / "agents" / "skills"


def _arch_root(agent_dir: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    root = agent_dir.parent / "docs" / "architecture"
    monkeypatch.setenv("WFCTL_ARCH_DIR", str(root))
    return root


def _write(root: Path, name: str, *sections: str) -> Path:
    """One record carrying exactly `sections`, in the tier `name` names."""
    path = root / name
    path.parent.mkdir(parents=True, exist_ok=True)
    body = "".join(f"## {s}\n\nprose\n\n" for s in sections)
    path.write_text(f"---\nstatus: proposed\n---\n\n# a record\n\n{body}")
    return path


def test_a_level_2_record_under_design_is_an_error(
    agent_dir: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The failure #419 was opened for. It has no symptom otherwise: the record
    is not reported wrong by `arch context`, it is missing from it."""
    root = _arch_root(agent_dir, monkeypatch)
    _write(root, f"{DESIGN_DIR}/misfiled.md", LEVEL_2_SECTION, "Considered")

    result = runner.invoke(app, ["doctor"])

    assert "misfiled.md" in result.output
    assert "binds nothing" in result.output
    assert result.exit_code == 1


def test_a_level_3_record_at_the_arch_root_is_an_error(
    agent_dir: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The mirror of #419, which the issue does not mention. Filing down hides
    a record; filing up publishes one, so `arch context` projects a design note
    as though it bound something."""
    root = _arch_root(agent_dir, monkeypatch)
    _write(root, "filed-up.md", LEVEL_3_SECTION, "Considered")

    result = runner.invoke(app, ["doctor"])

    assert "filed-up.md" in result.output
    assert "projected as though it bound something" in result.output
    assert result.exit_code == 1


def test_a_record_carrying_neither_section_only_warns(
    agent_dir: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A note in the wrong drawer is not a rule that has stopped binding, and
    the two cannot share a marker: `doctor`'s exit code turns `/start-session`
    and the definition of done red."""
    root = _arch_root(agent_dir, monkeypatch)
    _write(root, "just-a-note.md", "Context", "Considered")

    result = runner.invoke(app, ["doctor"])

    assert "just-a-note.md" in result.output
    assert "implementation/" in result.output
    assert result.exit_code == 0


def test_a_record_carrying_both_sections_is_read_as_level_2(
    agent_dir: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The case the first draft of the record left undecided. Asking
    `Owns truth` first settles it without a fourth finding — at the root the
    file is where it belongs, and a `Diagram` beside a decision that owns
    something is decoration."""
    root = _arch_root(agent_dir, monkeypatch)
    _write(root, "owns-and-draws.md", LEVEL_2_SECTION, LEVEL_3_SECTION)

    result = runner.invoke(app, ["doctor"])

    assert "owns-and-draws.md" not in result.output
    assert result.exit_code == 0


def test_a_record_carrying_both_sections_under_design_is_still_an_error(
    agent_dir: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The other half of asking `Owns truth` first, and the half that would be
    lost by treating the two sections as an exclusive pair: the `Diagram` does
    not excuse the tier."""
    root = _arch_root(agent_dir, monkeypatch)
    _write(root, f"{DESIGN_DIR}/owns-and-draws.md", LEVEL_2_SECTION, LEVEL_3_SECTION)

    result = runner.invoke(app, ["doctor"])

    assert "owns-and-draws.md" in result.output
    assert result.exit_code == 1


def test_a_heading_illustrated_in_a_fenced_block_does_not_satisfy_the_check(
    agent_dir: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Every record here quotes the rules it is checked against — this file's
    own subject is the two heading names — so a document that *documents* a
    heading must not read as carrying one. That is what `quoted_out` is in the
    path for, and a local regex would have dropped it."""
    root = _arch_root(agent_dir, monkeypatch)
    path = root / "illustrates.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        f"---\nstatus: proposed\n---\n\n# a record\n\n## Context\n\n"
        f"A level-2 record carries:\n\n```\n## {LEVEL_2_SECTION}\n```\n"
    )

    result = runner.invoke(app, ["doctor"])

    assert "illustrates.md" in result.output
    assert "implementation/" in result.output


def test_implementation_notes_are_never_read_as_a_tier(
    agent_dir: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """`implementation/` is where the warning *sends* a record that weighed
    nothing. Reading it back as a tier would report every repair as a fresh
    finding, which is a check that punishes being obeyed."""
    root = _arch_root(agent_dir, monkeypatch)
    _write(root, "implementation/why-a-dataclass.md", "Context")
    _write(root, "scans/419-clarify.md", "Context")

    result = runner.invoke(app, ["doctor"])

    assert "why-a-dataclass.md" not in result.output
    assert "419-clarify.md" not in result.output
    assert result.exit_code == 0


def test_an_undecodable_record_does_not_take_down_the_tier(
    agent_dir: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """`parse_record`'s rule, for its reason: a record root is a directory
    anyone can drop a file into, and one unreadable file must not stop the
    misfiled one beside it from being reported."""
    root = _arch_root(agent_dir, monkeypatch)
    root.mkdir(parents=True, exist_ok=True)
    (root / "binary.md").write_bytes(b"\xff\xfe\x00 not utf-8")
    _write(root, f"{DESIGN_DIR}/misfiled.md", LEVEL_2_SECTION)

    result = runner.invoke(app, ["doctor"])

    assert "misfiled.md" in result.output
    assert result.exit_code == 1


def test_an_absent_design_directory_is_not_a_finding(
    agent_dir: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A repo has no design records until it writes its first one, and most
    repos with an arch root have no `design/` at all."""
    root = _arch_root(agent_dir, monkeypatch)
    _write(root, "sound.md", LEVEL_2_SECTION)

    result = runner.invoke(app, ["doctor"])

    assert "sound.md" not in result.output
    assert result.exit_code == 0


def test_the_section_constants_are_the_ones_the_templates_require() -> None:
    """The names are written in wfctl's code and in the two templates the same
    wheel ships. `required-sections-are-wfctls` already decided that shape for
    `spec.md` and `plan.md`: wfctl pins the names, and a test holds the pin
    against the document, so a rename fails the build instead of silently
    turning the check into one that finds nothing."""
    templates = {
        LEVEL_2_SECTION: _SKILLS / "architecture-decisions" / "record-template.md",
        LEVEL_3_SECTION: _SKILLS / "software-design-decisions" / "design-record-template.md",
    }
    for section, template in templates.items():
        assert f"\n## {section}\n" in template.read_text(), (
            f"{template.name} no longer carries `## {section}`"
        )


def test_each_template_carries_its_own_section_and_not_the_others() -> None:
    """The split is what makes the tier readable from the file. Were both
    templates to carry both headings the check would still run, still pass its
    unit tests, and classify every record as level 2."""
    level_2 = (_SKILLS / "architecture-decisions" / "record-template.md").read_text()
    level_3 = (
        _SKILLS / "software-design-decisions" / "design-record-template.md"
    ).read_text()

    assert f"\n## {LEVEL_3_SECTION}\n" not in level_2
    assert f"\n## {LEVEL_2_SECTION}\n" not in level_3


@pytest.mark.skipif(
    not (Path(__file__).resolve().parents[1] / "docs" / "architecture").is_dir(),
    reason="run from a checkout that carries wfctl's own architecture records",
)
def test_this_repositorys_own_records_produce_no_placement_finding(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The gate the decision rests on, and the one a fixture cannot give.

    A check that fires on a correctly-placed record gets ignored and then
    removed, so the corpus is the evidence rather than the unit tests above —
    they only prove the predicate agrees with itself. 58 records at the time
    this was written; the assertion is on the verdict, not the count, because a
    number here would drift with every record added.
    """
    repo_root = Path(__file__).resolve().parents[1]
    # Delete rather than pop: an ambient `WFCTL_ARCH_DIR` would point this at
    # some other repo's records and the test would pass for the wrong reason.
    monkeypatch.delenv("WFCTL_ARCH_DIR", raising=False)

    assert _check_record_placement(repo_root) is False
