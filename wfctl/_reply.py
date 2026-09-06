"""Does a terminal reply violate the part of `conversation-response-shape` a
machine can see?

Pure functions over two strings — the reply and the prompt that drew it. The
caller finds them in the transcript; this decides. Same constraint as `_guard`,
for the same reason: the decision table is the part worth testing, and testing
it must not cost a session.

## Why this exists at all

The skill is already delivered three ways — a `UserPromptSubmit` hook every
turn, the rule in `SKILL.md`, a seven-question pre-send check — and all three
fire *before* the reply exists. Nothing looks at what was actually written.
`docs/architecture/the-underscore-is-the-module-contract.md` settled this shape
for module boundaries and the argument transfers whole: a correct rule with
nothing to check it gets crossed a fifth time the way it was crossed the first
four.

## What it can and cannot see

    Q4  `##` / `###` in the reply          exact       the rule forbids these outright
    r6  a counted lead-in                  by pattern  the digest names it as the tell
    Q3  length nothing asked for           a signal    length *plus* a silent prompt
    Q1  is the answer on the first line    no
    Q5  did the question want understanding no

The unobservable questions stay in the pre-send check. This catches the subset
that is visible in the text, which is also the subset that was observed
breaking — headings, counted lead-ins, and length nobody requested.

**It is not a word budget.** The skill's own rule 3 is that depth is opted into
by the words asked; a check that flagged long replies as such would contradict
the rule it enforces. Length alone is never a finding. It is a finding only
together with a prompt that asked for nothing, and the wording says so, because
a reader who reads it as a budget will disable it.
"""
from __future__ import annotations

import re

# Headings and counted lead-ins inside a fenced block are content, not voice: a
# reply quoting a SKILL.md excerpt or a `doctor` run carries both, and flagging
# them would fire hardest on the replies that did the most work. Stripped before
# anything is scanned, and before the words are counted — rule 6 exempts "a
# drawing", and a fifty-line diff is not fifty lines of prose.
_FENCE = re.compile(r"^\s*(```|~~~)", re.MULTILINE)

_HEADING = re.compile(r"^#{2,3}\s")

# Anywhere in the reply, not only the opening: the observed shape is a coda —
# the answer lands, then "One thing I couldn't finish:" starts a second block.
#
# The colon is the whole discriminator, and it is what separates the issue's
# own pair: `Three things worth flagging:` announces a list and flags,
# `Three reviewers reported` states a fact and does not. Anywhere in the line
# rather than at the end, because the observed lead-ins run the list on after
# the colon rather than breaking to bullets.
_COUNTED = re.compile(
    r"^\s*(?:\*\*|_)?(one|two|three|four|five|six|seven|eight|nine|ten"
    r"|both|several|a few)\b[^\n]*:",
    re.IGNORECASE,
)

# Words the prompt can use to opt into depth. Not a synonym list to be completed
# — it is deliberately over-broad, because every word missing from it turns a
# reply that *was* asked for into a false positive, and one of those teaches the
# reader to switch the check off. A missed real violation costs nothing: the
# other two findings still fire, and the reader is the backstop this always had.
#
# `?` is pointedly not here. The failure this issue was filed over is a yes/no
# question answered with a table and four paragraphs, so a question mark cannot
# be what licenses length.
_ASKED_FOR_DEPTH = re.compile(
    r"\b(thoughts|why|explain|compare|comparison|tradeoffs?|options|opinion"
    r"|walk me|analys\w+|analyz\w+|detail|elaborate|summar\w+|review"
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


def _prose(reply: str) -> str:
    """The reply with fenced blocks removed.

    Split on the fence markers, keep every fourth piece — `re.split` with one
    capturing group yields text, marker, text, marker, so the pieces outside a
    block land four apart. Preferred over matching fence pairs because an
    unclosed fence, which is what a reply cut off mid-block leaves, then drops
    its tail rather than matching nothing and scanning the code as prose.
    """
    return "".join(_FENCE.split(reply)[::4])


def findings(reply: str, prompt: str) -> list[str]:
    """What `reply` breaks, one line each, each naming the check it maps to.

    Empty when nothing is visible, which is the common case and the only one
    the caller prints nothing for.

    The wording is the point as much as the detection. Each line says which
    pre-send question the reader already agreed to and what the fix is, so it
    reads as the check they wrote rather than as a scolding from a script.
    """
    prose = _prose(reply)
    lines = prose.splitlines()
    out = []

    headings = [line for line in lines if _HEADING.match(line)]
    if headings:
        out.append(
            f"Q4 — {len(headings)} markdown heading(s), starting {headings[0].strip()!r}. "
            "Convert each to a bold lead-in on the sentence beneath it."
        )

    counted = [line for line in lines if _COUNTED.match(line)]
    if counted:
        first = " ".join(counted[0].split())[:60]
        out.append(
            f"rule 6 — counted lead-in: {first!r}. The answer plus at most one "
            "block, then stop; a counted lead-in is the tell."
        )

    words = len(prose.split())
    if words >= _LONG_WORDS and not _ASKED_FOR_DEPTH.search(prompt):
        out.append(
            f"Q3 — {words} words of prose, and nothing in the prompt asked for "
            "depth. Quote the words that asked, or cut it to the answer."
        )

    return out
