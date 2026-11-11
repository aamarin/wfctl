# Plan review scan for #445

## Review 2026-11-10T03:16Z

- Verdict: satisfied
- Reviewed: plan.md 59e167be327efa4cc8d5a758f49e6da873a26809, spec.md 24fd5a118b4e6254334263d5b75686e85836731d, .specify/memory/constitution.md absent, design.md 99ccf609456037ab232d3bc1281aa8408ba69b5b, docs/architecture/design/issue-edit-one-field-per-call.md 5b088a79fe78a1626608f526d5e377d5f8ce4756, research.md 8a23fbc24591508a078a3cf0b586da0800b9a214, data-model.md 5273cc44470967a399cbf48cf8a1d5891310a7d4, quickstart.md 18321b477b921bcfd2bf3cd01363e57f5c6604c3, contracts/cli.md 70ddc5de2f1d504cd0190a9bf9dd65f28cce4010, contracts/tracker-verb.md 9201df87cdcf64104b2950158c2b698117a3727a
- Review type: full (no earlier report, so no plan copy to diff against)
- Open: BLOCKER 0 · MAJOR 1 · MINOR 5 · Fixed since the earlier review: 0
- Detail: /Users/andremarin/Development/wfctl-specs/445-issue-edit-verb/plan-review.md

### Coverage

| Check | Status |
| --- | --- |
| Deterministic checks | Outstanding (PR-002) |
| Requirements and traceability | Outstanding (PR-005) |
| Architecture and boundaries | Outstanding (PR-006) |
| Adversarial implementation and verification | Outstanding (PR-003, PR-004) |
| Security and reliability | Outstanding (PR-001) |

### Findings

- **PR-001, MAJOR, open.** `tracker-check` accepts an `edit` template that leaves out `{field}` or `{value}`, because `_check_section` in `wfctl/_tracker.py` reports only placeholders that aren't allowed. With a template such as `["jira","edit","{id}","--summary","{value}"]`, a two-field edit writes the body over the title, and wfctl still reports and records both writes as successful. It stands because `plan.md §Project Structure` plans no check for missing placeholders, against `spec.md §FR-002`, `spec.md §User Story 3` scenarios 1 and 2, and `contracts/tracker-verb.md`.
- **PR-002, MINOR, open.** `plan.md §Complexity Tracking` and `§Constitution Check` say one helper comes out of `dispatch`, while `research.md §3` describes a second one. It stands because the two artifacts disagree about how many helpers the change adds.
- **PR-003, MINOR, open.** No planned test sends an empty value such as `--title ""`. If the field check tests truthiness instead of `is None`, an empty value exits 2 with the "needs a field" error, which contradicts `spec.md §Edge Cases` and `contracts/cli.md`. It stands because `plan.md §Project Structure` lists no such test.
- **PR-004, MINOR, open.** `plan.md §Constitution Check` says the existing scaffold test covers the new verb row. That test, `tests/test_tracker.py::test_scaffold_skill_documents_every_verb_the_contract_allows`, only checks that `` `edit` `` appears somewhere in the skill, so it doesn't check the placeholders or the script note `spec.md §FR-011` requires.
- **PR-005, MINOR, open.** The plan doesn't list two docs that go stale once `edit` ships: the verb list and recorded-writes list in `docs/reference.md § Issue trackers`, and the Safety section of `AGENTS.md`.
- **PR-006, MINOR, open.** `plan.md §Summary` builds on `docs/architecture/design/issue-edit-one-field-per-call.md` without saying the record is still `status: proposed`.

## Review 2026-11-10T17:47Z

- Verdict: satisfied
- Reviewed: plan.md a4d092957e4cdfddc1c51ea3261cc5d53e6fcf30, spec.md 035adf2d6a5940794e05e63c544645b121d64c88, .specify/memory/constitution.md absent, design.md e744aedcd3f7ec78a5e51232521e8339d529138c, docs/architecture/design/issue-edit-one-field-per-call.md b5fabc9a07e7c99deebabb74001a8bd3958e33bd, research.md 63e88d8acc812ec6cb9fac944342903b7d6591f0, data-model.md 5273cc44470967a399cbf48cf8a1d5891310a7d4, quickstart.md 18321b477b921bcfd2bf3cd01363e57f5c6604c3, contracts/cli.md b4bd7502471d2fd55cd46634c8a3fd46dd7815ca, contracts/tracker-verb.md 9201df87cdcf64104b2950158c2b698117a3727a, plan-review.plan.md 59e167be327efa4cc8d5a758f49e6da873a26809 (base)
- Review type: re-review, with spec.md, design.md, research.md, contracts/cli.md, and the design record re-read in full because they changed since the earlier review
- Open: BLOCKER 0 · MAJOR 1 · MINOR 6 · Fixed since the earlier review: 1
- Detail: /Users/andremarin/Development/wfctl-specs/445-issue-edit-verb/plan-review.md

### Coverage

| Check | Status |
| --- | --- |
| Deterministic checks | Resolved (PR-002 fixed) |
| Requirements and traceability | Outstanding (PR-005, PR-007) |
| Architecture and boundaries | Outstanding (PR-006, PR-008) |
| Adversarial implementation and verification | Outstanding (PR-003, PR-004) |
| Security and reliability | Outstanding (PR-001) |

### Findings

- **PR-001, MAJOR, open.** `spec.md §FR-002` now requires `tracker-check` to report an `edit` template that leaves out `{id}`, `{field}`, or `{value}`, but `plan.md §Project Structure` still plans only "ALLOWED gains edit". It stands because `ALLOWED` lists the placeholders a verb may use, not the ones it must use, so the plan doesn't say where the new rule lives. `contracts/tracker-verb.md`, `spec.md §User Story 3`, and `spec.md §Validation Strategy` also still describe only the unknown-placeholder case.
- **PR-002, MINOR, fixed.** Fixed by `plan.md` Constitution Check, Project Structure, and Complexity Tracking, which now name both helpers that come out of `dispatch`, matching `research.md §2` and `§3`.
- **PR-003, MINOR, open.** No planned test sends `--title ""` or `--body ""`, and `contracts/cli.md` has no row for an empty value. It stands because `spec.md §Edge Cases` says an empty value is sent as given, and nothing checks it.
- **PR-004, MINOR, open.** `plan.md §Constitution Check` still says the existing scaffold test covers the new row. It stands because that test only checks that `` `edit` `` appears in the skill, not the placeholders or the script note `spec.md §FR-011` requires.
- **PR-005, MINOR, open.** `docs/reference.md § Issue trackers` and the Safety section of `AGENTS.md` still leave out `edit`. It stands because `plan.md` lists no documentation file.
- **PR-006, MINOR, open.** The design record is still `status: proposed`. It stands because `plan.md §Summary` builds on it without saying so.
- **PR-007, MINOR, open.** The design record's Verification section still says a test names the body as "not changed", while its Decision section now says the body write failed. It stands because commit 6046fad updated only the Decision section, and the fix belongs in the design record.
- **PR-008, MINOR, open.** `design.md` MVP Scope item 2 puts the per-field calls in `cli.py`, and `plan.md §Structure Decision` puts them in `_tracker.py`. It stands because the plan doesn't say it overrides `design.md`, although `research.md §2` gives the reason.
