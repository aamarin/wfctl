Implementation complete: 2026-11-05

## Tasks at completion

~~~~markdown
# Tasks: A sign-off opens a new window of review rounds

**Input**: `plan.md`, `spec.md`, `research.md`, `data-model.md`, `contracts/cli-output.md`, and `quickstart.md` in this folder
**Design records**: `docs/architecture/review-round-window.md` (level 2) and `docs/architecture/design/725-sign-off-records-round-counts.md` (level 3), both proposed

**Tests**: Every story is test-first. Each test is named as a sentence, and its docstring says why it exists (`AGENTS.md`, Testing conventions). Tests that touch output pin `NO_COLOR`.

## Readings the plan review settled

The plan review left seven MINOR findings open (`plan-review.md`). These tasks resolve them as follows, so an implementer doesn't have to choose:

1. PR-001: `Started.since` and `RoundCapReached.since` are set whenever the sign-off file holds a `rounds` object, including for a group the object leaves out, since that group's window counts from 0 and is truthfully "since the sign-off". A sign-off file with no `rounds` object, from wfctl 0.26.0, keeps today's wording, since its window is the whole branch.
2. PR-002: the five existing tests that flip are listed in T009 and T015, each with its rewrite. No assertion is deleted.
3. PR-003: three more tests are added (T006, T007, T012), and the existing tests that cover the other edge cases carry over unchanged (T019).
4. PR-004: `AGENTS.md` and `fanning-out-code-review` are updated as well as `opening-a-change` (T022, T023).
5. PR-005: a recorded count above the group's current count reads as no entry, so the window falls back to the whole branch.
6. PR-006: `review sign-off` takes the round counts before the confirmation prompt and passes them to `sign_off`, so a run started while the user reads the prompt counts against the new window.
7. PR-007: a group with neither runs nor a tally is left out of `rounds`. A group with a tally and no runs on this branch gets an entry, as FR-001 says.

---

## Phase 1: Setup

- [x] T001 Commit the release note with `uv run towncrier create 725.change.md --content "…"` in `changes/725.change.md`, category `change`, saying that a sign-off now gives each review group the cap's number of rounds again; verify with `uv run wfctl verify` reporting the release note check green

---

## Phase 2: Foundational

**Purpose**: the sign-off records the counts, and one function reads the window. Every story depends on this.

- [x] T002 Write failing tests in `tests/test_review.py` for the counting helpers: `round_counts` returns `max(runs_started, rounds_tallied)` for every group with runs under `reviews/*/runs` or a tally under `rounds/*`, and leaves out a group with neither; `sign_off(agent_dir, sha, rounds)` writes `{"sha", "at", "rounds"}`; `signed_off_rounds` reads `{}` for a missing `rounds` object, a `rounds` that isn't an object, and drops an entry that is negative, not a whole number, or a bool
- [x] T003 Add `round_counts(agent_dir, rounds_dir=None) -> dict[str, int]` to `wfctl/_review.py`. With no `rounds_dir`, it counts in `agent_dir` alone, the same convention `start` uses; verify with T002
- [x] T004 Change `sign_off(agent_dir, sha, rounds=None)` in `wfctl/_review.py` to write the `rounds` object. With `rounds=None` it calls `round_counts(agent_dir)`. Keep the existing `sha` and `at` fields as they are; verify with T002 and the existing sign-off tests in `tests/test_review.py`
- [x] T005 Add `signed_off_rounds(agent_dir) -> dict[str, int] | None` and `rounds_in_window(agent_dir, group, rounds_dir) -> int` to `wfctl/_review.py`. `signed_off_rounds` returns None when there's no sign-off file or no `rounds` object, so callers can tell an old file from a new one. `rounds_in_window` returns `used - recorded`, where `used` is `max(runs_started, rounds_tallied)`, and treats a recorded count above `used` as no entry (reading 5); verify with T002 and T006
- [x] T006 Add a test in `tests/test_review.py` that a recorded count above the group's current count, such as 99, gives a window of the whole branch, not 0. The docstring says this closes the unbounded window the plan review named as PR-005
- [x] T007 Add a test in `tests/test_review.py` that a sign-off taken when the group had a tally on the issue and no runs on the branch records the tally's count. This is the only path that proves `cli.py` passes the round folder, so a dropped `rounds_dir` fails it
- [x] T008 Validate Phase 2 with `uv run pytest -q tests/test_review.py` and `uv run mypy` — merge gate

**Checkpoint**: the sign-off records counts, and the window can be read. Nothing reads it yet.

---

## Phase 3: User Story 1 - Fixes after a sign-off get reviewed (Priority: P1) 🎯 MVP

**Goal**: after a sign-off at the cap, each group starts the cap's number of rounds again, and then `review start` refuses.

**Independent Test**: with a cap of 3, start three runs for a group, sign off, then show `review start` writes three more runs and refuses the fourth.

**Verification**:

- Automated: `tests/test_review.py::test_a_sign_off_at_the_cap_gives_the_group_three_more_rounds`, the flipped tests in T009, and the CLI tests in T015 - T016
- Manual: the quickstart walk (T024)
- Evidence: runs 004 - 006 are written after the sign-off and the start after them raises `RoundCapReached` naming the sign-off

### Tests for User Story 1

- [x] T009 [US1] Rewrite these tests in `tests/test_review.py` so the sign-off is taken first and the runs after it use the window, which keeps what each was written to prove:
  1. `test_start_at_the_cap_with_a_sign_off_over_every_commit_writes_nothing`: sign off, then start the cap's number of runs at the signed head without completing them, then show the next start writes nothing.
  2. `test_start_at_the_cap_refuses_a_commit_made_after_the_sign_off`: sign off, use the window, add a commit, then show the start refuses.
  3. `test_start_at_the_cap_allows_a_clean_merge_of_main_after_the_sign_off`: sign off, use the window, merge `main` cleanly, then show the start still writes nothing.
- [x] T010 [P] [US1] Write `test_a_sign_off_at_the_cap_gives_the_group_three_more_rounds` in `tests/test_review.py`, following quickstart steps 1 - 7: three runs, a refusal at B, a sign-off at B, runs at B, C, and D with `Started.rounds` 0, 1, and 2, and a refusal at E
- [x] T011 [P] [US1] Write tests in `tests/test_review.py` that a second sign-off with no rounds in between leaves the same window, and that a group with no runs at the sign-off counts its window from 0
- [x] T012 [P] [US1] Write a test in `tests/test_review.py` that lowering the cap after a sign-off shrinks the window, since the window size is the `cap` argument `start` receives (FR-006)
- [x] T013 [P] [US1] Write a test in `tests/test_review.py` that a sign-off file with no `rounds` object counts the whole branch, so a branch at the cap stays refused (SC-003)

### Implementation for User Story 1

- [x] T014 [US1] In `start` in `wfctl/_review.py`, replace `rounds = max(...)` at line 1092 with `rounds_in_window`, keep `rounds` on `Started` as the window count, and add `Started.since: str | None`, set per reading 1. Keep passing the total count to `_tally_round`, since the tally's numbering is the total. Give `RoundCapReached` an optional `since` and word its message "… rounds since the sign-off at abc1234" when it's set; verify with T009 - T013
- [x] T015 [US1] Rewrite these tests in `tests/test_review_cli.py` the same way as T009, and update their expected wording to `contracts/cli-output.md`:
  1. `test_start_at_the_cap_with_a_sign_off_says_nothing_is_left_to_review`
  2. `test_start_past_a_lowered_cap_with_a_sign_off_says_so_in_the_same_words`
  3. `test_start_at_the_cap_with_a_commit_after_the_sign_off_still_refuses`
- [x] T016 [P] [US1] Write CLI tests in `tests/test_review_cli.py` that after a sign-off the header reads "round 1 of 3 since the sign-off at abc1234", and that with no sign-off the header is unchanged
- [x] T017 [US1] In `wfctl/cli.py`, have `review sign-off` call `_review.round_counts(agent_dir, resolve_round_dir(repo_root, branch))` before the `input()` prompt, and pass the result to `sign_off` (reading 6). Have `review start`'s header and its "the sign-off covers every commit left" line use the wording in `contracts/cli-output.md` when `started.since` is set; verify with T007, T015, and T016
- [x] T018 [US1] Validate Phase 3 with `uv run pytest -q tests/test_review.py tests/test_review_cli.py` — merge gate

**Checkpoint**: the issue's example works end to end through the CLI.

---

## Phase 4: User Story 2 - A sign-off still lets the change merge (Priority: P1)

**Goal**: the sign-off still covers every commit it lists.

**Independent Test**: sign off at HEAD, then show the guard's unreviewed-commit check reports nothing pending.

**Verification**:

- Automated: the existing coverage tests, including `tests/test_review.py::test_a_commit_after_the_sign_off_is_not_covered`, pass unchanged
- Evidence: no coverage code in `_review.py` changes

- [x] T019 [US2] Confirm with `uv run pytest -q tests/test_review.py tests/test_review_gate.py tests/test_review_rename.py tests/test_review_cli.py` that these carry over unchanged: `test_a_commit_after_the_sign_off_is_not_covered`, `test_a_rename_drops_the_branchs_sign_off_and_the_cap_still_holds`, `test_start_under_a_cap_of_zero_refuses_any_commit_without_a_sign_off`, `test_start_under_a_cap_of_zero_allows_a_signed_off_range`, and `test_sign_off_with_nothing_unreviewed_needs_none`. A failure here means coverage changed, which this feature doesn't allow — merge gate

---

## Phase 5: User Story 3 - Status and the refusal agree (Priority: P2)

**Goal**: `wfctl status` decides capped with the same function as `review start`.

**Independent Test**: after a sign-off, step a group from 0 to 3 rounds and show status reports capped only when `review start` would refuse.

**Verification**:

- Automated: the `test_coverage_for_status_*` tests in `tests/test_review.py`, plus T020
- Evidence: `_capped` calls `rounds_in_window` and has no `max(...)` of its own

- [x] T020 [US3] Write `test_coverage_for_status_agrees_with_start_at_every_count_after_a_sign_off` in `tests/test_review.py`, stepping 0 to the cap and comparing `pending_at_head(..., for_status=True)` with whether `start` raises
- [x] T021 [US3] In `_capped` in `wfctl/_review.py`, replace the `max(...) >= cap` at line 1497 with `rounds_in_window(...) >= cap`; verify with T020 and the existing `test_coverage_for_status_*` tests, then validate Phase 5 with `uv run pytest -q tests/test_review.py` — merge gate

---

## Phase 6: Polish & Cross-Cutting

- [x] T022 [P] Update the cap paragraph in `wfctl/agents/skills/opening-a-change/SKILL.md` (line 82) to say that a sign-off gives each group the cap's number of rounds again (FR-009), and update the `review.rounds` paragraph in `AGENTS.md` (line 392) to say the cap counts rounds since the latest sign-off; verify with `uv run wfctl install-skills` and reading the installed copy
- [x] T023 [P] Update `wfctl/agents/skills/fanning-out-code-review/SKILL.md` (line 97) so it says `review start` writes a run after a sign-off while the window is open, and says nothing is left to review only once the window is used up; verify with `uv run wfctl install-skills` and reading the installed copy
- [x] T024 Walk `quickstart.md` steps 1 - 8 on a scratch repository and confirm the run numbers, `Started.rounds`, and the capped result at each step
- [x] T025 Validate the definition of done with `uv run pytest -q`, `uv run ruff check wfctl/ tests/`, `uv run mypy`, `python3 .github/scripts/check_imports.py`, and `uv run wfctl doctor` — merge gate

---

## Dependencies & Execution Order

- Phase 1 has no dependencies.
- Phase 2 blocks every story.
- US1 (Phase 3) comes next. US2 (Phase 4) only confirms that nothing in coverage moved, so it runs after US1.
- US3 (Phase 5) depends on Phase 2 alone, and can run beside US1, though both edit `wfctl/_review.py`.
- Phase 6 follows the stories. T022 and T023 can run in parallel.

### Within each story

Tests are written and seen to fail before the implementation task that satisfies them.

## Parallel Example: User Story 1

```text
Task: "T010 the issue's example test in tests/test_review.py"
Task: "T011 no stacking and count from 0 in tests/test_review.py"
Task: "T012 cap lowered after a sign-off in tests/test_review.py"
Task: "T013 old sign-off file in tests/test_review.py"
```

These share one file, so they're parallel to write and serial to commit.

## Implementation Strategy

The MVP is Phases 1 - 3: the issue's example works, and a release PR still merges on a sign-off. Phase 5 keeps status honest, and #665's status row reads the same function once it lands. Phase 6 updates the guidance agents read, so it ships in the same PR as the behavior.
~~~~
