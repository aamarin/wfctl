"""Tests for `wfctl.arch._views` and the `Views` block `wfctl arch context` prints:
which views a repository needs, which a branch is shown, and whether each
present view still matches the code it covers."""
from __future__ import annotations

import re
import subprocess
from pathlib import Path

import pytest
from typer.testing import CliRunner

from tests.conftest import git_repo
from wfctl.arch import _contexts, _views
from wfctl.cli import app

runner = CliRunner()

_TEMPLATES = Path(__file__).parent.parent / "wfctl" / "agents" / "skills" / "architecture-design" / "views"


def _page(arch: Path, stem: str, *header: str, state: str = "accepted") -> None:
    domain = arch / "domain"
    domain.mkdir(parents=True, exist_ok=True)
    lines = [f"# {stem}", "", f"State: {state}", *header, "", "## Body", "", "text"]
    (domain / f"{stem}.md").write_text("\n".join(lines) + "\n")


def _paths(views: tuple[_views.RequiredView, ...]) -> list[str]:
    return [str(view.path) for view in views]


# --- contexts ----------------------------------------------------------------


def test_contexts_is_none_without_an_accepted_domain_page(tmp_path: Path) -> None:
    """None means the repository never named its contexts, so it needs no
    component view. A draft page's names would otherwise start asking for views
    nobody agreed to."""
    assert _contexts.contexts(tmp_path) is None
    _page(tmp_path, "wfctl", "Contexts: a", state="proposed")
    assert _contexts.contexts(tmp_path) is None


def test_contexts_is_none_when_the_page_lists_only_outside_parties(tmp_path: Path) -> None:
    _page(tmp_path, "wfctl", "Outside parties: github")

    assert _contexts.contexts(tmp_path) is None


def test_contexts_keeps_the_lines_order_and_drops_repeats(tmp_path: Path) -> None:
    """Component views print in this order, so a set, like the one `names`
    returns, would reorder the `Views` block from one run to the next."""
    _page(tmp_path, "wfctl", "Contexts: zeta, alpha, zeta, mid")

    assert _contexts.contexts(tmp_path) == ("zeta", "alpha", "mid")


def test_contexts_joins_two_pages_in_file_name_order(tmp_path: Path) -> None:
    _page(tmp_path, "b-page", "Contexts: two, shared")
    _page(tmp_path, "a-page", "Contexts: one, shared")

    assert _contexts.contexts(tmp_path) == ("one", "shared", "two")


def test_contexts_leaves_out_outside_parties(tmp_path: Path) -> None:
    """An outside party, such as GitHub, isn't part of the system, so it gets no
    component view. `names` joins both lines because a record can govern
    either, which is why this is a second function."""
    _page(tmp_path, "wfctl", "Contexts: a, b", "Outside parties: github, git")

    assert _contexts.contexts(tmp_path) == ("a", "b")


def test_contexts_leaves_out_a_malformed_name(tmp_path: Path) -> None:
    """Each name becomes a file under `views/components/`, so `../x` would point
    outside it. `malformed` already reports the name to `doctor`."""
    _page(tmp_path, "wfctl", "Contexts: a, ../x, b")

    assert _contexts.contexts(tmp_path) == ("a", "b")


# --- required views ------------------------------------------------------------


def test_required_views_for_three_contexts(tmp_path: Path) -> None:
    _page(tmp_path, "wfctl", "Contexts: records, design-method, attention")

    assert _paths(_views.required_views(tmp_path)) == [
        "views/system-context.md",
        "views/container.md",
        "views/components/records.md",
        "views/components/design-method.md",
        "views/components/attention.md",
    ]


def test_an_empty_contexts_line_requires_no_component_view(tmp_path: Path) -> None:
    _page(tmp_path, "wfctl", "Contexts: ")

    assert _paths(_views.required_views(tmp_path)) == [
        "views/system-context.md",
        "views/container.md",
    ]


def test_a_repository_with_no_architecture_folder_still_needs_two_views(tmp_path: Path) -> None:
    """Every repository has a system and its parts, whether or not anyone has
    written a record yet (data-model rule 1)."""
    views = _views.required_views(tmp_path / "docs" / "architecture")

    assert _paths(views) == ["views/system-context.md", "views/container.md"]
    assert not any(view.present for view in views)


def test_required_views_read_presence_and_covers_from_disk(tmp_path: Path) -> None:
    (tmp_path / "views").mkdir()
    (tmp_path / "views" / "container.md").write_text(
        "---\ncovers: [wfctl/, tests/]\n---\n\n# Container view\n"
    )

    system, container = _views.required_views(tmp_path)

    assert (system.present, system.covers) == (False, ())
    assert (container.present, container.covers) == (True, ("wfctl/", "tests/"))


def test_current_state_and_other_files_under_views_are_never_required(tmp_path: Path) -> None:
    (tmp_path / "views").mkdir()
    (tmp_path / "views" / "current-state.md").write_text("# Module layers\n")

    assert "views/current-state.md" not in _paths(_views.required_views(tmp_path))


# --- the templates match the list (FR-004) -------------------------------------


def test_every_required_view_kind_ships_a_template() -> None:
    """The list and the templates are two copies of one fact. A template
    renamed or a kind added without one would leave an agent told to draw a
    view with nothing to draw it from."""
    shipped = sorted(path.stem for path in _TEMPLATES.glob("*.md"))

    assert shipped == sorted(_views.VIEW_KINDS)


def test_each_template_carries_a_covers_line_in_bracket_form() -> None:
    """Without a `covers` line a drawn view prints as unchecked forever, so the
    template is where the line has to start (FR-003c)."""
    for path in _TEMPLATES.glob("*.md"):
        text = path.read_text()
        assert re.search(r"^covers: \[.*\]$", text, re.MULTILINE), path.name


def test_the_container_and_component_templates_ask_for_labeled_arrows() -> None:
    """A label naming the import or call is what lets the user check an arrow
    against the code without trusting the agent's coloring (FR-003b, R-011)."""
    for name in ("container.md", "component.md"):
        text = (_TEMPLATES / name).read_text()
        assert '-->|"imports' in text, name
        assert "label" in text.lower(), name


def test_the_container_and_component_templates_state_the_layout_rule_in_words() -> None:
    """A citation alone gives the agent nothing to follow (FR-003a). The rule
    has four parts, and each one is checked by a phrase the template has to
    carry."""
    for name in ("container.md", "component.md"):
        text = " ".join((_TEMPLATES / name).read_text().split()).lower()
        assert "rarely change" in text, name
        assert "change often" in text, name
        assert "toward the stable" in text, name
        assert "red" in text, name
        assert "the code has" in text, name


# --- the branch filter (R-003) -------------------------------------------------


def _set(arch: Path, contexts: str, present: tuple[str, ...] = ()) -> tuple[_views.RequiredView, ...]:
    """The required views for a page listing `contexts`, with the views named in
    `present` written to disk."""
    _page(arch, "wfctl", f"Contexts: {contexts}", "Outside parties: github")
    for name in present:
        file = arch / name
        file.parent.mkdir(parents=True, exist_ok=True)
        file.write_text("---\ncovers: [x/]\n---\n\n# A view\n")
    return _views.required_views(arch)


def _shown(arch: Path, listed: tuple[str, ...] | None, every: bool = False) -> list[str]:
    views = _views.required_views(arch)
    return _paths(_views.for_branch(views, _contexts.contexts(arch), listed, every))


def test_a_branch_listing_known_contexts_sees_only_their_component_views(tmp_path: Path) -> None:
    """The same narrowing the records get, so a session start doesn't show the
    records for one set of contexts and the views for another."""
    _set(tmp_path, "a, b, c")

    assert _shown(tmp_path, ("c", "a")) == [
        "views/system-context.md",
        "views/container.md",
        "views/components/a.md",
        "views/components/c.md",
    ]


def test_a_branch_with_no_list_or_an_empty_one_sees_every_component_view(tmp_path: Path) -> None:
    """No list is also what a branch with no spec folder reads as, so this
    covers that row of the table too."""
    _set(tmp_path, "a, b")
    every = [
        "views/system-context.md",
        "views/container.md",
        "views/components/a.md",
        "views/components/b.md",
    ]

    assert _shown(tmp_path, None) == every
    assert _shown(tmp_path, ()) == every


def test_a_branch_listing_an_unknown_name_sees_every_component_view(tmp_path: Path) -> None:
    """A misspelled name, or an outside party that has no component view, can't
    be narrowed to anything. Leaving out a view that applies is worse than
    showing one that doesn't."""
    _set(tmp_path, "a, b")

    assert len(_shown(tmp_path, ("a", "typo"))) == 4
    assert len(_shown(tmp_path, ("github",))) == 4


def test_all_shows_every_component_view_whatever_the_branch_lists(tmp_path: Path) -> None:
    _set(tmp_path, "a, b")

    assert len(_shown(tmp_path, ("a",), every=True)) == 4


def test_present_views_come_before_missing_ones(tmp_path: Path) -> None:
    """Contract rule 1. The paths an agent can open come first, and the
    reminders after them."""
    _set(tmp_path, "a, b", present=("views/container.md", "views/components/b.md"))

    assert _shown(tmp_path, None) == [
        "views/container.md",
        "views/components/b.md",
        "views/system-context.md",
        "views/components/a.md",
    ]


# --- the Views block (contracts/cli.md) ------------------------------------------


def _git(repo: Path, *args: str) -> None:
    subprocess.run(["git", "-C", str(repo), *args], check=True, capture_output=True)


def _commit(repo: Path, message: str) -> None:
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "-m", message)


def _write_view(arch: Path, name: str, covers: str | None = "README.md") -> Path:
    file = arch / "views" / name
    file.parent.mkdir(parents=True, exist_ok=True)
    front = f"---\ncovers: [{covers}]\n---\n\n" if covers is not None else ""
    file.write_text(f"{front}# A view\n")
    return file


def _cli_repo(agent_dir: Path, monkeypatch: pytest.MonkeyPatch) -> tuple[Path, Path]:
    """The repository `agent_dir` sits in, and its arch root, pointed at by
    `WFCTL_ARCH_DIR` so the test builds the record set by writing files."""
    repo = agent_dir.parent
    arch = repo / "docs" / "architecture"
    monkeypatch.setenv("WFCTL_ARCH_DIR", str(arch))
    return repo, arch


def _design(agent_dir: Path, monkeypatch: pytest.MonkeyPatch, contexts: str) -> None:
    specs = agent_dir.parent / "specs"
    folder = specs / "342-state-workflow"
    folder.mkdir(parents=True, exist_ok=True)
    (folder / "design.md").write_text(f"# t\n\nContexts: {contexts}\n\n## Problem\n")
    monkeypatch.setenv("WFCTL_SPEC_DIR", str(specs))


def _block(output: str) -> str:
    """Everything from the `Views` line on. Contract: the block is last."""
    return output[output.index("\nViews\n") + 1:]


def test_the_views_block_names_present_and_missing_views_for_the_branch(
    agent_dir: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repo, arch = _cli_repo(agent_dir, monkeypatch)
    _page(arch, "wfctl", "Contexts: records, design-method, attention")
    _write_view(arch, "system-context.md")
    _write_view(arch, "container.md")
    _commit(repo, "views")
    _design(agent_dir, monkeypatch, "records, design-method")

    result = runner.invoke(app, ["arch", "context"])

    assert result.exit_code == 0
    assert _block(result.output) == (
        "Views\n"
        "  docs/architecture/views/system-context.md\n"
        "  docs/architecture/views/container.md\n"
        "  missing: docs/architecture/views/components/records.md\n"
        "  missing: docs/architecture/views/components/design-method.md\n"
    )


def test_all_prints_every_component_view(
    agent_dir: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """`--all` already prints every record whatever the branch lists, and the
    views follow it (contract rule 2)."""
    _, arch = _cli_repo(agent_dir, monkeypatch)
    _page(arch, "wfctl", "Contexts: records, attention")
    _design(agent_dir, monkeypatch, "records")

    out = runner.invoke(app, ["arch", "context", "--all"]).output

    assert "  missing: docs/architecture/views/components/attention.md\n" in _block(out)


def test_a_repository_with_no_architecture_folder_is_told_both_views_are_missing(
    agent_dir: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Every view missing still exits 0, since a missing view is a reminder and
    never a refusal (contract rule 3, FR-007)."""
    _cli_repo(agent_dir, monkeypatch)

    result = runner.invoke(app, ["arch", "context"])

    assert result.exit_code == 0
    assert _block(result.output) == (
        "Views\n"
        "  missing: docs/architecture/views/system-context.md\n"
        "  missing: docs/architecture/views/container.md\n"
    )


def test_the_views_block_comes_after_every_line_about_records(
    agent_dir: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The records bind the work, so they stay directly under the header that
    counts them, and the views follow (R-009)."""
    _, arch = _cli_repo(agent_dir, monkeypatch)
    arch.mkdir(parents=True)
    (arch / "old.md").write_text("---\nstatus: rejected\n---\n\n# old\n")

    out = runner.invoke(app, ["arch", "context"]).output

    assert out.index("record not shown") < out.index("\nViews\n")


# --- freshness (R-010) ---------------------------------------------------------


def _fresh(repo: Path, arch: Path, name: str) -> _views.Freshness:
    view = next(v for v in _views.required_views(arch) if v.path.name == name)
    return _views.freshness(view, arch, repo)


def _repo(tmp_path: Path) -> tuple[Path, Path]:
    repo = git_repo(tmp_path / "repo")
    (repo / "wfctl").mkdir()
    (repo / "wfctl" / "a.py").write_text("x = 1\n")
    _commit(repo, "code")
    return repo, repo / "docs" / "architecture"


def test_a_commit_to_covered_code_marks_the_view_stale_until_the_view_is_committed(
    tmp_path: Path,
) -> None:
    """The case the mark exists for. A real repository rather than a mocked
    `git`, since a mock passes whatever range the code builds and can't catch
    an off-by-one in which commits count (plan Note 7)."""
    repo, arch = _repo(tmp_path)
    _write_view(arch, "container.md", covers="wfctl/, README.md")
    _commit(repo, "draw the view")
    assert _fresh(repo, arch, "container.md") == _views.Freshness("current", "")

    (repo / "wfctl" / "a.py").write_text("x = 2\n")
    _commit(repo, "change the code")
    (repo / "README.md").write_text("y\n")
    _commit(repo, "change the readme")
    assert _fresh(repo, arch, "container.md") == _views.Freshness(
        "stale", "2 commits to wfctl/, README.md since the view changed"
    )

    (arch / "views" / "container.md").write_text(
        "---\ncovers: [wfctl/, README.md]\n---\n\n# Redrawn\n"
    )
    _commit(repo, "redraw the view")
    assert _fresh(repo, arch, "container.md").state == "current"


def test_one_commit_reads_in_the_singular(tmp_path: Path) -> None:
    repo, arch = _repo(tmp_path)
    _write_view(arch, "container.md", covers="wfctl/")
    _commit(repo, "draw the view")
    (repo / "wfctl" / "a.py").write_text("x = 2\n")
    _commit(repo, "change the code")

    assert _fresh(repo, arch, "container.md").detail == "1 commit to wfctl/ since the view changed"


def test_uncommitted_edits_change_nothing(tmp_path: Path) -> None:
    """Freshness reads commits only (data-model rule 4), so a half-finished edit
    to the code or the view can't flip the mark back and forth."""
    repo, arch = _repo(tmp_path)
    _write_view(arch, "container.md", covers="wfctl/")
    _commit(repo, "draw the view")

    (repo / "wfctl" / "a.py").write_text("x = 3\n")
    assert _fresh(repo, arch, "container.md").state == "current"

    _commit(repo, "change the code")
    (arch / "views" / "container.md").write_text("---\ncovers: [wfctl/]\n---\n\n# Edited\n")
    assert _fresh(repo, arch, "container.md").state == "stale"


def test_an_uncommitted_covers_edit_cannot_clear_a_stale_mark(tmp_path: Path) -> None:
    """The `covers` line was read from the working tree while the count ran
    from the view's last commit, so narrowing `covers` to code with no newer
    commits made a stale view read current before the redraw was committed."""
    repo, arch = _repo(tmp_path)
    (repo / "docs.md").write_text("d\n")
    _write_view(arch, "container.md", covers="wfctl/")
    _commit(repo, "draw the view")
    (repo / "wfctl" / "a.py").write_text("x = 2\n")
    _commit(repo, "change the code")

    _write_view(arch, "container.md", covers="docs.md")
    assert _fresh(repo, arch, "container.md") == _views.Freshness(
        "stale", "1 commit to wfctl/ since the view changed"
    )

    _commit(repo, "redraw the view")
    assert _fresh(repo, arch, "container.md").state == "current"


def test_a_covered_file_deleted_in_a_commit_marks_the_view_stale(tmp_path: Path) -> None:
    """The deletion is a commit to the covered path, so the view needs
    redrawing. Checking the path against the working tree read it as gone and
    printed unchecked instead."""
    repo, arch = _repo(tmp_path)
    (repo / "wfctl" / "b.py").write_text("y = 1\n")
    _write_view(arch, "container.md", covers="wfctl/a.py, wfctl/b.py")
    _commit(repo, "draw the view")
    _git(repo, "rm", "-q", "wfctl/b.py")
    _commit(repo, "drop b")

    assert _fresh(repo, arch, "container.md") == _views.Freshness(
        "stale", "1 commit to wfctl/a.py, wfctl/b.py since the view changed"
    )


def test_a_covered_file_added_after_the_view_marks_it_stale(tmp_path: Path) -> None:
    """Checking the path against the view's commit alone read a file added
    later as untracked, when the commit that added it is newer code the view
    covers. A branch that commits its docs before its code hits this."""
    repo, arch = _repo(tmp_path)
    _write_view(arch, "container.md", covers="wfctl/a.py, wfctl/b.py")
    _commit(repo, "draw the view")
    (repo / "wfctl" / "b.py").write_text("y = 1\n")
    _commit(repo, "add b")

    assert _fresh(repo, arch, "container.md") == _views.Freshness(
        "stale", "1 commit to wfctl/a.py, wfctl/b.py since the view changed"
    )


def test_a_covered_file_added_and_deleted_after_the_view_marks_it_stale(
    tmp_path: Path,
) -> None:
    """A file added and removed again since the view is in neither the view's
    commit nor HEAD, and reading only those two called it missing when two
    commits to it are newer than the view."""
    repo, arch = _repo(tmp_path)
    _write_view(arch, "container.md", covers="wfctl/a.py, wfctl/b.py")
    _commit(repo, "draw the view")
    (repo / "wfctl" / "b.py").write_text("y = 1\n")
    _commit(repo, "add b")
    (repo / "wfctl" / "b.py").unlink()
    _commit(repo, "drop b")

    assert _fresh(repo, arch, "container.md") == _views.Freshness(
        "stale", "2 commits to wfctl/a.py, wfctl/b.py since the view changed"
    )


def test_a_tracked_symlink_pointing_outside_the_repository_is_counted(
    tmp_path: Path, tmp_path_factory: pytest.TempPathFactory
) -> None:
    """Following the link to decide whether a path is outside the repository
    called a link git tracks untracked, and let its target on disk decide a
    committed view."""
    repo, arch = _repo(tmp_path)
    first = tmp_path_factory.mktemp("first")
    (repo / "ext").symlink_to(first)
    _write_view(arch, "container.md", covers="wfctl/, ext")
    _commit(repo, "draw the view")

    assert _fresh(repo, arch, "container.md") == _views.Freshness("current", "")

    (repo / "ext").unlink()
    (repo / "ext").symlink_to(tmp_path_factory.mktemp("second"))
    _commit(repo, "repoint ext")

    assert _fresh(repo, arch, "container.md") == _views.Freshness(
        "stale", "1 commit to wfctl/, ext since the view changed"
    )


def test_a_tracked_symlink_whose_target_is_gone_reads_the_same_drawn_and_committed(
    tmp_path: Path,
) -> None:
    """The view being drawn followed the link to check it exists, so a dangling
    link git tracks read as missing until the view was committed, and current
    after."""
    repo, arch = _repo(tmp_path)
    (repo / "dang").symlink_to(tmp_path / "gone")
    _commit(repo, "add a dangling link")
    _write_view(arch, "container.md", covers="wfctl/, dang")

    assert _fresh(repo, arch, "container.md") == _views.Freshness("current", "")

    _commit(repo, "draw the view")

    assert _fresh(repo, arch, "container.md") == _views.Freshness("current", "")


def _merge_side_branch(repo: Path, *edits: tuple[str, str | None]) -> None:
    """Commit each edit on a side branch, then merge it the way this repository
    merges, with a merge commit. An edit is a path and its new text, or None to
    delete it."""
    _git(repo, "switch", "-q", "-c", "side")
    for path, text in edits:
        if text is None:
            (repo / path).unlink()
        else:
            (repo / path).write_text(text)
        _commit(repo, f"edit {path}")
    _git(repo, "switch", "-q", "-")
    _git(repo, "merge", "-q", "--no-ff", "side", "-m", "merge side")


def test_a_covered_file_added_and_deleted_on_a_merged_branch_marks_it_stale(
    tmp_path: Path,
) -> None:
    """git's default history leaves out a merged branch with no net change to a
    path, so the same two commits read stale on the trunk and unchecked when
    merged."""
    repo, arch = _repo(tmp_path)
    _write_view(arch, "container.md", covers="wfctl/a.py, wfctl/b.py")
    _commit(repo, "draw the view")
    _merge_side_branch(repo, ("wfctl/b.py", "y = 1\n"), ("wfctl/b.py", None))

    assert _fresh(repo, arch, "container.md") == _views.Freshness(
        "stale", "2 commits to wfctl/a.py, wfctl/b.py since the view changed"
    )


def test_a_covered_file_changed_and_changed_back_on_a_merged_branch_marks_it_stale(
    tmp_path: Path,
) -> None:
    """The file exists at both ends, so only the count decides, and the default
    history read it current."""
    repo, arch = _repo(tmp_path)
    _write_view(arch, "container.md", covers="wfctl/a.py")
    _commit(repo, "draw the view")
    _merge_side_branch(repo, ("wfctl/a.py", "x = 2\n"), ("wfctl/a.py", "x = 1\n"))

    assert _fresh(repo, arch, "container.md") == _views.Freshness(
        "stale", "2 commits to wfctl/a.py since the view changed"
    )


def test_a_change_merged_with_a_merge_commit_counts_once(tmp_path: Path) -> None:
    """`--full-history` alone also counts the merge commit that brings a change
    in, so every change merged the way this repository merges would count
    twice."""
    repo, arch = _repo(tmp_path)
    _write_view(arch, "container.md", covers="wfctl/a.py")
    _commit(repo, "draw the view")
    _merge_side_branch(repo, ("wfctl/a.py", "x = 2\n"))

    assert _fresh(repo, arch, "container.md") == _views.Freshness(
        "stale", "1 commit to wfctl/a.py since the view changed"
    )


def test_a_view_kept_over_a_discarded_redraw_is_measured_from_the_kept_commit(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The view's last commit uses default history while the counts use full
    history. Full history with `--no-merges` would find the side branch's
    redraw, which is newer but which the merge threw away, and count the
    trunk's code change that the kept redraw already covers."""
    repo, arch = _repo(tmp_path)
    view = _write_view(arch, "container.md", covers="wfctl/a.py")
    _commit(repo, "draw the view")
    _git(repo, "branch", "side")
    (repo / "wfctl" / "a.py").write_text("x = 2\n")
    _commit(repo, "change the code")
    view.write_text(view.read_text() + "\nRedrawn on the trunk.\n")
    _commit(repo, "redraw the view")
    _git(repo, "switch", "-q", "side")
    view.write_text(view.read_text() + "\nRedrawn on the side branch.\n")
    monkeypatch.setenv("GIT_COMMITTER_DATE", "2099-01-01T00:00:00")
    _commit(repo, "redraw the view later")
    monkeypatch.delenv("GIT_COMMITTER_DATE")
    _git(repo, "switch", "-q", "-")
    _git(repo, "merge", "-q", "-s", "ours", "side", "-m", "merge side")

    assert _fresh(repo, arch, "container.md") == _views.Freshness("current", "")


def test_an_untracked_dangling_symlink_on_covers_reads_untracked(tmp_path: Path) -> None:
    """The reason's wording followed the link, so a link git hasn't been told
    about read as a path that doesn't exist."""
    repo, arch = _repo(tmp_path)
    (repo / "dang").symlink_to(tmp_path / "gone")
    _write_view(arch, "container.md", covers="wfctl/, dang")

    assert _fresh(repo, arch, "container.md") == _views.Freshness(
        "unchecked", "covers names dang, which git doesn't track"
    )


def test_a_covers_path_outside_the_repository_reads_untracked_while_the_view_is_drawn(
    tmp_path: Path, tmp_path_factory: pytest.TempPathFactory
) -> None:
    """git refuses a path outside the repository with an error, and the view
    being drawn read that as the history reason while the committed view said
    untracked.

    The committed case is
    `test_a_covers_path_outside_the_repository_is_unchecked_as_untracked`."""
    repo, arch = _repo(tmp_path)
    outside = tmp_path_factory.mktemp("elsewhere")
    _write_view(arch, "container.md", covers=f"wfctl/, {outside}")

    assert _fresh(repo, arch, "container.md") == _views.Freshness(
        "unchecked", f"covers names {outside}, which git doesn't track"
    )


def test_an_uncommitted_deletion_of_covered_code_changes_nothing(tmp_path: Path) -> None:
    """Freshness reads commits only, and a file deleted but not committed
    printed the view as unchecked."""
    repo, arch = _repo(tmp_path)
    _write_view(arch, "container.md", covers="wfctl/a.py")
    _commit(repo, "draw the view")
    (repo / "wfctl" / "a.py").unlink()

    assert _fresh(repo, arch, "container.md") == _views.Freshness("current", "")


def test_a_committed_view_that_is_not_utf8_does_not_crash(tmp_path: Path) -> None:
    """Reading `covers` through `git show` decoded the output strictly, so one
    bad byte in a view raised out of `arch context`."""
    repo, arch = _repo(tmp_path)
    file = _write_view(arch, "container.md", covers="wfctl/")
    file.write_bytes(file.read_bytes() + b"\xff\xfe\n")
    _commit(repo, "draw the view")

    assert _fresh(repo, arch, "container.md") == _views.Freshness("current", "")


def test_a_deleted_view_being_redrawn_is_measured_against_its_last_version(
    tmp_path: Path,
) -> None:
    """The view's last commit was its deletion, which `git show` can't read, so
    the redraw printed as outside the history."""
    repo, arch = _repo(tmp_path)
    file = _write_view(arch, "container.md", covers="wfctl/")
    _commit(repo, "draw the view")
    file.unlink()
    _commit(repo, "drop the view")
    _write_view(arch, "container.md", covers="wfctl/")

    assert _fresh(repo, arch, "container.md") == _views.Freshness("current", "")


def test_a_view_with_no_commit_yet_is_current(tmp_path: Path) -> None:
    """It's being drawn now, so there's nothing for the code to be newer than
    (contract rule 6)."""
    repo, arch = _repo(tmp_path)
    _write_view(arch, "container.md", covers="wfctl/")

    assert _fresh(repo, arch, "container.md") == _views.Freshness("current", "")


def test_a_stale_view_prints_with_its_mark(
    agent_dir: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repo, arch = _cli_repo(agent_dir, monkeypatch)
    _write_view(arch, "container.md", covers="README.md")
    _commit(repo, "draw the view")
    (repo / "README.md").write_text("changed\n")
    _commit(repo, "change the readme")

    out = runner.invoke(app, ["arch", "context"]).output

    assert (
        "  stale: docs/architecture/views/container.md "
        "(1 commit to README.md since the view changed)\n"
    ) in _block(out)


def test_a_view_with_no_covers_line_or_an_empty_one_is_unchecked(tmp_path: Path) -> None:
    """Without a `covers` line wfctl can't tell whether the view is stale, and
    printing it as current would say it checked."""
    repo, arch = _repo(tmp_path)
    _write_view(arch, "system-context.md", covers=None)
    _write_view(arch, "container.md", covers="")
    _commit(repo, "views")

    for name in ("system-context.md", "container.md"):
        assert _fresh(repo, arch, name) == _views.Freshness("unchecked", "no covers line")


def test_a_covers_path_that_does_not_exist_names_the_first_one(tmp_path: Path) -> None:
    """A renamed folder leaves the count at 0 forever, since git finds no
    commits to a path that isn't there."""
    repo, arch = _repo(tmp_path)
    _write_view(arch, "container.md", covers="wfctl/, wfctl/attn/, gone/")
    _commit(repo, "view")

    assert _fresh(repo, arch, "container.md") == _views.Freshness(
        "unchecked", "covers names wfctl/attn/, which doesn't exist"
    )


def test_a_covers_path_git_does_not_track_is_unchecked(tmp_path: Path) -> None:
    """A path on disk that git ignores or hasn't been told about gets no
    commits, so the count would stay at 0 and the view would read current
    forever. `.agents/` and `specs/` are gitignored in this repo, which makes it
    an easy slip."""
    repo, arch = _repo(tmp_path)
    (repo / ".gitignore").write_text("build/\n")
    (repo / "build").mkdir()
    (repo / "build" / "out.py").write_text("x = 1\n")
    _write_view(arch, "container.md", covers="wfctl/, build/")
    _commit(repo, "view")

    assert _fresh(repo, arch, "container.md") == _views.Freshness(
        "unchecked", "covers names build/, which git doesn't track"
    )


def test_a_covers_path_outside_the_repository_is_unchecked_as_untracked(
    tmp_path: Path, tmp_path_factory: pytest.TempPathFactory
) -> None:
    """The view is in the history and the path isn't, so the history reason
    would point the reader at the wrong file."""
    repo, arch = _repo(tmp_path)
    outside = tmp_path_factory.mktemp("elsewhere")
    _write_view(arch, "container.md", covers=f"wfctl/, {outside}")
    _commit(repo, "view")

    assert _fresh(repo, arch, "container.md") == _views.Freshness(
        "unchecked", f"covers names {outside}, which git doesn't track"
    )


def test_a_view_git_ignores_is_unchecked_rather_than_current(tmp_path: Path) -> None:
    """An ignored view never gets a commit, so "no commit yet, being drawn now"
    would read current forever. It happens when the architecture root sits
    under an ignored folder."""
    repo, arch = _repo(tmp_path)
    (repo / ".gitignore").write_text("docs/\n")
    _commit(repo, "ignore docs")
    _write_view(arch, "container.md", covers="wfctl/")

    assert _fresh(repo, arch, "container.md") == _views.Freshness(
        "unchecked", "git ignores the view"
    )


def test_a_view_outside_the_working_tree_is_unchecked_and_prints_absolute(
    agent_dir: Path, monkeypatch: pytest.MonkeyPatch, tmp_path_factory: pytest.TempPathFactory
) -> None:
    """Its files aren't in the code's history, so a `git` call fails, and wfctl
    never reads a failed call as "no commit yet". Otherwise the view would print
    as current forever when nothing checked it (contract rules 4 and 7). A view
    there with no `covers` line takes the same reason, since the history reason
    comes first."""
    outside = tmp_path_factory.mktemp("specs-arch")
    monkeypatch.setenv("WFCTL_ARCH_DIR", str(outside))
    _write_view(outside, "container.md", covers="README.md")
    _write_view(outside, "system-context.md", covers=None)

    result = runner.invoke(app, ["arch", "context"])

    assert result.exit_code == 0
    assert _block(result.output) == (
        "Views\n"
        f"  unchecked: {outside}/views/system-context.md (not in this repository's history)\n"
        f"  unchecked: {outside}/views/container.md (not in this repository's history)\n"
    )


def test_a_directory_that_is_not_a_git_repository_gives_the_history_reason(
    tmp_path: Path,
) -> None:
    """In-tree, with no git at all. The view also has no `covers` line, and the
    history reason still wins, because it comes first in the order data-model.md
    sets."""
    arch = tmp_path / "docs" / "architecture"
    _write_view(arch, "container.md", covers="README.md")
    _write_view(arch, "system-context.md", covers=None)

    for name in ("container.md", "system-context.md"):
        assert _fresh(tmp_path, arch, name) == _views.Freshness(
            "unchecked", "not in this repository's history"
        )
