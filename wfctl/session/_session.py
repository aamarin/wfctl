"""The handoff a session leaves for the next one, and the caller's identity.

What a session file holds is what re-derivation cannot reach. Everything else —
the issue, the branch, the pipeline step, the next command, when it last moved —
is computed from artifacts on every read, so nothing here caches a conclusion
about it (`session-state-is-re-derived`).

The event log and the approval mode belong to evidence, which the domain page
gives them to, so who holds the branch, whether a session started, and the
blocks an agent reported are read from `wfctl.evidence`. What stays here is the
handoff, and which host variable carries the caller's identity.
"""
from __future__ import annotations

from collections.abc import Mapping
from datetime import datetime, timezone
from pathlib import Path
from typing import NamedTuple

from wfctl._io import append_event, write_atomic
from wfctl.evidence import identity


class Observations(NamedTuple):
    """What `end` could see at the moment it ran. No conclusion among them.

    Each field is a reading, not a verdict: where the pipeline stands, whether
    the boundary question was answered, whether the tree has uncommitted work.
    "Complete" is not here because it is not observable — that is #70.
    """

    step: str
    boundary: str
    tree: str


def _now_utc() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


# Each agent's own session variable, keyed by the name a developer puts in
# `WFCTL_AGENT` (`session-identity-from-named-agent`). An entry is added only once
# someone has measured what that host exports to a shell. A misspelled name only
# leaves the holder `unknown`, but a variable that holds something other than the
# conversation's id gives a wrong holder. Codex and Copilot are absent until
# someone repeats the 2026-09-13 measurement against a current release of each.
AGENT_SESSION_VARIABLES = {
    "claude": "CLAUDE_CODE_SESSION_ID",
}


def presented_identity(
    presented: str | None, environ: Mapping[str, str]
) -> str | None:
    """The caller's identity: what it presented, else its agent's own variable.

    `presented` is `--session-id` or `WFCTL_SESSION_ID`, already merged by the
    caller, so the agent's variable is only ever the last resort. A blank value at
    either step reads as absent and falls through, for the reason `identity`
    gives. The agent comes from `WFCTL_AGENT` and from nowhere else: a nested
    agent carries its parent's variable beside its own, so checking which
    variables are set would let the lookup order pick the conversation.
    """
    caller = identity(presented)
    if caller is not None:
        return caller
    variable = AGENT_SESSION_VARIABLES.get(environ.get("WFCTL_AGENT", ""))
    return identity(environ.get(variable)) if variable else None


# The two halves of the handoff's next-action section, named once. `end`
# recognises an unfilled section by them and the template writes it from them,
# so the two cannot drift apart into a warning that never fires.
NEXT_SESSION_TODO = "## Next Session TODO"
NEXT_ACTION_PLACEHOLDER = "- [ ] (fill in)"

# The section holding what the session was in the middle of. It is rendered here
# rather than left to `end-session`'s prose because this is the file an
# unattended restart edits: a section already present as a placeholder is a slot,
# and an instruction to add one is a step that gets skipped under exactly the
# context pressure that fired the restart (#397).
#
# Above `NEXT_SESSION_TODO` for reading order and to match step 4's template: the
# request that was cut off is context for the instruction below it. Not for
# safety — `names_no_first_action` breaks on the first `## `, so this section
# could sit either side of that heading without reaching its scan.
IN_FLIGHT = "## In Flight"
IN_FLIGHT_PLACEHOLDER = "- (fill in)"


def in_flight_unfilled(summary: str) -> bool:
    """Was this handoff's in-flight section left as the template wrote it?

    `a-rule-is-expressed-as-a-check`: a violation of "fill this in" is visible in
    `session-summary.md`, which the work already produces, so the rule is a check
    over that artifact or it is the rule's absence documented. `end-session`'s
    prose states it; this is what observes it.

    **It cannot fire where the rule binds, and that is the point.** `end` writes
    the scaffold at step 3 and the agent fills it at step 4, so every reader
    inside `end` — the `--continued` warning included — sees the placeholder on
    every run by construction and can say nothing about what came after. The
    reader that runs on the far side is `wfctl start`, in the session the restart
    spawned, which is why the warning lands there and reads as a report on the
    session before rather than a nudge to the one being closed.

    So what this buys is not prevention. It is that a request dropped under
    context pressure stops being silent: today an agent that skips the section
    leaves nobody who knows it was ever asked, and `/start-session` suppresses
    the placeholder rather than reporting it as a request nobody made. Holding
    the restart until the section is filled would prevent it, and that is
    `_restart.py`'s to do (#425); the two compose, and this stops firing when it
    lands.

    `_TEMPLATE_MARK` first, for `names_no_first_action`'s reason: a `worktree-handoff`
    document uses its own shape and never carries this section, so a file `end`
    did not write is not judged at all rather than judged absent.
    """
    if _TEMPLATE_MARK not in summary or IN_FLIGHT not in summary:
        return False
    body = summary[summary.index(IN_FLIGHT) + len(IN_FLIGHT) :]
    # To the next heading, so a section someone filled in *below* this one does
    # not answer for it — the same bound `names_no_first_action` walks.
    for line in body.splitlines():
        if line.startswith("## "):
            break
        stripped = line.strip()
        if stripped and stripped != IN_FLIGHT_PLACEHOLDER:
            return False
    return True

# The line that says `end` wrote this file: the title `_render_session_summary`
# opens with, which `end-session`'s own fill-in template repeats verbatim.
#
# Not `**Step**:`, which this was first and is too weak to carry it. That is an
# ordinary label, so a handoff reporting its own pipeline position under the same
# word reads as a summary `end` wrote — and since `worktree-handoff` forbids a
# `## Next Session TODO`, the false warning this mark exists to prevent comes
# straight back. A document has to title itself a session summary to collide
# with this one.
_TEMPLATE_MARK = "# Session Summary:"


def _render_session_summary(branch: str, observed: Observations) -> str:
    """The handoff, headed by what `end` could see rather than what it hoped.

    `**Status**: complete` used to sit here. Nothing observed it — `end` wrote
    the word on every run, including one that closed a session with half the
    tasks open and a dirty tree (#70). What replaces it is three facts and no
    conclusion drawn from them; the reader draws their own, which is the whole
    difference.

    Prose below stays as it is. A handoff whose sections were never filled in
    must read as unfilled, and nothing above them may claim otherwise.
    """
    now = _now_utc()
    return (
        f"# Session Summary: {now[:10]} — {branch}\n\n"
        f"**End**: {now}\n"
        f"**Step**: {observed.step}\n"
        f"**Boundary**: {observed.boundary}\n"
        f"**Tree**: {observed.tree}\n\n"
        f"## What We Accomplished\n\n"
        f"- (fill in)\n\n"
        f"{IN_FLIGHT}\n\n"
        f"{IN_FLIGHT_PLACEHOLDER}\n\n"
        f"{NEXT_SESSION_TODO}\n\n"
        f"{NEXT_ACTION_PLACEHOLDER}\n"
    )


def names_no_first_action(summary: str) -> bool:
    """Is this handoff's next-action section still the template's?

    Beside the renderer above and reading the same constants, because the only
    thing that can recognise the placeholder is whatever writes it. A copy of the
    literal in the command that prints the warning would go on matching the old
    text after the template moved on, and the warning would die with nothing
    going red.

    The question is narrow on purpose: whether the section was *ever filled in*,
    not whether what fills it names a usable first action. The second is step 8's
    judgment — its gate is quoting a literal sentence — and `end` has no way to
    reach it. Answering the narrow one is what lets `end` speak at the last
    moment the operator is still there to fix it (FR-013).

    **A file `end` did not write is not judged at all**, and a missing section is
    the case that turns on it. `worktree-handoff` tells handoff authors in as
    many words not to add a `Next Session TODO` — the sentence it can quote goes
    in that document's own shape — so reading "no section" as "no first action"
    warns on every fresh worktree, which is #352's own scenario and the one place
    the handoff is most likely to be complete. `_TEMPLATE_MARK` is the title
    `end` writes and `end-session` repeats, which no handoff carries by accident.
    """
    if _TEMPLATE_MARK not in summary:
        return False
    if NEXT_SESSION_TODO not in summary:
        return True
    body = summary[summary.index(NEXT_SESSION_TODO) + len(NEXT_SESSION_TODO) :]
    # To the next heading, so a section someone filled in *below* this one does
    # not answer for it.
    for line in body.splitlines():
        if line.startswith("## "):
            break
        stripped = line.strip()
        if stripped and stripped != NEXT_ACTION_PLACEHOLDER:
            return False
    return True


def end(
    agent_dir: Path, branch: str, observed: Observations, *, continued: bool
) -> tuple[Path, bool]:
    """Write session-summary.md if absent; return its path and whether it wrote.

    The observations are passed in rather than taken here: the caller has
    already built the report, and a second inference is a second chance to
    disagree with the line it is about to print.

    `continued` says whether the work carries on, and it is the caller's to
    declare — keyword-only and with no default, so a call site that has not
    thought about it does not compile rather than quietly recording a wrap-up.
    `end` cannot conclude it: `**Status**: complete` was written on every run
    including one that closed with half the tasks open, and #70 removed it
    because nothing observed the word. What `end` can observe is that it was
    told, and that is the whole of what goes in the log.

    Written once. A second `end` must not overwrite prose a human or agent
    filled in between the two.

    The flag is returned because only this function knows which of the two
    happened, and the caller reports it. Whether the file was written is not
    re-derivable afterwards: the kept file and a freshly written one are both
    just a `session-summary.md` sitting there, and the mtime cannot separate
    them either — `worktree-handoff` copies a handoff in after the branch's
    first `start` event, so "older than the session" classifies a handoff as
    stale (#239).
    """
    summary_file = agent_dir / "session-summary.md"
    written = not summary_file.exists()
    if written:
        write_atomic(summary_file, _render_session_summary(branch, observed))

    append_event(
        agent_dir, "end", branch=branch, step=observed.step, continued=continued
    )
    return summary_file, written
