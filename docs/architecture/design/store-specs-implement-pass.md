---
status: proposed
---

# Storing the spec dir is a built-in pass under implement

## Context

`spec-storage-read-from-git` decides that wfctl stores a branch's spec dir and
reads whether it is stored from git. It also says the pipeline hands an
unattended run the store command after `implement`, so the run stores its own
specs before it opens a pull request. That record leaves open where in the
pipeline the store sits, and the answer has to do two things:

1. Name `/store-specs` as the next command once `implement` is done and the spec
   dir is not stored, because an unattended run only ever runs the next command.
2. Read done again once the spec dir is stored, and get out of the way in a
   layout where nothing can be pushed.

The pipeline already has three places a new check could go: a top-level step, a
pass under an existing step, and the facts block that `wfctl status` prints
under the steps.

## Verified

- `_pipeline.py:127` declares `plan-review` as
  `SubStep("plan-review", "/plan-review", _REVIEW_REQUIRED, _evidence.plan_review)`
  under `plan`, so a built-in pass is one line in the step table.
- `_pipeline.py:138` declares `implement` with no passes today.
- `_pipeline.py:490-493`, in `_pass_states`, says a pass that reads `skipped` on
  its own account "no built-in reader returns today and a declared or future one
  may", and that it does not hold up the passes after it.
- `_pipeline.py:527-529` evaluates a step's passes only once the step itself
  reads `done`. Until then every pass under it reads `pending`.
- `_pipeline.py:1205` puts each pass's `command` in the `wfctl status --json`
  payload, which is how `/plan-review` becomes the next command after `plan`.
- `_evidence.py:1141-1165` builds exactly four facts in a fixed order, and its
  docstring says the list is "fixed and never filtered" because a consumer may
  index it.
- `AGENTS.md`, "Declaring a stage of your own", says a pass declared in
  `wfctl.json` can only check that a file exists under the feature directory.

## Assumed

- Reading git for the spec dir on every `wfctl status` is cheap enough. The pass
  runs one `git status` and one `git log @{u}..HEAD` scoped to one folder. If
  `wfctl status` gets noticeably slower on a spec store holding hundreds of
  folders, this is wrong, and the reader needs to be measured.
- This is the first built-in pass to read `skipped` on its own account. The
  `_pass_states` docstring says the walk handles it. If a view or the
  orchestrate skill treats a built-in `skipped` pass as outstanding, that view is
  wrong, not this pass.

## Direct baseline

Add a fifth fact, `specs stored`, beside the four `wfctl status` already prints.
It reads git the same way and shows `met` or `unmet`. Nothing in the step table
changes and no new command ships. `implement` reads done when its own work is
done, the pipeline finishes, and the fact says whether the spec dir made it.

## Decision

`implement` gets one built-in pass, `store-specs`, with `/store-specs` as its
command and no review required. Its reader asks git whether the spec dir is
stored:

1. Every file committed and the commit on the upstream branch reads `done`.
2. A layout with nowhere to push reads `skipped`, with a reason saying where the
   files are. That covers a plain folder, a spec root inside the code
   repository, and a spec store with no upstream branch.
3. Anything else reads `in_progress`, and `/store-specs` becomes the next
   command.

`/store-specs` is a new wrapper under `wfctl/agents/commands/`. It runs
`wfctl store specs`, and when the host refuses the push it runs
`wfctl report-block store-specs --reason "…"` instead of trying another way.

## Diagram

```
             baseline                             decision

stable    ┌──────────────────┐               ┌──────────────────┐
          │ step table       │               │ step table       │
          │ implement        │               │ implement        │
          └──────────────────┘               │  └ store-specs   │ (new)
                                             └────────┬─────────┘
          ┌──────────────────┐                        │ reads: stored?
          │ facts block      │                        ▼
          │ + specs stored   │ (new)         ┌──────────────────┐
          └────────┬─────────┘               │ pass reader      │ (new)
                   │ reads: stored?          └────────┬─────────┘
                   │                                  │ asks git
════ wfctl works out state from what is on disk (session-state-is-re-derived) ═══
                   │                                  │
volatile  ┌────────▼─────────┐               ┌────────▼─────────┐
          │ spec store (git) │               │ spec store (git) │
          └──────────────────┘               └──────────────────┘

          next command: none                  next command: /store-specs
```

Both sides read the same answer from git across the same boundary, so the
coupling is one arrow on each side. They differ in where the answer lands. The
baseline puts it in the facts block, which only reports, so the next command
stays empty and an unattended run finishes with the spec dir unstored and an
`unmet` line nobody reads. The decision puts it in the step table, which is the
only thing that sets the next command. No boundary is new on either side.

## Considered

- **The baseline, a fifth fact.** It is the smallest change, and it does make the
  gap visible. We didn't choose this because a fact never sets the next command,
  so the unattended run it exists for would never store anything. It would also
  change a list that consumers index by position.
- **A top-level `store` step after `implement`.** It puts storing in the step
  list, where it reads plainly. We didn't choose this because every step owns an
  artifact of its own in the spec dir, and this one would own nothing but the
  state of git. A pass is the existing shape for a check that runs after a step
  and has no artifact of its own, which is what `plan-review` is.
- **A pass declared in `wfctl.json`.** It needs no change to wfctl's step table.
  We didn't choose this because every repository would have to declare it, and a
  declared pass can only check that a file exists, which cannot say whether a
  commit was pushed.

## Consequences

An unattended run now stops at `/store-specs` before it reaches a pull request,
and an attended one gets it as the next command. A run whose host refuses the
push is held by `report-block`, which is how every other outward action is
reported.

`implement` reads `done` and the pipeline still has a next command, which is new
for the last step. Anything that treated "`implement` done" as "pipeline
finished" has to read the pass as well, and the orchestrate skill is the first
place to check.

In the default layout, with `specs/` inside the worktree, the pass reads
`skipped` every time. The spec dir there is saved at removal, not by the
pipeline.

## Verification

- With `implement` done and an uncommitted file in the spec dir,
  `wfctl status --json` names `/store-specs` as the next command.
- After `wfctl store specs` succeeds, the pass reads `done` with no fetch and no
  network access.
- With the spec root inside the code repository, the pass reads `skipped` with a
  reason saying where the files are, and the pipeline reads finished.
- An unpushed commit with nothing uncommitted reads `in_progress`.

## Log

- 2026-10-14  proposed  — #359 level 3: where the store sits in the pipeline,
  approved by Andre in the brainstorm
