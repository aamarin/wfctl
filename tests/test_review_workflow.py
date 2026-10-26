"""The `review` job runs only `main`'s code, and reads the PR as data.

GitHub runs a `pull_request_target` workflow from the base branch with the
base repository's token, which is safe only while the job executes nothing
from the PR's checkout (`contracts/review-job.md`, FR-017a). A step that ran
`uv sync` in `pr/`, or an expression that pasted a branch name into a shell
line, would hand that token to the PR's author. Nothing runs this file in a
PR, so these tests are where a change to it is checked.
"""
from __future__ import annotations

import re
from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parent.parent
REVIEW = ROOT / ".github" / "workflows" / "review.yml"
CI = ROOT / ".github" / "workflows" / "ci.yml"


def load(path: Path) -> dict[str, Any]:
    found = yaml.safe_load(path.read_text())
    # YAML 1.1 reads a bare `on` key as True.
    if True in found:
        found["on"] = found.pop(True)
    return found


def job() -> dict[str, Any]:
    (only,) = load(REVIEW)["jobs"].items()
    assert only[0] == "review"
    return only[1]


def steps() -> list[dict[str, Any]]:
    return job()["steps"]


def test_the_job_is_named_review() -> None:
    """The ruleset and the rerun both find the check by this name."""
    assert job().get("name", "review") == "review"


def test_the_job_runs_from_the_base_branch_on_every_pr_event_it_needs() -> None:
    """`pull_request_target` makes GitHub run `main`'s copy of this file, so a
    PR can't weaken its own check (R4). `edited` is how a retarget reruns the
    check against the new base (R14)."""
    on = load(REVIEW)["on"]

    assert list(on) == ["pull_request_target"]
    assert on["pull_request_target"]["types"] == ["opened", "synchronize", "reopened", "edited"]


def test_a_retarget_cancels_the_run_against_the_old_base() -> None:
    concurrency = load(REVIEW)["concurrency"]

    assert concurrency["group"] == "review-${{ github.event.pull_request.number }}"
    assert concurrency["cancel-in-progress"] is True


def test_the_token_can_only_read() -> None:
    assert load(REVIEW)["permissions"] == {"contents": "read"}
    assert "permissions" not in job() or job()["permissions"] == {"contents": "read"}


def test_the_prs_head_is_checked_out_into_pr_with_full_history() -> None:
    """A shallow checkout can't list the branch's commits, and the check
    refuses one."""
    (checkout,) = [
        s for s in steps()
        if str(s.get("uses", "")).startswith("actions/checkout") and s["with"].get("path") == "pr"
    ]

    assert checkout["with"]["ref"] == "${{ github.event.pull_request.head.sha }}"
    assert checkout["with"]["fetch-depth"] == 0


def test_the_review_notes_are_fetched_into_pr() -> None:
    runs = [s["run"] for s in steps() if "run" in s]

    assert any(
        "git -C pr fetch origin +refs/notes/wfctl-review:refs/notes/wfctl-review" in r
        for r in runs
    )


def test_the_base_branch_reaches_the_shell_only_through_env() -> None:
    """A branch name can hold shell text, so `${{ }}` inside `run:` would run
    it with the base repository's token."""
    for step in steps():
        assert "${{" not in step.get("run", ""), step
    (check,) = [s for s in steps() if "check reviews" in s.get("run", "")]
    assert check["env"]["BASE_REF"] == "${{ github.event.pull_request.base.ref }}"
    assert '--base "$BASE_REF"' in check["run"]


def test_nothing_from_the_prs_checkout_is_executed() -> None:
    """The check runs `main`'s wfctl from `trusted/`. Installing or running
    anything from `pr/` would run the PR's code with the base token."""
    for step in steps():
        uses = str(step.get("uses", ""))
        assert not uses.startswith(("./", "pr/")), step
        run = step.get("run", "")
        assert not re.search(r"\b(uv sync|pip install)\b", run), step
        if step.get("working-directory") == "pr":
            assert re.fullmatch(
                r"uv run --project \.\./trusted wfctl check reviews --base \"\$BASE_REF\"\s*", run,
            ), step
    (check,) = [s for s in steps() if "check reviews" in s.get("run", "")]
    assert check["working-directory"] == "pr"


def test_ci_defaults_every_job_to_a_read_only_token() -> None:
    """The PR jobs in `ci.yml` run the PR's code. Without a top-level
    `permissions` key their token could push in this repository. The tag job
    sets its own write access, which overrides the default for that job."""
    ci = load(CI)

    assert ci["permissions"] == {"contents": "read"}
    assert ci["jobs"]["tag"]["permissions"]["contents"] == "write"
