"""Tests for `wfctl install-config` — seed standardized repo config."""
from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest
from typer.testing import CliRunner

from wfctl.cli import app

runner = CliRunner()

_WORKMUX_YAML = "worktree_dir: wt\nagent: claude\n"


def _make_wf_skills_repo_with_config(base: Path, yaml: str = _WORKMUX_YAML) -> Path:
    src = base / "wf-skills-cfg"
    src.mkdir()
    subprocess.run(["git", "init", str(src)], check=True, capture_output=True)
    subprocess.run(["git", "-C", str(src), "config", "user.email", "t@t.com"], check=True, capture_output=True)
    subprocess.run(["git", "-C", str(src), "config", "user.name", "T"], check=True, capture_output=True)
    cfg = src / ".agents" / "configs" / "workmux"
    cfg.mkdir(parents=True)
    (cfg / ".workmux.yaml").write_text(yaml)
    subprocess.run(["git", "-C", str(src), "add", "-A"], check=True, capture_output=True)
    subprocess.run(["git", "-C", str(src), "commit", "-m", "init"], check=True, capture_output=True)
    return src


def _install(src: Path, *extra: str):
    return runner.invoke(
        app, ["install-config", "workmux", "--repo", f"file://{src}", "--ref", "master", *extra]
    )


def test_seed_writes_workmux_and_gitignores_wt(agent_dir: Path, tmp_path: Path) -> None:
    repo_root = agent_dir.parent
    result = _install(_make_wf_skills_repo_with_config(tmp_path))
    assert result.exit_code == 0
    assert "worktree_dir: wt" in (repo_root / ".workmux.yaml").read_text()
    assert "wt/" in (repo_root / ".gitignore").read_text().splitlines()  # created (absent before)


def test_gitignore_appended_when_line_missing(agent_dir: Path, tmp_path: Path) -> None:
    repo_root = agent_dir.parent
    (repo_root / ".gitignore").write_text("*.log\n")
    _install(_make_wf_skills_repo_with_config(tmp_path))
    lines = (repo_root / ".gitignore").read_text().splitlines()
    assert "*.log" in lines and "wt/" in lines


def test_gitignore_no_duplicate_when_present(agent_dir: Path, tmp_path: Path) -> None:
    repo_root = agent_dir.parent
    (repo_root / ".gitignore").write_text("wt/\n")
    _install(_make_wf_skills_repo_with_config(tmp_path))
    assert (repo_root / ".gitignore").read_text().splitlines().count("wt/") == 1


def test_refuses_existing_without_force(agent_dir: Path, tmp_path: Path) -> None:
    repo_root = agent_dir.parent
    (repo_root / ".workmux.yaml").write_text("mine: true\n")
    result = _install(_make_wf_skills_repo_with_config(tmp_path))
    assert result.exit_code != 0
    assert ".workmux.yaml" in result.output
    assert (repo_root / ".workmux.yaml").read_text() == "mine: true\n"  # untouched


def test_force_overwrites(agent_dir: Path, tmp_path: Path) -> None:
    repo_root = agent_dir.parent
    (repo_root / ".workmux.yaml").write_text("mine: true\n")
    result = _install(_make_wf_skills_repo_with_config(tmp_path), "--force")
    assert result.exit_code == 0
    assert "worktree_dir: wt" in (repo_root / ".workmux.yaml").read_text()


def test_unknown_config_name(agent_dir: Path) -> None:
    result = runner.invoke(app, ["install-config", "nope"])
    assert result.exit_code != 0
    assert "workmux" in result.output


def test_not_a_git_repo(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("WFCTL_REPO_ROOT", raising=False)
    monkeypatch.chdir(tmp_path)  # a fresh, non-git directory
    result = runner.invoke(app, ["install-config", "workmux"])
    assert result.exit_code != 0


def test_agent_flag_substituted(agent_dir: Path, tmp_path: Path) -> None:
    repo_root = agent_dir.parent
    _install(_make_wf_skills_repo_with_config(tmp_path), "--agent", "bob")
    text = (repo_root / ".workmux.yaml").read_text()
    assert "agent: bob" in text
    assert "agent: claude" not in text


def test_agent_defaults_from_manifest(agent_dir: Path, tmp_path: Path) -> None:
    repo_root = agent_dir.parent
    (repo_root / ".wf-skills-manifest.json").write_text(json.dumps({"bob": {"items": []}}))
    _install(_make_wf_skills_repo_with_config(tmp_path))
    assert "agent: bob" in (repo_root / ".workmux.yaml").read_text()


def test_seeded_config_does_not_invent_an_agent(agent_dir: Path, tmp_path: Path) -> None:
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


def test_legacy_none_manifest_is_not_treated_as_an_agent(agent_dir: Path, tmp_path: Path) -> None:
    """A pre-split `--agent none` install must not seed `agent: none`.

    Before the layer split, `--agent none` recorded a `none` entry owning
    `.agents/*`. `none` names the absence of an agent, so mirroring it writes a
    pane command literally called `none` into a version-controlled .workmux.yaml.
    """
    repo_root = agent_dir.parent
    (repo_root / ".wf-skills-manifest.json").write_text(
        json.dumps({"none": {"items": [{"path": ".agents/skills/x", "backup": None}]}})
    )
    _install(_make_wf_skills_repo_with_config(tmp_path))
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


def test_window_prefix_gets_the_real_project_name_active(
    agent_dir: Path, tmp_path: Path
) -> None:
    """Active, not commented — a project name is derivable, unlike `agent:`."""
    repo_root = agent_dir.parent
    src = _make_wf_skills_repo_with_config(tmp_path, _TEMPLATE_WITH_PREFIX)
    result = _install(src)
    assert result.exit_code == 0
    text = (repo_root / ".workmux.yaml").read_text()
    assert f"window_prefix: '{repo_root.name}__'" in text
    assert "# window_prefix:" not in text


def test_no_placeholder_survives_a_normal_seed(agent_dir: Path, tmp_path: Path) -> None:
    repo_root = agent_dir.parent
    _install(_make_wf_skills_repo_with_config(tmp_path, _TEMPLATE_WITH_PREFIX))
    assert "<project>" not in (repo_root / ".workmux.yaml").read_text()


def test_workmux_own_agent_token_is_not_flagged(agent_dir: Path, tmp_path: Path) -> None:
    """`<agent>` is workmux's runtime token, resolved by workmux — not ours to
    substitute, and warning about it would be a false positive on every seed."""
    result = _install(_make_wf_skills_repo_with_config(tmp_path, _TEMPLATE_WITH_PREFIX))
    assert "<agent>" not in result.output
    assert "still contains" not in result.output


def test_placeholder_warning_when_the_template_renames_the_key(
    agent_dir: Path, tmp_path: Path
) -> None:
    """The template versions independently. A renamed key defeats a key-presence
    check at exactly the moment the placeholder does ship, so the check watches
    for the survivor instead."""
    repo_root = agent_dir.parent
    renamed = _TEMPLATE_WITH_PREFIX.replace("window_prefix:", "session_prefix:")
    result = _install(_make_wf_skills_repo_with_config(tmp_path, renamed))
    assert result.exit_code == 0, "a drifted template warns, it does not fail the seed"
    assert "still contains" in result.output
    assert f"window_prefix: '{repo_root.name}__'" in result.output, "remediation is paste-ready"


def test_no_sanitize_notice_when_the_name_is_already_safe(
    agent_dir: Path, tmp_path: Path
) -> None:
    """The common path stays silent; only a changed name is worth a line."""
    result = _install(_make_wf_skills_repo_with_config(tmp_path, _TEMPLATE_WITH_PREFIX))
    assert "tmux rewrites" not in result.output


def test_sanitize_notice_when_the_project_name_has_a_dot(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """tmux silently rewrites `.` and `:`, then cannot be targeted by the original
    name. Sanitizing keeps the written value equal to what tmux will create."""
    import subprocess

    repo_root = tmp_path / "my.project"
    repo_root.mkdir()
    subprocess.run(["git", "init", str(repo_root)], check=True, capture_output=True)
    monkeypatch.setenv("WFCTL_REPO_ROOT", str(repo_root))
    monkeypatch.setenv("WFCTL_STATE_DIR", str(tmp_path / "state"))

    src = _make_wf_skills_repo_with_config(tmp_path, _TEMPLATE_WITH_PREFIX)
    result = _install(src)
    assert result.exit_code == 0
    assert "tmux rewrites" in result.output
    assert "window_prefix: 'my_project__'" in (repo_root / ".workmux.yaml").read_text()
