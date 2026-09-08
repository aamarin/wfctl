"""The part of `conversation-response-shape` a machine can see.

Pure functions over strings. The caller finds the text — in a transcript, or in
the file `gh pr create` is about to read — and this decides. Same constraint as
`_guard`, for the same reason: the decision table is the part worth testing, and
testing it must not cost a session.

## Why this exists at all

The skill is already delivered three ways — a `UserPromptSubmit` hook every
turn, the rule in `SKILL.md`, a seven-question pre-send check — and all three
fire *before* the text exists. Nothing looks at what was actually written.
`docs/architecture/the-underscore-is-the-module-contract.md` settled this shape
for module boundaries and the argument transfers whole: a correct rule with
nothing to check it gets crossed a fifth time the way it was crossed the first
four.

## Two surfaces, and they do not take the same rules

`findings()` reads a terminal reply. `body_findings()` reads a PR description.
The skill governs both and says so, but it draws a line between them that a
check has to respect — SKILL.md:429, on the header rule:

> This governs the reply only. Headers are correct, and usually required, in the
> artifacts a reply produces: design documents, published pages, PR bodies […]

So headers are a violation in a reply and correct in a PR body, while the
drawing rules run the other way: `.github/pull_request_template.md` names this
skill's form-selection table as the single owner of which drawing to use. Each
function carries the rules for its own surface and neither borrows the other's.

## What a reply check can and cannot see

    Q4  a markdown header in the reply     exact       the rule forbids these outright
    r6  a counted lead-in                  by pattern  the digest names it as the tell
    Q3  length nothing asked for           a signal    length *plus* a silent prompt
    Q1  is the answer on the first line    no
    Q5  did the question want understanding no

The unobservable questions stay in the pre-send check. This catches the subset
that is visible in the text, which is also the subset that was observed
breaking — headers, counted lead-ins, and length nobody requested.

**It is not a word budget.** The skill's own rule 3 is that depth is opted into
by the words asked; a check that flagged long replies as such would contradict
the rule it enforces. Length alone is never a finding. It is a finding only
together with a prompt that asked for nothing, and the wording says so, because
a reader who reads it as a budget will disable it.
"""
from __future__ import annotations

import re
from itertools import groupby

from wfctl import _md

# Fenced blocks and table rows are drawings, not voice. Both are stripped before
# anything is scanned and before the words are counted: rule 6 exempts "a
# drawing", a fifty-line diff is not fifty lines of prose, and the skill's own
# form-selection table makes a markdown table the drawing it asks for most often
# — counting its rows made a third of the length findings fire on the shape the
# rule recommends. Fences come from `_md`; only the table rule is this module's.
_TABLE_ROW = re.compile(r"^\s*\|")

# Every level, not just `##`/`###`. The rule is "a reply is not a document — no
# markdown headers in it" (SKILL.md:410); `##` and `###` are its examples of
# document furniture, not the closed set, and `#### Findings` is the same drift
# arriving one level deeper. Indented up to three spaces, which is markdown's own
# limit — at four the line is an indented code block and not a header at all.
_HEADING = re.compile(r"^ {0,3}#{1,6}\s")

# Anywhere in the reply, not only the opening: the observed shape is a coda —
# the answer lands, then "One thing I couldn't finish:" starts a second block.
#
# The colon is the whole discriminator, and it is what separates the issue's
# own pair: `Three things worth flagging:` announces a list and flags,
# `Three reviewers reported` states a fact and does not. Anywhere in the line
# rather than at the end, because the observed lead-ins run the list on after
# the colon rather than breaking to bullets — requiring the colon to close the
# line drops two thirds of the real hits in the corpus.
_COUNTED = re.compile(
    r"^\s*(?:\*\*|_)?(one|two|three|four|five|six|seven|eight|nine|ten"
    r"|both|several|a few)\b[^\n]*:",
    re.IGNORECASE,
)

# Inline code is quoted, not written, and a colon inside it is punctuation of
# whatever is being quoted. `Two unrelated branches show `[origin/…: gone]`` is
# a sentence, not a lead-in, and it was the only false positive the rule-6 check
# produced across ninety transcripts.
# A bare URL alongside it, for the same reason and one shape further out: the
# `https:` in a line beginning "Three of these came from https://…" is not a
# lead-in's colon either.
_QUOTED = re.compile(r"`[^`]*`|\bhttps?://\S+")

# Words the prompt can use to opt into depth. Not a synonym list to be completed
# — it is deliberately over-broad, because every word missing from it turns a
# reply that *was* asked for into a false positive, and one of those teaches the
# reader to switch the check off. A missed real violation costs nothing: the
# other two findings still fire, and the reader is the backstop this always had.
#
# `?` is pointedly not here. The failure this issue was filed over is a yes/no
# question answered with a table and four paragraphs, so a question mark cannot
# be what licenses length.
#
# `plain`, `simpl\w+`, `examples?` and `pm` are the "explain it simply" row of
# rule 3 — the row that licenses the longest replies the skill permits, and the
# one this had no word from. A prompt quoting it ("in plain terms, pretend you're
# talking to a PM… Provide a simple example as well") drew a Q3 saying nothing
# had asked for depth, which is the false positive this gate exists to avoid
# (#298).
_ASKED_FOR_DEPTH = re.compile(
    r"\b(thoughts|why|explain|compare|comparison|tradeoffs?|options|opinion"
    r"|eli5|plain|simpl\w+|examples?|pm"
    r"|walk me|analys\w+|analyz\w+|detail\w*|elaborat\w+|summar\w+|review"
    r"|more questions|deep\w*|research|assess\w*|evaluat\w+)\b",
    re.IGNORECASE,
)

# ponytail: a flat count, tuned on the twenty terminal replies of the #208
# transcript — the session this was observed in. There, 250 separates the five
# replies to a bare instruction ("file an issue for X" → 259 words) from every
# reply whose prompt asked for something. It is a threshold, not a measurement:
# raise it if the check starts firing on replies that earned their length, and
# note that the gate in front of it does most of the work.
_LONG_WORDS = 250

# --- the PR-body surface ----------------------------------------------------

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
    were decided by the walk, so this cannot disagree with `_prose` about where
    a block starts.

    **An unclosed fence is a block here, and `_split_fences` dropped it.** That
    is a deliberate change, not a side effect of the walk: the old pair
    disagreed with itself, since `_prose` already treated the tail as inside a
    fence while `blocks` acted as though the fence had never opened. A truncated
    PR body is one a reader can still be told about, and telling them nothing
    because the block has no closing line is the reading that has to argue for
    itself.

    What it costs is that `body_findings` can now fire on the tail of a body cut
    off mid-block. That is the same finding it would have made had the author
    typed the closing line, which is the test for whether a change like this is
    a fix or a regression.
    """
    blocks: dict[int, list[str]] = {}
    for line in _md.walk(text):
        if line.inside and line.opened is not None:
            blocks.setdefault(line.opened, []).append(line.text)
    return sorted(blocks.items())


def _prose(text: str) -> list[str]:
    """`text` as lines, with fenced blocks and table rows removed.

    The fence delimiters go too. `_md.walk` reports them as outside — they are
    the boundary, and `_arch` prints one — but to a prose scan a bare ``` is
    neither prose nor a heading, so this filters `fence` alongside `inside`.
    """
    return [
        line.text
        for line in _md.walk(text)
        if not line.inside
        and not line.fence
        and not _TABLE_ROW.match(line.text)
    ]


def findings(reply: str, prompt: str) -> list[str]:
    """What a terminal `reply` breaks, one line each, naming the check it maps to.

    Empty when nothing is visible, which is the common case and the only one
    the caller prints nothing for.

    The wording is the point as much as the detection. Each line says which
    pre-send question the reader already agreed to and what the fix is, so it
    reads as the check they wrote rather than as a scolding from a script.
    """
    lines = _prose(reply)
    out = []

    headings = [line for line in lines if _HEADING.match(line)]
    if headings:
        out.append(
            f"Q4 — {len(headings)} markdown header(s), starting {headings[0].strip()!r}. "
            "Convert each to a bold lead-in on the sentence beneath it."
        )

    counted = [line for line in lines if _COUNTED.match(_QUOTED.sub("``", line))]
    if counted:
        first = " ".join(counted[0].split())[:60]
        out.append(
            f"rule 6 — counted lead-in: {first!r}. The answer plus at most one "
            "block, then stop; a counted lead-in is the tell."
        )

    words = len(" ".join(lines).split())
    if words >= _LONG_WORDS and not _ASKED_FOR_DEPTH.search(prompt):
        out.append(
            f"Q3 — {words} words of prose, and nothing in the prompt asked for "
            "depth. Quote the words that asked, or cut it to the answer."
        )

    return out


def body_findings(body: str) -> list[str]:
    """What a PR description's drawings break. One rule, and only one.

    SKILL.md:322 — *"Tabular content goes in a table. Columns aligned by hand
    inside a code block read as jumbled the moment one cell outgrows its header.
    Reserve ASCII for flows and timelines."* Both halves are required to fire,
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
            f"SKILL.md:322 — the fenced block at line {opened} aligns columns by "
            f"hand and holds a cell that outgrew its header: {quoted!r}. Tabular "
            "content goes in a table; reserve ASCII for flows and timelines."
        )
    return out
