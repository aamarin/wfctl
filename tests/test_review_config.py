"""Tests for wfctl._review_config, the reader of the `review` key in wfctl.json."""
from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest

from wfctl._review_config import (
    DEFAULT_ROUNDS, Group, load, load_rounds, parse, parse_rounds, required, required_at,
)


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
            "review.commands: the command for 'codex' holds a character that can't be "
            "printed (U+000A)",
            id="command-with-a-newline",
        ),
        pytest.param(
            {"commands": {"codex": "codex exec\u2028s9 claude"},
             "groups": [{"group": "security", "reviewers": [{"name": "codex", "count": 1}]}]},
            "review.commands: the command for 'codex' holds a character that can't be "
            "printed (U+2028)",
            id="command-with-a-unicode-line-separator",
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


def test_the_reviewer_cap_is_reported_beside_the_groups_other_problems(
    tmp_path: Path,
) -> None:
    """The cap returned as soon as the total passed 20, and counted only the
    entries that were valid so far. A model with no command, a bad model name,
    an unknown key, or a missing name hid the cap, and the cap hid every entry
    after it, so each fix revealed the next problem."""
    _write(tmp_path, {"groups": [{"group": "security", "reviewers": [
        {"name": "gemini", "count": 6},
        {"name": "4o", "count": 6},
        {"name": "claude", "count": 6, "model": "opus"},
        {"count": 6},
        {"name": "x y", "count": 1},
    ]}]})
    groups, problems = load(tmp_path)
    assert groups == []
    assert "review group 'security': each reviewer needs a name and a count" in problems
    assert "review group 'security': model 'gemini' has no entry in review.commands" in problems
    assert any("model '4o'" in p for p in problems), problems
    assert "review group 'security': unknown key 'model' in a reviewer" in problems
    assert any("model 'x y'" in p for p in problems), problems
    assert "review group 'security' has more than 20 reviewers" in problems


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
            "review group 'money\\n': a name is lowercase letters, digits and hyphens, "
            "starting with a letter",
            id="trailing-newline",
        ),
        pytest.param(
            {"commands\nx": {}},
            "review: unknown key 'commands\\nx'", id="review-key-with-a-newline",
        ),
        pytest.param(
            {"groups": [{"group": "security", "skill\nx": "y"}]},
            "review group 'security': unknown key 'skill\\nx'", id="group-key-with-a-newline",
        ),
        pytest.param(
            {"groups": [{"group": "security",
                         "reviewers": [{"name": "claude", "count": 1, "n\nx": 1}]}]},
            "review group 'security': unknown key 'n\\nx' in a reviewer",
            id="reviewer-key-with-a-newline",
        ),
        pytest.param(
            {"commands": {"x\ny": "x\ty"}},
            "review.commands: the command for 'x\\ny' holds a character that can't be "
            "printed (U+0009)",
            id="commands-key-with-a-newline",
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


_ROUNDS_PROBLEM = "review.rounds must be a whole number of 0 or more"


def test_the_default_cap_is_three_rounds() -> None:
    """The default is the number the skill used to ask the agent to count to,
    so a repository that never sets the key sees no change in the limit."""
    assert DEFAULT_ROUNDS == 3


@pytest.mark.parametrize("value", [0, 1, 3, 12])
def test_parse_rounds_accepts_a_whole_number_of_zero_or_more(value: int) -> None:
    """Zero is valid: it means no review runs and every change needs a
    sign-off, which a repository may want for a sensitive branch."""
    assert parse_rounds({"rounds": value}) == (value, None)


def test_parse_rounds_reports_an_absent_key_as_neither_a_value_nor_a_problem() -> None:
    """An absent key is the default, and the caller picks the default. Returning
    3 here would make a repository that wrote `"rounds": 3` look identical to
    one that wrote nothing, which the mismatch warning has to tell apart."""
    assert parse_rounds({}) == (None, None)


@pytest.mark.parametrize("value", [-1, 1.5, "3", True, False, None, [3]])
def test_parse_rounds_rejects_anything_that_is_not_a_whole_number(value: object) -> None:
    """`True` is a subclass of `int`, so `"rounds": true` would pass as 1
    without the explicit check, the same trap `_is_count` closes for a reviewer
    count."""
    assert parse_rounds({"rounds": value}) == (None, _ROUNDS_PROBLEM)


def test_load_reports_an_invalid_rounds_value_as_a_finding(tmp_path: Path) -> None:
    """`check config`, `review start` and the guard all stop on the finding,
    since all three read the key through `load`."""
    _write(tmp_path, {"rounds": -1})
    groups, problems = load(tmp_path)
    assert problems == [_ROUNDS_PROBLEM]
    assert groups == []


def test_load_accepts_a_valid_rounds_value_beside_the_groups(tmp_path: Path) -> None:
    """`rounds` joined the known keys, so it no longer reads as a misspelling."""
    _write(tmp_path, {"rounds": 5})
    assert _shape(tmp_path) == _DEFAULT


def test_load_rounds_returns_the_working_trees_valid_value(tmp_path: Path) -> None:
    _write(tmp_path, {"rounds": 5})
    assert load_rounds(tmp_path) == 5


@pytest.mark.parametrize("review", [{}, {"rounds": "5"}, {"rounds": -2}, ["rounds"]])
def test_load_rounds_returns_none_for_an_absent_or_invalid_value(
    tmp_path: Path, review: object,
) -> None:
    """The command uses this only to compare with the trunk's cap, so an invalid
    value has nothing to compare and `load` has already reported it."""
    _write(tmp_path, review)
    assert load_rounds(tmp_path) is None


def test_load_rounds_returns_none_with_no_wfctl_json_or_bad_json(tmp_path: Path) -> None:
    assert load_rounds(tmp_path) is None
    (tmp_path / "wfctl.json").write_text("{not json")
    assert load_rounds(tmp_path) is None


# --- the groups a branch must review ---------------------------------------------


def _config(*custom: str) -> str:
    return json.dumps({"review": {"groups": [
        {"group": name, "reviewers": [{"name": "claude", "count": 1}]} for name in custom
    ]}})


def _names(groups: list[Group]) -> list[str]:
    return [g.name for g in groups]


def test_the_required_list_is_the_trunks_groups_then_each_one_the_head_adds() -> None:
    """A PR that removes a group from its own `wfctl.json` still owes that
    group's review, and a group the PR adds runs on that PR too (R13)."""
    trunk, _ = parse(_config("money-rules"))
    head, _ = parse(_config("audit"))

    assert _names(required(trunk, head)) == ["security", "code", "money-rules", "audit"]


def test_a_group_both_sides_list_appears_once_with_the_trunks_reviewers() -> None:
    """The join is by name. CI reads notes by group name and never counts
    reviewers, so which side's reviewers win changes nothing CI decides."""
    trunk, _ = parse(_config("money-rules"))
    head, _ = parse(json.dumps({"review": {"groups": [
        {"group": "money-rules", "reviewers": [{"name": "claude", "count": 5}]},
    ]}}))

    joined = required(trunk, head)

    assert _names(joined) == ["security", "code", "money-rules"]
    assert len(joined[2].reviewers) == 1


@pytest.mark.parametrize("text", [None, json.dumps({"trunk": "main"})])
def test_a_missing_file_or_one_with_no_review_key_parses_to_the_defaults(
    text: str | None,
) -> None:
    groups, problems = parse(text)
    assert problems == []
    assert _names(groups) == ["security", "code"]


def test_each_side_is_validated_on_its_own_so_two_first_letters_never_clash() -> None:
    """`money-rules` on the trunk and `mutation` on the head share a letter,
    but neither file holds both. Only `relay` cares, and it refuses an
    ambiguous id itself."""
    trunk, trunk_problems = parse(_config("money-rules"))
    head, head_problems = parse(_config("mutation"))

    assert trunk_problems == head_problems == []
    assert _names(required(trunk, head))[-2:] == ["money-rules", "mutation"]


def _git(repo: Path, *args: str) -> str:
    return subprocess.run(
        ["git", "-C", str(repo), *args], check=True, capture_output=True, text=True,
    ).stdout.strip()


def _commit_config(repo: Path, text: str | None) -> str:
    path = repo / "wfctl.json"
    if text is None:
        path.unlink(missing_ok=True)
        _git(repo, "add", "-A")
    else:
        path.write_text(text)
        _git(repo, "add", "wfctl.json")
    _git(repo, "commit", "-q", "--allow-empty", "-m", "config")
    return _git(repo, "rev-parse", "HEAD")


@pytest.fixture
def config_repo(tmp_path: Path) -> Path:
    repo = tmp_path / "work"
    subprocess.run(["git", "init", "-q", "-b", "main", str(repo)], check=True)
    for key, val in (("user.email", "test@test.com"), ("user.name", "Test")):
        _git(repo, "config", key, val)
    return repo


def test_required_at_reads_both_files_from_git_and_not_the_working_tree(
    config_repo: Path,
) -> None:
    """An uncommitted edit would let a person drop a group locally that CI
    still requires, so neither side reads the working tree (FR-010)."""
    trunk = _commit_config(config_repo, _config("money-rules"))
    head = _commit_config(config_repo, None)
    (config_repo / "wfctl.json").write_text(_config("scratch"))

    groups, problems = required_at(config_repo, head, trunk)

    assert problems == []
    assert _names(groups) == ["security", "code", "money-rules"]


def test_required_at_names_the_side_a_review_key_problem_came_from(
    config_repo: Path,
) -> None:
    """A broken key on the trunk fails every PR, and the fix is a PR against
    the trunk, so the line has to say which file to open."""
    good = _commit_config(config_repo, _config("money-rules"))
    bad = _commit_config(config_repo, json.dumps({"review": []}))

    _, from_trunk = required_at(config_repo, good, bad)
    _, from_head = required_at(config_repo, bad, good)

    assert from_trunk == [f"wfctl.json at {bad[:7]}: review must be an object"]
    assert from_head == [f"wfctl.json at {bad[:7]}: review must be an object"]


@pytest.mark.parametrize("locale_encoding", [None, "latin-1"])
def test_required_at_reports_a_file_that_is_not_utf8_instead_of_crashing(
    config_repo: Path, monkeypatch: pytest.MonkeyPatch, locale_encoding: str | None,
) -> None:
    """`git show` output decoded with the locale raised `UnicodeDecodeError`
    on a UTF-8 machine, which reached `review start` as a traceback and the
    guard as a refused PR. On a Latin-1 machine it decoded cleanly instead, so
    the same file passed there. The `latin-1` case stands in for that machine,
    the way `_read_config_at`'s test does."""
    if locale_encoding is not None:
        real_run = subprocess.run

        def run_under_locale(*args: object, **kwargs: object) -> object:
            if kwargs.get("text") and kwargs.get("encoding") is None:
                kwargs["encoding"] = locale_encoding
            return real_run(*args, **kwargs)  # type: ignore[call-overload]

        monkeypatch.setattr(subprocess, "run", run_under_locale)
    good = _commit_config(config_repo, _config("money-rules"))
    (config_repo / "wfctl.json").write_bytes(b'{"trunk": "caf\xe9"}')
    _git(config_repo, "add", "wfctl.json")
    _git(config_repo, "commit", "-q", "-m", "latin-1 config")
    bad = _git(config_repo, "rev-parse", "HEAD")

    groups, problems = required_at(config_repo, good, bad)

    assert groups == []
    assert problems == [f"wfctl.json at {bad[:7]}: it isn't UTF-8"]


def test_required_at_leaves_the_trunks_rounds_to_the_cap_reader(
    config_repo: Path,
) -> None:
    """A bad `review.rounds` on the trunk warns and falls back to the default
    in `trunk_rounds`. When the group list checked it too, that warning became
    a refusal of every review in the repository. The head's copy is still
    checked, since the branch is where the agent can write a bad one."""
    good = _commit_config(config_repo, _config("money-rules"))
    bad = _commit_config(config_repo, json.dumps({"review": {"rounds": -1}}))

    groups, from_trunk = required_at(config_repo, good, bad)
    _, from_head = required_at(config_repo, bad, good)

    assert from_trunk == []
    assert _names(groups) == ["security", "code", "money-rules"]
    assert from_head == [
        f"wfctl.json at {bad[:7]}: review.rounds must be a whole number of 0 or more"
    ]
