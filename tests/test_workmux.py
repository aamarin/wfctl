"""Tests for `wfctl._workmux` — pure text transforms for `.workmux.yaml`.

No fixtures, no git repo, no clone. That is the payoff for injecting the project
name and agent rather than resolving them inside the module: asserting a
substitution is a function call, where it previously took two git repos and a
`file://` clone (see the older cases in test_install_config.py).
"""
from __future__ import annotations

from wfctl import _workmux

# Trimmed from the real wf-skills template, keeping the lines that matter:
# the commented placeholder, workmux's own `<agent>` token, and the disabled hook.
TEMPLATE = """\
worktree_dir: wt

# Per-project tmux session/window name prefix (workmux default: "wm-").
# window_prefix: "<project>__"

mode: session

windows:
  - name: agent
    panes:
      - command: <agent>

agent: claude

pre_remove: []
"""


# --- tmux_safe -------------------------------------------------------------

def test_tmux_safe_rewrites_only_what_tmux_rewrites() -> None:
    """Measured against a live tmux server: `.` and `:` are silently rewritten
    to `_`, after which the original name can't be targeted. Nothing else is."""
    assert _workmux.tmux_safe("my.proj") == "my_proj"
    assert _workmux.tmux_safe("a:b.c") == "a_b_c"
    assert _workmux.tmux_safe("wfctl") == "wfctl"


def test_tmux_safe_leaves_legal_characters_alone() -> None:
    """Widening the set would mangle legitimate directory names."""
    for name in ("my proj", "my-proj", "my_proj", "proj$x"):
        assert _workmux.tmux_safe(name) == name


# --- patch_seed ------------------------------------------------------------

def test_window_prefix_is_written_active() -> None:
    """Uncommented, unlike `agent:`. A project name is derivable; every real
    consumer hand-edited to exactly this value."""
    out = _workmux.patch_seed(TEMPLATE, agent=None, project="proj")
    assert "window_prefix: 'proj__'\n" in out
    assert "# window_prefix:" not in out
    assert "<project>" not in out


def test_window_prefix_comment_above_it_survives() -> None:
    """Only the key line is rewritten — the explanatory comment stays."""
    out = _workmux.patch_seed(TEMPLATE, agent=None, project="proj")
    assert 'workmux default: "wm-"' in out


def test_project_name_with_apostrophe_is_escaped() -> None:
    """Directory names may contain `'`; YAML escapes it by doubling. Without
    this the seeded file is malformed."""
    out = _workmux.patch_seed(TEMPLATE, agent=None, project="it's")
    assert "window_prefix: 'it''s__'\n" in out


def test_resolved_agent_is_substituted() -> None:
    out = _workmux.patch_seed(TEMPLATE, agent="bob", project="p")
    assert "agent: bob\n" in out
    assert "agent: claude" not in out


def test_no_agent_leaves_the_key_commented() -> None:
    """A repo that installed no agent layer made no choice to mirror. Relocated
    from test_install_config.py, where it needed a git repo and a clone."""
    out = _workmux.patch_seed(TEMPLATE, agent=None, project="p")
    assert "# agent: claude" in out
    assert "\nagent: claude" not in out


def test_workmux_own_agent_token_is_untouched() -> None:
    """`<agent>` in a pane command is workmux's runtime token, not ours."""
    out = _workmux.patch_seed(TEMPLATE, agent="bob", project="p")
    assert "command: <agent>" in out


def test_absent_keys_are_left_alone_not_appended() -> None:
    """Seeding must not invent keys in a file it is about to hand to the repo."""
    out = _workmux.patch_seed("worktree_dir: wt\n", agent="bob", project="p")
    assert out == "worktree_dir: wt\n"


# --- unsubstituted_placeholder ---------------------------------------------

def test_placeholder_check_watches_the_symptom() -> None:
    """A renamed key upstream defeats a key-presence check exactly when the
    placeholder does ship, so the check looks for the survivor instead."""
    renamed = TEMPLATE.replace("window_prefix:", "session_prefix:")
    out = _workmux.patch_seed(renamed, agent=None, project="p")
    assert _workmux.unsubstituted_placeholder(out)


def test_placeholder_check_clean_after_a_normal_patch() -> None:
    out = _workmux.patch_seed(TEMPLATE, agent=None, project="p")
    assert not _workmux.unsubstituted_placeholder(out)


def test_placeholder_check_does_not_flag_workmux_agent_token() -> None:
    """`<agent>` is not ours to substitute; flagging it is a false positive."""
    assert not _workmux.unsubstituted_placeholder("      - command: <agent>\n")


# --- pre_remove_wired ------------------------------------------------------

def test_wired_when_a_real_line_invokes_archive_story() -> None:
    assert _workmux.pre_remove_wired(
        'pre_remove:\n  - command -v wfctl && wfctl archive-story "$X" || true\n'
    )


def test_empty_list_is_not_wired() -> None:
    """`pre_remove: []` is an explicit opt-out, not an absent default."""
    assert not _workmux.pre_remove_wired(TEMPLATE)


def test_archive_story_elsewhere_in_the_file_is_not_wired() -> None:
    """The scan is scoped to the `pre_remove:` block.

    A whole-file scan reported wired whenever `archive-story` appeared anywhere
    non-comment — a pane command here — while `pre_remove: []` left teardown
    unprotected. A safety check that fails open is worse than no check.
    """
    assert not _workmux.pre_remove_wired(
        "windows:\n"
        "  - name: term\n"
        "    panes:\n"
        "      - command: wfctl archive-story --help\n"
        "pre_remove: []\n"
    )


def test_wired_hook_is_found_when_other_keys_follow() -> None:
    """Block detection must not stop at the key line or run past its end."""
    assert _workmux.pre_remove_wired(
        "pre_remove:\n"
        "  - command -v wfctl && wfctl archive-story \"$X\" || true\n"
        "\n"
        "files: {}\n"
    )


def test_commented_hook_inside_the_block_is_not_wired() -> None:
    assert not _workmux.pre_remove_wired(
        "pre_remove:\n  # - wfctl archive-story \"$X\"\n"
    )


def test_comment_only_mention_is_not_wired() -> None:
    """A repo documenting archiving — or explaining why it skips it — is not
    wired, and treating it as wired would silence a real warning."""
    assert not _workmux.pre_remove_wired(
        "# we deliberately skip wfctl archive-story here\npre_remove: []\n"
    )


# --- wire_pre_remove -------------------------------------------------------

def test_wiring_replaces_the_placeholder_with_the_hook() -> None:
    """Derived from WIRED_PRE_REMOVE rather than hardcoding a line count, so the
    hook's shape can change — as it did when it became a block scalar — without
    this asserting the old one."""
    out = _workmux.wire_pre_remove(TEMPLATE)
    assert out is not None
    assert _workmux.pre_remove_wired(out)
    assert "pre_remove: []" not in out
    grew = len(_workmux.WIRED_PRE_REMOVE.rstrip("\n").splitlines()) - 1
    assert len(out.splitlines()) == len(TEMPLATE.splitlines()) + grew


def test_wiring_changes_nothing_else() -> None:
    """The retrofit writes into a file the repo owns and has customized."""
    out = _workmux.wire_pre_remove(TEMPLATE)
    assert out is not None
    before = [ln for ln in TEMPLATE.splitlines() if ln != "pre_remove: []"]
    injected = set(_workmux.WIRED_PRE_REMOVE.splitlines())
    after = [ln for ln in out.splitlines() if ln not in injected]
    assert before == after


def test_refuses_a_customized_pre_remove() -> None:
    """Ordering and intent of existing hooks are unknowable — don't guess."""
    assert _workmux.wire_pre_remove("pre_remove:\n  - echo hi\n") is None


def test_refuses_when_the_key_is_absent() -> None:
    """Appending a top-level key to an EOF we never parsed mangles files."""
    assert _workmux.wire_pre_remove("worktree_dir: wt\n") is None


# --- the rename: both names count as wired, only the old one is reported ------


def test_pre_remove_wired_accepts_the_current_name() -> None:
    """The hook `install-config` seeds now names `archive-specs`. A check keyed on
    the old name would report every freshly seeded repo as unprotected."""
    assert _workmux.pre_remove_wired(_workmux.WIRED_PRE_REMOVE)


def test_pre_remove_wired_still_accepts_the_former_name() -> None:
    """A repo wired before the rename IS wired — the alias keeps working. Reporting
    it as unwired would offer to add a second hook beside the one already there."""
    assert _workmux.pre_remove_wired(
        'pre_remove:\n  - command -v wfctl && wfctl archive-story "$X" || true\n'
    )
