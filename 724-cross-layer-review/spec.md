# Feature Specification: Reviewers check that each layer accepts the same input

**Feature Branch**: `724-cross-layer-review`  
**Created**: 2026-11-06  
**Status**: Draft  
**Input**: User description: "#724: two new passes in the code-review rubric (input trace across layers, sibling-path check), report trail, WARNING floor for layer mismatches. design.md in FEATURE_DIR carries the direction."

## Clarifications

### Session 2026-11-06

- Q: What counts as an input for the trace pass? → A: Any value from outside the program: form fields, request bodies, CLI flags, config and data files, and environment variables.
- Q: Where does the sibling-path pass find the fixes when the review covers no commits, such as uncommitted changes? → A: From the diff itself, and from the commit messages when the review covers commits.

## User Scenarios & Testing _(mandatory)_

The users here are the code reviewers on wfctl's review panel, and the developer who reads their reports before a PR opens. Today the rubric every code reviewer follows has six passes, and none of them asks the reviewer to compare one layer's limit on an input against the next layer's. A PFMS branch passed a three-reviewer panel with two bugs of that shape still in it.

### User Story 1 - A reviewer finds a value one layer accepts and the next refuses (Priority: P1)

A code reviewer reviewing a change that adds or edits inputs lists each input and follows it through every layer it passes: the form, client validation, the request, server validation, any conversion, and storage. At each layer the reviewer writes down the limit. When one layer accepts a value the next refuses, the reviewer reports it with a value that shows the mismatch and the file and line on both sides.

**Why this priority**: This is the bug class the panel missed and the reason for the issue. Without it the change delivers nothing.

**Independent Test**: Run one reviewer with the changed rubric over PFMS `7cde6095..996f5e5c` and confirm it reports the interest-rate mismatch: the form accepts any rate and the server caps it at 100.

**Acceptance Scenarios**:

1. **Given** a change where the form accepts a value the server refuses, **When** a code reviewer follows the rubric, **Then** the report carries a finding naming the input, a counterexample value, and the file and line of both layers.
2. **Given** a change where the server accepts a value that doesn't fit the storage column, **When** a code reviewer follows the rubric, **Then** the report carries a finding naming the input, a counterexample value, and the file and line of the server rule and the column.
3. **Given** a layer the reviewer couldn't read, **When** the reviewer writes the trail, **Then** that layer's limit reads "unknown" with the reason, not a guess.

---

### User Story 2 - A reviewer finds a fix that one path got and a sibling path didn't (Priority: P2)

A code reviewer reads each rule or fix the branch's commits add, then searches for every other place that writes the same value or sink, including code the branch didn't change. When a sibling doesn't enforce the rule, the reviewer reports it with the original rule and the sibling, each with its file and line.

**Why this priority**: The PFMS overflow was fixed for the paycheck and missed for the plan goal two commits later. It's the second bug the panel missed, and the input trace alone may not reach it when the sibling's input looks consistent at each layer.

**Independent Test**: The same PFMS run reports that the plan goal writes the 32-bit budget column without the guard the paycheck got.

**Acceptance Scenarios**:

1. **Given** a branch whose commits add a guard to one writer of a sink, **When** a code reviewer follows the rubric, **Then** the reviewer checks every other writer of that sink and reports each one without the guard.
2. **Given** new code on the branch that brings back a pattern an earlier commit on the branch fixed, **When** a code reviewer follows the rubric, **Then** the report carries a finding naming the earlier commit.

---

### User Story 3 - The developer can see what each reviewer checked (Priority: P3)

The developer reading a reviewer's report sees, after the findings, a short trail: each input with its limit at each layer, and each rule with the places checked. An input that's consistent across layers takes one line. A change with no inputs and no new rules says so in one line.

**Why this priority**: The trail is what makes a skipped check visible. A reviewer that writes "consistent" without opening a layer has to name the limit and file at that layer, so a skimmed pass shows up as gaps.

**Independent Test**: The PFMS run's report carries both lists. A review of a docs-only change carries the one-line statement instead of empty lists.

**Acceptance Scenarios**:

1. **Given** a change that touches inputs, **When** the reviewer writes the report, **Then** the trail lists each input with its limit at each layer it passes.
2. **Given** a change that adds no input and no rule, **When** the reviewer writes the report, **Then** the report says so in one line.

---

### Edge Cases

- A value is refused by the next layer with a clear error message. It's still at least a WARNING, because the user can never save that value.
- A change touches many inputs. Consistent inputs take one line each so the trail doesn't crowd out the findings.
- The other layers aren't in the diff. The reviewer follows names and calls through the repository, and writes "unknown" with the reason for any layer it can't reach.
- The rubric's examples could lead a reviewer toward a known answer. They use neutral cases (a username length, HTML escaping in a comment preview), not the PFMS bugs.

## Requirements _(mandatory)_

### Functional Requirements

- **FR-001**: The `code-review` rubric MUST carry an input-trace pass after its six existing passes, which every reviewer following the rubric runs.
- **FR-002**: The input-trace pass MUST ask the reviewer to list every value from outside the program that the change adds or changes, such as form fields, request bodies, CLI flags, config and data files, and environment variables, and to follow each one through every layer that checks or stores it, into unchanged code too.
- **FR-003**: The input-trace pass MUST ask the reviewer to write down each layer's limit (type, nullability, unit, bounds, precision, storage range), and to write "unknown" with the reason when a layer states none or can't be read.
- **FR-004**: The input-trace pass MUST report a finding only for a concrete contradiction between adjacent layers, with a counterexample value and the file and line on both sides.
- **FR-005**: The rubric MUST carry a sibling-path pass after the input-trace pass, which every reviewer following the rubric runs.
- **FR-006**: The sibling-path pass MUST ask the reviewer to read each rule or fix the change adds, from the diff and from the commit messages when the review covers commits, search for every other place that writes the same value or sink, including unchanged code, and check whether each one enforces the rule.
- **FR-007**: The sibling-path pass MUST report a sibling that lacks the rule with the original rule and the sibling, each with its file and line, and MUST report new code that brings back a pattern an earlier commit on the branch fixed, when the review covers commits.
- **FR-008**: The rubric MUST rate a value one layer accepts and the next refuses at WARNING or above, whatever error the user sees.
- **FR-009**: The rubric's report format MUST add a trail after the findings: each input with its limit at each layer, and each rule with the places checked. A consistent input takes one line.
- **FR-010**: A review of a change with no inputs and no new rules MUST say so in one line in place of the trail.
- **FR-011**: The two passes' examples MUST be neutral cases that aren't drawn from the PFMS branch.
- **FR-012**: Every place wfctl states the rubric's pass count or lists its passes MUST match the new count.
- **FR-013**: The rubric MUST stay general. It MUST NOT carry rules or examples that only one repository has.
- **FR-014**: The change MUST NOT change which review groups run, how many reviewers each group has, or how rounds are counted.

## Success Criteria _(mandatory)_

### Measurable Outcomes

- **SC-001**: One reviewer given the changed rubric, over PFMS `7cde6095..996f5e5c`, reports both the interest-rate mismatch and the plan goal overflow, each at WARNING or above. Today's rubric found neither across three reviewers.
- **SC-002**: That reviewer's trail names every input the PFMS branch changes that today's trace reviewer listed, with a limit or "unknown" at each layer.
- **SC-003**: A review of a docs-only change carries one line in place of the trail, and no empty lists.
- **SC-004**: The review panel's groups, reviewer counts, and round cap are the same before and after the change.

## Validation Strategy _(mandatory)_

- `uv run pytest -q`, `uv run ruff check wfctl/ tests/`, and `uv run mypy`, all green. The suite checks that skills ship and cross-reference correctly.
- `uv run wfctl install-skills`, then `uv run wfctl doctor` reporting no drift, so the installed rubric is the edited one.
- The PFMS run in SC-001 and SC-002: one reviewer, the saved experiment brief, and the installed rubric, over `7cde6095..996f5e5c`, read-only.
- One reviewer over a docs-only commit in this repository, for SC-003.
- A search of `wfctl/agents/` for the old pass count, for FR-012.
- A release note, `changes/724.change.md`, which `wfctl verify` checks.

## Assumptions

- Pre-specify design context loaded from specs/724-cross-layer-review/design.md.
- The two procedures still find the bugs when they sit beside six other passes, though in the experiment each ran alone. SC-001 tests this.
- A reviewer can find the other layers by following names and calls through the repository, without a map of the project's layers. The experiment's trace and sibling reviewers did.
- `code-review` is a wfctl-owned skill, edited in place since #47, so no upstream pull reverts the change.
