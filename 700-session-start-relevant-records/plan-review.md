# Plan Review Report

Review state: completed
Review type: re-review

## Reviewed inputs

| Artifact | Content identity | Role |
| --- | --- | --- |
| plan.md | d8c99c1655cfe6e90483645538a3bc1fdfc2af97 | technical strategy |
| spec.md | c077f467747057965110676c8683f3a498b2b2d5 | requirements |
| .specify/memory/constitution.md | absent | constitution |
| design.md | a7a9ec68ad7890ef9da7535fea84f5111ab1d6d9 | design-record index |
| docs/architecture/design/700-one-function-selects-records.md | 08b26c306103575732857f0df2116d1391c929ed | design record (level 3) |
| docs/architecture/branch-contexts-select-records.md | 2fe22ce93c2ffbccbcdcfabc013513ff0ae57b7c | design record (level 2) |
| research.md | 069bf6d1d67d2fed893d61507795641a13bf412c | planning evidence |
| data-model.md | 6f597f7eedfc65ab33dd64444fdb2312b4b09d0e | planning artifact |
| contracts/cli.md | 80f33c8e162a31c6a9910823bb57e2f5ad40f984 | planning artifact |
| quickstart.md | 4138b0d463d511641ee5da386b56e92eb52ac0b4 | planning artifact |
| plan-review.plan.md | faee052b6c0af3d5e422f1b511fe0c4132a01929 | earlier plan copy (base) |

## Review scope

- Re-review: the earlier report exists, the plan copy exists, and the copy's
  identity equals the identity the earlier report recorded for `plan.md`
  (`faee052b6c0af3d5e422f1b511fe0c4132a01929`).
- Plan diff: `plan.md` adds `test_evidence.py` and a broader `test_cli_status.py`
  comment to the test list, and adds the line that drops
  `_session_report.py -> _arch.py` from `.github/scripts/check_imports.baseline`.
- Input check: comparing every other row of the earlier report with its file now
  found one change, the level-3 record
  `docs/architecture/design/700-one-function-selects-records.md`, which went from
  `2ac621e3b5e167e99803ad5bca8776f80850d851` to the identity above. The review
  re-read it in full and checked the whole of `plan.md` against it. `spec.md`,
  `design.md`, the level-2 record, and the four planning artifacts match their
  earlier identities. `tasks.md` is not an input of this method and was not read.
- Lenses: requirements and traceability, architecture and boundaries,
  adversarial implementation and verification
- Conditional lenses: security and reliability did not apply. The feature reads
  local files and crosses no trust boundary, and the earlier review recorded the
  one trust question under Assumptions challenged.
- Existing code inspected: `wfctl/_session_report.py` (`Readers`,
  `default_readers`, the two docstrings that count session keys) and
  `.github/scripts/check_imports.baseline`
- Reviewers: the three lenses above, run in sequence by one agent

## Summary

BLOCKER: 0
MAJOR: 0
MINOR: 1

No BLOCKER findings identified in this review. Three of the four earlier
findings are fixed: the level-3 record now matches the data model, the plan now
lists the baseline deletion, and the plan now lists a test that compares the real
reader with `arch context`. The one open finding is the unstated shape of the
`Readers` change.

## Findings

### PR-001: The level-3 record and the data model give `select` different inputs

- Priority: MINOR
- Category: Architecture / Decision Conflict
- Status: fixed
- Evidence: `docs/architecture/design/700-one-function-selects-records.md
  §Decision` now reads `_contexts.select(names, listed, accepted)`, takes the
  name list, the listed contexts, and the accepted records, and "reads no
  files". It puts the file reads in `_evidence.records_for_branch`. That matches
  `data-model.md §select(names, listed, accepted)` and `plan.md §Summary`.
- Fixed by: the level-3 record's Decision section.
- Corroborated by: architecture and boundaries

### PR-002: Replacing the accepted-count reader leaves a baseline line stale

- Priority: MINOR
- Category: Dependency / Feasibility
- Status: fixed
- Evidence: `plan.md §Source Code` now lists `.github/scripts/check_imports.baseline`
  with the note "drop `_session_report.py -> _arch.py`". The baseline still holds that line (line 59),
  and `wfctl/_session_report.py` still uses `_arch` only in the
  `accepted_records` reader (lines 183 and 198), so the deletion matches what the
  change leaves behind.
- Fixed by: `plan.md §Source Code`.
- Corroborated by: architecture and boundaries, adversarial implementation

### PR-003: The plan doesn't say whether `Readers.accepted_records` stays

- Priority: MINOR
- Category: Missing Information
- Status: open
- Evidence:
  - `plan.md §Source Code`: "`Readers.records`", with nothing on the existing
    field
  - `research.md`: a `records` reader returns the accepted count and the applying
    count
  - `wfctl/_session_report.py:179`: `accepted_records: Callable[[], int]`;
    `tests/test_session_report.py` builds `Readers` with it
  - `wfctl/_session_report.py:209` and `:321`: the docstrings say "ten session
    keys" and "`contracts/cli.md` lists ten", and the payload gains
    `applying_records`
  - `plan.md §Source Code` now drops the `_arch` baseline line, which only holds
    if `accepted_records` stops importing `_arch`, so the plan implies a
    replacement without saying so
- Finding: The plan names a new `records` field but doesn't say whether it
  replaces `accepted_records` or sits beside it, or what it returns when the set
  isn't narrowed.
- Why it matters: Two implementers would write different `Readers` fields and
  fixtures. Nothing user-visible depends on the choice, and the two docstrings
  that count the keys go stale either way.
- Suggested response: State that `records` replaces `accepted_records` and
  returns `(accepted, applying | None)`, or the alternative, and list the two
  docstrings among the edits.
- Corroborated by: adversarial implementation

### PR-004: No planned test exercises the real reader against `arch context`

- Priority: MINOR
- Category: Verification Gap
- Status: fixed
- Evidence: `plan.md §Source Code` now lists `test_evidence.py` for
  `records_for_branch()` and describes `test_cli_status.py` as "session JSON key
  set, arch context vs status --session --json". That test goes through
  `default_readers` and `records_for_branch`, which is the comparison the level-3
  record's Verification section asks for.
- Fixed by: `plan.md §Source Code`.
- Corroborated by: adversarial implementation and verification

## Requirement-to-plan trace

| Requirement / criterion | Plan location | Review note |
| --- | --- | --- |
| FR-001 | data-model.md §select, last row | covered |
| FR-002 | contracts/cli.md §Narrowed | covered, singular forms included |
| FR-003 | research.md §What counts as narrowed | covered |
| FR-004 | data-model.md §select, row 2; contracts/cli.md | covered |
| FR-005 | data-model.md §select, row 3 | covered |
| FR-006 | data-model.md §select, row 1 | covered |
| FR-007 | design.md §Level-3 consequences 3; plan.md §Source Code (cli.py) | covered |
| FR-008 | contracts/cli.md §status --session | covered |
| FR-009 | data-model.md §Session payload | covered |
| FR-010 | plan.md §Summary; plan.md §Source Code (test_cli_status.py) | covered; PR-004 fixed |
| FR-011 | plan.md §Source Code (start-session) | covered |
| FR-012 | plan.md §Source Code (architecture-decisions) | covered |
| SC-001 | quickstart.md step 1 | covered |
| SC-002 | data-model.md invariant | covered |
| SC-003 | data-model.md invariant | covered |
| SC-004 | plan.md §Summary; plan.md §Source Code (test_cli_status.py) | covered; PR-004 fixed |

## Assumptions challenged

- Both records the plan cites are still `proposed`. The spec assumes the level-2
  record is accepted before the PR opens. Not verifiable at this point.
- The agent writes the `Contexts` line that decides which records it reads. The
  design names this under Not Doing, so it is a known limit rather than a gap in
  the plan.

## Reviewer disagreement

- None identified.

## Strengths worth preserving

- The level-3 record and the data model now describe one `select` signature, so
  the record can go to the user as written.
- The plan lists the baseline deletion, and the deletion narrows the import
  check, so it needs no sign-off.
- The plan's comparison test goes through the real reader, which is where the
  guarantee that the session report matches `arch context` is decided.

## Source freshness

This review describes only the content identities listed under
`## Reviewed inputs`. When `spec.md`, `plan.md`, a binding design record, or a
material planning artifact changes, this report no longer describes the current
plan, and a new review is needed before it counts as current evidence.
