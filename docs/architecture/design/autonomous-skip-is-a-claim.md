---
status: rejected
---

# An autonomous run records its skip of the plan walkthrough as a note

## Context

The `plan-walkthrough-is-private` record decides that a plan walkthrough only
runs with someone present. This means an autonomous run skips it. That record
leaves open how the skip gets recorded, and the answer has to work for three
readers at once:

1. wfctl, which has to move past the check, or the autonomous run stops there.
2. A person reading `wfctl status`, who must not see a check nobody did reported
   as done.
3. The plan owner coming back later to the same branch, who may still want to do
   the walkthrough.

A repository adds the check itself in `wfctl.json`, under any step, with
`/plan-walkthrough` as its command. With auto-approve on, the autonomous agent
runs that command without stopping, so the skill is the one that has to decide
what to leave behind.

## Verified

- `_pipeline.py:750-752` gives a check's command with
  `auto = on_finish == _AUTOMATIC or auto_approve`, so an autonomous run starts
  `/plan-walkthrough` without stopping.
- `_declared.py:32` sets `_DECLARED_DEFAULT = "review_required"` for a check a
  repository adds.
- `_declared.py:202` builds every added check's reader with
  `build_file_exists_reader(evidence)`, so any file at the evidence path reads
  `done`, whatever it says.
- `_pipeline.py:400-403` checks notes first: a check with a note from
  `wfctl step none` is `skipped` with the note's reason, before its reader runs.
- `_pipeline.py:426` stores notes under `<arch-root>/step-claims/<branch>/`, one
  file per check.
- `_pipeline.py:748-749` routes a check with no command to `<step>.<name>` with
  `auto = False`, and `_pipeline.py:511` reports it as `attention: manual`.

## Assumed

- A repository adds the check with `/plan-walkthrough` as its command, so the
  skill can find its own name in `wfctl status --json` by that command. A
  repository that wraps it in a command of its own breaks this, and the skill
  then asks for the name rather than guessing.
- One check per mode per repository. Two checks both running
  `/plan-walkthrough` in plan mode would leave the skill unable to tell which one
  started it.

## Direct baseline

With auto-approve on, the skill writes the evidence file anyway, with a line
saying the walkthrough was skipped because nobody was present. No command runs
and no new kind of file appears. The check reads `done`, the run moves on, and a
reader who opens the file learns what happened.

## Decision

With auto-approve on, the skill writes no evidence and runs
`wfctl step none <step>.<name> --reason "no person present; delete this claim to
run the check"`. The check reads `skipped` with that reason, the run moves on,
and `wfctl status` shows the skip where a person looks.

When the plan owner runs the walkthrough later, the skill first looks for a note
on its own check carrying that reason. If one exists, the skill tells the plan
owner and deletes the note before the first question. This means a walkthrough
on a branch an autonomous run already passed isn't hidden by the old skip.

## Diagram

```
             baseline                          decision

stable     ┌──────────────┐                 ┌──────────────┐
           │ check reader │                 │ check reader │
           │ (file exists)│                 │ note first   │
           └──────▲───────┘                 └──────▲───────┘
                  │ reads: exists → done           │ reads: note → skipped
                  │                                │
════ wfctl works out state from files (session-state-is-re-derived) ══════════
                  │                                │
volatile   ┌──────┴───────┐                 ┌──────┴───────┐   ┌────────────┐
           │ evidence     │                 │ note         │   │ evidence   │
           │ "skipped"    │                 │ "no person"  │   │ (not       │
           └──────▲───────┘                 └──────▲───────┘   │  written)  │
                  │ writes                         │ writes    └────────────┘
           ┌──────┴────────────┐            ┌──────┴────────────┐
           │ /plan-walkthrough │            │ /plan-walkthrough │
           │ autonomous run    │            │ autonomous run    │
           └───────────────────┘            └───────────────────┘
```

The two sides differ only in which file the skill writes. The baseline writes
evidence, and the reader can't see inside it, so it reports `done`. The decision
writes a note, which the reader checks first and reports as `skipped` with its
reason. No reader, file kind, or boundary is new. This means the decision moves
the skip onto the one path wfctl already shows as a skip.

## Considered

- **The baseline above, evidence that says it was skipped.** It moves the run on
  with the least work. It loses on the second reader: the check shows `done`, so
  `wfctl status` reports a walkthrough nobody did as passed.
- **Mark the check `manual`, with no command.** wfctl already stops an
  autonomous run at a manual check and reports `attention: manual`. It loses
  because `plan-walkthrough-is-private` says an autonomous run skips the check,
  and this would stop every autonomous run there instead.
- **Write nothing and let the run move on.** Nothing moves it. The check stays
  outstanding, the agent starts `/plan-walkthrough` again each time, and the run
  eventually stops as `stalled`. This means a skip gets reported as a loop that
  made no progress.
- **A new state or a new command, such as `not-run`.** It names the skip exactly.
  It loses on cost: the four state names are part of the versioned output of
  `wfctl status --json` (`pipeline-state-is-one-payload`), and `skipped` with a
  reason already says the same thing.

## Consequences

The note is committed under `step-claims/`, so the skip shows in the pull
request. It says only "no person present", which says nothing about any person.

A note wins over any evidence, so the skill has to delete it before a
walkthrough can count. The skill does this itself and says so, rather than
leaving the plan owner to find a file under `docs/architecture/`.

`wfctl step none` is documented as "this check does not apply to the change". An
autonomous skip is narrower, since it applies to one run, and the reason text
carries that difference rather than a new command.

## Verification

- With auto-approve on and the check added, `/plan-walkthrough` leaves the check
  `skipped` with the reason, writes no evidence, and the next
  `wfctl status --json` names the step after it.
- With auto-approve off on the same branch, the skill deletes the note, runs the
  walkthrough, writes the evidence, and the check reads `done`.
- A note carrying any other reason is left alone.

## Log

- 2026-09-27  proposed  — #500 level 3: how the unattended skip that
  `plan-walkthrough-is-private` requires is recorded
- 2026-09-27  rejected  — the claim committed a file per unattended run and
  outlived the mode it described; `autonomous-agent-skips-human-checks` has wfctl
  read the skip from the approval mode instead
- 2026-09-28  renamed   — from `design/500-unattended-skip-is-a-claim`, with no
  issue number (#510), in plain language, and "unattended" is now "autonomous"
