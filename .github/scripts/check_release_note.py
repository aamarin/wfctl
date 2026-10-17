#!/usr/bin/env python3
"""Fail a branch that makes a change without committing the release note for it.

A release note is a file under `changes/`, named for the issue it belongs to and
its category: `571.change.md`, or `+bump-ruff.fix.md` for work with no issue.
This script runs in two places, `wfctl verify` and the `release-note` CI job, and
both have to reach the same verdict, so it reads everything from git and
`pyproject.toml` and takes no arguments.

Standard library only. CI runs it with the runner's own Python, with no
`uv sync`, so it can't import towncrier or anything else from the dev extra.
"""
from __future__ import annotations

import os
import re
import subprocess
import sys
import tomllib
from pathlib import Path

PLACEHOLDER = "Add your info here"

# `<issue>.<category>.md`, with an optional counter that `towncrier create`
# adds when the name is taken, or `+<name>.<category>.md` for work with no issue.
NOTE_NAME = re.compile(r"^(?P<issue>\d+|\+[^.]+)\.(?P<category>[^.]+?)(?:\.\d+)?\.md$")
RELEASE_BRANCH = re.compile(r"^release/v(\d+)\.(\d+)\.(\d+)$")
BRANCH_ISSUE = re.compile(r"^(\d+)(?:-|$)")


def git(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(["git", *args], capture_output=True, text=True)


def branch_name() -> str:
    """The branch under check.

    In a pull request run, `actions/checkout` leaves a detached merge commit, so
    only `GITHUB_HEAD_REF` carries the name. GitHub sets it to the empty string
    on push runs, which counts as unset.
    """
    head_ref = os.environ.get("GITHUB_HEAD_REF", "")
    if head_ref:
        return head_ref
    done = git("rev-parse", "--abbrev-ref", "HEAD")
    name = done.stdout.strip()
    if done.returncode == 0 and name and name != "HEAD":
        return name
    return ""


def merge_base() -> str | None:
    """Where this branch left `main`, so a merge of `main` into it isn't its work."""
    for ref in ("origin/main", "main"):
        done = git("merge-base", ref, "HEAD")
        if done.returncode == 0 and done.stdout.strip():
            return done.stdout.strip()
    return None


def pyproject_at(rev: str) -> dict:
    done = git("show", f"{rev}:pyproject.toml")
    return tomllib.loads(done.stdout) if done.returncode == 0 else {}


def version_at(rev: str) -> tuple[int, ...] | None:
    """Three integers, so 0.10.0 is higher than 0.9.0."""
    version = pyproject_at(rev).get("project", {}).get("version", "")
    parts = version.split(".")
    if len(parts) == 3 and all(p.isdigit() for p in parts):
        return tuple(int(p) for p in parts)
    return None


def dotted(version: tuple[int, ...] | None) -> str:
    return ".".join(str(p) for p in version) if version else "unknown"


def towncrier_settings() -> tuple[str, list[str]]:
    """The notes folder and the category list, read on every run.

    The categories are towncrier's own `[[tool.towncrier.type]]` tables, so a
    category added there reaches every message below with no edit here.
    """
    table = tomllib.loads(Path("pyproject.toml").read_text()).get("tool", {}).get("towncrier", {})
    return table.get("directory", "changes"), [t["directory"] for t in table.get("type", [])]


def added_files(base: str, directory: str) -> list[str]:
    """Files this branch added under the notes folder.

    `--no-renames` makes a moved note count as added. A missing folder yields
    nothing, which is the ordinary state right after a release, since git keeps
    no empty folder.
    """
    done = git("diff", "--name-only", "--no-renames", "--diff-filter=A", base, "HEAD", "--", directory)
    return [line for line in done.stdout.splitlines() if line]


def uncommitted_notes(directory: str, issue: str | None) -> list[str]:
    """Notes sitting in the working tree that no commit carries yet.

    `wfctl verify` runs on a dirty tree, and the check judges commits only, so a
    note that was just created reads as missing. Naming the file tells the
    author to commit it, where "add a note" would send them to create a second.
    With no issue, any note counts.
    """
    done = git("status", "--porcelain", "--untracked-files=all", "--", directory)
    found: list[str] = []
    for line in done.stdout.splitlines():
        path = line[3:]
        match = NOTE_NAME.match(path.removeprefix(directory + "/"))
        if match and (issue is None or match["issue"] == issue):
            found.append(path)
    return found


def no_note_finding(
    where: str, directory: str, issue: str | None, pattern: str, example: str, listed: str
) -> str:
    pending = uncommitted_notes(directory, issue)
    if pending:
        return (
            f"✗ no committed release note {where}\n"
            f"  {', '.join(pending)} isn't committed yet, so git add it and commit"
        )
    return (
        f"✗ no release note {where}\n"
        f"  add {directory}/{pattern}, where the category is {listed}\n"
        f'  for example: uv run towncrier create {example} --content "What a user of wfctl will notice."'
    )


def check_release_branch(branch: str, base: str, groups: tuple[str, ...]) -> list[str]:
    named = tuple(int(p) for p in groups)
    carried = version_at("HEAD")
    if carried != named:
        return [
            f"✗ {branch} carries version {dotted(carried)} in pyproject.toml\n"
            "  a release branch needs no note only when its version matches its name"
        ]
    on_main = version_at(base)
    if on_main is None or named <= on_main:
        return [
            f"✗ {branch} carries version {dotted(carried)}, and main already carries {dotted(on_main)}\n"
            "  a release branch needs no note only when it raises the version"
        ]
    return []


def inspect_added_notes(
    base: str, directory: str, categories: list[str], listed: str
) -> tuple[list[str], list[tuple[str, str]]]:
    """Every file this branch added under the notes folder, as findings and notes.

    A file with a note's name counts as a note for its issue even when its
    category or content is wrong, so one mistake produces one finding instead of
    also reporting the issue as having no note.
    """
    findings: list[str] = []
    notes: list[tuple[str, str]] = []  # (path, issue)
    for path in added_files(base, directory):
        name = path.removeprefix(directory + "/")
        match = NOTE_NAME.match(name) if "/" not in name else None
        if match is None:
            findings.append(
                f"✗ {path} isn't a release note name\n"
                "  name it <issue>.<category>.md, or +<name>.<category>.md for work with no issue"
            )
            continue
        notes.append((path, match["issue"]))
        if match["category"] not in categories:
            findings.append(
                f'✗ {path} names the category "{match["category"]}", which doesn\'t exist\n'
                f"  use {listed}"
            )
            continue
        text = git("show", f"HEAD:{path}").stdout
        if not text.strip():
            findings.append(f"✗ {path} has no release note written in it\n  the file is empty")
        elif text.strip() == PLACEHOLDER:
            findings.append(
                f"✗ {path} has no release note written in it\n"
                f'  replace "{PLACEHOLDER}" with what a user of wfctl will notice'
            )
    return findings, notes


def main() -> int:
    branch = branch_name()
    if branch == "main":
        print("✓ on main, nothing to check")
        return 0

    base = merge_base()
    if base is None:
        print("✗ can't find main to compare this branch against\n"
              "  run git fetch origin main, then check again")
        return 1

    release_match = RELEASE_BRANCH.match(branch)
    if release_match:
        findings = check_release_branch(branch, base, release_match.groups())
        if findings:
            print("\n".join(findings))
            return 1
        print(f"✓ release branch for {branch.removeprefix('release/v')}, no note needed")
        return 0

    directory, categories = towncrier_settings()
    listed = ", ".join(categories[:-1]) + f", or {categories[-1]}"
    findings, notes = inspect_added_notes(base, directory, categories, listed)

    issue_match = BRANCH_ISSUE.match(branch)
    if issue_match:
        issue = issue_match.group(1)
        found = [path for path, noted in notes if noted == issue]
        if not found:
            findings.append(
                no_note_finding(f"for #{issue}", directory, issue, f"{issue}.<category>.md",
                                f"{issue}.{categories[0]}.md", listed)
            )
        label = f"release note for #{issue}"
    else:
        found = [path for path, _ in notes]
        if not found:
            example = f'+<what-changed>.{"fix" if "fix" in categories else categories[0]}.md'
            findings.append(
                no_note_finding("on this branch", directory, None, "+<what-changed>.<category>.md",
                                example, listed)
            )
        label = "release note"

    if findings:
        print("\n".join(findings))
        return 1
    print(f"✓ {label}: {', '.join(found)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
