---
status: rejected
---

# An unattended plan defense records its skip as a step claim, not as a marker

## Context

`plan-walkthrough-is-private` decides that plan defense runs only with a person
present, and that an unattended run skips it and says so. It leaves open how the
skip is recorded. The answer has to satisfy three readers at once:

1. wfctl, which must advance past the pass, or the unattended run stops on it.
2. A person reading `wfctl status`, who must not see a check that nobody ran
   reported as done.
3. A later attended session on the same branch, which may still want to run the
   check.

A repository places the pass itself, by declaring it in `wfctl.json` under any
step with `command: "/plan-defense"`. Declared passes default to
`review_required`, and `auto_approve` turns that automatic, so an unattended run
reaches `/plan-defense` and the skill is the one that has to decide.

## Verified

- `_pipeline.py:750-752` returns a pass's command with
  `auto = on_finish == _AUTOMATIC or auto_approve`, so an unattended run invokes
  `/plan-defense` without stopping.
- `_declared.py:32` sets `_DECLARED_DEFAULT = "review_required"` for a declared
  pass.
- `_declared.py:202` builds every declared pass's reader with
  `build_file_exists_reader(evidence)`, so any file at the evidence path reads
  `done`, whatever it says.
- `_pipeline.py:400-403` checks claims first: a pass with a claim is `skipped`
  with the claim's reason, before its reader is called.
- `_pipeline.py:426` stores claims under `<arch-root>/step-claims/<branch>/`,
  one file per pass, written by `wfctl step none`.
- `_pipeline.py:748-749` routes a pass with no command to `<step>.<name>` with
  `auto = False`, and `_pipeline.py:511` reports it as `attention: manual`.

## Assumed

- A repository declares the pass with `/plan-defense` as its command, so the skill
  can find its own qualified name in `wfctl status --json` by that command. A
  repository that wraps it in a command of its own breaks this, and the skill
  then asks for the name rather than guessing it.
- One declaration per mode per repository. Two passes both running
  `/plan-defense` in plan mode would leave the skill unable to tell which one it
  was invoked for.

## Direct baseline

Under `auto_approve`, the skill writes the marker file anyway, with a line saying
the check was skipped because no person was present. No command is run and no
new file kind appears. The pass reads `done`, the run advances, and the marker
tells a reader who opens it what happened.

## Decision

Under `auto_approve`, the skill writes no marker and runs
`wfctl step none <step>.<name> --reason "no person present; delete this claim to
run the check"`. The pass reads `skipped` with that reason, the run advances,
and `wfctl status` shows the skip where a person looks.

In attended mode, the skill first looks for a claim on its own pass carrying
that reason. If one exists, it tells the person and deletes the claim file before
the interview starts, so an attended run on a branch an unattended run already
passed through is not shadowed by the old skip.

## Diagram

```
             baseline                          decision

stable     ┌──────────────┐                 ┌──────────────┐
           │ pass reader  │                 │ pass reader  │
           │ (file exists)│                 │ claim first  │
           └──────▲───────┘                 └──────▲───────┘
                  │ reads: exists → done           │ reads: claim → skipped
                  │                                │
════ wfctl derives state from files (session-state-is-re-derived) ════════════
                  │                                │
volatile   ┌──────┴───────┐                 ┌──────┴───────┐   ┌────────────┐
           │ marker       │                 │ step claim   │   │ marker     │
           │ "skipped"    │                 │ "no person"  │   │ (not       │
           └──────▲───────┘                 └──────▲───────┘   │  written)  │
                  │ writes                         │ writes    └────────────┘
           ┌──────┴───────┐                 ┌──────┴───────┐
           │ /plan-defense│                 │ /plan-defense│
           │ unattended   │                 │ unattended   │
           └──────────────┘                 └──────────────┘
```

The two graphs differ in which file the skill writes. The baseline writes the
marker, whose reader cannot see its content and reports `done`. The decision
writes a step claim, which the reader checks first and reports as `skipped` with
its reason. No reader, file kind, or boundary is new; the decision moves the
skip onto the one path wfctl already renders as a skip.

## Considered

- **The direct baseline above**, a marker that says it was skipped. It advances
  the run with the least work, and it loses on the second reader: the pass shows
  `done`, so `wfctl status` reports a check that nobody ran as passed.
- **Declare the pass `manual` with no command.** wfctl already stops an
  unattended run on a manual pass and reports `attention: manual`. It loses on
  fit, since `plan-walkthrough-is-private` says an unattended run skips the check,
  and this would stop every unattended run at the pass instead.
- **Write nothing and let the run move on.** Nothing moves it. The pass stays
  outstanding, orchestrate invokes `/plan-defense` again on each pass, and the
  run eventually stops as `stalled`, which reports a skip as a loop that made no
  progress.
- **A new pass state or a new verb, such as `not-run`.** It names the skip
  exactly. It loses on cost, since the four state names are the payload's
  versioned contract (`pipeline-state-is-one-payload`), and `skipped` with a
  reason already carries the meaning.

## Consequences

The claim is committed under `step-claims/`, so the skip is visible at the pull
request. It holds only "no person present", which says nothing about any person.

A claim wins over any evidence, so the attended path has to remove it before the
check means anything. The skill does this itself, and says so, rather than
leaving the person to find a file under `docs/architecture/`.

`wfctl step none` is documented as "this pass does not apply to the change". An
unattended skip is narrower, since it does not apply to one run, and the reason
text carries that difference rather than a new verb.

## Verification

- Under `auto_approve`, `/plan-defense` on a branch with the pass declared leaves
  the pass `skipped` with the reason, writes no marker, and the next
  `wfctl status --json` names the step after it.
- In attended mode on the same branch, the skill deletes the claim, runs the
  interview, writes the marker, and the pass reads `done`.
- A claim carrying any other reason is left alone in attended mode.

## Log

- 2026-09-27  proposed  — #500 level 3: how the unattended skip that
  `plan-walkthrough-is-private` requires is recorded
- 2026-09-27  rejected  — the claim committed a file per unattended run and
  outlived the mode it described; `autonomous-agent-skips-human-checks` has wfctl
  read the skip from the approval mode instead
