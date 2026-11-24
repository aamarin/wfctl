# Plan Review Report

Review state: completed
Review type: re-review

## Reviewed inputs

| Artifact | Content identity | Role |
| --- | --- | --- |
| plan.md | e17289460a2d797159dfc71f75e196903f5b3395 | technical strategy |
| plan-review.plan.md | 8ffe7b6e59a8a28fbfc11f497313aa5b6ea1aa7c | base (plan copy from the earlier review) |
| spec.md | 142d57fc93d21634f201c46c53c6e2febdc48603 | requirements |
| .specify/memory/constitution.md | absent | constitution |
| design.md | 99b65ad42a7b3b837289fc2043fb3a052489c6a7 | design-record index |
| docs/architecture/design/settings-changes-ask-once.md | d173f026d1ec31f08a3d53087409d05595462c09 | design record (level 3, proposed) |
| docs/architecture/settings-edit-asks-first.md | e371b77d5b7f307165a334c632591ec6e03e95d5 | design record (level 2, accepted) |
| docs/architecture/install-modes.md | 8809f9dc46c01804c89054ef7dab32b677e5bb34 | design record (accepted, named by FR-015) |
| docs/architecture/auto-approve-grant-asks-first.md | 6c86610f95ced25f9bdf60108f6a9b10be1597bf | design record (accepted, named by FR-015) |
| research.md | a08cc0d8af4bc915199158f93b28464f7e3779b9 | planning evidence |
| data-model.md | 546adcd72b51cdab7cb53d9941a41618b3dfc3af | planning artifact |
| contracts/install-question.md | c967566aab46491f5efcc34ee849cd6e0ef848f6 | planning artifact |
| quickstart.md | e2c6cbb97f19ee3480d92a7df52172dfaf54abc6 | planning artifact |
| scans/clarify.md | 535e933bb52c5cd3afebebb33855a848a26fb992 | clarify scan |

## Review scope

- Re-review: the earlier report and the plan copy both exist, and the copy's
  identity (`8ffe7b6e…`) equals the earlier report's `plan.md` row.
- Changed since the earlier review: `plan.md` (diffed against the copy),
  `data-model.md`, and `contracts/install-question.md` (identities changed, and
  named by the invoking command). All three were re-read in full, and the whole
  of `plan.md` was reviewed against the data model and the contract. Every
  other input row matches its file now.
- The plan diff adds: `read_bytes` and `parsed` to the `_SettingsCopy` sketch;
  the `_rule_removed` helper and its four conditions in `§The passes edit the
  copy`; the change list for a `created` file and the warning for every
  unsaved outcome in `§The save step`; the dropped `added` filter in
  `§Doctor`; tests 12 (widened) and 14; and the three summary-block tests named
  in the rewrite paragraph.
- Lenses: requirements and traceability, architecture and boundaries,
  adversarial implementation and verification
- Conditional lenses: security and reliability applied, for the same reasons
  as the earlier reviews. The feature is a security control over a file that
  sets the agent's own permissions, its inputs include a hand-editable and
  committable manifest, and it holds a user-owned file in memory across an
  interactive prompt.
- Existing code inspected: `wfctl/cli.py` (`_read_settings`,
  `_permission_drift`, `_merge_permissions`, the drift call in
  `install_skills_cmd`, `_check_managed_permissions`),
  `tests/test_install_hook_merge.py` (the three assertions on the summary
  block, and the fresh-install test that holds the first)
- Reviewers: the four lenses above, run in sequence by one agent
- Deterministic checks: all required artifacts present; no
  `[NEEDS CLARIFICATION` marker, TODO, or placeholder in spec.md, plan.md, the
  data model, or the contract

## Summary

BLOCKER: 0
MAJOR: 0
MINOR: 2
Fixed since the earlier review: 14 of 14

No BLOCKER findings identified in this review. All four findings the earlier
review left open are fixed. The `_rule_removed` helper now matches
`_permission_drift`'s refusal for a missing file, a zero-byte file, and a
receipt with `added` false, and doctor reports each of those. The two new
MINOR findings are a leftover sentence in `§The save step` that still names
only two outcomes for the warning, and the helper's "file existed" condition,
which counts a dangling symlink where `_permission_drift` today does not.

## Findings

### PR-001: A zero-byte settings file reads as unparseable, but the spec says install asks

- Priority: MAJOR
- Category: Requirement / Plan Mismatch
- Status: fixed
- Evidence:
  - `plan.md §The settings copy`: a file holding zero bytes or only whitespace
    is read as `{}` by `_load_settings`, and `_read_settings` stays unchanged
  - `plan.md §Tests` items 9 and 14
- Finding: Fixed in the earlier revision, and still holds.

### PR-002: Interrupting the question strands the copied skills without a manifest record

- Priority: MAJOR
- Category: Risk / Failure Mode
- Status: fixed
- Evidence:
  - `plan.md §The save step` item 4; `data-model.md §Save outcomes`, the
    `declined` row
  - `plan.md §Tests` item 10

### PR-003: The save overwrites any edit made to the file while the question waits

- Priority: MAJOR
- Category: Assumption Challenge
- Status: fixed
- Evidence:
  - `plan.md §The save step` item 5; `data-model.md §Settings copy`, the
    `read_bytes` row
  - `plan.md §Tests` item 11

### PR-004: Doctor's pending list would include a rule the user removed, which install refuses to restore

- Priority: MAJOR
- Category: Missing Information
- Status: fixed
- Evidence:
  - `plan.md §The passes edit the copy`: the skip uses `_rule_removed`
  - `plan.md §Doctor`: the rule is absent from the pending list, and
    `_check_managed_permissions` reports it
  - `plan.md §Tests` item 12

### PR-005: The contract's sample question contradicts its own rule for hook lines

- Priority: MINOR
- Category: Requirement / Plan Mismatch
- Status: fixed
- Evidence:
  - `contracts/install-question.md §At a terminal`: the hook's `why` line is
    `_HOOK_GONE[_WORKTREE_GUARD]` with "is gone — " trimmed

### PR-006: The existing merge summary and the `--yes` help text aren't addressed

- Priority: MINOR
- Category: Missing Information
- Status: fixed
- Evidence:
  - `plan.md §The save step`: the summary block is removed and the change list
    replaces it
  - `plan.md §Docs and skills`: the `--yes` help text is updated

### PR-007: A structural error in one pass is not placed in the shared-copy model

- Priority: MINOR
- Category: Missing Information
- Status: fixed
- Evidence:
  - `plan.md §The passes edit the copy`: a `ValueError` from `merge_hook` or
    `merge_permission` is printed by that pass, and the question lists only
    the other passes' changes

### PR-008: Acceptance scenario 5 is read as two runs without saying so

- Priority: MINOR
- Category: Requirement / Plan Mismatch
- Status: fixed
- Evidence:
  - `plan.md §Tests` item 5

### PR-009: The question's entry text isn't required to be escaped

- Priority: MINOR
- Category: Risk / Failure Mode
- Status: fixed
- Evidence:
  - `plan.md §The save step` item 3; `plan.md §Tests` item 13

### PR-010: `install-modes.md` still says a missing managed hook exits 1

- Priority: MINOR
- Category: Architecture / Decision Conflict
- Status: fixed
- Evidence:
  - `plan.md §Doctor`: quotes the superseded sentence and names the amendment
    as a follow-up issue, as FR-015 leaves it

### PR-011: The receipted-rule skip is wider than the refusal it mirrors, so a shipped rule can be neither added, refused, nor reported

- Priority: MAJOR
- Category: Risk / Failure Mode
- Status: fixed
- Evidence:
  - `plan.md §The passes edit the copy`: `_rule_removed(copy, receipts, rule,
    kind)` is one helper that `_merge_permissions` and `_permission_drift`
    both call, and a rule counts as removed only when it has a receipt of any
    `added` value, the file existed, `_read_settings` parsed it, and the rule
    isn't in it
  - `wfctl/cli.py` `_permission_drift`: skips a path that doesn't exist and a
    file `_read_settings` returns `None` for, and doesn't read `added` to
    decide whether to stop. Conditions 1, 3, and 4 match it, and condition 2
    matches it for every path except a dangling symlink (PR-016)
  - `plan.md §Doctor`: `_check_managed_permissions` now calls `_rule_removed`
    and drops its `added` filter, so it warns about every rule drift refuses
    over. Today it reads `if not record.get("added", False) … continue`, which
    is the filter being removed
  - `plan.md §Tests` items 12 (with `added` true and false) and 14 (a fresh
    clone with a committed manifest, and a zero-byte file with receipts)
- Finding: Fixed. The three cases the earlier review named now each land
  somewhere. A missing file under a committed manifest isn't removed, so the
  passes add every rule and the file is created. A zero-byte file isn't
  removed, so its rules are pending, install asks, and doctor lists them. A
  deleted rule whose receipt has `added` false is refused by drift and now
  warned about by `_check_managed_permissions`, whose existing message
  already says "is gone" without claiming wfctl installed it.

### PR-012: `data-model.md` and the plan's dataclass weren't updated for the revision

- Priority: MINOR
- Category: Requirement / Plan Mismatch
- Status: fixed
- Evidence:
  - `plan.md §The settings copy`: the `_SettingsCopy` sketch carries
    `read_bytes` and `parsed`
  - `data-model.md §Settings copy`: rows for both fields
  - `data-model.md §Save outcomes`: `declined` includes an interrupted prompt,
    and `failed` includes a file changed while the question was open

### PR-013: A `failed` outcome prints neither the count nor the command FR-008 asks for

- Priority: MINOR
- Category: Requirement / Plan Mismatch
- Status: fixed
- Evidence:
  - `plan.md §The save step`: every file that ends `declined`, `skipped`, or
    `failed` gets the `left unchanged` warning, a `failed` file prints its
    reason line first, and install exits 0 if nothing else failed
  - `contracts/install-question.md §At a terminal`: the changed-file line's
    text, followed by the warning
- Finding: Fixed. A stale sentence that still names two outcomes is raised
  separately as PR-015.

### PR-014: A created file loses the only explanation of what wfctl put in it

- Priority: MINOR
- Category: Risk / Failure Mode
- Status: fixed
- Evidence:
  - `plan.md §The save step`: a `created` file prints the change list,
    followed by `✓ <path> created (N changes)`
  - `contracts/install-question.md §At a terminal`: the same, with no
    `Apply them?` line
  - `plan.md §Tests`, the closing paragraph: names the three tests near lines
    927, 1446, and 1518. The one at 927 is
    `test_a_fresh_install_never_trips_the_refusal`, a created file, so the
    rewrite covers the created change list

### PR-015: `§The save step` still says the warning prints for `declined` and `skipped` only

- Priority: MINOR
- Category: Requirement / Plan Mismatch
- Status: open
- Evidence:
  - `plan.md §The save step`, the new paragraph: "Every file that ends
    `declined`, `skipped`, or `failed` gets the contract's `left unchanged`
    warning"
  - `plan.md §The save step`, three paragraphs later: "For `declined` and
    `skipped`, install prints one warning per file:", followed by the warning
    block
  - The first is in the save step's description, and the second says
    "install prints"
- Finding: The revision added the three-outcome rule and left the older
  two-outcome sentence in place, and the two name different callers. An
  implementer can read the warning as printed by `_save_settings` for all
  three, by install for two, or by both.
- Why it matters: A `failed` file gets no warning, or a `declined` file gets
  two. Tests written from the contract would catch the first and not the
  second.
- Suggested response: Drop the older sentence or make it name all three
  outcomes, and say which function prints the warning. The warning's text,
  "N changes need your yes", also reads oddly after a yes that ended
  `failed`; consider whether the contract wants a variant for that case.
- Corroborated by: deterministic checks, requirements and traceability

### PR-016: `_rule_removed`'s "file existed" counts a dangling symlink, where `_permission_drift` does not

- Priority: MINOR
- Category: Assumption Challenge
- Status: open
- Evidence:
  - `plan.md §The settings copy`: `existed` uses `exists() or is_symlink()`
  - `plan.md §The passes edit the copy`, condition 2: "The file existed when
    `_load_settings` read it"
  - `wfctl/cli.py` `_permission_drift`: `if not path.exists(): continue`, and
    `Path.exists()` is false for a dangling symlink
  - `wfctl/cli.py` `_read_settings`: returns `({}, None)` when the path
    doesn't exist, so a dangling link reads as parsed `{}`
- Finding: The plan says `_rule_removed` is "the same test `_permission_drift`
  uses", but for a settings path that is a symlink to a missing target with
  receipts on record, condition 2 holds where drift's test does not. All four
  conditions then hold, so drift starts refusing every install there, and
  doctor warns that each rule is gone, where today install proceeds.
- Why it matters: It's a narrow case, but it's the shape of a settings file
  linked to a shared location that isn't there yet, which is close to the
  fresh-clone case the plan means to keep adding rules. Two implementers would
  pick different tests for condition 2.
- Suggested response: Say whether condition 2 is `existed` or `path.exists()`.
  If it's `existed`, name the behavior change. If it's `path.exists()`, say
  so in the condition.
- Corroborated by: adversarial implementation and verification, security and
  reliability

## Requirement-to-plan trace

| Requirement / criterion | Plan location | Review note |
| --- | --- | --- |
| FR-001 | plan.md §The save step | covered |
| FR-002 | plan.md §The save step ("`--yes` is never passed in") | covered |
| FR-003 | plan.md §The save step; design record | covered |
| FR-004 | plan.md §The passes edit the copy; contract | covered |
| FR-005 | plan.md §The save step (`default=False`) | covered |
| FR-006 | plan.md §The save step item 2; §The passes edit the copy | covered |
| FR-007 | plan.md §The save step; data-model.md §Save outcomes | covered |
| FR-008 | plan.md §The save step warning; contract | covered; PR-015 |
| FR-009 | plan.md §The save step (runs after copies, item 4) | covered |
| FR-010 | plan.md §Doctor | covered |
| FR-011 | plan.md §Doctor | covered |
| FR-012 | plan.md §The save step, uninstall paragraph | covered |
| FR-013 | plan.md §Tests item 6; contract prefix test | covered |
| FR-014 | plan.md §Docs and skills (`changes/859.fix.md`) | covered |
| FR-015 | plan.md §Doctor (follow-up issue, no record edited) | covered |
| SC-001 | plan.md §Tests item 1 | covered |
| SC-002 | plan.md §Tests item 2 | covered |
| SC-003 | plan.md §Tests item 3 | covered |
| SC-004 | plan.md §Tests items 7, 12, and 14 | covered |
| Edge: unparseable file | plan.md §The passes edit the copy; §Tests item 8 | covered |
| Edge: save fails | plan.md §The save step item 7 and the warning paragraph | covered; PR-015 |
| Edge: symlink | plan.md §The passes edit the copy items 3 and 4 | covered; PR-016 |
| Edge: decline then rerun | plan.md §The save step (prior receipts kept) | covered |
| Edge: empty file | plan.md §The settings copy; §Tests items 9 and 14 | covered |
| US1 scenario 5 | plan.md §Tests item 5 | covered |
| US3 scenario 1 | plan.md §The save step item 2; §Tests item 14 | covered |

## Assumptions challenged

- No other process writes the settings file while install holds its copy.
  Narrowed by the byte comparison before a save, as in the earlier review.
- `_permission_drift` can call a helper that takes a copy. Today it reads each
  file itself from `(repo_root, agent, manifest)` and runs before the skills
  are copied. The plan doesn't say whether drift builds its own copies or
  install builds the copies earlier and hands them on. Either works, and
  neither changes behavior, so this isn't raised as a finding.
- Standard input is not a terminal for the worktree creation hook. Unchanged
  from the earlier reviews, and not raised as a finding.

## Reviewer disagreement

- None identified.

## Strengths worth preserving

- One `_rule_removed` helper now decides removal for install's refusal,
  install's passes, and both doctor checks, so the four can't drift apart
  again.
- `plan.md §Doctor` runs the same passes install runs, so doctor's list and
  install's question come from one computation.
- `plan.md §The save step` keeps `--yes` out of the save step's signature, so
  FR-002 is enforced by what the function can receive.
- Each fix arrived with its own test, including test 14 for the fresh-clone
  case the earlier review found.

## Source freshness

This review describes only the content identities listed under
`## Reviewed inputs`. When `spec.md`, `plan.md`, a binding design record, or a
material planning artifact changes, this report no longer describes the current
plan, and a new review is needed before it counts as current evidence.
