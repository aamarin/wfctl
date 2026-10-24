"""Tests for `wfctl._sections`, the reader of `change_sections` and the checker
of a PR body against it.

Everything here is a pure function of a string or a temporary directory, which
is why the cases can name every state in `data-model.md` rather than the two a
CLI run would reach. The CLI wiring is asserted in `test_shape.py` and
`test_cli_status.py`.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from wfctl import _sections

NAME = "Needs a spec?"

MISSING = f'"{NAME}" is missing. This repository asks every pull request to answer it.'
EMPTY = f'"{NAME}" is empty. The template\'s comment under that heading says what to write.'
NA = f'"{NAME}" holds N/A. The template\'s comment under that heading says what to write.'
NO_REASON = (
    f'"{NAME}" answers yes or no with no reason. '
    "The template's comment under that heading says what to write."
)

COMMENT = (
    "<!--\nDid this change need a full spec? Answer yes or no, then give the reason.\n-->"
)


def _write_config(root: Path, data: object) -> None:
    (root / "wfctl.json").write_text(json.dumps(data))


# --- load_required ----------------------------------------------------------


def test_no_wfctl_json_requires_nothing(tmp_path: Path) -> None:
    assert _sections.load_required(tmp_path) == ([], [])


def test_an_absent_key_requires_nothing(tmp_path: Path) -> None:
    """The repository that never opted in sees no change (SC-003), so an absent
    key and a file without it must be the same answer as no file at all."""
    _write_config(tmp_path, {"verify": ["true"]})
    assert _sections.load_required(tmp_path) == ([], [])


def test_an_empty_list_requires_nothing(tmp_path: Path) -> None:
    _write_config(tmp_path, {"change_sections": []})
    assert _sections.load_required(tmp_path) == ([], [])


def test_a_valid_list_is_returned_in_order(tmp_path: Path) -> None:
    _write_config(tmp_path, {"change_sections": [NAME, "Rollout"]})
    assert _sections.load_required(tmp_path) == ([NAME, "Rollout"], [])


def test_a_duplicate_heading_is_kept_once(tmp_path: Path) -> None:
    """Listing a heading twice would otherwise report its findings twice."""
    _write_config(tmp_path, {"change_sections": [NAME, NAME]})
    assert _sections.load_required(tmp_path) == ([NAME], [])


def test_a_string_instead_of_a_list_is_a_problem(tmp_path: Path) -> None:
    _write_config(tmp_path, {"change_sections": "x"})
    assert _sections.load_required(tmp_path) == (
        [],
        ["wfctl.json: 'change_sections' must be a list of section headings"],
    )


def test_a_non_string_entry_is_a_problem_and_drops_every_name(tmp_path: Path) -> None:
    """A half-valid declaration yields no names at all, the way
    `_change.load_required` does: findings justified from a file the reader
    could not fully read are worse than none."""
    _write_config(tmp_path, {"change_sections": [NAME, 2]})
    assert _sections.load_required(tmp_path) == (
        [],
        ["wfctl.json: 'change_sections' entry 2 must be a section heading, got int"],
    )


def test_an_empty_entry_is_a_problem(tmp_path: Path) -> None:
    _write_config(tmp_path, {"change_sections": [NAME, "  "]})
    assert _sections.load_required(tmp_path) == (
        [],
        ["wfctl.json: 'change_sections' entry 2 is empty"],
    )


def test_a_malformed_wfctl_json_is_left_to_doctor(tmp_path: Path) -> None:
    (tmp_path / "wfctl.json").write_text("{not json")
    assert _sections.load_required(tmp_path) == ([], [])


# --- body_findings ----------------------------------------------------------


def _body(section: str) -> str:
    return f"# Pull Request\n\n## Summary\n\nsomething\n\n{section}\n"


def test_a_body_with_no_required_sections_has_no_findings() -> None:
    assert _sections.body_findings(_body(""), []) == []


def test_a_deleted_heading_is_missing() -> None:
    """The template's own rule is "N/A over deletion", so a deleted heading is
    the one state no template instruction can produce and a check must catch."""
    assert _sections.body_findings(_body(""), [NAME]) == [MISSING]


def test_a_section_holding_only_its_comment_is_empty() -> None:
    body = _body(f"## {NAME}\n{COMMENT}\n")
    assert _sections.body_findings(body, [NAME]) == [EMPTY]


def test_a_single_line_comment_is_empty() -> None:
    body = _body(f"## {NAME}\n<!-- say why -->\n")
    assert _sections.body_findings(body, [NAME]) == [EMPTY]


def test_a_section_with_nothing_under_it_is_empty() -> None:
    assert _sections.body_findings(_body(f"## {NAME}\n"), [NAME]) == [EMPTY]


@pytest.mark.parametrize(
    "answer", ["N/A", "n/a", "NA", "N/A.", "  na  ", "None", "none."]
)
def test_every_spelling_of_n_a_is_flagged(answer: str) -> None:
    body = _body(f"## {NAME}\n{COMMENT}\n{answer}\n")
    assert _sections.body_findings(body, [NAME]) == [NA]


@pytest.mark.parametrize("answer", ["No.", "YES", "no!", "yes", "No"])
def test_a_bare_yes_or_no_is_flagged(answer: str) -> None:
    """A yes or no with no reason leaves a reviewer nothing to compare with the
    diff, which is the contradiction the answer exists to expose."""
    body = _body(f"## {NAME}\n{COMMENT}\n{answer}\n")
    assert _sections.body_findings(body, [NAME]) == [NO_REASON]


@pytest.mark.parametrize(
    ("answer", "finding"),
    [
        ("**No.**", NO_REASON),
        ("*No*", NO_REASON),
        ("_Yes._", NO_REASON),
        ("**N/A**", NA),
        ("**No**.", NO_REASON),
        ("_None_.", NA),
        ("`No`", NO_REASON),
        ("> No", NO_REASON),
        ("- No", NO_REASON),
        ("- [ ] No", NO_REASON),
        ("[x] Yes", NO_REASON),
    ],
)
def test_a_bare_answer_in_markdown_markup_is_flagged(answer: str, finding: str) -> None:
    """Bolding a one-word answer, or writing it as a list item or a quote, is a
    common way to fill a template section. The plan review found "**No.**"
    passing as answered (PR-024), and the review panel then found "**No**." and
    "- No" passing after that fix."""
    body = _body(f"## {NAME}\n{COMMENT}\n{answer}\n")
    assert _sections.body_findings(body, [NAME]) == [finding]


def test_a_section_holding_only_a_sub_heading_is_empty() -> None:
    """A lower-level heading stays inside the section, so a body that kept only
    the template's sub-heading would otherwise read as an answer."""
    body = _body(f"## {NAME}\n{COMMENT}\n### Why\n")
    assert _sections.body_findings(body, [NAME]) == [EMPTY]


def test_an_emphasized_answer_with_a_reason_passes() -> None:
    body = _body(f"## {NAME}\n{COMMENT}\n**No**, small change.\n")
    assert _sections.body_findings(body, [NAME]) == []


def test_an_answer_with_a_reason_passes() -> None:
    body = _body(f"## {NAME}\n{COMMENT}\nNo, small change.\n")
    assert _sections.body_findings(body, [NAME]) == []


def test_the_full_example_from_the_spec_passes() -> None:
    answer = "No. It fixes an off-by-one in check-body and moves no boundary."
    body = _body(f"## {NAME}\n{COMMENT}\n{answer}\n")
    assert _sections.body_findings(body, [NAME]) == []


def test_a_heading_inside_a_fence_does_not_count() -> None:
    """A body quoting the template inside a fenced block has not answered it.
    `_md.walk` is the fence reader the other body checks share."""
    body = _body(f"```\n## {NAME}\nNo, small change.\n```\n")
    assert _sections.body_findings(body, [NAME]) == [MISSING]


def test_a_commented_out_heading_does_not_count() -> None:
    """GitHub does not render an HTML comment, so a heading inside one is not a
    section the reviewer can read."""
    body = _body(f"<!--\n## {NAME}\nNo, small change.\n-->")
    assert _sections.body_findings(body, [NAME]) == [MISSING]


def test_a_third_level_heading_matches() -> None:
    body = _body(f"### {NAME}\nNo, small change.\n")
    assert _sections.body_findings(body, [NAME]) == []


def test_the_heading_match_ignores_case_and_surrounding_space() -> None:
    body = _body("##   NEEDS A SPEC?  \nNo, small change.\n")
    assert _sections.body_findings(body, [NAME]) == []


def test_a_section_ends_at_the_next_heading_of_the_same_level() -> None:
    """The answer under the next heading belongs to that heading, so this
    section is empty even though the body has prose after it."""
    body = _body(f"## {NAME}\n{COMMENT}\n## Next\nNo, small change.\n")
    assert _sections.body_findings(body, [NAME]) == [EMPTY]


def test_a_section_ends_at_a_higher_level_heading() -> None:
    body = _body(f"### {NAME}\n# Top\nNo, small change.\n")
    assert _sections.body_findings(body, [NAME]) == [EMPTY]


def test_a_lower_level_heading_stays_inside_the_section() -> None:
    """A reason may be broken up under sub-headings, and cutting the section at
    the first one would report a written answer as empty."""
    body = _body(f"## {NAME}\n### Why\nNo, small change.\n")
    assert _sections.body_findings(body, [NAME]) == []


def test_findings_follow_the_order_of_the_required_list() -> None:
    body = _body(f"## {NAME}\nN/A\n")
    assert _sections.body_findings(body, ["Rollout", NAME]) == [
        '"Rollout" is missing. This repository asks every pull request to answer it.',
        NA,
    ]


# --- templates and template_problems ----------------------------------------


def _template(root: Path, rel: str, text: str = "## Summary\n") -> Path:
    path = root / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text)
    return path


def test_templates_finds_the_single_file_layout(tmp_path: Path) -> None:
    found = _template(tmp_path, ".github/pull_request_template.md")
    assert _sections.templates(tmp_path) == [found]


def test_templates_matches_the_path_case_insensitively(tmp_path: Path) -> None:
    found = _template(tmp_path, "docs/Pull_Request_Template.md")
    assert _sections.templates(tmp_path) == [found]


def test_templates_finds_a_gitlab_merge_request_template(tmp_path: Path) -> None:
    found = _template(tmp_path, ".gitlab/merge_request_templates/default.md")
    assert _sections.templates(tmp_path) == [found]


def test_templates_finds_files_in_the_multi_template_directory(tmp_path: Path) -> None:
    """GitHub's multi-template layout names its files `bug.md` and `feature.md`,
    which match only through the directory they sit in."""
    bug = _template(tmp_path, ".github/PULL_REQUEST_TEMPLATE/bug.md")
    feature = _template(tmp_path, ".github/PULL_REQUEST_TEMPLATE/feature.md")
    assert _sections.templates(tmp_path) == [bug, feature]


def test_templates_ignores_anything_under_dot_git(tmp_path: Path) -> None:
    _template(tmp_path, ".git/pull_request_template.md")
    assert _sections.templates(tmp_path) == []


def test_templates_does_not_look_four_levels_down(tmp_path: Path) -> None:
    """The search mirrors `find -maxdepth 3` in `opening-a-change` Step 2, so a
    template the skill would not find is not one `check config` reports on."""
    _template(tmp_path, "a/b/c/pull_request_template.md")
    assert _sections.templates(tmp_path) == []


def test_no_template_is_one_finding(tmp_path: Path) -> None:
    assert _sections.template_problems(tmp_path, [NAME]) == [
        "wfctl.json: 'change_sections' lists sections, but no PR template was found"
    ]


def test_nothing_listed_is_never_a_finding(tmp_path: Path) -> None:
    assert _sections.template_problems(tmp_path, []) == []


def test_a_template_with_every_listed_section_has_no_finding(tmp_path: Path) -> None:
    _template(tmp_path, ".github/pull_request_template.md", f"## {NAME}\n<!-- c -->\n")
    assert _sections.template_problems(tmp_path, [NAME]) == []


def test_a_template_missing_a_listed_section_is_named(tmp_path: Path) -> None:
    _template(tmp_path, ".github/pull_request_template.md")
    assert _sections.template_problems(tmp_path, [NAME]) == [
        f"wfctl.json: 'change_sections' lists \"{NAME}\", which "
        ".github/pull_request_template.md doesn't have"
    ]


def test_an_empty_section_in_a_template_is_not_a_finding(tmp_path: Path) -> None:
    """A template's sections are meant to be empty. Only a missing one means a
    PR written from it can never pass."""
    _template(tmp_path, ".github/pull_request_template.md", f"## {NAME}\n")
    assert _sections.template_problems(tmp_path, [NAME]) == []


def test_each_template_missing_the_section_is_its_own_finding(tmp_path: Path) -> None:
    """Any template in a multi-template directory can be the one a change
    uses, so a gap in one is not covered by another that has the section."""
    _template(tmp_path, ".github/PULL_REQUEST_TEMPLATE/bug.md", f"## {NAME}\n")
    _template(tmp_path, ".github/PULL_REQUEST_TEMPLATE/feature.md")
    assert _sections.template_problems(tmp_path, [NAME]) == [
        f"wfctl.json: 'change_sections' lists \"{NAME}\", which "
        ".github/PULL_REQUEST_TEMPLATE/feature.md doesn't have"
    ]
