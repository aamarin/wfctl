# Analyze scans — #364

## Session 2026-09-13

- Verdict: satisfied
- Scanned: spec.md, plan.md, tasks.md — all three present and read
- Findings: 6 · Critical: 0 · Acted on: 5 · Accepted: 1
- Detail: /Users/andremarin/Development/wfctl-specs/364-two-permission-systems/checklists/analysis-report.md

Nobody was present to answer step 8's remediation offer: the run was asked for
unattended. Every finding below was settled against the policy in the command
wrapper rather than left waiting — five were in scope and were applied to the
artifacts, one was accepted with its reason. Nothing was filed, so there is no
`### Filing` block and no finding somebody still has to carry.

### Coverage

| Pass | Status |
| --- | --- |
| A · Duplication | Outstanding (1 LOW, accepted) |
| B · Ambiguity | Clear |
| C · Underspecification | Resolved (1 MEDIUM) |
| D · Constitution alignment | Clear |
| E · Coverage gaps | Resolved (1 HIGH) |
| F · Inconsistency | Resolved (1 HIGH, 2 MEDIUM) |
| G · Design-record contradiction | Clear (1 record read) |
| Requirement-to-task coverage | 100% |

Coverage is post-remediation. It was 96% when the passes ran — 26 of 27
requirement keys — and the one gap is finding E1 below.

`D · Constitution alignment` is `Clear` against a substitution rather than
against a constitution: this repository has no `.specify/memory/constitution.md`,
and `plan.md` substitutes `AGENTS.md` § Definition of done, § Testing conventions
and § Code style plus the records `wfctl arch context` prints, recording the
substitution in its Complexity Tracking table as the template requires. The pass
read those gates and found no conflict; it did not skip for want of a file.

### Findings

- **E · Coverage gap, HIGH** — FR-009, *there must be no way to report a success
  through this command*, carried zero tasks and zero tests. It is the narrow
  exception to `wfctl-runs-the-verification` (accepted) that this whole feature
  turns on, and the level-3 record's own argument is that the exception is
  enforced by the shape of the command surface rather than by prose. Nothing
  failed when that shape changed.
  → Fixed: added `T010a` to `tasks.md` Phase 3 —
  `test_no_spelling_of_blocked_records_a_success`, asserting against the
  command's own parameter set that its only recordable outcomes are a block and
  a clearing. Decided against renumbering T011–T039 to make room: every later ID
  is cross-referenced from the dependency graph, the parallel-opportunities list
  and three phase checkpoints, and a renumber is the "materially larger" route
  out of scope. A letter suffix keeps every existing reference valid.

- **F · Inconsistency, HIGH** — SC-005 and User Story 2's *Why this priority*
  both asserted that the blocked agent cannot reach the release. FR-013,
  clarification Q4 and `contracts/cli.md` all make `wfctl blocked --clear`
  ungated and explicitly agent-reachable, on the rule that leaves `wfctl issue
  close` ungated. So SC-005 was a measurable outcome the design deliberately does
  not deliver, and a test written against it would have failed by design rather
  than by defect.
  → Fixed: both restated to the property that does hold — the asymmetry is on
  *what may be reported*, not on who may clear, and no spelling of the reporting
  command records a success. Decided against the other repair, gating `--clear`
  to match SC-005: that reverses clarification Q4 and the level-3 record's
  Decision, which is a design change and not an analysis finding.

- **F · Inconsistency, MEDIUM** — the edge case *An action spelling that matches
  nothing* said the report "holds whatever step owns that action", and that an
  action belonging to no step holds nothing. FR-010 and `data-model.md` say the
  opposite: the step is inferred at call time, stored on the event, and the
  report names no step of its own. An implementer reading the edge case would
  have built an action-to-step mapping the design does not have.
  → Fixed: reworded to FR-010's rule, and now says what an odd spelling actually
  costs — the release rather than the hold, since a clearing or a recorded
  success under a different string does not match it.

- **C · Underspecification, MEDIUM** — T013 read as *refuse when `--reason` is
  absent* across every mode, which would refuse the `--clear` mode T023 builds.
  `contracts/cli.md` gives `--clear` exit 0 always.
  → Fixed: scoped the requirement to the reporting mode, and named the conflict
  it would otherwise create so the next reader does not re-derive it.

- **F · Inconsistency, MEDIUM** — SC-003 said the authority report must be true
  in *all seven grant states*. `_NOTIFY_LINES` (`wfctl/cli.py:179`) carries seven
  keys and `_notify_line` builds an eighth rendering for `label`, which names the
  issue the label is on. `plan.md` and T029 both say eight; `research.md`
  reconciles the two in prose, but SC-003 is the line a reader verifies against.
  → Fixed: SC-003 now reads eight renderings and names both halves — the seven
  keyed states plus the one built for a label.

- **A · Duplication, LOW** — FR-020 restates FR-012's most-recent-event rule for
  the success case.
  → Accepted: FR-020 carries the fact FR-012 does not — that a block and the
  success answering it are matched on the action's *name* — and that fact is
  where both the level-3 record and `data-model.md` say this design breaks first.
  Merging them into FR-012 would lose it, and splitting the matching rule into a
  requirement of its own trades one duplicate for one more requirement.
  Not filed: nothing outstanding to file. The duplication is accepted as the
  shape the spec should keep, not deferred to someone.

### Deferred

- **Both design records are `proposed`, and stay that way.** The level-2
  `the-agent-reports-the-block-wfctl-never-saw` and the level-3
  `364-the-block-report-is-its-own-verb` bind this work as designed. Promoting
  them is T037, and it belongs to a person: `wfctl arch accept` records where a
  human agreed and never decides that an agreement happened
  (`a-human-accepts-a-decision`). Pass G graded against `proposed` accordingly —
  HIGH rather than CRITICAL had it found a reversal, which it did not.
