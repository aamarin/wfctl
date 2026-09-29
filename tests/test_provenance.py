"""Where the running wfctl was installed from (#76), and the remedy it prints (#524).

The payloads here were read off real installs, not written from the PEP 610
specification: `uv tool install` from GitHub, `uv run` in a worktree, and
`uv pip install` of a directory and of a built wheel into a scratch venv. A
test built from the specification would pass against a shape uv never writes.
"""
from __future__ import annotations

from pathlib import Path

import pytest

from wfctl import _provenance
from wfctl._provenance import Kind, Origin, describe, parse, runner

RELEASE = (
    '{"url":"https://github.com/aamarin/wfctl.git",'
    '"vcs_info":{"vcs":"git","commit_id":"4ca1604f3172d5f1ecd0221a2ca6d8d6fb231e22"}}'
)
EDITABLE = (
    '{"url":"file:///Users/me/wfctl/wt/69-machine-checked-done",'
    '"dir_info":{"editable":true}}'
)
DIRECTORY = '{"url":"file:///Users/me/wfctl/wt/69-machine-checked-done","dir_info":{}}'
WHEEL = '{"url":"file:///tmp/dist/wfctl-0.21.0-py3-none-any.whl","archive_info":{}}'


def _working_copy(path: Path) -> Origin:
    return parse(f'{{"url":"{path.as_uri()}","dir_info":{{"editable":true}}}}')


# --- parse ---


@pytest.mark.parametrize(("raw", "kind"), [
    (RELEASE, Kind.VCS),
    (EDITABLE, Kind.DIRECTORY),
    (DIRECTORY, Kind.DIRECTORY),
    (WHEEL, Kind.ARCHIVE),
    (None, Kind.INDEX),
])
def test_every_shape_a_real_install_writes_parses_to_its_own_kind(
    raw: str | None, kind: Kind
) -> None:
    assert parse(raw).kind is kind


@pytest.mark.parametrize("raw", [
    "",
    "not json",
    "[]",
    '{"vcs_info":{"commit_id":"abc"}}',
    '{"url":"https://x/wfctl.git","vcs_info":{"vcs":"git"}}',
    '{"url":"https://x/wfctl.git"}',
])
def test_a_file_this_process_cannot_use_is_unreadable_and_never_raises(raw: str) -> None:
    """`doctor` runs this inside `/start-session` before it has reported
    anything, and the file is one some other tool wrote."""
    assert parse(raw).kind is Kind.UNREADABLE


def test_an_empty_file_is_not_read_as_an_index_install() -> None:
    """An index install writes no file at all. An empty one is something another
    tool left, and saying "package index" for it would name an origin nobody
    recorded."""
    assert parse("").kind is not parse(None).kind


def test_a_git_install_of_a_local_clone_is_a_repository_not_a_working_copy() -> None:
    """`git+file://` looks like a directory by its URL, and is a real git install
    with a real branch worth comparing, so `vcs_info` decides."""
    origin = parse('{"url":"file:///src/wfctl","vcs_info":{"vcs":"git","commit_id":"abc1234"}}')
    assert origin.kind is Kind.VCS


def test_a_pin_is_carried_on_a_repository_origin() -> None:
    raw = RELEASE.replace('"vcs":"git"', '"vcs":"git","requested_revision":"v0.13.0"')
    assert parse(raw).pinned is True
    assert parse(RELEASE).pinned is False


@pytest.mark.real_install_origin
def test_read_reports_a_missing_distribution_as_unreadable(monkeypatch) -> None:
    import importlib.metadata

    def missing(name: str) -> None:
        raise importlib.metadata.PackageNotFoundError(name)

    monkeypatch.setattr(importlib.metadata, "distribution", missing)
    assert _provenance.read().kind is Kind.UNREADABLE


# --- describe ---


@pytest.mark.parametrize(("raw", "clause"), [
    (RELEASE, "aamarin/wfctl @ 4ca1604"),
    (EDITABLE, "working copy wt/69-machine-checked-done"),
    (DIRECTORY, "working copy wt/69-machine-checked-done"),
    (WHEEL, "archive wfctl-0.21.0-py3-none-any.whl"),
    (None, "package index"),
    ("not json", "origin unreadable"),
])
def test_every_kind_names_itself_so_no_install_prints_the_bare_version(
    raw: str | None, clause: str
) -> None:
    """A clause printed only sometimes leaves the silent runs reading as a
    release, which is the failure #76 exists to end."""
    assert describe(parse(raw)) == clause


def test_a_percent_encoded_working_copy_is_named_as_a_person_would_type_it() -> None:
    origin = _working_copy(Path("/Users/me/my projects/wfctl"))
    assert describe(origin) == "working copy my projects/wfctl"


# --- runner ---


def test_a_release_is_run_as_the_wfctl_on_path(tmp_path: Path) -> None:
    assert runner(parse(RELEASE), tmp_path) == "wfctl"


def test_a_working_copy_standing_in_itself_is_run_through_uv(tmp_path: Path) -> None:
    """What this repository's `post_create` runs. A bare `wfctl` here is the
    release, and following it installs the release over the checkout (#524)."""
    assert runner(_working_copy(tmp_path), tmp_path) == "uv run wfctl"


def test_a_working_copy_elsewhere_is_named_so_uv_does_not_find_another_project(
    tmp_path: Path,
) -> None:
    """A wfctl worktree sits under the main checkout's directory, so `uv run`
    from it finds the worktree's own project first. Containment is not enough;
    only the checkout itself can drop `--project`."""
    source = tmp_path / "main"
    here = source / "wt" / "76-x"
    here.mkdir(parents=True)
    assert runner(_working_copy(source), here) == f"uv run --project {source} wfctl"


def test_a_working_copy_path_with_a_space_is_quoted_for_the_shell(tmp_path: Path) -> None:
    source = tmp_path / "my src"
    assert runner(_working_copy(source), tmp_path) == f"uv run --project '{source}' wfctl"


@pytest.mark.real_install_origin
def test_a_record_that_is_not_utf8_is_unreadable_rather_than_a_traceback(monkeypatch) -> None:
    """`read` runs on every `doctor`, `start` and `install-skills`, and the file
    is one some other tool wrote."""
    import importlib.metadata

    class _Dist:
        def read_text(self, name: str) -> str:
            raise UnicodeDecodeError("utf-8", b"\xff", 0, 1, "invalid start byte")

    monkeypatch.setattr(importlib.metadata, "distribution", lambda name: _Dist())
    assert _provenance.read().kind is Kind.UNREADABLE


# --- every printed install command ---

# Strings that name `wfctl install-skills` and are deliberately not a command
# the running wfctl should start. The `.workmux.yaml` entry is the repository's
# own config, whose right command depends on the repository.
_NOT_A_RUNNING_COMMAND = (
    "post_create does not call `wfctl install-skills`",
    '&& wfctl install-skills ${WFCTL_AGENT:+--agent "$WFCTL_AGENT"} || true',
)


def _printed_strings(path: Path) -> list[str]:
    """Every string literal in a module except its docstrings.

    Adjacent literals arrive joined, as the compiler joins them. The fragments of an f-string are Constant nodes of their own, so a command
    built as `f"{runner} install-skills"` leaves the fragment ` install-skills`,
    which the pattern below does not match.
    """
    import ast

    tree = ast.parse(path.read_text())
    docstrings = {
        id(node.body[0].value)
        for node in ast.walk(tree)
        if isinstance(node, (ast.Module, ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))
        and node.body
        and isinstance(node.body[0], ast.Expr)
        and isinstance(node.body[0].value, ast.Constant)
    }
    return [
        node.value
        for node in ast.walk(tree)
        if isinstance(node, ast.Constant)
        and isinstance(node.value, str)
        and id(node) not in docstrings
    ]


def test_no_printed_install_command_names_a_bare_wfctl() -> None:
    """#524 was fixed at one site and survived at seven more, three of them
    found only after a pass that said "every". A bare `wfctl install-skills`
    printed by a working copy runs the release on PATH, so each one is either
    built from `_runner` or named above as not meant to be."""
    import re

    import wfctl

    offenders = [
        f"{module.name}: {text!r}"
        for module in sorted(Path(wfctl.__file__).parent.glob("*.py"))
        for text in _printed_strings(module)
        if re.search(r"(?<![\w-])wfctl install-skills", text)
        and not any(allowed in text for allowed in _NOT_A_RUNNING_COMMAND)
    ]
    assert offenders == []


@pytest.mark.parametrize("where", ["release", "here", "elsewhere"])
def test_start_session_is_granted_every_repair_the_runner_can_print(
    tmp_path: Path, where: str
) -> None:
    """`/start-session` runs doctor's repair line unattended, and its
    `allowed-tools` grants what it may run without asking. A runner form with no
    grant turns that refresh into a permission prompt nobody answers, and the
    layer stays stale in the one flow the working-copy runner was built for.
    Codex caught this on #536 after the runner shipped with only the bare grant.
    """
    import re
    from fnmatch import fnmatchcase

    from importlib.resources import files

    from wfctl import _arch

    checkout = tmp_path / "checkout dir"
    checkout.mkdir()
    origin = parse(RELEASE) if where == "release" else _working_copy(checkout)
    here = checkout if where == "here" else tmp_path
    line = f"{runner(origin, here)} install-skills --prune --yes --agent claude"
    skill = Path(str(files("wfctl"))) / "agents" / "skills" / "start-session" / "SKILL.md"
    allowed = _arch._frontmatter(skill.read_text()).get("allowed-tools", "")
    grants = re.findall(r"Bash\(([^)]*)\)", allowed)

    assert any(fnmatchcase(line, grant) for grant in grants), (line, grants)
