---
status: proposed
---

# The early spec answer is a `Needs-spec:` trailer on the branch's first commit

## Context

`every-change-answers-spec-question` decides that the `design-passes` skill asks
whether a change needs a spec before the agent writes any code, and records the
answer. This record decides where that answer goes.

The location has to meet three conditions:

1. It exists before any code is written, since that's when the decision gets
   made.
2. A reviewer can read it, so the decision isn't left to the agent alone.
3. It adds no file, since Andre ruled out a new file for every one-line fix.

## Verified

- `.github/rulesets/main.json:17` allows only merge commits, so a branch's own
  commits stay in `main`'s history after merging.
- `git log --format='%(trailers:key=Needs-spec,valueonly)'` prints one trailer
  value per commit, so a later reader, such as #382's short pipeline, can get
  the answer without parsing commit bodies.
- `wfctl arch none` writes `<arch-root>/declarations/<branch>.md`, one file per
  branch.
- The state dir is outside the repo, so nothing written there reaches a
  reviewer.

## Assumed

- The first commit on a branch lands before the code it describes. `design-passes`
  writes the test before the fix, so the first commit is a failing test, or a
  design record if there is one. If the first commit is the fix, the trailer
  records the answer after the code is written. The PR section still requires an
  answer, but neither one shows that the answer came before the code.

## Direct baseline

Don't write anything early. `design-passes` asks the question, the agent answers it
before writing code, and the PR section holds the first written answer.

## Decision

The branch's first commit carries a trailer with the answer, yes or no, plus a
one-sentence reason:

```
test(guard): a store check that fails on the main checkout

Needs-spec: no. The fix changes one check inside the worktree guard and adds no state.
```

`design-passes` adds the trailer to whichever commit comes first. Nothing
checks the trailer, since the PR section is the backstop.

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

The divider splits what lives in the repo's history from what lives only on
GitHub. The two graphs differ by one arrow. In the baseline, the answer is only
written down after the code. In the decision, `design-passes` also writes it in
the first commit. The design has to survive a session that stops partway, which
happens often when a pane restarts. In the baseline, the answer is
lost with the transcript. In the decision, it's on the branch.

## Considered

- **The direct baseline above.** It adds nothing, and the PR section still
  catches a missing answer. We didn't choose it because nothing would record
  the decision until the PR, and a session that restarts partway loses it.
- **An `arch none` declaration.** The Spec Kit design step already reads it.
  We didn't choose it because it adds a file to every branch, and it answers
  the boundary question, not the spec question.
- **The session summary in the state dir.** The agent writes it early, and it
  survives a restart. We didn't choose it because it lives outside the repo,
  so no reviewer sees it.
- **A comment on the issue.** It's posted early, and a reviewer can read it. We
  didn't choose it because it's an outward action that needs its own
  permission, it adds a comment to every issue, and it lives outside the
  repo's history.

## Consequences

The answer lives in the repo's history, so it survives a restart and outlives
the PR. The only way to add a missing trailer is to rewrite the branch's
history. That's why the check runs on the PR section, not the trailer.

## Verification

- Run `design-passes` for real on a throwaway branch. The first commit carries
  the trailer, and `git log` with the trailer format prints the answer.

## Log

- 2026-10-22  proposed  — #628: Andre asked for the spec decision to be written
  down early, before any code, without adding a file
