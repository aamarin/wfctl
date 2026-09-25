"""The part of a PR body's drawing rules a machine can see.

Pure functions over strings. The caller finds the text — in the file
`gh pr create` is about to read — and this decides. Same constraint as `_guard`,
for the same reason: the decision table is the part worth testing, and testing
it must not cost a session.

## Why this exists at all

A `Stop`-hook checker once read a finished reply and caught what a per-turn
reminder and a pre-send check could not
(`docs/architecture/the-underscore-is-the-module-contract.md` settled this shape
for module boundaries, and the argument transferred). It was retired for costing
more than it returned — it reopened a turn the reader had already seen, and
delivered the reply twice (#276, #475) — so `a-rule-is-expressed-as-a-check`'s
instance for response style is now the comment it names as the alternative, not
a check (#476).

What is left checkable is the PR-body surface, which is a file on disk rather
than a reply already delivered: `body_findings()` runs before `gh pr create`
reads it, so a finding here still reaches the author in time to fix it.

## What a PR body check can and cannot see

A PR body is a document — `.github/pull_request_template.md` is built out of
headers — so nothing here checks for them; whether a reply may use one is a
rule for whatever governs replies, not this module. The drawing rule is the one
piece that runs the same on both surfaces, so it's the one piece this module
carries.
"""
from __future__ import annotations

import re
from itertools import groupby

from wfctl import _md

# Two or more spaces between two non-spaces: a column boundary someone typed.
_HAND_ALIGNED = re.compile(r"\S {2,}\S")

# A sentence end followed by a new one. This is "one cell outgrew its header" in
# the only form a machine can see it — the rejected drawing's overflowing cell
# was a three-sentence paragraph, and no accepted drawing in the same PR body
# contains a single sentence boundary.
_SENTENCE = re.compile(r"[a-z)\]`]\.\s+[A-Z]")

# Three, because two adjacent aligned lines is a pair of annotations and any
# drawing with columns has that. Three consecutive is a column.
_ALIGNED_RUN = 3


def _blocks(text: str) -> list[tuple[int, list[str]]]:
    """Every fenced block as `(line number of its opening fence, its lines)`.

    Grouping is `_md.walk`'s `opened` field and nothing else — the boundaries
    were decided by the walk, so this cannot disagree about where a block
    starts.

    **An unclosed fence is a block here.** A truncated PR body is one a reader
    can still be told about, and telling them nothing because the block has no
    closing line is the reading that has to argue for itself. What it costs is
    that `body_findings` can now fire on the tail of a body cut off mid-block —
    the same finding it would have made had the author typed the closing line.
    """
    blocks: dict[int, list[str]] = {}
    for line in _md.walk(text):
        if line.inside and line.opened is not None:
            blocks.setdefault(line.opened, []).append(line.text)
    return sorted(blocks.items())


def body_findings(body: str) -> list[str]:
    """What a PR description's drawings break. One rule, and only one.

    `opening-a-change/SKILL.md`:234 — *"Tabular content goes in a table. Columns
    aligned by hand inside a code block read as jumbled the moment one cell
    outgrows its header. Reserve ASCII for flows and timelines."* Both halves are required to fire,
    because the rule states both: hand-aligned columns are the *form* the skill
    blesses most often (its form-selection table's most frequent row is two
    columns), and what makes them fail is a cell that outgrew its header.

    Measured on the only corpus that exists — PR #208's body, where one drawing
    was rejected as "noisy and confusing" and four were not. The rejected block
    is the only one of the five carrying a sentence boundary; every accepted one
    is hand-aligned too, so alignment alone would have flagged the fix along with
    the fault.

    The issue's third suggested signal — a fenced line over ~80 characters — is
    deliberately not here. The rejected block's longest line is 75 and the widest
    accepted one is 78, so on that corpus the threshold separating them does not
    exist. Width was not what broke it; the sentence was.
    """
    out = []
    for opened, block in _blocks(body):
        aligned = groupby(block, lambda line: bool(_HAND_ALIGNED.search(line)))
        if max((len(list(g)) for k, g in aligned if k), default=0) < _ALIGNED_RUN:
            continue
        sentences = [line for line in block if _SENTENCE.search(line)]
        if not sentences:
            continue
        quoted = " ".join(sentences[0].split())[:60]
        out.append(
            f"opening-a-change/SKILL.md:234 — the fenced block at line {opened} "
            f"aligns columns by hand and holds a cell that outgrew its header: "
            f"{quoted!r}. Tabular "
            "content goes in a table; reserve ASCII for flows and timelines."
        )
    return out
