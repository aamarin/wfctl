from __future__ import annotations

import os
import subprocess
import types
from pathlib import Path

import pytest

# Set before any wfctl import: `wfctl.cli` builds its `Console()` at module
# scope, and rich resolves the color system there — a fixture would run too
# late. Without this, rich emits ANSI whenever the terminal supports color, so
# `[green]✓[/green] Installed` arrives as `\x1b[32m✓\x1b[0m Installed` and
# assertions like `line.startswith("✓ Installed")` fail locally while passing in
# CI, which has no terminal. Tests must not depend on where they run.
#
# NO_COLOR is presence-only per https://no-color.org — rich tests
# `environ.get("NO_COLOR", "") != ""`, so *any* non-empty value disables color
# and only unsetting the variable re-enables it. Deliberately not "TRUE"/"FALSE":
# a boolean-looking value invites someone to write NO_COLOR=FALSE expecting color
# back, and get no color. The "1" is arbitrary and ignored; this comment is the
# documentation.
os.environ["NO_COLOR"] = "1"


def init_git(path: Path) -> Path:
    """An initialized git repo at `path`, with a committer identity and no commits.

    The identity is not cosmetic: `git commit` fails outright when neither the
    repo nor the environment supplies one, and CI has no global config.
    """
    path.mkdir(parents=True, exist_ok=True)
    subprocess.run(["git", "init", str(path)], check=True, capture_output=True)
    for key, val in (("user.email", "test@test.com"), ("user.name", "Test")):
        subprocess.run(["git", "-C", str(path), "config", key, val],
                       check=True, capture_output=True)
    return path


def git_repo(path: Path) -> Path:
    """`init_git` plus one commit.

    The commit is the whole difference: `git worktree add` needs a ref to branch
    from, and the root-resolution tests exercise the main-checkout fallback from
    a worktree. Shared rather than copied because `test_spec_root` and
    `test_arch_root` cover two resolvers built on one walk, so a fixture drifting
    between them would hide the divergence they exist to catch.
    """
    init_git(path)
    (path / "README.md").write_text("x\n")
    subprocess.run(["git", "-C", str(path), "add", "README.md"], check=True, capture_output=True)
    subprocess.run(["git", "-C", str(path), "commit", "-m", "init"], check=True, capture_output=True)
    return path


@pytest.fixture(autouse=True)
def _tool_version_is_not_under_test(
    request: pytest.FixtureRequest, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Stub `doctor`'s tool-version check for every test in the suite.

    Left live, it resolves the newest published tag over the network and compares
    it against this environment's installed metadata, then contributes to
    `doctor`'s exit code. Any test asserting that exit code therefore reports
    whether the machine running it happens to be current — three did, and all
    three went red the moment v0.14.0 was tagged, on a change that touched none of
    them.

    A build behind the newest tag is a normal state: a contributor who installed
    last week, CI on a checkout predating the tag, anyone mid-release. None of
    that is a test failure. Autouse rather than per-test so a future test cannot
    reintroduce the dependency by forgetting.

    Also removes the suite's only unavoidable network call, so it runs offline.
    The check's own behaviour is still tested, by the two cases marked
    `real_version_check` — they stub `ls-remote` and the installed version
    themselves, which is the only honest way to assert on a comparison between
    the two.
    """
    if "real_version_check" in request.keywords:
        return
    monkeypatch.setattr("wfctl.cli._check_wfctl_version", lambda: False)


@pytest.fixture(autouse=True)
def bundle(
    tmp_path_factory: pytest.TempPathFactory, monkeypatch: pytest.MonkeyPatch
) -> Path:
    """Point the vendored-tree lookup at a fake bundle for every test.

    Autouse because the alternative is opt-in, and a test that forgets reads the
    real `wfctl/agents/` — passing for the wrong reason, and coupling assertions
    about installed content to whatever wf-skills happened to ship. Returns the
    root so a test needing particular content can add to it.

    Built under `tmp_path_factory` rather than the test's own `tmp_path`: many
    tests use `tmp_path` as the destination repo root, and a bundle unpacked
    there would show up inside the repo under test.
    """
    root = tmp_path_factory.mktemp("bundle")
    skill = root / "agents" / "skills" / "test-skill"
    skill.mkdir(parents=True)
    (skill / "SKILL.md").write_text("# test-skill\n")
    commands = root / "agents" / "commands"
    commands.mkdir(parents=True)
    (commands / "test-cmd.md").write_text("# test-cmd\n")
    monkeypatch.setattr("wfctl._bundle.BUNDLE_ROOT", root)
    return root


@pytest.fixture
def agent_dir(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Isolated state dir backed by a real git repo — wfctl resolves the branch
    and repo root by shelling out to git."""
    subprocess.run(["git", "init", str(tmp_path)], check=True, capture_output=True)
    subprocess.run(
        ["git", "-C", str(tmp_path), "config", "user.email", "test@test.com"],
        check=True, capture_output=True,
    )
    subprocess.run(
        ["git", "-C", str(tmp_path), "config", "user.name", "Test"],
        check=True, capture_output=True,
    )
    (tmp_path / "README.md").write_text("test\n")
    subprocess.run(
        ["git", "-C", str(tmp_path), "add", "README.md"], check=True, capture_output=True
    )
    subprocess.run(
        ["git", "-C", str(tmp_path), "commit", "-m", "init"],
        check=True, capture_output=True,
    )
    d = tmp_path / ".wfctl-state"
    d.mkdir()
    monkeypatch.setenv("WFCTL_STATE_DIR", str(d))
    monkeypatch.setenv("WFCTL_BRANCH", "342-state-workflow")
    monkeypatch.setenv("WFCTL_REPO_ROOT", str(tmp_path))
    return d


_STEP_ARTIFACTS: dict[str, object] = {
    "brainstorm": lambda root, spec: spec / "design.md",
    "specify":    lambda root, spec: spec / "spec.md",
    # no "clarify" — its artifact is a section inside specify's spec.md, so writing
    # it through this helper would clobber the spec instead of appending to it
    "plan":       lambda root, spec: spec / "plan.md",
    "tasks":      lambda root, spec: spec / "tasks.md",
    "analyze":    lambda root, spec: spec / "checklists" / "analysis-report.md",
    "decompose":  lambda root, spec: spec / "delivery.md",
    "implement":  lambda root, spec: spec / "tasks.md",
}


@pytest.fixture
def storyctl_dir(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> types.SimpleNamespace:
    """Isolated fixture: git repo + specs layout + env overrides."""
    subprocess.run(["git", "init", str(tmp_path)], check=True, capture_output=True)
    subprocess.run(
        ["git", "-C", str(tmp_path), "config", "user.email", "test@test.com"],
        check=True, capture_output=True,
    )
    subprocess.run(
        ["git", "-C", str(tmp_path), "config", "user.name", "Test"],
        check=True, capture_output=True,
    )
    (tmp_path / "README.md").write_text("test\n")
    subprocess.run(
        ["git", "-C", str(tmp_path), "add", "README.md"], check=True, capture_output=True
    )
    subprocess.run(
        ["git", "-C", str(tmp_path), "commit", "-m", "init"],
        check=True, capture_output=True,
    )

    agent_dir = tmp_path / ".agent-runs"
    agent_dir.mkdir()
    spec_dir = tmp_path / "specs" / "418-storyctl"
    spec_dir.mkdir(parents=True)

    monkeypatch.setenv("WFCTL_STATE_DIR", str(agent_dir))
    monkeypatch.setenv("WFCTL_BRANCH", "418-storyctl")
    monkeypatch.setenv("WFCTL_SPEC_DIR", str(tmp_path / "specs"))
    monkeypatch.setenv("WFCTL_REPO_ROOT", str(tmp_path))

    def make_spec_artifact(step: str, content: str = "x") -> Path:
        artifact: Path = _STEP_ARTIFACTS[step](tmp_path, spec_dir)  # type: ignore[operator]
        artifact.parent.mkdir(parents=True, exist_ok=True)
        artifact.write_text(content)
        return artifact

    return types.SimpleNamespace(
        agent_dir=agent_dir,
        spec_dir=spec_dir,
        repo_root=tmp_path,
        make_spec_artifact=make_spec_artifact,
    )


@pytest.fixture
def repo_root(tmp_path: Path) -> Path:
    """Minimal initialized git repo for tests needing real repo root resolution.

    No commit — `git_repo` is the variant for tests that need one.
    """
    return init_git(tmp_path)
