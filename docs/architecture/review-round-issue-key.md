---
status: proposed
diagram: data-flow
---

# wfctl counts review rounds by issue, not by branch name

## Context

`review-round-count.md` makes wfctl count each group's review rounds, so an agent
that reaches the cap needs a person's sign-off to continue. Currently, wfctl
keeps those counts in the branch's state folder, which is named after the full
branch name, such as `626-review-round-cap`. The same folder holds the last
reviewed commit and the sign-off.

When an agent runs `git branch -m 626-round-cap`, wfctl looks for a state folder
under the new name and finds none. The count starts again at zero, and the agent
gets three more rounds without anyone being asked. A rename is an ordinary git
command that leaves no sign it was used to get past the cap. A person who
renames a branch to shorten its name loses a sign-off in the same way.

## Direct baseline

Leave the state folder keyed by branch name and accept that a rename resets the
count. This requires no code changes. However, it leaves the round cap open to
anyone who runs `git branch -m`, and that is the case the cap exists to stop in
an unattended run.

## Decision

wfctl keeps each review group's run records, its last reviewed commit, and the
sign-off in a folder named after the issue the branch names, not the branch. A
branch that names no issue, such as `main`, keeps the folder named after the
branch. A `WFCTL_STATE_DIR` override still pins one folder for every branch.

Two branches that name the same issue share one folder. This means a stacked PR
with a different slug starts with the rounds the first branch used. The user
signs off to continue past the cap.

The event log and the session handoff stay in the branch's own folder. Runs
recorded under a branch folder before this change are not read, so each branch
starts its count again once. wfctl has one user right now, so we accept this
cost while that holds.

## Owns truth

wfctl owns "how many rounds has this change used, and has a person signed off
on it?". The answer is kept under the issue key, which wfctl takes from the
branch name using the repository's `key_pattern`.

The agent cannot own it, because the agent controls the branch name. A count
keyed on something the agent can change with one git command is a count the
agent can reset.

## Boundary

```mermaid
flowchart TB
  subgraph agent["agent"]
    rename["git branch -m"]
    start["wfctl review start"]
  end
  subgraph wfctl
    key["issue key from the branch name"]
    issue[("review runs, last reviewed commit, sign-off<br/>one folder per issue")]
    branch[("event log and handoff<br/>one folder per branch")]
    count["count the runs the group has started"]
    nokey["branch names no issue: use the branch folder"]
  end

  rename --> key
  start --> key
  key -- "issue found" --> count
  key -- "no issue" --> nokey
  issue -.-> count
  nokey -.-> count
  count -- "events" --> branch
  agent -- "a new branch name means a new count" --x wfctl
```

A solid arrow is a direct call, a dotted arrow is a file wfctl reads later, and
an arrow ending in x is a claim wfctl doesn't accept from the agent.

## Considered

- Give each branch its own count, as described in the direct baseline for
  branches that share an issue. We didn't choose this because a new branch on
  the same issue would then be another way past the cap, and the cap exists to
  limit the rounds on one change.
- Move the whole state folder to the issue key. We didn't choose this because
  the folder also holds the session handoff and the event log, and `wfctl start`
  already derives those from the branch. Moving them changes more than the bug
  needs.
- Notice a rename and move the folder to the new name. We didn't choose this
  because wfctl would have to detect the rename, and git doesn't record one. A
  new branch with a copied name would be another case to handle.
- Carry the old branch folders forward the first time they are read. We didn't
  choose this because it adds a second place that reads state wfctl no longer
  writes, and the cost it avoids is one reset for a single user.

## Consequences

- A stacked PR for an issue starts with the rounds an earlier branch on that
  issue used. The user signs off to continue.
- The cap refusal says the group ran its rounds "on this branch". For a second
  branch on the same issue that is no longer exact, and the wording is left for
  a follow-up.
- The count stays tamper-evident, not unforgeable, as `review-round-count.md`
  already accepts. An agent can still rename a branch to name a different issue
  number, or delete the run records.

## Log

- 2026-10-27  proposed    — #666 level 2, after Andre chose one count per issue shared by every branch that names it
