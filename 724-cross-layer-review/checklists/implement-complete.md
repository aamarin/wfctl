Implementation complete: 2026-11-06

## Tasks at completion

~~~~markdown
# Tasks: Reviewers check that each layer accepts the same input

**Input**: Design documents from `specs/724-cross-layer-review/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/review-report.md, quickstart.md

**Tests**: The change is prose in skill files, so the suite checks structure (the pass count and cross-references) and the reviewer runs in quickstart.md check behavior. Every story names its verification below.

**Design record**: `docs/architecture/design/724-cross-layer-checks-in-rubric.md` (proposed). It puts the two checks in the shared rubric as passes 7 and 8, with no new group, no new skill, and no `_review*.py` edits. No task below reverses it.

**Plan review findings folded in**: the plan review left one MAJOR and seven MINOR findings open (`plan-review.md`). Tasks take the cheap fixes where they land: PR-002 in T004, PR-003 in T013, PR-004 in T011, PR-005 in T009 and T012, PR-006 in T014, PR-007 in T003, and PR-008 in T009. PR-001 stays open. Pass 8 follows FR-007 as written, reading earlier fixes only from the commits the review covers, so a fix made in an earlier panel round isn't in front of the reviewer.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (US1, US2, US3)

---

## Phase 1: Setup

**Purpose**: Confirm the starting point the edits assume.

- [x] T001 Confirm the baseline: `uv run pytest -q tests/test_review_fanout_skill.py` passes with 6 passes asserted at `tests/test_review_fanout_skill.py:165`, and `grep -n "six\|five passes" wfctl/agents/` lists only the lines in plan.md's Source Code section plus the `Step 4 — The six passes` heading and the red flag at `wfctl/agents/skills/code-review/SKILL.md:161`. Verify with the command output.

---

## Phase 2: Foundational

**Purpose**: Make room for two more passes, so the story phases add content rather than rename things.

- [x] T002 In `wfctl/agents/skills/code-review/SKILL.md`, rename the heading `## Step 4 — The six passes` to `## Step 4 — The eight passes`, and change the red flag "ignoring the other five passes" to "ignoring the other seven passes". In `tests/test_review_fanout_skill.py:165`, change `assert len(passes) == 6` to `== 8`. Verify with T006 (the test fails until passes 7 and 8 exist, which is expected here).

**Checkpoint**: the heading and the test agree on eight passes. Story work can begin.

---

## Phase 3: User Story 1 - A reviewer finds a value one layer accepts and the next refuses (Priority: P1) 🎯 MVP

**Goal**: Every code reviewer follows each outside input through each layer and reports a value one layer accepts and the next refuses.

**Independent Test**: One reviewer with the changed rubric over PFMS `7cde6095..996f5e5c` reports the interest-rate mismatch (the form accepts any rate and the server caps it at 100) at WARNING or above.

### Verification

- `uv run pytest -q tests/test_review_fanout_skill.py` passes with 8 passes.
- The PFMS reviewer run in T009.

### Implementation

- [x] T003 [US1] Add `**7. Input trace**` to Step 4 of `wfctl/agents/skills/code-review/SKILL.md`, after `**6. Over-engineering**`. The heading must match `^\*\*\d\. ([A-Za-z][A-Za-z &-]*)\*\*`. The pass:
  1. Lists every value from outside the program that the change adds or changes, such as form fields, request bodies, CLI flags, config and data files, and environment variables (FR-002).
  2. Follows each one through every layer that checks, converts, or stores it, into unchanged code too, by following names and calls through the repository.
  3. Writes down each layer's limit (type, nullability, unit, bounds, precision, storage range), or `unknown (<reason>)` when a layer states none or can't be read (FR-003).
  4. Reports a finding only for a concrete contradiction, with a counterexample value and the file and line on both sides (FR-004). When a layer between two others is unknown, it compares the two known layers and says in the finding which layer was unknown (PR-007).
  5. Uses the neutral example from research.md R5: a signup form that allows a 40-character username where the server caps it at 32 (FR-011, FR-013).

  Verify with T006 and T009.
- [x] T004 [US1] In Step 5 of `wfctl/agents/skills/code-review/SKILL.md`, add one line under the severity table: a value one layer accepts and the next refuses is WARNING or above, whatever error the user sees, because the user can never save it (FR-008). Extend the Step 5 report example with the `Inputs traced` list from `contracts/review-report.md`, placed after the findings and before `net:` and the verdict. Replace the contract's `--rounds flag` row with a neutral CLI case, such as `--retries flag  parser: any int · config schema: 0–10   ← mismatch`, so no example names wfctl's own config (PR-002, FR-013). Verify with T006 and by reading the example back against `contracts/review-report.md`.
- [x] T005 [P] [US1] Update the description in `wfctl/agents/skills/code-review/SKILL.md` frontmatter and in `wfctl/agents/commands/code-review.md` from "six lenses" to "eight lenses", and add "input trace" and "sibling paths" to each lens list (FR-012). Verify with T013.
- [x] T006 [US1] Run `uv run pytest -q tests/test_review_fanout_skill.py` and confirm it passes with 8 passes. This is the checkpoint for T002 - T005, and it needs pass 8 from T007 too, so run it after T007.

**Checkpoint**: pass 7, the WARNING floor, and the trail's input list are in the rubric. The pass-count test stays red until T007 adds pass 8, so T006 runs after T007 and closes both phases.

---

## Phase 4: User Story 2 - A reviewer finds a fix that one path got and a sibling path didn't (Priority: P2)

**Goal**: Every code reviewer checks each rule or fix the change adds against every other place that writes the same value or sink.

**Independent Test**: The same PFMS run reports that the plan goal writes the 32-bit budget column without the guard the paycheck got, at WARNING or above.

### Verification

- `uv run pytest -q tests/test_review_fanout_skill.py` passes with 8 passes.
- The PFMS reviewer run in T009.

### Implementation

- [x] T007 [US2] Add `**8. Sibling paths**` to Step 4 of `wfctl/agents/skills/code-review/SKILL.md`, after pass 7. The pass:
  1. Reads each rule or fix the change adds, from the diff and from the commit messages when the review covers commits (FR-006).
  2. Searches for every other place that writes the same value or sink, including unchanged code, and checks whether each one enforces the rule.
  3. Reports a sibling that lacks the rule with the original rule and the sibling, each with its file and line, and reports new code that brings back a pattern an earlier commit in the review fixed (FR-007).
  4. Uses the neutral example from research.md R5: a commit that escapes HTML in a comment preview, where every other view of the same comment text should be checked (FR-011, FR-013).

  Verify with T006 and T009.
- [x] T008 [US2] Extend the Step 5 report example in `wfctl/agents/skills/code-review/SKILL.md` with the `Rules checked` list from `contracts/review-report.md`, after `Inputs traced`. Verify by reading the example back against the contract.
- [x] T009 [US2] Run the SC-001 and SC-002 check after `uv run wfctl install-skills`. Dispatch one fresh reviewer with the brief at `$(wfctl state-dir)/experiment-pfms-1011/brief.md` and the installed `.agents/skills/code-review/SKILL.md` as its rubric, over PFMS `7cde6095..996f5e5c`, read-only.
  1. Pass for SC-001: the report names the interest-rate mismatch and the plan goal overflow, each at WARNING or above.
  2. Pass for SC-002: the `Inputs traced` list names every input listed under `## Per-input trace` in `$(wfctl state-dir)/experiment-pfms-1011/reports/t1.md`, with a limit or `unknown (<reason>)` at each layer (PR-005).
  3. On a miss, revise the pass text and run once more. If the second run also misses, stop and tell the user, since the design record treats that as evidence against its decision (PR-008).

**Checkpoint**: both passes are in the rubric, and the PFMS run finds both bugs.

---

## Phase 5: User Story 3 - The developer can see what each reviewer checked (Priority: P3)

**Goal**: A reviewer's report shows what it traced and checked, and a change with nothing to trace says so in one line.

**Independent Test**: The PFMS run's report carries both lists (T009). A review of a docs-only change carries the one-line statement instead of empty lists.

### Verification

- The docs-only reviewer run in T012.

### Implementation

- [x] T010 [US3] In Step 5 of `wfctl/agents/skills/code-review/SKILL.md`, state the trail's rules from `contracts/review-report.md`: a consistent input takes one line (FR-009), an unreadable layer reads `unknown (<reason>)`, and a change with no inputs and no new rules writes one line in place of both lists, `Inputs traced: none — the change reads no outside value and adds no rule` (FR-010). Verify with T012.
- [x] T011 [P] [US3] In `wfctl/agents/skills/requesting-code-review/SKILL.md:15`, change "(the six-pass rubric)" to "(the rubric)". The `vendor-upstream-skills` record lists this skill as derived from obra/superpowers, so dropping the count keeps the pointer true through later pass changes and leaves an upstream pull nothing to conflict with (PR-004). Verify with T013.
- [x] T012 [US3] Run the SC-003 check. Dispatch one fresh reviewer with the installed rubric over commit `98a4536` in this repo (`docs(scans): clarify scan for #724`, a docs-only commit), read-only, with this brief: "Review commit 98a4536 in this repository with the code-review rubric. Read-only: change no file." Pass when the report carries the one-line `none` statement and no empty lists (PR-005).

**Checkpoint**: the trail's format is in the rubric, and both trail cases show up in real reports.

---

## Phase 6: Polish & cross-cutting

- [x] T013 [P] Search for stale counts and lens lists: `grep -rn "six-pass\|six lenses\|six passes\|five passes\|six instructions" wfctl/agents/` prints only `wfctl/agents/skills/fanning-out-code-review/SKILL.md:194`, "the six instructions above", which counts dispatch instructions rather than passes. Change the example row at `wfctl/agents/skills/fanning-out-code-review/SKILL.md:415` from "six passes" to "eight passes". Confirm both descriptions from T005 name the two new passes (FR-012, PR-003).
- [x] T014 [P] Confirm the panel is unchanged: `git diff --stat main -- wfctl.json 'wfctl/_review*.py'` prints nothing (FR-014, SC-004, PR-006).
- [x] T015 Write the release note: `uv run towncrier create 724.change.md --content "Every code reviewer now follows each outside input through the layers that check or store it, and checks every other place a fix should also apply. Reports carry a short list of what was traced."`. Verify with `uv run wfctl verify`.
- [x] T016 Run the definition of done: `uv run pytest -q`, `uv run ruff check wfctl/ tests/`, `uv run mypy`, then `uv run wfctl install-skills` and `uv run wfctl doctor`. Validate the polish phase with these commands — merge gate.

---

## Dependencies & execution order

- Phase 1, then Phase 2, then US1 and US2. Both stories edit `code-review/SKILL.md`, so their edits run in sequence: T003, T004, T007, T008, then T006.
- T005 and T011 edit other files and can run beside the story work.
- T009 and T012 need `uv run wfctl install-skills` first, so the installed rubric is the edited one.
- US3 depends on US1 and US2, since the trail lists what passes 7 and 8 produce.
- Phase 6 runs last. T013 and T014 can run in parallel.

## Parallel examples

- T005 (both descriptions) and T011 (`requesting-code-review`) while T003 is written.
- T013 and T014 together at the end.

## Implementation strategy

US1 alone is the MVP: pass 7, the WARNING floor, and the `Inputs traced` list catch the interest-rate bug. US2 adds pass 8 for the overflow, and US3 adds the trail's rules and the docs-only check. All three edit one file, so they land in one PR.
~~~~
