"""Tests for wfctl install-skills command."""
from __future__ import annotations

import contextlib
import json
import shlex
import shutil
import subprocess
from collections.abc import Iterator
from importlib.metadata import version
from pathlib import Path

import pytest
from typer.testing import CliRunner

from wfctl.cli import _MIRRORED_SKILLS, _recorded_items, app

runner = CliRunner()


@contextlib.contextmanager
def _edit_manifest(repo_root: Path) -> Iterator[dict]:
    """Round-trip the manifest so a test can bend one field and write it back.

    doctor's states differ only in what the record claims versus what the bundle
    now hashes to. Bending the record reaches states the bundle cannot be edited
    into — a version that is not the running one, a key that predates it.
    """
    path = repo_root / ".wf-skills-manifest.json"
    manifest = json.loads(path.read_text())
    yield manifest
    path.write_text(json.dumps(manifest))


def test_install_skills_copies_skills(agent_dir: Path) -> None:
    import os
    repo_root = os.environ["WFCTL_REPO_ROOT"]
    result = runner.invoke(app, ["install-skills"])
    assert result.exit_code == 0
    assert (Path(repo_root) / ".agents" / "skills" / "test-skill" / "SKILL.md").exists()


def test_install_skills_copies_commands(agent_dir: Path) -> None:
    import os
    repo_root = os.environ["WFCTL_REPO_ROOT"]
    runner.invoke(app, ["install-skills", "--agent", "claude"])
    assert (Path(repo_root) / ".claude" / "commands" / "test-cmd.md").exists()


def test_install_skills_gitignores_installed_paths(agent_dir: Path) -> None:
    """Installed skill/command paths and the manifest/backup dir land in .gitignore,
    so a sync never dirties whatever branch happens to be checked out."""
    import os
    repo_root = Path(os.environ["WFCTL_REPO_ROOT"])
    result = runner.invoke(app, ["install-skills", "--agent", "claude"])
    assert result.exit_code == 0
    gitignore = (repo_root / ".gitignore").read_text().splitlines()
    assert ".agents/skills/test-skill" in gitignore
    assert ".claude/commands/test-cmd.md" in gitignore
    assert ".wf-skills-manifest.json" in gitignore
    assert ".wf-skills-backup/" in gitignore


def test_install_skills_does_not_gitignore_tracker_config(
    bundle: Path, agent_dir: Path
) -> None:
    """Tracker config is project-owned and meant to be committed, not managed
    as install-skills output — must not end up in .gitignore."""
    import os
    _add_tracker(bundle, "{}\n")

    repo_root = Path(os.environ["WFCTL_REPO_ROOT"])
    result = runner.invoke(
        app, ["install-skills", "--tracker", "github"]
    )
    assert result.exit_code == 0
    gitignore = (repo_root / ".gitignore").read_text() if (repo_root / ".gitignore").exists() else ""
    assert ".agents/trackers/github.json" not in gitignore.splitlines()


def test_install_skills_does_not_gitignore_the_definition_of_done(agent_dir: Path) -> None:
    """`wfctl.json` is hand-authored and must stay tracked (FR-011).

    Satisfied by construction today: the ignore list is built by appending each
    path install-skills is about to write, and it never writes this one. The
    assertion pins the property rather than that implementation — the list is
    assembled inside two loops, and a future change that ships a starter config
    would silently ignore the file every CI run and every fresh clone depends on.
    """
    import os
    repo_root = Path(os.environ["WFCTL_REPO_ROOT"])
    (repo_root / "wfctl.json").write_text('{"verify": [["pytest", "-q"]]}\n')

    result = runner.invoke(app, ["install-skills", "--agent", "claude"])
    assert result.exit_code == 0

    gitignore = (repo_root / ".gitignore")
    lines = gitignore.read_text().splitlines() if gitignore.exists() else []
    assert "wfctl.json" not in lines
    assert not any(line.strip().rstrip("/") == "wfctl.json" for line in lines)

    tracked = subprocess.run(
        ["git", "-C", str(repo_root), "check-ignore", "wfctl.json"],
        capture_output=True, text=True,
    )
    assert tracked.returncode != 0, "wfctl.json is ignored by some rule"


def _add_tracker(bundle: Path, body: str = '{"verbs": {}}\n') -> None:
    """Give the `bundle` fixture the tracker config it deliberately omits.

    Absent by default so the tracker prompt and its warning branch are both
    reachable; every test that wants the config present asks for it here.
    """
    tracker_dir = bundle / "agents" / "trackers"
    tracker_dir.mkdir(parents=True, exist_ok=True)
    (tracker_dir / "github.json").write_text(body)
    # The backend is two files. Omitting the script here would leave every
    # caller testing a github backend that cannot run its own `start`.
    (tracker_dir / "github-board.sh").write_text("#!/usr/bin/env bash\nexit 0\n")


def test_install_skills_no_tracker_without_a_human(bundle: Path, agent_dir: Path) -> None:
    """A non-interactive install never commits a tracker config nobody asked for."""
    import json
    import os
    _add_tracker(bundle)
    repo_root = Path(os.environ["WFCTL_REPO_ROOT"])
    result = runner.invoke(app, ["install-skills"])
    assert result.exit_code == 0
    assert not (repo_root / ".agents" / "trackers" / "github.json").exists()
    manifest = json.loads((repo_root / ".wf-skills-manifest.json").read_text())
    assert "tracker" not in manifest


@pytest.mark.parametrize("answer,expected", [("y\n", True), ("n\n", False)])
def test_install_skills_prompts_for_tracker(bundle: Path, 
    agent_dir: Path, monkeypatch: pytest.MonkeyPatch, answer: str, expected: bool
) -> None:
    """First interactive install offers the GitHub tracker; declining installs nothing.

    Either answer is a choice, so both are recorded — see
    test_declining_the_tracker_is_not_asked_again for why declining writes a
    key at all.
    """
    import json
    import os
    from wfctl import cli
    monkeypatch.setattr(cli, "_interactive", lambda: True)
    _add_tracker(bundle)
    repo_root = Path(os.environ["WFCTL_REPO_ROOT"])
    result = runner.invoke(
        app, ["install-skills"],
        # "1" answers the spec-location question that follows: this test is about
        # the tracker, and option 1 records no spec_root, so it changes nothing here.
        input=answer + "1\n",
    )
    assert result.exit_code == 0
    assert (repo_root / ".agents" / "trackers" / "github.json").exists() is expected
    manifest = json.loads((repo_root / ".wf-skills-manifest.json").read_text())
    assert manifest["tracker"] == ("github" if expected else None)
    if not expected:  # declining points at both ways back in
        assert "--tracker github" in result.output
        assert "/scaffold-tracker" in result.output


def test_install_skills_keeps_existing_tracker_config(bundle: Path, agent_dir: Path) -> None:
    """Once a tracker is chosen, a plain re-install leaves the config alone —
    local edits to it survive."""
    import os
    _add_tracker(bundle)
    repo_root = Path(os.environ["WFCTL_REPO_ROOT"])
    runner.invoke(
        app,
        ["install-skills", "--tracker", "github"],
    )

    cfg = repo_root / ".agents" / "trackers" / "github.json"
    cfg.write_text('{"verbs": {"list": ["gh", "issue", "list", "--limit", "30"]}}\n')
    result = runner.invoke(app, ["install-skills"])
    assert result.exit_code == 0
    assert "--limit" in cfg.read_text()


def test_install_skills_tracker_none_opts_out(bundle: Path, agent_dir: Path) -> None:
    """--tracker none opts out without a prompt."""
    import json
    import os
    _add_tracker(bundle)
    repo_root = Path(os.environ["WFCTL_REPO_ROOT"])
    result = runner.invoke(
        app, ["install-skills", "--tracker", "none"]
    )
    assert result.exit_code == 0
    manifest = json.loads((repo_root / ".wf-skills-manifest.json").read_text())
    assert "tracker" not in manifest
    assert not (repo_root / ".agents" / "trackers" / "github.json").exists()


@pytest.fixture
def declared_mirror(monkeypatch: pytest.MonkeyPatch) -> None:
    """Narrow the discoverable set to the one skill these tests create.

    The real set names skills that the `bundle` fixture does not ship, so a test
    left reading it would assert against the installer's production list rather
    than the fixture in front of it.
    """
    monkeypatch.setattr("wfctl.cli._MIRRORED_SKILLS", frozenset({"native-skill"}))


def test_install_skills_skips_native_mirror_by_default(
    agent_dir: Path, declared_mirror: None
) -> None:
    """A skill absent from the declared set stays reference-only."""
    import os
    repo_root = Path(os.environ["WFCTL_REPO_ROOT"])
    runner.invoke(app, ["install-skills"])
    assert not (repo_root / ".claude" / "skills").exists()


def test_install_skills_mirrors_native_skill_for_claude(
    bundle: Path, agent_dir: Path, declared_mirror: None
) -> None:
    """A name in the declared set also mirrors to .claude/skills/<name>.

    The fixture's frontmatter carries nothing wfctl wrote, which is the point:
    membership is decided by name alone, so a vendored skill taken unmodified can
    be mirrored and stay mirrored across an upstream replacement (FR-004). The
    frontmatter mechanism this replaced could not express that.
    """
    import os
    native = bundle / "agents" / "skills" / "native-skill"
    native.mkdir(parents=True)
    (native / "SKILL.md").write_text("---\nname: native-skill\n---\nBody.\n")

    repo_root = Path(os.environ["WFCTL_REPO_ROOT"])
    result = runner.invoke(app, ["install-skills", "--agent", "claude"])
    assert result.exit_code == 0
    # Still gets the reference-only mirror every agent gets...
    assert (repo_root / ".agents" / "skills" / "native-skill" / "SKILL.md").exists()
    # ...plus the Claude-native discovery mirror.
    assert (repo_root / ".claude" / "skills" / "native-skill" / "SKILL.md").exists()
    # The undeclared skill from the base fixture is not mirrored.
    assert not (repo_root / ".claude" / "skills" / "test-skill").exists()


def test_install_skills_bob_ignores_declared_mirror_set(
    bundle: Path, agent_dir: Path, declared_mirror: None
) -> None:
    """The .claude/skills mirror is Claude-specific; bob never gets it."""
    import os
    native = bundle / "agents" / "skills" / "native-skill"
    native.mkdir(parents=True)
    (native / "SKILL.md").write_text("---\nname: native-skill\n---\nBody.\n")

    repo_root = Path(os.environ["WFCTL_REPO_ROOT"])
    result = runner.invoke(
        app, ["install-skills", "--agent", "bob"]
    )
    assert result.exit_code == 0
    assert not (repo_root / ".claude").exists()


def test_uninstall_removes_native_skill_mirror(
    bundle: Path, agent_dir: Path, declared_mirror: None
) -> None:
    import os
    native = bundle / "agents" / "skills" / "native-skill"
    native.mkdir(parents=True)
    (native / "SKILL.md").write_text("---\nname: native-skill\n---\nBody.\n")

    repo_root = Path(os.environ["WFCTL_REPO_ROOT"])
    runner.invoke(app, ["install-skills", "--agent", "claude"])
    assert (repo_root / ".claude" / "skills" / "native-skill").exists()

    runner.invoke(app, ["uninstall-skills", "--agent", "claude"])
    assert not (repo_root / ".claude" / "skills" / "native-skill").exists()


# The mirrored skills that also ship a command wrapper — the set
# `_mirror_supersedes_wrapper` acts on. Pinned rather than derived, because
# deriving it from the two directories is what the tests below would then be
# asserting against itself: the intersection is exactly the thing that has to be
# noticed when it changes.
_SUPPRESSED_ON_A_MIRRORING_LAYER = frozenset({
    "conversation-response-shape",
    "fanning-out-code-review",
    "i-have-adhd",
    "opening-a-change",
    "receiving-code-review",
    "start-session",
    "verification-before-completion",
    "worktree-handoff",
})


def test_every_suppressed_wrapper_still_ships_in_the_bundle() -> None:
    """The wrappers the Claude layer skips are still in the bundle for the layers
    that need them.

    Suppression is per layer and works only because the file still exists —
    `.bob/commands/` installs it with `_copy_command_for_bob` stripping the key
    Bob Shell reads as "never execute the body" (#182 tracks that claim's
    provenance), and `.bob/skills/` gets the vendored `i-have-adhd` with that key
    intact. Delete the wrapper from the bundle and bob has no route left.

    That is not hypothetical: it is what the first version of #170's fix did, and
    it is invisible to every other test here. Deleting five of these seven leaves
    the suite at 838 passed, because the install-level tests build their own
    wrapper inside the `bundle` fixture and never read the shipped tree.

    Resolved from the installed package for `test_every_declared_mirror_names_a_
    shipped_skill`'s reason: the autouse `bundle` fixture repoints `BUNDLE_ROOT`
    at a fixture tree holding none of these names.
    """
    import wfctl
    from wfctl.cli import _MIRRORED_SKILLS

    agents = Path(wfctl.__file__).parent / "agents"
    assert _SUPPRESSED_ON_A_MIRRORING_LAYER <= _MIRRORED_SKILLS
    missing = sorted(
        n for n in _SUPPRESSED_ON_A_MIRRORING_LAYER
        if not (agents / "commands" / f"{n}.md").exists()
    )

    assert missing == []


def test_no_suppressed_wrapper_carries_more_than_a_pointer() -> None:
    """A wrapper that is suppressed must hold nothing its skill does not.

    Suppression drops the whole file, so anything the wrapper carries beyond
    "read the skill" is dropped with it — silently, and only on the mirroring
    layer. `end-session.md` is the live example: it carries an `allowed-tools:`
    pre-approval its SKILL.md does not, so adding that name to `_MIRRORED_SKILLS`
    would revoke it on the Claude layer with the suite still green.

    `start-session.md` was the other, and #204 mirrored it — by moving the key
    onto the SKILL.md first, which is what this test asks for. It is the worked
    example of paying the price rather than exempting the name.

    `description` and `disable-model-invocation` are the two keys a pointer needs
    — one to be findable, one to say a human types it — and neither survives into
    a mirrored skill's behaviour, because the skill file supplies both itself.
    """
    import wfctl
    from wfctl import _arch
    from wfctl.cli import _MIRRORED_SKILLS

    # Derived from `_MIRRORED_SKILLS`, not from the pinned set above: the whole
    # failure is a name being *added* to that set, and a loop over the pinned
    # seven would never see the addition it exists to catch.
    commands = Path(wfctl.__file__).parent / "agents" / "commands"
    carrying = {}
    for name in sorted(n for n in _MIRRORED_SKILLS if (commands / f"{n}.md").exists()):
        keys = set(_arch._frontmatter((commands / f"{name}.md").read_text()))
        extra = sorted(keys - {"description", "disable-model-invocation"})
        if extra:
            carrying[name] = extra

    assert carrying == {}


def test_every_declared_mirror_names_a_shipped_skill() -> None:
    """A name in `_MIRRORED_SKILLS` that matches no skill directory fails here.

    The failure it catches is silent: rename or remove a skill and its entry in
    the set becomes a no-op, so the skill simply stops being discoverable and
    every other test still passes. The set is a declaration, and a declaration
    nothing checks is a comment.

    Resolved from the installed package, not `BUNDLE_ROOT` — the autouse
    `bundle` fixture repoints that at a fixture tree with none of these names in
    it, which would make this assert against the fixture instead of the bundle.
    """
    import wfctl
    from wfctl.cli import _MIRRORED_SKILLS

    skills_root = Path(wfctl.__file__).parent / "agents" / "skills"
    missing = sorted(n for n in _MIRRORED_SKILLS if not (skills_root / n).is_dir())

    assert missing == []


def test_the_mirror_suppresses_the_wrapper_it_collides_with(
    bundle: Path, agent_dir: Path, declared_mirror: None
) -> None:
    """A mirrored skill's wrapper does not land in `.claude/commands/`.

    Both files claim one `/name`, and which wins is not wfctl's to set: Claude
    Code documents the skill as winning, and a session on 2026-09-04 got the
    wrapper, whose `disable-model-invocation` refused the Skill tool for the very
    skill it points at, while another session the same day got the skill (#170).
    Shipping both is shipping the tie.

    The `.agents/` assertion is the half that keeps this honest. Deleting the
    wrapper from the bundle passes the first assertion too, and takes bob's only
    working route to `i-have-adhd` with it — `.bob/commands/` gets the copy
    `_copy_command_for_bob` strips, and `.bob/skills/` gets the vendored key
    intact.
    """
    import os
    native = bundle / "agents" / "skills" / "native-skill"
    native.mkdir(parents=True)
    (native / "SKILL.md").write_text("---\nname: native-skill\n---\nBody.\n")
    (bundle / "agents" / "commands" / "native-skill.md").write_text(
        "---\ndisable-model-invocation: true\n---\nRead the skill.\n"
    )

    repo_root = Path(os.environ["WFCTL_REPO_ROOT"])
    result = runner.invoke(app, ["install-skills", "--agent", "claude"])
    assert result.exit_code == 0
    assert not (repo_root / ".claude" / "commands" / "native-skill.md").exists()
    assert (repo_root / ".agents" / "commands" / "native-skill.md").exists()


def test_an_unmirrored_wrapper_still_reaches_the_claude_layer(
    bundle: Path, agent_dir: Path, declared_mirror: None
) -> None:
    """Suppression is scoped to the colliding name, not to the command layer.

    Worth its own test because the guard sits in the loop that builds every
    layer's plan: a predicate that returned True too broadly would empty
    `.claude/commands/` entirely, and the collision test above would still pass —
    it only ever asserts a file is absent.
    """
    import os
    (bundle / "agents" / "commands" / "plain-command.md").write_text("Body.\n")

    repo_root = Path(os.environ["WFCTL_REPO_ROOT"])
    result = runner.invoke(app, ["install-skills", "--agent", "claude"])
    assert result.exit_code == 0
    assert (repo_root / ".claude" / "commands" / "plain-command.md").exists()


def test_bob_keeps_the_wrapper_for_a_mirrored_skill(
    bundle: Path, agent_dir: Path, declared_mirror: None
) -> None:
    """Only the layer that got the mirror drops the wrapper.

    bob gets no `.claude/skills` mirror, so for bob the wrapper is not redundant
    — it is the route. And for `i-have-adhd` it is the only working one: the
    skills copy is a `copytree` that never reaches `_copy_command_for_bob`, so
    `.bob/skills/i-have-adhd/SKILL.md` keeps upstream's
    `disable-model-invocation`, which cli.py records as making Bob Shell skip
    model invocation entirely — the body never executes.

    This is the test that fails if someone "simplifies" the suppression by
    deleting the seven wrappers from the bundle instead. Three reviewers found
    that regression by reading the diff; nothing in the suite caught it.
    """
    import os
    native = bundle / "agents" / "skills" / "native-skill"
    native.mkdir(parents=True)
    (native / "SKILL.md").write_text("---\nname: native-skill\n---\nBody.\n")
    (bundle / "agents" / "commands" / "native-skill.md").write_text(
        "---\ndisable-model-invocation: true\n---\nRead the skill.\n"
    )

    repo_root = Path(os.environ["WFCTL_REPO_ROOT"])
    result = runner.invoke(app, ["install-skills", "--agent", "bob"])
    assert result.exit_code == 0
    wrapper = repo_root / ".bob" / "commands" / "native-skill.md"
    assert wrapper.exists()
    assert "disable-model-invocation" not in wrapper.read_text()


def test_installed_tree_is_never_a_mirror_source(
    agent_dir: Path, declared_mirror: None
) -> None:
    """A skill sitting in the destination `.agents/skills/` but in no bundle is
    never mirrored.

    Worth a test because the mirror set is computed from the wheel's own bundle,
    and nothing in the code says so out loud. A future change that walked the
    installed tree instead would still pass every other test here — the
    declaration and its reader would disagree, and the only symptom would be a
    hand-authored directory quietly becoming discoverable.
    """
    import os
    repo_root = Path(os.environ["WFCTL_REPO_ROOT"])
    squatter = repo_root / ".agents" / "skills" / "native-skill"
    squatter.mkdir(parents=True)
    (squatter / "SKILL.md").write_text("---\nname: native-skill\n---\nBody.\n")

    result = runner.invoke(app, ["install-skills", "--agent", "claude", "--yes"])

    assert result.exit_code == 0
    # Asserted first: if the install had removed the squatter, the real
    # assertion below would hold for a reason that has nothing to do with FR-008.
    assert squatter.exists()
    assert not (repo_root / ".claude" / "skills" / "native-skill").exists()


def test_removed_source_options_are_an_error(agent_dir: Path) -> None:
    """`--repo`/`--ref` fail loudly rather than being accepted and ignored.

    Both commands took them, and both are in people's shell history and in
    scripts. Typer rejects an unknown option with exit 2 and names it, which is
    the whole behaviour — asserted rather than assumed, because a stray
    `**kwargs` or a re-added option would silently make an install read from
    the network again.
    """
    for argv in (["install-skills", "--repo", "x"], ["install-config", "workmux", "--ref", "y"]):
        result = runner.invoke(app, argv)
        assert result.exit_code == 2, argv
        assert "No such option" in result.output, argv
        # Not the flag as written: typer highlights it, and the ANSI it inserts
        # lands between the two dashes. The stem is what survives that.
        assert argv[-2].lstrip("-") in result.output, argv


def test_no_module_can_still_clone_the_archived_upstream() -> None:
    """No module holds the wf-skills clone URL any more (FR-003, SC-006).

    The URL, not the bare `aamarin/wf-skills`, which FR-003 does not forbid:
    `_bundle.BUNDLE_SOURCE` records the revision this tree was copied from, and
    `_archive.py` cites an issue in that repo. Neither reaches a network. What
    must not come back is the thing an option default or a `git clone` would
    need, and that always carries the host.

    Only `wfctl/*.py` is scanned: the vendored trees are wf-skills' own content,
    and a skill documenting its origin is not a runtime source.
    """
    root = Path(__file__).resolve().parent.parent / "wfctl"
    offenders = [
        f"{p.relative_to(root).as_posix()}:{n}"
        for p in root.rglob("*.py")
        if p.relative_to(root).parts[0] not in ("agents", "specify")
        for n, line in enumerate(p.read_text().splitlines(), 1)
        if "github.com/aamarin/wf-skills" in line
    ]
    assert offenders == [], f"can still clone the archived upstream: {offenders}"


def test_install_skills_reports_what_it_installed(agent_dir: Path, tmp_path: Path) -> None:
    """The summary names the source it installed from.

    The single `Installed N item(s)` total this used to assert is gone: N
    conflated skills, commands, runtime files and the tracker config into one
    number that read as a skill count. Per-layer, per-kind counts are asserted
    by test_install_summary_reports_per_layer_counts.
    """
    result = runner.invoke(
        app,
        ["install-skills", "--agent", "claude"],
    )
    assert result.exit_code == 0
    assert f"Installed from wfctl {version('wfctl')}" in result.output


def test_install_skills_bob_writes_skills_to_bob_dir(agent_dir: Path) -> None:
    import os
    repo_root = Path(os.environ["WFCTL_REPO_ROOT"])
    result = runner.invoke(
        app, ["install-skills", "--agent", "bob"]
    )
    assert result.exit_code == 0
    assert (repo_root / ".bob" / "skills" / "test-skill" / "SKILL.md").exists()
    assert (repo_root / ".bob" / "commands" / "test-cmd.md").exists()
    assert not (repo_root / ".claude").exists()


def test_install_skills_unknown_agent_exits_one(agent_dir: Path) -> None:
    result = runner.invoke(
        app, ["install-skills", "--agent", "nope"]
    )
    assert result.exit_code == 1


def test_install_skills_warns_on_missing_source_path(bundle: Path, agent_dir: Path) -> None:
    """A bundle missing a path a layer expects warns instead of skipping silently.

    Only reachable from a damaged install now that the source ships with the
    package, which is what the message says — the old wording sent people to
    look upstream for a problem on their own disk.
    """
    import shutil

    # Every layer's skills come from agents/skills, which this bundle lacks.
    shutil.rmtree(bundle / "agents" / "skills")
    result = runner.invoke(
        app, ["install-skills", "--agent", "bob"]
    )
    assert result.exit_code == 0
    assert "missing from this wfctl install" in result.output
    assert "agents/skills" in result.output


def test_uninstall_removes_only_the_named_layer(bundle: Path, agent_dir: Path) -> None:
    """Uninstalling an agent drops that agent's items and nothing else.

    Behavior change: `.agents/skills` used to go with `--agent claude`, because
    claude claimed it. The base layer owns it now, so it survives — as does the
    tracker selection, which `wfctl issue` reads without needing skills at all.
    """
    import json
    import os
    _add_tracker(bundle)
    repo_root = Path(os.environ["WFCTL_REPO_ROOT"])
    runner.invoke(
        app,
        ["install-skills", "--tracker", "github"],
    )
    assert (repo_root / ".agents" / "skills" / "test-skill").exists()

    result = runner.invoke(app, ["uninstall-skills", "--agent", "claude"])
    assert result.exit_code == 0
    assert not (repo_root / ".claude" / "commands" / "test-cmd.md").exists()
    # Base layer untouched.
    assert (repo_root / ".agents" / "skills" / "test-skill").exists()
    assert (repo_root / ".agents" / "commands" / "test-cmd.md").exists()
    manifest = json.loads((repo_root / ".wf-skills-manifest.json").read_text())
    assert "claude" not in manifest
    assert "base" in manifest
    assert manifest["tracker"] == "github"


def test_install_backs_up_and_uninstall_restores_pre_existing_file(agent_dir: Path) -> None:
    import os
    repo_root = Path(os.environ["WFCTL_REPO_ROOT"])

    # A command of the same name already exists before wf-skills touches it.
    existing_cmd_dir = repo_root / ".claude" / "commands"
    existing_cmd_dir.mkdir(parents=True)
    (existing_cmd_dir / "test-cmd.md").write_text("# my own pre-existing command\n")

    result = runner.invoke(
        app,
        ["install-skills",
         "--agent", "claude", "--yes"],
    )
    assert result.exit_code == 0
    assert "Backed up 1" in result.output
    # Overwritten with wf-skills' version after install.
    assert (existing_cmd_dir / "test-cmd.md").read_text() == "# test-cmd\n"

    result = runner.invoke(app, ["uninstall-skills", "--agent", "claude"])
    assert result.exit_code == 0
    assert "restored 1" in result.output
    # Original content is back, not just deleted.
    assert (existing_cmd_dir / "test-cmd.md").read_text() == "# my own pre-existing command\n"
    assert not (repo_root / ".wf-skills-backup").exists()


def test_uninstall_with_nothing_installed_is_a_noop(agent_dir: Path) -> None:
    result = runner.invoke(app, ["uninstall-skills", "--agent", "claude"])
    assert result.exit_code == 0
    assert "Nothing installed" in result.output


def test_reinstall_does_not_re_backup_already_tracked_item(agent_dir: Path) -> None:
    import os
    repo_root = Path(os.environ["WFCTL_REPO_ROOT"])

    existing_cmd_dir = repo_root / ".claude" / "commands"
    existing_cmd_dir.mkdir(parents=True)
    (existing_cmd_dir / "test-cmd.md").write_text("# my own pre-existing command\n")

    runner.invoke(app, ["install-skills", "--yes"])
    # Second install of the same item should not report a fresh backup.
    result = runner.invoke(
        app, ["install-skills", "--yes"]
    )
    assert "Backed up" not in result.output

    # The original pre-existing content must still be recoverable.
    runner.invoke(app, ["uninstall-skills", "--agent", "claude"])
    assert (existing_cmd_dir / "test-cmd.md").read_text() == "# my own pre-existing command\n"


def test_install_prompts_before_overwriting_and_declining_aborts(    agent_dir: Path
) -> None:
    import os
    repo_root = Path(os.environ["WFCTL_REPO_ROOT"])
    existing_cmd_dir = repo_root / ".claude" / "commands"
    existing_cmd_dir.mkdir(parents=True)
    (existing_cmd_dir / "test-cmd.md").write_text("# my own pre-existing command\n")

    result = runner.invoke(
        app, ["install-skills", "--agent", "claude"], input="n\n"
    )
    assert result.exit_code != 0
    assert "test-cmd.md" in result.output
    # Declined — nothing touched, no manifest written.
    assert (existing_cmd_dir / "test-cmd.md").read_text() == "# my own pre-existing command\n"
    assert not (repo_root / ".wf-skills-manifest.json").exists()


def test_install_prompts_before_overwriting_and_confirming_proceeds(    agent_dir: Path
) -> None:
    import os
    repo_root = Path(os.environ["WFCTL_REPO_ROOT"])
    existing_cmd_dir = repo_root / ".claude" / "commands"
    existing_cmd_dir.mkdir(parents=True)
    (existing_cmd_dir / "test-cmd.md").write_text("# my own pre-existing command\n")

    result = runner.invoke(
        app, ["install-skills", "--agent", "claude"], input="y\n"
    )
    assert result.exit_code == 0
    assert (existing_cmd_dir / "test-cmd.md").read_text() == "# test-cmd\n"


def test_install_no_prompt_when_nothing_would_be_overwritten(    agent_dir: Path
) -> None:
    # No --yes, no input supplied — would hang/fail on an unexpected prompt.
    result = runner.invoke(app, ["install-skills"])
    assert result.exit_code == 0


def test_install_records_the_wfctl_version_and_bundle_hash(
    bundle: Path, agent_dir: Path
) -> None:
    """The manifest pins what a bundled install can be identified by.

    Both halves are needed and neither substitutes for the other: the version
    says which wfctl produced the tree, the hash says what that tree actually
    contained — which is what an editable install changes without the version
    moving. Asserts the removed keys are gone too, since a stale `commit`
    left behind would send `doctor` back to comparing against a repo that no
    longer exists.
    """
    import json
    import os

    from wfctl import _bundle

    repo_root = Path(os.environ["WFCTL_REPO_ROOT"])
    runner.invoke(app, ["install-skills", "--agent", "claude"])
    entry = json.loads((repo_root / ".wf-skills-manifest.json").read_text())["claude"]
    assert entry["wfctl_version"] == version("wfctl")
    assert entry["content_hash"] == _bundle.content_hash(bundle)
    assert not {"repo", "ref", "commit"} & entry.keys()


def test_doctor_with_nothing_installed(agent_dir: Path) -> None:
    """No manifest yet — doctor reports that plainly instead of erroring."""
    result = runner.invoke(app, ["doctor"])
    assert result.exit_code == 0
    assert "Nothing installed" in result.output


# --- doctor's four staleness states (data-model.md §3) ---
#
# All four turn on one comparison: the `content_hash` on record against the
# bundle's hash right now. Nothing is fetched, so each state is reached by
# either editing the bundle (a real hash change) or the record.

def test_doctor_reports_up_to_date(agent_dir: Path) -> None:
    """Nothing has moved since the install — the hash still matches."""
    runner.invoke(app, ["install-skills", "--agent", "claude"])
    result = runner.invoke(app, ["doctor"])
    assert result.exit_code == 0
    assert f"claude: skills current (wfctl {version('wfctl')})" in result.output


def test_doctor_reports_stale_across_versions(bundle: Path, agent_dir: Path) -> None:
    """A newer wfctl shipped different skills — name both versions, exit 1.

    The bundle is edited for real rather than the hash faked, so this asserts the
    comparison and not a string put there by the test.
    """
    repo_root = agent_dir.parent
    runner.invoke(app, ["install-skills", "--agent", "claude"])

    (bundle / "agents" / "skills" / "test-skill" / "SKILL.md").write_text("# v2\n")
    with _edit_manifest(repo_root) as manifest:
        manifest["claude"]["wfctl_version"] = "0.0.1"

    result = runner.invoke(app, ["doctor"])
    assert result.exit_code == 1
    assert f"installed by wfctl 0.0.1, running {version('wfctl')}" in result.output
    assert "wfctl install-skills" in result.output  # the remedy


def test_doctor_reports_stale_at_the_same_version(bundle: Path, agent_dir: Path) -> None:
    """Skills edited under one wfctl version — the editable-install case.

    Once skills live in this repo they are authored against an editable install,
    so equal versions with a changed tree is the state a contributor sees most.
    Reporting it as `installed by 0.15.0, running 0.15.0` would read as a bug.
    """
    runner.invoke(app, ["install-skills", "--agent", "claude"])
    (bundle / "agents" / "skills" / "test-skill" / "SKILL.md").write_text("# v2\n")

    result = runner.invoke(app, ["doctor"])
    assert result.exit_code == 1
    assert "claude: bundled skills changed since install" in result.output
    assert "wfctl install-skills" in result.output
    assert "running" not in result.output, "no version comparison to imply"


def test_doctor_warns_on_a_record_without_a_fingerprint(agent_dir: Path) -> None:
    """A record written before content hashing is unmeasurable, not stale.

    Warn and leave the exit code alone: the layer may well be current, and
    exiting 1 on a manifest the user cannot have known to avoid would fail every
    pre-upgrade repo's CI over nothing.
    """
    repo_root = agent_dir.parent
    runner.invoke(app, ["install-skills", "--agent", "claude"])
    with _edit_manifest(repo_root) as manifest:
        del manifest["claude"]["content_hash"]

    result = runner.invoke(app, ["doctor"])
    assert result.exit_code == 0
    assert "claude: installed before content hashing" in result.output


# --- doctor: entries wfctl installed and no longer records (#38) -------------
#
# An upstream rename writes the new path and leaves the old file, then the
# manifest is replaced per layer and the old path falls out of the record.
# `uninstall-skills` reads only the current manifest, so nothing can reach the
# file afterwards. Simulated by dropping a path from the record.
#
# That simulation stopped being a faithful rename when #38's flag landed in
# v0.16.0: an install that stops shipping a path now keeps it on record marked
# `orphaned`, so a rename never empties the record again. What `_forget_one_item`
# reproduces today is the *pre-flag* orphan — installed by v0.15.0 or earlier and
# never recorded since — which is the only case the disk scan still owns.
#
# It is also indistinguishable from a skill someone hand-placed (#183): both are
# untracked paths in a wfctl destination that the record does not hold. So the
# scan names what it finds and exits 0, and only the flag returns a finding.
# Tests below assert that split; the pair at the end of this section is what
# keeps it from collapsing into "report nothing".


def _forget_one_item(repo_root: Path, suffix: str) -> str:
    """Drop the recorded entry ending in `suffix`, leaving the file on disk."""
    with _edit_manifest(repo_root) as manifest:
        for key, entry in manifest.items():
            if not isinstance(entry, dict) or "items" not in entry:
                continue
            for i, item in enumerate(entry["items"]):
                if item["path"].endswith(suffix):
                    del entry["items"][i]
                    return str(item["path"])
    raise AssertionError(f"no recorded item ends in {suffix!r}")


def test_doctor_names_an_installed_path_that_fell_out_of_the_record(
    agent_dir: Path,
) -> None:
    """Named, because nothing else ever will — the record does not hold it, so
    neither `--prune` nor `uninstall-skills` can reach it (#38).

    Exit 0, because the scan cannot tell this from a hand-placed skill (#183) and
    a wrong exit code here fails a consumer's build over their own file. The
    certainty lives in the flag, and the flag half still exits 1.
    """
    repo_root = agent_dir.parent
    runner.invoke(app, ["install-skills", "--agent", "claude"])
    forgotten = _forget_one_item(repo_root, "test-cmd.md")

    result = runner.invoke(app, ["doctor"])

    assert forgotten in result.output
    assert "no longer shipped" not in result.output, (
        "the scan has not earned that claim — it did not see the install"
    )
    assert result.exit_code == 0


def test_doctor_never_removes_what_it_reports(agent_dir: Path) -> None:
    """Report-only, and the one property here whose violation destroys work.

    A consumer may have edited the file, and a path also falls out of the record
    when a layer is deselected rather than dropped upstream — this check cannot
    tell either case from a genuine rename, so it must not act on any of them.
    """
    repo_root = agent_dir.parent
    runner.invoke(app, ["install-skills", "--agent", "claude"])
    forgotten = _forget_one_item(repo_root, "test-cmd.md")
    (repo_root / forgotten).write_text("edited by hand\n")

    runner.invoke(app, ["doctor"])

    assert (repo_root / forgotten).read_text() == "edited by hand\n"


def test_an_abandoned_directory_is_one_finding_however_many_files_it_holds(
    bundle: Path, agent_dir: Path
) -> None:
    """SC-007. A skill is installed and recorded as one directory, so a renamed
    one is one finding — not one per file inside it, which is what a recursive
    walk would produce and what makes a single upstream rename unreadable."""
    repo_root = agent_dir.parent
    (bundle / "agents" / "skills" / "test-skill" / "extra.md").write_text("x\n")
    runner.invoke(app, ["install-skills", "--agent", "claude"])
    forgotten = _forget_one_item(repo_root, "skills/test-skill")
    held = [p for p in (repo_root / forgotten).rglob("*") if p.is_file()]

    out = runner.invoke(app, ["doctor"]).output

    assert len(held) > 1, "fixture must hold several files for this to mean anything"
    assert out.count(forgotten) == 1
    assert "1 path is not on record" in out


def test_doctor_does_not_report_a_command_the_user_wrote_themselves(
    agent_dir: Path,
) -> None:
    """`.claude/` is the user's own agent directory. wfctl copies into it, but a
    slash command someone authored there is not wfctl's abandoned output — and
    under this contract, reporting it would fail their build over their file."""
    repo_root = agent_dir.parent
    runner.invoke(app, ["install-skills", "--agent", "claude"])
    mine = repo_root / ".claude" / "commands" / "my-own-thing.md"
    mine.parent.mkdir(parents=True, exist_ok=True)
    mine.write_text("mine\n")

    result = runner.invoke(app, ["doctor"])

    assert "my-own-thing" not in result.output
    assert result.exit_code == 0


def test_doctor_does_not_report_a_skill_the_repo_commits_beside_the_installed_ones(
    agent_dir: Path,
) -> None:
    """`.agents/skills/` is shared ground: a project may commit its own skills
    there, ignoring the tree and naming its own as exceptions.

    Found against pfms, which does exactly that and was told to delete eleven
    committed files — the four `pfms-*` skills, `verifier-storybook`, and the
    `speckit.git.*` commands — on doctor's say-so. Absent from the record and
    tracked means the repo owns it, not that wfctl orphaned it.

    Asserts the orphan beside it still reports, because the cheap wrong fix is a
    fallback that treats everything as tracked and silences the check outright.
    """
    repo_root = agent_dir.parent
    runner.invoke(app, ["install-skills", "--agent", "claude"])
    forgotten = _forget_one_item(repo_root, "test-cmd.md")

    mine = repo_root / ".agents" / "skills" / "proj-own-skill"
    mine.mkdir(parents=True, exist_ok=True)
    (mine / "SKILL.md").write_text("# proj-own-skill\n")
    subprocess.run(
        ["git", "-C", str(repo_root), "add", "-f", ".agents/skills/proj-own-skill"],
        check=True, capture_output=True,
    )
    subprocess.run(
        ["git", "-C", str(repo_root), "commit", "-m", "add project skill"],
        check=True, capture_output=True,
    )

    result = runner.invoke(app, ["doctor"])

    assert "proj-own-skill" not in result.output
    assert forgotten in result.output, "an untracked orphan must still be named"
    assert result.exit_code == 0


def test_doctor_does_not_report_a_hand_authored_tracker_config(
    bundle: Path, agent_dir: Path
) -> None:
    """`.agents/trackers/` is shared ground wearing an owned tree's prefix.

    The real deployment, not a simplified one: `github.json` recorded by
    `install-skills --tracker github`, and a Jira config hand-authored beside it
    the way `/scaffold-tracker` documents. That pairing is what makes the
    directory a candidate at all — with nothing recorded there, a scan derived
    from the record would skip it for the wrong reason and the test would pass
    without proving anything.

    Scanning it would call the repo's own Jira config abandoned and, under this
    contract, fail its build over a file wfctl never wrote.
    """
    repo_root = agent_dir.parent
    trackers_src = bundle / "agents" / "trackers"
    trackers_src.mkdir(parents=True, exist_ok=True)
    (trackers_src / "github.json").write_text(json.dumps({"verbs": {}}))
    runner.invoke(app, ["install-skills", "--agent", "claude", "--tracker", "github"])

    recorded = {i["path"] for i in _recorded_items(_manifest(repo_root))}
    assert ".agents/trackers/github.json" in recorded, "fixture must record a tracker"

    mine = repo_root / ".agents" / "trackers" / "jira.json"
    mine.write_text('{"verbs": {"list": "jira issue list"}}\n')

    result = runner.invoke(app, ["doctor"])

    assert "jira" not in result.output
    assert result.exit_code == 0
    assert mine.exists(), "report-only, and this one is not wfctl's file at all"


def test_an_orphan_is_reported_even_as_its_directorys_last_recorded_entry(
    agent_dir: Path,
) -> None:
    """The scan reads fixed destinations, not the parents of recorded paths.

    Derived from the record, a directory whose last recorded entry falls out drops
    out of the scan with it — so the orphan goes unreported in exactly the case
    the check exists for. Here `.agents/commands/` holds one recorded file and it
    is the one that falls out.
    """
    repo_root = agent_dir.parent
    runner.invoke(app, ["install-skills", "--agent", "claude"])
    forgotten = _forget_one_item(repo_root, ".agents/commands/test-cmd.md")
    remaining = [
        i["path"]
        for i in _recorded_items(_manifest(repo_root))
        if i["path"].startswith(".agents/commands/")
    ]

    result = runner.invoke(app, ["doctor"])

    assert remaining == [], "fixture must leave the directory with nothing recorded"
    assert forgotten in result.output
    assert result.exit_code == 0


def test_doctor_reports_a_mirror_left_behind_when_a_skill_stops_being_mirrored(
    bundle: Path, agent_dir: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """#110. `.claude/skills/` is a selective mirror, so its orphans have no twin.

    Every other agent destination copies a base source whole, and a rename there
    orphans the `.agents/` copy alongside it — which the scan already reports.
    Dropping a name from `_MIRRORED_SKILLS` orphans nothing under `.agents/`: the
    skill stays installed and recorded there, and only the `.claude/` copy falls
    off the record. Before this, nothing named it, ever.

    Un-mirrors for real rather than editing the record, because the install that
    stops mirroring is the link in the chain the fix depends on. That install now
    keeps the path on record flagged as dropped (#38), so this travels doctor's
    flag route; `_forget_one_item` covers the disk-scan route, which still owns
    orphans left by an install that predates the flag.

    Reads the name out of `_MIRRORED_SKILLS` rather than hardcoding one: a literal
    would keep passing as a no-op the day that skill stops being mirrored.
    """
    repo_root = agent_dir.parent
    name = sorted(_MIRRORED_SKILLS)[0]
    skill = bundle / "agents" / "skills" / name
    skill.mkdir(parents=True)
    (skill / "SKILL.md").write_text(f"# {name}\n")
    runner.invoke(app, ["install-skills", "--agent", "claude", "--yes"])
    mirror = repo_root / ".claude" / "skills" / name
    assert mirror.is_dir(), "fixture must install the mirror before un-mirroring it"

    monkeypatch.setattr("wfctl.cli._MIRRORED_SKILLS", _MIRRORED_SKILLS - {name})
    runner.invoke(app, ["install-skills", "--agent", "claude", "--yes"])

    result = runner.invoke(app, ["doctor"])

    dropped = [
        i for i in _recorded_items(_manifest(repo_root))
        if i["path"] == f".claude/skills/{name}"
    ]
    assert dropped and dropped[0].get("orphaned"), (
        "the install must keep the path on record and flag it, or nothing names "
        "it after its own run"
    )
    assert mirror.exists(), "the copy stays on disk — that is the whole problem"
    assert f".claude/skills/{name}" in result.output
    assert result.exit_code == 1

    runner.invoke(app, ["install-skills", "--agent", "claude", "--yes", "--prune"])

    assert not mirror.exists()
    assert runner.invoke(app, ["doctor"]).exit_code == 0


def test_doctor_does_not_report_a_claude_skill_the_user_wrote_themselves(
    agent_dir: Path,
) -> None:
    """The layer gate is not enough — `.claude/skills/` is shared ground in a repo
    that *did* install for claude, and that is the common repo.

    Claude Code and its plugins keep project-local skills there, and `.claude/` is
    commonly gitignored whole (this repo's own `.gitignore` does it), so
    `_tracked_paths` cannot exempt a hand-authored skill the way it can under
    `.agents/`. Reporting one claims wfctl installed it, tells the reader to
    delete it, and exits 1 in their CI — over their file.

    What separates the two is the base-layer copy: a mirror is a copy of a skill
    under `.agents/skills/`, and a skill someone wrote has no counterpart there.
    """
    repo_root = agent_dir.parent
    runner.invoke(app, ["install-skills", "--agent", "claude", "--yes"])
    mine = repo_root / ".claude" / "skills" / "my-own-skill"
    mine.mkdir(parents=True)
    (mine / "SKILL.md").write_text("mine\n")
    assert not (repo_root / ".agents" / "skills" / "my-own-skill").exists(), (
        "a hand-authored claude skill has no base-layer copy — that is the tell"
    )

    result = runner.invoke(app, ["doctor"])

    assert "my-own-skill" not in result.output
    assert result.exit_code == 0


def test_doctor_does_not_report_a_claude_skill_in_a_bob_installed_repo(
    agent_dir: Path,
) -> None:
    """The mirror root is scanned only because the claude layer wrote to it.

    Under `--agent bob`, `.claude/` is entirely the user's — wfctl never put a
    file there — so a skill someone keeps in it is theirs, and reporting it would
    fail their build over their own work. The gate is the manifest's claude entry,
    not the directory's existence.

    Asserts an orphan in an owned tree still reports, because a gate that
    silenced the scan outright would pass the first assertion for the wrong
    reason.
    """
    repo_root = agent_dir.parent
    runner.invoke(app, ["install-skills", "--agent", "bob", "--yes"])
    mine = repo_root / ".claude" / "skills" / "my-own-skill"
    mine.mkdir(parents=True)
    (mine / "SKILL.md").write_text("mine\n")
    forgotten = _forget_one_item(repo_root, ".agents/commands/test-cmd.md")

    result = runner.invoke(app, ["doctor"])

    assert "my-own-skill" not in result.output
    assert forgotten in result.output, "an orphan in an owned tree must still be named"


def test_doctor_does_not_report_a_hand_placed_skill_as_abandoned(
    agent_dir: Path,
) -> None:
    """#183. `.agents/skills/` is shared ground too, and the signal #87 used
    cannot reach here.

    #87 drew the line at git tracking, which works because a repo committing its
    own skills names them as exceptions to the gitignore. An *uncommitted*
    hand-placed skill has no such signal: being untracked is exactly what it
    shares with an orphan, so `_tracked_paths` passes it straight through.

    Before this, `doctor` told the reader wfctl had installed the skill, that it
    was dropped upstream, and to delete it — three claims about a file wfctl never
    wrote — and exited 1 every run, so the repo could never be green while the
    skill existed.

    The path is still named. Silence would be the other wrong answer, and the
    test below is what stops this one from being reached by turning the check
    off.
    """
    repo_root = agent_dir.parent
    runner.invoke(app, ["install-skills", "--agent", "claude", "--yes"])
    mine = repo_root / ".agents" / "skills" / "my-own-skill"
    mine.mkdir(parents=True)
    (mine / "SKILL.md").write_text("# my-own-skill\n")

    result = runner.invoke(app, ["doctor"])

    assert "my-own-skill" in result.output, "named, but not as a finding"
    assert "no longer shipped" not in result.output
    assert "by hand" not in result.output, "naming a path is not advice to delete it"
    assert "--prune" not in result.output
    assert result.exit_code == 0


def test_doctor_still_fails_on_a_path_the_install_really_did_stop_shipping(
    bundle: Path, agent_dir: Path
) -> None:
    """The half of #183 that gets skipped: the fix must narrow the verdict, not
    silence the check.

    Renames a file the bundle ships between two real installs, so the flag is
    written by the code path that writes it in production rather than asserted
    into a fixture. That is the one case wfctl has evidence for — it watched the
    path stop being shipped — and it is the case that keeps exiting 1 with
    `--prune` as its remedy.
    """
    import os
    repo_root = Path(os.environ["WFCTL_REPO_ROOT"])
    runner.invoke(app, ["install-skills", "--agent", "claude", "--yes"])
    _rename_shipped_command(bundle, "test-cmd.md", "speckit.test-cmd.md")
    runner.invoke(app, ["install-skills", "--agent", "claude", "--yes"])

    result = runner.invoke(app, ["doctor"])

    assert ".claude/commands/test-cmd.md" in result.output
    assert "no longer shipped" in result.output
    assert "wfctl install-skills --prune" in result.output
    assert result.exit_code == 1
    assert (repo_root / ".claude" / "commands" / "test-cmd.md").exists(), (
        "report-only: doctor never removes what it names"
    )


def test_doctor_keeps_the_two_halves_apart_when_one_run_holds_both(
    bundle: Path, agent_dir: Path
) -> None:
    """The case the old code spent bespoke wording on, and the one a later
    refactor would quietly re-merge.

    A `--prune` line attached to the informational block would send the reader to
    a command that removes what the manifest lists — precisely what those paths
    are not — and it is invisible in a run holding only one of the halves.
    """
    import os
    repo_root = Path(os.environ["WFCTL_REPO_ROOT"])
    runner.invoke(app, ["install-skills", "--agent", "claude", "--yes"])
    _rename_shipped_command(bundle, "test-cmd.md", "speckit.test-cmd.md")
    runner.invoke(app, ["install-skills", "--agent", "claude", "--yes"])
    mine = repo_root / ".agents" / "skills" / "my-own-skill"
    mine.mkdir(parents=True)
    (mine / "SKILL.md").write_text("# my-own-skill\n")

    out = runner.invoke(app, ["doctor"]).output
    info, _, warning = out.partition("no longer shipped")

    assert "my-own-skill" in info and "my-own-skill" not in warning
    assert "test-cmd.md" in warning and "test-cmd.md" not in info
    assert "--prune" not in info, "the remedy must not attach to the named half"


def test_doctor_names_a_bracketed_path_verbatim(agent_dir: Path) -> None:
    """A path in this block is one wfctl did not write, so its name is entirely
    the user's — and it is printed through rich markup.

    Unescaped, `[draft]-skill` renders as `-skill`: a different path, in the one
    block whose whole job is naming the path, about a file the reader then goes
    looking for.

    Not the MarkupError a closing tag would raise. `[/x]` needs a slash, so no
    single path component can carry one, and the scan is one level deep — the
    crash is unreachable here even though the same string raises off a filesystem.
    """
    repo_root = agent_dir.parent
    runner.invoke(app, ["install-skills", "--agent", "claude", "--yes"])
    (repo_root / ".agents" / "skills" / "[draft]-skill").mkdir(parents=True)

    result = runner.invoke(app, ["doctor"])

    assert "[draft]-skill" in result.output
    assert result.exit_code == 0


def test_the_prune_doctor_advises_names_the_layer_it_has_to_reach(
    bundle: Path, agent_dir: Path
) -> None:
    """`install-skills` diffs only the layers the run installs, so a bare
    `--prune` never touches `.claude/` — pinned one file over by
    `test_deselecting_an_agent_layer_does_not_orphan_the_paths_it_installed`.

    Advising the bare form for an agent-layer path is advice that runs, reports
    success, changes nothing, and leaves doctor exiting 1 on the next run.
    """
    runner.invoke(app, ["install-skills", "--agent", "claude", "--yes"])
    _rename_shipped_command(bundle, "test-cmd.md", "speckit.test-cmd.md")
    runner.invoke(app, ["install-skills", "--agent", "claude", "--yes"])

    out = runner.invoke(app, ["doctor"]).output

    assert "wfctl install-skills --agent claude --prune" in out


def test_the_prune_doctor_advises_keeps_the_source_the_layer_was_installed_from(
    tmp_path_factory: pytest.TempPathFactory, agent_dir: Path
) -> None:
    """`--from` is one-shot, so a repair that omits it does not fail — it
    succeeds, reinstalls the running release over the branch under test, and
    reports the layer green.

    That is the repair destroying the thing it was called to check, and
    `/start-session` runs this line unattended. The stale-skills repair carries
    `--from` for exactly this reason; this one is the same command.

    Quoted, because a source under a directory holding a space printed as two
    arguments and the second was rejected.
    """
    source = _named_source(tmp_path_factory.mktemp("named source"))
    runner.invoke(app, ["install-skills", "--from", str(source), "--yes"])
    (source / "agents" / "commands" / "test-cmd.md").rename(
        source / "agents" / "commands" / "speckit.test-cmd.md"
    )
    runner.invoke(app, ["install-skills", "--from", str(source), "--yes"])

    out = runner.invoke(app, ["doctor"]).output

    assert "no longer shipped" in out, "fixture must produce a flagged path"
    assert f"--from '{source}' --prune" in out


def test_doctor_is_silent_when_every_installed_path_is_still_recorded(
    agent_dir: Path,
) -> None:
    runner.invoke(app, ["install-skills", "--agent", "claude"])

    result = runner.invoke(app, ["doctor"])

    assert "no longer shipped" not in result.output
    assert "not on record" not in result.output, (
        "the informational block must stay silent too — an assertion on the "
        "warning alone would pass with it printing on every clean repo"
    )
    assert result.exit_code == 0


def test_doctor_does_not_scan_for_abandoned_entries_with_nothing_installed(
    agent_dir: Path,
) -> None:
    """With no layers recorded, every file in the owned trees is unrecorded. The
    scan sits behind the manifest gate so it never reports all of them."""
    repo_root = agent_dir.parent
    (repo_root / ".agents" / "commands").mkdir(parents=True)
    (repo_root / ".agents" / "commands" / "stray.md").write_text("x\n")

    result = runner.invoke(app, ["doctor"])

    assert "no longer shipped" not in result.output
    assert "Nothing installed" in result.output


# --- a bundle that is not there ---
#
# `_bundle.content_hash` raises rather than fingerprinting an empty tree, so
# both callers have to turn that into a CLI error. Reached by emptying the fake
# bundle, which is what a wheel that lost its vendored trees looks like.

def test_doctor_errors_on_a_missing_bundle(bundle: Path, agent_dir: Path) -> None:
    """A broken install exits 1 with the reason, not a traceback."""
    runner.invoke(app, ["install-skills", "--agent", "claude"])
    shutil.rmtree(bundle / "agents")

    result = runner.invoke(app, ["doctor"])
    assert result.exit_code == 1
    assert "no bundled trees" in result.output
    assert "reinstall the package" in result.output


def test_install_skills_errors_on_a_missing_bundle(bundle: Path, agent_dir: Path) -> None:
    """Same for install-skills, and it leaves the repo untouched.

    The hash is taken before the copy for this reason: failing afterwards would
    leave files on disk with no manifest naming them, which uninstall cannot undo.
    """
    repo_root = agent_dir.parent
    shutil.rmtree(bundle / "agents")

    result = runner.invoke(app, ["install-skills", "--agent", "claude"])
    assert result.exit_code == 1
    assert "no bundled trees" in result.output
    assert not (repo_root / ".wf-skills-manifest.json").exists()
    assert not (repo_root / ".agents").exists()


def test_reinstall_migrates_a_pre_change_record(agent_dir: Path) -> None:
    """One install is the whole migration, and it takes the dead keys with it.

    `repo`/`ref`/`commit` describe a fetch that no longer happens, so they are
    dropped rather than carried: a record asserting a commit the tool cannot act
    on is worse than one that says nothing about where the files came from.
    """
    repo_root = agent_dir.parent
    runner.invoke(app, ["install-skills", "--agent", "claude"])
    with _edit_manifest(repo_root) as manifest:
        entry = manifest["claude"]
        del entry["content_hash"]
        del entry["wfctl_version"]
        entry["repo"] = "https://github.com/aamarin/wf-skills"
        entry["ref"] = "main"
        entry["commit"] = "9ee468a" + "0" * 33

    assert runner.invoke(app, ["install-skills", "--agent", "claude"]).exit_code == 0
    entry = json.loads((repo_root / ".wf-skills-manifest.json").read_text())["claude"]
    assert not {"repo", "ref", "commit"} & entry.keys()
    assert entry["wfctl_version"] == version("wfctl")
    assert entry["content_hash"]


def test_uninstall_restores_backups_recorded_before_the_change(agent_dir: Path) -> None:
    """A backup pointer written by the old code still restores after migrating.

    `items` is the one part of a record that cannot be recomputed: it names the
    user's file and where their copy of it went. A rewrite that dropped the dead
    provenance keys and took `backup` with it would lose their content silently,
    on the install that was meant to be a no-op.
    """
    repo_root = agent_dir.parent
    mine = repo_root / ".agents" / "commands" / "test-cmd.md"
    mine.parent.mkdir(parents=True)
    mine.write_text("# mine, not wfctl's\n")

    runner.invoke(app, ["install-skills", "--yes"])  # backs `mine` up
    with _edit_manifest(repo_root) as manifest:
        entry = manifest["base"]
        del entry["content_hash"]
        entry["commit"] = "9ee468a" + "0" * 33
    backup = json.loads((repo_root / ".wf-skills-manifest.json").read_text())
    recorded = {i["path"]: i["backup"] for i in backup["base"]["items"]}
    assert recorded[".agents/commands/test-cmd.md"], "precondition: a backup was taken"

    runner.invoke(app, ["install-skills", "--yes"])  # the migrating re-install
    assert runner.invoke(app, ["uninstall-skills", "--agent", "base"]).exit_code == 0
    assert mine.read_text() == "# mine, not wfctl's\n"


def test_doctor_says_nothing_about_a_layer_that_installed_nothing(agent_dir: Path) -> None:
    """`none` has no targets of its own, so there is no entry to check.

    doctor iterates the manifest's layer keys, so an entry written for an empty
    layer would produce a staleness verdict about a layer holding no files —
    and, being hash-compared like any other, could report it as stale.
    """
    repo_root = agent_dir.parent
    assert runner.invoke(app, ["install-skills", "--agent", "none"]).exit_code == 0
    assert "none" not in json.loads((repo_root / ".wf-skills-manifest.json").read_text())
    assert "none:" not in runner.invoke(app, ["doctor"]).output


@pytest.mark.real_version_check
def test_doctor_skills_verdict_survives_an_offline_release_check(
    bundle: Path, agent_dir: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The skills verdict is local, so losing the network must not weaken it.

    The release check needs `ls-remote`; the skills check no longer does. When
    the first goes dark it reports ⚠ and returns 0, and a stale layer still has
    to drive the exit code — otherwise `doctor` is quietly advisory offline.
    """
    runner.invoke(app, ["install-skills", "--agent", "claude"])
    (bundle / "agents" / "skills" / "test-skill" / "SKILL.md").write_text("# v2\n")
    monkeypatch.setattr(
        subprocess, "run",
        lambda argv, **kw: subprocess.CompletedProcess(argv, 1, stdout="", stderr="no route"),
    )

    result = runner.invoke(app, ["doctor"])
    assert "couldn't check releases" in result.output
    assert "claude: bundled skills changed since install" in result.output
    assert result.exit_code == 1


def test_layer_destinations_are_disjoint() -> None:
    """No two layers may write the same path.

    This is what makes the backup cross-attribution unreachable rather than
    patched: if the base layer and an agent layer never share a destination,
    one layer's install can never mistake another's files for the user's. The
    invariant is enforced here rather than in a comment, because a future agent
    entry would otherwise reintroduce the collision silently.
    """
    from wfctl import cli

    base = getattr(cli, "_BASE_TARGETS", [])
    assert base, "_BASE_TARGETS must exist and be non-empty"

    seen: dict[str, str] = {}
    collisions: list[str] = []
    for layer, targets in [("base", base), *cli._AGENT_TARGETS.items()]:
        for _src, dst in targets:
            if dst in seen:
                collisions.append(f"{dst!r}: claimed by both {seen[dst]!r} and {layer!r}")
            seen[dst] = layer

    assert not collisions, "layers share destinations:\n  " + "\n  ".join(collisions)


def test_bare_install_writes_agents_only(agent_dir: Path) -> None:
    """No --agent means no assistant-specific files."""
    import json
    import os
    repo_root = Path(os.environ["WFCTL_REPO_ROOT"])
    result = runner.invoke(app, ["install-skills"])
    assert result.exit_code == 0

    assert (repo_root / ".agents" / "skills" / "test-skill").exists()
    assert (repo_root / ".agents" / "commands" / "test-cmd.md").exists()
    assert not (repo_root / ".claude").exists()
    assert not (repo_root / ".bob").exists()
    assert not (repo_root / ".github").exists()

    manifest = json.loads((repo_root / ".wf-skills-manifest.json").read_text())
    assert list(manifest) == ["base"]
    for item in manifest["base"]["items"]:
        assert item["path"].startswith((".agents/", ".specify/")), item["path"]


def _summary_layers(output: str) -> dict[str, str]:
    """Parse the per-layer summary block into {layer: counts}.

    Scoped to the block after the ✓ line so assertions cannot be satisfied by
    the opt-in hint below it, which legitimately names the same agents.
    """
    lines = output.splitlines()
    start = next(i for i, line in enumerate(lines) if line.startswith("✓ Installed"))
    # Rich wraps the repo URL onto its own continuation line, so the summary
    # does not necessarily start immediately after the ✓. Take the run of
    # indented lines up to the blank that separates it from the opt-in hint.
    layers = {}
    for line in lines[start + 1:]:
        if not line.strip():
            break
        if not line.startswith("  "):
            continue
        layer, _, counts = line.strip().partition("  ")
        layers[layer] = counts.strip()
    return layers


def test_install_summary_reports_per_layer_counts(agent_dir: Path) -> None:
    """Counts are per layer and per kind, never one total that
    reads as a skill count. A layer contributing nothing is omitted, not `0`."""
    bare = runner.invoke(app, ["install-skills"])
    assert bare.exit_code == 0
    layers = _summary_layers(bare.output)
    assert list(layers) == ["base"], layers
    assert "1 skill" in layers["base"] and "1 command" in layers["base"]
    assert "0 " not in bare.output  # never a zero count anywhere

    claude = runner.invoke(
        app, ["install-skills", "--agent", "claude"]
    )
    assert claude.exit_code == 0
    layers = _summary_layers(claude.output)
    assert list(layers) == ["base", "claude"], layers
    assert "1 command" in layers["claude"]


def test_bare_install_prints_agent_optin_hint(agent_dir: Path) -> None:
    """After a base-only install, name every agent that has a layer and
    the command to add it. Derived from _AGENT_TARGETS so an agent added later
    is covered without editing this test."""
    from wfctl import cli
    bare = runner.invoke(app, ["install-skills"])
    opt_in = [a for a, targets in cli._AGENT_TARGETS.items() if targets]
    assert opt_in, "expected at least one agent with a layer of its own"
    for agent in opt_in:
        assert f"--agent {agent}" in bare.output
    assert "--agent none" not in bare.output  # no layer, nothing to opt into

    claude = runner.invoke(
        app, ["install-skills", "--agent", "claude"]
    )
    assert "install-skills --agent" not in claude.output


def test_upgrade_from_pre_layer_manifest_is_silent(agent_dir: Path) -> None:
    """A repo installed before the layer split upgrades quietly.

    The old shape recorded `.agents/*` under the agent key. This version plans
    those same paths as the base layer, so without unioning items across
    entries they read as files the user wrote — and the first install after
    upgrading would prompt to overwrite content wfctl installed itself, then
    back it up. The prompt aborts when there is no tty, which is how CI and
    workmux hooks would see it.
    """
    import json
    import os
    repo_root = Path(os.environ["WFCTL_REPO_ROOT"])

    # Install, then rewrite the manifest into the pre-split shape: one agent
    # entry owning every path, no `base` key.
    runner.invoke(
        app,
        ["install-skills", "--agent", "claude"],
    )
    manifest_file = repo_root / ".wf-skills-manifest.json"
    manifest = json.loads(manifest_file.read_text())
    legacy_items = [i for entry in manifest.values() for i in entry.get("items", [])]
    manifest_file.write_text(json.dumps({"claude": {**manifest["claude"], "items": legacy_items}}))

    backups_before = sorted(p.name for p in (repo_root / ".wf-skills-backup").glob("*"))

    # The upgrade path: a bare install, which is what the new default gives you.
    result = runner.invoke(app, ["install-skills"])

    assert result.exit_code == 0, result.output
    assert "will be overwritten" not in result.output
    assert "Backed up" not in result.output
    assert sorted(p.name for p in (repo_root / ".wf-skills-backup").glob("*")) == backups_before


def test_user_authored_file_is_still_backed_up(agent_dir: Path) -> None:
    """Unioning prior items must not relax detection of real user files.

    The guard on the test above — a path wfctl never installed is still foreign,
    still backed up, and still restored on uninstall.
    """
    import os
    repo_root = Path(os.environ["WFCTL_REPO_ROOT"])

    mine = repo_root / ".agents" / "commands" / "test-cmd.md"
    mine.parent.mkdir(parents=True)
    mine.write_text("# mine, not wfctl's\n")

    result = runner.invoke(
        app, ["install-skills", "--yes"]
    )
    assert result.exit_code == 0
    assert "Backed up 1" in result.output
    assert mine.read_text() == "# test-cmd\n"

    result = runner.invoke(app, ["uninstall-skills", "--agent", "base"])
    assert result.exit_code == 0
    assert mine.read_text() == "# mine, not wfctl's\n"


def test_agent_copilot_writes_github_skills(agent_dir: Path) -> None:
    """One command, on a repo with no prior install, and the
    skills land unmodified — `.agents/skills/<name>/SKILL.md` is already the
    shape Copilot's skills layout expects, so there is nothing to transform."""
    import json
    import os
    repo_root = Path(os.environ["WFCTL_REPO_ROOT"])
    result = runner.invoke(
        app,
        ["install-skills", "--agent", "copilot"],
    )
    assert result.exit_code == 0

    installed = repo_root / ".github" / "skills" / "test-skill" / "SKILL.md"
    assert installed.exists()
    assert installed.read_text() == (repo_root / ".agents" / "skills" / "test-skill" / "SKILL.md").read_text()
    # Its own root only — no other agent's paths.
    assert not (repo_root / ".claude").exists()
    assert not (repo_root / ".bob").exists()

    manifest = json.loads((repo_root / ".wf-skills-manifest.json").read_text())
    assert sorted(manifest) == ["base", "copilot"]
    assert all(i["path"].startswith(".github/") for i in manifest["copilot"]["items"])


def test_agent_codex_informs_and_installs_base(agent_dir: Path) -> None:
    """Codex reads no repo-local command path, so there is nothing to
    install for it — but that is a fact to state, not an error. The base layer
    still lands and the command succeeds."""
    import json
    import os
    repo_root = Path(os.environ["WFCTL_REPO_ROOT"])
    result = runner.invoke(
        app,
        ["install-skills", "--agent", "codex"],
    )
    assert result.exit_code == 0
    assert "AGENTS.md" in result.output

    assert (repo_root / ".agents" / "skills" / "test-skill").exists()
    assert not (repo_root / ".codex").exists()
    manifest = json.loads((repo_root / ".wf-skills-manifest.json").read_text())
    # No entry of its own, so uninstalling it has nothing to fail on.
    assert list(manifest) == ["base"]


def test_unknown_agent_exits_listing_accepted_names(agent_dir: Path) -> None:
    """An unrecognised agent fails loudly and says what is accepted;
    `none` remains a valid way to ask for the base layer explicitly."""
    from wfctl import cli
    bad = runner.invoke(
        app,
        ["install-skills", "--agent", "nope"],
    )
    assert bad.exit_code == 1
    for name in cli._AGENT_TARGETS:
        assert name in bad.output, f"{name} missing from the accepted list"

    ok = runner.invoke(
        app, ["install-skills", "--agent", "none"]
    )
    assert ok.exit_code == 0


def test_backup_hint_names_a_command_that_restores(agent_dir: Path) -> None:
    """The restore hint must name the layer that took the backup, not --agent.

    A bare install backs up under `base`, so a hint built from the requested
    agent said `--agent none` — which matches no manifest entry and silently
    does nothing, leaving the user's file overwritten with no working way back.
    """
    import os
    repo_root = Path(os.environ["WFCTL_REPO_ROOT"])

    mine = repo_root / ".agents" / "commands" / "test-cmd.md"
    mine.parent.mkdir(parents=True)
    mine.write_text("# mine, not wfctl's\n")

    result = runner.invoke(
        app, ["install-skills", "--yes"]
    )
    assert "uninstall-skills --agent base" in result.output
    assert "--agent none" not in result.output

    # Follow the printed instruction literally — it has to actually restore.
    assert runner.invoke(app, ["uninstall-skills", "--agent", "base"]).exit_code == 0
    assert mine.read_text() == "# mine, not wfctl's\n"


def test_overwrite_prompt_names_the_owning_layer(agent_dir: Path) -> None:
    """Same hint, on the pre-overwrite confirmation — the earlier of the two."""
    import os
    repo_root = Path(os.environ["WFCTL_REPO_ROOT"])
    mine = repo_root / ".agents" / "commands" / "test-cmd.md"
    mine.parent.mkdir(parents=True)
    mine.write_text("# mine\n")

    result = runner.invoke(
        app, ["install-skills"], input="n\n"
    )
    assert "uninstall-skills --agent base" in result.output


def test_legacy_none_entry_is_dropped_once_base_owns_its_paths(    agent_dir: Path
) -> None:
    """A pre-split `none` entry must not double-book paths `base` now owns.

    Left in place, `uninstall-skills --agent none` deletes files `base` still
    claims — and `doctor` reports a phantom layer. It is dropped only after
    base has recorded every path it held, so nothing is orphaned.
    """
    import json
    import os
    repo_root = Path(os.environ["WFCTL_REPO_ROOT"])
    manifest_file = repo_root / ".wf-skills-manifest.json"

    runner.invoke(app, ["install-skills"])
    base = json.loads(manifest_file.read_text())["base"]
    manifest_file.write_text(json.dumps({"none": base}))  # the pre-split shape

    result = runner.invoke(app, ["install-skills"])
    assert result.exit_code == 0
    manifest = json.loads(manifest_file.read_text())
    assert "none" not in manifest
    assert {i["path"] for i in manifest["base"]["items"]} >= {i["path"] for i in base["items"]}


def test_legacy_entry_holding_an_unowned_path_survives(agent_dir: Path) -> None:
    """The guard on the test above: dropping an entry must never orphan a path.

    An entry base does not fully cover still owns something — including the
    backup pointer for a user file — so it stays and remains uninstallable.
    """
    import json
    import os
    repo_root = Path(os.environ["WFCTL_REPO_ROOT"])
    manifest_file = repo_root / ".wf-skills-manifest.json"

    runner.invoke(app, ["install-skills"])
    base = json.loads(manifest_file.read_text())["base"]
    stale = {**base, "items": [*base["items"], {"path": ".elsewhere/thing", "backup": None}]}
    manifest_file.write_text(json.dumps({"none": stale}))

    runner.invoke(app, ["install-skills"])
    assert "none" in json.loads(manifest_file.read_text())


def test_declining_the_tracker_is_not_asked_again(bundle: Path, 
    agent_dir: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The tracker question is asked once, not once per install.

    Declining used to write nothing, so the question came back on every
    upgrade and there was no way to answer it permanently: `--tracker none`
    clears the key rather than recording an opt-out.
    """
    import os
    from wfctl import cli
    monkeypatch.setattr(cli, "_interactive", lambda: True)
    _add_tracker(bundle)
    repo_root = Path(os.environ["WFCTL_REPO_ROOT"])

    first = runner.invoke(
        app, ["install-skills"], input="n\n1\n"
    )
    assert "No issue tracker configured" in first.output

    # No input at all: a re-prompt would abort on EOF rather than pass.
    again = runner.invoke(app, ["install-skills"])
    assert again.exit_code == 0
    assert "No issue tracker configured" not in again.output
    assert not (repo_root / ".agents" / "trackers" / "github.json").exists()


def test_uninstall_defaults_to_the_layer_a_bare_install_writes(    agent_dir: Path
) -> None:
    """`install-skills` then `uninstall-skills`, both bare, must round-trip.

    The default stayed `claude` after install's moved to the base layer, so a
    bare uninstall reported nothing to remove.
    """
    import os
    repo_root = Path(os.environ["WFCTL_REPO_ROOT"])
    runner.invoke(app, ["install-skills"])
    assert (repo_root / ".agents" / "skills" / "test-skill").exists()

    result = runner.invoke(app, ["uninstall-skills"])
    assert result.exit_code == 0
    assert not (repo_root / ".agents" / "skills" / "test-skill").exists()


def test_removing_base_under_an_agent_layer_asks_first(agent_dir: Path) -> None:
    """Agent layers are views of the base, not copies — their command wrappers
    point into .agents/skills. Removing the base underneath one leaves it
    installed and broken, and `uninstall-skills` with no flags now targets the
    base, so this is the least-typed command in the tool.
    """
    import os
    repo_root = Path(os.environ["WFCTL_REPO_ROOT"])
    runner.invoke(
        app, ["install-skills", "--agent", "claude"]
    )

    declined = runner.invoke(app, ["uninstall-skills"], input="n\n")
    assert declined.exit_code != 0, "declining must abort"
    assert "claude" in declined.output
    assert (repo_root / ".agents" / "skills" / "test-skill").exists(), "aborted — nothing removed"

    confirmed = runner.invoke(app, ["uninstall-skills"], input="y\n")
    assert confirmed.exit_code == 0
    assert not (repo_root / ".agents" / "skills" / "test-skill").exists()


def test_removing_base_alone_does_not_ask(agent_dir: Path) -> None:
    """The guard is about dependents, not about the base being special: with no
    agent layer installed there is nothing to break, so no prompt."""
    import os
    repo_root = Path(os.environ["WFCTL_REPO_ROOT"])
    runner.invoke(app, ["install-skills"])

    result = runner.invoke(app, ["uninstall-skills"])  # no input to give
    assert result.exit_code == 0
    assert not (repo_root / ".agents" / "skills" / "test-skill").exists()


def test_removing_an_agent_layer_never_asks(agent_dir: Path) -> None:
    """Nothing depends on an agent layer, so removing one is always safe."""
    import os
    repo_root = Path(os.environ["WFCTL_REPO_ROOT"])
    runner.invoke(
        app, ["install-skills", "--agent", "claude"]
    )
    result = runner.invoke(app, ["uninstall-skills", "--agent", "claude"])
    assert result.exit_code == 0
    assert (repo_root / ".agents" / "skills" / "test-skill").exists(), "base survives"


def test_install_preserves_spec_root(agent_dir: Path) -> None:
    """`spec_root` is a bare string beside the layer entries, not a layer.

    Anything iterating layers does `manifest[key].get("items", [])`, so a string
    key that is not registered as a non-layer raises AttributeError on the next
    install — an upgrade breaking on config the user set is the failure this
    guards.
    """
    import json
    import os
    repo_root = Path(os.environ["WFCTL_REPO_ROOT"])
    runner.invoke(app, ["install-skills"])

    manifest_file = repo_root / ".wf-skills-manifest.json"
    manifest = json.loads(manifest_file.read_text())
    manifest["spec_root"] = "~/Development/pfms-specs"
    manifest_file.write_text(json.dumps(manifest))

    upgrade = runner.invoke(app, ["install-skills"])
    assert upgrade.exit_code == 0, upgrade.output
    assert json.loads(manifest_file.read_text())["spec_root"] == "~/Development/pfms-specs"


def test_doctor_runs_over_a_manifest_carrying_spec_root(
    agent_dir: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """`doctor` enumerates layers through the same helper as install."""
    import json
    import os
    repo_root = Path(os.environ["WFCTL_REPO_ROOT"])
    runner.invoke(app, ["install-skills"])

    manifest_file = repo_root / ".wf-skills-manifest.json"
    manifest = json.loads(manifest_file.read_text())
    manifest["spec_root"] = str(tmp_path / "elsewhere")
    manifest_file.write_text(json.dumps(manifest))

    monkeypatch.chdir(repo_root)
    result = runner.invoke(app, ["doctor"])
    assert "AttributeError" not in result.output
    assert result.exception is None or isinstance(result.exception, SystemExit), result.exception


def test_uninstall_preserves_spec_root(agent_dir: Path) -> None:
    """Uninstalling a layer is not a reason to drop repo config.

    `uninstall` deletes only its own agent key, so this should already hold —
    pinned rather than trusted, since nothing else would catch a regression that
    silently discards a user's spec root.
    """
    import json
    import os
    repo_root = Path(os.environ["WFCTL_REPO_ROOT"])
    runner.invoke(
        app, ["install-skills", "--agent", "claude"]
    )

    manifest_file = repo_root / ".wf-skills-manifest.json"
    manifest = json.loads(manifest_file.read_text())
    manifest["spec_root"] = "~/Development/pfms-specs"
    manifest_file.write_text(json.dumps(manifest))

    result = runner.invoke(app, ["uninstall-skills", "--agent", "claude"])
    assert result.exit_code == 0, result.output
    assert json.loads(manifest_file.read_text())["spec_root"] == "~/Development/pfms-specs"


def _doctor_in(repo_root: Path, monkeypatch: pytest.MonkeyPatch):
    """Run doctor in `repo_root`, without the real network version check."""
    monkeypatch.setattr("wfctl.cli._check_wfctl_version", lambda: 0)
    monkeypatch.chdir(repo_root)
    return runner.invoke(app, ["doctor"])


def test_doctor_reports_specs_left_behind_after_a_root_is_recorded(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Recording a root does not migrate anything, and the
    recorded root is the only one consulted — so in-repo specs become invisible.
    Silent invisibility is the failure class this whole issue is about, so the
    transition gets reported.

    Must fire with no layers installed: a repo can record a spec root without
    ever having installed skills, and `doctor` returns early on an empty
    manifest — so the check has to run before that gate.
    """
    import json
    import subprocess

    repo = tmp_path / "proj"
    repo.mkdir()
    subprocess.run(["git", "init", str(repo)], check=True, capture_output=True)
    (repo / ".wf-skills-manifest.json").write_text(json.dumps({"spec_root": str(tmp_path / "elsewhere")}))
    (repo / "specs" / "18-left-behind").mkdir(parents=True)
    (repo / "specs" / "7-also-left").mkdir(parents=True)

    result = _doctor_in(repo, monkeypatch)

    assert "spec_root" in result.output
    assert "2" in result.output, "says how many, so the scale is visible"
    assert str(tmp_path / "elsewhere") in result.output
    assert (repo / "specs" / "18-left-behind").exists(), "reports only — never moves or deletes"


def test_doctor_is_quiet_when_specs_dir_is_empty_or_absent(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """No leftovers, no warning — the common case must stay silent."""
    import json
    import subprocess

    repo = tmp_path / "proj"
    repo.mkdir()
    subprocess.run(["git", "init", str(repo)], check=True, capture_output=True)
    (repo / ".wf-skills-manifest.json").write_text(json.dumps({"spec_root": str(tmp_path / "elsewhere")}))

    assert "still holds" not in _doctor_in(repo, monkeypatch).output

    (repo / "specs").mkdir()  # present but empty
    assert "still holds" not in _doctor_in(repo, monkeypatch).output


def test_doctor_is_quiet_without_a_recorded_root(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """In-repo specs are correct when no root is recorded — that is the default."""
    import subprocess

    repo = tmp_path / "proj"
    repo.mkdir()
    subprocess.run(["git", "init", str(repo)], check=True, capture_output=True)
    (repo / "specs" / "18-normal").mkdir(parents=True)

    assert "still holds" not in _doctor_in(repo, monkeypatch).output


def test_doctor_fails_over_stranded_specs_and_passes_without_a_recorded_root(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Stranded specs fail the run; the same repo with no recorded root does not.

    One repo, two manifests, so the only difference between the passing and
    failing runs is the recorded root — the property under test. Asserting a
    constant 1 against a fixture that always strands would pass for a check that
    ignores the manifest entirely.

    Asserted the reverse until the exit-code contract landed. A spec directory the
    tool has stopped reading is exactly the silent failure the spec_root feature
    exists to remove, so it is a finding, not a note.
    """
    import json
    import subprocess

    repo = tmp_path / "proj"
    repo.mkdir()
    subprocess.run(["git", "init", str(repo)], check=True, capture_output=True)
    (repo / "specs" / "18-left-behind").mkdir(parents=True)

    (repo / ".wf-skills-manifest.json").write_text(json.dumps({}))
    assert _doctor_in(repo, monkeypatch).exit_code == 0

    (repo / ".wf-skills-manifest.json").write_text(json.dumps({"spec_root": str(tmp_path / "elsewhere")}))
    stranded = _doctor_in(repo, monkeypatch)

    assert "still holds" in stranded.output
    assert stranded.exit_code == 1


def test_doctor_does_not_warn_when_the_root_is_the_in_repo_specs_dir(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A recorded root pointing at `<repo>/specs` strands nothing.

    Compared unresolved, it looked like a mismatch: a relative value comes back
    resolved while repo_root does not have to be (WFCTL_REPO_ROOT is taken
    verbatim, and /tmp is a symlink on macOS). Doctor then told the reader to
    move specs from a directory to itself — wrong advice from the command whose
    job is being trusted about repo state.
    """
    import json
    import os
    import subprocess

    real = tmp_path / "proj"
    real.mkdir()
    subprocess.run(["git", "init", str(real)], check=True, capture_output=True)
    (real / "specs" / "18-here").mkdir(parents=True)
    (real / ".wf-skills-manifest.json").write_text(json.dumps({"spec_root": "specs"}))

    # An unresolved path to the same repo, which is what an env override gives.
    link = tmp_path / "via-symlink"
    os.symlink(real, link)
    monkeypatch.setenv("WFCTL_REPO_ROOT", str(link))

    result = _doctor_in(link, monkeypatch)

    assert "still holds" not in result.output, result.output


def test_doctor_does_not_warn_for_a_transient_env_override(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The warning is about what a manifest records, not what resolution returns.

    WFCTL_SPEC_DIR is a per-invocation escape hatch. Keyed on the resolved root,
    a one-off `WFCTL_SPEC_DIR=... wfctl doctor` announced "spec_root is set" in a
    repo that records nothing — and anyone who exports the var in a shell profile
    would be nagged to move their specs into a transient directory, in every repo.
    """
    import subprocess

    repo = tmp_path / "proj"
    repo.mkdir()
    subprocess.run(["git", "init", str(repo)], check=True, capture_output=True)
    (repo / "specs" / "18-normal").mkdir(parents=True)
    monkeypatch.setenv("WFCTL_SPEC_DIR", str(tmp_path / "transient"))

    assert "still holds" not in _doctor_in(repo, monkeypatch).output


# .gitignore coverage guard (#11). These assert on the resulting file contents,
# not on how coverage was determined, so a batched implementation must pass them
# unchanged.


def test_install_skills_skips_glob_covered_paths(agent_dir: Path) -> None:
    """A path an existing pattern already covers gets no line of its own.

    Regression test for #11 — fails against a literal-comparison guard.
    """
    import os
    repo_root = Path(os.environ["WFCTL_REPO_ROOT"])
    (repo_root / ".gitignore").write_text(".agents/\n")

    result = runner.invoke(app, ["install-skills"])
    assert result.exit_code == 0

    lines = (repo_root / ".gitignore").read_text().splitlines()
    assert ".agents/skills/test-skill" not in lines
    assert ".agents/commands/test-cmd.md" not in lines
    assert ".agents/" in lines, "the covering pattern itself is untouched"


def test_install_skills_second_run_leaves_gitignore_identical(    agent_dir: Path
) -> None:
    """Installing twice against an unchanged repo is a no-op on .gitignore."""
    import os
    repo_root = Path(os.environ["WFCTL_REPO_ROOT"])

    assert runner.invoke(
        app, ["install-skills"]
    ).exit_code == 0
    after_first = (repo_root / ".gitignore").read_bytes()

    assert runner.invoke(
        app, ["install-skills"]
    ).exit_code == 0
    assert (repo_root / ".gitignore").read_bytes() == after_first


def test_install_skills_creates_gitignore_when_absent(agent_dir: Path) -> None:
    """No .gitignore at all still gets one, listing every installed path."""
    import os
    repo_root = Path(os.environ["WFCTL_REPO_ROOT"])
    (repo_root / ".gitignore").unlink(missing_ok=True)

    result = runner.invoke(app, ["install-skills"])
    assert result.exit_code == 0

    lines = (repo_root / ".gitignore").read_text().splitlines()
    assert ".agents/skills/test-skill" in lines
    assert ".agents/commands/test-cmd.md" in lines
    assert ".wf-skills-manifest.json" in lines
    assert ".wf-skills-backup/" in lines


def test_install_skills_appends_uncovered_paths(agent_dir: Path) -> None:
    """An existing .gitignore that covers none of the install paths is appended to,
    unchanged from the behavior before the coverage guard."""
    import os
    repo_root = Path(os.environ["WFCTL_REPO_ROOT"])
    (repo_root / ".gitignore").write_text("*.log\n")

    result = runner.invoke(app, ["install-skills"])
    assert result.exit_code == 0

    lines = (repo_root / ".gitignore").read_text().splitlines()
    assert "*.log" in lines, "the unrelated pattern survives"
    assert ".agents/skills/test-skill" in lines
    assert ".agents/commands/test-cmd.md" in lines


def test_ensure_gitignored_handles_directory_form(repo_root: Path) -> None:
    """Directory-form entries need their trailing slash to resolve.

    git only matches the pattern with the slash when the directory does not yet
    exist on disk, which is the normal case at install time.
    """
    from wfctl.cli import _ensure_gitignored

    (repo_root / ".gitignore").write_text("wt/\n")
    assert _ensure_gitignored(repo_root, "wt/") is False, "covered, nothing written"
    assert _ensure_gitignored(repo_root, ".wf-skills-backup/") is True, "not covered, written"
    assert ".wf-skills-backup/" in (repo_root / ".gitignore").read_text().splitlines()
    assert (repo_root / ".gitignore").read_text().splitlines().count("wt/") == 1


def test_ensure_gitignored_appends_when_not_a_repo(tmp_path: Path, capsys) -> None:
    """Outside a git repo the check cannot answer: write the line, stay quiet.

    `check-ignore` exits 128 there and writes `fatal:` to stderr.
    """
    from wfctl.cli import _ensure_gitignored

    not_a_repo = tmp_path / "plain"
    not_a_repo.mkdir()
    capsys.readouterr()  # drop anything buffered before this call

    assert _ensure_gitignored(not_a_repo, "build/") is True
    assert (not_a_repo / ".gitignore").read_text() == "build/\n"

    captured = capsys.readouterr()
    assert "fatal" not in captured.err
    assert "fatal" not in captured.out


def test_install_skills_skips_tracked_path_covered_by_pattern(    agent_dir: Path
) -> None:
    """A tracked path matched by a pattern gets no entry — one would be inert.

    Covers `--no-index`; without it `check-ignore` reports a tracked path as not
    ignored and the guard appends a dead line.
    """
    import os
    repo_root = Path(os.environ["WFCTL_REPO_ROOT"])

    dest = repo_root / ".agents" / "skills" / "test-skill"
    dest.mkdir(parents=True)
    (dest / "SKILL.md").write_text("# placeholder\n")
    # -f because .agents/ is ignored below; a plain `add` would refuse.
    subprocess.run(
        ["git", "-C", str(repo_root), "add", "-f", ".agents/skills/test-skill/SKILL.md"],
        check=True, capture_output=True,
    )
    subprocess.run(
        ["git", "-C", str(repo_root), "commit", "-m", "track a skill"],
        check=True, capture_output=True,
    )
    (repo_root / ".gitignore").write_text(".agents/\n")

    # --yes: the pre-created destination reads as a foreign overwrite, which
    # otherwise prompts and aborts under the non-interactive test runner.
    result = runner.invoke(
        app, ["install-skills", "--yes"]
    )
    assert result.exit_code == 0
    assert ".agents/skills/test-skill" not in (
        repo_root / ".gitignore"
    ).read_text().splitlines()


def test_install_skills_appends_after_missing_trailing_newline(    agent_dir: Path
) -> None:
    """A .gitignore with no trailing newline must not get the first entry glued
    onto its last line."""
    import os
    repo_root = Path(os.environ["WFCTL_REPO_ROOT"])
    (repo_root / ".gitignore").write_text("*.log")  # deliberately no newline

    result = runner.invoke(app, ["install-skills"])
    assert result.exit_code == 0

    lines = (repo_root / ".gitignore").read_text().splitlines()
    assert "*.log" in lines, "not concatenated with the appended entry"
    assert ".wf-skills-manifest.json" in lines


def test_install_skills_reports_skipped_count(agent_dir: Path) -> None:
    """Entries skipped as already covered are counted in the output."""
    import os
    repo_root = Path(os.environ["WFCTL_REPO_ROOT"])
    (repo_root / ".gitignore").write_text(".agents/\n")

    result = runner.invoke(app, ["install-skills"])
    assert result.exit_code == 0
    # `.agents/` covers the skill and the command; the manifest and the backup
    # dir match nothing, so exactly two of the four are skipped.
    assert "2 ignore entries already covered" in result.output


def test_install_skills_silent_when_nothing_skipped(agent_dir: Path) -> None:
    """The clean case adds no output — no zero count."""
    import os
    repo_root = Path(os.environ["WFCTL_REPO_ROOT"])
    (repo_root / ".gitignore").unlink(missing_ok=True)

    result = runner.invoke(app, ["install-skills"])
    assert result.exit_code == 0
    assert "already covered" not in result.output


def test_ensure_gitignored_treats_dash_leading_paths_as_paths(repo_root: Path) -> None:
    """A path beginning with `-` is a path, not a flag.

    Covers the `--` separator; without it git parses the dash as an option
    (`-Z` exits 129) and the non-zero result reads as "not covered".
    """
    from wfctl.cli import _ensure_gitignored

    (repo_root / ".gitignore").write_text("-Z\n--no-index\n")
    assert _ensure_gitignored(repo_root, "-Z") is False, "covered, nothing written"
    assert _ensure_gitignored(repo_root, "--no-index") is False, "covered, nothing written"
    assert (repo_root / ".gitignore").read_text() == "-Z\n--no-index\n", "byte-identical"

    assert _ensure_gitignored(repo_root, "-unlisted") is True, "uncovered, written"
    assert "-unlisted" in (repo_root / ".gitignore").read_text().splitlines()


# --- Where this project's specs live: asked once, on first interactive setup ---


def _manifest(repo_root: Path) -> dict:
    import json
    return json.loads((repo_root / ".wf-skills-manifest.json").read_text())


def _install(*extra: str, answers: str = "") -> object:
    return runner.invoke(
        app, ["install-skills", *extra],
        input=answers,
    )


def test_asked_marker_is_not_mistaken_for_an_installed_layer(
    agent_dir: Path, tmp_path: Path
) -> None:
    """`_layer_keys` returns every manifest key it does not know to skip, and its
    callers do `manifest[key].get("items", [])`. A bare `True` there raises
    AttributeError on sight — in doctor and in install-skills both."""
    import os
    from wfctl.cli import _layer_keys
    repo_root = Path(os.environ["WFCTL_REPO_ROOT"])
    (repo_root / ".wf-skills-manifest.json").write_text(
        '{"base": {"items": []}, "tracker": null, "spec_root_asked": true}\n'
    )

    assert "spec_root_asked" not in _layer_keys(_manifest(repo_root))
    # `exit_code is not None` was vacuous: CliRunner captures the exception and
    # still reports a code, so an AttributeError would have passed. Assert the
    # run actually succeeded and that nothing was raised.
    result = runner.invoke(app, ["doctor"])
    assert result.exception is None, result.exception
    assert result.exit_code == 0, result.output


def test_spec_location_is_not_asked_without_a_human(bundle: Path, agent_dir: Path) -> None:
    """Non-interactive installs record no location and no marker."""
    import os
    repo_root = Path(os.environ["WFCTL_REPO_ROOT"])

    assert _install().exit_code == 0

    m = _manifest(repo_root)
    assert "spec_root" not in m
    assert "spec_root_asked" not in m


def test_spec_location_is_not_asked_with_yes(    agent_dir: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """`--yes` suppresses the question the same way it suppresses the tracker's."""
    import os
    from wfctl import cli
    monkeypatch.setattr(cli, "_interactive", lambda: True)
    repo_root = Path(os.environ["WFCTL_REPO_ROOT"])

    assert _install("--yes").exit_code == 0

    assert "spec_root_asked" not in _manifest(repo_root)


def test_keeping_specs_in_the_repo_records_no_location(    agent_dir: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The default answer must be indistinguishable from never having been asked.

    That is what makes it safe: `spec_root` stays absent, so resolution is
    byte-identical to a repo that predates the question.
    """
    import os
    from wfctl import cli
    from wfctl._paths import spec_root
    monkeypatch.setattr(cli, "_interactive", lambda: True)
    repo_root = Path(os.environ["WFCTL_REPO_ROOT"])

    assert _install(answers="n\n1\n").exit_code == 0

    m = _manifest(repo_root)
    assert "spec_root" not in m, "option 1 must record no location"
    assert m["spec_root_asked"] is True
    assert spec_root(repo_root) == repo_root / "specs"


def test_choosing_a_durable_location_records_it_and_reports_the_files(
    agent_dir: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Never created, never cloned, never checked for existence — a not-yet-existing
    root is the case the setting exists to support."""
    import os
    from wfctl import cli
    monkeypatch.setattr(cli, "_interactive", lambda: True)
    repo_root = Path(os.environ["WFCTL_REPO_ROOT"])
    target = tmp_path.parent / "nowhere-yet"

    result = _install(answers=f"n\n3\n{target}\n")

    assert result.exit_code == 0
    m = _manifest(repo_root)
    assert m["spec_root"] == str(target)
    assert m["spec_root_asked"] is True
    assert not target.exists(), "the root must not be created"
    assert str(repo_root / ".wf-skills-manifest.json") in result.output


def test_the_question_is_asked_once(    agent_dir: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """post_create runs install-skills in every new worktree; a second prompt on
    every upgrade would be noise."""
    from wfctl import cli
    monkeypatch.setattr(cli, "_interactive", lambda: True)

    first = _install(answers="n\n1\n")
    assert "Where should this project's specs live?" in first.output

    second = _install(answers="")
    assert second.exit_code == 0
    assert "Where should this project's specs live?" not in second.output


def test_an_existing_spec_root_counts_as_already_answered(    agent_dir: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Issue #26 requires the question be skipped when a root is already recorded.

    Repos that ran `wfctl spec-root` before this prompt existed have no marker.
    Asking them would be asking a question they answered more explicitly than the
    prompt can, and a wrong answer would silently relocate their specs.
    """
    import os
    from wfctl import cli
    monkeypatch.setattr(cli, "_interactive", lambda: True)
    repo_root = Path(os.environ["WFCTL_REPO_ROOT"])
    (repo_root / ".wf-skills-manifest.json").write_text(
        '{"spec_root": "/somewhere/durable"}\n'
    )

    # No answer supplied: a re-prompt would abort on EOF rather than pass.
    result = _install(answers="n\n")

    assert result.exit_code == 0
    assert "Where should this project's specs live?" not in result.output
    assert _manifest(repo_root)["spec_root"] == "/somewhere/durable"


def test_option_two_with_an_absolute_path_keeps_its_clone_guidance(
    agent_dir: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The option drives the guidance, not the path's shape.

    Both prompts accept absolute and relative input, so inferring the option from
    `is_absolute()` dropped the clone instructions for an absolute answer to
    option 2 — and handed them to a relative answer to option 3.
    """
    import os
    from wfctl import cli
    monkeypatch.setattr(cli, "_interactive", lambda: True)
    repo_root = Path(os.environ["WFCTL_REPO_ROOT"])
    target = tmp_path.parent / "abs-specs"

    result = _install(answers=f"n\n2\n{target}\n")

    assert result.exit_code == 0
    assert "git clone" in result.output, "option 2 lost its guidance"
    assert _manifest(repo_root)["spec_root"] == str(target)


def test_option_three_with_a_relative_path_gets_no_clone_guidance(    agent_dir: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The mirror case: a relative answer to option 3 is not a specs repo."""
    from wfctl import cli
    monkeypatch.setattr(cli, "_interactive", lambda: True)

    result = _install(answers="n\n3\n../elsewhere\n")

    assert result.exit_code == 0
    assert "git clone" not in result.output


def test_option_two_clone_commands_are_anchored_to_the_main_checkout(    agent_dir: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """`chosen` is stored relative to the main checkout, but these lines get
    pasted into whatever shell the user is standing in. Left relative, running
    them from a linked worktree would create the specs repo inside the worktree —
    the one place it must not go."""
    import os
    from wfctl import cli
    monkeypatch.setattr(cli, "_interactive", lambda: True)
    repo_root = Path(os.environ["WFCTL_REPO_ROOT"])

    result = _install(answers="n\n2\nproj-specs\n")

    assert f"git clone <url> {repo_root / 'proj-specs'}" in result.output

def _rename_shipped_command(bundle: Path, old: str, new: str) -> None:
    """Rename a file the bundle ships, which is what an upstream rename looks
    like from the installer's side.

    The rename happens between two real installs rather than in a hand-written
    manifest. The defect #38 reports is in what `install-skills` *writes*, so a
    fixture asserting what we think it wrote would restate the assumption that
    produced the bug instead of testing it.
    """
    commands = bundle / "agents" / "commands"
    (commands / old).rename(commands / new)


def test_a_path_the_install_stopped_shipping_is_named_and_left_alone(
    bundle: Path, agent_dir: Path
) -> None:
    """The default is report, not remove: a path also stops being shipped when
    the consumer edited it or when a layer was deselected, and the install
    cannot be sure which of those it is looking at."""
    import os
    repo_root = Path(os.environ["WFCTL_REPO_ROOT"])
    runner.invoke(app, ["install-skills", "--agent", "claude", "--yes"])
    _rename_shipped_command(bundle, "test-cmd.md", "speckit.test-cmd.md")

    result = runner.invoke(app, ["install-skills", "--agent", "claude", "--yes"])

    assert result.exit_code == 0
    assert "no longer shipped" in result.output
    assert ".claude/commands/test-cmd.md" in result.output
    assert (repo_root / ".claude" / "commands" / "test-cmd.md").exists()


def test_a_reported_orphan_stays_on_record_so_the_prune_it_advises_can_reach_it(
    bundle: Path, agent_dir: Path
) -> None:
    """The report tells the reader to re-run with --prune, and replacing the
    layer wholesale would make that advice impossible to act on: the record
    naming the path is the only thing the next run could diff against, and
    dropping it in the same breath as reporting it is what put the original
    orphan out of reach in the first place."""
    import os
    repo_root = Path(os.environ["WFCTL_REPO_ROOT"])
    runner.invoke(app, ["install-skills", "--agent", "claude", "--yes"])
    _rename_shipped_command(bundle, "test-cmd.md", "speckit.test-cmd.md")
    runner.invoke(app, ["install-skills", "--agent", "claude", "--yes"])

    recorded = {i["path"] for i in _recorded_items(json.loads(
        (repo_root / ".wf-skills-manifest.json").read_text()
    ))}

    assert ".claude/commands/test-cmd.md" in recorded


def test_prune_deletes_a_path_the_install_no_longer_ships(
    bundle: Path, agent_dir: Path
) -> None:
    """The half the automation needs. A prune that only ever reported would
    leave every orphan on disk, which is the state #38 exists to end."""
    import os
    repo_root = Path(os.environ["WFCTL_REPO_ROOT"])
    runner.invoke(app, ["install-skills", "--agent", "claude", "--yes"])
    _rename_shipped_command(bundle, "test-cmd.md", "speckit.test-cmd.md")

    result = runner.invoke(app, ["install-skills", "--agent", "claude", "--yes", "--prune"])

    assert result.exit_code == 0
    assert not (repo_root / ".claude" / "commands" / "test-cmd.md").exists()
    assert (repo_root / ".claude" / "commands" / "speckit.test-cmd.md").exists()
    recorded = {i["path"] for i in _recorded_items(json.loads(
        (repo_root / ".wf-skills-manifest.json").read_text()
    ))}
    assert ".claude/commands/test-cmd.md" not in recorded


def test_deselecting_an_agent_layer_does_not_orphan_the_paths_it_installed(
    bundle: Path, agent_dir: Path
) -> None:
    """The diff is per-layer for this case. A path leaves the union of recorded
    paths when the user installs a *narrower* set of layers too, so a
    whole-manifest diff would report every path of the layer they deselected and
    --prune would delete a working install of it."""
    import os
    repo_root = Path(os.environ["WFCTL_REPO_ROOT"])
    runner.invoke(app, ["install-skills", "--agent", "claude", "--yes"])

    result = runner.invoke(app, ["install-skills", "--yes", "--prune"])

    assert result.exit_code == 0
    assert "no longer shipped" not in result.output
    assert (repo_root / ".claude" / "commands" / "test-cmd.md").exists()


def test_prune_puts_back_the_file_it_overwrote_when_it_drops_the_path(
    bundle: Path, agent_dir: Path
) -> None:
    """Deleting the path and leaving the backup would strand the user's own file
    under .wf-skills-backup/ with its record gone — the same unreachable-output
    defect this flag exists to fix, one directory over."""
    import os
    repo_root = Path(os.environ["WFCTL_REPO_ROOT"])
    mine = repo_root / ".claude" / "commands" / "test-cmd.md"
    mine.parent.mkdir(parents=True)
    mine.write_text("# mine\n")
    runner.invoke(app, ["install-skills", "--agent", "claude", "--yes"])
    _rename_shipped_command(bundle, "test-cmd.md", "speckit.test-cmd.md")

    result = runner.invoke(app, ["install-skills", "--agent", "claude", "--yes", "--prune"])

    assert result.exit_code == 0
    assert mine.read_text() == "# mine\n"


def test_prune_removes_a_symlinked_install_path_without_crashing(
    bundle: Path, agent_dir: Path
) -> None:
    """Linking installed paths in from a main checkout is a real layout — #38's
    own evidence found twelve worktrees doing it. `is_dir()` follows the link and
    `shutil.rmtree` refuses one, so the plain directory-or-file branch raised
    partway through `install-skills` and took the whole command down.

    The link goes; what it points at is never wfctl's to delete.
    """
    import os
    repo_root = Path(os.environ["WFCTL_REPO_ROOT"])
    runner.invoke(app, ["install-skills", "--yes"])
    installed = repo_root / ".agents" / "skills" / "test-skill"
    elsewhere = repo_root.parent / "main-checkout-skill"
    shutil.move(str(installed), str(elsewhere))
    installed.symlink_to(elsewhere)
    (bundle / "agents" / "skills" / "test-skill").rename(
        bundle / "agents" / "skills" / "renamed-skill"
    )

    result = runner.invoke(app, ["install-skills", "--yes", "--prune"])

    assert result.exit_code == 0, result.output
    assert not installed.is_symlink()
    assert (elsewhere / "SKILL.md").exists(), "the link's target is not ours to delete"


def test_prune_leaves_a_recorded_path_that_escapes_the_repo(
    bundle: Path, agent_dir: Path, tmp_path: Path
) -> None:
    """`Path` joining discards the repo root when the recorded path is absolute,
    so one hand-edited or corrupted manifest row would have --prune delete outside
    the project entirely. Nothing wfctl writes looks like this; the guard is on
    the delete because that is where being wrong is unrecoverable."""
    import os
    repo_root = Path(os.environ["WFCTL_REPO_ROOT"])
    outsider = tmp_path.parent / "not-ours.md"
    outsider.write_text("someone else's file\n")
    runner.invoke(app, ["install-skills", "--yes"])
    with _edit_manifest(repo_root) as manifest:
        manifest["base"]["items"].append({"path": str(outsider), "backup": None})

    result = runner.invoke(app, ["install-skills", "--yes", "--prune"])

    assert result.exit_code == 0
    assert outsider.exists(), "a path outside the repo is never wfctl's to remove"
    assert "outside this repo" in result.output


def test_doctor_names_the_agent_layer_in_the_command_it_advises(
    bundle: Path, agent_dir: Path
) -> None:
    """The bare form does not repair an agent layer's drift. `install-skills`
    rewrites the record only for layers it installed, so the advice a reader
    follows would report the same finding on every later session and re-run the
    same incomplete fix each time — the loop a review panel reproduced.

    Drift is created by changing the bundle between two real installs rather than
    by editing the record, because the recorded hash is what doctor reads.
    """
    runner.invoke(app, ["install-skills", "--agent", "claude", "--yes"])
    (bundle / "agents" / "skills" / "later-skill").mkdir(parents=True)
    (bundle / "agents" / "skills" / "later-skill" / "SKILL.md").write_text("# later\n")

    out = runner.invoke(app, ["doctor"]).output

    assert "update: wfctl install-skills --agent claude" in out
    base_line = [ln for ln in out.splitlines() if "update:" in ln and "--agent" not in ln]
    assert base_line, "the base layer still repairs with no flag"


# ---------------------------------------------------------------------------
# Bob agent: Claude-only frontmatter stripping
# ---------------------------------------------------------------------------

def test_bob_install_strips_disable_model_invocation(
    agent_dir: Path, bundle: Path
) -> None:
    """Commands installed to .bob/commands/ must not contain
    `disable-model-invocation` — Bob Shell interprets that key literally and
    skips model invocation, so the skill body never executes."""
    import os

    repo_root = Path(os.environ["WFCTL_REPO_ROOT"])
    cmd = bundle / "agents" / "commands" / "test-cmd.md"
    cmd.write_text(
        "---\n"
        "disable-model-invocation: true\n"
        "allowed-tools: Read Bash(git status*)\n"
        "description: A command that does something.\n"
        "---\n"
        "\nDo the thing.\n"
    )

    result = runner.invoke(app, ["install-skills", "--agent", "bob", "--yes"])
    assert result.exit_code == 0

    installed = (repo_root / ".bob" / "commands" / "test-cmd.md").read_text()
    assert "disable-model-invocation" not in installed
    assert "allowed-tools" not in installed
    # description must survive
    assert "description: A command that does something." in installed
    # body must survive
    assert "Do the thing." in installed


def test_bob_install_drops_frontmatter_block_when_only_claude_keys(
    agent_dir: Path, bundle: Path
) -> None:
    """When every frontmatter key is Claude-only, the block is dropped entirely
    rather than leaving a bare `---\\n---\\n` stub."""
    import os

    repo_root = Path(os.environ["WFCTL_REPO_ROOT"])
    cmd = bundle / "agents" / "commands" / "test-cmd.md"
    cmd.write_text(
        "---\n"
        "disable-model-invocation: true\n"
        "allowed-tools: Read\n"
        "---\n"
        "\nDo the thing.\n"
    )

    runner.invoke(app, ["install-skills", "--agent", "bob", "--yes"])

    installed = (repo_root / ".bob" / "commands" / "test-cmd.md").read_text()
    # The frontmatter block must be gone — file must not start with a fence.
    assert not installed.lstrip().startswith("---")
    assert "Do the thing." in installed


def test_non_bob_install_preserves_claude_frontmatter(
    agent_dir: Path, bundle: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Claude frontmatter must not be stripped when installing for --agent claude."""
    import os

    repo_root = Path(os.environ["WFCTL_REPO_ROOT"])
    cmd = bundle / "agents" / "commands" / "test-cmd.md"
    cmd.write_text(
        "---\n"
        "disable-model-invocation: true\n"
        "description: A command.\n"
        "---\n"
        "\nDo the thing.\n"
    )

    runner.invoke(app, ["install-skills", "--agent", "claude", "--yes"])

    installed = (repo_root / ".claude" / "commands" / "test-cmd.md").read_text()
    assert "disable-model-invocation: true" in installed


# --- install-skills --from: the named source (#146) ---------------------------
#
# The autouse `bundle` fixture is the *running* wfctl's tree. Every test below
# needs a second one to point `--from` at, and needs its content to differ, or
# "installed from the source you named" and "installed from the running tool"
# produce the same bytes and no assertion can tell them apart.

_NAMED_SOURCE_SKILL = "# from the named source\n"


def _named_source(root: Path) -> Path:
    """A second bundle, shaped like conftest's but with distinguishable content."""
    skill = root / "agents" / "skills" / "test-skill"
    skill.mkdir(parents=True)
    (skill / "SKILL.md").write_text(_NAMED_SOURCE_SKILL)
    commands = root / "agents" / "commands"
    commands.mkdir(parents=True)
    (commands / "test-cmd.md").write_text("# test-cmd from the named source\n")
    return root


def test_install_from_a_named_source_copies_that_source(
    tmp_path_factory: pytest.TempPathFactory, agent_dir: Path
) -> None:
    """The headline of #146: the installed tree is the one you pointed at.

    Asserts content rather than the summary line, because a run that printed the
    source and copied the running bundle would satisfy the line and none of the
    reason for it.
    """
    repo_root = agent_dir.parent
    source = _named_source(tmp_path_factory.mktemp("named-source"))

    result = runner.invoke(app, ["install-skills", "--from", str(source)])

    assert result.exit_code == 0
    installed = repo_root / ".agents" / "skills" / "test-skill" / "SKILL.md"
    assert installed.read_text() == _NAMED_SOURCE_SKILL


def test_install_from_a_checkout_root_finds_the_package_inside_it(
    tmp_path_factory: pytest.TempPathFactory, agent_dir: Path
) -> None:
    """`--from ../116-pr` names a worktree, and the trees are one level in.

    The spelling people actually have in hand — `resolve_root` covers the probe,
    this covers that `install-skills` goes through it rather than joining the
    path itself.
    """
    repo_root = agent_dir.parent
    checkout = tmp_path_factory.mktemp("checkout")
    _named_source(checkout / "wfctl")

    result = runner.invoke(app, ["install-skills", "--from", str(checkout)])

    assert result.exit_code == 0
    installed = repo_root / ".agents" / "skills" / "test-skill" / "SKILL.md"
    assert installed.read_text() == _NAMED_SOURCE_SKILL


def test_a_named_source_is_recorded_absolute_and_a_default_records_nothing(
    tmp_path_factory: pytest.TempPathFactory, agent_dir: Path
) -> None:
    """Absence of the key is what means "the default" — no sentinel, no migration.

    Both halves in one test because the pair is the contract: were the key
    written as `"default"` the first assertion would still pass, and every
    manifest predating this feature would read as unmeasurable.
    """
    repo_root = agent_dir.parent
    source = _named_source(tmp_path_factory.mktemp("named-source"))
    manifest_path = repo_root / ".wf-skills-manifest.json"

    runner.invoke(app, ["install-skills", "--agent", "claude", "--from", str(source)])
    named = json.loads(manifest_path.read_text())
    for layer in ("base", "claude"):
        assert Path(named[layer]["source"]).is_absolute()
        assert Path(named[layer]["source"]) == source.resolve()

    runner.invoke(app, ["install-skills", "--agent", "claude", "--yes"])
    default = json.loads(manifest_path.read_text())
    for layer in ("base", "claude"):
        assert "source" not in default[layer]


def test_doctor_reports_a_named_source_as_a_state_not_as_drift(
    tmp_path_factory: pytest.TempPathFactory, agent_dir: Path
) -> None:
    """The whole point of the feature.

    Before this change the same situation was reported as drift on every run,
    because the only thing `doctor` could compare against was the running wheel.
    """
    source = _named_source(tmp_path_factory.mktemp("named-source"))
    runner.invoke(app, ["install-skills", "--from", str(source)])

    result = runner.invoke(app, ["doctor"])

    assert result.exit_code == 0
    assert f"base: skills current (from {source.resolve()})" in result.output


def test_a_relative_source_still_resolves_from_a_different_directory(
    tmp_path_factory: pytest.TempPathFactory,
    agent_dir: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """FR-004, which asserting the stored path is absolute does not reach.

    `doctor` runs from wherever the session is standing, and `/start-session`
    runs it unprompted. A source stored as typed would resolve against the wrong
    directory on every run after the install — including the very next one.
    """
    import os

    repo_root = agent_dir.parent
    source = _named_source(tmp_path_factory.mktemp("named-source"))
    monkeypatch.chdir(repo_root)
    runner.invoke(app, ["install-skills", "--from", os.path.relpath(source, repo_root)])

    monkeypatch.chdir(repo_root / ".agents" / "skills")
    result = runner.invoke(app, ["doctor"])

    assert result.exit_code == 0
    assert f"base: skills current (from {source.resolve()})" in result.output


def test_a_source_holding_neither_tree_leaves_the_repo_untouched(
    tmp_path_factory: pytest.TempPathFactory, agent_dir: Path
) -> None:
    """A typo must not half-install, and must never fall back to the default.

    Falling back is the tempting behaviour and the wrong one: the run would
    report success over a tree the caller did not ask for, which is the exact
    confusion #146 opens with.
    """
    repo_root = agent_dir.parent
    empty = tmp_path_factory.mktemp("not-a-checkout")

    result = runner.invoke(app, ["install-skills", "--from", str(empty)])

    assert result.exit_code != 0
    assert str(empty) in result.output
    assert str(empty / "wfctl") in result.output
    assert not (repo_root / ".agents").exists()
    assert not (repo_root / ".wf-skills-manifest.json").exists()


def test_a_bare_install_over_a_named_source_says_so_even_under_yes(
    tmp_path_factory: pytest.TempPathFactory, agent_dir: Path
) -> None:
    """`--from` is one-shot, and the run that discards it must say so.

    Not gated on `--yes`, because the unattended session-start refresh is the
    case it exists for: `/start-session` passes `--yes`, so a suppressed notice
    would make the discard silent in the only place it happens automatically.
    """
    repo_root = agent_dir.parent
    source = _named_source(tmp_path_factory.mktemp("named-source"))
    runner.invoke(app, ["install-skills", "--from", str(source)])

    result = runner.invoke(app, ["install-skills", "--yes"])

    assert result.exit_code == 0
    assert "Will replace an install from" in result.output
    assert str(source.resolve()) in result.output
    manifest = json.loads((repo_root / ".wf-skills-manifest.json").read_text())
    assert "source" not in manifest["base"]


def test_prune_diffs_against_the_named_source_not_the_running_bundle(
    tmp_path_factory: pytest.TempPathFactory, agent_dir: Path
) -> None:
    """FR-012 holds today only because the prune diff reads from the plan.

    Nothing states that, so a later change routing the diff through
    `BUNDLE_ROOT` would restore the running tool as the authority and prune
    against a bundle nobody named. The renamed command still ships under the
    running bundle, so a prune reading that would keep the old path.
    """
    repo_root = agent_dir.parent
    source = _named_source(tmp_path_factory.mktemp("named-source"))
    runner.invoke(app, ["install-skills", "--agent", "claude", "--yes", "--from", str(source)])
    _rename_shipped_command(source, "test-cmd.md", "speckit.test-cmd.md")

    result = runner.invoke(
        app, ["install-skills", "--agent", "claude", "--yes", "--prune", "--from", str(source)]
    )

    assert result.exit_code == 0
    assert not (repo_root / ".claude" / "commands" / "test-cmd.md").exists()
    assert (repo_root / ".claude" / "commands" / "speckit.test-cmd.md").exists()
    recorded = {i["path"] for i in _recorded_items(json.loads(
        (repo_root / ".wf-skills-manifest.json").read_text()
    ))}
    assert ".claude/commands/test-cmd.md" not in recorded


def test_doctor_reports_the_named_source_moving_on(
    tmp_path_factory: pytest.TempPathFactory, agent_dir: Path
) -> None:
    """The edit-install-test loop, which is silent without this.

    Someone installs from a branch to try a skill, edits the skill, and has no
    signal that the installed copy is now behind. Reported as a finding rather
    than a warning: the repo genuinely holds something other than what its record
    names, which is the same condition as ordinary staleness.
    """
    source = _named_source(tmp_path_factory.mktemp("named-source"))
    runner.invoke(app, ["install-skills", "--from", str(source)])
    (source / "agents" / "skills" / "test-skill" / "SKILL.md").write_text("# moved on\n")

    result = runner.invoke(app, ["doctor"])

    assert result.exit_code == 1
    assert f"base: source changed since install — {source.resolve()}" in result.output


def test_the_remedy_carries_the_source_only_for_the_layer_that_recorded_one(
    tmp_path_factory: pytest.TempPathFactory, agent_dir: Path, bundle: Path
) -> None:
    """FR-008. The printed command is what the reader — or `/start-session` — runs.

    A remedy without `--from` repairs the drift by discarding the source that
    produced it, which destroys exactly the install the reader was testing. Both
    layers are asserted in one test because the failure is a line that is right
    for one kind of layer and wrong for the other, and only the pair catches
    `--from` leaking onto a default install.
    """
    source = _named_source(tmp_path_factory.mktemp("named-source"))
    runner.invoke(app, ["install-skills", "--agent", "claude", "--from", str(source)])
    # Base back on the default, claude still on the named source.
    runner.invoke(app, ["install-skills", "--yes"])
    (source / "agents" / "skills" / "test-skill" / "SKILL.md").write_text("# moved on\n")
    (bundle / "agents" / "skills" / "test-skill" / "SKILL.md").write_text("# also moved\n")

    remedies = {
        line.strip()
        for line in runner.invoke(app, ["doctor"]).output.splitlines()
        if line.strip().startswith("update:")
    }

    assert remedies == {
        f"update: wfctl install-skills --agent claude --from {source.resolve()}",
        "update: wfctl install-skills",
    }


def test_doctor_warns_rather_than_fails_when_the_recorded_source_is_gone(
    tmp_path_factory: pytest.TempPathFactory, agent_dir: Path
) -> None:
    """A checkout that moved is not a defect in this repo.

    Reported as a warning and left out of the exit code, the way a record with no
    fingerprint already is: the layer may well be current, and the only thing
    that could say either way is the thing that is missing. Failing here would
    turn every session start red for a worktree someone tidied up.
    """
    source = _named_source(tmp_path_factory.mktemp("named-source"))
    runner.invoke(app, ["install-skills", "--from", str(source)])
    shutil.move(str(source), str(source.parent / "moved-away"))

    result = runner.invoke(app, ["doctor"])

    assert result.exit_code == 0
    assert f"base: installed from {source.resolve()} — source is gone" in result.output


def test_the_remedy_quotes_a_source_whose_path_holds_a_space(
    tmp_path_factory: pytest.TempPathFactory, agent_dir: Path
) -> None:
    """FR-008 again, for the half of it that is not "carries `--from`".

    The line's contract is that running it repairs the install, and
    `/start-session` runs it unattended. Unquoted, a source under `my src` printed
    as `--from /…/my src` and typer rejected the run with `Got unexpected extra
    argument(s) (src)` — a remedy that parses as two arguments repairs nothing.
    """
    source = _named_source(tmp_path_factory.mktemp("named source") / "my src")
    runner.invoke(app, ["install-skills", "--from", str(source)])
    (source / "agents" / "skills" / "test-skill" / "SKILL.md").write_text("# moved on\n")

    remedy = next(
        line.strip()
        for line in runner.invoke(app, ["doctor"]).output.splitlines()
        if line.strip().startswith("update:")
    )

    assert remedy == (
        f"update: wfctl install-skills --from {shlex.quote(str(source.resolve()))}"
    )
    # The point of quoting: the line survives the trip back through a shell.
    assert shlex.split(remedy)[-1] == str(source.resolve())


def test_a_bracketed_source_path_survives_the_console(
    tmp_path_factory: pytest.TempPathFactory, agent_dir: Path
) -> None:
    """Square brackets are legal in a directory name and are rich's markup syntax.

    Unescaped, `/x/[old]/wfctl` printed as `/x//wfctl` — a different path, with
    no error and nothing to tell the reader a path had been rewritten. Every
    source-bearing line is covered here because they took the escape separately
    and the install line took it last.
    """
    source = _named_source(tmp_path_factory.mktemp("bracketed") / "[old]")

    installed = runner.invoke(app, ["install-skills", "--from", str(source)])
    assert f"Installed from {source}" in installed.output

    current = runner.invoke(app, ["doctor"])
    assert f"skills current (from {source.resolve()})" in current.output

    (source / "agents" / "skills" / "test-skill" / "SKILL.md").write_text("# moved on\n")
    changed = runner.invoke(app, ["doctor"])
    assert f"source changed since install — {source.resolve()}" in changed.output
    assert str(source.resolve()) in shlex.split(
        next(line for line in changed.output.splitlines() if "update:" in line)
    )


def test_doctor_warns_rather_than_crashes_when_the_source_cannot_be_read(
    tmp_path_factory: pytest.TempPathFactory, agent_dir: Path
) -> None:
    """FR-009 covers "can't check", not only "isn't there".

    A source on an unmounted volume or under a directory this user cannot read is
    unmeasurable for the same reason a moved one is, and has the same remedy.
    Catching only FileNotFoundError let a PermissionError out as a traceback, and
    `doctor` runs inside `/start-session` before it has reported anything.
    """
    source = _named_source(tmp_path_factory.mktemp("unreadable"))
    runner.invoke(app, ["install-skills", "--from", str(source)])
    # A file, not the directory holding it: `os.walk` skips a directory it cannot
    # descend and the hash merely comes out different, which is the "source
    # changed" verdict rather than this one. Reading a file is where it raises.
    unreadable = source / "agents" / "skills" / "test-skill" / "SKILL.md"
    unreadable.chmod(0o000)
    try:
        result = runner.invoke(app, ["doctor"])
    finally:
        unreadable.chmod(0o644)

    assert result.exit_code == 0
    assert f"base: installed from {source.resolve()} — source is gone" in result.output


def test_a_partial_named_source_is_not_reported_as_a_broken_wheel(
    tmp_path_factory: pytest.TempPathFactory, agent_dir: Path
) -> None:
    """`resolve_root` admits a root holding one tree, so this state is reachable.

    The message was written when only a damaged wheel could reach it, and it sent
    the reader to reinstall wfctl over a defect in the path they had just typed.
    The default install's wording is asserted alongside, because the fix is a
    branch and a branch can take the wrong arm.
    """
    source = _named_source(tmp_path_factory.mktemp("agents-only"))

    named = runner.invoke(app, ["install-skills", "--from", str(source), "--yes"])

    assert f"missing from the source you named ({source.resolve()})" in named.output
    assert "missing from this wfctl install" not in named.output


def test_the_replacement_notice_is_future_tense(
    tmp_path_factory: pytest.TempPathFactory, agent_dir: Path
) -> None:
    """It prints before a confirm that can still abort the run.

    Past tense described something that had not happened yet, and on an abort
    would have been the last word about a replacement that never took place.
    """
    source = _named_source(tmp_path_factory.mktemp("named-source"))
    runner.invoke(app, ["install-skills", "--from", str(source)])

    result = runner.invoke(app, ["install-skills", "--yes"])

    assert f"Will replace an install from {source.resolve()}" in result.output


@pytest.mark.parametrize("chosen,installs", [("github", True), (None, False)])
def test_install_skills_inherits_the_tracker_from_the_main_checkout(
    bundle: Path, agent_dir: Path, tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch, chosen: str | None, installs: bool,
) -> None:
    """A worktree comes up with the project's tracker without anyone answering.

    #184: every install in a worktree's lifecycle is non-interactive — post_create
    is a hook and /start-session passes --yes — so the prompt is never shown and
    the key is never written either way. The choice is the project's, so it is
    inherited the way `spec_root` is. `None` inherits too: a recorded decline is
    a decision, and copying it is what keeps the question closed.
    """
    import json
    import os
    import subprocess
    _add_tracker(bundle)
    main = Path(os.environ["WFCTL_REPO_ROOT"])
    (main / ".wf-skills-manifest.json").write_text(json.dumps({"tracker": chosen}))
    wt = tmp_path / "wt" / "184-tracker"
    subprocess.run(
        ["git", "-C", str(main), "worktree", "add", "-b", "184-tracker", str(wt)],
        check=True, capture_output=True,
    )
    monkeypatch.setenv("WFCTL_REPO_ROOT", str(wt))

    result = runner.invoke(app, ["install-skills"])

    assert result.exit_code == 0, result.output
    manifest = json.loads((wt / ".wf-skills-manifest.json").read_text())
    assert manifest["tracker"] == chosen
    assert (wt / ".agents" / "trackers" / "github.json").exists() is installs


def test_a_later_bare_install_keeps_the_backend_on_record(
    bundle: Path, agent_dir: Path
) -> None:
    """The tracker's files survive installs that do not name a tracker.

    The copy loop runs only on a run that selected one, so without the carry
    forward every later `install-skills` drops the backend from the record and
    then diffs it as dropped upstream — and `--prune` acts on that. Two files
    make it a break rather than a mess: `github.json` names `github-board.sh` in
    its `start` argv, so losing half the pair leaves a config pointing at a path
    that is gone.

    The deselect at the end is the other half of the same rule: this must keep
    the record alive, not make it permanent.
    """
    import json
    repo_root = agent_dir.parent
    _add_tracker(bundle)
    assert runner.invoke(app, ["install-skills", "--tracker", "github"]).exit_code == 0

    result = runner.invoke(app, ["install-skills"])
    assert result.exit_code == 0
    assert "no longer shipped" not in result.output, result.output
    recorded = {
        i["path"]
        for i in json.loads((repo_root / ".wf-skills-manifest.json").read_text())
        ["base"]["items"]
    }
    assert ".agents/trackers/github.json" in recorded
    assert ".agents/trackers/github-board.sh" in recorded

    deselected = runner.invoke(app, ["install-skills", "--tracker", "none"])
    assert "no longer shipped" in deselected.output
    assert "github-board.sh" in deselected.output


def test_inherited_tracker_leaves_a_committed_config_alone(
    bundle: Path, agent_dir: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A project that commits its backend config gets it back untouched.

    `.agents/trackers/` is deliberately not gitignored — see
    test_install_skills_does_not_gitignore_tracker_config — so a worktree checks
    the config out from git while its own manifest is still empty. Inheriting the
    name must not also re-plan a copy of it: the write lands on a tracked file
    that no manifest records, which the installer reads as a foreign overwrite.
    Under the TTY-less hook this feature exists to serve, that prompt aborts the
    entire install and no skills land at all; under --yes it replaces the
    project's own config with the bundle's stock one.
    """
    import json
    import os
    import subprocess
    _add_tracker(bundle)
    main = Path(os.environ["WFCTL_REPO_ROOT"])
    committed = main / ".agents" / "trackers" / "github.json"
    committed.parent.mkdir(parents=True)
    mine = '{"verbs": {"list": ["gh", "issue", "list", "--limit", "99"]}}\n'
    committed.write_text(mine)
    subprocess.run(["git", "-C", str(main), "add", "-Af"], check=True, capture_output=True)
    subprocess.run(
        ["git", "-C", str(main), "commit", "-m", "commit the tracker config"],
        check=True, capture_output=True,
    )
    # After the commit, never in it: the manifest is gitignored by convention, so
    # a worktree that checked one out would have the key already and inherit
    # nothing — the shape that made an earlier draft of this test pass against
    # the very bug it exists to catch.
    (main / ".wf-skills-manifest.json").write_text(json.dumps({"tracker": "github"}))
    wt = tmp_path / "wt" / "184-committed"
    subprocess.run(
        ["git", "-C", str(main), "worktree", "add", "-b", "184-committed", str(wt)],
        check=True, capture_output=True,
    )
    monkeypatch.setenv("WFCTL_REPO_ROOT", str(wt))

    # No --yes and no TTY: exactly what `post_create` runs.
    result = runner.invoke(app, ["install-skills"])

    assert result.exit_code == 0, result.output
    assert "Proceed?" not in result.output, "a tracked config is not a foreign overwrite"
    assert (wt / ".agents" / "trackers" / "github.json").read_text() == mine
    manifest = json.loads((wt / ".wf-skills-manifest.json").read_text())
    assert manifest["tracker"] == "github"
    # The install ran to completion rather than aborting before the copy loop.
    assert (wt / ".agents" / "skills" / "test-skill" / "SKILL.md").exists()
    # And the half the project did not commit still arrives: `github.json`
    # names the script in its `start` argv, so a config kept without it declares
    # a verb that exits 127.
    assert (wt / ".agents" / "trackers" / "github-board.sh").exists()
