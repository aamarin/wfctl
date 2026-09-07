---
status: proposed
---

# wfctl classes an action by what it reaches, and the class decides who is asked

## Context

`end-session` stops twice a session — step 5 asks before committing, step 6 asks
before touching the tracker — and never mentions pushing at all. Nobody chose
that ordering. A commit on a feature branch is the most reversible thing in the
list, and *not* committing is a documented way to lose work here (#37, #40),
while a push updates a PR others are reading and starts CI.

The three classes that would have decided it were written on #131, folded into
#127, and shipped with neither: `approval-mode-is-stored-intent` governs where
`design-levels` gates stop, which is design approval and nothing else. So the
classes are recoverable only by knowing which closed issue folded into which.

Two files already spend the vocabulary against that absence. `_pipeline.py`
justifies leaving an issue unkeyed because "creating them is outward-facing and
waits for a human"; `start-session/SKILL.md` tells the agent that "beginning
implementation is local and reversible". Both name a class the reader cannot
look up.

The harness will not supply one. Claude Code's permission rules match command
strings, and so do Gemini's, Cursor's and Copilot's — `git push` is gated if
somebody listed that string, never because of what it does.

## Direct baseline

Write the three classes into one shipped skill as prose, change nothing else,
and let `end-session` go on asking in the order it asks today. This costs one
file through the base layer every agent already receives, needs no install
machinery, and would satisfy the first acceptance criterion on #277 outright.

What it leaves is the classification unowned: a skill file states the classes,
`_pipeline.py` cites them, and nothing connects the two or decides which of the
two is wrong when they disagree.

## Decision

An action's class is decided by what the action reaches, not by which command
performs it, and how often a class fires decides how it is delivered:

| Class | What it reaches | Delivery |
|---|---|---|
| local and reversible — edit files, commit, write the summary | this worktree only; `git reset` undoes it | prose. It fires many times an hour, and a gate that frequent is answered reflexively rather than read |
| outward-facing — push, comment on an issue, open one, add a label | people who are notified, and deleting it later does not un-notify them | prose, plus a check wherever one is cheap |
| irreversible — merge, close an issue, force-push, delete a branch or worktree | history, and work that is not this agent's | always the human. No switch, not configurable |

Two constraints travel with all three. Granted authority is bounded by the
branch: nothing on `main`, under any switch. And the agent reports what it did
with the authority whether or not it was asked, because a run that committed and
pushed silently is indistinguishable from one that did nothing.

## Owns truth

wfctl owns *"what class is this action, and who has to be asked?"*.

The harness cannot compute it. Its rules match a command string against a
prefix, so the question it can answer is "did someone list this string", which
is a different question that happens to correlate. A rule of the form "anything
that notifies a watcher" has no expression in any of the five agent
configurations surveyed, and none of them special-cases a git subcommand. The
agent cannot own it either, for `wfctl-runs-the-verification`'s reason: an actor
classing its own action is making the claim the class exists to check.

Row three is owned by the human and is not delegated to wfctl at all. #100 and
#101 already hold merge authority out of the loop, and that property is what
makes relaxing the first two rows safe rather than reckless.

## Considered

- **A `permissions` block written by `install-skills`** — rejected on an
  accepted record. `install-modes` gives the consumer that half of
  `.claude/settings.json`, and `test_install_hook_merge.py` asserts the block
  survives an install byte-identical, calling that the acceptance criterion for
  the whole mode. Reversing it would buy a mechanism the agent can delete with
  the same tool it edits anything else.
- **A `PreToolUse` hook answering allow / ask / deny per call** — sound, and
  more portable than it looks: Claude Code, Codex, Gemini and Cursor have
  converged on one contract, and hook entries are the half of the settings file
  wfctl already owns. Not chosen here because it is a *consumer* of this
  boundary rather than the boundary, and a change that moves both cannot be
  reviewed as either. It is the successor work this record expects.
- **Enforcing all three classes** — rejected on frequency. Anthropic measures
  93% of Claude Code permission prompts approved, and the browser-warning
  literature puts security-warning click-through at 50–70%; a gate on row one
  trains exactly the reflex that costs row three its meaning.
- **Leaving the classes on the closed issue** — the status quo, and the reason
  two files now cite a class no reader can resolve.
- **A fourth class for "degrades security posture"**, following Auto Mode's
  categories — equally defensible, and left out because nothing in this pipeline
  reaches it. A class with no member in the work wfctl drives is a class the
  next reader has to rule out.

## Consequences

#240 is unblocked: `decompose` creates issues, which this record places in row
two, and row two now has a stated default rather than an absent one.

`end-session`'s prompts become a stated defect instead of an accident — it gates
row one and omits row two — but this record does not change them. That is its
own change, with its own argument.

Row two's delivery is deliberately unfinished. `a-rule-is-expressed-as-a-check`
asks whether a violation is visible in an artifact the work already produces,
and for "pushed without asking" it is not: the push looks identical either way.
The reporting constraint above is what makes it visible, and it is prose until
something reads it.

## Log

- 2026-09-07  proposed    — #277 level 2; the classes had no home, and two files
  were already citing them
