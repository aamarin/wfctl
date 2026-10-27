"""Tests for `wfctl._contexts` — the context names, and the branch's list of them."""
from __future__ import annotations

from pathlib import Path

from wfctl import _contexts


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
