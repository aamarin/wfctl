# Specification Analysis Report: step-command drift check

**Date**: 2026-08-17
**Artifacts**: spec.md, plan.md, tasks.md, research.md, data-model.md, quickstart.md
**Mode**: read-only — no artifact was modified

## Findings

| ID | Category | Severity | Location(s) | Summary | Recommendation |
| --- | --- | --- | --- | --- | --- |
| C1 | Coverage | HIGH | spec.md FR-009, US3-AS3; tasks.md T003 | Step *order* preservation has no asserting task. T003 checks each step's command and flag, which is order-agnostic; nothing fails if the merged literal is reordered. Order is the pipeline sequence, so a silent reorder reroutes the whole workflow. | Extend T003 to assert the ordered list `[(n, *next_step_content(n)) for n in _STEP_NAMES]` equals the recorded baseline, rather than asserting per-step. |
| C2 | Coverage | MEDIUM | spec.md FR-007; tasks.md Phase 4 | "MUST NOT report shipped commands that no step names" is satisfied structurally — the comprehension iterates the step table, so the reverse direction cannot be reported — but no task states or verifies it. A later refactor to a set-difference could reverse it silently. | Add one assertion to T009 that the 15 non-step commands (`speckit.checklist`, `speckit.brief`, `speckit.orchestrate`, …) are absent from the failure output. |
| C3 | Coverage | MEDIUM | spec.md Validation Strategy L214; tasks.md T012 | Spec requires `wfctl status` **and `wfctl next`** to be unchanged; tasks check only `wfctl status`. `wfctl next` is the command that writes `next-step.md` and actually surfaces the drift to a session. | Extend T012 to capture and diff `wfctl next` output too, or drop `wfctl next` from the spec's validation list. |
| E1 | Underspecification | MEDIUM | tasks.md T011 | Verification is "by inspection of the failure output, then revert" — a manual, mutating check that leaves no artifact behind. The empty-directory edge case is then unguarded on every later commit. | Rewrite as an automated test passing an empty set to the comparison helper and asserting all eight entries come back unresolved. No filesystem mutation needed. |
| E2 | Risk | MEDIUM | tasks.md T010 | Renames a tracked file (`mv wfctl/agents/commands/speckit.plan.md …`) and relies on a manual `mv` back. An interrupted run leaves the repository broken and the bundle content hash wrong. | Use `tmp_path` with a copied command tree, or monkeypatch `_COMMANDS`, so the negative case never touches tracked files. |
| F1 | Inconsistency | MEDIUM | spec.md L216; plan.md, tasks.md, ci.yml L131 | Spec says `uv run mypy wfctl`; plan, tasks and CI all say `uv run mypy`. The narrower form checks a different file set than the gate that actually runs. | Change spec.md to `uv run mypy`, matching CI. |
| E3 | Underspecification | LOW | tasks.md T009; spec.md FR-003 | FR-003 (the report names each unresolved step and command) is an MVP requirement, but the task that builds the message is T014 in Phase 5. T009's text does not state that its assertion message must name the step. | State the message requirement in T009 so FR-003 holds at the Phase 4 MVP boundary, not only after Phase 5. |
| A1 | Duplication | LOW | spec.md FR-003, FR-004 | FR-003 ("name each step and the command that failed to resolve") is a subset of FR-004 ("show both the unresolved entries and the shipped set"). Two requirements govern one message. | Keep both — FR-003 is the MVP floor and FR-004 the P2 addition — but note the containment in FR-004 so neither is read as a separate feature. |
| F2 | Inconsistency | LOW | spec.md, data-model.md, quickstart.md | Terminology drift: "bundled command file", "shipped command", "the tree shipped with the tool" and "the bundle" all name one thing. `data-model.md` settles on "shipped command set"; the spec uses all four. | Normalize on "shipped command" across spec.md; keep "bundle" only where it names the `_bundle` module. |
| F3 | Inconsistency | LOW | spec.md L192 | SC-006 is placed between SC-002 and SC-003, and user stories run US1, US3, US2. Both orderings are deliberate (SC-006 groups with SC-002; US3 was added at clarify) but read as a mistake. | Move SC-006 after SC-005, or add a one-line note that ordering is thematic. |

No CRITICAL findings.

## Coverage Summary

| Requirement | Has Task? | Task IDs | Verification? | Notes |
| --- | --- | --- | --- | --- |
| FR-001 verify every step command ships | yes | T009 | automated | Core assertion |
| FR-002 runs in the suite, no install/network | yes | T009, T013, T018 | automated | Gates named |
| FR-003 report names step + command | partial | T010, T014 | automated | See E3 — message construction lands in Phase 5 |
| FR-004 show both sides, nominate nothing | yes | T014, T015 | automated | Backed by research.md R1 |
| FR-005 silent when they agree | yes | T009 | automated | "passes on the unmodified tree" |
| FR-006 read the real shipped tree | yes | T008 | automated | Probe-verified during plan |
| FR-007 never report non-step commands | structural | — | none | See C2 |
| FR-008 one definition per step | yes | T005 | automated | T003/T004 pin behaviour |
| FR-009 step order derived | yes | T005 | **none** | See C1 — implemented but not asserted |
| FR-010 unknown step yields empty | yes | T004 | automated | Guards "story complete" |
| SC-001 detected at commit time | yes | T009, T010 | automated | |
| SC-002 100% of 8 commands | yes | T009 | automated | |
| SC-003 reader can attribute | yes | T015 | automated | |
| SC-004 no measurable time, no network | n/a | — | structural | Excluded: no buildable work — the check does one glob |
| SC-005 zero false positives today | yes | T009 | automated | Verified 23 shipped / 0 unresolved |
| SC-006 two shapes made impossible | yes | T005 | automated | T003, T004 |

## Constitution Alignment

No `.specify/memory/constitution.md` exists. `plan.md` substitutes gates from
`.github/workflows/ci.yml` and `.github/pull_request_template.md` and records the
substitution in Complexity Tracking, which is what the template requires.
Informational, not a violation.

## Unmapped Tasks

| Task | Note |
| --- | --- |
| T017 (wheel check) | Maps to no FR/SC. It verifies an assumption — that the check holds for an installed wheel — rather than a requirement. Legitimate; the CI job it points at already exists. |
| T001, T002 (baseline) | Map to US3's verification rather than to a requirement. Consumed by T012. |

## Verification Gaps

1. **FR-009 / US3-AS3** — order preservation implemented, never asserted (C1, HIGH).
2. **FR-007** — holds by construction, guarded by nothing (C2).
3. **Empty-directory edge case** — T011 verifies by inspection and leaves no test (E1).
4. **`wfctl next`** — named in the spec's validation strategy, absent from tasks (C3).

All three user stories have an `Independent Test` and a `Verification` block, and
every implementation task carries a verification path in its text.

## Metrics

- Total requirements: 16 (10 FR + 6 SC); 15 buildable, SC-004 excluded
- Total tasks: 18
- Coverage: 14/15 buildable requirements have ≥1 task — **93%**
- Requirements implemented but unasserted: 1 (FR-009)
- Ambiguity count: 0 unresolved placeholders, 0 unquantified vague adjectives
- Duplication count: 1 (FR-003 ⊂ FR-004, deliberate)
- CRITICAL issues: 0
- HIGH issues: 1

## Next Actions

No CRITICAL issues — `/speckit.decompose` is not blocked.

Recommended before implementation, in order:

1. **C1 (HIGH)** — extend T003 to assert ordered equality. One line, and it closes
   the only requirement that is implemented but unverified.
2. **E2, E1 (MEDIUM)** — make T010 and T011 operate on a copied tree or a
   monkeypatched constant instead of mutating tracked files. Turns two manual
   checks into two permanent tests.
3. **F1, C3 (MEDIUM)** — reconcile the `mypy` invocation and decide whether
   `wfctl next` is in the validation set.

LOW findings (E3, A1, F2, F3) are wording and ordering; they change no behaviour
and can ride along with any later edit.

## Remediation Applied — 2026-08-17

Four findings were fixed after this report was written. The findings above are
left as recorded; this section states what changed.

| ID | Status | Change |
| --- | --- | --- |
| C1 | fixed | `tasks.md` T003 now asserts the **ordered** list `[(n, *next_step_content(n)) for n in _STEP_NAMES]` against the eight `data-model.md` rows, closing the reorder hole. `quickstart.md` carries the same instruction under "Watch for". |
| E1 | fixed | T012 (was T011) calls `_unresolved(set())` and asserts all eight entries come back unresolved. The by-inspection check is gone; the empty-set edge case is now guarded permanently. |
| E2 | fixed | T011 (was T010) calls `_unresolved` with a constructed set — real stems minus `speckit.plan` plus `plan`. No `mv` of tracked files, so no interrupted run can leave the repo broken or the bundle hash wrong. `quickstart.md` updated to match. |
| F1 | fixed | `spec.md` Validation Strategy now says `uv run mypy`, matching plan, tasks and CI, with a note on why the narrower form is wrong. |
| E3 | fixed incidentally | T010 now states that the assertion message must name the unresolved step and command, so FR-003 holds at the Phase 4 MVP boundary. |

**Structural consequence**: closing E1 and E2 required the comparison to become a
pure helper, `_unresolved(shipped: set[str]) -> dict[str, str]`, added as T009.
Passing the shipped names in rather than globbing inside is what lets both
negative cases run as ordinary tests. Phase 4 grew by one task and Phases 4-6
renumbered: T008-T014, T015-T017, T018-T019.

**Still open**: C2 (FR-007 guarded by nothing), C3 (`wfctl next` in the spec's
validation list but not in tasks), and the LOW findings A1, F2, F3. None blocks
`/speckit.decompose`.
