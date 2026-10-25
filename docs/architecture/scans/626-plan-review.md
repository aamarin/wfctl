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
