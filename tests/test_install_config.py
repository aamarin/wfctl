"""Tests for `wfctl install-config` — seed standardized repo config."""
from __future__ import annotations

import json
from pathlib import Path

import pytest
from typer.testing import CliRunner

from wfctl.cli import app

runner = CliRunner()

_WORKMUX_YAML = "worktree_dir: wt\nagent: claude\n"


def _install(bundle: Path, *extra: str, yaml: str = _WORKMUX_YAML):
    """Seed the fake bundle with the workmux config, then install it.

    The `bundle` fixture ships skills and commands only, so the config every
    test here needs is written on the way in rather than by each test.
    """
    cfg = bundle / "agents" / "configs" / "workmux"
    cfg.mkdir(parents=True, exist_ok=True)
    (cfg / ".workmux.yaml").write_text(yaml)
    return runner.invoke(
        app, ["install-config", "workmux", *extra]
    )


def test_seed_writes_workmux_and_gitignores_wt(bundle: Path, agent_dir: Path) -> None:
    repo_root = agent_dir.parent
    result = _install(bundle)
    assert result.exit_code == 0
    assert "worktree_dir: wt" in (repo_root / ".workmux.yaml").read_text()
    assert "wt/" in (repo_root / ".gitignore").read_text().splitlines()  # created (absent before)


def test_gitignore_appended_when_line_missing(bundle: Path, agent_dir: Path) -> None:
    repo_root = agent_dir.parent
    (repo_root / ".gitignore").write_text("*.log\n")
    _install(bundle)
    lines = (repo_root / ".gitignore").read_text().splitlines()
    assert "*.log" in lines and "wt/" in lines


def test_gitignore_no_duplicate_when_present(bundle: Path, agent_dir: Path) -> None:
    repo_root = agent_dir.parent
    (repo_root / ".gitignore").write_text("wt/\n")
    _install(bundle)
    assert (repo_root / ".gitignore").read_text().splitlines().count("wt/") == 1


def test_refuses_existing_without_force(bundle: Path, agent_dir: Path) -> None:
    repo_root = agent_dir.parent
    (repo_root / ".workmux.yaml").write_text("mine: true\n")
    result = _install(bundle)
    assert result.exit_code != 0
    assert ".workmux.yaml" in result.output
    assert (repo_root / ".workmux.yaml").read_text() == "mine: true\n"  # untouched


def test_force_overwrites(bundle: Path, agent_dir: Path) -> None:
    repo_root = agent_dir.parent
    (repo_root / ".workmux.yaml").write_text("mine: true\n")
    result = _install(bundle, "--force")
    assert result.exit_code == 0
    assert "worktree_dir: wt" in (repo_root / ".workmux.yaml").read_text()


def test_seeding_never_touches_the_manifest(bundle: Path, agent_dir: Path) -> None:
    """install-config is seed-once: no manifest entry, no backup, no uninstall.

    Both commands now read the same bundle, and this one runs the same copy loop
    over it, so a manifest write is a plausible thing to grow here by analogy —
    and would put files the user owns under `uninstall-skills`. Asserted for
    both states, since "absent" and "unchanged" are different bugs.
    """
    repo_root = agent_dir.parent
    manifest = repo_root / ".wf-skills-manifest.json"

    assert _install(bundle).exit_code == 0
    assert not manifest.exists()

    before = json.dumps({"base": {"items": []}})
    manifest.write_text(before)
    assert _install(bundle, "--force").exit_code == 0
    assert manifest.read_text() == before


def _seed_github(bundle: Path, body: str = "# Pull Request\n") -> Path:
    cfg = bundle / "agents" / "configs" / "github" / ".github"
    cfg.mkdir(parents=True, exist_ok=True)
    (cfg / "pull_request_template.md").write_text(body)
    return cfg


def test_nested_config_lands_at_its_path_in_the_repo(bundle: Path, agent_dir: Path) -> None:
    """A source directory's structure is the structure that lands in the repo."""
    repo_root = agent_dir.parent
    _seed_github(bundle)

    result = runner.invoke(app, ["install-config", "github"])
    assert result.exit_code == 0
    assert (repo_root / ".github" / "pull_request_template.md").read_text() == "# Pull Request\n"


def test_nested_config_merges_into_a_directory_the_repo_already_has(
    bundle: Path, agent_dir: Path
) -> None:
    """An existing `.github/` is not a conflict — the file inside it would be.

    Every repo worth seeding a PR template into already has `.github/`, so a
    conflict check on the top-level directory name would refuse all of them. The
    workflows beside the template must also survive the copy.
    """
    repo_root = agent_dir.parent
    workflow = repo_root / ".github" / "workflows" / "ci.yml"
    workflow.parent.mkdir(parents=True)
    workflow.write_text("name: CI\n")
    _seed_github(bundle)

    result = runner.invoke(app, ["install-config", "github"])
    assert result.exit_code == 0
    assert (repo_root / ".github" / "pull_request_template.md").exists()
    assert workflow.read_text() == "name: CI\n"


def test_nested_config_refuses_an_existing_file_by_its_repo_path(
    bundle: Path, agent_dir: Path
) -> None:
    repo_root = agent_dir.parent
    existing = repo_root / ".github" / "pull_request_template.md"
    existing.parent.mkdir(parents=True)
    existing.write_text("mine\n")
    _seed_github(bundle)

    result = runner.invoke(app, ["install-config", "github"])
    assert result.exit_code != 0
    # Named as the repo sees it, not by the bundle-relative path or a bare filename.
    assert ".github/pull_request_template.md" in result.output
    assert existing.read_text() == "mine\n"


def test_unknown_config_name(agent_dir: Path) -> None:
    result = runner.invoke(app, ["install-config", "nope"])
    assert result.exit_code != 0
    assert "workmux" in result.output


def test_not_a_git_repo(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("WFCTL_REPO_ROOT", raising=False)
    monkeypatch.chdir(tmp_path)  # a fresh, non-git directory
    result = runner.invoke(app, ["install-config", "workmux"])
    assert result.exit_code != 0


def test_agent_flag_substituted(bundle: Path, agent_dir: Path) -> None:
    repo_root = agent_dir.parent
    _install(bundle, "--agent", "bob")
    text = (repo_root / ".workmux.yaml").read_text()
    assert "agent: bob" in text
    assert "agent: claude" not in text


def test_agent_defaults_from_manifest(bundle: Path, agent_dir: Path) -> None:
    repo_root = agent_dir.parent
    (repo_root / ".wf-skills-manifest.json").write_text(json.dumps({"bob": {"items": []}}))
    _install(bundle)
    assert "agent: bob" in (repo_root / ".workmux.yaml").read_text()


def test_seeded_config_does_not_invent_an_agent(agent_dir: Path) -> None:
    """A repo that installed no agent layer made no choice to mirror.

    Before the layer split a bare install recorded `claude`, so seeding
    `agent: claude` reflected reality. It no longer does — the default install
    is agent-agnostic — and .workmux.yaml is committed, so asserting an agent
    would put a claim the repo's own install contradicts into every checkout.
    """
    import json
    import os
    from wfctl.cli import _resolve_config_agent

    repo_root = Path(os.environ["WFCTL_REPO_ROOT"])
    manifest = repo_root / ".wf-skills-manifest.json"

    manifest.write_text(json.dumps({"base": {"items": []}}))
    assert _resolve_config_agent(repo_root, None) is None, "bare install must not name an agent"

    manifest.write_text(json.dumps({"base": {}, "claude": {}}))
    assert _resolve_config_agent(repo_root, None) == "claude", "a sole agent is mirrored"

    manifest.write_text(json.dumps({"base": {}, "claude": {}, "copilot": {}}))
    assert _resolve_config_agent(repo_root, None) is None, "several agents — picking one is arbitrary"

    manifest.write_text(json.dumps({"base": {"items": []}}))
    assert _resolve_config_agent(repo_root, "bob") == "bob", "an explicit flag always wins"


def test_legacy_none_manifest_is_not_treated_as_an_agent(bundle: Path, agent_dir: Path) -> None:
    """A pre-split `--agent none` install must not seed `agent: none`.

    Before the layer split, `--agent none` recorded a `none` entry owning
    `.agents/*`. `none` names the absence of an agent, so mirroring it writes a
    pane command literally called `none` into a version-controlled .workmux.yaml.
    """
    repo_root = agent_dir.parent
    (repo_root / ".wf-skills-manifest.json").write_text(
        json.dumps({"none": {"items": [{"path": ".agents/skills/x", "backup": None}]}})
    )
    _install(bundle)
    text = (repo_root / ".workmux.yaml").read_text()
    assert "agent: none" not in text
    assert "# agent: claude" in text, "no agent to mirror — the key stays commented out"


# --- window_prefix substitution (#17) --------------------------------------
#
# The template ships `# window_prefix: "<project>__"` — a literal a human is
# expected to replace, and nobody does at seed time. These assert the seam that
# fills it, plus the guard for when the upstream template moves out from under us.

_TEMPLATE_WITH_PREFIX = (
    '# Per-project tmux session/window name prefix (workmux default: "wm-").\n'
    '# window_prefix: "<project>__"\n'
    "worktree_dir: wt\n"
    "      - command: <agent>\n"
    "agent: claude\n"
)


def test_window_prefix_gets_the_real_project_name_active(bundle: Path, agent_dir: Path) -> None:
    """Active, not commented — a project name is derivable, unlike `agent:`."""
    repo_root = agent_dir.parent
    result = _install(bundle, yaml=_TEMPLATE_WITH_PREFIX)
    assert result.exit_code == 0
    text = (repo_root / ".workmux.yaml").read_text()
    assert f"window_prefix: '{repo_root.name}__'" in text
    assert "# window_prefix:" not in text


def test_no_placeholder_survives_a_normal_seed(bundle: Path, agent_dir: Path) -> None:
    repo_root = agent_dir.parent
    _install(bundle, yaml=_TEMPLATE_WITH_PREFIX)
    assert "<project>" not in (repo_root / ".workmux.yaml").read_text()


def test_workmux_own_agent_token_is_not_flagged(bundle: Path, agent_dir: Path) -> None:
    """`<agent>` is workmux's runtime token, resolved by workmux — not ours to
    substitute, and warning about it would be a false positive on every seed."""
    result = _install(bundle, yaml=_TEMPLATE_WITH_PREFIX)
    assert "<agent>" not in result.output
    assert "still contains" not in result.output


def test_placeholder_warning_when_the_template_renames_the_key(bundle: Path, agent_dir: Path) -> None:
    """The template versions independently. A renamed key defeats a key-presence
    check at exactly the moment the placeholder does ship, so the check watches
    for the survivor instead."""
    repo_root = agent_dir.parent
    renamed = _TEMPLATE_WITH_PREFIX.replace("window_prefix:", "session_prefix:")
    result = _install(bundle, yaml=renamed)
    assert result.exit_code == 0, "a drifted template warns, it does not fail the seed"
    assert "still contains" in result.output
    assert f"window_prefix: '{repo_root.name}__'" in result.output, "remediation is paste-ready"


def test_no_sanitize_notice_when_the_name_is_already_safe(bundle: Path, agent_dir: Path) -> None:
    """The common path stays silent; only a changed name is worth a line."""
    result = _install(bundle, yaml=_TEMPLATE_WITH_PREFIX)
    assert "tmux rewrites" not in result.output


def test_sanitize_notice_when_the_project_name_has_a_dot(bundle: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """tmux silently rewrites `.` and `:`, then cannot be targeted by the original
    name. Sanitizing keeps the written value equal to what tmux will create."""
    import subprocess

    repo_root = tmp_path / "my.project"
    repo_root.mkdir()
    subprocess.run(["git", "init", str(repo_root)], check=True, capture_output=True)
    monkeypatch.setenv("WFCTL_REPO_ROOT", str(repo_root))
    monkeypatch.setenv("WFCTL_STATE_DIR", str(tmp_path / "state"))

    result = _install(bundle, yaml=_TEMPLATE_WITH_PREFIX)
    assert result.exit_code == 0
    assert "tmux rewrites" in result.output
    assert "window_prefix: 'my_project__'" in (repo_root / ".workmux.yaml").read_text()
