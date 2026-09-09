from __future__ import annotations

import os
import subprocess
import types
from collections.abc import Callable
from pathlib import Path

import pytest

from wfctl._pipeline import _REQUIRED_PLAN_SECTIONS, _REQUIRED_SPEC_SECTIONS

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

# NO_COLOR is not sufficient on its own: it suppresses *color*, and bold and dim
# are not color. Rich keeps emitting `\x1b[1m` and `\x1b[2m` whenever it believes
# it is writing to a terminal, and FORCE_COLOR is what settles that belief before
# any tty check runs (`Console.is_terminal`). Claude Code exports FORCE_COLOR=3,
# so on that machine 30 tests failed on a clean tree — every one of them
# asserting on a line styled bold or dim, while the green `✓` lines NO_COLOR
# already handled kept passing. Popping it is what makes the two agree.
os.environ.pop("FORCE_COLOR", None)

# Same shape, different variable. `WFCTL_SHAPE_ECHO=1` sends the `Stop` hook's
# report to stderr, and the tests that assert on that hook parse its stdout as
# JSON off a combined stream — so a developer who exported the flag to watch the
# check fire by hand, which is the only reason it exists, would find four tests
# failing on `Extra data`.
os.environ.pop("WFCTL_SHAPE_ECHO", None)


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


# A spec that satisfies both `specify` and `clarify`: no markers, and the
# `## Clarifications` section clarify writes on every run, including a clean scan.
# The sections `specify` requires, as the template writes them — suffix and all,
# because that is the form that reaches a real spec and the form the stem match
# has to tolerate. Built from the constant rather than typed out, so a change to
# the required list moves the fixtures with it instead of failing 39 tests that
# are about something else.
SPEC_SECTIONS = "".join(
    f"## {name} _(mandatory)_\n\nPlaceholder.\n\n" for name in _REQUIRED_SPEC_SECTIONS
)

# The same for `plan`. No suffix: `plan-template.md` marks nothing mandatory,
# which is why the two constants are spelled differently here as well as in the
# drift test.
PLAN_SECTIONS = "".join(
    f"## {name}\n\nPlaceholder.\n\n" for name in _REQUIRED_PLAN_SECTIONS
)

def structured(body: str) -> str:
    """`body` plus the sections `specify` requires, for a test about something else.

    A test asserting on markers, fenced blocks or the Clarifications section is
    not asserting on structure, and since #309 it needs the structure anyway or
    the step it is about never reports `done`. Wrapping keeps the test's own text
    the thing the reader sees — the sections are appended, not interleaved.
    """
    return body + "\n" + SPEC_SECTIONS


def _default_body(filename: str) -> str:
    """What an artifact holds when a test names it but not its text.

    `_file_exists` treats an empty file as absent, so this used to be the single
    character `x` — enough to be present and nothing more. Since #309 `specify`
    and `plan` read their artifact's sections, so `x` is no longer a spec or a
    plan: a fixture writing it produces a document the pipeline correctly refuses,
    and 39 tests about unrelated steps fail on it.

    So the default is the smallest document that satisfies the step reading it.
    Tests that want the shapeless case pass `content=` and say so — that case is
    the subject of `test_pipeline_sections.py`, and it should be written down
    where it is being asserted rather than inherited from a fixture default.
    """
    if filename == "spec.md":
        return CLEAN_SPEC
    if filename == "plan.md":
        return "# Plan\n\n" + PLAN_SECTIONS
    return "x"


CLEAN_SPEC = (
    "# Spec\n\nClean.\n\n"
    + SPEC_SECTIONS
    + "## Clarifications\n\n### Session 2026-08-25\n\n"
    "- No critical ambiguities detected.\n"
)

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

    # Both of these live inside the repo in this fixture, and neither does in a
    # real one: the state dir is XDG and `specs/` is gitignored by
    # `install-skills`. Left tracked, the fixture's own bookkeeping reads as
    # uncommitted work — which is invisible until something consults the working
    # tree. #69's verification record does, so every record arrived stale and the
    # step it gates could never report complete.
    (tmp_path / ".gitignore").write_text(".agent-runs/\nspecs/\n")
    subprocess.run(
        ["git", "-C", str(tmp_path), "add", ".gitignore"], check=True, capture_output=True
    )
    subprocess.run(
        ["git", "-C", str(tmp_path), "commit", "-m", "ignore wfctl state and specs"],
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

    def make_spec_artifact(step: str, content: str | None = None) -> Path:
        artifact: Path = _STEP_ARTIFACTS[step](tmp_path, spec_dir)  # type: ignore[operator]
        artifact.parent.mkdir(parents=True, exist_ok=True)
        artifact.write_text(content if content is not None else _default_body(artifact.name))
        return artifact

    def stage_upstream_of(step: str, tasks: str = "- [x] T001 done\n") -> None:
        """Create every artifact a step needs to be *reachable*.

        `_infer_steps` cascades: the first `○` marks everything after it `○` too,
        so a test that stages only the artifact it cares about asserts against a
        step the inference never reached. The failure is silent — the assertion
        sees a plausible symbol for the wrong reason.

        `specify` gets a spec carrying a `## Clarifications` section, because
        `clarify` reads `▶` without one and cascades just the same.
        """
        order = ("brainstorm", "specify", "plan", "analyze", "decompose", "tasks")
        for name in order[: order.index(step) + 1]:
            if name == "specify":
                make_spec_artifact("specify", content=CLEAN_SPEC)
            elif name == "tasks":
                make_spec_artifact("tasks", content=tasks)
            else:
                make_spec_artifact(name)

    return types.SimpleNamespace(
        agent_dir=agent_dir,
        spec_dir=spec_dir,
        repo_root=tmp_path,
        make_spec_artifact=make_spec_artifact,
        stage_upstream_of=stage_upstream_of,
    )


@pytest.fixture
def spec_tree(tmp_path: Path) -> Callable[..., Path]:
    """Build a feature dir holding exactly the named artifacts; return its path.

    `storyctl_dir` is the fixture for a command: it builds a repo, sets the env
    overrides, and stages every upstream artifact a step needs to be reachable.
    That staging is the wrong tool for a test about which state a step is *in* —
    it writes files the test never named, so the combination under assertion is
    not the combination on disk.

    Here the argument list is the whole input. `spec_tree("design.md")` is a
    feature that has brainstormed and nothing else, and there is no second place
    to look for what else got written. Suitable only for the pure inference
    functions, which take a directory and never resolve one.

    Content defaults to a non-empty placeholder because `_file_exists` treats an
    empty file as absent. Pass `content=` for the two artifacts whose text is
    read rather than counted — `spec.md` (markers, the Clarifications section)
    and `tasks.md` (checkbox tallies).
    """
    def build(*names: str, content: dict[str, str] | None = None) -> Path:
        feature = tmp_path / "specs" / "74-feature"
        feature.mkdir(parents=True, exist_ok=True)
        text = content or {}
        for name in (*names, *text):
            artifact = feature / name
            artifact.parent.mkdir(parents=True, exist_ok=True)
            artifact.write_text(text.get(name) or _default_body(artifact.name))
        return feature

    return build


@pytest.fixture
def repo_root(tmp_path: Path) -> Path:
    """Minimal initialized git repo for tests needing real repo root resolution.

    No commit — `git_repo` is the variant for tests that need one.
    """
    return init_git(tmp_path)
