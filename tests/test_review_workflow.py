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


def checkout(path: str) -> dict[str, Any]:
    (found,) = [
        s for s in steps()
        if str(s.get("uses", "")).startswith("actions/checkout") and s["with"].get("path") == path
    ]
    return found


def test_the_prs_head_is_checked_out_into_pr_with_full_history() -> None:
    """A shallow checkout can't list the branch's commits, and the check
    refuses one."""
    assert checkout("pr")["with"]["ref"] == "${{ github.event.pull_request.head.sha }}"
    assert checkout("pr")["with"]["fetch-depth"] == 0


def test_only_the_pr_checkout_opts_in_to_checking_out_a_fork() -> None:
    """`actions/checkout` refuses to check out a fork's head under
    `pull_request_target` unless the step opts in. Without the opt-in, the
    required `review` check failed on every fork PR before it checked
    anything (#790). The opt-in is safe only because nothing in `pr/` runs.
    The `trusted` checkout's code does run, so it never opts in."""
    assert checkout("pr")["with"]["allow-unsafe-pr-checkout"] is True
    assert "allow-unsafe-pr-checkout" not in checkout("trusted")["with"]


def test_the_pr_checkout_leaves_no_token_in_its_git_config() -> None:
    """By default, `actions/checkout` saves the base repository's token in
    `pr/.git/config`, where it stays for the rest of the job beside a fork's
    files. The notes fetch doesn't need it, because the repository is public
    and anyone can read its notes ref."""
    assert checkout("pr")["with"]["persist-credentials"] is False


def test_the_trusted_checkout_leaves_no_token_in_its_git_config() -> None:
    """No step after the checkout uses the token from `trusted/`, so saving
    it there only leaves a copy in the same job as a fork's files."""
    assert checkout("trusted")["with"]["persist-credentials"] is False


def test_the_uv_cache_is_off() -> None:
    """Under `pull_request_target`, `setup-uv` saves its cache to the base
    branch's scope, under a key hashed from every `uv.lock` in the workspace,
    `pr/uv.lock` included. A fork could add a cache entry on every push and
    push CI's own entries out of the 10 GB limit."""
    (setup,) = [s for s in steps() if str(s.get("uses", "")).startswith("astral-sh/setup-uv")]

    assert setup["with"]["enable-cache"] is False


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


INSTALL = "uv sync --frozen --no-dev"

CHECK = '"$GITHUB_WORKSPACE/trusted/.venv/bin/wfctl" check reviews --base "$BASE_REF"'

IMPORT_CHECK = """\
git rev-parse --verify "origin/$DEFAULT^{commit}"
git show "origin/$DEFAULT:.github/scripts/check_imports.py" > "$RUNNER_TEMP/check_imports.py"
python3 -I "$RUNNER_TEMP/check_imports.py"
python3 -I "$RUNNER_TEMP/check_imports.py" --approvals --base "origin/$DEFAULT"
"""


def test_nothing_from_the_prs_checkout_is_executed() -> None:
    """The check runs `main`'s wfctl from `trusted/`. Installing or running
    anything from `pr/` would run the PR's code with the base token.

    A step that runs in `pr` must be one of the two listed here, word for
    word. The import check runs the default branch's copy of its script, read
    out of git into `$RUNNER_TEMP`, so it executes nothing the PR wrote.

    wfctl is installed in `trusted/`, and the only install step runs there.
    The check calls the installed binary by its full path, never through
    `uv run`. Run from `pr/`, `uv run ... wfctl` resolves `wfctl` against the
    working directory first, so a fork that adds a zip file named `wfctl`
    holding a `__main__.py` gets that file run in place of wfctl (#790)."""
    for step in steps():
        uses = str(step.get("uses", ""))
        assert not uses.startswith(("./", "pr/")), step
        run = step.get("run", "")
        assert not re.search(r"\b(uv run|uv tool run|uvx|pip install)\b", run), step
        if re.search(r"\buv sync\b", run):
            assert step.get("working-directory") == "trusted" and run.strip() == INSTALL, step
        if step.get("working-directory") == "pr":
            assert run in (IMPORT_CHECK, CHECK, CHECK + "\n"), step
    (check,) = [s for s in steps() if "check reviews" in s.get("run", "")]
    assert check["working-directory"] == "pr"


def test_ci_defaults_every_job_to_a_read_only_token() -> None:
    """The PR jobs in `ci.yml` run the PR's code. Without a top-level
    `permissions` key their token could push in this repository. The tag job
    sets its own write access, which overrides the default for that job."""
    ci = load(CI)

    assert ci["permissions"] == {"contents": "read"}
    assert ci["jobs"]["tag"]["permissions"]["contents"] == "write"


def import_step() -> dict[str, Any]:
    (found,) = [s for s in steps() if "check_imports.py" in s.get("run", "")]
    return found


def test_the_import_check_takes_the_default_branch_through_env() -> None:
    """The default branch, not the PR's base, so a stacked PR gets the same
    merge base and digest here as `wfctl arch approve-imports` gives it."""
    step = import_step()

    assert step["env"] == {"DEFAULT": "${{ github.event.repository.default_branch }}"}
    assert '--base "origin/$DEFAULT"' in step["run"]


def test_the_import_check_runs_the_default_branchs_copy_from_runner_temp_with_dash_i() -> None:
    """Outside both checkouts and with `-I`, so Python doesn't put the PR's
    directory first on the import path, where a PR's `ast.py` would load."""
    lines = import_step()["run"].splitlines()

    assert lines[1] == (
        'git show "origin/$DEFAULT:.github/scripts/check_imports.py" '
        '> "$RUNNER_TEMP/check_imports.py"'
    )
    runs = [line for line in lines if line.startswith("python")]
    assert runs == [
        'python3 -I "$RUNNER_TEMP/check_imports.py"',
        'python3 -I "$RUNNER_TEMP/check_imports.py" --approvals --base "origin/$DEFAULT"',
    ]


def test_the_import_check_runs_after_the_notes_are_fetched() -> None:
    """An approval is a note line, so a check that ran before the fetch would
    fail every approved branch."""
    names = [s.get("name") for s in steps()]

    assert names.index("Fetch the review notes") < names.index(import_step()["name"])


def test_the_lint_job_runs_the_branchs_copy_of_the_import_check() -> None:
    """The author sees a rule change working before it merges. It needs no
    history or notes, so the default shallow checkout is enough."""
    lint = load(CI)["jobs"]["lint"]["steps"]

    assert "python3 .github/scripts/check_imports.py" in [s.get("run") for s in lint]
