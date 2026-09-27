---
status: proposed
diagram: state
---

# An unattended run goes as far as it can and stops only on a named stop condition

## Context

`auto_approve` is one switch, and its intent is that a run performs the whole
workflow unattended, makes its own decisions, and records the trade-offs for a
reviewer at the pull request (`approval-mode-is-stored-intent`). What that
intent has never had is the other half: a stated list of the conditions under
which the run stops anyway, because only a person can move it.

The list exists in the code without being named as one. `attention` reports three
kinds (`wfctl-owns-whether-a-worktree-wants-a-human`), and each was added for its
own reason:

1. `blocked`, when the host refused an outward action and only a person can take
   it.
2. `manual`, when the outstanding pass is one a person performs.
3. `stalled`, when a step was repeated with its evidence unchanged.

Plan defense (#500) needs a fourth. Under `auto_approve` a challenge found
`REVISION_REQUIRED` sends the agent back to `plan`, and the defense runs again
(`unattended-answers-using-evidence`). Each round rewrites
`plan.md`, so the evidence differs every time and `stalled` never fires. The loop
has no end.

Adding a fourth kind the way the first three were added would work. What it would
not do is tell a reader, or a repository deciding how much to trust an
unattended run, what the complete set of stops is and which of them they may
change.

## Direct baseline

Add the defense cap as a fourth `attention` kind, with its own override, and
state no rule about the list. It is one new kind, one new config key, and no new
concept.

It answers #500 and leaves the question one level up where it is. The next
condition is added for its own reason again, the override for it lands under
whatever key its author picks, and a repository wanting to know "when will an
unattended run stop and wait for me?" reads four records and the code to find
out.

## Decision

An unattended run proceeds until a stop condition holds, and then it stops and
reports that condition in `attention`. Stop conditions are a closed, named list
that wfctl owns. Nothing outside the list stops an unattended run, and a question
only a person can answer that is not on the list goes to the reviewer at the pull
request instead.

Each stop condition has a default handling, and the list says which of them a
repository may prescribe differently. A repository does so in `wfctl.json` under
`stop_conditions`, keyed by the condition's name. #500 adds the first
prescribable one:

| Stop condition | Why the run stops | Default | Prescribable |
|---|---|---|---|
| `blocked` | the host refused an outward action | stop | no, the host's permission layer decides |
| `manual` | the outstanding pass is one a person performs | stop | by declaring the pass or not |
| `stalled` | a step repeated with its evidence unchanged | stop | not yet |
| defense rounds | plan defense returned `REVISION_REQUIRED` at the cap | stop at 3 rounds | yes, `stop_conditions.defense_rounds` |

Merging, force-pushing, closing an issue, and deleting a branch are not on the
list, because wfctl never performs them in any mode. They are not stops a run
reaches; they are actions a run does not take.

The defense cap stops the run rather than advancing to `tasks` with the remaining
revisions deferred. A plan the agent itself judged wrong three times is the
wrong foundation for tasks, and the stop is the same kind `stalled` already
produces.

## Owns truth

wfctl owns "must this unattended run stop now, and on which condition?".

The agent cannot compute it, for two reasons. The agent is the party with a
reason to keep going, so a stop it decides for itself is a self-report, which
`wfctl-runs-the-verification` removes from the agent's side for the same reason
here. And two of the conditions are counts that have to outlive the agent's
memory: a run long enough to stall or to revise its plan three times is one whose
conversation is cleared or compacted partway, and an agent's tally resets to zero
at the moment the bound should fire (`wfctl-counts-the-passes`). wfctl reads the
count from disk on every report.

The repository owns "how should this condition be handled here?", for the
conditions the list marks prescribable. wfctl cannot compute it, because the
answer is a repository's tolerance for unattended work, and a default is only
the answer for a repository that has not said otherwise.

## Boundary

```mermaid
stateDiagram-v2
    [*] --> running
    running --> running: no stop condition holds
    running --> deferred_to_reviewer: a question only a person answers, not on the list
    deferred_to_reviewer --> running
    running --> stopped: a stop condition holds
    stopped --> running: a person acts, or the repository prescribes otherwise
    running --> [*]: story complete, pull request for the reviewer
```

The edge into `stopped` is the decision. wfctl takes it from its own reading of
the list, and nothing the agent reports moves the run along that edge or keeps it
off it. The edge into `deferred_to_reviewer` is the other half: a question that
needs a person but is not a stop condition does not stop the run.

## Considered

- **The direct baseline above**, a fourth kind with no rule about the list. It
  is the smallest change and answers #500, and it leaves the set of stops
  discoverable only by reading every record that added one.
- **An agent that counts its own rounds**, in `speckit-orchestrate`'s
  conversation. It is sound while the conversation lasts and loses the count
  when a run is long enough to need one, the argument `wfctl-counts-the-passes`
  already made.
- **At the defense cap, defer the remaining revisions and advance to `tasks`.**
  It keeps the run going, and it builds tasks on a plan the agent has already
  said must change. Stopping costs one person's attention, and advancing costs
  every task written against the wrong plan.
- **Widen `stalled` to cover the defense loop.** A stall means re-entering
  changed nothing, and here re-entering changes the plan every time. One kind
  meaning two things is the silent contract change
  `wfctl-owns-whether-a-worktree-wants-a-human` warns against.
- **Every condition prescribable now**, a stall bound and a way to turn any
  pass into a hard stop among them. It is where the list is heading, and no
  repository has asked for any of it yet. The list names which conditions are
  prescribable so that adding one is a row, not a redesign.
- **Rename `attention` to `stop_condition` in the payload.** The concept's name
  would match the field's, and the field is part of the versioned `status
  --json` contract, so every consumer breaks for a word. A stop condition is
  reported in `attention`, and this record is where that is said.

## Consequences

`wfctl-owns-whether-a-worktree-wants-a-human` is extended, not superseded. Its
three kinds are this list's first three rows, and its rank of `blocked`, then
`manual`, then `stalled` still decides which condition `attention` shows when
two hold. Where the defense cap ranks, and the `attention` kind it is reported
under, are level-3 decisions, and either is a contract change that moves the
payload version.

What the defense round count is read from is a level-3 decision. It has to be
readable by wfctl on every report without trusting a number the agent wrote.

`wfctl check config` validates `stop_conditions` the way it validates `steps`: an
unknown condition name, or a value for a condition the list does not mark
prescribable, is a finding rather than a silent drop.

An attended run reaches the defense cap only if a person answered
`REVISION_REQUIRED` three times, since each attended revision already routes to
`/speckit.plan` with `auto: false`. The conditions apply in both modes, and they
matter unattended.

## Log

- 2026-09-26  proposed    — #500 level 2: plan defense adds a stop to unattended
  runs, and the stops had no list a repository could read or prescribe against
