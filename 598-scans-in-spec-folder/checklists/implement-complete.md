Implementation complete: 2026-11-11

## Tasks at completion

~~~~markdown
---
description: 'Tasks for scan files in the spec folder (#598)'
---

# Tasks: Scan files in the spec folder

**Input**: `plan.md`, `spec.md`, and `design.md` in this folder.
**Prerequisites**: plan review satisfied, 0 BLOCKER open.

One PR. Every task is verified by the test named beside it or by the
definition-of-done commands in Phase 6.

## Phase 1: Setup

- [x] T001 Add `spec_scan(spec_dir, step)` to `wfctl/_paths.py`, and update the `SCANS_DIR` comment to say pipeline scans live in the spec folder while the arch-root subtree keeps older and evaluation scans. Verify: `tests/test_scan_reader.py::test_the_scan_path_is_under_the_spec_folder`.
- [x] T002 Add `write_scan(feature, step)` to `tests/conftest.py`. Have `write_plan_review` write the plan-review scan, and `stage_upstream_of` write the clarify scan with the spec and the analyze scan with the analyze artifact (PR-006). Verify: the existing suite.

## Phase 2: US2 and US3, the step readers (P1)

- [x] T003 [US2] Add `SCAN_MISSING`, `SCAN_NO_VERDICT`, `SCAN_NO_ROWS`, `scan_reason(spec_dir, step)`, and `_scan_hold(...)` to `wfctl/_evidence.py`. The held reading puts the text in `display` with `reason` None. Verify: T006.
- [x] T004 [US2] Call `_scan_hold` from `clarify` (later artifact `plan.md`), `analyze` (`delivery.md`), and both `done` exits of `plan_review` (`tasks.md`). Verify: T006 and T007.
- [x] T005 [US2] Fix every test that stages a done clarify, analyze, or plan review by hand without a scan: the direct `CLEAN_SPEC` writes and the files that write `analysis-report.md` (PR-011). Verify: `uv run pytest -q`.
- [x] T006 [P] [US2] New `tests/test_scan_reader.py`: missing, no verdict, no coverage rows, a valid file, a file with only sign-off sections, an `unsatisfied` verdict that still reads done (FR-008), and an analyze file whose only status row sits beside a measurement row, for each of the three steps. Verify: the test file.
- [x] T007 [P] [US2] In `tests/test_scan_reader.py`, a held clarify routes to `/speckit.clarify` with `auto` true under auto-approve, and an older feature reads done with the warning and its fix line (US3).

### Verification

`uv run pytest -q tests/test_scan_reader.py`

## Phase 3: US4, the plan sign-off (P2)

- [x] T008 [US4] `wfctl/_plan_review.py`: `append_sign_off` takes `issue`; heading `# Plan review scan` when it is `unknown`. Add `sign_off_reasons(agent_dir, branch)`. Verify: T010.
- [x] T009 [US4] `wfctl/cli.py` `step sign-off`: write to `spec_scan(spec_dir, "plan-review")`, drop the branch check, its undo, the commit line, and the no-issue refusal. `_exception_findings`: report each sign-off reason the body leaves out. Verify: T010.
- [x] T010 [US4] Update `tests/test_plan_review_signoff.py` for the new path and output, replace the out-of-tree and ignored-file refusal tests with one that writes into a spec folder outside the repo, and add a `check-body` test for a missing sign-off reason.

### Verification

`uv run pytest -q tests/test_plan_review_signoff.py`

## Phase 4: US1 and US5, the skill and wrappers (P1)

- [x] T011 [US1] Rewrite `wfctl/agents/skills/writing-a-scan-file/SKILL.md`: spec-folder destination, no commit or arch check, the `- Verdict:` line and coverage table the reader matches (FR-014), and an evaluation section keeping the arch-root path, the refusals, the commit, and the check (US5).
- [x] T012 [US1] `wfctl/agents/commands/speckit.clarify.md` and `speckit.analyze.md`: description, `allowed-tools`, `File` line, commit sentences, and the passages that say the PR reviewer reads the scan (PR-005).
- [x] T013 [US1] `wfctl/agents/commands/plan-review.md`: description, `allowed-tools`, `File` line, the commit sentence, and a scan-only mode for a pass held, or done with a warning, on one of the three scan texts (FR-013, PR-012).
- [x] T014 [US4] `wfctl/agents/skills/opening-a-change/SKILL.md`: copy each plan sign-off reason into the PR body (FR-012).
- [x] T015 [US1] Update `tests/test_scan_files.py`, `tests/test_plan_review_skill.py`, and any skill cross-reference test for the new text. Verify: `uv run pytest -q tests/test_scan_files.py tests/test_plan_review_skill.py tests/test_skill_cross_references.py`.

## Phase 5: Docs

- [x] T016 `AGENTS.md`: the `scans/` paragraph, and the sign-off reason beside `step none`'s PR body rule (FR-011).
- [x] T017 `changes/598.change.md`. Verify: `uv run wfctl verify`'s release-note check.

## Phase 6: Polish and verification

- [x] T018 `uv run pytest -q`, `uv run ruff check wfctl/ tests/`, `uv run mypy`, `python3 .github/scripts/check_imports.py`.
- [x] T019 `uv run wfctl install-skills`, then walk one scan through the new path: write it to the spec folder, check that nothing appears under `docs/architecture/scans/`, and check `wfctl status` reads it. Confirm the spec store keeps `scans/` with the rest of the folder (`git -C <spec root> ls-files` after `wfctl store specs`, or the store's own report) (SC-004). Then `uv run wfctl doctor` and `uv run wfctl check config`.

## Dependencies

Phase 1 before Phase 2. Phase 2 and Phase 3 share `_evidence.py` and `cli.py` only through `spec_scan`, so they can follow in either order. Phase 4 and 5 are text only. Phase 6 last.
~~~~
