# Plan Review Report

Review state: completed
Review type: re-review

## Reviewed inputs

| Artifact | Content identity | Role |
| --- | --- | --- |
| plan.md | 6a0e2d4abba00699396f571a735b7bd758b30f28 | technical strategy |
| spec.md | 839880bd6f5205a0073a1158793a7df7dc09c8e7 | requirements |
| .specify/memory/constitution.md | absent | constitution |
| design.md | e82e45ce32266ada7c33003be09900fdbd625387 | design-record index |
| docs/architecture/design/622-review-records-in-state-dir.md | 4027336f312d54eaf9b30470a60a701fe87f5e8c | design record |
| docs/architecture/design/622-review-groups-list.md | 44048f18080066767fa5f064e3b7e75c9738fa91 | design record |
| docs/architecture/design/622-blocked-reviewer-relays-report.md | 737f15b5d4a3019e229cdc9bb30a6eb544450116 | design record |
| docs/architecture/design/622-review-check-in-worktree-guard.md | c08a744939fabe46c8971bf8727e65c9306d61ad | design record |
| research.md | ba551572fd9977ddf274c92bc5ea034c8db29357 | planning evidence |
| data-model.md | 4a2b1597bd61bf6d47295f00336d5a0fb2716f26 | planning evidence |
| contracts/cli.md | 9c633dacc9f4c7b8e578315d36323d05f1701b77 | planning evidence |
| contracts/config.md | a6cb93ef21e11f2778edb6e78b51027b2dbd0576 | planning evidence |
| quickstart.md | ff7e876c9ed0bd86381649db4d6a0ffec639348c | planning evidence |
| docs/architecture/review-covers-unreviewed-commits.md | 69bf5f4cdcae15c3495bf402deb23c104fa3bd3c | accepted architecture record |
| docs/architecture/vendor-upstream-skills.md | 299f4f8cb5e2b2e0d84661741696f97ca6c0b3f0 | accepted architecture record |
| docs/architecture/a-rule-is-expressed-as-a-check.md | 81e9a7d67301935f73a6e3b97c9b06284310879f | accepted architecture record |
| docs/architecture/wfctl-records-outward-actions-and-never-gates-them.md | 8ff8575e2c4b1e5c7ff342092144866d12c98380 | proposed architecture record |
| AGENTS.md | 4dfb90941c8fb593b64d5bdc5d2ff631a4bcc70a | repository guidance |
| wfctl/_hook.py | 77060f8723515559fe708b0e9f10bff2ee9ae99c | existing code |
| wfctl/_entry.py | a26598d8eeb62a3847fff5fb70235410ae4ccde9 | existing code |
| wfctl/_io.py | 50990ecb0d1bfb76788e4592465c21bffb3306ed | existing code |
| wfctl/_paths.py | 73d865219982aa4da4aade36fe472032fe550da7 | existing code |
| wfctl/_restart.py | 97eface9df371260af973dca55a215a2251304de | existing code |
| wfctl/_guard.py | 2b6f0d39f1c0af749d32b0fbd409448fdf5e06f3 | existing code |
| tests/test_guard_entry.py | 04b8a817989f7d5af46815ae6cf36a29b916c5d1 | existing code |
| tests/test_skill_attribution.py | 6665bbf9db2490b969e0d389d0e45561accadb6a | existing code |
| wfctl/agents/skills/NOTICES.md | 4aeb6145750062f3fbc661974f460a2f885f8ab2 | existing code |
| wfctl/agents/skills/fanning-out-code-review/SKILL.md | dcf63a66bd69730ab52866916c0bd83299a395c2 | existing code |
| wfctl/agents/skills/code-review/SKILL.md | f1b669063ac31d22c94cfaebb32c1131f147e304 | existing code |
| wfctl/agents/skills/idea-refine/SKILL.md | ca60506bac2baa0dd8bca0e3ef9b42de20a524d4 | existing code |
| wfctl/agents/skills/opening-a-change/SKILL.md | ec2437e0ab6ff1d188cadd9b677db0c715144ee5 | existing code |
| wfctl/agents/skills/receiving-code-review/SKILL.md | d9dc70c6c98e60b96b9fb591e2079920bd2eec99 | existing code |
| wfctl/agents/skills/architecture-decisions/SKILL.md | bdcc407f2bbe287b6d31099ab2bcf483129e405f | repository guidance |
| .github/scripts/release.py | 5573934e6746db3dd261a7c143d91730b22decf1 | existing code |
| plan-review.plan.md | 41b127397541b1228cc131fe0fc86f80bfc795bf | base of this re-review |

## Review scope

- Re-review: the earlier report exists, the plan copy exists, and the copy's
  identity equals the earlier report's `plan.md` row.
- Changed since the earlier report: two passages of `plan.md`, which make up
  the whole plan diff.
  1. `§Summary` now says the check refuses the commands its rules can't read
     for sure, and that every hole still open on 2026-10-24, and any found
     later, is a known limit listed in the spec's Edge Cases that #627 closes.
     It was reviewed together with `research.md §R6`, `spec.md §Edge Cases`
     and `§Clarifications`, and the guard record's paragraph after Decision
     item 8 and its Log.
  2. The `test_review_gate.py` list in `§Project Structure` adds the two
     override refusals and says how the other gate tests handle
     `WFCTL_BRANCH`. It was reviewed together with `research.md §R4`
     (Timeouts and errors) item 2, `§R5`, and the two override rows in
     `contracts/cli.md §Guard`.
- Inputs that changed and were re-read in full, with the whole of `plan.md`
  reviewed against each: `spec.md`, `research.md`, and
  `docs/architecture/design/622-review-check-in-worktree-guard.md`. Every
  other earlier row still matches its file.
- The dispatching session named the edits since the seventh review, and each
  was checked across the files it touches:
  1. PR-060: `plan.md §Summary`, `research.md §R6` item 1, and the guard
     record's paragraph after Decision item 8 now date the cutoff.
  2. PR-061: `research.md §R4` (Another branch) numbering.
  3. PR-062: the `test_review_gate.py` list in `plan.md §Project Structure`.
  4. PR-063: `spec.md §Edge Cases` known limit 2.10 and `research.md §R6`
     (Known limits) item 11.
  5. PR-043: `spec.md §Edge Cases` (Some ordinary commands are refused) items
     4 to 6.
- Scoring follows Andre's decision of 2026-10-24, recorded in `spec.md
  §Clarifications` (Session 2026-10-24), `§Edge Cases`, R6, `plan.md
  §Summary`, and the guard record. The review check stops adding rules. A
  disguised command already listed as a known limit isn't a finding, and a
  new one is at most MINOR, with "record it as a known limit" as its
  response. This review found no new disguised command.
- Lenses: requirements and traceability, architecture and boundaries, and
  adversarial implementation and verification, with verification and risk
  folded into the adversarial lens and dependency and scope into the
  architecture lens.
- Conditional lenses: security and reliability applied. The feature adds an
  enforcement gate to the worktree guard, and this revision changes which
  holes the artifacts say that gate closes.
- Design records: 4 listed in `design.md`. Only the guard record changed, in
  the one sentence that dates the cutoff. Its Log was read against that
  sentence (PR-064).
- No constitution exists at `.specify/memory/constitution.md`.
- No `[NEEDS CLARIFICATION` marker, TODO, or placeholder stands in `spec.md`
  or the planning artifacts.
- Existing code inspected: `tests/conftest.py`, which sets `WFCTL_BRANCH` in
  two fixtures, at lines 254 and 446.
- The finding history in `docs/architecture/scans/622-plan-review.md` and the
  guard record's commit dates were read to date when PR-049 to PR-052 were
  fixed (PR-064).
- Reviewers: the lenses above, run in sequence by one agent that wrote none
  of the edits under review.

## Summary

BLOCKER: 0
MAJOR: 0
MINOR: 1

No BLOCKER findings identified in this review, and no MAJOR finding is open.
Five earlier findings are fixed:

1. PR-060: the plan's Summary, R6 item 1, and the guard record date the
   cutoff instead of counting reviews, and the Summary names the known limits
   and #627.
2. PR-061: R4 (Another branch) now numbers its items 1 to 5.
3. PR-062: the plan's test list carries both override refusals, and says
   every other gate test clears `WFCTL_BRANCH` or sets it to the `cwd`'s
   branch.
4. PR-063: known limit 2.10 and R6 limit 11 now name a git alias and a shell
   function or alias.
5. PR-043: each of the six wrong refusals now has its own rewording, and
   each rewording avoids the refusal as R6 describes the patterns.

One MINOR finding is new. PR-064: the date doesn't mark the cutoff by
itself, because four holes were closed by new rules on 2026-10-24, before
Andre's decision that day.

## Findings

### PR-001: The plan keeps vendored files byte-identical, and the accepted record puts the attribution line inside them

- Priority: BLOCKER
- Category: Architecture / Decision Conflict
- Status: fixed
- Evidence:
  - `plan.md §Technical Context` (Constraints) and `§Constitution Check`: the
    `security-and-hardening` skill ends with the attribution line and is
    otherwise unedited.
  - `spec.md §FR-024` and `research.md §R10` items 3 and 4: the
    `/security-review` file carries no line, and its credit is a row in the
    record's file table plus a `NOTICES.md` entry naming it by path.
- Finding: The plan no longer claims both vendored files stay byte-identical.
- Why it matters: The contradiction between the plan's constraint and the
  record is gone.
- Suggested response: Fixed by `plan.md §Technical Context`, `§Constitution
  Check`, and `research.md §R10`.
- Corroborated by: deterministic checks, architecture and boundaries

### PR-002: The review check doesn't say which way it fails after a match, and its `gh` call has no timeout

- Priority: MAJOR
- Category: Risk / Failure Mode
- Status: fixed
- Evidence: `spec.md §FR-015`, `research.md §R4` (Timeouts and errors), and
  `contracts/cli.md §Guard` rows for a lookup that times out and any other
  error after a match. The guard record's `§Decision` says the same.
- Finding: The failure direction and the timeout are both stated.
- Why it matters: A bug in the check refuses rather than passes.
- Suggested response: Fixed by `research.md §R4` and FR-015.
- Corroborated by: security and reliability, adversarial implementation

### PR-003: The sign-off refusal is a text match an agent can step around

- Priority: MAJOR
- Category: Requirement / Plan Mismatch
- Status: fixed
- Evidence: `research.md §R6` pattern 5, `§R9` items 1 and 2, and `spec.md
  §Edge Cases`, which records a direct write of `sign-off.json` as a limit.
- Finding: The command enforces inside itself as well as in the guard, and the
  direct-write limit is recorded.
- Why it matters: The sign-off doesn't depend on the text match alone.
- Suggested response: Fixed by R6, R9, and FR-013.
- Corroborated by: security and reliability

### PR-004: Other `gh` spellings open or merge a pull request without matching

- Priority: MAJOR
- Category: Requirement / Plan Mismatch
- Status: fixed
- Evidence: `research.md §R6` patterns 1 - 4 and 6 - 7, `§R4` (`--auto`
  refuses), and `spec.md §FR-012` and `§Edge Cases`, which now record two
  limits.
- Finding: Every spelling the earlier report listed matches or is a recorded
  limit.
- Why it matters: SC-001 counts only what FR-012 names.
- Suggested response: Fixed by R4, R6, FR-012, and SC-001.
- Corroborated by: security and reliability

### PR-005: The plan doesn't say how the check reads the pull request or branch out of the command

- Priority: MAJOR
- Category: Missing Information
- Status: fixed
- Evidence: `research.md §R4` (How the check reads the arguments) and item 1
  on `--head`.
- Finding: The extraction rule, `--head`, and `-R` are defined. PR-034 covers
  a new contradiction about the `-R` value.
- Why it matters: The fallback that failed open is gone.
- Suggested response: Fixed by `research.md §R4`.
- Corroborated by: adversarial implementation, security and reliability

### PR-006: A run with no expected reviewer completes with no review

- Priority: MAJOR
- Category: Risk / Failure Mode
- Status: fixed
- Evidence: `spec.md §FR-023`, `research.md §R7` item 1, and `data-model.md
  §State a run moves through`.
- Finding: A run can't complete with zero reports.
- Why it matters: A group doesn't turn into a pass when its models are
  missing.
- Suggested response: Fixed by FR-023, R7, and the data model.
- Corroborated by: security and reliability

### PR-007: The agent controls the `PATH` that decides whether a model is available

- Priority: MINOR
- Category: Assumption Challenge
- Status: fixed
- Evidence: `plan.md §Constitution Check` ownership 2 says the lookup is
  visible rather than enforced.
- Finding: Both halves of the earlier finding are stated.
- Why it matters: The ownership claim doesn't read as enforced.
- Suggested response: Fixed by ownership 2 and R7.
- Corroborated by: adversarial implementation

### PR-008: The three-round cap ships as prose, and the gate is marked passed

- Priority: MINOR
- Category: Architecture / Decision Conflict
- Status: fixed
- Evidence: `plan.md §Constitution Check` leaves the
  `a-rule-is-expressed-as-a-check` gate unchecked and now says that nothing in
  wfctl stops an agent that ignores the instruction. `§Complexity Tracking`
  carries the deviation, and #626 is open and carries the cap.
- Finding: The gap is recorded as a deviation, and its cost is stated. PR-040
  covers a spec sentence that still claims more.
- Why it matters: A reader of the gate list doesn't see the rule satisfied.
- Suggested response: Fixed by the gate and the Complexity Tracking row.
- Corroborated by: architecture and boundaries

### PR-009: `AGENTS.md` still says wfctl doesn't gate outward actions

- Priority: MINOR
- Category: Requirement / Plan Mismatch
- Status: fixed
- Evidence: `plan.md §Constitution Check` (`knowledge-placement`) and
  `§Project Structure` plan an edit to `AGENTS.md §Safety`.
- Finding: The edit is planned.
- Why it matters: An agent meeting the refusal is told to run the groups.
- Suggested response: Fixed by the `knowledge-placement` gate.
- Corroborated by: architecture and boundaries

### PR-010: The trunk the range excludes is underspecified

- Priority: MINOR
- Category: Missing Information
- Status: fixed
- Evidence: `research.md §R3` items 1 and 2, the `no trunk branch found` rows
  in `contracts/cli.md`, and `spec.md §FR-006`.
- Finding: The refs, the None case, and the default agree.
- Why it matters: The merge base is always defined, or the check refuses.
- Suggested response: Fixed by R3 and FR-006.
- Corroborated by: requirements and traceability

### PR-011: The config contract doesn't constrain a group's name

- Priority: MINOR
- Category: Missing Information
- Status: fixed
- Evidence: `spec.md §FR-020`, `data-model.md §Review group`, and
  `contracts/config.md §findings`.
- Finding: A name is lowercase, safe as a directory name, and starts with a
  letter.
- Why it matters: The id-to-group lookup has one answer.
- Suggested response: Fixed by FR-020 and the config contract.
- Corroborated by: architecture and boundaries

### PR-012: The plan's test list leaves out the `store specs` test

- Priority: MINOR
- Category: Verification Gap
- Status: fixed
- Evidence: `plan.md §Project Structure` lists `test_review_store.py` for
  SC-004.
- Finding: SC-004 has a test.
- Why it matters: A skill rewrite that still writes to the spec directory
  fails a test.
- Suggested response: Fixed by the test list.
- Corroborated by: deterministic checks

### PR-013: FR-003 and FR-004 have no place in the plan

- Priority: MINOR
- Category: Requirement / Plan Mismatch
- Status: fixed
- Evidence: `plan.md §What the skill rewrites say` traces FR-001, FR-003,
  FR-004, FR-015, FR-012a, FR-026, R2, R8, R10, and R11 to the three skills.
- Finding: Each skill rewrite lists what it says.
- Why it matters: The tasks step doesn't have to rebuild these from `spec.md`.
- Suggested response: Fixed by the section.
- Corroborated by: requirements and traceability

### PR-014: The vendored hardening skill points at a checklist outside its folder

- Priority: MINOR
- Category: Dependency / Feasibility
- Status: fixed
- Evidence: `research.md §R10` item 2.
- Finding: Every security reviewer can reach the checklist.
- Why it matters: The skill's checklist step finds its file.
- Suggested response: Fixed by R10 item 2.
- Corroborated by: architecture and boundaries

### PR-015: A pushed head behind the last reviewed commit reads as wholly unreviewed

- Priority: MINOR
- Category: Risk / Failure Mode
- Status: fixed
- Evidence: `research.md §R3` item 3 and `data-model.md §Derived on every
  read`.
- Finding: The case is handled, and the reason it is safe is stated.
- Why it matters: The refusal list doesn't name reviewed commits.
- Suggested response: Fixed by R3 item 3.
- Corroborated by: adversarial implementation

### PR-016: The new attribution table changes an accepted decision without saying how, and the existing test fails on its row

- Priority: MAJOR
- Category: Architecture / Decision Conflict
- Status: fixed
- Evidence: `plan.md §Constitution Check` (the `layer-model` and
  `vendor-upstream-skills` gate) and `research.md §R10` items 3 to 6.
- Finding: The decision text that becomes false, the Log line, the choice of
  amendment, the reason, and how the test tells the row apart are all stated.
- Why it matters: The binding record and its enforcement change together.
- Suggested response: Fixed by `plan.md §Constitution Check` and R10.
- Corroborated by: deterministic checks, architecture and boundaries

### PR-017: The check judges one matched command at hook time, and the rest of the command text is unaccounted for

- Priority: MAJOR
- Category: Risk / Failure Mode
- Status: fixed
- Evidence: `spec.md §FR-012b`, `research.md §R4` (A matched command that
  follows another command), and the chained-form rows in `contracts/cli.md
  §Guard`.
- Finding: Every chained case the earlier finding listed refuses. PR-037
  covers wrappers that change the directory with no separator.
- Why it matters: The chain of commit, push, and `gh pr create` doesn't open a
  PR with an unjudged commit.
- Suggested response: Fixed by FR-012b and R4.
- Corroborated by: adversarial implementation, security and reliability

### PR-018: A relayed report travels in the command line, where the guard's text match refuses it

- Priority: MAJOR
- Category: Risk / Failure Mode
- Status: fixed
- Evidence: `spec.md §FR-017`, `research.md §R8` item 1, and `contracts/cli.md
  §relay`.
- Finding: The report doesn't reach the guard's text.
- Why it matters: A security report that quotes refused commands can be
  relayed.
- Suggested response: Fixed by FR-017 and R8.
- Corroborated by: adversarial implementation

### PR-019: `gh pr new` opens a pull request and matches no pattern

- Priority: MAJOR
- Category: Requirement / Plan Mismatch
- Status: fixed
- Evidence: `spec.md §FR-012` and `research.md §R6` patterns 1 and 4.
- Finding: Both spellings match. The alias limit this finding once pointed
  at is gone, and PR-056 covers the aliases that still pass.
- Why it matters: The one-word bypass is gone.
- Suggested response: Fixed by FR-012 and R6.
- Corroborated by: security and reliability

### PR-020: The argument rule's flag tables miss spellings `gh` accepts

- Priority: MINOR
- Category: Missing Information
- Status: fixed
- Evidence: `research.md §R4` (How the check reads the arguments) items 1, 2,
  4, and 5.
- Finding: Each spelling the earlier finding named is defined.
- Why it matters: Common spellings don't refuse as unknown flags.
- Suggested response: Fixed by R4.
- Corroborated by: adversarial implementation

### PR-021: Other ways to name another repository aren't compared the way `-R` is

- Priority: MINOR
- Category: Risk / Failure Mode
- Status: fixed
- Evidence: `research.md §R4` (Another repository) items 2 and 3 compare a
  `repos/<owner>/<repo>/` path and an `owner:` prefix. A `GH_REPO=` prefix now
  refuses with every other environment prefix, per `spec.md §FR-012b` and
  `contracts/cli.md §Guard`.
- Finding: Both forms the earlier finding named refuse. PR-036 covers gh's
  `:owner/:repo` placeholder spelling, which the comparison doesn't name.
- Why it matters: The check doesn't judge this repository's PR for a command
  aimed at another one.
- Suggested response: Fixed by FR-012a, FR-012b, and R4.
- Corroborated by: security and reliability

### PR-022: The error rule doesn't fit every call the check makes

- Priority: MINOR
- Category: Verification Gap
- Status: fixed
- Evidence:
  - `research.md §R4` (Timeouts and errors) item 1: eight `_paths` helpers
    take the keyword. `trunk_branch` passes it to `_resolve_declared` and
    `_bare_head`, and `_bare_head` passes it to `is_bare_layout`.
  - `plan.md §Technical Context` (Scale/Scope) says eight, and `§Project
    Structure` names the same eight.
  - `wfctl/_paths.py`: those eight are every function on the check's path that
    runs `git`. `declared_trunk` reads `wfctl.json` and runs no subprocess.
- Finding: Every `git` call under the helpers the check uses is now bounded,
  and the count matches the list.
- Why it matters: The plan's promise of a bound on every call now holds.
- Suggested response: Fixed by `research.md §R4` item 1 and `plan.md §Project
  Structure`.
- Corroborated by: adversarial implementation

### PR-023: A built-in group listed with an empty `reviewers` has no defined meaning

- Priority: MINOR
- Category: Requirement / Plan Mismatch
- Status: fixed
- Evidence: `spec.md §FR-019` and `§FR-021`, `data-model.md §Review group`,
  `contracts/config.md`, and the groups record's `§Decision` item 3.
- Finding: The case has one meaning everywhere.
- Why it matters: The person sees a config finding instead of a run that
  never completes.
- Suggested response: Fixed by FR-021 and the config contract.
- Corroborated by: requirements and traceability

### PR-024: Two design records still describe the shape before the fixes

- Priority: MINOR
- Category: Architecture / Decision Conflict
- Status: fixed
- Evidence: the guard record's `§Decision` now lists the first kind's three
  commands and the second kind's nine, matching `research.md §R4` and `§R6`,
  and its Log records the walkthrough.
- Finding: The records match the plan.
- Why it matters: A reader of the records sees the check the plan builds.
- Suggested response: Fixed by the record edits and their Log lines.
- Corroborated by: architecture and boundaries

### PR-025: The terminal check on the sign-off can be satisfied by a pseudo-terminal

- Priority: MINOR
- Category: Assumption Challenge
- Status: fixed
- Evidence: `spec.md §FR-013` and `§Edge Cases`, `research.md §R9`, and
  `contracts/cli.md §review sign-off`.
- Finding: The claim matches what the check delivers.
- Why it matters: Nobody reads the terminal check as enforcement.
- Suggested response: Fixed by FR-013 and R9.
- Corroborated by: security and reliability

### PR-026: The vendored `/security-review` file tells the reviewer to reply with a report that wfctl won't count

- Priority: MAJOR
- Category: Assumption Challenge
- Status: fixed
- Evidence: `plan.md §What the skill rewrites say` item 3.3, `research.md
  §R10` item 7.4, and `spec.md §FR-025`.
- Finding: The note's precedence over the vendored file is stated everywhere
  the note's jobs are listed.
- Why it matters: A security reviewer that follows the note writes a report
  wfctl counts.
- Suggested response: Fixed by item 3, R10 item 7, and FR-025.
- Corroborated by: adversarial implementation, requirements and traceability

### PR-027: The attribution test change leaves out a second filter that reads the same constant

- Priority: MINOR
- Category: Verification Gap
- Status: fixed
- Evidence: `research.md §R10` item 6 and `plan.md §Project Structure`.
- Finding: `_TEMPLATE_ROW` stays a string, and `_NOTICED_ROWS` and the new
  path-claim reader are planned.
- Why it matters: The existing template tests keep passing.
- Suggested response: Fixed by R10 item 6.
- Corroborated by: adversarial implementation

### PR-028: A substitution or a directory-changing wrapper moves the branch without a separator before the match

- Priority: MINOR
- Category: Risk / Failure Mode
- Status: fixed
- Evidence: `spec.md §FR-012b` and `research.md §R4` item 4 refuse a
  substitution. R4 (`gh`'s command words) refuses a substitution between `gh`
  and the verb, and R4 (An environment prefix or `env`) refuses `env -C`. The
  two limits this finding left recorded are now refusals.
- Finding: Both forms the earlier finding named refuse. PR-037 covers other
  wrappers that change the directory.
- Why it matters: SC-001's count no longer depends on these two limits.
- Suggested response: Fixed by FR-012b and R4.
- Corroborated by: security and reliability

### PR-029: The argument rule leaves an `owner:` head and grouped short flags undefined

- Priority: MINOR
- Category: Missing Information
- Status: fixed
- Evidence: `research.md §R4` items 1 and 4, `spec.md §FR-012a`, and the
  matching rows in `contracts/cli.md §Guard`.
- Finding: Both gaps are defined, and the fork head fails safe.
- Why it matters: A fork's same-named branch doesn't pass on `origin`'s
  reviews.
- Suggested response: Fixed by R4 and FR-012a.
- Corroborated by: security and reliability

### PR-030: The existing `opening-a-change` block chains `gh pr create` after two commands

- Priority: MINOR
- Category: Requirement / Plan Mismatch
- Status: fixed
- Evidence: `plan.md §What the skill rewrites say` item 1.5 names Step 5's
  block and gives its rewrite, now also with no environment prefix.
- Finding: The block is named, and the rewrite removes its chain and its `$(`.
- Why it matters: The skill doesn't show a form the check refuses.
- Suggested response: Fixed by item 1.5.
- Corroborated by: requirements and traceability

### PR-031: A `GIT_DIR=` prefix sends `gh` to another checkout's branch, the way `env -C` does

- Priority: MINOR
- Category: Risk / Failure Mode
- Status: fixed
- Evidence:
  - `spec.md §FR-012b` requires a refusal of a matched command preceded by a
    `NAME=value` word or by `env`, and `§Edge Cases` gives
    `GIT_DIR=../630-x/.git gh pr create --fill` as the example.
  - `research.md §R4` (An environment prefix or `env`) refuses every name
    rather than a list, and explains why.
  - `contracts/cli.md §Guard` has a row for `GH_REPO=`, `GIT_DIR=`,
    `NO_COLOR=1`, and `env -C`. `plan.md §Project Structure` lists the same
    cases, plus `GIT_WORK_TREE=`, in `test_review_gate.py`.
  - The guard record's second kind, item 6, says the same.
- Finding: The prefix refuses whatever variable it sets.
- Why it matters: SC-001 no longer counts a form the check can see and
  doesn't stop.
- Suggested response: Fixed by FR-012b and R4.
- Corroborated by: security and reliability

### PR-032: No artifact says which directory the check reads the branch and `HEAD` from

- Priority: MAJOR
- Category: Missing Information
- Status: fixed
- Evidence:
  - `research.md §R4` (Where the check reads from): the check reads the
    repository, the current branch, and `HEAD` from the payload's `cwd`, and
    runs every `gh` and `git` call there. Item 2 finds the root with
    `git -C <cwd> rev-parse --show-toplevel` and passes it as `repo_root`.
    Item 3 refuses a matched command whose payload has no `cwd`, or whose
    `cwd` isn't in a git repository, with the error refusal.
  - `spec.md §FR-012c` requires the same, and `plan.md §Constitution Check`
    ownership 8 names the host as the owner of the session's directory.
  - `contracts/cli.md §Guard` has a row for a payload `cwd` in `630-x` while
    the hook runs in the `main` checkout, and a row for a payload with no
    `cwd`.
  - `plan.md §Project Structure` lists both cases in `test_review_gate.py`,
    and the guard record's `§Decision` and `§Verification` say the same.
- Finding: Every artifact now names the payload's `cwd`. The `cd wt/630-x`
  scenario from the earlier finding is judged by `630-x`'s records, and
  `gh pr merge 631` from there refuses as another branch's pull request. A
  `cwd` in a subdirectory resolves to its worktree's root through
  `--show-toplevel`. PR-045 covers an environment override that still names
  the branch without reading `cwd`.
- Why it matters: The check and `gh` now act on the same branch.
- Suggested response: Fixed by R4, FR-012c, ownership 8, the contract rows,
  and the planned tests.
- Corroborated by: architecture and boundaries, adversarial implementation

### PR-033: The refusal for `gh` command words has no pattern that triggers it

- Priority: MAJOR
- Category: Missing Information
- Status: fixed
- Evidence:
  - `research.md §R6` pattern 8: `\bgh\s+` followed by a command word that
    holds `$`, a backslash, `*`, `?`, `[`, or `{`, or a quote or backtick
    anywhere but its last character. It refuses every time, on every branch.
  - `spec.md §FR-012b` says the refusal doesn't wait for one of FR-012's
    commands to match, and `§FR-016` sends a command on to the worktree check
    only when it holds none of these words.
  - `contracts/cli.md §Guard`: `gh pr $(git push -q) create`, `gh "$X" merge
    630`, `gh pr 'merge' 630`, and `gh pr m* 630` refuse, and
    `rg 'gh (pr|api)' wfctl/` and a commit message quoting `` `gh pr` `` aren't
    matched.
- Finding: The rule has a trigger, it says when it refuses, and FR-016 agrees.
  Each of the contract's four refused examples matches pattern 8, and each of
  the two passing examples doesn't. PR-043 covers ordinary commands the
  pattern refuses beyond the glob case R6 names.
- Why it matters: The contract's rows can pass, and the rule doesn't refuse
  every `gh` in the text.
- Suggested response: Fixed by R6 pattern 8, FR-012b, and FR-016.
- Corroborated by: adversarial implementation, requirements and traceability

### PR-034: The command-word rule covers the `-R` value, which always holds a slash, and skips the verb after it

- Priority: MINOR
- Category: Requirement / Plan Mismatch
- Status: fixed
- Evidence:
  - `research.md §R4` (`gh`'s command words): "The `-R` value isn't a command
    word. It always holds a `/`, and the comparison under Another repository
    reads it."
  - `research.md §R6` pattern 8 checks the run after the `-R` value when one
    follows `pr`.
- Finding: Both halves of the earlier finding are settled. `gh pr -R <this
  repo> 'merge' 630` refuses under pattern 8. PR-041 covers an attached `-R`
  value and `-R` placed before `pr`, which neither pattern 1 nor pattern 8
  reads.
- Why it matters: The two `-R` contract rows can both pass.
- Suggested response: Fixed by R4 and R6 pattern 8.
- Corroborated by: deterministic checks, security and reliability

### PR-035: A GraphQL mutation in a variable or a substitution matches no pattern

- Priority: MINOR
- Category: Risk / Failure Mode
- Status: fixed
- Evidence: `spec.md §Edge Cases` known limit 2.7 and `research.md §R6`
  (Known limits) item 8 record `gh api graphql -f query="$(cat m.graphql)"`
  as a limit that #627 covers.
- Finding: The hole is recorded rather than closed, as Andre decided on
  2026-10-24. SC-001 no longer counts it.
- Why it matters: An implementer doesn't need a rule for it, and a reader of
  the spec knows it stays open until #627.
- Suggested response: Fixed by the Edge Case and R6.
- Corroborated by: security and reliability

### PR-036: The new rules refuse `gh api` calls that are legitimate

- Priority: MINOR
- Category: Risk / Failure Mode
- Status: fixed
- Evidence: `spec.md §Edge Cases` (Some ordinary commands are refused) items
  1 to 3, and `research.md §R6` (Known wrong refusals).
- Finding: Each of the three wrong refusals is recorded with its rewording:
  write the path before `-f merge_method=merge`, use the `{owner}/{repo}`
  placeholders, and write a variable path out. Each rewording avoids the
  refusal as R4 and R6 describe the rules.
- Why it matters: An agent meeting one of these refusals on the
  stacked-merge path has a documented way past it.
- Suggested response: Fixed by the Edge Case and R6.
- Corroborated by: adversarial implementation

### PR-037: Other wrappers change the directory or the arguments `gh` runs with, the way `env -C` does

- Priority: MINOR
- Category: Risk / Failure Mode
- Status: fixed
- Evidence: `spec.md §Edge Cases` known limit 2.8 and `research.md §R6`
  (Known limits) item 9 name `uv run --directory ../630-x gh pr create`,
  `direnv exec ../630-x gh …`, and `<<<630 xargs gh pr merge`.
- Finding: All three forms the earlier finding named are recorded as limits.
- Why it matters: SC-001 no longer counts them.
- Suggested response: Fixed by the Edge Case and R6.
- Corroborated by: security and reliability

### PR-038: The trunk-checkout rule rests on the branch name a worktree can switch to

- Priority: MINOR
- Category: Assumption Challenge
- Status: fixed
- Evidence:
  - `plan.md §Constitution Check` ownership 6 now says the rule is a
    convention that keys on the branch name, and that #627 covers a worktree
    switched to the trunk branch.
  - `research.md §R4` (Another branch) item 3 strips `origin/` from the trunk
    ref before comparing, as R3 item 1 does, and item 4 calls the rule a
    convention.
  - The guard record's Consequences and the last row of `contracts/cli.md
    §Guard` say the same.
  - `wfctl/_paths.py`: `trunk_branch` returns `origin/<name>` or a local
    name, so stripping `origin/` gives the local name in both cases.
- Finding: Both halves of the earlier finding are settled, and the four files
  agree. PR-061 covers a numbering slip in the edited list.
- Why it matters: A merge from the trunk checkout now compares equal, and
  nobody reads ownership 6 as enforcement.
- Suggested response: Fixed by ownership 6, R4, the guard record, and the
  contract row.
- Corroborated by: architecture and boundaries, security and reliability

### PR-039: It is unclear which refusals carry the terminal sentence

- Priority: MINOR
- Category: Requirement / Plan Mismatch
- Status: fixed
- Evidence: `contracts/cli.md` now says above the error refusal block that
  every refusal where the check couldn't reach an answer uses it, and names
  them: a failed or timed-out lookup, an unreadable record or config, no
  trunk branch, a payload with no `cwd`, and any other error after a match.
  Each of those rows points at the block, and the timed-out lookup row now
  gives only the error refusal.
- Finding: Each row now says whether it carries the terminal sentence. The
  rows that judge a command, or refuse a spelling the rules can't read, don't.
- Why it matters: `plan.md §What the skill rewrites say` item 1.6 has the
  agent tell an error refusal from the others, and it now can.
- Suggested response: Fixed by the contract paragraph and its rows.
- Corroborated by: deterministic checks

### PR-040: Two spec passages still describe the earlier behavior

- Priority: MINOR
- Category: Requirement / Plan Mismatch
- Status: fixed
- Evidence:
  - `spec.md §US3` now says the three-round cap is a skill instruction that
    nothing enforces, and that #626 adds the enforcement. That agrees with
    `plan.md §Constitution Check`.
  - `spec.md §Validation Strategy` now pipes the other-branch merge from the
    checkout on the trunk branch, and pipes the same merge from a feature
    worktree to check that it refuses. That agrees with FR-012a and the
    plan's test list.
- Finding: Both passages match the plan.
- Why it matters: A reader of the spec gets the guarantee and the test scope
  the plan delivers.
- Suggested response: Fixed by US3 and the Validation Strategy.
- Corroborated by: deterministic checks, requirements and traceability

### PR-041: `-R` before `pr`, or attached to its value before the verb, merges with no pattern matching

- Priority: MAJOR
- Category: Requirement / Plan Mismatch
- Status: fixed
- Evidence:
  - `research.md §R6` pattern 1 is now
    `\bgh\s+(?:REPO\s+)?pr\s+(?:REPO\s+)?(create|new|merge)\b`, with `REPO`
    `(?:(?:-R|--repo)(?:\s+|=)\S+|-R\S+)`.
  - `research.md §R4` (Another repository) item 1 reads `-R` wherever it sits,
    and refuses more than one `-R` or `--repo`.
  - `research.md §R4` (`gh`'s command words) and `§R6` pattern 8 skip an `-R`
    flag and its value before either command word.
  - `spec.md §FR-012`, three new rows in `contracts/cli.md §Guard`, and the
    `test_review_gate.py` list in `plan.md §Project Structure` name the same
    spellings.
- Finding: Each spelling the earlier finding named now matches pattern 1, as
  run in Python: `gh -R andremarin/wfctl pr merge 630`,
  `gh --repo andremarin/wfctl pr create --fill`, and
  `gh pr -Randremarin/wfctl merge 630`, plus the `--repo=` and `-R=` forms.
  `gh -R <this repo> pr merge -R owner/other 630` matches and then refuses
  under the new two-`-R` rule. R6's note about the outer group is correct:
  without it, the spaced form before `pr` stops matching. `--repo` with an
  attached value and no `=` isn't a spelling `gh` accepts, so it needs no
  pattern. PR-046 covers other words `gh` accepts in the same two places.
- Why it matters: The three plain spellings now reach the review check, the
  trunk-checkout rule, and the repository comparison.
- Suggested response: Fixed by R6 pattern 1, R4, FR-012, the contract rows,
  and the planned tests.
- Corroborated by: security and reliability, adversarial implementation

### PR-042: The `gh` word itself, quoted or from a variable, matches no pattern

- Priority: MINOR
- Category: Risk / Failure Mode
- Status: fixed
- Evidence: `spec.md §Edge Cases` known limit 2.9 and `research.md §R6`
  (Known limits) item 10 record `"gh" pr merge 630` and `$GH pr merge 630`.
- Finding: The hole is recorded as a limit. PR-060 covers the R6 sentence
  that still dates every hole before the sixth review as closed by a rule.
- Why it matters: SC-001 no longer counts it.
- Suggested response: Fixed by the Edge Case and R6.
- Corroborated by: security and reliability

### PR-043: Pattern 8 refuses more ordinary commands than R6 says

- Priority: MINOR
- Category: Risk / Failure Mode
- Status: fixed
- Evidence:
  - `spec.md §Edge Cases` (Some ordinary commands are refused) items 4 to 6
    now give a rewording each:
    1. Item 4, a search that quotes a refused form: search without the `gh `
       prefix.
    2. Item 5, `which gh && gh pr view`: run `which gh` on its own.
    3. Item 6, a commit message that quotes a refused form: write the message
       to a file and commit with `git commit -F <file>`.
  - `research.md §R6` (Known wrong refusals) says the spec names the
    rewording for each.
- Finding: Each rewording avoids the refusal as R6 describes the patterns.
  `which gh` ends in `gh` with no word after it, so pattern 8 reads nothing.
  `git commit -F <file>` and a search such as `rg 'pr.*merge'` hold no `gh`
  followed by a word, and match none of patterns 1 to 7. R6 still files
  `which gh && gh pr view` under "a search or commit message quoting a
  refused form", which is loose, but the spec item it points at is right.
- Why it matters: An agent meeting any of the six wrong refusals has a
  documented way past it, and R6's claim that the spec names the rewording
  for each case now holds.
- Suggested response: Fixed by the Edge Case items 4 to 6.
- Corroborated by: adversarial implementation

### PR-044: A `gh` call made inside a script or program isn't refused or recorded

- Priority: MINOR
- Category: Requirement / Plan Mismatch
- Status: fixed
- Evidence: `spec.md §Edge Cases` known limit 2.10 and `research.md §R6`
  (Known limits) item 11 record a `gh` call inside a script the agent runs,
  and name `.github/scripts/release.py`.
- Finding: The limit is recorded, and naming `release.py` there answers the
  earlier question: the release PR isn't judged by the review check until
  #627. PR-063 covers aliases and shell functions, which are close to this
  case and not named.
- Why it matters: SC-001's "zero exceptions" no longer covers it.
- Suggested response: Fixed by the Edge Case and R6.
- Corroborated by: requirements and traceability, security and reliability

### PR-045: The `WFCTL_BRANCH` override names the current branch without reading `cwd`

- Priority: MINOR
- Category: Requirement / Plan Mismatch
- Status: fixed
- Evidence:
  - `research.md §R4` (Timeouts and errors) item 2: when `WFCTL_BRANCH` is
    set and names a different branch from the one checked out in `cwd`, the
    check refuses and says why, the same as for `WFCTL_STATE_DIR` in R5.
  - `contracts/cli.md §Guard` has a row for that case.
  - `spec.md §FR-012c` requires the branch from the session's directory.
- Finding: FR-012c and R4 now give the same answer, and the override can only
  agree with `cwd` or refuse. PR-062 covers the missing test.
- Why it matters: An implementer has one answer to build.
- Suggested response: Fixed by R4 item 2 and the contract row.
- Corroborated by: deterministic checks, architecture and boundaries

### PR-046: Other flags `gh` accepts before `pr` and before the verb still merge with no pattern matching

- Priority: MAJOR
- Category: Requirement / Plan Mismatch
- Status: fixed
- Evidence:
  - `research.md §R4` (What sits before a command word) and `§R6` pattern 8:
    one plain `-R` flag passes before the word after `gh` and before the verb
    after `gh pr`. Any other word starting with `-` there, and a second `-R`,
    refuses every time, on every branch.
  - `spec.md §FR-012b` and `§Edge Cases`, the new row in `contracts/cli.md
    §Guard`, the `test_review_gate.py` list in `plan.md §Project Structure`,
    and the guard record's Decision item 7 say the same.
- Finding: Both spellings the earlier finding named now refuse, as run in
  Python: `gh pr --squash=true merge 630` and
  `gh -R <this repo> -R owner/other pr merge 630`. The rule names the one
  spelling it allows, so a flag `gh` adds later refuses with no edit to the
  check. `gh pr mer --help` and `gh pr MERGE --help` don't reach
  `gh pr merge`, so a verb can't slip past pattern 1 that way either. PR-049
  covers the program name, which pattern 8 doesn't read.
- Why it matters: The list of refused spellings, which PR-019, PR-041, and
  this finding each found a gap in, is gone for the words between `gh` and
  the verb.
- Suggested response: Fixed by R4, R6 pattern 8, FR-012b, the contract row,
  and the planned tests.
- Corroborated by: security and reliability, adversarial implementation

### PR-047: A substitution with a space in an `-R` value hides the command words

- Priority: MINOR
- Category: Risk / Failure Mode
- Status: fixed
- Evidence:
  - `research.md §R4` (What sits before a command word): a plain value is
    `OWNER/REPO` or `HOST/OWNER/REPO`, with each part in letters, digits, `.`,
    `_`, and `-`. Item 2 says an `-R` value holding a quote, `$(`, or a
    backtick refuses.
  - `spec.md §FR-012b` and the new row in `contracts/cli.md §Guard` give
    `gh -R $(git push -q; echo a/b) pr merge 630` as a refusal, and the
    `test_review_gate.py` list carries an `-R` value holding `$(`.
- Finding: Pattern 8 now reads `$(git` as the `-R` value and refuses it as not
  plain, before it reaches `push`. The same holds after `pr`. A quoted value,
  such as `gh -R 'owner/repo' pr merge 630`, refuses too.
- Why it matters: A substitution can no longer hide the command words.
- Suggested response: Fixed by R4 item 2 and R6 pattern 8.
- Corroborated by: security and reliability

### PR-048: No artifact says how the check reads an `-R` that sits before the verb

- Priority: MINOR
- Category: Missing Information
- Status: fixed
- Evidence:
  - `research.md §R4` (Another repository) item 1 reads an `-R` value before
    `pr` or before the verb from the words pattern 8 read, and one after the
    verb from the `shlex.split` words. It reads `-R=value` and
    `--repo=value` without the `=`, and counts `-R` and `--repo` across all
    three places.
  - `contracts/cli.md §Guard` has a row for `gh -R=<this repo> pr merge 630`,
    and the `test_review_gate.py` list covers the `=` form and one `-R` before
    `pr` with one after the verb.
- Finding: An implementer now knows where each value comes from and how the
  count spans the two readers. The earlier finding also asked which value goes
  to `gh pr view`. That point is still open, and PR-050 carries it, since it
  matters only for a value with a host.
- Why it matters: `gh -R owner/other pr merge 630` now refuses by the
  comparison, and a test written from R4 can tell.
- Suggested response: Fixed by R4.
- Corroborated by: adversarial implementation

### PR-049: `GH pr create` and `GH pr merge` run `gh` on macOS and match no pattern

- Priority: MAJOR
- Category: Requirement / Plan Mismatch
- Status: fixed
- Evidence:
  - `research.md §R6` opening paragraph: the program word `gh` matches in any
    case, in the substring test and in every pattern that names it.
    Everything after the program word stays case-sensitive, since `-R` and
    `-r` are different flags, and `gh pr MERGE` runs as `gh pr`.
  - `contracts/cli.md §Guard` has a row judging `GH pr merge 630` and
    `/opt/homebrew/bin/Gh pr create --fill` as their lowercase forms.
  - `plan.md §Project Structure` lists `GH pr merge`, `Gh pr create`, and
    `GH api …/pulls` with a body in `test_review_gate.py`.
  - `spec.md §FR-012b`, a new `§Edge Cases` entry, and the guard record's
    Decision item 7 say the same.
- Finding: As run in Python, with `gh` matched in any case, the substring
  test and pattern 1 now match `GH pr merge 630`, `GH pr create --fill`, and
  `/opt/homebrew/bin/Gh pr create --fill`, and pattern 3 matches
  `GH api repos/{owner}/{repo}/pulls -f head=x -f base=main`. Keeping the
  rest case-sensitive is safe: `gh PR merge --help` exits 1 with
  `unknown command "PR"`, and GitHub returns 404 for a `PULLS` path, so
  neither a command word nor a REST path in another case reaches a merge.
- Why it matters: The plain spellings on Andre's machine now reach the check.
- Suggested response: Fixed by R6, FR-012b, the Edge Case, the contract row,
  and the planned tests.
- Corroborated by: security and reliability, adversarial implementation

### PR-050: An `-R` naming another GitHub host reads as this repository

- Priority: MINOR
- Category: Missing Information
- Status: fixed
- Evidence:
  - `research.md §R4` (Another repository) item 1: a value with three parts
    refuses unless the host is `github.com`, and is then compared after
    dropping the host. The check passes the value to `gh pr view` as written.
  - `spec.md §FR-012b`: a host other than `github.com` MUST refuse as another
    repository.
  - `contracts/cli.md §Guard` refuses `-R ghe.example.com/<this repo>` and
    judges `-R github.com/<this repo>` as this repository.
  - `spec.md §Edge Cases` and the guard record's Decision item 7 now allow
    `OWNER/REPO` or `github.com/OWNER/REPO`.
  - `plan.md §Project Structure` lists an `-R` host other than `github.com`
    refused.
- Finding: `gh pr -R ghe.example.com/aamarin/wfctl merge 630` now refuses,
  and the lookup reads the same value `gh` acts on. The Edge Case and the
  guard record agree with FR-012b. PR-053 covers a checkout that isn't on
  `github.com`, and a URL as the `-R` value.
- Why it matters: A pull request on another server no longer compares as
  this repository's.
- Suggested response: Fixed by R4, FR-012b, the Edge Case, Decision item 7,
  the contract row, and the planned test.
- Corroborated by: adversarial implementation, security and reliability

### PR-051: Pattern 3 doesn't say whether it reads an attached field or a query string after `/pulls`

- Priority: MAJOR
- Category: Missing Information
- Status: fixed
- Evidence:
  - `research.md §R6` pattern 3 items 1 to 4: the path can end in `/pulls`,
    `/pulls/`, or `/pulls?<query>`. A body flag counts as its own word,
    attached (`-fhead=x`), or after `=` (`--field=head=x`). A method counts as
    `-X` or `--method` with `POST` after a space, after `=`, or attached, in
    any case. Pattern 6 reads them the same way.
  - `spec.md §FR-012b` requires every spelling `gh` accepts, attached ones
    included, and `§Validation Strategy` pipes a create with attached
    `-fhead=x` fields.
  - `contracts/cli.md §Guard` refuses `-fhead=… -fbase=…`,
    `"…/pulls?x=1" --field=head=…`, and `-XPOST …/pulls/`, and the
    `test_review_gate.py` list in `plan.md §Project Structure` names the same
    five spellings.
- Finding: Both commands the earlier finding named now match pattern 3:
  `gh api repos/{owner}/{repo}/pulls -fhead=630-x -fbase=main -ftitle=t` and
  `gh api 'repos/{owner}/{repo}/pulls?x=1' -f head=630-x -f base=main`.
  PR-057 covers two spellings the lists still leave out.
- Why it matters: The two plain spellings now refuse.
- Suggested response: Fixed by R6 pattern 3, FR-012b, the contract row, and
  the planned tests.
- Corroborated by: adversarial implementation, security and reliability

### PR-052: The `gh stack` extension opens and merges pull requests, and no pattern matches it

- Priority: MAJOR
- Category: Missing Information
- Status: fixed
- Evidence:
  - `research.md §R4` (`gh`'s command words) items 1 to 4: the word after
    `gh` passes only when it is on a fixed list taken from `gh help` in `gh`
    2.91, less `copilot` and `agent-task`. Any other word refuses, which
    covers `gh stack`.
  - `research.md §R6` pattern 8 refuses a command word off the list every
    time, on every branch.
  - `spec.md §FR-012b` item 1 and `§Edge Cases`, the `gh stack merge` and
    `gh stack submit` row in `contracts/cli.md §Guard`, the
    `test_review_gate.py` list, and the guard record's Decision item 7 say
    the same.
- Finding: `gh stack submit --auto` and `gh stack merge` now refuse, and the
  list matches what `gh help` prints in `gh` 2.91. PR-055 covers
  `gh extension exec`, which runs the same extension through a listed word,
  and PR-056 covers a shortcut attached under a listed word.
- Why it matters: The plain spellings of the installed extension now refuse.
- Suggested response: Fixed by R4, R6 pattern 8, FR-012b, the Edge Case, the
  contract row, and the planned tests.
- Corroborated by: security and reliability, requirements and traceability

### PR-053: The `-R` host rule assumes the checkout is on `github.com`, and doesn't say how it reads a URL

- Priority: MINOR
- Category: Assumption Challenge
- Status: fixed
- Evidence: `spec.md §Edge Cases` known limit 2.11 and `research.md §R6`
  (Known limits) item 12 record a command aimed at another GitHub host
  through `gh api --hostname`, or through an `-R` value written as a URL.
- Finding: All three cases the earlier finding named are commands aimed at
  another host, and the limit covers them.
- Why it matters: The rule no longer claims to handle another host, so an
  implementer doesn't have to pick a reading for a URL value.
- Suggested response: Fixed by the Edge Case and R6.
- Corroborated by: adversarial implementation

### PR-054: A backtick substitution glued to `pr` hides the verb, and the merge runs with no pattern matching

- Priority: MAJOR
- Category: Requirement / Plan Mismatch
- Status: fixed
- Evidence:
  - `spec.md §Edge Cases` known limit 2.1 and `research.md §R6` (Known
    limits) item 2 record `` gh pr` git push -q` merge 630 ``.
  - `research.md §R6` pattern 8 item 1 now says the same form reads as `pr`
    and is a known limit.
- Finding: The rule that drops a trailing backtick stays, and the hole it
  leaves is recorded where an implementer reads the rule.
- Why it matters: Nobody builds pattern 8 believing it closes this form, and
  SC-001 no longer counts it.
- Suggested response: Fixed by the Edge Case, R6 pattern 8, and the limit
  list.
- Corroborated by: security and reliability, adversarial implementation

### PR-055: `gh extension exec` runs an extension through a listed command word

- Priority: MAJOR
- Category: Requirement / Plan Mismatch
- Status: fixed
- Evidence: `research.md §R4` (`gh`'s command words) item 1 now says an
  extension run through `gh extension exec` passes and is a known limit.
  `spec.md §Edge Cases` says the same beside the `gh stack merge` entry, and
  lists it as known limit 2.2. The guard record names it as an example.
- Finding: The artifacts no longer promise that every extension refuses.
- Why it matters: An implementer and #627's scope both see the gap.
- Suggested response: Fixed by R4, the Edge Cases, and the guard record.
- Corroborated by: security and reliability, requirements and traceability

### PR-056: A two-word `gh` alias under one of `gh`'s own commands merges with no pattern matching

- Priority: MAJOR
- Category: Assumption Challenge
- Status: fixed
- Evidence:
  - `research.md §R4` (`gh`'s command words) item 3 now says `gh` won't
    create a one-word shortcut named after one of its own commands, but
    accepts a two-word one such as `pr ship`, which is a known limit.
  - `spec.md §FR-012b` item 1 now says a one-word shortcut, and `§Edge
    Cases` lists the two-word form as known limit 2.3.
  - The guard record's limit paragraph and its last Log line name it.
- Finding: The claim the earlier finding challenged is corrected, and the
  removed limit is back.
- Why it matters: Neither the implementer nor #627's scope misses the gap.
- Suggested response: Fixed by R4, FR-012b, the Edge Cases, and the guard
  record.
- Corroborated by: security and reliability, adversarial implementation

### PR-057: Pattern 3 still lists the spellings it reads, and a fragment or a grouped flag creates a pull request

- Priority: MAJOR
- Category: Requirement / Plan Mismatch
- Status: fixed
- Evidence:
  - `research.md §R6` pattern 3 items 1 and 2 now say a path ending in a
    fragment and a body flag grouped after another short flag aren't read,
    and are known limits.
  - `spec.md §FR-012b` now names the three spellings it requires rather than
    "every spelling `gh` accepts", and `§Edge Cases` lists both forms as
    known limit 2.4.
- Finding: FR-012b and R6 now describe the same lists, and the two spellings
  outside them are recorded.
- Why it matters: An implementer who builds R6's lists builds what FR-012b
  requires.
- Suggested response: Fixed by FR-012b, R6 pattern 3, and the Edge Cases.
- Corroborated by: adversarial implementation, security and reliability

### PR-058: `gh` with nothing written after it takes its command words from stdin

- Priority: MINOR
- Category: Risk / Failure Mode
- Status: fixed
- Evidence: `spec.md §Edge Cases` known limit 2.5 and `research.md §R6`
  (Known limits) item 6 record `printf '%s\n' pr merge 630 | xargs gh`.
- Finding: The hole is recorded as a limit.
- Why it matters: SC-001 no longer counts it.
- Suggested response: Fixed by the Edge Case and R6.
- Corroborated by: security and reliability

### PR-059: A `repositories/<id>/` path names another repository, and the comparison doesn't read it

- Priority: MINOR
- Category: Risk / Failure Mode
- Status: fixed
- Evidence: `spec.md §Edge Cases` known limit 2.6 and `research.md §R6`
  (Known limits) item 7 record a merge through a
  `repositories/<id>/pulls/<n>/merge` path.
- Finding: The hole is recorded as a limit.
- Why it matters: SC-001 no longer counts it.
- Suggested response: Fixed by the Edge Case and R6.
- Corroborated by: adversarial implementation

### PR-060: Three passages still state the refusal rule more broadly than the limit list allows

- Priority: MINOR
- Category: Requirement / Plan Mismatch
- Status: fixed
- Evidence:
  - `plan.md §Summary` now says the check refuses "the commands its rules
    can't read for sure", and that every hole still open on 2026-10-24, and
    any found later, is a known limit listed in the spec's Edge Cases, which
    the required CI check in #627 closes.
  - `research.md §R6` (Which holes refuse and which are recorded) item 1 and
    the guard record's paragraph after Decision item 8 date the cutoff the
    same way. R6 item 1 also names PR-035 and PR-042 as limits that the
    sorting test would otherwise refuse.
- Finding: No artifact counts reviews any more, and the Summary no longer
  promises a refusal for the recorded limits. The three passages agree with
  each other and with the limit list. PR-064 covers the date, which falls on
  a day the check still gained rules.
- Why it matters: The tasks step reads the Summary first, and it now points
  at the limit list rather than promising to refuse what is on it.
- Suggested response: Fixed by `plan.md §Summary`, R6 item 1, and the guard
  record.
- Corroborated by: deterministic checks, requirements and traceability

### PR-061: R4 (Another branch) numbers two items 3

- Priority: MINOR
- Category: Requirement / Plan Mismatch
- Status: fixed
- Evidence: `research.md §R4` (Another branch) now runs 1 to 5, with the
  refusal text as item 5. No artifact cites one of its items by number;
  `plan.md §Constitution Check` ownership 6 cites the section.
- Finding: Each item has one number.
- Why it matters: A task or test that cites an item by number names one item.
- Suggested response: Fixed by the renumbering.
- Corroborated by: deterministic checks

### PR-062: The plan's test list has no case for the two override refusals

- Priority: MINOR
- Category: Verification Gap
- Status: fixed
- Evidence:
  - `plan.md §Project Structure`: the `test_review_gate.py` list now names
    `WFCTL_STATE_DIR` set while another branch is judged, and `WFCTL_BRANCH`
    naming a branch other than the `cwd`'s, both refused. It says every other
    gate test clears `WFCTL_BRANCH` or sets it to the `cwd`'s branch, since
    fixtures in `tests/conftest.py` set it.
  - `contracts/cli.md §Guard` rows for both overrides, `research.md §R4`
    (Timeouts and errors) item 2, and `§R5` define the same two refusals.
  - `tests/conftest.py` sets `WFCTL_BRANCH` at lines 254 and 446.
- Finding: Both refusals have a planned test, and the fixture interaction is
  written where the gate tests are planned.
- Why it matters: The PR-045 fix now has a test that fails without it, and a
  gate test won't pass or refuse for the wrong reason.
- Suggested response: Fixed by the test list.
- Corroborated by: adversarial implementation

### PR-063: A git alias or a shell function that runs `gh` is a disguise no limit names

- Priority: MINOR
- Category: Risk / Failure Mode
- Status: fixed
- Evidence: `spec.md §Edge Cases` known limit 2.10 now records a `gh` call
  inside something the agent runs whose text the command doesn't show: a
  script such as `.github/scripts/release.py`, a git alias written into
  `.git/config` such as `pm = !gh pr merge`, or a shell function or alias
  from the person's profile. `research.md §R6` (Known limits) item 11 says
  the same and cites PR-063.
- Finding: Both forms the earlier finding named are recorded as known
  limits, as Andre's decision asks, and no rule was added for them.
- Why it matters: SC-001 no longer counts them.
- Suggested response: Fixed by the Edge Case and R6.
- Corroborated by: security and reliability

### PR-064: Rules were still being added on 2026-10-24, so the date alone doesn't mark the cutoff

- Priority: MINOR
- Category: Requirement / Plan Mismatch
- Status: open
- Evidence:
  - `research.md §R6` (Which holes refuse and which are recorded) item 1:
    "That rule covers the holes fixed before 2026-10-24. Every hole still
    open on that date, and any found later, is recorded as a known limit
    instead of becoming a new rule."
  - `plan.md §Summary`: "Every hole still open on 2026-10-24, and any found
    later, is a known limit instead". The guard record's paragraph after
    Decision item 8 says the same.
  - The guard record's own Log has a 2026-10-24 line that adds two rules: the
    word after `gh` has to be one of `gh`'s own commands, and a `gh api`
    create is read in every body-flag spelling. Commit 5a2863d, which made
    that edit, is dated 2026-10-24 00:36 -0500.
  - `docs/architecture/scans/622-plan-review.md`: the review at
    2026-10-24T04:46Z marks PR-049 and PR-050 fixed by new rules, and the
    review at 05:48Z marks PR-051 and PR-052 fixed the same way. PR-051 and
    PR-052 were open when 2026-10-24 began.
  - `spec.md §Clarifications` (Session 2026-10-24): "A disguise found from
    now on is recorded as a known limit". That places the cutoff at the
    decision, not at the start of the day.
- Finding: The edit replaced a review count with a date, as the earlier
  review suggested under PR-060, but the check still gained rules on that
  date. PR-051 and PR-052 were open on 2026-10-24 and became rules, so R6
  item 1 now says they should have been recorded as limits. Its phrase "the
  holes fixed before 2026-10-24" also leaves out the four holes that the
  rules added that day close. The cutoff the artifacts mean is Andre's
  decision, after the review at 05:48Z, which the Clarification already
  says. The earlier review's suggestion named the date, and that is where
  the slip came from.
- Why it matters: This is the reader PR-060 named. A reader who checks
  `gh stack merge` against R6 item 1 finds a hole that was open on
  2026-10-24 and is a rule rather than a limit, and may take the rule back
  out or wonder which list is wrong. Nothing an implementer builds changes.
- Suggested response: Name the decision rather than the day, in R6 item 1,
  the plan's Summary, and the guard record. For example, "Every hole still
  open when the check stopped adding rules on 2026-10-24, and any found
  later, is a known limit", and in R6 item 1, "That rule covers the holes
  fixed up to the plan review at 2026-10-24T05:48Z".
- Corroborated by: deterministic checks, requirements and traceability

## Requirement-to-plan trace

| Requirement / criterion | Plan location | Review note |
| --- | --- | --- |
| FR-001 | plan.md §What the skill rewrites say 1.1 | covered |
| FR-002 | plan.md §What the skill rewrites say 3, research.md §R10 | covered |
| FR-003 | plan.md §What the skill rewrites say 1.2 | covered |
| FR-004 | plan.md §What the skill rewrites say 1.3 | covered |
| FR-005 | data-model.md §Run record, contracts/cli.md §review start | covered |
| FR-006 | research.md §R3 | covered |
| FR-007 | research.md §R3, data-model.md §Last reviewed commit | covered |
| FR-008 | research.md §R2, plan.md §What the skill rewrites say 2.2 and 3.3 | covered |
| FR-009 | data-model.md §State a run moves through | covered |
| FR-010 | contracts/cli.md §review check | covered |
| FR-011 | data-model.md, contracts/cli.md §review start | covered |
| FR-012 | research.md §R4, §R6, contracts/cli.md §Guard | covered; limits recorded in spec.md §Edge Cases |
| FR-012a | research.md §R4 (Another branch, Another repository), §R5, plan.md §What the skill rewrites say 1.6 | covered |
| FR-012b | research.md §R4 (`gh`'s command words, What sits before a command word), §R6 patterns 3 and 8, plan.md §What the skill rewrites say 1.5 | covered; wrong refusals and their rewordings in spec.md §Edge Cases |
| FR-012c | research.md §R4 (Where the check reads from, Timeouts and errors item 2), plan.md §Constitution Check ownership 8, §Project Structure (`test_review_gate.py`) | covered |
| FR-013 | research.md §R6, §R9 | covered |
| FR-014 | research.md §R9, data-model.md §Sign-off | covered |
| FR-015 | research.md §R4 (Timeouts and errors), contracts/cli.md §Guard, plan.md §What the skill rewrites say 1.6 | covered |
| FR-016 | research.md §R6, plan.md §Project Structure (`_hook.py`) | covered |
| FR-017 | contracts/cli.md §relay, research.md §R8 | covered |
| FR-018 | contracts/config.md | covered |
| FR-019 | data-model.md §Review group | covered |
| FR-020 | data-model.md §Review group, contracts/config.md | covered |
| FR-021 | contracts/config.md §findings | covered |
| FR-022 | contracts/config.md, contracts/cli.md §review groups | covered |
| FR-023 | research.md §R7 | covered |
| FR-024 | research.md §R10, plan.md §Project Structure | covered |
| FR-025 | research.md §R10 item 7, plan.md §What the skill rewrites say 3 | covered |
| FR-026 | plan.md §What the skill rewrites say 2 | covered |
| SC-001 | research.md §R4, §R6, spec.md §Edge Cases, plan.md §Summary | covered; PR-064 on how the limit list's cutoff is dated |
| SC-002 | plan.md §Project Structure (`test_review.py`) | covered |
| SC-003 | research.md §R6, plan.md §Constitution Check | covered |
| SC-004 | plan.md §Project Structure (`test_review_store.py`) | covered |
| SC-005 | contracts/config.md, quickstart.md step 1 | covered |

## Assumptions challenged

- The day 2026-10-24 marks when the check stopped adding rules. Rules were
  still added early that day, and the decision came after the review at
  05:48Z (PR-064).
- The spec's Session 2026-10-24 Clarification says "from now on", while the
  plan, R6, and the guard record give a date. The Clarification's wording is
  the one that matches what happened, and the two read the same once PR-064
  is fixed.
- Only the checkout on the trunk branch acts on another branch's pull
  request. The artifacts say this is a convention, and the other branch
  still has to be reviewed, so SC-001 holds either way.
- The host updates the payload's `cwd` when a `cd` in one command carries
  over to the next. Ownership 8 states this. The planned test pipes a payload
  with a chosen `cwd`, so it checks how wfctl reads the field, not how the
  host fills it.
- A reviewer follows `reviewing-security`'s note over the vendored file's last
  line, and `codex exec --sandbox read-only` prints a report the relay can
  save. Both are stated, and nothing has run them yet.

## Reviewer disagreement

- None identified. The lenses ran in sequence in one agent. PR-064 is MINOR
  because the limit list and the rules are both right, and only the sentence
  that dates the boundary between them is off by a few hours.

## Strengths worth preserving

- `plan.md §Summary` now sends the tasks step to the spec's list of known
  limits and to #627, rather than promising a refusal for them.
- The `test_review_gate.py` list says why the other gate tests have to clear
  or match `WFCTL_BRANCH`, so an implementer learns about the fixture
  interaction where the tests are planned.
- `spec.md §Edge Cases` gives each wrong refusal its own rewording, and
  sorts the gaps into commands that pass and commands that refuse wrongly.
- `research.md §R4` and `§R6` say which spellings each rule doesn't read,
  next to the rule, so an implementer learns a limit where it applies rather
  than only from the Edge Cases.
- `research.md §R4` checks `WFCTL_BRANCH` against `cwd` instead of choosing
  one, the same move R5 makes for `WFCTL_STATE_DIR`.
- `research.md §R4` (`gh`'s command words) lists the commands it allows
  rather than the ones it refuses, so a command a newer `gh` adds refuses
  until it is listed.

## Source freshness

This review describes only the content identities listed under
`## Reviewed inputs`. When `spec.md`, `plan.md`, a binding design record, or a
material planning artifact changes, this report no longer describes the
current plan, and a new review is needed before it counts as current evidence.
