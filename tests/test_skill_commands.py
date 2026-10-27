"""A shell command a shipped skill tells the agent to run does what its prose says.

Every other test here checks that skills ship, cross-reference, and declare the
right frontmatter — all properties of the file. This one runs what is inside it.

The lookup in `opening-a-change` was wrong twice before it was tested. First it
was an `ls` over a path list containing globs, which under `zsh` aborts the whole
command line when one glob matches nothing and reports *no template* in a repo
that has one. Then it matched `-iname` against basenames, which finds the
`PULL_REQUEST_TEMPLATE/` directory and none of the files inside it. Both failures
are silent and both end the same way: the agent takes the fallback shape and the
project's template goes unread, which is the failure #124 exists to prevent.
"""
import re
import shutil
import subprocess
from importlib.resources import files
from pathlib import Path

import pytest

_SKILL = (
    Path(str(files("wfctl"))) / "agents" / "skills" / "opening-a-change" / "SKILL.md"
)

# The one fenced block that finds templates. Keyed on the content rather than on
# "the first bash fence": Step 5's `gh pr create` is also a bash fence, and an
# edit reordering the sections must not silently retarget this test.
_FENCE = re.compile(r"```bash\n(.*?)```", re.DOTALL)


def _lookup_command() -> str:
    blocks = [b for b in _FENCE.findall(_SKILL.read_text()) if "template" in b]
    assert len(blocks) == 1, f"expected one template-lookup fence, found {len(blocks)}"
    return blocks[0]


def _fixture(root: Path) -> None:
    """The three layouts a real repo uses, plus a decoy inside `.git`."""
    for rel in (
        ".github/PULL_REQUEST_TEMPLATE/bug.md",
        ".github/PULL_REQUEST_TEMPLATE/feature.md",
        ".gitlab/merge_request_templates/Default.md",
        ".git/objects/ab/pull_request_template.md",
    ):
        path = root / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("# t\n")


def _run(shell: str, root: Path) -> list[str]:
    out = subprocess.run(
        [shell, "-c", _lookup_command()], cwd=root, capture_output=True, text=True
    )
    return sorted(line for line in out.stdout.splitlines() if line)


def test_the_lookup_finds_multi_template_directories(tmp_path: Path) -> None:
    """The skill's own prose tells the agent to ask which template applies when a
    repo has a `PULL_REQUEST_TEMPLATE/` directory. A lookup that cannot see into
    that directory makes the instruction unreachable and reports no template at
    all — the command and the prose have to agree."""
    _fixture(tmp_path)

    assert _run("sh", tmp_path) == [
        "./.github/PULL_REQUEST_TEMPLATE/bug.md",
        "./.github/PULL_REQUEST_TEMPLATE/feature.md",
        "./.gitlab/merge_request_templates/Default.md",
    ]


def test_the_lookup_finds_a_single_template_and_ignores_git(tmp_path: Path) -> None:
    """The common case, and the pruning that keeps a blob in the object store from
    being offered as the project's template."""
    _fixture(tmp_path)
    (tmp_path / ".github" / "pull_request_template.md").write_text("# t\n")

    found = _run("sh", tmp_path)

    assert "./.github/pull_request_template.md" in found
    assert not [f for f in found if ".git/" in f]


def test_the_lookup_survives_zsh(tmp_path: Path) -> None:
    """zsh aborts a command line when a glob matches nothing, which is how the
    first version of this lookup failed. Skipped where zsh is absent — CI runs
    Ubuntu — so this is the macOS half of the guarantee, and `sh` above is the
    half that always runs."""
    if not shutil.which("zsh"):
        return
    _fixture(tmp_path)

    assert _run("zsh", tmp_path) == _run("sh", tmp_path)


def _open_commands() -> list[str]:
    """Step 5's fences, each a single command."""
    text = _SKILL.read_text()
    step = text.split("## Step 5: Open it")[1].split("## Step 6")[0]
    return [b.strip() for b in _FENCE.findall(step)]


def test_step_5_runs_check_body_and_gh_pr_create_as_two_commands() -> None:
    """The guard refuses `gh pr create` after a separator, a substitution, or an
    environment prefix (FR-012b). Step 5 once set the body path with
    `$(git branch --show-current)` and ran both commands in one block, which
    the guard refuses every time."""
    commands = _open_commands()

    assert [c.split()[:2] for c in commands] == [["wfctl", "check-body"], ["gh", "pr"]]
    for command in commands:
        assert "\n" not in command
        assert "/tmp/pr-body-622-security-review-panel.md" in command
        assert not re.search(r"\$\(|`|[;&|]|^[A-Za-z_]+=|\benv\b", command), command


def test_step_5s_gh_pr_create_passes_the_guard_on_a_reviewed_branch(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The skill's own command has to pass the check it teaches, or every PR
    this repo opens by the skill is refused until someone rewords it by hand."""
    import json

    from tests.test_review import review_repo
    from tests.test_review_gate import commit
    from wfctl import _hook, _review, _review_config
    from wfctl._paths import resolve_review_dir

    repo = review_repo(tmp_path, monkeypatch)
    commit(repo, "change.txt")
    agent_dir = resolve_review_dir(repo, "637-x")
    for group in _review_config.load(repo)[0]:
        started = _review.start(repo, agent_dir, group, cap=9)
        assert started.run is not None
        for rid in started.expected:
            (started.run.path / f"{rid}.md").write_text(
                f"Reviewed: {started.head[:7]}\n\nNo findings.\n\nVerdict: Approve\n"
            )
        assert _review.check(agent_dir, group.name).complete

    line = _open_commands()[1].replace("622-security-review-panel", "637-x")
    payload = json.dumps({"tool_input": {"command": line}, "cwd": str(repo)})

    assert _hook.worktree_guard(payload.encode()) == 0
