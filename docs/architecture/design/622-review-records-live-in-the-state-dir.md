---
status: proposed
---

# Review reports and run records live in the branch's state directory

## Context

The accepted record on review coverage has wfctl keep three things for each
review group: the last reviewed commit, a run record listing the expected
reviewers and the commits to review, and the reviewers' reports. That record
leaves the location to this level.

Currently, reviewers write their reports to `$FEATURE_DIR/reviews/`, the
`reviews` folder inside the branch's spec directory. The `wfctl store specs`
command commits the whole spec directory to the `specs-trunk` branch, so it
commits the reports too. Nobody meant to keep them there. The reports describe
one commit of one branch, and they are worth nothing once the branch merges.

The decision on session state constrains where they can go instead. A session
file holds only what wfctl can't work out from disk, and the last reviewed
commit is one of those things, since no artifact records which commits a panel
read.

## Verified

- `fanning-out-code-review/SKILL.md`, line 110: "Write findings to
  `$FEATURE_DIR/reviews/<id>.md`, the id you assigned it."
- `git ls-tree -r --name-only origin/specs-trunk | grep -c "/reviews/"` prints
  376, so `wfctl store specs` has already committed 376 report files.
- `_verify.py` writes `verify.json` into the branch's state directory with
  `write_record(agent_dir, record)`. It is the existing record of a check wfctl
  ran and the agent can't certify.
- `_paths.resolve_agent_dir` returns `$XDG_STATE_HOME/wfctl/<project>/<branch>`
  unless `WFCTL_STATE_DIR` overrides it. The path sits outside every worktree,
  so removing a worktree leaves the directory where it was.

## Assumed

- Andre is the only user, and he runs every review and every pull request
  from one machine. A second machine, or a second person, would see no review
  history for a branch reviewed elsewhere. That falsifies this bet, and the
  follow-up issue on pushing review records so CI can check them is where it
  would be answered.

## Direct baseline

Keep everything in the spec directory. The reports stay in
`$FEATURE_DIR/reviews/`, and wfctl writes the run record and the last reviewed
commit beside them. `wfctl store specs` goes on committing the folder, so the
review history reaches `specs-trunk` with the rest of the spec.

## Decision

wfctl keeps all of it in the branch's state directory, under `reviews/`, beside
`verify.json`. Each group has its own last reviewed commit and its own run
records, and each run's reports sit under that run. The panel skill asks wfctl
for the path rather than building it from `$FEATURE_DIR`.

The location is one directory. wfctl doesn't search a list of places for a
report.

## Diagram

```
             baseline                               decision

stable    ┌──────────────┐                       ┌──────────────┐
          │ specs-trunk  │                       │ specs-trunk  │
          └──────▲───────┘                       └──────▲───────┘
                 │ commits                              │ commits
          ┌──────┴────────────┐                  ┌──────┴───────┐
          │ spec dir          │                  │ spec dir     │
          │  + reviews/       │                  └──────────────┘
          │  + run records    │
          └──────▲────────────┘
                 │ writes, reads
═══ session-state-is-re-derived ═════════════════════════════════════════
                 │                               ┌──────────────────────┐
          ┌──────┴───────┐                       │ state dir            │
          │ review check │                       │  verify.json         │
          └──────────────┘                       │  reviews/ (new)      │
                                                 └──────▲───────────────┘
                                                        │ writes, reads
                                                 ┌──────┴───────┐
                                                 │ review check │
                                                 └──────────────┘
```

The divider separates what wfctl derives from artifacts, above, from session
files that hold what derivation can't reach, below. In the baseline the review
check writes above the line, and `wfctl store specs` carries every report to
`specs-trunk`. In the decision the review check writes below the line, and the
arrow from the review records to `specs-trunk` is gone. The graphs differ by one
arrow fewer into `specs-trunk` and by the review records moving below the
divider, where `verify.json` already sits.

## Considered

- Keep the records in the spec directory, as the direct baseline describes. We
  didn't choose this because `wfctl store specs` commits them to `specs-trunk`,
  which keeps 376 reports nobody will read, and the last reviewed commit is
  session state by the decision on session state.
- Search a list of directories, so a report in an old location still counts if
  the location moves. Andre suggested this in case the location changes later.
  We didn't choose it because a report counts only when it names the run's
  newest commit, so a report left in an old location can't count anyway. Losing
  the last reviewed commit makes the next review start where the branch left
  `main`, which costs one larger review and lets nothing through. A list would
  also give an agent more places to plant a report.
- Commit the records into the repository, under the architecture root beside the
  scan files. We didn't choose this because the scans record what a pipeline
  step covered for a reviewer to read in the pull request, and review reports
  are the agent's working input. Committing them would put a report about
  commit N into commit N + 1.

## Consequences

- `wfctl store specs` no longer commits review reports, since none are in the
  spec directory.
- A review counts only on the machine where it ran. This is acceptable while
  Andre is the only user, and the Assumed section names what breaks it.
- The 376 reports already on `specs-trunk` stay where they are. Removing them is
  a separate decision for Andre.
- Removing a worktree removes none of the review history, since the state
  directory sits outside it. Removing the state directory, or setting
  `WFCTL_STATE_DIR` to a new path, starts the next review where the branch left
  `main`.

## Verification

- A test runs a review group, then runs `wfctl store specs`, and asserts that no
  file under `reviews/` reaches the spec store's commit.
- A test points `WFCTL_STATE_DIR` at an empty directory on a branch with an
  earlier review, and asserts that the next run starts where the branch left
  `main`.

## Log

- 2026-10-21  proposed  — #622 level 3. Andre said the reports "shouldn't be
  committed to the specs" and that he expected them in the state directory.
