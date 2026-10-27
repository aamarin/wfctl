---
status: proposed
---

# The worktree guard blocks an agent from writing any git note or pushing any notes ref

## Context

The accepted record `review-record-in-git-notes.md` has CI trust any note it
finds under `refs/notes/wfctl-review`. An agent runs with the person's own Git
credentials, so it can write a note saying a group reviewed a commit and push
it, and CI would pass the PR. Andre accepted that CI can't catch a deliberately
forged note, and asked for one cheap rule: the guard blocks an agent from
writing a note by hand, so only wfctl writes one, when a run completes or a
person signs off.

wfctl writes and pushes notes from its own process, which the agent's hook never
sees. So the rule only has to cover commands the agent types.

## Verified

- `_hook.py:176` loads the review check only when the command holds `gh` in any
  case, `merge`, or `sign`. A command with none of them never reaches it.
- `_review_gate.py:160` `refusal` calls `read(command)` first, which refuses
  from the text alone before any git or `gh` call. The sign-off refusal works
  this way, with the loose pattern `_SIGN_OFF` at `_review_gate.py:75`.
- Git lets a command pick the notes ref in three ways: the `--ref` option, the
  `GIT_NOTES_REF` environment variable, and the `core.notesRef` setting, which
  can also be set for one command with `git -c`.

## Assumed

- Agents in this repo have no other use for writing git notes. If one appears,
  such as a skill that annotates commits, it gets refused and has to go through a
  wfctl command instead.
- A `git push` that names no notes ref doesn't push one. A remote configured with
  a `push` refspec for `refs/notes/*`, or `git push --mirror`, breaks this. The
  rule refuses `--mirror`, and a configured refspec is a limit the record states.

## Direct baseline

The guard refuses only writes to our ref: a `git notes` write that names
`wfctl-review` with `--ref`, and a `git push` that names
`refs/notes/wfctl-review`. Every other note stays allowed.

## Decision

The guard refuses any `git notes` command that writes, whichever ref it targets:
`add`, `append`, `edit`, `copy`, `merge`, `remove`, and `prune`. Reading stays
allowed, so `git notes show`, `git notes list`, and `git log --notes` still run.

It also refuses any `git push` whose text names `refs/notes/` or carries
`--mirror`.

Both checks read only the command's text, in the same first pass as the sign-off
refusal, and refuse without calling git. The hook's substring test adds `notes`
and `--mirror`, so these commands reach the check. The refusal says that wfctl
writes review notes when a run completes, and names `wfctl store reviews` for a
note that wasn't sent.

## Diagram

```
             baseline                               decision

stable    ┌────────────────────┐               ┌────────────────────┐
          │ refs/notes/        │               │ refs/notes/        │
          │ wfctl-review       │               │ wfctl-review       │
          └─────────▲──────────┘               └─────────▲──────────┘
                    │ protects                           │ protects
          ┌─────────┴──────────┐               ┌─────────┴──────────┐
          │ review check:      │               │ review check:      │
          │ which ref does this│               │ is this a notes    │
          │ write? (--ref, env,│               │ write, or a push   │
          │ -c core.notesRef)  │               │ naming refs/notes? │
          └─────────▲──────────┘               └─────────▲──────────┘
                    │ calls                              │ calls
volatile  ┌─────────┴──────────┐               ┌─────────┴──────────┐
          │ hook               │               │ hook               │
          └────────────────────┘               └────────────────────┘
```

No boundary in force runs through either graph. Both checks sit in the same
place and protect the same ref, so the graphs differ only in what the middle box
has to know. The change this is built to absorb is a new way to name a notes
ref. In the baseline, each one is a new rule the check has to learn, the same
pattern as the shell spellings #622 stopped chasing. In the decision, no rule
changes, since the check never asks which ref a write targets.

## Considered

- Refuse only writes to our ref, as the direct baseline describes. We didn't
  choose it because the check would have to follow `--ref`, `GIT_NOTES_REF`,
  and `-c core.notesRef`, and each one it missed would let a hand-written note
  through.
- No guard rule, and rely on CI alone. That's what the accepted record had
  before Andre asked for the rule. We didn't keep it because writing a note by
  hand is the cheapest way to forge a review, and blocking it costs one more
  pattern in a check that already runs.

## Consequences

- An agent can't write a single note by hand and push it. It could still fake
  the reviewer reports that complete a run, which is the gap the accepted record
  states.
- Every agent command holding `notes` now loads the review check. That costs one
  module import on a command that was otherwise a substring test.
- Like every guard rule, this one blocks a command only when the command exactly
  matches its rules. A git alias or a script file gets past it.

## Verification

- Tests check that `git notes add`, `git notes --ref other append`, `git -c
  core.notesRef=x notes add`, `git push origin refs/notes/wfctl-review`, and
  `git push --mirror` are refused.
- Tests check that `git notes show`, `git log --notes=wfctl-review`, and a plain
  `git push origin HEAD` are allowed.

## Log

- 2026-10-24  proposed  — #627 level 3. Andre asked for the guard rule when
  accepting that CI can't catch a forged note, and approved blocking every notes
  write in the 627-ci-review-check session.
