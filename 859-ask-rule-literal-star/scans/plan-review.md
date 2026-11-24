# Plan review scan for #859

## Review 2026-11-23T21:12Z

- Verdict: satisfied
- Reviewed: plan.md b2f043e6a58e21d1319f4a0e99b9ee753c69d839, spec.md 142d57fc93d21634f201c46c53c6e2febdc48603, .specify/memory/constitution.md absent, design.md 99b65ad42a7b3b837289fc2043fb3a052489c6a7, docs/architecture/design/settings-changes-ask-once.md d173f026d1ec31f08a3d53087409d05595462c09, docs/architecture/settings-edit-asks-first.md e371b77d5b7f307165a334c632591ec6e03e95d5, docs/architecture/install-modes.md 8809f9dc46c01804c89054ef7dab32b677e5bb34, docs/architecture/auto-approve-grant-asks-first.md 6c86610f95ced25f9bdf60108f6a9b10be1597bf, research.md a08cc0d8af4bc915199158f93b28464f7e3779b9, data-model.md 049c6e9ca57352aeb869ac33f1a018fbe129852e, contracts/install-question.md 8adcc8febf4ba38f5063ec87ebc95355a5e0d32d, quickstart.md e2c6cbb97f19ee3480d92a7df52172dfaf54abc6, scans/clarify.md 535e933bb52c5cd3afebebb33855a848a26fb992
- Review type: full (no earlier review)
- Open: BLOCKER 0 · MAJOR 4 · MINOR 6 · Fixed since the earlier review: 0
- Detail: /Users/andremarin/Development/wfctl-specs/859-ask-rule-literal-star/plan-review.md

### Coverage

| Check | Status |
| --- | --- |
| Deterministic checks | Outstanding (PR-005) |
| Requirements and traceability | Outstanding (PR-001, PR-008) |
| Architecture and boundaries | Outstanding (PR-010) |
| Adversarial implementation and verification | Outstanding (PR-004, PR-006, PR-007) |
| Security and reliability | Outstanding (PR-002, PR-003, PR-009) |

### Findings

- **PR-001, MAJOR, open.** The spec says install asks about an existing empty
  settings file, but `_read_settings` treats a zero-byte file as unparseable, so
  nothing is asked and plan test 6 may leave FR-013 untested. Stands because the
  plan names no handling for the zero-byte case.
- **PR-002, MAJOR, open.** The question sits between the skill copies and the
  manifest write, and Ctrl-C or Ctrl-D at the prompt leaves copied skills
  unrecorded. Stands because the plan says nothing about an interrupted answer.
- **PR-003, MAJOR, open.** The design record assumes a few seconds between read
  and save, but the prompt stretches that to however long the user takes, and a
  yes overwrites any edit made meanwhile. Stands because the plan has no re-read
  or change check before the save.
- **PR-004, MAJOR, open.** A rule the user deleted would show as a `+` change
  whose install `_permission_drift` refuses, while `_check_managed_permissions`
  prints a different fix for the same rule. Stands because the plan says such a
  rule isn't pending without saying how the pass excludes it.
- **PR-005, MINOR, open.** Three samples of the hook description line disagree
  across the contract and the design record. Stands because no artifact was
  reconciled.
- **PR-006, MINOR, open.** The plan doesn't say what happens to the existing
  "Merged wfctl's managed entries…" block or the `--yes` help text. Stands
  because neither is named in the plan.
- **PR-007, MINOR, open.** A `ValueError` from one pass after others have edited
  the shared copy is unhandled in the plan. Stands because only the unparseable
  case is covered.
- **PR-008, MINOR, open.** Spec US1 scenario 5 has one install change both files,
  but `--agent` takes one value and plan test 5 silently runs two installs.
  Stands because the spec and plan disagree on the scenario's shape.
- **PR-009, MINOR, open.** Removed-entry text comes from editable manifest
  receipts, and nothing requires `escape()` on the question's lines. Stands
  because neither the plan nor the contract requires it.
- **PR-010, MINOR, open.** Accepted install-modes.md still says a missing
  managed hook exits 1, which the plan changes to a warning without naming the
  sentence it supersedes. Stands because FR-015 forbids editing install-modes.md
  and no other record says it.

## Review 2026-11-23T21:19Z

- Verdict: satisfied
- Reviewed: plan.md 8ffe7b6e59a8a28fbfc11f497313aa5b6ea1aa7c, plan-review.plan.md b2f043e6a58e21d1319f4a0e99b9ee753c69d839 (base), spec.md 142d57fc93d21634f201c46c53c6e2febdc48603, .specify/memory/constitution.md absent, design.md 99b65ad42a7b3b837289fc2043fb3a052489c6a7, docs/architecture/design/settings-changes-ask-once.md d173f026d1ec31f08a3d53087409d05595462c09, docs/architecture/settings-edit-asks-first.md e371b77d5b7f307165a334c632591ec6e03e95d5, docs/architecture/install-modes.md 8809f9dc46c01804c89054ef7dab32b677e5bb34, docs/architecture/auto-approve-grant-asks-first.md 6c86610f95ced25f9bdf60108f6a9b10be1597bf, research.md a08cc0d8af4bc915199158f93b28464f7e3779b9, data-model.md 049c6e9ca57352aeb869ac33f1a018fbe129852e, contracts/install-question.md 3e3a6ab305a22a8006bfd42ba187a3e89e99cd42, quickstart.md e2c6cbb97f19ee3480d92a7df52172dfaf54abc6, scans/clarify.md 535e933bb52c5cd3afebebb33855a848a26fb992
- Review type: re-review
- Open: BLOCKER 0 · MAJOR 1 · MINOR 3 · Fixed since the earlier review: 10
- Detail: /Users/andremarin/Development/wfctl-specs/859-ask-rule-literal-star/plan-review.md

### Coverage

| Check | Status |
| --- | --- |
| Deterministic checks | Outstanding (PR-012; PR-005 fixed) |
| Requirements and traceability | Outstanding (PR-013; PR-001, PR-008 fixed) |
| Architecture and boundaries | Resolved (PR-010 fixed) |
| Adversarial implementation and verification | Outstanding (PR-011, PR-014; PR-004, PR-006, PR-007 fixed) |
| Security and reliability | Resolved (PR-002, PR-003, PR-009 fixed) |

### Findings

- **PR-011, MAJOR, open.** The skip for a receipted rule the user removed is
  wider than `_permission_drift`, which exempts a missing or unparseable file.
  Stands because a committed manifest with no settings file would create the
  file without its receipted rules, a zero-byte file with receipts never gets
  them, and a deleted rule whose receipt has `added` false is refused by
  install but not reported by doctor.
- **PR-012, MINOR, open.** `data-model.md` and the plan's `_SettingsCopy` block
  don't show `read_bytes`, and the data model's `failed` and `declined` rows
  don't cover the changed-file and interrupted-prompt cases.
- **PR-013, MINOR, open.** FR-008 wants a warning for every unsaved file, but
  the plan prints it only for `declined` and `skipped`, and the contract has no
  text for the changed-file line test 11 asserts on.
- **PR-014, MINOR, open.** A `created` file is never asked about, so removing
  the summary block drops the only explanation of the `cd` deny rule, and three
  tests in `tests/test_install_hook_merge.py` that assert on it aren't in the
  rewrite list.
- **PR-001 to PR-010, fixed.** Fixed by the plan revision: empty file read as
  `{}`, interrupted prompt is `declined`, re-read before save, receipted-rule
  skip, contract sample trimmed, summary and `--yes` help named, `ValueError`
  placed, scenario 5 noted as two runs, `escape()` required, and the
  `install-modes.md` sentence cited with a follow-up.

## Review 2026-11-23T21:23Z

- Verdict: satisfied
- Reviewed: plan.md e17289460a2d797159dfc71f75e196903f5b3395, plan-review.plan.md 8ffe7b6e59a8a28fbfc11f497313aa5b6ea1aa7c (base), spec.md 142d57fc93d21634f201c46c53c6e2febdc48603, .specify/memory/constitution.md absent, design.md 99b65ad42a7b3b837289fc2043fb3a052489c6a7, docs/architecture/design/settings-changes-ask-once.md d173f026d1ec31f08a3d53087409d05595462c09, docs/architecture/settings-edit-asks-first.md e371b77d5b7f307165a334c632591ec6e03e95d5, docs/architecture/install-modes.md 8809f9dc46c01804c89054ef7dab32b677e5bb34, docs/architecture/auto-approve-grant-asks-first.md 6c86610f95ced25f9bdf60108f6a9b10be1597bf, research.md a08cc0d8af4bc915199158f93b28464f7e3779b9, data-model.md 546adcd72b51cdab7cb53d9941a41618b3dfc3af, contracts/install-question.md c967566aab46491f5efcc34ee849cd6e0ef848f6, quickstart.md e2c6cbb97f19ee3480d92a7df52172dfaf54abc6, scans/clarify.md 535e933bb52c5cd3afebebb33855a848a26fb992
- Review type: re-review
- Open: BLOCKER 0 · MAJOR 0 · MINOR 2 · Fixed since the earlier review: 4
- Detail: /Users/andremarin/Development/wfctl-specs/859-ask-rule-literal-star/plan-review.md

### Coverage

| Check | Status |
| --- | --- |
| Deterministic checks | Outstanding (PR-015; PR-012 fixed) |
| Requirements and traceability | Resolved (PR-013 fixed) |
| Architecture and boundaries | Clear |
| Adversarial implementation and verification | Outstanding (PR-016; PR-011, PR-014 fixed) |
| Security and reliability | Clear |

### Findings

- **PR-015, MINOR, open.** `plan.md §The save step` says every `declined`,
  `skipped`, or `failed` file gets the warning, and a leftover sentence later
  says only `declined` and `skipped` do. Stands because the plan wasn't revised
  again; tasks take the first sentence as the rule.
- **PR-016, MINOR, open.** `_rule_removed` checks `existed`, which counts a
  dangling symlink, where `_permission_drift` uses `path.exists()`, which
  doesn't. Stands because the plan wasn't revised again; tasks keep
  `path.exists()` so a dangling link behaves as today.
- **PR-011, MAJOR, fixed.** Fixed by `_rule_removed`, shared with
  `_permission_drift` and `_check_managed_permissions`.
- **PR-012, PR-013, PR-014, MINOR, fixed.** Fixed by the `read_bytes` and
  `parsed` fields, the warning for every unsaved file with its exit code and
  changed-file text, and the change list for a created file with the three
  summary-block tests named.
