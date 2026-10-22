---
status: proposed
---

# The early spec answer is a `Needs-spec:` trailer on the branch's first commit

## Context

`every-change-answers-spec-question` decides that the `design-passes` skill asks
whether a change needs a spec before any code is written, and records the answer.
This record decides where that answer is written.

The location has to meet three conditions:

1. It exists before the code does, since the early answer is where the decision
   is made.
2. A reviewer can read it, so the decision isn't left to the agent alone.
3. It adds no file, since Andre ruled out a file on every one-line fix.

## Verified

- `.github/rulesets/main.json:17` allows only merge commits, so a branch's own
  commits stay in `main`'s history after it merges.
- `git log --format='%(trailers:key=Needs-spec,valueonly)'` reads one trailer
  key from each commit, so a later reader, such as #382's short pipeline, can
  read the answer without parsing commit bodies.
- `wfctl arch none` writes `<arch-root>/declarations/<branch>.md`, a file per
  branch.
- The state dir is outside the repository, so nothing written there reaches a
  reviewer.

## Assumed

- The first commit on a branch comes before the code it describes. `design-passes`
  orders the test before the fix, so the first commit is a failing test, or a
  design record when one was written. A branch whose first commit is the fix
  would carry the answer after the code, which the late section still catches.

## Direct baseline

Write nothing early. `design-passes` asks the question, the agent answers it
before writing code, and the first written answer is the pull request section.

## Decision

The branch's first commit carries a trailer stating the answer, with yes or no
and one sentence of reasoning:

```
test(guard): a store check that fails on the main checkout

Needs-spec: no. The fix changes one check inside the worktree guard and adds no state.
```

`design-passes` writes the trailer on whichever commit comes first. Nothing
checks it, because the pull request section is the backstop.

## Diagram

```
               baseline                                  decision

stable   ┌──────────────────────────┐         ┌──────────────────────────┐
         │ design-passes            │         │ design-passes            │
         │ asks the question        │         │ asks the question        │
         └────────────┬─────────────┘         └──────┬────────────┬──────┘
                      │ writes, after the code       │ writes     │ writes, before the code
                      │                              │            ▼
                      │                              │     ┌────────────────────┐
                      │                              │     │ first commit's     │
                      │                              │     │ trailer (new)      │
                      │                              │     └────────────────────┘
════ in the repository / on GitHub ══════════════════╪═════════════════════════════
                      │                              │
volatile ┌────────────▼─────────────┐         ┌──────▼──────┐
         │ PR section               │         │ PR section  │
         └──────────────────────────┘         └─────────────┘
```

The divider separates what lives in the repository's history from what lives
only on GitHub. The two graphs differ by one arrow. In the
baseline, the only written answer comes after the code. In the decision, one
answer is written with the first commit. The change this is built to absorb is a
session that stops partway, which is common when a pane restarts. In the
baseline, the answer is lost with the transcript. In the decision, it is on the
branch.

## Considered

- **The direct baseline above.** It adds nothing and the pull request section
  still catches a missing answer. We didn't choose it because the decision
  would leave no trace until the pull request, and a session that restarts
  partway loses it.
- **An `arch none` declaration.** It is the mechanism the Spec Kit design step
  already reads. We didn't choose it because it is a file on every branch, and
  it answers the boundary question rather than the spec question.
- **The session summary in the state dir.** It is written early and survives a
  restart. We didn't choose it because it lives outside the repository, so no
  reviewer reads it.
- **A comment on the issue.** It is early and a reviewer can read it. We didn't
  choose it because it is an outward action that needs its own permission, it
  adds a comment to every issue, and it lives outside the repository's history.

## Consequences

The answer lives in the history, so it survives a restart and outlives the pull
request. A missing trailer can be added only by rewriting the branch's history,
which is why the pull request section, not the trailer, is the one that fails.

## Verification

- A real run of `design-passes` on a throwaway branch, where the first commit
  carries the trailer and `git log` with the trailer format prints the answer.

## Log

- 2026-10-22  proposed  — #628: Andre asked for the spec decision to be written
  down early, before any code, without adding a file
