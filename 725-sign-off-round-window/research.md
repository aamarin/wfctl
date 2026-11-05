# Research: sign-off round window

## R1: Where the window's starting count comes from

- Decision: the sign-off records each group's round count when it's given.
- Rationale: the round tally has no times, so a time-based count could only read the branch's run records, and a rename leaves those behind. The sign-off is the event that opens a window, so it's the place to record where the window starts.
- Alternatives considered: comparing run `started_at` times with the sign-off's `at`; a marker folder in the issue's tally; deleting the count. The level-3 record gives the reason each lost.

## R2: Whether a sign-off at the cap still skips a run when it covers every commit

- Decision: no. With the window open, `start` writes a run over every commit since the group's last review, signed off or not. The "sign-off covers every commit left" path applies only once the window is used up.
- Rationale: the user agreed in the brainstorm that the next round reviews the commit they signed off on. Skipping it would let the fix through unreviewed, which is the problem #725 fixes.
- Alternatives considered: keep skipping whenever the sign-off covers everything left. We didn't choose this because round 4 would then never review B in the issue's example.

## R3: Which existing tests change

- Decision: `tests/test_review.py` tests that sign off after reaching the cap and then expect no run. Those are rewritten so the sign-off is taken first and the runs after it use the window, which keeps what each test proves about the covered path.
- Rationale: the old behavior they pin is the behavior #725 changes.

## R4: A sign-off file from wfctl 0.26.0

- Decision: no `rounds` object reads as no recorded rounds. The window is the whole branch, which matches today.
- Rationale: it fails closed. A branch at the cap with an old sign-off stays refused until the user signs off once more.

## R5: #665 and #723

- Decision: neither is implemented here. #665 is open and not merged, so there's no status row to change. `_capped` uses the shared function, and #665's row reads it once it lands. The window size is the `cap` argument `start` receives, so #723 changes what's passed in, not this code.
