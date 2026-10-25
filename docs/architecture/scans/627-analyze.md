# Analyze scan: #627

## Session 2026-10-25

- Verdict: satisfied
- Scanned: spec.md, plan.md, tasks.md — all three present and read
- Findings: 6 · Critical: 0 · Acted on: 5 · Accepted: 1
- Detail: /Users/andremarin/Development/wfctl-specs/627-ci-review-check/checklists/analysis-report.md

### Coverage

| Pass | Status |
| --- | --- |
| A · Duplication | Clear |
| B · Ambiguity | Clear |
| C · Underspecification | Clear |
| D · Constitution alignment | Clear (no constitution; the `AGENTS.md` gates the plan uses are carried by the tasks) |
| E · Coverage gaps | Resolved (1 MEDIUM, 2 LOW, tasks fixed) |
| F · Inconsistency | Outstanding (1 MEDIUM; 1 HIGH and 1 LOW resolved) |
| G · Design-record contradiction | Clear (3 records read) |
| Requirement-to-task coverage | 100% |

### Findings

- **F · Inconsistency, HIGH**: T019 had `relay` pick the group whose latest run expects the reviewer's id, and refuse only when both runs do. FR-010a says `relay` exits 1 naming both groups whenever two groups share the first letter.
  → Fixed: T019 now refuses whenever two groups match, with the example of a group renamed on the branch (`money-rules` to `money`) and a remedy telling the user to rename the group the branch added. T018 tests the refusal. We decided against keeping the run-based pick, because it changes a requirement the spec already settled.
- **F · Inconsistency, MEDIUM**: the plan says `review check` uses the FR-010a group list. T030 keeps today's name check and loads no group list, so a broken trunk config or a missing trunk can't stop a completed run from recording its note (PR-024).
  → Accepted: the maintainer chose this session to carry PR-024 in the tasks rather than edit the plan, since a plan edit needs another plan review. FR-010a still holds, because `review check` accepts every group on the list. T030 updates `contracts/cli.md` to match.
    Not filed: the departure is decided and carried by T030, so an issue would track nothing that isn't already a task.
- **E · Coverage gaps, MEDIUM**: no task tested SC-003, where a clean merge of `main` into a reviewed branch passes the check with no new review.
  → Fixed: T032 adds that case. We decided against leaving it to the post-merge throwaway PR, because a scratch repository can test it before merge.
- **E · Coverage gaps, LOW**: no task checked FR-005, that the state directory record is still written beside the note.
  → Fixed: T024 checks that `last-reviewed.json` is still written. We decided against relying on the existing tests alone, because T030 changes the command those tests cover.
- **E · Coverage gaps, LOW**: the workflow test didn't check the step that fetches `refs/notes/wfctl-review`, which FR-017 requires.
  → Fixed: T035 checks it. We decided against leaving it to the after-merge run, because a missing fetch makes every PR fail and the YAML test catches it for free.
- **F · Inconsistency, LOW**: `contracts/review-note.md` says a group line counts when "the current `wfctl.json`" lists the group, while `data-model.md` and FR-015 say the trunk's or the head's.
  → Fixed: T015 updates the contract's reader rule 3 to match. We decided against editing the contract now, because contracts are outside the three artifacts this step edits.

### Filing

None. The one accepted finding is carried by T030 and needs no issue.

### Deferred

- **SC-001's GitHub half**: the `review` job only runs once it is on `main`, so quickstart steps 2 - 5 run after merge, on a throwaway PR. That belongs to the maintainer after merge, not to this scan.
