# Delivery Plan: orchestrate loop bound (332)

One issue, one PR. All four PR-boundary signals point at bundling, and the
feature is M by files touched.

## PR Decomposition

| PR | Tasks | Files Touched | Size | Merge Condition |
|----|-------|--------------|------|----------------|
| the branch's PR | T001–T012 | `wfctl/_stall.py` (created), `wfctl/_pipeline.py` (modified), `wfctl/cli.py` (modified), `wfctl/agents/skills/speckit-orchestrate/SKILL.md` (modified), `tests/test_stall.py` (created) | M | `pytest`, `ruff`, `mypy` and `wfctl doctor` green, plus one watched unattended run that halted on its own |

Boundary signals, all four applied:

- **File conflict risk** — no. The phases are sequenced and no two groups edit
  one file concurrently.
- **Reviewability** — bundle. A reviewer cannot judge the counting without the
  payload field that exposes it or the skill branch that acts on it.
- **Mergeable increment** — bundle. The counting module alone changes no
  behaviour; shipping it without the other two leaves the loop exactly as
  unbounded as it is now.
- **Story independence** — no. All three user stories run through the same code
  path and share the same state.

## Issue Grouping Map

| Issue | Tasks | Title | Estimate | Closes With |
|-------|-------|-------|----------|-------------|
| #332 | T001–T012 | `[332] speckit-orchestrate has no loop bound` | M | this branch's PR |

No issue is created by this step. The feature maps to the issue that already
exists, which is the single-issue default — and this run was granted no authority
to notify anyone, so creating one was never available to it either.

## Parallelization Waves

| Wave | Mode | Tasks | Gate / Notes |
|------|------|-------|-------------|
| 0 | Sequential | T001 → T002 | the digest exists before anything counts with it |
| 1 | Parallel | T003 ‖ T004 | the tests and the report field touch different files |
| 2 | Sequential | T005 → T006 → T007 | all three are in files the earlier waves establish |
| 3 | Sequential | T008 → T009 | the skill is edited, then installed and read back |
| 4 | Sequential | T010 → T011 → T012 | proof last: tests, then the watched run, then the repo's definition of done |
