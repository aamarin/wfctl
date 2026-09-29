"""Where the running wfctl was installed from, read once and asked three ways.

The answer is PEP 610's `direct_url.json`, which pip and uv write for every
install that did not come from an index. That it is already on disk is what
keeps every caller free: no build-time stamping, no packaging change, no
network.

`parse` is the only place the file's shapes are enumerated
(`docs/architecture/design/install-origin-parsed-once.md`). The callers ask
different questions of the result and disagree about what a checkout means:
`doctor` asks whether the build can drift from a branch, where a checkout has
no branch to compare; `install-skills` asks which files it just wrote, where a
checkout is the answer that matters most. So the parse is shared and the
interpretation is not.
"""
from __future__ import annotations

import enum
import json
import shlex
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import unquote, urlsplit
from urllib.request import url2pathname


class Kind(enum.Enum):
    """Named for the key that decides it, so a reader can match a kind to a file.

    VCS           `vcs_info` — a repository at a commit
    DIRECTORY     `dir_info` — a working copy, editable or copied from one
    ARCHIVE       `archive_info` — a wheel or sdist named by path or URL
    INDEX         no file at all — resolved from a package index
    UNREADABLE    a file this process cannot use, or no distribution to ask
    """

    VCS = "vcs"
    DIRECTORY = "directory"
    ARCHIVE = "archive"
    INDEX = "index"
    UNREADABLE = "unreadable"


@dataclass(frozen=True)
class Origin:
    kind: Kind
    url: str = ""
    commit: str = ""
    pinned: bool = False
    """The user asked for a fixed revision, so drift against a branch is not news."""


def parse(raw: str | None) -> Origin:
    """The file's text as an `Origin`. Pure, and never raises.

    None is a missing file and "" an empty one. They are different kinds: an
    index install writes nothing, and an empty file is something another tool
    left behind. A health check must not raise on either.

    `vcs_info` is tested first because it is what makes an install comparable
    to a branch, and `git+file://` is a real git install of a local clone even
    though its URL looks like a directory's.
    """
    if raw is None:
        return Origin(Kind.INDEX)
    try:
        payload = json.loads(raw)
    except ValueError:
        return Origin(Kind.UNREADABLE)
    if not isinstance(payload, dict):
        return Origin(Kind.UNREADABLE)
    url = payload.get("url")
    if not isinstance(url, str) or not url:
        return Origin(Kind.UNREADABLE)
    vcs = payload.get("vcs_info")
    if isinstance(vcs, dict):
        commit = vcs.get("commit_id")
        if not isinstance(commit, str) or not commit:
            return Origin(Kind.UNREADABLE)
        return Origin(Kind.VCS, url, commit, pinned="requested_revision" in vcs)
    if isinstance(payload.get("dir_info"), dict):
        return Origin(Kind.DIRECTORY, url)
    if isinstance(payload.get("archive_info"), dict):
        return Origin(Kind.ARCHIVE, url)
    return Origin(Kind.UNREADABLE)


def read() -> Origin:
    """The running wfctl's `Origin`.

    `distribution` is looked up at call time rather than imported at module
    load, so a test that stubs `importlib.metadata.distribution` reaches it.
    """
    from importlib.metadata import PackageNotFoundError, distribution

    try:
        raw = distribution("wfctl").read_text("direct_url.json")
    except (PackageNotFoundError, OSError):
        return Origin(Kind.UNREADABLE)
    return parse(raw)


def _tail(url: str, segments: int) -> str:
    """The last `segments` path segments of a URL: `aamarin/wfctl`, `wt/69-x`.

    Two for an origin rather than one, because the leaf alone repeats; every
    fork ends in `wfctl`, and every worktree of one clone sits in the same
    parent. Two rather than the whole path, because this ends a success line
    read at a glance, and an absolute path pushes the version off a narrow
    terminal.
    """
    path = unquote(urlsplit(url).path).rstrip("/")
    path = path.removesuffix(".git")
    parts = [p for p in path.split("/") if p]
    return "/".join(parts[-segments:]) if parts else url


def describe(origin: Origin) -> str:
    """The clause `install-skills` appends to its success line.

    Every kind has one. A line that says nothing for some installs is the
    failure this exists to end, since a reader cannot tell "a release" from "a
    shape nobody named".
    """
    if origin.kind is Kind.VCS:
        return f"{_tail(origin.url, 2)} @ {origin.commit[:7]}"
    if origin.kind is Kind.DIRECTORY:
        return f"working copy {_tail(origin.url, 2)}"
    if origin.kind is Kind.ARCHIVE:
        return f"archive {_tail(origin.url, 1)}"
    if origin.kind is Kind.INDEX:
        return "package index"
    return "origin unreadable"


def _checkout(origin: Origin) -> Path | None:
    """The working copy's directory, or None for every other kind.

    Also None for a `dir_info` URL that is not `file:`, which PEP 610 does not
    allow and which no path could be read from anyway.
    """
    if origin.kind is not Kind.DIRECTORY:
        return None
    parts = urlsplit(origin.url)
    if parts.scheme != "file":
        return None
    return Path(url2pathname(parts.path))


def runner(origin: Origin, here: Path) -> str:
    """The words that start this same wfctl from `here`, for a remedy to print.

    A bare `wfctl` is whatever is on PATH, which beside a working copy is
    usually the release. A remedy printed by a working copy that says `wfctl`
    installs the release's bundle over the checkout under test, and reports
    success doing it. So a working copy is run through uv, as this
    repository's own `post_create` does.

    `--project` names the checkout unless `here` is that checkout. `uv run`
    finds its project by walking up from the working directory, and it leaves
    that directory alone, so the install still lands in `here`. Equality and
    not containment: a worktree nested under the main checkout finds its own
    `pyproject.toml` first.

    The program only. Which bundle it installs is `--from`'s question, and a
    caller that has one still adds it.
    """
    path = _checkout(origin)
    if path is None:
        return "wfctl"
    if path.resolve() == here.resolve():
        return "uv run wfctl"
    return f"uv run --project {shlex.quote(str(path))} wfctl"
