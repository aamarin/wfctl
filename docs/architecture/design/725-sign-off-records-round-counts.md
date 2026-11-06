---
status: proposed
governs: evidence-and-derivation
---

# The sign-off records each group's round count

## Context

In `review-round-window.md`, each group's window starts at the latest
sign-off. To count the rounds in a window, wfctl has to know how many rounds
each group had started when the user signed off.

Currently, two places count rounds, and neither marks a sign-off.
Each of the branch's run records carries a `started_at` time. The round tally
is kept by issue, as one empty folder per round with no time or commit
(`review-round-issue-key.md`). The sign-off is one file in the branch's state
folder holding the commit and the time it was given.

Both `review start` and `wfctl status` check whether a group is at the cap,
and each computes the count separately today. If they count the
window differently, `wfctl status` shows that a group can run while `review
start` refuses it.

## Verified

- `_review.py:1092` computes the count in `start` as
  `max(runs_started(agent_dir, group), rounds_tallied(tally_dir, group))`, and
  `_review.py:1099` refuses when `rounds >= cap`.
- `_review.py:1497`, in `_capped`, repeats the same `max(...) >= cap` for
  `wfctl status`.
- `_review.py:1295`, `sign_off(agent_dir, sha)`, writes
  `{"sha": ..., "at": ...}` to `reviews/sign-off.json` and replaces any earlier
  sign-off.
- `cli.py:6744` is the only caller of `sign_off`.
- `rounds_tallied` counts folders whose names are digits, and `_tally_round`
  creates them with `mkdir`. Neither reads or writes a time.

## Assumed

- Nothing other than `review start` and `_capped` checks whether a group is at
  the cap. A third caller with its own `>= cap` check would count every
  round since the start of the branch and make this assumption false.

## Direct baseline

Count the rounds started after the sign-off's `at` time. `start` and `_capped`
read each run record's `started_at` and count the ones later than the sign-off.
The sign-off file doesn't change.

## Decision

`sign_off` also writes each group's round count at that moment, as a `rounds`
object in `sign-off.json` keyed by group name. The count is the same
`max(runs_started, rounds_tallied)` that `start` uses. A group with no runs yet
is left out and counts as 0.

One rule, `_in_window`, takes a group's count minus the count the latest
sign-off recorded for it, and one function, `_rounds_used`, takes the count.
`_capped` uses both through `rounds_in_window`. `start` uses both directly,
since it takes the count under its lock and also passes the total to the
tally. Both compare the result with the cap. wfctl treats a sign-off with no
`rounds` object, written by an older wfctl, as recording no rounds. Its window
is the whole branch, which matches today's behavior.

## Diagram

```
          baseline                               decision

stable    ┌──────────────┐  ┌──────────────┐     ┌──────────────┐ ┌──────────────┐
          │ sign-off.json│  │ round tally  │     │ sign-off.json│ │ round tally  │
          │ sha, at      │  │ (no times)   │     │ sha, at,     │ │ (no times)   │
          └──────────────┘  └──────────────┘     │ rounds (new) │ └──────────────┘
                 ▲                                └──────────────┘        ▲
                 │ reads at                              ▲ reads rounds   │ reads
          ┌──────┴───────┐                        ┌──────┴──────────────┴─┐
          │ run records  │◄── reads started_at    │ window count (new)    │
          └──────────────┘    (start, _capped)    └───────────────────────┘
                 ▲                                    ▲              ▲
════ state folder / code ═════════════════════════════╪══════════════╪══════
                 │                                    │ calls        │ calls
volatile  ┌──────┴┐ ┌────────┐                    ┌───┴───┐     ┌────┴────┐
          │ start │ │_capped │                    │ start │     │ _capped │
          └───────┘ └────────┘                    └───────┘     └─────────┘
```

In the baseline, two callers read the run records' times. The tally has
no times, so it drops out of the count. That's four
read arrows across the line. In the decision, two calls cross the line into one
new function, and that function reads two files. The design is built to absorb
a third place that shows the window, such as the status row from #665. In the
baseline, that adds two more read arrows and a third copy of the time
comparison. In the decision, it adds one call.

The decision adds no divider. The sign-off file and the tally are already in the state
folder, and the line between them and the code is already in force.

## Considered

- Count runs started after the sign-off's `at` time, as described in the
  direct baseline. We didn't choose this because the tally has no times, so the
  count would read only the branch's run records. A rename leaves those behind,
  and the tally exists so that a rename can't lower the count. Comparing times
  also makes the window depend on the clock, so a run started in the same
  second as the sign-off is counted wrong.
- Add a marker folder to the tally when the user signs off, and count the
  folders after it. We didn't choose this because the tally is shared by every
  branch on the issue, and a sign-off is for one branch. A marker there would
  open a window on a branch nobody signed off on.
- Reset the count by deleting the tally and run records at a sign-off. We
  didn't choose this because the run records hold the reports, and deleting
  them loses the history a reader uses to check what was reviewed.
- Keep the two `>= cap` checks and change each one. We didn't choose this
  because two copies of the window rule can disagree, and the third copy #665
  adds would make that more likely.

## Consequences

- The sign-off command counts with the issue's round folder, since the tally is
  stored there, and passes the counts to `sign_off`. It records every group that
  has runs or a tally on disk, so the command needs no new option. A group that
  never ran gets no entry.
- The `review-sign-off` event in the branch's event log carries the same counts.
  An agent can edit the sign-off file, and the event is what shows the edit,
  the same way a deleted run record leaves its `review-start` event behind.
- A sign-off file written before this change has no `rounds` object. Its window
  covers the whole branch, so a branch already at the cap stays refused until
  the user signs off once more. We accepted that, since it fails closed.
- `Started.rounds`, which `review start` prints as "round N of cap", becomes
  the count in the window. The header then reads "round 1 of 3" for the first
  round after a sign-off.

## Verification

- A test signs off with a group at the cap, then shows `start` writes the cap's
  number of runs, and refuses the next one.
- A test shows `_capped` and `start` agree at every count from 0 to the cap
  after a sign-off.
- A test shows a sign-off file with no `rounds` object counts the whole branch.
- A test shows a second sign-off with no rounds in between doesn't widen the
  window.

## Log

- 2026-11-05  proposed  — #725 level 3, how the window `review-round-window.md`
  decides is counted
