"""Tests for `wfctl._contexts` — the context names, and the branch's list of them."""
from __future__ import annotations

from pathlib import Path

from wfctl import _arch, _contexts, _design_exceptions


def _page(arch: Path, stem: str, *header: str, state: str = "accepted") -> None:
    domain = arch / "domain"
    domain.mkdir(parents=True, exist_ok=True)
    lines = [f"# {stem}", "", f"State: {state}", *header, "", "## Body", "", "text"]
    (domain / f"{stem}.md").write_text("\n".join(lines) + "\n")


# --- names ------------------------------------------------------------------


def test_names_combines_the_contexts_and_outside_parties_lines(tmp_path: Path) -> None:
    """A record can govern either kind, so the two lines read as one list."""
    _page(tmp_path, "wfctl", "Contexts: a, b", "Outside parties: workmux")

    assert _contexts.names(tmp_path) == frozenset({"a", "b", "workmux"})


def test_names_ignores_a_page_that_is_not_accepted(tmp_path: Path) -> None:
    """A page nobody accepted is a draft, and a draft's names would start
    pausing branches."""
    _page(tmp_path, "wfctl", "Contexts: a", state="proposed")

    assert _contexts.names(tmp_path) is None


def test_names_combines_two_accepted_pages_and_counts_a_shared_name_once(tmp_path: Path) -> None:
    _page(tmp_path, "one", "Contexts: a, b")
    _page(tmp_path, "two", "Contexts: b, c")

    assert _contexts.names(tmp_path) == frozenset({"a", "b", "c"})


def test_names_is_none_when_no_accepted_page_has_a_contexts_key(tmp_path: Path) -> None:
    """None, not an empty set: a repo with no list gets the old check, and a repo
    whose list is empty would pause every branch."""
    _page(tmp_path, "wfctl")

    assert _contexts.names(tmp_path) is None
    assert _contexts.names(tmp_path / "missing") is None


def test_a_page_with_only_outside_parties_still_bears_names(tmp_path: Path) -> None:
    """Codex found that the filter wanted a `Contexts` line, so a page listing
    only outside parties was dropped: its parties came back unknown beside
    another page, and as the only page `names` returned None and turned the
    check off."""
    _page(tmp_path, "parties", "Outside parties: workmux, Bad_Name")

    assert _contexts.names(tmp_path) == frozenset({"workmux"})
    assert _contexts.malformed(tmp_path) == [("parties", "Bad_Name")]

    _page(tmp_path, "wfctl", "Contexts: a")

    assert _contexts.names(tmp_path) == frozenset({"a", "workmux"})


def test_a_name_that_is_not_kebab_case_is_left_off_and_reported(tmp_path: Path) -> None:
    """Each name becomes a folder under `exceptions/`, so `../x` would point out
    of it."""
    _page(tmp_path, "wfctl", "Contexts: ok, session continuity, ../x", "Outside parties: Bad_Name, fine-2")

    assert _contexts.names(tmp_path) == frozenset({"ok", "fine-2"})
    assert sorted(_contexts.malformed(tmp_path)) == [
        ("wfctl", "../x"),
        ("wfctl", "Bad_Name"),
        ("wfctl", "session continuity"),
    ]


def test_malformed_is_empty_when_every_entry_is_a_name(tmp_path: Path) -> None:
    _page(tmp_path, "wfctl", "Contexts: a, b-c")

    assert _contexts.malformed(tmp_path) == []


# --- listed -----------------------------------------------------------------


def _design(spec_dir: Path, text: str) -> None:
    spec_dir.mkdir(parents=True, exist_ok=True)
    (spec_dir / "design.md").write_text(text)


def test_listed_reads_the_header_line(tmp_path: Path) -> None:
    _design(tmp_path, "# Design\n\nContexts: a, b\n\n## Body\n")

    assert _contexts.listed(tmp_path) == ("a", "b")


def test_listed_ignores_a_line_quoted_below_the_first_heading(tmp_path: Path) -> None:
    """This repo's own `design.md` quotes the line in a code block; reading it
    would answer for a branch that never wrote one."""
    _design(tmp_path, "# Design\n\n## Notes\n\n```\nContexts: a\n```\n")

    assert _contexts.listed(tmp_path) is None


def test_listed_is_none_without_a_design_md_or_a_key(tmp_path: Path) -> None:
    assert _contexts.listed(tmp_path) is None
    _design(tmp_path, "# Design\n\nNothing here.\n")
    assert _contexts.listed(tmp_path) is None


def test_listed_distinguishes_an_empty_value_from_a_missing_line(tmp_path: Path) -> None:
    """An empty line is a branch that says it changes no context; a missing line
    is one that never said, and the two get different pauses."""
    _design(tmp_path, "# Design\n\nContexts:\n")

    assert _contexts.listed(tmp_path) == ()


def test_listed_drops_duplicates_and_keeps_the_order(tmp_path: Path) -> None:
    _design(tmp_path, "# Design\n\nContexts: b, a, b\n")

    assert _contexts.listed(tmp_path) == ("b", "a")


# --- unanswered, pause, answers ------------------------------------------------


def _record(slug: str, *governs: str) -> "_arch.Record":
    return _arch.Record(slug, Path(f"{slug}.md"), "accepted", "", governs=governs)


def _design(spec: Path, line: str | None) -> None:
    spec.mkdir(parents=True, exist_ok=True)
    lines = ["# Design", ""] + ([line] if line is not None else []) + ["", "## Body"]
    (spec / "design.md").write_text("\n".join(lines) + "\n")


ALL = frozenset({"a", "b", "c", "workmux"})


def test_unanswered_returns_the_first_listed_context_with_no_answer(tmp_path: Path) -> None:
    """Listed order, not record order, so the reason names the same context on
    every read."""
    records = [_record("r", "c")]

    assert _contexts.unanswered(("b", "a", "c"), records, tmp_path, _contexts.ARCHITECTURE) == "b"


def test_a_record_that_governs_several_contexts_answers_each(tmp_path: Path) -> None:
    records = [_record("r", "a", "b")]

    assert _contexts.unanswered(("a", "b"), records, tmp_path, _contexts.ARCHITECTURE) is None


def test_a_no_for_one_context_does_not_answer_another(tmp_path: Path) -> None:
    """The whole point of #649: a "no" for `a` once cleared a branch that also
    changed `b`."""
    _design_exceptions.write(tmp_path, "boundary", "Copy only", context="a")

    assert _contexts.unanswered(("a", "b"), [], tmp_path, _contexts.ARCHITECTURE) == "b"
    assert _contexts.unanswered(("a",), [], tmp_path, _contexts.ARCHITECTURE) is None


def test_the_software_design_level_reads_its_own_pass_claim(tmp_path: Path) -> None:
    """A level-2 "no" for `a` is a different answer from a level-3 one."""
    _design_exceptions.write(tmp_path, "boundary", "Copy only", context="a")
    assert _contexts.unanswered(("a",), [], tmp_path, _contexts.SOFTWARE_DESIGN) == "a"

    _design_exceptions.write(tmp_path, "brainstorm.software-design", "None", context="a")
    assert _contexts.unanswered(("a",), [], tmp_path, _contexts.SOFTWARE_DESIGN) is None


def test_pause_checks_for_a_missing_line_first(tmp_path: Path) -> None:
    _design(tmp_path, None)

    gap = _contexts.pause(ALL, tmp_path, [], _contexts.ARCHITECTURE, location="docs/architecture")

    assert gap is not None
    assert gap.reason == "design.md lists no contexts"
    assert "Contexts: <names from the domain page>" in gap.remedy
    assert not gap.unanswered


def test_pause_reads_an_empty_line_as_a_missing_one(tmp_path: Path) -> None:
    """A branch that lists nothing has answered nothing, and an empty list would
    otherwise pass every branch."""
    _design(tmp_path, "Contexts:")

    gap = _contexts.pause(ALL, tmp_path, [], _contexts.ARCHITECTURE, location="docs/architecture")

    assert gap is not None and gap.reason == "design.md lists no contexts"


def test_pause_names_an_unknown_context_and_lists_the_known_ones(tmp_path: Path) -> None:
    _design(tmp_path, "Contexts: a, sesion")

    gap = _contexts.pause(ALL, tmp_path, [], _contexts.ARCHITECTURE, location="docs/architecture")

    assert gap is not None
    assert gap.reason == "sesion is not a context on the domain page"
    assert "The domain page lists:" in gap.remedy
    assert "a, b, c, workmux" in gap.remedy
    assert not gap.unanswered


def test_pause_names_the_context_that_has_no_answer_at_each_level(tmp_path: Path) -> None:
    """The two levels differ only in the noun, the folder, and the "no"
    command, so each remedy is checked against `contracts/cli.md`."""
    _design(tmp_path, "Contexts: a")

    arch = _contexts.pause(ALL, tmp_path, [], _contexts.ARCHITECTURE, location="docs/architecture")
    soft = _contexts.pause(
        ALL, tmp_path, [], _contexts.SOFTWARE_DESIGN, location="docs/architecture/design"
    )

    assert arch is not None and soft is not None
    assert arch.reason == "no architecture record governs a"
    assert arch.unanswered
    assert arch.remedy == "\n".join([
        "  Either add a record whose governs field names a, under:",
        "      docs/architecture/",
        "  or state that it needs none:",
        '      wfctl arch none --context a --reason "<why>"',
    ])
    assert soft.reason == "no software design record governs a"
    assert "      docs/architecture/design/" in soft.remedy
    assert (
        '      wfctl step none brainstorm.software-design --context a --reason "<why>"'
        in soft.remedy
    )


def test_pause_is_none_once_every_listed_context_is_answered(tmp_path: Path) -> None:
    _design(tmp_path, "Contexts: a, b")
    _design_exceptions.write(tmp_path, "boundary", "Copy only", context="b")

    assert _contexts.pause(
        ALL, tmp_path, [_record("r", "a")], _contexts.ARCHITECTURE, location="x"
    ) is None


def test_answers_reports_each_context_answered_with_a_no(tmp_path: Path) -> None:
    """The done row shows these, so a reviewer of `wfctl status` sees which
    contexts the branch said needed nothing."""
    _design_exceptions.write(tmp_path, "boundary", "Copy change", context="a")
    _design_exceptions.write(tmp_path, "boundary", "No hook changes", context="workmux")

    lines = _contexts.answers(
        ("a", "b", "workmux"), [_record("r", "b")], tmp_path, _contexts.ARCHITECTURE
    )

    assert lines == ["a: no — Copy change", "workmux: no — No hook changes"]


def test_a_listed_name_that_could_leave_exceptions_is_unknown_not_a_path(tmp_path: Path) -> None:
    """`listed` returns the line as written. A name like `../x` is refused by
    `pause` as not on the domain page, before anything builds a folder from it
    (the #655 review)."""
    _design(tmp_path, "Contexts: ../x")

    gap = _contexts.pause(ALL, tmp_path, [], _contexts.ARCHITECTURE, location="x")

    assert gap is not None and gap.reason == "../x is not a context on the domain page"
