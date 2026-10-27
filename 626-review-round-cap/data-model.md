# Data model: wfctl stops a review group after three rounds

This feature adds no stored state. Every value below is derived when
`wfctl review start` runs, and none of it is written anywhere
(`session-state-is-re-derived.md`).

## Round cap

The number of runs each group may start on one branch.

| Source | Value used |
| --- | --- |
| The trunk has no `wfctl.json` | 3 |
| The trunk's `wfctl.json` has no `review` key, or no `review.rounds` | 3 |
| The trunk's `review.rounds` is an `int` of 0 or more, not a `bool` | that value |
| The trunk's `review.rounds` is anything else | 3, with a warning |
| The trunk's `wfctl.json` isn't valid JSON, or isn't an object | 3, with a warning |
| The trunk's `review` value isn't an object | 3, with the invalid-value warning |

"The trunk" is the first ref `trunk_refs` returns, for the trunk
`review_trunk` finds (see Review trunk below). wfctl doesn't read the cap
from the working tree. The working tree's value is read only to compare with
the trunk's, and an invalid one there is a `check config` finding that also
stops `review start` and the guard.

## Review trunk

The branch that reviews measure commits against and read the cap from. wfctl
reads it from `wfctl.json` on the default branch, the one `origin/HEAD` names,
and not from the working tree (`research.md` R11).

| Source | Trunk used |
| --- | --- |
| No `origin/HEAD`, or `origin` doesn't fetch every branch | today's resolution, which reads the working tree's `trunk` first |
| `origin/HEAD` names a ref the clone doesn't have | refused |
| The default branch has no `wfctl.json`, or no `trunk` key | the default branch |
| The default branch's `trunk` is a branch name the clone has | that branch |
| The default branch's `trunk` is a branch name the clone doesn't have | refused |
| The default branch's `trunk` isn't a branch name | the default branch, with a warning |
| The default branch's `wfctl.json` isn't valid JSON, or isn't an object | the default branch, with a warning |
| The working tree names a different trunk the clone has | the default branch's trunk, with a warning |
| The working tree names a trunk the clone doesn't have, or isn't a branch name | refused, as today |

## Rounds started

For one group on one branch, rounds started is the number of folders under
`reviews/<group>/runs/` that hold a `run.json`. A folder with no `run.json`
belongs to an interrupted start and isn't counted. A run that never completed is
still counted.

## Run record

This is unchanged. `run.json` gains no field. The round a run belongs to is its
position in the count, and it is printed in the header, not stored.

## Sign-off

This is unchanged, and this feature only reads it. A sign-off covers a commit
when the commit is the signed-off commit or one of its ancestors, and the
repository has the signed-off commit. At the cap, `review start` asks whether
the sign-off covers every commit in the group's range, the same check
`unreviewed` makes for the guard. It doesn't ask about the head, because a
clean merge of the trunk is a head that the range leaves out.

## `review start` outcomes

`review start` takes the first row that matches, top to bottom.

| Condition | Outcome | Exit | Writes |
| --- | --- | --- | --- |
| The group has no commits to review | 1, up to date | 0 | nothing |
| Rounds started is below the cap | 2, run started | 0 | the run folder and `run.json` |
| The sign-off covers every commit in the range | 3, nothing left to review | 0 | nothing |
| Otherwise | 4, refused | 1 | nothing |

Rows 3 and 4 apply only at or past the cap, since row 2 comes first.

## Types in code

- `_review_config.DEFAULT_ROUNDS = 3`.
- `_review_config.parse_rounds(review: object) -> tuple[int | None, str | None]`
  returns the value, or None when the key is absent, plus a problem string or
  None.
- `_review_config.load_rounds(repo_root: Path) -> int | None` returns the
  working tree's valid `review.rounds`, or None.
- `_review.TrunkRounds`, a frozen dataclass with three fields:
  - `cap: int`
  - `ref: str`, the short name, such as `origin/main`
  - `warning: str | None`
- `_review.ReviewTrunk`, a frozen dataclass with three fields:
  - `name: str`, the trunk's local branch name, such as `main`
  - `source: str | None`, the default branch's short ref, such as
    `origin/main`, when the trunk came from its `wfctl.json`, or None on the
    fallback path. The refusal messages name the file from it.
  - `warning: str | None`
- `_review.Started` gains two fields:
  - `rounds: int` is the number of runs the group had started before this
    call, on every outcome. The header prints `rounds + 1`, and outcome 3
    prints `rounds`.
  - `sign_off: str | None` is the signed-off commit, set only for outcome 3.
    Outcome 3 prints it.

  `cap` isn't stored on `Started`, since the command passed it in. The command
  checks `sign_off` before `run is None`, since outcome 3 has no run either.
- `_review.RoundCapReached(ReviewError)` carries `group`, `rounds`, and `cap`.
