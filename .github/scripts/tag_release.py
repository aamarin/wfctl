#!/usr/bin/env python3
"""Tag the version in pyproject.toml and publish the release its commit describes.

The `tag` job in ci.yml runs this on every push to `main`. It does nothing when
the version is already tagged and released. Otherwise it finds the release
commit for that version, tags it, and creates the GitHub release with the
commit's body as the text. The version is chosen and the text is written before
the release pull request exists (see release.py), so this only turns that
commit into a tag and a release.

Standard library only, since CI runs it with the runner's own Python. The `gh`
command is a parameter so the tests can replace it with a stub.
"""
from __future__ import annotations

import subprocess
import sys
import tempfile
import tomllib
from collections.abc import Sequence
from pathlib import Path


def run(*args: str, stdin: str | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(args, capture_output=True, text=True, input=stdin)


def git(*args: str) -> subprocess.CompletedProcess[str]:
    return run("git", *args)


def fail(message: str) -> int:
    print(f"::error::{message}")
    return 1


def version_of(pyproject_text: str) -> str:
    # `tomllib` and not a grep for `^version =`. A version key in a section above
    # [project] wins that grep, and "9.9.9" is a valid tag name, so the wrong
    # release would ship with no error.
    return str(tomllib.loads(pyproject_text)["project"]["version"])


def release_commit(version: str) -> tuple[str | None, str]:
    """The commit that cut `version`, or None and the reason there isn't one.

    `--no-merges` is required. This repository's merge commits carry the pull
    request's title in their body, so the merge of the release pull request also
    matches the search. The subject is then compared exactly, since the search
    matches anywhere in the message and a later commit can quote the subject in
    its body.
    """
    subject = f"chore(release): cut {version}"
    found = git("log", "--no-merges", "--format=%H%x09%s", "--fixed-strings",
                "--grep", subject, "HEAD").stdout.splitlines()
    for line in found:
        sha, _, title = line.partition("\t")
        if title != subject:
            continue
        at = version_of(git("show", f"{sha}:pyproject.toml").stdout)
        if at != version:
            return None, f"the commit found for {version} carries version {at}"
        return sha, ""
    return None, f"no commit with the subject {subject}"


def main(*, gh: Sequence[str] = ("gh",)) -> int:
    version = version_of(Path("pyproject.toml").read_text())
    tag = f"v{version}"

    # Each half is checked on its own. If both were keyed on the tag, a
    # `gh release create` that failed after the push would never be retried,
    # because the next run would see the tag and stop, and the release would stay
    # missing. `refs/tags/` is explicit since a branch can share the name.
    tagged = git("rev-parse", "-q", "--verify", f"refs/tags/{tag}").returncode == 0
    released = run(*gh, "release", "view", tag).returncode == 0
    if tagged and released:
        print(f"{tag} already released")
        return 0

    # Everything is checked before anything is tagged. Every machine upgrades to
    # the tag, so a tag with no release is half published, and a failure here
    # leaves neither.
    sha, reason = release_commit(version)
    if sha is None:
        return fail(reason)
    body = git("log", "-1", "--format=%b", sha).stdout
    if not body.strip():
        return fail(f"the release commit for {version} has no release notes in its body")

    if tagged:
        print(f"{tag} already tagged")
    else:
        git("config", "user.name", "github-actions[bot]")
        git("config", "user.email", "github-actions[bot]@users.noreply.github.com")
        tagging = git("tag", "-a", tag, "-m", tag)
        if tagging.returncode != 0:
            return fail(f"couldn't tag {tag}: {tagging.stderr.strip()}")
        pushed = git("push", "origin", tag)
        if pushed.returncode != 0:
            return fail(f"couldn't push {tag}: {pushed.stderr.strip()}")

    # The release text is the commit's body that the person cutting the release
    # confirmed. GitHub's generated list of pull request titles isn't used, since
    # nobody reads it.
    if not released:
        with tempfile.TemporaryDirectory() as tmp:
            notes = Path(tmp) / "notes.md"
            notes.write_text(body)
            created = run(*gh, "release", "create", tag, "--notes-file", str(notes))
        if created.returncode != 0:
            return fail(f"couldn't create the release for {tag}: {created.stderr.strip()}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
