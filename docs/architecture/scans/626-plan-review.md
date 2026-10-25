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
