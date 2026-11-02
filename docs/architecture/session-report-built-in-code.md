---
status: proposed
diagram: data-flow
governs: session-continuity, agent-host
---

# wfctl builds the session-start report for the skill

## Context

`/start-session` is how an agent recovers its context at the start of a
session. Currently, the skill's instructions tell the agent to run ten
commands one at a time and write the report itself: `wfctl start`, `doctor`,
`arch context`, `status --json`, a read of the handoff, a grep of the event log,
`git log` and `git status`, and then `wfctl issue list` and `wfctl change list`.
The agent then checks the branch's commits against every open issue.

In this repository, a session that runs `/start-session` holds 19.2k more
tokens of context than one that only replies to a one-word prompt, measured on
2026-11-01. The instructions account for 8.4k of that, since
`start-session/SKILL.md` grew from 15.8 KB to 25.2 KB without anyone noticing.
Most of the rest is repository-wide context.

Previously, the tracker was Linear, and a session had to rebuild the picture of
all open work itself. Currently, each worktree exists for one issue, and GitHub
holds the epics. As a result, the open issue and PR lists are rarely used in a
worktree. Sessions on the `main` checkout are usually exploratory and not tied
to one issue, so a list loaded before anyone asks for it is often not used
there either.

The user decided on 2026-11-01 that session start loads no repository-wide
list in either place. A worktree session loads its own issue, the issue's
parent epic, and the branch's open PR. A `main` session loads none of those,
and the agent runs `wfctl issue list` or `wfctl change list` when the
conversation needs one.

## Direct baseline

Edit the skill's instructions. Remove the steps that run the issue and PR
lists, add a step that runs `wfctl issue view` for the branch's issue, and move
the doctor repair guidance to a reference file the agent opens only when
`doctor` reports a finding. The agent still runs each command and writes the
report.

This meets the token target. However, the rule about what to load stays in the
instructions, and an agent can follow an older installed copy, skip a step, or
add one back. When it does, the only trace is in a transcript nobody reads.
This is the problem in `a-rule-is-expressed-as-a-check.md`, where a
rule is broken and no artifact shows it. That's why the decision below moves
the rule into wfctl.

## Decision

One wfctl command builds the session-start report. It reads the branch, the
pipeline position, the handoff, the commits, and the tracker, and prints the
finished report. In a worktree whose branch names an issue, the report carries
that issue, its parent epic, and the branch's open PR. On a branch that names
no issue, it carries none of the three. The skill runs that command, reports
what it printed, and decides what to do next with the step 8 table, which is
unchanged.

## Owns truth

wfctl decides which context a session on this branch starts with.

The agent shouldn't decide this, for two reasons.

1. The instructions are the agent's only copy of the rule, and the agent is the
   party the rule constrains. If the agent loads the issue list anyway, its
   report is its own account of what it loaded, and nothing outside the
   transcript records it. When wfctl prints the report, the agent runs no list
   command at session start, so it has no rule left to break.
2. Each instruction the agent has to follow costs tokens on every session,
   including the ones where it changes nothing. A rule in wfctl's code costs
   nothing until it prints a line.

The agent still decides what happens next. The step 8 decision uses the report
to choose between starting work and asking what to work on. It stays in the
skill because it depends on the conversation, which wfctl can't see.

## Boundary

```mermaid
flowchart LR
    subgraph agent["agent, running /start-session"]
        direction TB
        RUN["runs the report command"]
        READ["reads the report"]
        DECIDE["step 8: start work or ask"]
        ONDEMAND["runs wfctl issue list or<br>wfctl change list<br>only when the conversation asks"]
    end
    subgraph wfctl["wfctl"]
        direction TB
        BRANCH{"branch names an issue?"}
        LOCAL["pipeline position, handoff,<br>commits, uncommitted changes"]
        ISSUE["the issue, its parent epic,<br>the branch's open PR"]
        REPORT["the session-start report"]
    end
    subgraph disk["state dir and git"]
        STATE["session-summary.md, events.jsonl,<br>commits"]
    end
    subgraph tracker["tracker backend"]
        TRACK["issue, parent, change"]
    end
    RUN --> BRANCH
    BRANCH -- "yes: worktree" --> ISSUE
    BRANCH -- "no: main checkout" --> LOCAL
    ISSUE --> LOCAL
    ISSUE --> TRACK
    STATE -.-> LOCAL
    LOCAL --> REPORT
    REPORT --> READ
    READ --> DECIDE
    ONDEMAND -- "later, when the conversation asks" --> TRACK
    agent -- "the open issue and PR lists" --x REPORT
```

The `--x` edge is the decision. The report never carries the repository-wide
lists, whichever branch it runs on, and the agent loads them only when the
conversation asks for them. A dotted edge is a file wfctl reads from disk, and
a solid edge is a call.

## Considered

- **Edit the instructions only (the direct baseline).** We didn't choose this
  because the rule about what to load stays in prose, and a skipped or
  reordered step leaves no trace outside the transcript. It also cuts fewer
  tokens, since the agent still reads instructions for every command it runs.
- **Keep the repository-wide view on the `main` checkout, with the open
  issues ranked rather than cut off at the tracker's first 20 (#296).** This was the plan in #432 until 2026-11-01. We didn't
  choose this because sessions on `main` are usually exploratory, so a list
  loaded before anyone asks for it is often not used. When it is needed, the
  agent can run it in one command.
- **Add the issue lines to `wfctl status --json` and have the skill read
  that.** This would work, and `status` already carries the pipeline position.
  We didn't choose this because `status` runs on every pipeline step and in the
  supervisory screen. A tracker call there would add network time to every
  command that reads status, not only to session start.

## Consequences

wfctl needs two new tracker reads, for an issue's parent and for the
branch's open PR with its check state. Who owns them is decided in
`backend-tracker-reads-parent-and-change.md`.

`start-session/SKILL.md` now only runs one command, reports its output, and
keeps the step 8 table. The doctor repair guidance moves to a reference file
the agent opens only when `doctor` reports a finding. A test fails when the
skill grows past a size limit, because the growth from 15.8 KB to
25.2 KB went unnoticed.

`/start-session` makes the same decisions as before. The step 8 table, the
doctor repair policy, and the freshness rules stay the same.

## Log

- 2026-11-01  proposed    — #432 cuts session start to the branch's own context
