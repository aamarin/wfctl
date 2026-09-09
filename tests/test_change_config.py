"""`change_check` in `wfctl.json` — what a repository declares it requires.

The second reader of that file, beside `_verify.load_config`. Each owns one key
and its schema; only the *path* is shared, because that is the part that would
drift.

Every malformed shape here degrades to "nothing required" rather than raising.
A check that reported findings it could not justify from a file it could not
read would be worse than one that reported none — and the reader meets this
while opening a change, where a parse error is not what they asked about.
"""
from __future__ import annotations

import json
from pathlib import Path

from wfctl._change import load_required


def _write(repo_root: Path, payload: object) -> None:
    (repo_root / "wfctl.json").write_text(json.dumps(payload))


def test_no_file_at_all_requires_nothing(tmp_path: Path) -> None:
    assert load_required(tmp_path) == ([], [])


def test_a_file_without_the_key_requires_nothing(tmp_path: Path) -> None:
    """The common case, and the one that must stay silent.

    Every repository that has ever run `wfctl verify` has this file and has not
    heard of `change_check`. Reading its absence as anything but "nothing
    required" would turn the feature on for all of them at once.
    """
    _write(tmp_path, {"verify": [["pytest", "-q"]]})
    assert load_required(tmp_path) == ([], [])


def test_an_empty_list_is_the_same_as_the_key_being_absent(tmp_path: Path) -> None:
    _write(tmp_path, {"change_check": []})
    assert load_required(tmp_path) == ([], [])


def test_field_names_come_back_in_the_order_written(tmp_path: Path) -> None:
    _write(tmp_path, {"change_check": ["assignees", "labels"]})
    assert load_required(tmp_path) == (["assignees", "labels"], [])


def test_a_duplicate_is_collapsed_rather_than_reported(tmp_path: Path) -> None:
    """Writing a name twice is a typo with no consequence, not a mistake to
    report. Reporting it would spend a finding on something that changes
    nothing."""
    _write(tmp_path, {"change_check": ["labels", "labels"]})
    assert load_required(tmp_path) == (["labels"], [])


def test_a_declaration_that_is_not_a_list_is_reported(tmp_path: Path) -> None:
    _write(tmp_path, {"change_check": "assignees"})
    keys, errs = load_required(tmp_path)
    assert keys == [] and len(errs) == 1 and "change_check" in errs[0]


def test_an_entry_that_is_not_a_string_names_its_position(tmp_path: Path) -> None:
    _write(tmp_path, {"change_check": ["labels", 7]})
    keys, errs = load_required(tmp_path)
    assert keys == []
    assert any("2" in e for e in errs)


def test_an_empty_entry_is_reported(tmp_path: Path) -> None:
    """A blank string would otherwise require a field named "", which no tracker
    reports — so it would surface as an `unreported` finding naming nothing."""
    _write(tmp_path, {"change_check": ["  "]})
    keys, errs = load_required(tmp_path)
    assert keys == [] and errs


def test_one_bad_entry_discards_the_whole_declaration(tmp_path: Path) -> None:
    """Half a declaration is not a declaration.

    `_verify.load_config` decides the same way about `verify`: "a config that is
    half-valid is not a definition of done." Requiring the good half here would
    have the check enforce a policy nobody finished writing.
    """
    _write(tmp_path, {"change_check": ["labels", 7, "assignees"]})
    assert load_required(tmp_path)[0] == []


def test_a_file_that_is_not_json_requires_nothing_and_says_nothing(
    tmp_path: Path,
) -> None:
    """`doctor` already reports a malformed `wfctl.json`, and better.

    Saying it twice puts the same finding in front of someone opening a change,
    where it is not what they asked about.
    """
    (tmp_path / "wfctl.json").write_text("{not json")
    assert load_required(tmp_path) == ([], [])


def test_a_top_level_that_is_not_an_object_requires_nothing(tmp_path: Path) -> None:
    _write(tmp_path, ["change_check"])
    assert load_required(tmp_path) == ([], [])
