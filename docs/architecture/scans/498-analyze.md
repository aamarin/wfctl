# Analyze scan: #498

## Session 2026-09-26

- Verdict: satisfied
- Scanned: spec.md, plan.md, tasks.md; all three present and read
- Findings: 9 · Critical: 1 · Acted on: 9 · Accepted: 0
- Detail: /Users/andremarin/Development/wfctl-specs/498-check-drawing-at-design-gate/checklists/analysis-report.md

### Coverage

| Pass | Status |
| --- | --- |
| A · Duplication | Clear |
| B · Ambiguity | Resolved (1 MEDIUM) |
| C · Underspecification | Resolved (2 LOW) |
| D · Constitution alignment | Clear (no constitution; the plan's substituted `AGENTS.md` gates hold) |
| E · Coverage gaps | Resolved (1 MEDIUM, 1 LOW) |
| F · Inconsistency | Resolved (1 CRITICAL, 1 MEDIUM, 2 LOW) |
| G · Design-record contradiction | Clear (1 record read) |
| Requirement-to-task coverage | 100% |

### Findings

- **F · Inconsistency, CRITICAL**: SC-004 required every existing design-gate test to pass unchanged, and the US3 merge gate required `tests/test_pipeline_commands.py` to be untouched. At least four existing tests (in `test_pipeline_commands.py`, `test_storyctl.py`, `test_agent_session.py`, and `test_pipeline_state_names.py`) use a proposed record with no drawing as the answer to the boundary question and assert brainstorm is done. FR-001 now judges that record, so those tests fail on their fixture and the merge gate could never pass.
  → Fixed: SC-004 now requires the assertions unchanged and gives drawing-less fixtures a record that passes `accept_blockers`; a new task (T013) does that and names the four files; the US3 gate checks that no `assert` line changed. Decided against narrowing the gate to spare those fixtures: FR-001 and the design judge every proposed record, and a proposed record with no drawing is exactly what the gate exists to hold.
- **B · Ambiguity, MEDIUM**: the edge case "the reason names the first by slug" read two ways, and the plan had chosen slug order.
  → Fixed: the spec now says "the first in slug order", with the remedy in the same order.
- **F · Inconsistency, MEDIUM**: FR-008 said the dry run prints "every refusal `accept` would make", while `accept` stops at the first refusal category and the clarification says the dry run prints only what `accept` would print.
  → Fixed: FR-008 now says it prints what `accept` would print up to the write, including every blocker once it reaches that check.
- **E · Coverage gaps, MEDIUM**: the edge case for an unanswerable git read or an out-of-tree arch root had no test with a failing record in it.
  → Fixed: T019 adds a failing proposed record under an out-of-tree root that is not judged.
- **F · Inconsistency, LOW**: US2's scenarios were numbered 1, 2, 6, 3, 4, 5.
  → Fixed: scenario 6 moved to the end, so every `US2-6` reference still holds.
- **C · Underspecification, LOW**: the snapshot task said "regenerate" and named no command.
  → Fixed: it points to the command in the snapshot test's module docstring.
- **C · Underspecification, LOW**: T011's verify filter matched test names that do not exist yet.
  → Fixed: it verifies against the test file and names the tasks whose tests now pass.
- **E · Coverage gaps, LOW**: FR-008 says the dry run writes no file, and the test checked only the record.
  → Fixed: the dry-run test compares every file under the arch root.
- **F · Inconsistency, LOW**: the plan's "15 - 20 tests" did not match the 21 test items it listed, or the new fixture work.
  → Fixed: it now says about 25 new tests and fixture edits in 3 - 5 existing files.

Pass G read `docs/architecture/design/498-the-fix-line-travels-with-the-reason.md`, which is `proposed`. Its Decision and Consequences are implemented as written by T010 - T012, and no task parses a slug out of a reason or runs the check twice.

### Filing

Nothing was filed. Every finding was in scope and fixed.

### Deferred

Nothing was deferred.
