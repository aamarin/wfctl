# Plan Review Report

Review state: completed
Review type: re-review

## Reviewed inputs

| Artifact | Content identity | Role |
| --- | --- | --- |
| plan.md | b3a6055f26ad3682d1e444f7f864c75de6c32447 | technical strategy |
| spec.md | d94cd4dcff98a52399770c7e04e070cad8e63d87 | requirements |
| .specify/memory/constitution.md | absent | constitution |
| design.md | da3188fe0adbff1a41e466028d96ca6fe8a37b2d | design-record index |
| research.md | db347b387762792da9328bf029c9ad661d7512e2 | planning evidence |
| data-model.md | e950c13cfde3f24fa6e8acfdf3b23ca8e232f3c7 | planning evidence |
| quickstart.md | a3b8e3dd8c7c73f57039573a90f4ed20a668b133 | planning evidence |
| docs/architecture/deletion-follows-recorded-files.md | 1293d70d8f186e31156d9f606e1494488baae550 | level-2 record the plan names (proposed) |
| docs/architecture/install-modes.md | 4233b4dbe4343f4c734e175db91417108db59428 | accepted record the plan's gates cite |
| docs/architecture/a-rule-is-expressed-as-a-check.md | 81e9a7d67301935f73a6e3b97c9b06284310879f | accepted record the plan's gates cite |
| plan-review.plan.md | 627fb00f0756dc7b046dd32181e69c7b7d62ba85 | base of this re-review |

## Review scope

- Re-review: the plan copy's identity equals the earlier report's `plan.md` row.
- The plan diff is one change, in `plan.md §Technical Context`, Constraints.
  The deletion rule is now scoped to a repository that has been redone or
  freshly installed, and a new sentence says a repository not redone can still
  lose a path at a pruning install, as a cost the record accepts. It was
  reviewed together with `plan.md §Summary`, which describes the same cost, and
  `§Test Plan` rows US3 scenarios 2 and 3, which test the rule.
- Inputs that changed, each re-read in full with the whole of `plan.md`
  reviewed against it:
  1. `quickstart.md`. `§1` gains a paragraph on a repository that installed
     over the old record before its redo: delete
     `.wf-skills-backup/.specify/scripts/bash/` before the uninstall.
  2. `docs/architecture/deletion-follows-recorded-files.md`. The second
     Consequences item gains the same exit, to be taken before the redo.
- `spec.md`, `design.md`, `research.md`, `data-model.md`, the two accepted
  records, and the absent constitution match their rows.
- Lenses: requirements and traceability, architecture and boundaries,
  adversarial implementation and verification.
- Conditional lenses: security and reliability ran, since the change decides
  what `--prune` and `uninstall-skills` delete in a consuming repository, and
  the new exit tells a person to delete a folder by hand.
- Design records: none. `design.md §Software design decisions` lists no record.
  The level-2 record that `design.md §Boundaries and Ownership` names is listed
  above.
- Unresolved markers: no `[NEEDS CLARIFICATION`, TODO, or TBD in any planning
  artifact.
- Existing code inspected, to check the new exit: `wfctl/cli.py` lines
  4859 - 4872 (a planned path that exists and is not on record is copied to
  `.wf-skills-backup/<path>`, with `copytree` for a folder), lines 5296 - 5314
  (`uninstall-skills` moves a backup back only when it exists, and counts the
  path as removed otherwise), and lines 5057 - 5097 (`--prune` restores an
  orphan's backup the same way, and without `--prune` the orphan stays on record
  with its `backup` field).
- Reviewers: the four lenses above, run in sequence by one agent in a fresh
  context.

## Summary

BLOCKER: 0
MAJOR: 0
MINOR: 1

No BLOCKER findings identified in this review. The two findings the earlier
review left open are fixed:

1. PR-014 is fixed by the record's second Consequences item and
   `quickstart.md §1`, which both give the exit from the backup cycle. The code
   confirms it works: with the backups gone, the uninstall removes the scripts
   instead of restoring them, and the install that follows finds nothing to back
   up.
2. PR-015 is fixed by `plan.md §Technical Context`, whose Constraints line is
   now scoped the way `spec.md §FR-004` is.

One new MINOR finding stands. PR-016: the exit says the backups are all
wfctl's own copies, and in a repository that had its own scripts folder before
its first wfctl install, the same backup folder also holds that repository's
original scripts.

## Findings

### PR-001: The upgrade's one-time backup is not harmless

- Priority: MAJOR
- Category: Risk / Failure Mode
- Status: fixed
- Evidence:
  - `deletion-follows-recorded-files.md §Consequences`, second item
  - `spec.md §Edge Cases`, third item
- Finding: Still fixed as an accepted cost. The way out of the cycle, which
  was PR-014, is now in the same Consequences item.
- Why it matters: `/start-session` runs `install-skills --prune --yes`
  unattended.
- Suggested response: Fixed by the record and `spec.md §Edge Cases`.
- Corroborated by: adversarial implementation and verification, security and
  reliability

### PR-002: An older wfctl pruning over the per-file record deletes the scripts or crashes

- Priority: MAJOR
- Category: Risk / Failure Mode
- Status: fixed
- Evidence:
  - `deletion-follows-recorded-files.md §Consequences`, the item on an older
    wfctl
  - `spec.md §Edge Cases`, second item
- Finding: Still fixed.
- Why it matters: `/start-session` runs the prune unattended.
- Suggested response: Fixed by the record's Consequences and the spec's Edge
  Cases.
- Corroborated by: adversarial implementation and verification, security and
  reliability

### PR-003: The stale `none`-layer cleanup reads `.specify/` paths too

- Priority: MINOR
- Category: Assumption Challenge
- Status: fixed
- Evidence:
  - `research.md §1`, second paragraph, unchanged
- Finding: Still fixed.
- Why it matters: It was a planning-time claim the code did not support.
- Suggested response: Fixed by `research.md §1`.
- Corroborated by: architecture and boundaries

### PR-004: "Sits below" is not specified as a path-component test

- Priority: MINOR
- Category: Missing Information
- Status: fixed
- Evidence:
  - `plan.md §Summary`: neither part compares one recorded path with another
- Finding: Still fixed by the redesign.
- Why it matters: A string prefix would have put `brainstorming` below
  `brainstorm`.
- Suggested response: None needed.
- Corroborated by: adversarial implementation and verification

### PR-005: The acceptance scenarios are not mapped to tests

- Priority: MINOR
- Category: Verification Gap
- Status: fixed
- Evidence:
  - `plan.md §Test Plan`: twelve rows, unchanged
- Finding: Still fixed.
- Why it matters: Tasks are cut from the plan.
- Suggested response: Fixed by `plan.md §Test Plan`.
- Corroborated by: requirements and traceability, adversarial implementation
  and verification

### PR-006: Fresh installs change the `.gitignore` lines they write

- Priority: MINOR
- Category: Assumption Challenge
- Status: fixed
- Evidence:
  - `plan.md §Summary`, the `.gitignore` paragraph
- Finding: Still fixed.
- Why it matters: `.gitignore` is tracked in the consuming repository.
- Suggested response: Fixed by `plan.md §Summary`.
- Corroborated by: requirements and traceability

### PR-007: `quickstart.md` still expects the upgrade to back the scripts up

- Priority: MINOR
- Category: Requirement / Plan Mismatch
- Status: fixed
- Evidence:
  - `quickstart.md §1`, first two paragraphs, unchanged
- Finding: Still fixed. The new paragraph covers a different repository, one
  that installed over the old record before its redo, and does not bring the
  expectation back for this worktree.
- Why it matters: A backup would be PR-001's effect on the redo path.
- Suggested response: Fixed by `quickstart.md §1`.
- Corroborated by: requirements and traceability, adversarial implementation
  and verification

### PR-008: The backup branch has two cases, and the plan names one

- Priority: MINOR
- Category: Missing Information
- Status: fixed
- Evidence:
  - `plan.md §Summary` and `§Project Structure`: the copy loop's backup branch
    is not changed
- Finding: Still fixed by the redesign.
- Why it matters: Swapping the predicate alone would have raised `KeyError`.
- Suggested response: None needed.
- Corroborated by: adversarial implementation and verification

### PR-009: Counts and cross-references still describe the two-change plan

- Priority: MINOR
- Category: Requirement / Plan Mismatch
- Status: fixed
- Evidence:
  - `design.md`, unchanged
- Finding: Still fixed.
- Why it matters: A reader of `design.md` alone saw a smaller change than the
  one planned.
- Suggested response: Fixed by the rewritten `design.md`.
- Corroborated by: requirements and traceability

### PR-010: The Test Plan pins whole-component comparison for the helper only

- Priority: MINOR
- Category: Verification Gap
- Status: fixed
- Evidence:
  - `plan.md §Summary`: no orphan guard and no helper
- Finding: Still fixed by the redesign.
- Why it matters: A string-prefix guard would have hidden a dropped skill.
- Suggested response: None needed.
- Corroborated by: adversarial implementation and verification

### PR-011: The FR-007 test stops before the clean `doctor`

- Priority: MINOR
- Category: Verification Gap
- Status: fixed
- Evidence:
  - `plan.md §Test Plan`, row US2 scenario 1
- Finding: Still fixed.
- Why it matters: FR-007 and SC-002 both require a clean `doctor`.
- Suggested response: Fixed by `plan.md §Test Plan`.
- Corroborated by: requirements and traceability

### PR-012: A pruning install over the old record deletes a developer's own script

- Priority: MINOR
- Category: Risk / Failure Mode
- Status: fixed
- Evidence:
  - `deletion-follows-recorded-files.md §Consequences`, third item
  - `spec.md §Edge Cases`, fourth item, and `§FR-004` and `§SC-003`
  - `plan.md §Technical Context`, Constraints, now scoped the same way
- Finding: Still fixed as an accepted cost, and the plan now agrees with it.
- Why it matters: An untracked script deleted by the prune cannot be
  recovered.
- Suggested response: Fixed by the record, `spec.md`, and `plan.md`.
- Corroborated by: requirements and traceability, security and reliability

### PR-013: The redo removes and replaces the tracker files

- Priority: MINOR
- Category: Assumption Challenge
- Status: fixed
- Evidence:
  - `research.md §2`
  - `deletion-follows-recorded-files.md §Consequences`, fourth item
  - `spec.md §Edge Cases`, sixth item
- Finding: Still fixed as an accepted cost.
- Why it matters: A repository whose board columns differ from the bundle's
  config would lose that change.
- Suggested response: Fixed by `research.md §2` and the record.
- Corroborated by: adversarial implementation and verification, security and
  reliability

### PR-014: No artifact says how a repository caught in the backup cycle gets out

- Priority: MINOR
- Category: Missing Information
- Status: fixed
- Evidence:
  - `deletion-follows-recorded-files.md §Consequences`, second item: "A
    repository already caught in it deletes
    `.wf-skills-backup/.specify/scripts/bash/` before the redo, since the
    backups are wfctl's own earlier copies."
  - `quickstart.md §1`, third paragraph, which gives the same step before the
    uninstall
  - `wfctl/cli.py` lines 5307 - 5314: with the backup gone, the uninstall
    removes the script and moves nothing back
  - `wfctl/cli.py` lines 4859 - 4872: with the script gone, the install finds
    nothing at the path and records no backup
- Finding: Fixed. The exit is stated in the record and in the quickstart, and
  the code confirms it breaks the cycle. `spec.md §Edge Cases` does not carry
  it, which the earlier suggested response also named. The spec states the
  cost and accepts it, and a recovery step for an operator belongs in the
  record and the quickstart, so the finding no longer stands on that.
- Why it matters: A repository that misses the redo window would otherwise
  stay in the cycle through every later redo.
- Suggested response: Fixed by the record and `quickstart.md §1`. Its wording
  is PR-016.
- Corroborated by: adversarial implementation and verification, security and
  reliability

### PR-015: `plan.md` states the deletion rule without the condition the record now puts on it

- Priority: MINOR
- Category: Requirement / Plan Mismatch
- Status: fixed
- Evidence:
  - `plan.md §Technical Context`, Constraints: "In a repository that has been
    redone or freshly installed, a path wfctl cannot show it wrote is never
    deleted ... A repository not redone can still lose one at a pruning
    install, which the record accepts as a cost."
  - `spec.md §FR-004` and `§SC-003`, scoped the same way
  - `deletion-follows-recorded-files.md §Consequences`, third item
- Finding: Fixed. The constraint and the "no upgrade guard" line beside it can
  now both hold, since the rule no longer claims the case the guard would have
  covered.
- Why it matters: A task writer reading the constraint as absolute could have
  added the guard the record chose against.
- Suggested response: Fixed by `plan.md §Technical Context`.
- Corroborated by: requirements and traceability, architecture and boundaries

### PR-016: The exit assumes every backup under the scripts folder is wfctl's own

- Priority: MINOR
- Category: Assumption Challenge
- Status: open
- Evidence:
  - `deletion-follows-recorded-files.md §Consequences`, second item: "since
    the backups are wfctl's own earlier copies"
  - `quickstart.md §1`, third paragraph: "The backups are wfctl's own earlier
    copies, so nothing a developer wrote is lost."
  - `wfctl/cli.py` lines 4861 - 4868: a planned path that already exists and is
    not on record is backed up to `.wf-skills-backup/<path>`, and a folder is
    backed up whole with `copytree`
  - `wfctl/cli.py` lines 5095 - 5097: an install without `--prune` keeps the
    dropped folder entry on record, `backup` field included
- Finding: A repository that had its own `.specify/scripts/bash/` before its
  first wfctl install, which is any repository that ran Spec Kit first, got
  that folder backed up whole to `.wf-skills-backup/.specify/scripts/bash/`
  under the old folder entry. The install over the old record then copies
  wfctl's three scripts into the same folder, one file at a time. So the
  folder the exit says to delete holds two things: wfctl's earlier copies, and
  the repository's original scripts that wfctl never shipped, such as Spec
  Kit's `create-new-feature.sh`. Deleting it per the exit loses the second.
- Why it matters: Bounded. The files lost are Spec Kit's upstream scripts in
  the likely case, and they can be fetched again. The quickstart sentence
  promises that nothing a developer wrote is lost, and in this case that is
  not true.
- Suggested response: Scope the claim. Either say to delete only the three
  files wfctl ships (`check-prerequisites.sh`, `common.sh`, `setup-plan.sh`)
  under that folder, or say to check first whether the old folder entry in
  `.wf-skills-manifest.json` carries a `backup` field.
- Corroborated by: adversarial implementation and verification, security and
  reliability

## Requirement-to-plan trace

| Requirement / criterion | Plan location | Review note |
| --- | --- | --- |
| FR-001 | plan.md §Summary part 1; Test Plan US2 s1, SC-004 | covered |
| FR-002 | plan.md §Summary part 1; Test Plan US1 s1 - s3 | covered |
| FR-003 | plan.md §Summary, the redo paragraph; Test Plan US2 s1 | covered |
| FR-004 | plan.md §Technical Context, Constraints; Test Plan US3 s2, s3 | covered |
| FR-005 | research.md §3; Test Plan US3 s1, s4 | covered |
| FR-006 | Test Plan FR-006, tests/test_bundle.py | covered |
| FR-007 | Test Plan US2 s1; quickstart.md §1 | covered |
| SC-001 | Test Plan US1 s1, s2 | covered |
| SC-002 | Test Plan US2 s1 | covered |
| SC-003 | Test Plan US3 s2, s3 | covered |
| SC-004 | Test Plan SC-004 | covered |

## Assumptions challenged

- The record says to delete the backup folder "before the redo", and the
  quickstart says "before the uninstall". The redo begins with the uninstall,
  so the two say the same thing.
- The exit is a manual step with no test. It is an operator recovery for an
  accepted cost, not behavior the spec requires, so the Test Plan does not
  need a row for it.
- In a repository that ran Spec Kit first, the install over the old record has
  already overwritten that repository's original copies of the three scripts
  in the backup folder before the exit is ever taken. That loss is part of the
  accepted backup cost in the record's second Consequences item, not something
  the exit adds, so it is not filed.
- wfctl is installed in a handful of repositories, all Andre's, and each cost
  is accepted on that condition. A recorded decision, and not challenged here.

## Reviewer disagreement

- None identified.

## Strengths worth preserving

- The Constraints line now carries its condition and its exception in two
  sentences, and points to the record for the decision rather than restating
  it.
- The exit names the exact folder to delete, which makes PR-016 a scoping fix
  rather than a missing step.

## Source freshness

This review describes only the content identities listed under
`## Reviewed inputs`. When `spec.md`, `plan.md`, a binding design record, or a
material planning artifact changes, this report no longer describes the current
plan, and a new review is needed before it counts as current evidence.
