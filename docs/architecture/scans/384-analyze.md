# Analyze scan — #384

## Session 2026-09-15

- Verdict: satisfied
- Scanned: spec.md, plan.md, tasks.md — all three present and read
- Findings: 3 · Critical: 0 · Acted on: 3 · Accepted: 0
- Detail: /Users/andremarin/Development/wfctl-specs/384-strip-allow-notify/checklists/analysis-report.md

Run unattended at the user's request ("go and can you go unattended?"). Step 8's
remediation offer was settled by the wrapper's policy. Every finding was in
scope and was applied.

### Coverage

| Pass | Status |
| --- | --- |
| A · Duplication | Clear |
| B · Ambiguity | Clear |
| C · Underspecification | Resolved (1 MEDIUM, tasks fixed) |
| D · Constitution alignment | Clear |
| E · Coverage gaps | Resolved (1 MEDIUM, 1 LOW, tasks fixed) |
| F · Inconsistency | Clear |
| G · Design-record contradiction | Clear (2 records read) |
| Requirement-to-task coverage | 100% |

### Findings

- **C · Underspecification, MEDIUM** — `tasks.md` split the CLI change (phase 4) and the skill changes (phase 6) into phases that each end in a "merge gate", without saying whether they land together. `384-the-agent-reports-through-two-flat-verbs` says in Consequences: "Every skill call site and both docs change in the same commit as the CLI." A commit between the two would install skills that call commands which no longer exist.
  → Fixed: the Dependencies section of `tasks.md` now says phases 4–6 land in one commit, quotes the record, and says the "merge gate" lines are checkpoints inside that commit. Decided against reordering the phases so the skills come first: skills can't name `report-block` before it exists, so the other order breaks just as badly. Not a pass G finding, because no task said "separate commits". The gap was what the tasks left unsaid.
- **E · Coverage gaps, MEDIUM** — T035 removes `Bash(wfctl notify*)` from `speckit.decompose.md`'s `allowed-tools`, and `tests/test_skill_cross_references.py::test_decompose_allows_the_commands_its_notify_gate_needs` asserts it is there. No task updated that test, so the phase 6 merge gate would fail.
  → Fixed: T029 now rewrites that test to require `wfctl report-block`, and renames it. Decided against deleting the test: its first half (that `Write` and `wfctl issue create` are allowed) still guards the unattended `decompose` run it was written for.
- **E · Coverage gaps, LOW** — the spec's edge case "a leftover local grant file … changes nothing" had no verification path.
  → Fixed: T020 adds a case with a leftover `notify.json` holding `denied`. `wfctl issue create` still reaches the tracker, and `status` output is identical with and without the file. Decided against treating the grep in Phase 5 as enough: it proves the reader code is gone, not that nothing else picks up the file.

### Filing

None. Every finding was applied.

### Deferred

None.
