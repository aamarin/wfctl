# A sign-off opens a new window of review rounds

Contexts: evidence-and-derivation

## Problem Statement

How might a sign-off at the round cap let the panel keep reviewing later fixes, instead of letting each later commit through unreviewed with its own sign-off?

## Recommended Direction

When the user signs off, each review group can start up to the cap's number of rounds again, counted from the latest sign-off. When a group has used its window, `wfctl review start` refuses as it does today and asks for another sign-off. There's no new command and no new setting. The window size is the cap `review start` reads when it runs, which is `review.rounds` on the trunk today.

The sign-off still covers the commits it lists, so a release PR, which gets no panel, still merges on a sign-off alone. A sign-off doesn't move a group's last reviewed commit. So the first round in a new window reviews every commit since that group's last review, including the ones the sign-off covered. In practice, the user signs off at the commit `review start` just refused, and the next round reviews it.

In the issue's example, the user signs off at B, rounds 4 to 6 review B, C, and D, and `review start` refuses at E. The user signs off twice, and every fix gets a review.

## Boundaries and Ownership

wfctl counts the rounds each group started since the latest sign-off, and decides whether another may start. The agent shouldn't count, since the cap exists to stop its loop, and a restarted conversation loses the count.

The user opens a window by signing off in their own terminal. The worktree guard refuses `wfctl review sign-off` from an agent, since an agent that could open a window would make the cap stop nothing.

The sign-off file records each group's round count when it was given, not the cap. So the window always follows the cap `review start` reads. Once #723 lands, that is whichever cap #723 settles, the trunk's or an approved branch value, with nothing on this branch to keep in step.

`review start` and `wfctl status` count the window with one function, so the refusal and the screen can't disagree. #665, still open, shows each group's rounds against the cap, and with this change that count is the rounds since the latest sign-off.

## Key Assumptions to Validate

- [ ] Nothing other than `review start` and `_capped` decides whether a group is at the cap. Test: grep for `>= cap` and `runs_started` callers.
- [ ] A sign-off file with no `rounds` object, written by wfctl 0.26.0, still parses and counts the whole branch. Test: a unit test with the old file shape.
- [ ] The issue's example works end to end: reach the cap, sign off, three commits each get a round, and the fourth is refused. Test: walk it in a scratch branch, with the user typing the sign-off, or drive `sign_off` and `start` directly below the command.

## MVP Scope

In:

1. `sign_off` records each group's round count in `sign-off.json`.
2. One `rounds_in_window` function, called by `start` and `_capped`.
3. `review start`'s header and refusal read the count in the window.
4. `opening-a-change` and any skill text that says a sign-off doesn't reset the count.
5. A release note, `changes/725.change.md`.

Out: the #665 status row itself.

## Not Doing (and Why)

- A `wfctl review extend` command — the sign-off already stands for the user's approval to continue, and `review-round-count.md` rejected the same command.
- A new setting for the window size — the cap is the window, so there's nothing for a repository to set twice.
- A window counted for the whole branch — the count is per group today, and per group is the smaller change.
- Letting the user sign off when nothing is unreviewed, to open a window early — the next refusal is the point to sign off, and the window opened then reviews that commit anyway.
- Any part of #723 — this branch only says which cap the window follows once #723 lands.

## Open Questions

None. The three questions the issue left open are answered above: the window is per group, the sign-off still covers its commits, and status counts the window with the same function as `review start`.

## Software design decisions

The level-2 decision is `docs/architecture/review-round-window.md`, which supersedes `review-round-count`.

- docs/architecture/design/725-sign-off-records-round-counts.md — the sign-off records each group's round count, and one function counts the window for `start` and `status`
