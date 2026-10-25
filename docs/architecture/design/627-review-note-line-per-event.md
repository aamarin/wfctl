---
status: proposed
---

# A review note holds one plain line per event, such as "reviewed by security"

## Context

The accepted record `review-record-in-git-notes.md` has wfctl add a git note to
a commit when a review run completes there or a person signs off through it. It
leaves the note's contents to this level.

One commit can collect several events. If the code group commits no fixes, the
security and code groups both complete a run on the same head, and a person can
sign off there too. Git keeps one note per commit per notes ref, so every event
on that commit has to fit in that one note.

Two machines can also write to the same note. When the second one pushes,
`origin` rejects the push, and the accepted record has wfctl merge the two notes
refs with `git notes merge -s cat_sort_uniq` and push again. That strategy joins
the two notes line by line, sorts the lines, and drops duplicates.

## Verified

- In a scratch repository on git 2.44.0, a push of the notes ref from one clone
  was rejected after another clone pushed first. `git notes merge -s
  cat_sort_uniq` then joined `security run 1` and a local line with the other
  clone's `code run 1`, sorted them, and the next push succeeded.
- A note added from a linked worktree showed in the main checkout with no
  fetch, so every worktree on one machine shares one notes ref.
- `git notes --ref fresh append -m "reviewed by code" HEAD` on a commit with no
  note created one holding that line.

## Assumed

- No reader needs the run number. CI counts commits from the group's name alone,
  and the run's folder exists only on the machine that ran it. If a later feature
  wants to link a note to its reports, the line needs a field it doesn't have
  now.

## Direct baseline

The note is a JSON object, the same shape as `last-reviewed.json`:
`{"groups": {"security": {"run": 3, "at": "…"}}, "sign_off": {"at": "…"}}`.
wfctl reads the old note, adds the event, and writes the note back with `git
notes add -f`.

## Decision

Each event is one line of plain text, added with `git notes append`:

```
reviewed by security
reviewed by code
signed off by a person
```

A reader ignores blank lines and any line it doesn't recognize. A group's line
names the group as `wfctl.json` spells it. The line carries no run number and no
time, so two machines that record the same event write the same line, and the
merge keeps one copy.

`git log --notes=wfctl-review` shows the lines under each commit, so a person
can see what was reviewed without wfctl.

## Diagram

```
                 baseline                              decision

stable    ┌──────────────────────┐             ┌──────────────────────┐
          │ git notes merge      │             │ git notes merge      │
          │ -s cat_sort_uniq     │             │ -s cat_sort_uniq     │
          └──────────▲───────────┘             └──────────▲───────────┘
                     │ breaks                             │ joins lines
          ┌──────────┴───────────┐             ┌──────────┴───────────┐
          │ note: one JSON object│             │ note: one line per   │
          │                      │             │ event                │
          └──▲──────────────▲────┘             └──▲──────────────▲────┘
             │ reads,       │ reads               │ appends      │ reads
             │ rewrites     │                     │              │
volatile  ┌──┴──────────┐ ┌─┴────────┐         ┌──┴──────────┐ ┌─┴────────┐
          │ review check│ │ CI check │         │ review check│ │ CI check │
          └─────────────┘ └──────────┘         └─────────────┘ └──────────┘
```

The change this is built to absorb is a second machine writing the same note. In
the baseline, `cat_sort_uniq` sorts the lines of two JSON objects into text that
no longer parses, so wfctl needs its own merge that reads both objects and
writes one back. In the decision, git's own merge already produces a valid note.
The decision also drops one arrow, since recording an event appends to the note
and doesn't read it first.

## Considered

- A JSON object per note, as the direct baseline describes. We didn't choose it
  because git's line merge breaks it, and wfctl would need its own merge for a
  rejected push.
- One notes ref per group, such as `refs/notes/wfctl-review/security`, so each
  note holds one event. We didn't choose it because CI then fetches one ref per
  group and a sign-off per ref, and the guard has more refs to match. One ref
  with one line per event keeps a single fetch.
- Keep the run number and time on each line, such as `reviewed by security, run
  003`. Andre asked what the number meant and approved dropping it. CI doesn't
  use it, and it points at a folder only one machine has.

## Consequences

- Recording an event doesn't read the note first, so wfctl needs no merge logic
  of its own, locally or after a rejected push.
- The note can't say which run reviewed a commit. The state directory on the
  machine that ran it still can.
- A line in a format wfctl doesn't recognize is ignored, not an error, so an
  older or newer wfctl reading the note skips what it can't use.

## Verification

- A test records two groups and a sign-off on one commit and checks that the
  note has three lines.
- A test merges two notes refs that both hold `reviewed by security` for the
  same commit and checks that the merged note holds it once.

## Log

- 2026-10-24  proposed  — #627 level 3. Andre approved the line format and
  dropping the run number in the 627-ci-review-check session.
