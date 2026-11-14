# Plan review scan for #626

## Review 2026-10-25T21:26Z

- Verdict: satisfied
- Reviewed: plan.md 371709ea34d5796324a44db1419d6c834334c453, spec.md 1a926afb47f3ac79b74a720640b818b9b6b5272c, .specify/memory/constitution.md absent, design.md aaabe0549f5adeaac928dff090cde4be9bddc65d, research.md 9e5b0f9df88c20140d4f9e7443e24fe1bc5e28a7, data-model.md 3309b53e23ae9be21db9c8a37c2fcff4aa13847f, quickstart.md 28ceca7df098fd9c12771788d65f63e9572258e3, contracts/cli.md 16c3a1f63a7c9e98615498689ac4d377fdd5202d, docs/architecture/review-round-count.md 3c8019a211b55887fdd3a64310564638c0c7173c, docs/architecture/review-round-cap.md bd4ca93d778972947b918072cc00e766fceb4895
- Review type: full (no earlier report)
- Open: BLOCKER 0 · MAJOR 2 · MINOR 6 · Fixed since the earlier review: 0
- Detail: /Users/andremarin/Development/wfctl-specs/626-review-round-cap/plan-review.md

### Coverage

| Check | Status |
| --- | --- |
| Deterministic checks | Clear |
| Requirements and traceability | Outstanding (PR-004, PR-008) |
| Architecture and boundaries | Outstanding (PR-001, PR-002, PR-005) |
| Adversarial implementation and verification | Outstanding (PR-001, PR-003, PR-004, PR-006, PR-007) |
| Security and reliability | Outstanding (PR-002) |

### Findings

- **PR-001, MAJOR, open.** `plan.md §Code changes, wfctl/_review.py` item 5
  gives outcome 3 when the sign-off covers the head, while the guard's
  `unreviewed` checks each commit in the range. `commit_range` drops a clean
  merge of the trunk, so a merge of `main` after a sign-off makes `review
  start` refuse while the guard allows `gh pr create`. Stands because
  `spec.md §FR-004` asks for both rules, and they disagree on that head.
- **PR-002, MAJOR, open.** The cap is read from `trunk_refs(...)[0]`, and
  `_paths.trunk_branch` takes the trunk from the `trunk` key in the branch's
  own `wfctl.json` first. An agent can point that key at a branch carrying a
  higher `review.rounds`. Stands because `review-round-cap.md` says the branch
  under review has no say, and the record's owner hasn't decided whether to
  accept this as a known limit or close it.
- **PR-003, MINOR, open.** The outcome 3 line in `contracts/cli.md` prints the
  round count, and `Started` carries no field for it there. Stands because no
  artifact gives the wording for a count above the cap, or the order of the
  `signed_off` check against `run is None`.
- **PR-004, MINOR, open.** The Step 1 rewrite fails
  `tests/test_opening_a_change_panel.py::test_the_panel_step_stops_after_three_rounds_to_ask_for_a_sign_off`,
  which the plan doesn't name. Stands because the plan puts the new
  `opening-a-change` assertions in `tests/test_review_fanout_skill.py`, which
  never reads that skill.
- **PR-005, MINOR, open.** `plan.md §Technical Context` cites the 5-second git
  timeout, which is the guard's. Stands because `review start` passes no
  timeout, and the plan doesn't say which value it passes to `trunk_rounds`.
- **PR-006, MINOR, open.** `research.md §R2` sends the trunk's text to
  `parse_rounds`, which takes the `review` object. Stands because no artifact
  names the function that parses the trunk's JSON, and `data-model.md` has no
  row for a trunk `review` value that isn't an object.
- **PR-007, MINOR, open.** `quickstart.md` runs `uv run wfctl` inside a scratch
  clone. Stands because `uv run` resolves the project from the current
  directory, and the steps don't say how the clone runs this worktree's wfctl.
- **PR-008, MINOR, open.** `design.md` still says `review.rounds` is 1 or more,
  and `spec.md §Assumptions` still calls both records proposed. Stands because
  the plan follows the clarified spec and the accepted records without noting
  that those two inputs are out of date.

## Review 2026-10-25T23:40Z

- Verdict: unsatisfied
- Reviewed: plan.md 5b892c5607088598037088ae6def4585cc23c7e9, spec.md cd6591444b5fffc32ffc674ec0b1b21a86968912, .specify/memory/constitution.md absent, design.md aaabe0549f5adeaac928dff090cde4be9bddc65d, research.md 253592c7aabf9d4aad42ac4b9ea96242967fd1e7, data-model.md bd7811a44e69e85edb273ea893a0e5ed60db2b9a, quickstart.md 989faaf6e0319ef71cb7e2bba6cd0944338da549, contracts/cli.md d0baf0ab4953549a48cc42f55f82a1d49b556d53, docs/architecture/review-round-count.md 3c8019a211b55887fdd3a64310564638c0c7173c, docs/architecture/review-round-cap.md bd4ca93d778972947b918072cc00e766fceb4895, docs/architecture/design/642-commit-range-takes-judged-branch.md b5dff1df8d6f4b6472f244ad198cf71a142cd580, docs/architecture/design/642-origin-head-trusted-on-full-fetch.md 241b285ccc6db8375365d9df6eda744a71857604, plan-review.plan.md 371709ea34d5796324a44db1419d6c834334c453 (base)
- Review type: re-review
- Open: BLOCKER 1 · MAJOR 2 · MINOR 4 · Fixed since the earlier review: 8
- Detail: /Users/andremarin/Development/wfctl-specs/626-review-round-cap/plan-review.md

### Coverage

| Check | Status |
| --- | --- |
| Deterministic checks | Clear |
| Requirements and traceability | Outstanding (PR-009, PR-013, PR-014) |
| Architecture and boundaries | Outstanding (PR-010, PR-012, PR-015) |
| Adversarial implementation and verification | Outstanding (PR-009, PR-011) |
| Security and reliability | Outstanding (PR-009, PR-010) |

### Findings

- **PR-009, BLOCKER, open.** The `TrunkChanged` refusal in `contracts/cli.md`
  tells the user to run `wfctl review sign-off`, and that command calls
  `unreviewed`, which reaches `trunk_refs` and refuses the same way. Stands
  because nothing in the plan gets a branch past the refusal. Moving the trunk
  change into its own PR is refused the same way, and exempting the sign-off
  would show the user a list without the commits the changed trunk hides.
- **PR-010, MAJOR, open.** `research.md §R11` skips the check when there's no
  `origin/HEAD`, which covers remotes added with `git remote add`, bare
  layouts, clones of an empty repository, and single-branch clones. Stands
  because in those repositories a branch edit alone still chooses the trunk,
  with no ref to move, so the Constitution Check overstates the closure.
- **PR-011, MAJOR, open.** The plan doesn't say how the two trunk names are
  normalised, how the default branch's `wfctl.json` is read, or whether a
  dangling `origin/HEAD`, invalid JSON, or an invalid `trunk` there refuses or
  skips. Stands because that choice decides whether one bad commit on the
  default branch refuses every PR, and the order against the existing
  same-name check, which a test pins, is open too.
- **PR-012, MINOR, open.** A repository whose trunk isn't its default branch is
  refused on every PR until the default branch declares the trunk. Stands
  because no user-facing text, such as `AGENTS.md`, says so.
- **PR-013, MINOR, open.** Some wording in the spec and the contract still says
  the sign-off covers the head. Stands because after a clean merge of the
  trunk, the outcome 3 line names a head the sign-off doesn't cover.
- **PR-014, MINOR, open.** `spec.md §FR-012` says the guard doesn't change, and
  FR-017 has it refuse a changed trunk. Stands because the two disagree, and
  FR-017's merge refusal has no test from the `main` checkout, where it can't
  be seen.
- **PR-015, MINOR, open.** `plan.md §Technical Context` counts the git calls
  from before the trunk check. Stands because the check adds calls to the
  guard, under its 5-second timeout.
- **PR-001 to PR-008, fixed.** PR-001 by `plan.md §_review.py` item 6, which
  checks every commit in the range. PR-002 by the decision to refuse a changed
  trunk (`research.md §R11`), whose open gaps are PR-009 to PR-011. PR-003 to
  PR-008 by the count field and check order, the named test file, the named
  timeout, the trunk parser, the quickstart's `--project`, and the note on
  `design.md`.

## Review 2026-10-26T16:58Z

- Verdict: satisfied
- Reviewed: plan.md 7b2b330905348dc22992528b7c1f3c7e0c67eb84, spec.md 131735051ce27c800a85490edde0c950b937b789, .specify/memory/constitution.md absent, design.md aaabe0549f5adeaac928dff090cde4be9bddc65d, research.md 67afd6417cf777506fb117703a63151541e7a1dd, data-model.md c4b74b958aa12dbf0e6eb14c9c45c54ad2407f3f, quickstart.md 4100ed78a241a44bf39660891da6fb074d7294e1, contracts/cli.md e0e12f33244b9b1007a32cb57eef1f1eebc07cc0, docs/architecture/review-round-count.md 3c8019a211b55887fdd3a64310564638c0c7173c, docs/architecture/review-round-cap.md 666b350e7b510f98f6fb6f5bc6f7218c13817631, docs/architecture/design/642-commit-range-takes-judged-branch.md b5dff1df8d6f4b6472f244ad198cf71a142cd580, docs/architecture/design/642-origin-head-trusted-on-full-fetch.md 241b285ccc6db8375365d9df6eda744a71857604, plan-review.plan.md 5b892c5607088598037088ae6def4585cc23c7e9 (base)
- Review type: re-review
- Open: BLOCKER 0 · MAJOR 1 · MINOR 6 · Fixed since the earlier review: 7
- Detail: /Users/andremarin/Development/wfctl-specs/626-review-round-cap/plan-review.md

### Coverage

| Check | Status |
| --- | --- |
| Deterministic checks | Resolved (PR-004 fixed) |
| Requirements and traceability | Outstanding (PR-020, PR-021) |
| Architecture and boundaries | Outstanding (PR-019) |
| Adversarial implementation and verification | Outstanding (PR-016, PR-018, PR-022) |
| Security and reliability | Outstanding (PR-017) |

### Findings

- **PR-016, MAJOR, open.** A branch whose `trunk` names a branch the clone
  doesn't have fits two rows of `research.md §R11`'s table, the mismatch
  warning and the `NoTrunk` refusal. Stands because read as a warning, it
  breaks two existing `NoTrunk` tests the plan doesn't list. `review start`
  would also warn while the guard's `_judge`, which still reads
  `_paths.trunk_branch`, refuses the PR.
- **PR-017, MINOR, open.** R11 has no row for a default-branch `trunk` that
  names a branch the clone doesn't have. Stands because it falls through to
  `NoTrunk` for every review and sign-off in the repository, and the message
  points at the working tree's `wfctl.json`, which that path no longer reads.
- **PR-018, MINOR, open.** R11 step 1 runs `git symbolic-ref --short`, which
  exits 128 both when there's no `origin/HEAD` and when git fails. Stands
  because the two table rows can't be told apart without `--quiet`, which
  exits 1 for a missing ref.
- **PR-019, MINOR, open.** The two #642 design records and the `trunk_refs`
  docstring still say `_paths.trunk_branch` and the declared trunk choose the
  trunk. Stands because the plan doesn't name updating them.
- **PR-020, MINOR, open.** `research.md` R4, R5, and R10 trail the plan on
  what `_covered_by_sign_off` returns, the `review_trunk` call, and the
  `AGENTS.md` and release note text. Stands because the plan was updated and
  those sections weren't.
- **PR-021, MINOR, open.** The release note is planned as `626.addition.md`,
  but the trunk read and the round order change behavior users rely on.
  Stands because `AGENTS.md` files that under `change`.
- **PR-022, MINOR, open.** Quickstart step 2 doesn't make sure the scratch
  clone has `origin/HEAD`. Stands because without it, step 10 shows the
  fallback reading the cap from `loose`, not the default-branch read it
  means to check.
- **PR-009 to PR-015, fixed.** PR-009 by `research.md §R11`, which replaces
  the refusal with a warning, so `review sign-off` and a deliberate trunk
  change both get through. PR-010 by stating the no-`origin/HEAD` fallback as
  a known limit in R11, the Constitution Check, and the cap record. PR-011 by
  R11's five steps, case table, and check order. PR-012 by the `AGENTS.md` and
  release note text on declaring `trunk` on the default branch. PR-013 by the
  outcome 3 line naming the signed-off commit. PR-014 by rewording FR-012 and
  FR-017 and adding FR-017 to the Validation Strategy. PR-015 by the updated
  git-call counts.

## Review 2026-10-26T19:09Z

- Verdict: satisfied
- Reviewed: plan.md ce505bac67e4a2b08143bd8e6d84e243134d8f63, spec.md 81217e14d8637b1611a0333ec7c6e097b1091b4c, .specify/memory/constitution.md absent, design.md aaabe0549f5adeaac928dff090cde4be9bddc65d, research.md 0c5e71c50ddbb64eadf125f19685e2774c5e8c53, data-model.md 142a067dd4e8d84ec07dca945d76fd2b597e8d9d, quickstart.md 189f41bfae57580bc1643a543ea4701da2ae35d9, contracts/cli.md 6d9c8bd7ac52a070b5f69d42893d5416d1a34f93, docs/architecture/review-round-count.md 3c8019a211b55887fdd3a64310564638c0c7173c, docs/architecture/review-round-cap.md 666b350e7b510f98f6fb6f5bc6f7218c13817631, docs/architecture/design/642-commit-range-takes-judged-branch.md b5dff1df8d6f4b6472f244ad198cf71a142cd580, docs/architecture/design/642-origin-head-trusted-on-full-fetch.md 241b285ccc6db8375365d9df6eda744a71857604, plan-review.plan.md 7b2b330905348dc22992528b7c1f3c7e0c67eb84 (base)
- Review type: re-review
- Open: BLOCKER 0 · MAJOR 0 · MINOR 2 · Fixed since the earlier review: 7
- Detail: /Users/andremarin/Development/wfctl-specs/626-review-round-cap/plan-review.md

### Coverage

| Check | Status |
| --- | --- |
| Deterministic checks | Resolved (PR-020 fixed) |
| Requirements and traceability | Resolved (PR-016 fixed) |
| Architecture and boundaries | Resolved (PR-019, PR-021 fixed) |
| Adversarial implementation and verification | Outstanding (PR-023, PR-024) |
| Security and reliability | Resolved (PR-017 fixed) |

### Findings

- **PR-023, MINOR, open.** With `origin/HEAD` set, a branch whose `trunk`
  names the branch itself gets the mismatch warning from `review start`, and
  its review and sign-off go through. The guard's `_judge` then refuses its PR
  with the same-name check. Stands because that's the disagreement between
  `review start` and the guard that `research.md §R11` step 5 says the plan
  avoids.
- **PR-024, MINOR, open.** `quickstart.md` step 10 expects `review start` to
  list the branch's commits since `main`. Stands because by then security is
  at the cap and the sign-off covers the range, so the command prints only the
  outcome 3 line.
- **PR-016 to PR-022, fixed.** PR-016 by R11 step 5 and its table row, which
  refuse a branch `trunk` the clone doesn't have with `NoTrunk` as today, and
  by FR-017 naming only the readers that decide which commits a review covers.
  PR-017 by the R11 row that refuses a default-branch `trunk` the clone lacks,
  with messages that name `wfctl.json on origin/<default>`. PR-018 by
  `symbolic-ref --quiet` with `answers=(0, 1)`. PR-019 by the `trunk_refs`
  docstring rewrite and the Log lines for both #642 records. PR-020 by the
  updated R4, R5, and R10. PR-021 by `changes/626.change.md`. PR-022 by
  quickstart step 2, which checks the clone has `origin/HEAD`.
