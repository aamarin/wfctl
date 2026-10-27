"""The ruleset that protects `main` names only checks that CI really reports.

`.github/rulesets/main.json` is applied by hand after this repository's CI has a
`release-note` job, so nothing runs it in a pull request. Both files are
committed, which makes the one failure that matters visible here.
"""
from __future__ import annotations

import json
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
RULESET = ROOT / ".github" / "rulesets" / "main.json"
CI = ROOT / ".github" / "workflows" / "ci.yml"
REVIEW = ROOT / ".github" / "workflows" / "review.yml"

# The GitHub Actions app. A required check pinned to it can only be met by a
# job, so a commit status someone posts by hand under the same name doesn't
# count.
ACTIONS = 15368


def reported_check_names() -> set[str]:
    """The names GitHub shows for each job in both workflows: its `name`, or
    its id, and for a matrix job the id followed by the matrix value in
    parentheses."""
    names: set[str] = set()
    for workflow in (CI, REVIEW):
        for job_id, job in yaml.safe_load(workflow.read_text())["jobs"].items():
            matrix = job.get("strategy", {}).get("matrix", {})
            if matrix:
                (values,) = matrix.values()
                names.update(f"{job.get('name', job_id)} ({value})" for value in values)
            else:
                names.add(job.get("name", job_id))
    return names


def required_checks() -> list[dict]:
    return rule("required_status_checks")["parameters"]["required_status_checks"]


def rule(kind: str) -> dict:
    (found,) = [r for r in json.loads(RULESET.read_text())["rules"] if r["type"] == kind]
    return found


def test_every_required_check_is_a_job_name_ci_reports() -> None:
    """A required check whose name never reports blocks every merge into
    `main`, for Andre too, so a renamed job has to fail here instead."""
    required = {c["context"] for c in required_checks()}

    assert required == {"test (3.11)", "test (3.13)", "wheel", "lint", "release-note", "review"}
    assert required <= reported_check_names()


def test_the_review_check_can_only_be_met_by_a_github_actions_job() -> None:
    """Anyone with write access can post a commit status named `review`
    through the API, and an unpinned requirement would accept it as the
    check passing (PR-010)."""
    (review,) = [c for c in required_checks() if c["context"] == "review"]

    assert review == {"context": "review", "integration_id": ACTIONS}


def test_no_one_can_bypass_the_ruleset() -> None:
    """With a bypass, a push straight to `main` would work for the person
    cutting a release, and the release would stop arriving as a pull request."""
    assert json.loads(RULESET.read_text())["bypass_actors"] == []


def test_merge_commits_are_the_only_merge_method() -> None:
    """The release script finds merges with no note through merge commits, and
    a squash or rebase leaves none."""
    assert rule("pull_request")["parameters"]["allowed_merge_methods"] == ["merge"]
