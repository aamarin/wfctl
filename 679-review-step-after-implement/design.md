# Review becomes a pipeline step after implement

Contexts: evidence-and-derivation, design-method

## Problem Statement

How might we make `wfctl status` keep a branch open until every review group
has reviewed its newest commit, for branches that run the spec pipeline and for
branches that skip it?

Once implement finishes, `wfctl status` reports the story complete and names no
next command, so the review panel runs only when someone remembers it. On pfms
#919, every step read done and the panel ran only because the user asked. The
PR guard is the only place wfctl enforces the panel, and it blocks `gh pr
create` after the work has already been reported finished.

A branch that skips the spec has the same gap one step earlier. Nothing records
whether anyone asked if it needs a spec, and `wfctl status` points every branch
without a spec folder at brainstorm.

## Recommended Direction

wfctl adds `review` as a ninth built-in step, after `implement`. The step is
done when every required review group has reviewed HEAD, or a person's sign-off
covers it. wfctl reads that from the files the PR guard reads, through one
function both of them call, so `wfctl status` and the guard always give the
same answer. The agent can run the panel but can't mark review done: only
`wfctl review check` records a run complete, and only a person at a terminal
signs off.

Every branch answers whether it needs a spec before any code, using three spec questions
that step 1 of the `design-passes` skill lays out with their sources. The
change needs a spec when it alters behavior or adds persistent state, makes an
architecturally significant decision that is expensive to reverse, or moves
ownership. A "yes" runs the pipeline and writes nothing. A "no" is recorded
with `wfctl spec none --reason "…"`, which writes `exceptions/spec.md` in the
spec folder. The pipeline then reads the seven spec rows as skipped, sends the
branch to `implement`, judged by `wfctl verify` alone, and then to `review`.
`/start-session` asks the question on any issue branch with no spec folder.

Keeping review reports after the worktree is removed (#679 item 3) needs no
code. The git notes carry only "reviewed by <group>", but the full reports are
in the state dir under `reviews/<group>/runs/NNN/`, and nothing deletes the
state dir when a worktree is removed. They survive on the machine, not off it.

## What the user sees (level 1)

Approved by Andre on 2026-10-31 ("the states look right").

After implement, before any review:

```
implement    ●
  store-specs       ●
review       ▶  ← current
                security, code: not reviewed yet
next: /fanning-out-code-review
```

Every group has reviewed HEAD:

```
review       ●
Story complete. Open PR or run /end-session.
```

One more commit after that. The commit stales the verify record too, so verify
comes first and review follows:

```
implement    ▶  ← current
                stale — verified at 3f2a1c9, HEAD is 8d04e17
review       ○
next: wfctl verify
```

Then, once verified:

```
review       ▶  ← current
                security, code: 1 commit unreviewed since 3f2a1c9
next: /fanning-out-code-review
```

A branch that recorded "no spec":

```
brainstorm … decompose   –  skipped: no spec
implement    ▶  ← current
                unverified — run `wfctl verify`
review       ○
```

A branch nobody has asked yet, with no spec folder:

```
brainstorm   ○  ← current
next: /speckit.brainstorm
  or, if it needs no spec: wfctl spec none --reason "…"
```

Planning added the commit count to `not reviewed yet`, as `not reviewed yet (4 commits)`, so every group's line says how much is left.

Planning dropped the `or, if it needs no spec` hint (research R11). `/start-session` and `design-passes` step 1 ask the spec question before any code, and a hint on every new branch would offer the skip without the three spec questions.

Other states, each with its own string:

1. A review config that can't be read leaves `review` at `▶` with the config
   error as its reason, never `●`. The guard refuses on the same error.
2. `review.rounds` of 0, or a group that has used all its rounds, leaves
   `review` at `▶` until a person signs off, and stops an unattended run.
3. A branch with both `exceptions/spec.md` and a spec artifact runs the full
   pipeline and prints a warning naming the stale file to delete.

Verify reruns the repo's whole definition of done at the new HEAD. Review
covers only the commits since each group last reviewed.

## Decisions

| # | Level | Decision |
|---|---|---|
| 1 | behavior | review is a step after implement; a commit after review reopens verify, then review |
| 2 | behavior | an unanswered branch runs the full pipeline; only a "no" writes a file |
| 3 | architecture | status reads the guard's local files through the guard's function, not git notes |
| 4 | architecture | a "no spec" is written to the spec folder before code and to the PR body |
| 5 | method | three spec questions decide the spec question; a moved boundary means yes |
| 6 | design | review is a ninth row, not a pass under implement |
| 7 | design | one `spec_step` flag on the table skips the seven spec rows |
| 8 | behavior | item 3 needs no code; reports survive in the state dir |

## Architecture decisions

- docs/architecture/review-step-reads-guard-state.md — the review step reads
  the same files and function as the PR guard (new, proposed)
- docs/architecture/every-change-answers-spec-question.md — a "no spec" is
  recorded before code, and three spec questions define the line (revised, proposed)

## Software design decisions

- docs/architecture/design/679-review-is-its-own-step.md — review is a ninth step, and the guard and status share one `_review` function
- docs/architecture/design/679-no-spec-skips-spec-rows.md — one `spec_step` flag on the step table skips the spec rows for a no-spec branch

The design-method context makes no structural choice: its changes are skill
prose, recorded with `wfctl step none brainstorm.software-design --context
design-method` in `exceptions/design-method/brainstorm.software-design.md` in
this folder.

## Claims (level 3)

| Checked | Assumed |
|---|---|
| `_STEPS` order is pipeline order (`_pipeline.py:112-159`) | the guard's computation is fast enough for every `wfctl status` |
| `pending` cascades to later steps (`_pipeline.py:431-436`) | no branch with spec artifacts needs to move to the no-spec route |
| `skipped` counts as finished (`_pipeline.py:795`, `:967`) | a consumer of the payload treats a ninth row as a meaning change, so 1.3 → 1.4 |
| the guard's four calls (`_review_gate.py:850-891`) | |
| `implement` is `pending` without `tasks.md` (`_evidence.py:1958`) | |
| blocked `implement` with no open tasks routes to `wfctl verify` | |
| `step complete` refuses unless current is implement or None (`cli.py:2471`) | |
| `report-block` falls back to `_STEP_NAMES[-1]` (`cli.py:596`) | |
| notes carry only "reviewed by <group>" (`_review_notes.py:20-35`) | |
| the state dir survives worktree removal (`_archive.py`) | |

## Key Assumptions to Validate

- [ ] `wfctl status` stays quick on a long branch with the review reading added.
      Time it on this repo's longest open branch.
- [ ] The no-spec route reads correctly end to end. Record "no" on a scratch
      branch and walk it through verify and review.
- [ ] Review reopens on a new commit. Run the real flow on this branch before
      the PR: finish implement, see review next, run the panel, see it done,
      make one commit, see it pending again.

## MVP Scope

In:

1. The `review` row, its reader, and the shared `_review` function the guard
   and `build_evidence` call.
2. `wfctl spec none --reason`, the `spec_step` flag, the `implement` change for
   a branch with no `tasks.md`, and the warning for a stale claim.
3. `step complete implement` accepting `review` as current, and `report-block`
   falling back to `implement` by name.
4. Status payload version 1.4, the snapshot and step-list tests, README.md's
   step count, and `speckit-orchestrate`'s story-complete handling.
5. The skill text already committed on this branch (1a0e668).
6. `changes/679.addition.md`.

## Not Doing (and Why)

- A refactor review group after security and code. The issue leaves it
  undecided, it changes code where groups only report, and clean-code says a
  refactor is cheapest before review. It stays inside `/speckit.implement`.
- Archiving review reports. The state dir already keeps them.
- Reading git notes in `wfctl status`. A failed push would make status disagree
  with the guard.
- A second, shorter step table (#382). That needs an answer to #100's
  objection to a registry, and the flag covers the no-spec route alone.
- Moving modules ahead of #671. This branch keeps the flat layout so it doesn't
  conflict with the reorg it was ordered ahead of.

## Open Questions

None. The payload version bump is listed as an assumption and is decided in
the plan.
