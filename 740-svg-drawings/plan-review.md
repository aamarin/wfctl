# Plan Review Report

Review state: completed
Review type: re-review

## Reviewed inputs

| Artifact | Content identity | Role |
| --- | --- | --- |
| plan.md | 9b28d25d3b45b251dfe7bc8c2e93f4667c53a8a5 | technical strategy |
| spec.md | 81f85cbca453832f227ac928bc10852632da2775 | requirements |
| .specify/memory/constitution.md | absent | constitution |
| design.md | 7575e6e8fe6f530f3d78ebba7158c159fb6c0834 | design-record index |
| docs/architecture/design/740-one-drawing-reader.md | cbce100ef658286191756a8975462a67bc5cd9c4 | design record |
| docs/architecture/design/740-drawing-style-one-file.md | 8188b04cc03b1fa9726d8ae69e7bd45c7e2bc28e | design record |
| docs/architecture/record-drawing-can-be-svg.md | 9241aee3471d0d12e38497a602df952c3506d274 | level-2 record |
| research.md | e3c1f1831803b2e0221510603c6adbd781b275e7 | planning evidence |
| data-model.md | 7f0e8d8868fc37c06b6c11bb298eb50e4ae0be08 | data model |
| contracts/cli.md | ae564e71737bd48779115ae8065619c13fb27982 | CLI contract |
| quickstart.md | 8b16046e12d96a3c95e571eb3c96f63565308b92 | verification guide |
| plan-review.plan.md | 9a22ac8d7c4959039542743db84ba9d4764f6d74 | base of this re-review |

## Review scope

- Re-review: the plan copy's identity equals the earlier report's `plan.md`
  row (`9a22ac8…`)
- Changed since the earlier report: `plan.md` §Technical Context
  (Constraints: the `no drawing` line now shows in the design gate's reason,
  and doctor doesn't print it), §Project Structure (`_paths.py` gains
  `record_change`, `decided_on_this_branch` and `records_on_this_branch(skip=)`;
  `_record_gate.py`, `_evidence.py`, `cli.py` and `arch/__init__.py` entries;
  `_records.py` gains `REDRAWN_LINE` and `redraw_only`; new
  `test_redraw_only.py`, `test_paths_redraw.py`, and extended
  `test_design_gate_drawing.py` and `test_scan_files.py` entries), and
  §A redraw on a branch, rewritten. Reviewed together with §Constitution Check,
  which describes what `arch/__init__.py` exports.
- Inputs the caller named as changed, each re-read in full with the whole of
  `plan.md` reviewed against it: `plan.md` (the Constraints sentence),
  `spec.md` (FR-011's two-item list), and `contracts/cli.md` (the first
  paragraph under "The reworded fix text"). `spec.md` also carries the
  FR-026 wording that the revision for PR-020 and PR-025 added.
- Other inputs whose identity differs from the earlier row, re-read in full:
  `research.md` (R-014 rewritten; R-010 read again for the FR-011 claim) and
  `quickstart.md` (§1 item 3, the redraw tests). `design.md`, `data-model.md`,
  and the three records match their earlier rows.
- The FR-011 correction was checked against the code rather than taken from
  the caller. `accept_blockers` appends `"no drawing: add a fenced block under
  '## Boundary'"` as a whole string, and `accept_problems` returns
  `accept_blockers(record)` plus only the `problem` half of each
  `kind_refusals` entry, so the `no drawing` line reaches every
  `accept_problems` reader and the `_DRAWING_FIX` text, which lives in
  `Refusal.fix`, doesn't. `_evidence.py:1641` builds the design gate's reason
  from `accept_problems`, and `tests/pipeline_payload_snapshot.json:914-916`
  carries the line as both the annotation and the reason. `validate` emits
  no `no drawing` finding, so doctor doesn't print it. The claim holds.
- Design records: 2 listed in design.md, both read
  (`740-one-drawing-reader`, `740-drawing-style-one-file`), plus the level-2
  record the feature implements
- Unresolved markers: no `[NEEDS CLARIFICATION`, TODO, or TBD in `spec.md` or
  any planning artifact
- Lenses: requirements and traceability, architecture and boundaries,
  adversarial implementation and verification
- Conditional lenses: security and reliability applied. The feature adds a
  worktree-guard refusal and a terminal check meant to keep an agent from
  performing a person's sign-off, and R-014 adds an exclusion that lets a
  redraw-only record change pass the record and design gates. It touches no
  secrets or network.
- Existing code inspected: `wfctl/arch/_records.py` (`_DRAWING_FIX`,
  `_drawing_refusals`, `kind_refusals`, `accept_blockers`, `accept_problems`,
  `validate`'s drawing findings), `wfctl/_evidence.py` (`_level_records`,
  `_architecture_answered`, `branch_records`, `fact_architecture_accepted`,
  the `accept_problems` call at line 1641), `wfctl/_paths.py`
  (`non_record_subtrees`, `touched_on_this_branch`, `records_on_this_branch`),
  `wfctl/_record_gate.py` (`touched`, its imports of `wfctl.arch`),
  `wfctl/cli.py` (the `record:` listing, `_observe`, the `acceptable` listing,
  the record-committed check), `.github/scripts/check_imports.baseline` (the
  contexts of `_paths`, `_evidence`, `_record_gate`), every test that names
  `no drawing`, and `tests/test_scan_files.py`'s boundary tests
- Reviewers: the lenses above, run in sequence by one agent

## Summary

BLOCKER: 0
MAJOR: 0
MINOR: 2

No BLOCKER findings identified in this review. PR-020, PR-025, PR-026 and
PR-027 are fixed, and PR-001 to PR-019 and PR-021 to PR-024 stay fixed. Every
reader that asks what a branch decided now takes `arch.redraw_only`, the
general boundary check and `cli._observe` included, and `record_change` diffs
the merge base against the working tree and keeps a record whenever it can't
answer. The FR-011 correction is right, and the spec, plan, contract, and
quickstart agree on it. Two MINOR findings remain: `research.md §R-010` and
the plan's Constitution Check each keep a line the revisions made untrue
(PR-028), and R-014's contract reads wrong for a deleted record and, taken
literally, for the no-newline case it means to allow (PR-029).

## Findings

### PR-001: The extended `no drawing` line and the corpus snapshot can't both hold

- Priority: MAJOR
- Category: Requirement / Plan Mismatch
- Status: fixed
- Evidence:
  - `contracts/cli.md §The reworded fix text`; `research.md §R-010`
- Finding: The contract picks the broad reading, and the comparison allows for
  it explicitly.
- Why it matters: The corpus check can pass without re-taking a snapshot.
- Suggested response: Fixed.
- Corroborated by: requirements and traceability

### PR-002: The accept output for a drawing with a problem is unspecified

- Priority: MAJOR
- Category: Missing Information
- Status: fixed
- Evidence:
  - `contracts/cli.md §A drawing with a problem`; `data-model.md §Problem`
- Finding: The full list and each fix are stated.
- Why it matters: Tests that assert output have one answer.
- Suggested response: Fixed.
- Corroborated by: adversarial implementation

### PR-003: doctor doesn't repeat a one-kind record's drawing problems

- Priority: MAJOR
- Category: Requirement / Plan Mismatch
- Status: fixed
- Evidence:
  - `contracts/cli.md §Doctor`; `quickstart.md §1 item 1`
- Finding: The path doctor reads for a one-kind problem is named and tested.
- Why it matters: FR-001's doctor warning fires for the record it names.
- Suggested response: Fixed.
- Corroborated by: requirements and traceability

### PR-004: FR-006's per-format wording conflicts with "checks never see either format"

- Priority: MAJOR
- Category: Architecture / Decision Conflict
- Status: fixed
- Evidence:
  - `data-model.md §Drawing` `failure_fix`; `740-one-drawing-reader.md
    §Verification`
- Finding: The check reads `failure_fix`, never `format`.
- Why it matters: The record's verification bullet holds.
- Suggested response: Fixed.
- Corroborated by: architecture and boundaries

### PR-005: The skills' mermaid-default prose isn't in the plan's edits

- Priority: MAJOR
- Category: Requirement / Plan Mismatch
- Status: fixed
- Evidence:
  - `plan.md §Skill prose that changes`; `quickstart.md §5`
- Finding: The templates and the skill text agree.
- Why it matters: An agent reads one rule, not two.
- Suggested response: Fixed.
- Corroborated by: requirements and traceability

### PR-006: A snapshot of every record on disk breaks unrelated later branches

- Priority: MAJOR
- Category: Verification Gap
- Status: fixed
- Evidence:
  - `research.md §R-010`: a one-off comparison in the scratchpad
- Finding: Nothing pins live records.
- Why it matters: A later record-writing branch can't trip over this feature.
- Suggested response: Fixed.
- Corroborated by: adversarial implementation

### PR-007: An accepted record's SVG can change with no check or gate noticing

- Priority: MAJOR
- Category: Boundary / Ownership Concern
- Status: fixed
- Evidence:
  - `plan.md §What drawings/ being excluded costs`; `spec.md §FR-020`,
    `§FR-021`
- Finding: An edit to an accepted record's SVG reaches the user through doctor.
- Why it matters: The protection the record body had is restored for the SVG.
- Suggested response: Fixed.
- Corroborated by: architecture and boundaries

### PR-008: How the SVG path is resolved and printed is unstated

- Priority: MINOR
- Category: Missing Information
- Status: fixed
- Evidence:
  - `data-model.md §Problem` and `§Building it`; `research.md §R-008`
- Finding: Each question has a one-line answer that matches the code.
- Why it matters: The output strings tests assert on are fixed.
- Suggested response: Fixed.
- Corroborated by: adversarial implementation

### PR-009: The plan says `_records.py` already imports `_paths`, and it doesn't

- Priority: MINOR
- Category: Dependency / Feasibility
- Status: fixed
- Evidence:
  - `plan.md §Constitution Check`, post-design re-check
- Finding: The sentence matches the code.
- Why it matters: The gate's reasoning is accurate.
- Suggested response: Fixed.
- Corroborated by: architecture and boundaries

### PR-010: `test_arch_labels.py` can't be both unchanged and run against `read_fence`

- Priority: MINOR
- Category: Verification Gap
- Status: fixed
- Evidence:
  - `data-model.md §Building it`; `plan.md §Project Structure`
- Finding: The plan says which way the test changes.
- Why it matters: The mermaid reader keeps its regression tests.
- Suggested response: Fixed.
- Corroborated by: adversarial implementation

### PR-011: The "file missi" recreation doesn't match the original drawing

- Priority: MINOR
- Category: Verification Gap
- Status: fixed
- Evidence:
  - `research.md §R-003`, `quickstart.md §1 item 1` and `§4`: `x="708"`
- Finding: The recreation matches commit `0d7e56d`.
- Why it matters: SC-005 tests the overflow the user saw.
- Suggested response: Fixed.
- Corroborated by: adversarial implementation

### PR-012: "Built once per drawing" doesn't describe the planned code

- Priority: MINOR
- Category: Requirement / Plan Mismatch
- Status: fixed
- Evidence:
  - `spec.md §FR-009`; `data-model.md §State`
- Finding: The spec and the plan describe the same property.
- Why it matters: The plan claims no property it lacks.
- Suggested response: Fixed.
- Corroborated by: requirements and traceability

### PR-013: XML safety rests on one machine's expat, and other read failures are unnamed

- Priority: MINOR
- Category: Assumption Challenge
- Status: fixed
- Evidence:
  - `research.md §R-001`; `data-model.md §Problem`
- Finding: A DOCTYPE is refused and every read failure becomes a problem line.
- Why it matters: Entity handling doesn't depend on the local expat.
- Suggested response: Fixed.
- Corroborated by: security and reliability

### PR-014: Two SVG images under one heading leave the second unchecked

- Priority: MINOR
- Category: Risk / Failure Mode
- Status: fixed
- Evidence:
  - `research.md §R-007`; `data-model.md §Validation rules`
- Finding: Two SVG links under one heading are a problem.
- Why it matters: A second picture can't pass unchecked.
- Suggested response: Fixed.
- Corroborated by: adversarial implementation

### PR-015: The `_DRAWING_FIX` rewording is a second wording change the spec and the research both rule out

- Priority: MAJOR
- Category: Requirement / Plan Mismatch
- Status: fixed
- Evidence:
  - `spec.md §FR-011`; `contracts/cli.md §The reworded fix text`
- Finding: The rewording is a stated decision in every artifact, and R-010's
  rationale no longer says the three test files run unchanged. A separate
  stale sentence in R-010 is PR-028.
- Why it matters: An implementer has one answer.
- Suggested response: Fixed.
- Corroborated by: requirements and traceability

### PR-016: `model-the-domain` still states mermaid for records, and the rewrite extends SVG to domain documents the spec doesn't cover

- Priority: MINOR
- Category: Requirement / Plan Mismatch
- Status: fixed
- Evidence:
  - `plan.md §Skill prose that changes` and `§Project Structure`: both list
    `model-the-domain/SKILL.md`
- Finding: Both halves are answered, and the structure tree carries the file.
- Why it matters: The skill and its reference file agree.
- Suggested response: Fixed.
- Corroborated by: requirements and traceability

### PR-017: The doctor warning for an accepted record's broken SVG isn't in the spec

- Priority: MINOR
- Category: Scope Expansion
- Status: fixed
- Evidence:
  - `spec.md §FR-021`
- Finding: The spec carries the warning.
- Why it matters: The code and the spec agree.
- Suggested response: Fixed.
- Corroborated by: requirements and traceability

### PR-018: The spec's validation strategy still asks for a committed corpus test

- Priority: MINOR
- Category: Requirement / Plan Mismatch
- Status: fixed
- Evidence:
  - `spec.md §Validation Strategy`
- Finding: The spec describes the comparison the plan makes.
- Why it matters: `analyze` won't look for a test that isn't written.
- Suggested response: Fixed.
- Corroborated by: requirements and traceability

### PR-019: The DOCTYPE check scans bytes, so a UTF-16 SVG slips past it

- Priority: MINOR
- Category: Assumption Challenge
- Status: fixed
- Evidence:
  - `spec.md §FR-025`; `research.md §R-001`; `quickstart.md §1`
- Finding: Both suggested responses are in the plan, with tests.
- Why it matters: The "every machine" claim holds.
- Suggested response: Fixed.
- Corroborated by: security and reliability

### PR-020: A `redrawn` Log line reads to both gates as a branch that answered the boundary question

- Priority: MAJOR
- Category: Risk / Failure Mode
- Status: fixed
- Evidence:
  - `research.md §R-014`, the five readers: `_record_gate.touched`,
    `_evidence.branch_records`, `_evidence._level_records`, the `record:`
    lines in `cli.py`, and `_evidence._architecture_answered` with
    `cli._observe`, which switch from `touched_on_this_branch` to
    `decided_on_this_branch`
  - `plan.md §Project Structure`: `_evidence.py` and `cli.py` both listed with
    `decided_on_this_branch`; `_observe` placed in `cli.py`, which matches the
    code at `cli.py:1314-1329`
  - `quickstart.md §1 item 3`: the design gate test with no exception present,
    once with a name list and once without, and `test_scan_files.py` for the
    `Boundary` line and the `record:` lines
- Finding: The general boundary check and the session's Boundary line now
  reach the exclusion, `_observe` sits in the right module, and every reader
  FR-026 names has a test.
- Why it matters: A redraw no longer answers the boundary question in a repo
  without a context name list.
- Suggested response: Fixed.
- Corroborated by: architecture and boundaries, adversarial implementation

### PR-021: The terminal check breaks real accepts in two test files the plan calls unchanged or doesn't list

- Priority: MINOR
- Category: Verification Gap
- Status: fixed
- Evidence:
  - `plan.md §Project Structure`; `research.md §R-013`; `quickstart.md §1`
- Finding: Both files are listed, and the check's position is stated with its
  reason.
- Why it matters: The test list matches what the change breaks.
- Suggested response: Fixed.
- Corroborated by: adversarial implementation

### PR-022: Stale cross-references left by the revision

- Priority: MINOR
- Category: Requirement / Plan Mismatch
- Status: fixed
- Evidence:
  - `research.md §R-010` Rationale; `plan.md §Project Structure`
- Finding: All three lines describe the current plan.
- Why it matters: `tasks` reads the right file list.
- Suggested response: Fixed.
- Corroborated by: requirements and traceability

### PR-023: `architecture-decisions` still says an accepted record changes only by status

- Priority: MINOR
- Category: Requirement / Plan Mismatch
- Status: fixed
- Evidence:
  - `plan.md §Skill prose that changes`: the `architecture-decisions/SKILL.md:230-237`
    row
- Finding: The skill and the plan will agree on the record lifecycle.
- Why it matters: An agent editing a record reads one rule.
- Suggested response: Fixed.
- Corroborated by: requirements and traceability

### PR-024: The redraw path leaves two cases undefined

- Priority: MINOR
- Category: Missing Information
- Status: fixed
- Evidence:
  - `spec.md §FR-022`; `contracts/cli.md §wfctl arch accept on an accepted
    record`; `quickstart.md §1 item 3`
- Finding: Both cases have one answer and a test.
- Why it matters: Tests can assert on them.
- Suggested response: Fixed.
- Corroborated by: adversarial implementation

### PR-025: `redraw_only` reads only the committed diff, while one of its readers lists working-tree changes

- Priority: MAJOR
- Category: Risk / Failure Mode
- Status: fixed
- Evidence:
  - `research.md §R-014` items 1 and 3: an empty diff isn't a redraw;
    `record_change` diffs the merge base against the working tree and returns
    None with no trunk, on a git failure, or when the merge base has no file
    at the path; a None keeps the record
  - `research.md §R-014`, reader 1: the record gate diffs `trunk...head`
    through the guard's session, so a git error refuses
  - `quickstart.md §1 item 3`: `test_paths_redraw.py` covers an uncommitted
    edit beside a committed redraw, an untracked record, and no trunk
- Finding: Each reader has its own diff, and every case the plan can't answer
  keeps the record, which fails closed.
- Why it matters: A record written moments ago still answers the boundary
  question.
- Suggested response: Fixed.
- Corroborated by: adversarial implementation, security and reliability

### PR-026: The redraw pattern matches outside `## Log` and on a record of any status

- Priority: MINOR
- Category: Risk / Failure Mode
- Status: fixed
- Evidence:
  - `research.md §R-014` item 1: the record's status at the new side is
    `accepted`, and each added line's new-side number, read from the hunk
    header, falls inside `## Log` as `_log_bounds` finds it
  - `quickstart.md §1 item 3`: `test_redraw_only.py` covers a proposed record
    and a `redrawn`-shaped bullet under `## Decision`
- Finding: The exclusion's edge is now the `## Log` of an accepted record.
- Why it matters: A body edit shaped like a Log line counts as a change.
- Suggested response: Fixed. The no-newline wording is PR-029.
- Corroborated by: security and reliability

### PR-027: The `redrawn` Log line gets a second definition in a core module

- Priority: MINOR
- Category: Boundary / Ownership Concern
- Status: fixed
- Evidence:
  - `research.md §R-014` items 1, 2 and 4: `REDRAWN_LINE` and `redraw_only`
    live in `_records.py` beside `_append_log`, `_paths` takes a `skip`
    callable, and a test checks that a line `_append_log` writes matches
  - `check_imports.baseline`: `_evidence.py` and `_record_gate.py` are in the
    evidence context, which already imports `wfctl.arch`, and `cli.py` is
    wiring, so no arrow is added
- Finding: One module spells the format, and core stays free of a context
  import.
- Why it matters: A change to the Log line's shape fails a test.
- Suggested response: Fixed.
- Corroborated by: architecture and boundaries

### PR-028: Two lines the revisions made untrue

- Priority: MINOR
- Category: Requirement / Plan Mismatch
- Status: open
- Evidence:
  - `research.md §R-010`, last bullet: "The reworded fix text from FR-011, the
    `no drawing` fix and the `_DRAWING_FIX` entries, prints only under `wfctl
    arch accept`. `accept_problems` and `validate` don't carry it"
  - `spec.md §FR-011` item 1, `plan.md §Technical Context` Constraints, and
    `contracts/cli.md §The reworded fix text`: the `no drawing` line is part of
    `accept_problems` and shows in the design gate's reason. The code agrees
    (`accept_blockers` appends the whole string, `accept_problems` returns it,
    `_evidence.py:1641` reads it, and the snapshot at lines 914-916 carries it)
  - `plan.md §Constitution Check`, the `contexts-are-packages` bullet:
    "`arch/__init__.py` exports nothing new"
  - `plan.md §Project Structure`: `arch/__init__.py  # exports redraw_only`,
    and `research.md §R-014` item 1: `redraw_only` is "exported from the
    `wfctl.arch` package"
- Finding: The analyze edit corrected three artifacts and left the same false
  claim in R-010, whose bullet also contradicts its own decision, which counts
  the `no drawing` change in the `accept_problems` dump. The revision for
  PR-027 added an export, and the Constitution Check still says there is none.
- Why it matters: Each is one wrong sentence beside a correct one, so an
  implementer reading only `research.md` would expect the design gate's reason
  and its snapshot to stay unchanged. T017 in `tasks.md` updates the snapshot,
  so nothing breaks if the tasks are followed.
- Suggested response: Rewrite R-010's last bullet to match FR-011, and say in
  the Constitution Check that `arch/__init__.py` exports `redraw_only`, which
  the evidence context and `cli.py` already import the package for.
- Corroborated by: requirements and traceability, architecture and boundaries

### PR-029: R-014's contract reads wrong for a deleted record and for the no-newline case

- Priority: MINOR
- Category: Missing Information
- Status: open
- Evidence:
  - `research.md §R-014` item 3: `record_change` returns the diff and "the
    file's current text", and None only with no trunk, a git failure, or no
    file at the merge base
  - `wfctl/_paths.py` `records_on_this_branch` lists `git status --porcelain`
    paths, which include a deleted record, and `_evidence._level_records`'s
    docstring names that case ("A record the branch deleted is listed by git
    and has no file"). `decided_on_this_branch` lists the same changed paths
  - `research.md §R-014` item 1, conditions 3 and 4: condition 3 requires
    every added line to match `REDRAWN_LINE`, and condition 4's exception
    re-adds the old last line unchanged, which doesn't match it
  - `quickstart.md §1 item 3`: "A Log whose last line had no newline still
    reads as a redraw"
- Finding: For a record deleted in the working tree there is no current text
  to read, and the contract doesn't say whether that is None or a crash in
  the design gate. Condition 3 read literally fails the no-newline case that
  condition 4 and the test say passes.
- Why it matters: Both answers are clear from intent: a deletion should keep
  the record, since condition 4 would refuse its removed lines anyway, and the
  re-added line is exempt from condition 3. The test pins the second, and
  nothing pins the first.
- Suggested response: Add "or when the working tree has no file at that path"
  to `record_change`'s None cases, with a deleted-record case in
  `test_paths_redraw.py`, and say in condition 3 that the line condition 4
  re-adds is exempt.
- Corroborated by: adversarial implementation

## Requirement-to-plan trace

| Requirement / criterion | Plan location | Review note |
| --- | --- | --- |
| FR-001 | research.md §R-009, data-model.md §Problem, contracts/cli.md §A drawing with a problem, §Doctor | covered |
| FR-002 | research.md §R-007, §R-008, data-model.md §Building it, §Paths | covered |
| FR-003 | data-model.md §Problem, research.md §R-001 | covered |
| FR-004 | data-model.md §Drawing `labels` | covered |
| FR-005 | plan.md §Summary, `validate` reads summary labels | covered |
| FR-006 | data-model.md `failure_fix`, contracts/cli.md | covered |
| FR-007 | data-model.md (no field reads it) | covered by omission |
| FR-008 | research.md §R-003 to §R-006, quickstart.md §1, §4 | covered |
| FR-009 | plan.md §Summary, data-model.md §Drawing, §State | covered |
| FR-010 | data-model.md §Paths, quickstart.md §1 item 5 | covered |
| FR-011 | plan.md §Technical Context, contracts/cli.md §The reworded fix text, plan.md §Project Structure, research.md §R-010 | covered; PR-028 |
| FR-012 | plan.md §Source Code `drawing-style.md`, §An accepted record's drawing | covered |
| FR-013 | plan.md §Skill prose that changes | covered |
| FR-014 | tests/test_drawing_style_links.py | covered |
| FR-015 | plan.md §Source Code templates | covered |
| FR-016 | plan.md §Source Code, quickstart.md §3 | covered |
| FR-017 | plan.md §Source Code `docs/reference.md` | covered |
| FR-018 | plan.md §Constitution Check | covered |
| FR-019 | plan.md §Source Code (`_paths.py`, `drawing-style.md` #761 pointers) | covered |
| FR-020 | research.md §R-011, data-model.md §Drawing fingerprint, quickstart.md §1 item 2 | covered |
| FR-021 | contracts/cli.md §Doctor, §wfctl doctor warnings, data-model.md §Reading it back | covered |
| FR-022 | research.md §R-012, contracts/cli.md §wfctl arch accept on an accepted record, quickstart.md §1 item 3 | covered |
| FR-023 | research.md §R-013, contracts/cli.md §The worktree guard, quickstart.md §1 item 3 | covered |
| FR-024 | research.md §R-013, plan.md §Project Structure `cli.py` | covered |
| FR-025 | research.md §R-001, quickstart.md §1 | covered |
| FR-026 | research.md §R-014, plan.md §A redraw on a branch, §Project Structure, quickstart.md §1 item 3 | covered; PR-029 |
| SC-001 | quickstart.md §3 | covered |
| SC-002 | research.md §R-010, quickstart.md §0, §2 | covered |
| SC-003 | quickstart.md §3 | covered |
| SC-004 | quickstart.md §1 item 1 | covered |
| SC-005 | quickstart.md §1 item 1, §4 | covered |
| SC-006 | quickstart.md §5 grep | covered |
| SC-007 | quickstart.md §1 item 2, §6 | covered |
| SC-008 | quickstart.md §1 item 3, §6 | covered |

## Assumptions challenged

- The `no drawing` line reaches the design gate's reason and not doctor
  (`spec.md §FR-011`, `plan.md §Technical Context`). Verified in the code, as
  the review scope says. The only exact-string assertion on the old text is
  the snapshot's two lines, and every other test matches the substring `no
  drawing`, which the new wording keeps.
- `decided_on_this_branch` fails closed (`research.md §R-014` item 5). Holds:
  it returns `touched_on_this_branch`'s None and False unchanged, and a path
  under the arch root that isn't a record `skip` drops, such as a level-3
  record under `design/` in `_observe`'s call or an untracked directory,
  keeps the answer true.
- `fact_architecture_accepted` keeps calling `touched_on_this_branch` and then
  reads `branch_records`. With `skip`, a redraw-only branch reads `n/a` there
  rather than `met`. Either answer lets the branch through, since the redrawn
  record is accepted, so this is not a finding.
- An agent can still append a `redrawn` line by hand, and the SVG edit it
  covers sits in `drawings/`, outside every record reader. That stays inside
  the ceiling `research.md §R-011` names, a hand edit to an accepted record
  that the PR diff shows, so it is a stated limit rather than a finding.

## Reviewer disagreement

- None identified.

## Strengths worth preserving

- R-014 splits the check into a pure function over a diff and a record, which
  `test_redraw_only.py` exercises without git, and a git side in `_paths`,
  which `test_paths_redraw.py` runs on a real repo. Each of the four conditions
  has a test that breaks it alone.
- Every case `record_change` can't answer keeps the record, and the record
  gate's git errors refuse, so the exclusion widens no gate on an error.
- The skip is passed in as a callable, which keeps `_paths` core and adds no
  arrow to the Context Map.
- The FR-011 correction names the snapshot as its evidence, so the claim
  points at a file a reader can check.

## Source freshness

This review describes only the content identities listed under
`## Reviewed inputs`. When `spec.md`, `plan.md`, a binding design record, or a
material planning artifact changes, this report no longer describes the current
plan, and a new review is needed before it counts as current evidence.
