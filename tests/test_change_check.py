"""What `wfctl change check` decides, as a machine sees it.

Pure over two payloads and a list, so every state below is reachable without a
tracker, a network call or a repository. The states that need one of those live
in `test_change_cli.py`; the states that decide *whether a blank field matters*
live here, because that decision is the feature.

`compare` returns one row per **checkable** key — a key something expected. A
key nobody expected is absent from the result rather than present and passing,
which is what keeps a repository that uses no milestones from ever seeing the
word.
"""
from __future__ import annotations

from wfctl._change import compare


def _findings(rows: list) -> list:
    return [r for r in rows if not r.satisfied]


def test_a_key_the_issue_carries_and_the_change_lacks_is_a_finding() -> None:
    rows = _findings(compare([], {"labels": ["P1"]}, {"labels": []}))
    assert [(r.key, r.source) for r in rows] == [("labels", "inherited")]
    assert rows[0].missing == ["P1"]


def test_a_scalar_set_on_the_issue_and_unset_on_the_change_is_a_finding() -> None:
    rows = _findings(compare([], {"milestone": "v2"}, {"milestone": None}))
    assert [(r.key, r.source) for r in rows] == [("milestone", "inherited")]
    assert rows[0].missing == ["v2"]


def test_a_label_the_change_earned_itself_is_not_a_finding() -> None:
    """Step 6: "a label the change earns in its own right is added to that set,
    never swapped in for it."

    The reason the comparison is a set difference rather than an emptiness test.
    #301's sidebar was filled and still did not carry #280's label, so an
    emptiness test would have reported it clean — green-lighting the exact
    change that motivated the issue, one step later than before.
    """
    assert _findings(compare([], {"labels": ["P1"]}, {"labels": ["P1", "bug"]})) == []


def test_a_list_missing_only_some_of_the_issues_values_is_a_finding() -> None:
    rows = _findings(compare([], {"labels": ["P1", "epic"]}, {"labels": ["P1"]}))
    assert [r.key for r in rows] == ["labels"]
    assert rows[0].missing == ["epic"]


def test_everything_expected_and_set_reports_no_findings() -> None:
    rows = compare(
        ["assignees"],
        {"labels": ["P1"], "assignees": []},
        {"labels": ["P1"], "assignees": ["aamarin"]},
    )
    assert _findings(rows) == []
    assert sorted(r.key for r in rows) == ["assignees", "labels"]


def test_a_key_neither_source_expects_is_absent_from_the_result() -> None:
    """The rule the whole design turns on.

    Absent, not present-and-passing: a repository that never uses milestones
    must never see the word. Reporting every blank field is the noisy check that
    gets learned around and then ignored, which loses the prose and the check
    together.
    """
    assert compare([], {"milestone": None}, {"milestone": None}) == []
    assert compare([], {"milestone": None}, {"milestone": "v2"}) == []


def test_a_required_key_left_blank_is_a_finding_the_repo_asked_for() -> None:
    rows = _findings(compare(["assignees"], {"assignees": []}, {"assignees": []}))
    assert [(r.key, r.source) for r in rows] == [("assignees", "required")]


def test_a_key_both_sources_expect_is_reported_as_required() -> None:
    """The source the reader can act on directly.

    Both are true, and only one of them names a file they can open and change.
    """
    rows = _findings(compare(["labels"], {"labels": ["P1"]}, {"labels": []}))
    assert [(r.key, r.source) for r in rows] == [("labels", "required")]


def test_a_required_key_the_tracker_never_reports_is_its_own_finding() -> None:
    """The spelling mismatch that would otherwise be silence.

    `wfctl.json` says `assignee`; the backend emits `assignees`. Treating the
    absent key as "nothing required" makes a typo mean the requirement never
    existed — a check that silently stops checking, which is the failure class
    this whole feature is about.
    """
    rows = _findings(compare(["assignee"], {}, {"assignees": ["a"]}))
    assert [(r.key, r.source) for r in rows] == [("assignee", "unreported")]
    assert rows[0].reported == ["assignees"]


def test_every_missing_field_is_named_on_one_run() -> None:
    """SC-006. A check that reported one field per invocation would be run once."""
    rows = _findings(
        compare(
            ["assignees"],
            {"labels": ["P1"], "milestone": "v2"},
            {"labels": [], "milestone": None, "assignees": []},
        )
    )
    assert sorted(r.key for r in rows) == ["assignees", "labels", "milestone"]


def test_the_issue_being_unreadable_leaves_required_keys_still_checked() -> None:
    """FR-016's half that is not about exit codes.

    A failed issue read must not quietly become "nothing to inherit" — but what
    the repository requires is knowable without the issue, and dropping it too
    would report less than the run actually saw.
    """
    rows = _findings(compare(["assignees"], None, {"assignees": []}))
    assert [(r.key, r.source) for r in rows] == [("assignees", "required")]
