---
status: proposed
---

# wfctl keeps review reports and run records in the branch's state directory

## Context

The accepted record on review coverage has wfctl keep three things for each
review group:

1. The last reviewed commit.
2. A run record, which lists the expected reviewers and the commits to review.
3. The reviewers' reports.

That record leaves the location to this level.

Previously, reviewers wrote their reports to `$FEATURE_DIR/reviews/`, a folder
inside the branch's spec directory. The `wfctl store specs` command commits the
whole spec directory to the `specs-trunk` branch, so it commits the reports too.
Nobody meant to keep them there. A report describes one commit of one branch,
and it has no use once the branch merges.

The decision on session state limits where the records can go instead. A
session file holds only what wfctl can't work out from the files on disk. The
last reviewed commit is one of those things, because no artifact records which
commits a panel read.

## Verified

- `fanning-out-code-review/SKILL.md`, line 110: "Write findings to
  `$FEATURE_DIR/reviews/<id>.md`, the id you assigned it."
- `git ls-tree -r --name-only origin/specs-trunk | grep -c "/reviews/"` prints
  376, so `wfctl store specs` has already committed 376 report files.
- `_verify.py` writes `verify.json` into the branch's state directory with
  `write_record(agent_dir, record)`. It is the existing record of a check that
  wfctl runs and the agent can't certify.
- `_paths.resolve_agent_dir` returns `$XDG_STATE_HOME/wfctl/<project>/<branch>`
  unless `WFCTL_STATE_DIR` overrides it. The path sits outside every worktree,
  so removing a worktree leaves the directory in place.

## Assumed

- Andre is the only user, and he runs every review and every PR from one
  machine. This assumption fails if a second machine or a second person reviews
  a branch, since the other machine has no review history for it. The follow-up
  issue on pushing review records so CI can check them covers that case.

## Direct baseline

The simplest approach keeps everything in the spec directory. The reports stay
in `$FEATURE_DIR/reviews/`, and wfctl writes the run record and the last
reviewed commit beside them. `wfctl store specs` keeps committing the folder, so
the review history reaches `specs-trunk` with the rest of the spec.

## Decision

wfctl keeps all three in the branch's state directory, in a `reviews/` folder
beside `verify.json`. Each group has its own last reviewed commit and its own
run records, and each run's reports sit under that run. The panel skill asks
wfctl for the path instead of building it from `$FEATURE_DIR`.

wfctl reads from this one directory and doesn't search a list of places for a
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

Above the line are the files wfctl derives state from. Below it are the session
files, which hold what wfctl can't derive. In the baseline, the review check
writes above the line, and `wfctl store specs` then commits every report to
`specs-trunk`. In the decision, the review check writes below the line, beside
`verify.json`, and nothing carries the reports to `specs-trunk`. The decision
has one arrow fewer into `specs-trunk`.

## Considered

- Keep the records in the spec directory, as the direct baseline describes. We
  didn't choose this because `wfctl store specs` commits them to `specs-trunk`,
  which already holds 376 reports nobody will read. The last reviewed commit is
  also session state under the decision on session state.
- Search a list of directories, so a report in an old location still counts if
  the location moves. Andre suggested this, and we didn't choose it for three
  reasons:
  1. A report counts only when it names the run's newest commit, so a report
     left in an old location can't count anyway.
  2. If wfctl loses the last reviewed commit, the next review starts where the
     branch left `main`. That costs one larger review and lets nothing through.
  3. A list would give an agent more places to plant a report.
- Commit the records into the repository, beside the scan files under the
  architecture root. We didn't choose this because a scan file records what a
  pipeline step covered, for a reviewer to read in the PR. A review
  report is the agent's working input. Committing it would also put a report
  about one commit into the next commit.

## Consequences

- `wfctl store specs` no longer commits review reports, since the spec directory
  no longer holds any.
- A review counts only on the machine where it ran. This is acceptable while
  Andre is the only user, and the Assumed section says what changes that.
- The 376 reports already on `specs-trunk` stay there. Removing them is a
  separate decision for the project's maintainer.
- Removing a worktree keeps the review history, since the state directory sits
  outside it. Removing the state directory, or pointing `WFCTL_STATE_DIR` at a
  new path, makes the next review start where the branch left `main`.

## Verification

- A test runs a review group, then runs `wfctl store specs`, and checks that no
  file under `reviews/` lands in the spec store's commit.
- A test points `WFCTL_STATE_DIR` at an empty directory on a branch with an
  earlier review, and checks that the next run starts where the branch left
  `main`.

## Log

- 2026-10-21  proposed  — #622 level 3. Andre said the reports "shouldn't be
  committed to the specs" and that he expected them in the state directory.
