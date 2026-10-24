"""Which sections of a PR body a repository requires answered, and whether they are.

`every-change-answers-spec-question` has every PR say whether the change needed a
spec, and a rule only the author reads is a rule that gets skipped:
`a-rule-is-expressed-as-a-check` ships it as a check over the PR body, which is
an artifact the work already produces. `check-body` runs it.

## Why wfctl holds no section name

`check-body` ships to every repository that uses wfctl, and each repository owns
its PR template. A section name written here would fail the body of a repository
whose template has never heard of it. So the repository lists the headings it
requires under `change_sections` in `wfctl.json`, the way `change_check` lists
the fields a change must carry, and wfctl compares the body against that list.
`docs/architecture/design/628-spec-answer-in-pr-body.md` records the choice.

## What is pure here and what is not

`body_findings` is, and stays that way: a body and a list in, lines out, no
repository and no subprocess. That is `_shape.py`'s shape, and it is why every
state it reports is reachable from a unit test.

`load_required` and `templates` read the repository. `load_required` follows
`_change.load_required` line for line and borrows only `CONFIG_PATH`, so the
file's location has one definition while each key's schema lives with the feature
that reads it.
"""
from __future__ import annotations

import json
import os
import re
from pathlib import Path

from wfctl import _md
from wfctl._verify import CONFIG_PATH

CONFIG_KEY = "change_sections"

# An unclosed comment runs to the end of the body, because GitHub hides
# everything after it.
_COMMENT = re.compile(r"<!--.*?(?:-->|\Z)", re.DOTALL)

# Up to three leading spaces, which is markdown's own limit. A closing run of `#`
# is part of the syntax, not of the heading's text.
_HEADING = re.compile(r"^ {0,3}(#{1,6})[ \t]+(.*?)(?:[ \t]+#+)?[ \t]*$")

# The PR template's comment names None beside N/A as a non-answer, so the check
# flags both.
_NOT_AN_ANSWER = re.compile(r"(n/?a|none)\.?", re.IGNORECASE)
_BARE_ANSWER = re.compile(r"(yes|no)[.!,;:]?", re.IGNORECASE)

# A quote, a list bullet, a numbered item, or a checkbox at the start of a line,
# in any mix.
_MARKER = re.compile(r"^\s*(?:>\s*|[-*+]\s+|\d+[.)]\s+|\[[ xX]\]\s*)*")

# A horizontal rule renders as a line and nothing else.
_RULE = re.compile(r"^ {0,3}([-*_])(?:[ \t]*\1){2,}[ \t]*$")

# `find -maxdepth 3`, as `opening-a-change` Step 2 spells it: a path with three
# parts at most, counted from the repository root.
_TEMPLATE_PARTS = 3
_TEMPLATE_MARKERS = ("pull_request_template", "merge_request_template")


def load_required(repo_root: Path) -> tuple[list[str], list[str]]:
    """Return (required headings, problems). Both empty means nothing is required.

    Problems come back rather than raise, so a caller that only wants to know "is
    anything required" needs no guard. A half-valid declaration yields no headings
    at all: findings justified from a list the reader could not fully read would
    be worse than none.
    """
    path = repo_root / CONFIG_PATH
    if not path.exists():
        return [], []
    try:
        data = json.loads(path.read_text())
    except (OSError, json.JSONDecodeError):
        # `doctor` already reports a malformed `wfctl.json`, and says it better
        # than this reader could. Saying it twice would put the same finding in
        # front of someone opening a change, where it is not what they asked.
        return [], []
    if not isinstance(data, dict):
        return [], []

    declared = data.get(CONFIG_KEY)
    if declared is None:
        return [], []
    if not isinstance(declared, list):
        return [], [f"{CONFIG_PATH}: '{CONFIG_KEY}' must be a list of section headings"]

    names: list[str] = []
    errs: list[str] = []
    for i, entry in enumerate(declared, 1):
        if not isinstance(entry, str):
            errs.append(
                f"{CONFIG_PATH}: '{CONFIG_KEY}' entry {i} must be a section "
                f"heading, got {type(entry).__name__}"
            )
        elif not entry.strip():
            errs.append(f"{CONFIG_PATH}: '{CONFIG_KEY}' entry {i} is empty")
        elif entry not in names:
            names.append(entry)

    return ([], errs) if errs else (names, [])


def _section(body: str, name: str) -> str | None:
    """The text under the heading called `name`, or None when no such heading.

    Comments go first, before any heading is looked for: GitHub does not render
    an HTML comment, so a heading inside one is not a section the reviewer can
    read, and a template's instruction comment can quote its own heading without
    counting as an answer.

    A section runs to the next heading of the same or a higher level, so a reason
    broken up under sub-headings stays inside it. A heading inside a fence is
    quoted text and opens nothing, which is what `_md.walk` is shared for.
    """
    wanted = name.strip().casefold()
    lines = [
        (line, _HEADING.match(line.text) if not line.inside and not line.fence else None)
        for line in _md.walk(_COMMENT.sub("", body))
    ]

    level = 0
    collected: list[str] = []
    for line, heading in lines:
        if not level:
            if heading and heading.group(2).strip().casefold() == wanted:
                level = len(heading.group(1))
            continue
        if heading and len(heading.group(1)) <= level:
            break
        collected.append(line.text)
    return "\n".join(collected) if level else None


def _markup_removed(text: str) -> str:
    """The section's text with its markdown markup taken out, for matching only.

    "**No**.", "- [ ] No" and "> No" are each a bare answer once the markup is
    gone, and the markup is the most common way an agent fills a template
    section. Removing it can't turn an answer with a reason into a bare one,
    since the patterns only ever match the whole text. A sub-heading or a
    horizontal rule carries no answer, so a section holding only one reads as
    empty. HTML tags go too, since `<strong>No</strong>` renders as a bare "No".
    """
    lines = [
        _MARKER.sub("", line)
        for line in text.splitlines()
        if not _HEADING.match(line) and not _RULE.match(line)
    ]
    text = re.sub(r"<[^>]+>", "", "\n".join(lines))
    return re.sub(r"[*_`~]", "", text).strip()


def body_findings(body: str, required: list[str]) -> list[str]:
    """One line per listed section the body leaves unanswered, in list order.

    The check confirms that a reason is there, not that it is a good one:
    "No, small change." passes, and the reviewer judges it. A bare yes or no is
    flagged because it leaves nothing to compare with the diff, and that
    comparison is how a contradiction between the answer and the change is caught.
    """
    findings: list[str] = []
    for name in required:
        text = _section(body, name)
        if text is None:
            findings.append(
                f'"{name}" is missing. This repository asks every pull request to answer it.'
            )
            continue
        answer = _markup_removed(text)
        hint = "The template's comment under that heading says what to write."
        if not answer:
            findings.append(f'"{name}" is empty. {hint}')
        elif _NOT_AN_ANSWER.fullmatch(answer):
            findings.append(f'"{name}" holds N/A. {hint}')
        elif _BARE_ANSWER.fullmatch(answer):
            findings.append(f'"{name}" answers yes or no with no reason. {hint}')
    return findings


def templates(repo_root: Path) -> list[Path]:
    """Every PR or MR template in the repository, as `opening-a-change` finds them.

    That skill's Step 2 runs `find . -maxdepth 3 -name .git -prune -o -type f
    ( -ipath '*pull_request_template*' -o -ipath '*merge_request_template*' )`.
    This mirrors it so that `check config` reports on the files a change would
    actually pick from, including the files in GitHub's multi-template directory,
    which are named `bug.md` and match only through the directory they sit in.
    """
    found: list[Path] = []
    for dirpath, dirnames, filenames in os.walk(repo_root):
        here = Path(dirpath)
        depth = len(here.relative_to(repo_root).parts)
        if ".git" in dirnames:
            dirnames.remove(".git")
        if depth + 1 >= _TEMPLATE_PARTS:
            dirnames.clear()
        for filename in filenames:
            path = here / filename
            rel = path.relative_to(repo_root).as_posix().lower()
            if any(marker in rel for marker in _TEMPLATE_MARKERS):
                found.append(path)
    return sorted(found)


def _winning(repo_root: Path, paths: list[Path]) -> list[Path]:
    """The templates in the location `opening-a-change` picks from.

    Its Step 2 says `.github/` wins over `docs/` and the repository root, which
    win over a match anywhere else. Every template in the winning location is
    kept, so a multi-template directory stays whole.
    """
    def rank(path: Path) -> int:
        parts = path.relative_to(repo_root).parts
        if parts[0].lower() == ".github":
            return 0
        if len(parts) == 1 or parts[0].lower() == "docs":
            return 1
        return 2

    best = min((rank(p) for p in paths), default=0)
    return [p for p in paths if rank(p) == best]


def template_problems(repo_root: Path, required: list[str]) -> list[str]:
    """The gaps between the listed sections and the repository's PR templates.

    Only a missing heading is a gap. A template's sections are meant to be empty,
    so reporting an empty one would flag every repository that opted in. Each
    template in the winning location is checked, since any of them can be the
    one a change uses, and a template it shadows never is.

    A template that can't be read is a problem rather than a skip. When it is the
    only one, skipping it would pass the check without reading any heading.
    """
    if not required:
        return []
    paths = _winning(repo_root, templates(repo_root))
    if not paths:
        return [f"{CONFIG_PATH}: '{CONFIG_KEY}' lists sections, but no PR template was found"]

    problems: list[str] = []
    for path in paths:
        rel = path.relative_to(repo_root).as_posix()
        try:
            text = path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            problems.append(
                f"{CONFIG_PATH}: '{CONFIG_KEY}' lists sections, but {rel} can't be "
                "read as UTF-8 text"
            )
            continue
        for name in required:
            if _section(text, name) is None:
                problems.append(
                    f"{CONFIG_PATH}: '{CONFIG_KEY}' lists \"{name}\", which {rel} doesn't have"
                )
    return problems
