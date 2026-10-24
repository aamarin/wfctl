"""Tests for wfctl._review_config, the reader of the `review` key in wfctl.json."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from wfctl._review_config import load


def _write(repo: Path, review: object) -> None:
    (repo / "wfctl.json").write_text(json.dumps({"review": review}))


def _shape(repo: Path) -> list[tuple[str, str, list[tuple[str, str, str | None]]]]:
    groups, problems = load(repo)
    assert problems == []
    return [
        (g.name, g.skill, [(r.id, r.model, r.command) for r in g.reviewers])
        for g in groups
    ]


_DEFAULT = [
    ("security", "reviewing-security",
     [("s1", "claude", None), ("s2", "claude", None), ("s3", "claude", None)]),
    ("code", "code-review",
     [("c1", "claude", None), ("c2", "claude", None), ("c3", "claude", None)]),
]


def test_a_repository_with_no_wfctl_json_gets_three_claude_reviewers_per_group(
    tmp_path: Path,
) -> None:
    """A repository that never heard of the key still gets both groups, and no
    model it hasn't installed. Naming Codex by default would leave a run nobody
    can complete on a machine without it (FR-022, SC-005)."""
    assert _shape(tmp_path) == _DEFAULT


def test_a_wfctl_json_with_no_review_key_gets_the_defaults(tmp_path: Path) -> None:
    """Most repositories declare `steps` or `trunk` and never `review`, and the
    defaults have to hold for them as well as for a repo with no file."""
    (tmp_path / "wfctl.json").write_text(json.dumps({"trunk": "main"}))
    assert _shape(tmp_path) == _DEFAULT


def test_the_documented_example_numbers_ids_across_each_groups_whole_reviewer_list(
    tmp_path: Path,
) -> None:
    """The example in contracts/config.md is the one AGENTS.md copies. Ids run
    across the group's list, so `s3` is the first Codex reviewer rather than a
    second `s1`, which would put two reports in one file."""
    _write(tmp_path, {
        "commands": {"codex": "codex exec --sandbox read-only"},
        "groups": [
            {"group": "security",
             "reviewers": [{"name": "claude", "count": 2}, {"name": "codex", "count": 2}]},
            {"group": "money-rules", "skill": "money-rules-review",
             "reviewers": [{"name": "claude", "count": 2}]},
        ],
    })
    codex = "codex exec --sandbox read-only"
    assert _shape(tmp_path) == [
        ("security", "reviewing-security", [
            ("s1", "claude", None), ("s2", "claude", None),
            ("s3", "codex", codex), ("s4", "codex", codex),
        ]),
        _DEFAULT[1],
        ("money-rules", "money-rules-review", [("m1", "claude", None), ("m2", "claude", None)]),
    ]


def test_a_custom_group_listed_first_still_runs_after_security_and_code(tmp_path: Path) -> None:
    """The code group reviews the security group's fixes, and every custom group
    reviews both. A list order that moved a custom group ahead would have it
    review code the next two groups then change (FR-019)."""
    _write(tmp_path, {"groups": [
        {"group": "money-rules", "reviewers": [{"name": "claude", "count": 1}]},
        {"group": "code"},
        {"group": "accessibility", "reviewers": [{"name": "claude", "count": 1}]},
    ]})
    groups, problems = load(tmp_path)
    assert problems == []
    assert [g.name for g in groups] == ["security", "code", "money-rules", "accessibility"]


def test_a_built_in_group_listed_without_reviewers_keeps_three_claude_reviewers(
    tmp_path: Path,
) -> None:
    """Listing `security` to change its skill shouldn't also drop its reviewers.
    Only a missing key gets the default; an empty list is a finding."""
    _write(tmp_path, {"groups": [{"group": "security", "skill": "our-security-review"}]})
    groups, _ = load(tmp_path)
    assert groups[0].skill == "our-security-review"
    assert [r.id for r in groups[0].reviewers] == ["s1", "s2", "s3"]


def test_a_custom_group_with_no_skill_runs_the_code_review(tmp_path: Path) -> None:
    """A group that names no skill still needs one to hand its reviewers, and
    the code review is the general one."""
    _write(tmp_path, {"groups": [
        {"group": "money-rules", "reviewers": [{"name": "claude", "count": 1}]},
    ]})
    groups, _ = load(tmp_path)
    assert groups[2].skill == "code-review"


@pytest.mark.parametrize(
    ("review", "finding"),
    [
        pytest.param([], "review must be an object", id="review-not-object"),
        pytest.param({"groups": {}}, "review.groups must be a list", id="groups-not-list"),
        pytest.param(
            {"groups": [{"group": "code"}, {"group": "money-rules",
                                            "reviewers": [{"name": "claude", "count": 1}]},
                        {"skill": "x"}]},
            "review.groups[2] has no group name", id="no-group-name",
        ),
        pytest.param(
            {"groups": [{"group": "../x", "reviewers": [{"name": "claude", "count": 1}]}]},
            "review group '../x': a name is lowercase letters, digits and hyphens, "
            "starting with a letter",
            id="bad-name",
        ),
        pytest.param(
            {"groups": [{"group": "money-rules"}]},
            "review group 'money-rules' has no reviewers", id="custom-no-reviewers-key",
        ),
        pytest.param(
            {"groups": [{"group": "security", "reviewers": []}]},
            "review group 'security' has no reviewers", id="built-in-empty-reviewers",
        ),
        pytest.param(
            {"groups": [{"group": "money-rules", "reviewers": []}]},
            "review group 'money-rules' has no reviewers", id="custom-empty-reviewers",
        ),
        pytest.param(
            {"groups": [{"group": "storage", "reviewers": [{"name": "claude", "count": 1}]}]},
            "review groups 'security' and 'storage' both start with 's'; "
            "reviewer ids would clash",
            id="first-letter-clash",
        ),
        pytest.param(
            {"groups": [{"group": "security", "reviewers": [{"name": "codex", "count": 1}]}]},
            "review group 'security': model 'codex' has no entry in review.commands",
            id="model-without-command",
        ),
        pytest.param(
            {"groups": [{"group": "security", "reviewers": [{"name": "claude", "count": 0}]}]},
            "review group 'security': count for 'claude' must be 1 or more", id="count-zero",
        ),
        pytest.param(
            {"groups": [{"group": "security", "reviewers": [{"name": "claude", "count": "2"}]}]},
            "review group 'security': count for 'claude' must be 1 or more",
            id="count-not-integer",
        ),
        pytest.param(
            {"groups": [{"group": "security", "reviewers": [{"name": "claude", "count": True}]}]},
            "review group 'security': count for 'claude' must be 1 or more", id="count-bool",
        ),
        pytest.param(
            {"commands": ["codex exec"]},
            "review.commands must map each model to a command string", id="commands-not-object",
        ),
        pytest.param(
            {"commands": {"codex": 5}},
            "review.commands must map each model to a command string",
            id="command-not-string",
        ),
        pytest.param(
            {"groups": [{"group": "security", "reviewers": [{"name": "claude", "count": 21}]}]},
            "review group 'security' has more than 20 reviewers",
            id="count-too-large",
        ),
        pytest.param(
            {"groups": [{"group": "security",
                         "reviewers": [{"name": "claude", "count": 20}] * 2}]},
            "review group 'security' has more than 20 reviewers",
            id="repeated-entries-too-many",
        ),
        pytest.param(
            {"commands": {"gpt 5": "gpt"},
             "groups": [{"group": "security", "reviewers": [{"name": "gpt 5", "count": 1}]}]},
            "review group 'security': model 'gpt 5' isn't lowercase letters, digits and "
            "hyphens, starting with a letter",
            id="model-name-with-a-space",
        ),
        pytest.param(
            {"commands": {"4o": "gpt"},
             "groups": [{"group": "security", "reviewers": [{"name": "4o", "count": 1}]}]},
            "review group 'security': model '4o' isn't lowercase letters, digits and "
            "hyphens, starting with a letter",
            id="model-name-starting-with-a-digit",
        ),
        pytest.param(
            {"commands": {"x\ns9 claude": "x"},
             "groups": [{"group": "security",
                         "reviewers": [{"name": "x\ns9 claude", "count": 1}]}]},
            "review group 'security': model 'x\\ns9 claude' isn't lowercase letters, "
            "digits and hyphens, starting with a letter",
            id="model-name-with-a-newline",
        ),
        pytest.param(
            {"commands": {"codex": "codex exec\nreports: /tmp/x/\ns9 claude"},
             "groups": [{"group": "security", "reviewers": [{"name": "codex", "count": 1}]}]},
            "review.commands: the command for 'codex' holds a control character",
            id="command-with-a-newline",
        ),
        pytest.param(
            {"groups": [{"group": "money", "skill": "../../etc",
                         "reviewers": [{"name": "claude", "count": 1}]}]},
            "review group 'money': skill must be a skill name", id="skill-path",
        ),
        pytest.param(
            {"commands": {"claude": "claude -p"}},
            "review.commands: claude runs inside the agent and takes no command",
            id="command-for-claude",
        ),
        pytest.param(
            {"commands": {"codex": "codex 'exec"},
             "groups": [{"group": "security", "reviewers": [{"name": "codex", "count": 1}]}]},
            "review.commands: can't split the command for 'codex': No closing quotation",
            id="command-unbalanced-quote",
        ),
    ],
)
def test_each_bad_declaration_is_a_finding_in_the_words_check_config_prints(
    tmp_path: Path, review: object, finding: str
) -> None:
    """A declaration wfctl drops without saying so is indistinguishable, to the
    person who wrote it, from one wfctl never read. The wording is
    contracts/config.md's, since `check config` prints it as written."""
    _write(tmp_path, review)
    groups, problems = load(tmp_path)
    assert finding in problems, problems
    assert groups == []


def test_a_wfctl_json_that_is_not_json_is_a_finding_rather_than_an_exception(
    tmp_path: Path,
) -> None:
    """`review start` and the guard both read this file, and a traceback from
    the guard reaches the agent as a hook error on every Bash call."""
    (tmp_path / "wfctl.json").write_text("{not json")
    groups, problems = load(tmp_path)
    assert groups == []
    assert len(problems) == 1
    assert problems[0].startswith("wfctl.json: not valid JSON")


def test_a_wfctl_json_whose_top_level_is_not_an_object_is_a_finding(tmp_path: Path) -> None:
    """`[]` parses, so the JSON check alone lets it through to a `.get` that
    raises."""
    (tmp_path / "wfctl.json").write_text("[]")
    groups, problems = load(tmp_path)
    assert groups == []
    assert problems == ["wfctl.json: top level must be an object"]


# --- wfctl check config ----------------------------------------------------------


def _check_config(repo: Path, config: object) -> tuple[int, list[str]]:
    from typer.testing import CliRunner

    from wfctl.cli import app

    (repo / "wfctl.json").write_text(json.dumps(config))
    result = CliRunner().invoke(app, ["check", "config"])
    return result.exit_code, result.output.splitlines()


@pytest.mark.parametrize(
    ("review", "finding"),
    [
        ([], "review must be an object"),
        ({"groups": {}}, "review.groups must be a list"),
        ({"groups": [{"group": "money-rules"}]}, "review group 'money-rules' has no reviewers"),
        ({"groups": [{"group": "security", "reviewers": [{"name": "codex", "count": 1}]}]},
         "review group 'security': model 'codex' has no entry in review.commands"),
    ],
)
def test_check_config_prints_each_review_finding_as_its_own_line(
    storyctl_dir: object, monkeypatch: pytest.MonkeyPatch, review: object, finding: str
) -> None:
    """`check config` is where a person learns a declaration is broken, and
    `review start` refuses on the same findings, so the two have to agree
    (FR-021, US5 scenarios 2 to 4)."""
    monkeypatch.setenv("NO_COLOR", "1")
    repo = storyctl_dir.repo_root  # type: ignore[attr-defined]

    code, lines = _check_config(repo, {"review": review})

    assert code == 1, lines
    assert lines[0] == "✗ wfctl.json:"
    assert f"  - {finding}" in lines


def test_check_config_prints_review_findings_beside_the_trunk_and_steps_ones(
    storyctl_dir: object, monkeypatch: pytest.MonkeyPatch
) -> None:
    """One run reports every problem in the file, so fixing one doesn't reveal
    the next only on the following run."""
    monkeypatch.setenv("NO_COLOR", "1")
    repo = storyctl_dir.repo_root  # type: ignore[attr-defined]

    code, lines = _check_config(repo, {
        "trunk": 5, "steps": {"nope": []}, "review": {"groups": {}},
    })

    assert code == 1
    assert "  - review.groups must be a list" in lines
    assert any("'trunk' must be a branch name" in line for line in lines)
    assert any("'nope' is not a pipeline step" in line for line in lines)


def test_check_config_reports_invalid_json_once(
    storyctl_dir: object, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Both readers find a file that won't parse, and the same line twice
    reads as two problems."""
    from typer.testing import CliRunner

    from wfctl.cli import app

    monkeypatch.setenv("NO_COLOR", "1")
    repo = storyctl_dir.repo_root  # type: ignore[attr-defined]
    (repo / "wfctl.json").write_text("{not json")

    result = CliRunner().invoke(app, ["check", "config"])

    assert result.exit_code == 1
    assert sum("not valid JSON" in line for line in result.output.splitlines()) == 1


def test_check_config_passes_the_documented_review_example(
    storyctl_dir: object, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A valid declaration is silent about `review`, as a valid `steps` is."""
    monkeypatch.setenv("NO_COLOR", "1")
    repo = storyctl_dir.repo_root  # type: ignore[attr-defined]

    code, lines = _check_config(repo, {"review": {
        "commands": {"codex": "codex exec --sandbox read-only"},
        "groups": [
            {"group": "security",
             "reviewers": [{"name": "claude", "count": 2}, {"name": "codex", "count": 2}]},
            {"group": "money-rules", "skill": "money-rules-review",
             "reviewers": [{"name": "claude", "count": 2}]},
        ],
    }})

    assert code == 0, lines


@pytest.mark.parametrize(
    ("review", "finding"),
    [
        pytest.param(
            {"groups": [{"group": "money-rules", "reviewers": [{"name": "claude", "count": 1}]},
                        {"group": "money-rules", "reviewers": [{"name": "claude", "count": 5}]}]},
            "review group 'money-rules' is listed twice", id="listed-twice",
        ),
        pytest.param({"group": []}, "review: unknown key 'group'", id="review-typo"),
        pytest.param(
            {"groups": [{"group": "security", "reviewer": []}]},
            "review group 'security': unknown key 'reviewer'", id="group-typo",
        ),
        pytest.param(
            {"groups": [{"group": "security", "reviewers": [{"name": "claude", "cnt": 2}]}]},
            "review group 'security': unknown key 'cnt' in a reviewer", id="reviewer-typo",
        ),
        pytest.param(
            {"groups": [{"group": "money\n", "reviewers": [{"name": "claude", "count": 1}]}]},
            "review group 'money\n': a name is lowercase letters, digits and hyphens, "
            "starting with a letter",
            id="trailing-newline",
        ),
    ],
)
def test_a_declaration_that_would_have_passed_silently_is_a_finding(
    tmp_path: Path, review: object, finding: str
) -> None:
    """Each of these used to load. A group listed twice kept only its last
    entry, a misspelled key fell back to three Claude reviewers, and a name
    ending in a newline passed `$` and became a directory name."""
    _write(tmp_path, review)
    groups, problems = load(tmp_path)
    assert finding in problems, problems
    assert groups == []


def test_an_unreadable_commands_key_is_one_finding_not_one_per_model(tmp_path: Path) -> None:
    """A second finding per model saying it has no command points at the wrong
    fix, since the command is there and the key around it is broken."""
    _write(tmp_path, {
        "commands": ["codex exec"],
        "groups": [{"group": "security", "reviewers": [{"name": "codex", "count": 1}]}],
    })
    _, problems = load(tmp_path)
    assert problems == ["review.commands must map each model to a command string"]
