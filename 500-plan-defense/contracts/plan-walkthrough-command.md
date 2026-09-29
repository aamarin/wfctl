# Contract: `/plan-walkthrough`

## Invocation

`/plan-walkthrough` with an optional argument, `plan` or `change`. A
declaration cannot carry the argument, since `check config` looks up the
command's name as a file, so the skill resolves the mode in this order and
says which it picked before the first question:

1. The argument, when one was given.
2. The current pass in `wfctl status --json`, when its `command` is
   `/plan-walkthrough`: change mode under `implement`, plan mode under any
   other step.
3. Plan mode.

## What it does first

1. Run `wfctl status --json` and read `auto_approve`.
2. If `auto_approve` is `true`, print the refusal below and stop. Nothing is
   written.
3. Run `wfctl feature-paths` and `wfctl state-dir` for the two destinations.
4. In plan mode, stop without writing anything if `plan.md` is missing, and
   say there is no plan to walk through.

## The refusal (FR-014)

```
Plan walkthrough needs a person at the prompt, and auto-approve is on.
Run `wfctl start --no-auto-approve`, then `/plan-walkthrough` again.
An autonomous run skips this pass only when its declaration in
wfctl.json carries "needs_person": true.
```

## What it writes

| When | Where | What |
|---|---|---|
| every run that asked at least one question | `$(wfctl state-dir)/walkthrough/<mode>-<date-time>.md` | the answers file (`data-model.md`) |
| an interview that reached its outcome | `<FEATURE_DIR>/plan-walkthrough.md` or `change-walkthrough.md` | the marker, three fields |
| change mode with uncommitted changes | nothing extra | a line telling the person the marker names the last commit only |

It never writes to the plan, the code, the architecture records, or anything
the repository commits, other than the marker.

## Closing lines

The skill ends by printing the outcome counts and the answers file's path, so
the person knows where the private record is.
