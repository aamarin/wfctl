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


def reported_check_names() -> set[str]:
    """The names GitHub shows for each job: its `name`, or its id, and for a
    matrix job the id followed by the matrix value in parentheses."""
    names: set[str] = set()
    for job_id, job in yaml.safe_load(CI.read_text())["jobs"].items():
        matrix = job.get("strategy", {}).get("matrix", {})
        if matrix:
            (values,) = matrix.values()
            names.update(f"{job.get('name', job_id)} ({value})" for value in values)
        else:
            names.add(job.get("name", job_id))
    return names


def rule(kind: str) -> dict:
    (found,) = [r for r in json.loads(RULESET.read_text())["rules"] if r["type"] == kind]
    return found


def test_every_required_check_is_a_job_name_ci_reports() -> None:
    """A required check whose name never reports blocks every merge into
    `main`, for Andre too, so a renamed job has to fail here instead."""
    required = {c["context"] for c in rule("required_status_checks")["parameters"]["required_status_checks"]}

    assert required == {"test (3.11)", "test (3.13)", "wheel", "lint", "release-note"}
    assert required <= reported_check_names()


def test_no_one_can_bypass_the_ruleset() -> None:
    """With a bypass, a push straight to `main` would work for the person
    cutting a release, and the release would stop arriving as a pull request."""
    assert json.loads(RULESET.read_text())["bypass_actors"] == []


def test_merge_commits_are_the_only_merge_method() -> None:
    """The release script finds merges with no note through merge commits, and
    a squash or rebase leaves none."""
    assert rule("pull_request")["parameters"]["allowed_merge_methods"] == ["merge"]
