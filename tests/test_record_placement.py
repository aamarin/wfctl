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

from wfctl._arch import DOMAIN_MODEL_SECTION, LEVEL_2_SECTION, LEVEL_3_SECTION
from wfctl._paths import DESIGN_DIR, DOMAIN_DIR
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


def _adopted(root: Path) -> Path:
    """One correctly-filed level-2 record, so the tier is wfctl's to judge.

    Called by name rather than folded into `_arch_root`, because a fixture that
    granted adoption invisibly would let the gate be deleted with every test
    still passing. A tree carrying only the misfiled record is the *unadopted*
    case and is silent by design — which is what these tests would then be
    asserting the opposite of.

    Tests writing into `design/` need no call: the directory is itself one of
    the two signals, and `_write` creates it.
    """
    return _write(root, "already-adopted.md", LEVEL_2_SECTION)


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
    _adopted(root)
    _write(root, "filed-up.md", LEVEL_3_SECTION, "Considered")

    result = runner.invoke(app, ["doctor"])

    assert "filed-up.md" in result.output
    assert "projected as though it bound something" in result.output
    assert result.exit_code == 1


def test_a_level_3_record_under_design_is_silent(
    agent_dir: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The most common shape in the tree, and the one cell of the grid no other
    test here covers — 20 of this repo's 59 records were exactly this when it
    was written, and the share is why it is worth a fixture of its own.

    Every other test asserts that something is *said*. A regression that warned
    on a correctly-filed design record would leave all of them passing, and the
    corpus test only sees it because it was taught to read stdout; this sees it
    from a fixture, which is what fails on a laptop with no records checked out.
    """
    root = _arch_root(agent_dir, monkeypatch)
    _write(root, f"{DESIGN_DIR}/well-filed.md", LEVEL_3_SECTION, "Considered")

    result = runner.invoke(app, ["doctor"])

    assert "well-filed.md" not in result.output
    assert result.exit_code == 0


def test_a_record_carrying_neither_section_only_warns(
    agent_dir: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A note in the wrong drawer is not a rule that has stopped binding, and
    the two cannot share a marker: `doctor`'s exit code turns `/start-session`
    and the definition of done red."""
    root = _arch_root(agent_dir, monkeypatch)
    _adopted(root)
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
    _adopted(root)
    path = root / "illustrates.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        f"---\nstatus: proposed\n---\n\n# a record\n\n## Context\n\n"
        f"A level-2 record carries:\n\n```\n## {LEVEL_2_SECTION}\n```\n"
    )

    result = runner.invoke(app, ["doctor"])

    assert "illustrates.md" in result.output
    assert "implementation/" in result.output


def test_a_heading_parked_in_an_html_comment_does_not_satisfy_the_check(
    agent_dir: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A panel reviewer's blocker, and the case the fenced test above misses.

    Commenting a section out is how an author parks it without losing the text.
    A note whose only `Diagram` sat inside `<!-- -->` was read as a level-3
    record filed up at the root — an error row and a red exit for a file that
    had written no section at all. The `⚠` below is the right answer: it
    weighed nothing, which is what the comment says about it.

    The comment opens and closes on its own lines because that is the half that
    fires: headings match at the start of a line, so `<!-- ## Diagram -->` on
    one line never counted and was never the defect.
    """
    root = _arch_root(agent_dir, monkeypatch)
    _adopted(root)
    path = root / "parked.md"
    path.write_text(
        f"---\nstatus: proposed\n---\n\n# a note\n\n## Context\n\n"
        f"<!--\n## {LEVEL_3_SECTION}\n\nnot ready\n-->\n"
    )

    result = runner.invoke(app, ["doctor"])

    assert "parked.md" in result.output
    assert "weighed nothing" in result.output
    assert result.exit_code == 0


def test_a_domain_model_at_the_arch_root_is_sent_to_domain_not_implementation(
    agent_dir: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A domain model carries neither record heading, so before #464 the
    weighed-nothing row sent it to `implementation/` — a repair that files a
    level-2 description as a level-4 note. The row is right that it binds
    nothing and wrong about where it goes, and a check whose remedy is wrong is
    obeyed into a second misfiling."""
    root = _arch_root(agent_dir, monkeypatch)
    _adopted(root)
    _write(root, "billing.md", "Decision frame", DOMAIN_MODEL_SECTION)

    result = runner.invoke(app, ["doctor"])

    assert "billing.md" in result.output
    assert f"{DOMAIN_DIR}/" in result.output
    assert "implementation/" not in result.output
    assert result.exit_code == 0


def test_a_domain_model_parked_under_design_is_sent_to_domain(
    agent_dir: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The domain-model row is the only one of the heading rows with no tier
    guard, because neither tier this check walks is its home. That is correct
    by construction and was pinned only at the root, so a guard added here by
    analogy with the level-3 row — which *is* at home under `design/` — would
    silence the one misfiling a writer reaching for "a design document" makes
    most naturally."""
    root = _arch_root(agent_dir, monkeypatch)
    _write(root, f"{DESIGN_DIR}/billing.md", "Decision frame", DOMAIN_MODEL_SECTION)

    result = runner.invoke(app, ["doctor"])

    assert "billing.md" in result.output
    assert f"{DOMAIN_DIR}/" in result.output
    assert result.exit_code == 0


def test_implementation_notes_are_never_read_as_a_tier(
    agent_dir: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """`implementation/` is where the warning *sends* a record that weighed
    nothing. Reading it back as a tier would report every repair as a fresh
    finding, which is a check that punishes being obeyed."""
    root = _arch_root(agent_dir, monkeypatch)
    _write(root, "implementation/why-a-dataclass.md", "Context")
    _write(root, "scans/419-clarify.md", "Context")
    _write(root, f"{DOMAIN_DIR}/billing.md", DOMAIN_MODEL_SECTION)

    result = runner.invoke(app, ["doctor"])

    assert "why-a-dataclass.md" not in result.output
    assert "419-clarify.md" not in result.output
    assert "billing.md" not in result.output
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


def test_an_arch_root_that_never_adopted_the_format_is_left_alone(
    agent_dir: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """`docs/architecture` is where a project already keeps ADRs, and the
    default puts this check over all of them.

    An adr-tools record carries `Status`, `Context`, `Decision`,
    `Consequences` — none of them wfctl's — and one drawing a diagram would
    have been read as a level-3 record filed up, which is an error row. So a
    repo that installed wfctl and never wrote a record got a red
    `/start-session` over forty files it was right about. `_check_arch_records`
    states the limit for this same directory: nagged, never failed.
    """
    root = _arch_root(agent_dir, monkeypatch)
    _write(root, "0001-record-architecture-decisions.md", "Status", "Context")
    _write(root, "0002-use-postgres.md", "Status", LEVEL_3_SECTION)

    result = runner.invoke(app, ["doctor"])

    assert "0001-record-architecture-decisions.md" not in result.output
    assert "0002-use-postgres.md" not in result.output
    assert result.exit_code == 0


def test_one_sound_record_opens_the_gate_over_the_whole_root(
    agent_dir: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The gate is self-clearing, which is why it is read off the tree and not
    from a configured exemption.

    The same two ADRs as the test above, and the repo has now written one
    record of its own. Nothing about the ADRs changed; what changed is that
    this root is one wfctl's convention is in use in, so the legacy files are
    reported too. That is the cost of the gate, paid once, and the alternative
    is a repo permanently exempt from a check it has started needing.
    """
    root = _arch_root(agent_dir, monkeypatch)
    _write(root, "0002-use-postgres.md", "Status", LEVEL_3_SECTION)
    _adopted(root)

    result = runner.invoke(app, ["doctor"])

    assert "0002-use-postgres.md" in result.output
    assert result.exit_code == 1


def test_a_design_directory_alone_is_adoption(
    agent_dir: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The second of the two signals, and the one #419 needs.

    A repo whose only wfctl record is a level-2 one misfiled into `design/`
    has nothing carrying `Owns truth` at the root — so keying adoption on that
    alone would make the failure this issue was opened for the one case the
    check cannot see.
    """
    root = _arch_root(agent_dir, monkeypatch)
    _write(root, f"{DESIGN_DIR}/misfiled.md", LEVEL_2_SECTION)

    result = runner.invoke(app, ["doctor"])

    assert "misfiled.md" in result.output
    assert result.exit_code == 1


def test_the_section_constants_are_the_ones_the_templates_require() -> None:
    """The names are written in wfctl's code and in the two templates the same
    wheel ships. `required-sections-are-wfctls` already decided that shape for
    `spec.md` and `plan.md`: wfctl pins the names, and a test holds the pin
    against the document, so a rename fails the build instead of silently
    turning the check into one that finds nothing."""
    templates = {
        LEVEL_2_SECTION: _SKILLS / "architecture-decisions" / "record-template.md",
        LEVEL_3_SECTION: _SKILLS / "software-design-decisions" / "design-record-template.md",
        DOMAIN_MODEL_SECTION: _SKILLS / "model-the-domain" / "domain-model-template.md",
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
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """The gate the decision rests on, and the one a fixture cannot give.

    A check that fires on a correctly-placed record gets ignored and then
    removed, so the corpus is the evidence rather than the unit tests above —
    they only prove the predicate agrees with itself. 58 records at the time
    this was written; the assertion is on the verdict, not the count, because a
    number here would drift with every record added.

    Silence and not just `False`: the return value carries the `error` rows
    alone, so a regression that `⚠`'d every correctly-filed record would leave
    this passing. That run is what the decision's `Assumed` block names as its
    falsifier, and this is the only test positioned to see it.
    """
    repo_root = Path(__file__).resolve().parents[1]
    # Set rather than delete: deleting only clears the override, and resolution
    # then falls through to this repo's manifest and the main checkout's — both
    # gitignored and machine-local, so on a box declaring `arch_root` elsewhere
    # this asserted about another repo's records and passed for that reason.
    monkeypatch.setenv("WFCTL_ARCH_DIR", str(repo_root / "docs" / "architecture"))

    failed = _check_record_placement(repo_root)

    assert capsys.readouterr().out == ""
    assert failed is False
