# Quickstart: walk the issue's example

The sign-off command needs a person at a terminal, so this walk drives the functions below it on a scratch repository.

1. Make a scratch git repository with an `origin` whose `main` has one commit, and a branch `999-scratch` with one commit A.
2. With a cap of 3, call `_review.start` for `security` three times, adding a commit before each of the second and third. Complete each run so its commits count as reviewed.
3. Add commit B. `start` raises `RoundCapReached`.
4. Call `_review.sign_off(state, B, rounds_dir)`. `sign-off.json` holds `"rounds": {"security": 3}`.
5. Call `start`. It writes run 004, `Started.rounds` is 0, and `Started.since` is B.
6. Add C, then D, starting a run after each. Both runs are written, with `Started.rounds` 1 and 2.
7. Add E. `start` raises `RoundCapReached`, and its message names the sign-off at B.
8. `_review._capped`, through `pending_at_head(..., for_status=True)`, reports `security` capped at step 7 and not at steps 5 or 6.

The same walk is in `tests/test_review.py` as `test_a_sign_off_at_the_cap_gives_the_group_three_more_rounds`.
