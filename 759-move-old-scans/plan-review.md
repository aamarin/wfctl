# Plan Review Report

Review state: completed
Review type: re-review

## Reviewed inputs

| Artifact | Content identity | Role |
| --- | --- | --- |
| plan.md | 030437ab5926f381f6fe0fd27b62d6154159a9b7 | technical strategy |
| spec.md | f2230d4af73d0540c29cf7c98b718a5eaa3f84dc | requirements |
| .specify/memory/constitution.md | absent | constitution |
| design.md | e6fb1d95b1f7883470001192b1269f88fc931458 | design-record index |
| docs/architecture/design/759-scan-names-its-folder.md | 88054a61096a687c2ae2ee817d4c3bbdb3a19f4b | design record |
| docs/architecture/scans-live-in-spec-folder.md | 6ba8ee6b8f6ea703939fad101702eb43415a9f99 | level-2 record this branch amends |
| AGENTS.md | 81e97f405ca993195c2450a3dffeed74c67dd18a | gates the plan substitutes for a constitution |
| research.md | ddfa9e4c434f08c3644e565005870e7a93f21a80 | planning evidence |
| data-model.md | 6425079f26ddb49c39ce35d09cf61e14ca4f6d34 | planning evidence |
| contracts/cli.md | 197de9496df5cef3456980a0c39906d4d43af140 | planning evidence |
| quickstart.md | 90a95f558891b2afd899352bd870288facb526ea | planning evidence |
| plan-review.plan.md | a8fb98e4f92b5253b9250bf58bf294d4a8c77bb0 | base of this re-review |

## Review scope

- Re-review: the earlier report and its plan copy exist, and the copy's
  identity equals the earlier report's `plan.md` row.
- Changed since the earlier report: `plan.md §Summary`, one paragraph. The
  sentence that stopped storing only on a failure "that would repeat for every
  folder" now says the first failed store stops storing for the rest of the run
  (FR-014, R8). Reviewed together with the sections that name that behavior:
  research R5, R6, R8, data-model `§Write` and `§Folder result`, contracts
  `§Output`, and the quickstart test map.
- Inputs whose identity changed, each re-read in full with the whole plan
  reviewed against it: `spec.md` (User Story 3 intro and scenario 1, new
  FR-014, Assumptions), `research.md` (R3, R5, R8), `data-model.md` (`§Write`),
  `contracts/cli.md` (the Output example and the paragraph after the cell
  table), `quickstart.md` (test map, pfms line), and
  `docs/architecture/design/759-scan-names-its-folder.md` (Consequences
  example, pfms line; an uncommitted edit in the worktree).
- Unchanged inputs, compared by identity: `design.md`,
  `scans-live-in-spec-folder.md`, `AGENTS.md`.
- Lenses: requirements and traceability, architecture and boundaries,
  adversarial implementation and verification.
- Conditional lenses: security and reliability applied, since the command
  deletes files in the code repository, pushes to a remote once per folder, and
  builds folder names from text read out of committed files.
- Constitution: none at `.specify/memory/constitution.md`. The plan's
  substitution of `AGENTS.md` and the accepted records is unchanged.
- Design records: 1 listed in design.md,
  `docs/architecture/design/759-scan-names-its-folder.md` (status `proposed`).
- Existing code inspected, each to check a claim the plan makes:
  `wfctl/_spec_store.py` (`report_lines`, `_outcome_lines`, the remedy text
  R8 rewrites).
- Data inspected read-only: pfms's `docs/architecture/scans/` on the local
  `dev` ref and on `origin/dev`, commit `18b0d71d` in pfms, and commit
  `e3463c30` in `pfms-specs`.
- Reviewers: the four lenses above, run in sequence by one agent, in a context
  that did not write the revision.

## Summary

BLOCKER: 0
MAJOR: 1
MINOR: 4

No BLOCKER findings identified in this review. PR-008 is fixed: the spec now
says the first failed store stops storing (FR-014, User Story 3 scenario 1),
and the plan, R8, the contract, and the test map all say the same. The same
change fixes PR-009. PR-011 and PR-013 are fixed.

The one MAJOR finding is new and isn't caused by the revision. pfms moved its
91 review scans by hand on 2026-11-13 (#1120), so SC-005, the spec's pfms
assumption, the quickstart's pfms run, and the record's pfms evidence describe
a move that has already happened. PR-012's count stays open because the files
still say 89 where pfms had 91. Two new MINOR findings come from the revision:
a rerun can still replace a scan the run never stored (PR-015), and the
contract's example contradicts its own cell table (PR-016). PR-010 is narrower
but still open for one remedy line.

## Findings

### PR-001: A rerun after a failed store reads #649's plan review as a conflict with its own output

- Priority: MAJOR
- Category: Requirement / Plan Mismatch
- Status: fixed
- Evidence:
  - `research.md §R5`: a plain or `--overwrite` write counts as already there
    when the destination starts with the scan's text, and an `--append` when
    the destination contains the block.
  - `quickstart.md §Test map`: the US3-5 row covers a destination holding one
    scan with a second appended to it.
- Finding: Unchanged since the earlier review.
- Why it matters: This was the recovery path for the one shared destination in
  wfctl.
- Suggested response: Fixed by `research.md §R5` and the US3-5 test row.
- Corroborated by: requirements and traceability, adversarial implementation

### PR-002: A `Detail` path that isn't a spec folder is reported by the record and created by the plan

- Priority: MAJOR
- Category: Architecture / Decision Conflict
- Status: fixed
- Evidence:
  - `docs/architecture/design/759-scan-names-its-folder.md §Consequences` and
    `research.md §R3` state one rule, the first `<issue>-<slug>` segment, and
    its one known limit.
- Finding: Unchanged since the earlier review.
- Why it matters: The two readings of the record would have given two
  commands.
- Suggested response: Fixed by the record's `§Consequences` and `research.md
  §R3`.
- Corroborated by: architecture and boundaries, adversarial implementation

### PR-003: The data model holds one write per step per folder, and deletes by folder

- Priority: MAJOR
- Category: Verification Gap
- Status: fixed
- Evidence:
  - `data-model.md §Folder result`, `research.md §R6`, `contracts/cli.md
    §Output`, and the SC-004 row of `quickstart.md §Test map` all key writes
    and deletion by scan.
- Finding: Unchanged since the earlier review.
- Why it matters: SC-004 is the safety promise.
- Suggested response: Fixed by the four sections above.
- Corroborated by: adversarial implementation, security and reliability

### PR-004: The record's count of scans with no folder disagrees with R3's rule, and backticks go unhandled

- Priority: MINOR
- Category: Assumption Challenge
- Status: fixed
- Evidence:
  - `docs/architecture/design/759-scan-names-its-folder.md §Verified`,
    `research.md §R3` and `§R4`, and the backtick row in the test map.
- Finding: Unchanged since the earlier review.
- Why it matters: The record is the stated evidence for the rule.
- Suggested response: Fixed.
- Corroborated by: single lens (adversarial implementation)

### PR-005: AGENTS.md and a `_paths.py` comment still say the old scans stay under the arch root

- Priority: MINOR
- Category: Architecture / Decision Conflict
- Status: fixed
- Evidence:
  - `plan.md §Constitution Check` and `§Project Structure` list both texts.
- Finding: Unchanged since the earlier review.
- Why it matters: `AGENTS.md` is what the next agent reads first.
- Suggested response: Fixed by `plan.md`.
- Corroborated by: requirements and traceability, architecture and boundaries

### PR-006: The Stored cell names an outcome text the store doesn't have, and drops the store's remedies

- Priority: MINOR
- Category: Risk / Failure Mode
- Status: fixed
- Evidence:
  - `research.md §R8`: a label for each of the eight failed outcomes, and the
    store's `report_lines` printed once under the table.
- Finding: Unchanged since the earlier review.
- Why it matters: The person reading a failed row needs the commands that
  clear it.
- Suggested response: Fixed by `research.md §R8` and `contracts/cli.md`.
- Corroborated by: adversarial implementation, security and reliability

### PR-007: The pushes are not recorded as outward actions

- Priority: MINOR
- Category: Missing Information
- Status: fixed
- Evidence:
  - `research.md §R9` and `plan.md §Project Structure`.
- Finding: Unchanged since the earlier review.
- Why it matters: The event log is the trace a restarted session reads.
- Suggested response: Fixed by `research.md §R9`.
- Corroborated by: single lens (architecture and boundaries)

### PR-008: R8 stops storing after an unreachable remote, and the spec says the other folders' scans move

- Priority: BLOCKER
- Category: Requirement / Plan Mismatch
- Status: fixed
- Evidence:
  - `spec.md §User Story 3`: the intro now says a failed store stops storing
    for the rest of the run, and scenario 1 has the first of three folders
    move, the second show the store's reason, and the third show it wasn't
    tried.
  - `spec.md §FR-014`: after the first folder whose store fails, no other
    folder is stored in that run, the unstored folders' scans stay, and a
    rerun stores them.
  - `research.md §R8`: stops after the first failed outcome, whichever of the
    eight, and cites FR-014.
  - `plan.md §Summary`: the same rule, citing FR-014 and R8.
  - `contracts/cli.md §Output`: `– not tried` cell, and at most one failure
    per run.
  - `quickstart.md §Test map`: one US3-1 row for the stop, and the earlier
    second row filed under US3-5 is gone.
- Finding: The spec, the plan, and every planning artifact now give one
  answer.
- Why it matters: Two durable sources gave opposite answers for the failure
  path User Story 3 exists for.
- Suggested response: Fixed by FR-014, User Story 3 scenario 1, R8, and the
  test map.
- Corroborated by: requirements and traceability, adversarial implementation

### PR-009: R8 treats `conflict` and `merge_refused` as specific to one folder, and the store says they stop every store

- Priority: MINOR
- Category: Assumption Challenge
- Status: fixed
- Evidence:
  - `research.md §R8`: every failed outcome now stops storing, and the
    rationale cites the store's own conflict text. Its Alternatives paragraph
    names `conflict` and `merge_refused` as the reason the outcomes can't be
    split.
  - `contracts/cli.md §Output`: a run has at most one failure, so
    "distinct failure" no longer needs a definition.
- Finding: The stop rule removes the repeated rows.
- Why it matters: One real conflict printed 44 times.
- Suggested response: Fixed by `research.md §R8`.
- Corroborated by: adversarial implementation, security and reliability

### PR-010: The reused remedy lines tell the user to run `wfctl store specs`

- Priority: MINOR
- Category: Risk / Failure Mode
- Status: open
- Evidence:
  - `research.md §R8` and `contracts/cli.md §Output`: each `report_lines`
    line is printed with `wfctl store scans` in place of `wfctl store specs`.
  - `wfctl/_spec_store.py`, `_outcome_lines`, the `merge_blocked_staged`
    branch: "run `wfctl store specs` from the branch that owns that folder, or
    unstage the files, then run `wfctl store specs` again".
- Finding: The substitution fixes every remedy line but one. After it, the
  `merge_blocked_staged` line reads "run `wfctl store scans` from the branch
  that owns that folder". The staged files belong to another branch's spec
  folder, and what clears them is `wfctl store specs` on that branch. Running
  `store scans` from that branch would start the whole move again from that
  branch's own arch root.
- Why it matters: The user following the printed remedy for that one outcome
  runs the wrong command on the wrong branch. Nothing is lost, since a failed
  store keeps its scans, but the remedy doesn't clear the block.
- Suggested response: Keep `wfctl store specs` in the first clause of that one
  line, or say in R8 which lines the substitution applies to.
- Corroborated by: adversarial implementation

### PR-011: `--overwrite` on a destination written earlier in the same run deletes the earlier scan

- Priority: MINOR
- Category: Risk / Failure Mode
- Status: fixed
- Evidence:
  - `research.md §R5`: `--overwrite` never replaces a destination written
    earlier in the same run, and holds it as a conflict.
  - `data-model.md §Write`: the same rule, and the report says to rerun once
    the earlier scan is stored.
  - `quickstart.md §Test map`: an Edge row for the held overwrite.
- Finding: The first-run path the earlier review named is closed. A rerun path
  remains, which is PR-015.
- Why it matters: SC-004.
- Suggested response: Fixed by R5, the data model, and the Edge test row.
- Corroborated by: adversarial implementation, security and reliability

### PR-012: pfms has 91 review scans, not 89

- Priority: MINOR
- Category: Assumption Challenge
- Status: open
- Evidence:
  - `spec.md §Assumptions`, `docs/architecture/design/759-scan-names-its-folder.md
    §Verified`, and `quickstart.md §Run it in pfms`: "pfms's `dev` branch has
    89 review scans".
  - `git -C /Users/andremarin/Development/pfms ls-tree --name-only dev
    docs/architecture/scans/`: 91 entries, each named
    `<n>-(clarify|plan-review|analyze).md`, 31 issues in all.
  - pfms commit `18b0d71d` (#1120): "The 91 clarify, plan-review, and analyze
    scans under docs/architecture/scans", deleting 91 files. `pfms-specs`
    commit `e3463c30` adds the same 91.
- Finding: The revision named the branch, but the count is still off by two.
  This review couldn't reproduce 89 from any ref.
- Why it matters: The record's Verified section is the stated evidence, and a
  reader checking it finds a different number. If PR-014 removes the pfms text,
  this finding goes with it.
- Suggested response: Write 91, or drop the count along with PR-014's text.
- Corroborated by: single lens (requirements and traceability)

### PR-013: The dated-folder example points at a case the first-match rule handles

- Priority: MINOR
- Category: Assumption Challenge
- Status: fixed
- Evidence:
  - `research.md §R3 "Why the first match is enough"` and
    `docs/architecture/design/759-scan-names-its-folder.md §Consequences`: both
    now give a matching segment above the spec folder,
    `…/wt/656-foo/specs/649-bar/plan.md`, as the case the rule gets wrong.
- Finding: The example now names the case the rule actually misses.
- Why it matters: The record states the rule's one known limit.
- Suggested response: Fixed by R3 and the record.
- Corroborated by: single lens (architecture and boundaries)

### PR-014: pfms has already moved its review scans, so SC-005 and the pfms text describe a run that won't happen

- Priority: MAJOR
- Category: Assumption Challenge
- Status: open
- Evidence:
  - `spec.md` intro ("pfms has its own set"), `§SC-005` ("The same move in pfms
    needs one command after the release"), and `§Assumptions` ("The command is
    removed in a later release, once pfms has run it").
  - `quickstart.md §Run it in pfms`: "After the release that ships the
    command, the user runs `wfctl store scans` in pfms."
  - `docs/architecture/design/759-scan-names-its-folder.md §Verified`: the
    pfms bullet.
  - pfms `origin/dev`: commit `18b0d71d`, 2026-11-13, "docs: move review scans
    to the spec folders (#1120)", deletes all 91. `git ls-tree origin/dev
    docs/architecture/scans/` lists nothing.
  - `pfms-specs`: commit `e3463c30`, 2026-11-13, "docs: add review scans moved
    from the code repo (#1120)", adds the 91 under `<folder>/scans/<step>.md`.
    The subject isn't a `specs(<issue>):` store commit, so the move was made
    by hand, not by this command.
- Finding: Once a person pulls pfms's `dev`, `wfctl store scans` there prints
  `✓ no review scans in docs/architecture/scans/` and exits 0. SC-005 can no
  longer be observed as written. The removal trigger in the Assumptions never
  fires. And pfms was the one reason for the command to work in any
  repository, with the tracker key pattern and the layout check.
- Why it matters: Only wfctl's 114 scans are left to move. The plan still
  works for those, so tasks can be written. But a task built from the
  quickstart's pfms section verifies nothing, and whether the command still
  needs to be general, and when it is removed, is now a question nobody has
  answered.
- Suggested response: A person decides whether SC-005 is dropped or restated,
  for example "no pfms-specific code in wfctl", and when the command is
  removed. Then remove or rewrite the pfms text in `spec.md`, the quickstart,
  and the record's Verified section.
- Corroborated by: single lens (requirements and traceability)

### PR-015: A rerun after a stop can still replace a scan whose text was never stored

- Priority: MINOR
- Category: Risk / Failure Mode
- Status: open
- Evidence:
  - `research.md §R5` and `data-model.md §Write`: `--overwrite` is held as a
    conflict when "an earlier scan wrote" the destination "in the same run".
    `already_there` is a separate write state, not a write.
  - `research.md §R5`: on a rerun, a destination that starts with a scan's
    text reads as `already_there`.
  - `spec.md §FR-014` and `research.md §R8`: an earlier folder's failure
    leaves later folders `– not tried`, with their files written and nothing
    committed.
  - `research.md §R6`: `already_there` plus a stored folder deletes the scan.
  - `spec.md §SC-004`.
- Finding: Take a first run with `--overwrite 656-plan-review.md`. #649's plan
  review is written, #656's is held, and an earlier folder's failure leaves
  `649-design-checks-by-context` not tried. On the rerun with the same flag,
  #649's write is `already_there`. If the guard keys on a write in this run, it
  doesn't fire. #656's text replaces #649's, the store succeeds, and #649's scan
  is deleted, though its text was never committed to the spec store. The same
  holds after a `locked` or `merge_in_progress` failure on that folder, which
  commit nothing either.
- Why it matters: It breaks SC-004 on a path FR-014 makes more likely, since
  any earlier failure leaves the folder untried. The text is recoverable from
  the code repository's history, which is why this is MINOR.
- Suggested response: Hold `--overwrite` whenever an earlier scan in this run
  targets the same destination and is ready to store, whatever its write
  state. Add the rerun case to the Edge test row.
- Corroborated by: adversarial implementation, security and reliability

### PR-016: The contract's example shows `✓` for scans whose folder wasn't stored

- Priority: MINOR
- Category: Verification Gap
- Status: open
- Evidence:
  - `contracts/cli.md §Output`, the example table: `650-bob-pr-review-guard
    (new)` shows `✓` under plan review and analyze beside `✗ not pushed`, and
    `711-…` shows `✓` under analyze beside `– not tried`.
  - Same file, the cell table: `✓` means "written … and stored", and `✗` means
    "ready, but the folder's store failed". No value covers a ready scan in a
    folder that wasn't tried.
- Finding: The example contradicts the cell table on both failed rows, and
  the table has no mark for the new `– not tried` case.
- Why it matters: US1-6 and US3-1 assert on this output with `NO_COLOR`. An
  implementer who copies the example and one who follows the table write
  different tests.
- Suggested response: Show `✗` in the 650 row, and give a ready scan in an
  untried folder its own mark or say it uses `✗`.
- Corroborated by: single lens (adversarial implementation)

## Requirement-to-plan trace

| Requirement / criterion | Plan location | Review note |
| --- | --- | --- |
| FR-001 | plan.md §Project Structure (`cli.py` on `store_app`); contracts/cli.md | covered |
| FR-002 | data-model.md §Review scan | covered |
| FR-003 | research.md §R3 | covered |
| FR-004 | research.md §R4 | covered |
| FR-005 | research.md §R3; data-model.md §Folder result `created` | covered |
| FR-006 | plan.md §Summary; `spec_scan` reused | covered |
| FR-007 | research.md §R5, §R7; data-model.md §Write; contracts/cli.md §Flags | covered; PR-015 |
| FR-008 | research.md §R1 | covered |
| FR-009 | research.md §R6; data-model.md §Folder result | covered; PR-015 |
| FR-010 | research.md §R6 (layout read first) | covered |
| FR-011 | contracts/cli.md §Output; research.md §R8 | covered; PR-010, PR-016 |
| FR-012 | data-model.md §Run result; contracts/cli.md §Exit codes | covered |
| FR-013 | plan.md §Constitution Check, §Project Structure | covered |
| FR-014 | plan.md §Summary; research.md §R8; contracts/cli.md §Output; quickstart.md US3-1 | covered |
| US1 scenarios 1–6 | quickstart.md §Test map | covered; PR-016 on US1-6's output |
| US2 scenarios 1–4 | quickstart.md §Test map | covered |
| US3 scenario 1 | research.md §R8; quickstart.md §Test map | covered; PR-016 on the row marks |
| US3 scenarios 2–6 | quickstart.md §Test map | covered |
| SC-001, SC-002 | quickstart.md §Run it in wfctl | covered |
| SC-003 | quickstart.md §Run it in wfctl | covered |
| SC-004 | research.md §R5, §R6; quickstart.md SC-004 and Edge rows | covered; PR-015 |
| SC-005 | quickstart.md §Run it in pfms | PR-014; PR-012 on the count |

## Assumptions challenged

- pfms still has review scans to move. Not true on `origin/dev` since
  2026-11-13 (PR-014).
- pfms had 89 review scans. Its `dev` ref and the #1120 commit both give 91
  (PR-012).
- Replacing `wfctl store specs` with `wfctl store scans` in every remedy line
  gives a correct remedy. True for every line except `merge_blocked_staged`'s
  first clause (PR-010).
- A rerun can't replace a scan the run never stored. True on the first run,
  and not on a rerun where the earlier scan reads `already_there` (PR-015).
- An unreachable remote, a held lock, an unfinished merge, and a conflict each
  fail every later store. Verified against `_outcome_lines`' own text, and
  this is what FR-014 now rests on.

## Reviewer disagreement

- PR-014's priority. It could be read as a BLOCKER under the rubric's test
  that verification of a critical requirement is impossible as written, since
  SC-005 can no longer be observed. It's graded MAJOR because SC-005 is about
  another repository, wfctl's own move is fully specified and verifiable, and
  the decision it needs, whether to drop or restate SC-005, doesn't change any
  task for wfctl's 114 scans.

## Strengths worth preserving

- FR-014 resolves PR-008 and PR-009 with one rule, and R8 explains why a
  per-outcome split wouldn't hold.
- The `– not tried` state gives the stop a visible row, and the rerun recovers
  those folders through R5 with no new mechanism.
- The held `--overwrite` closes the first-run path to losing #649's text.

## Source freshness

This review describes only the content identities listed under
`## Reviewed inputs`. When `spec.md`, `plan.md`, a binding design record, or a
material planning artifact changes, this report no longer describes the current
plan, and a new review is needed before it counts as current evidence.
