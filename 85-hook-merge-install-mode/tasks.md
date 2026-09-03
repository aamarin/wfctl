---
description: 'Task list for #85 — a merge install mode for hooks in a consumer-owned settings file'
---

# Tasks: A merge install mode for hooks in a consumer-owned settings file

**Input**: Design documents from `specs/85-hook-merge-install-mode/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/hook-command.md, quickstart.md

**Tests**: Every user story below is TDD — its Tests subtasks are written and
run to confirm they fail before the matching Implementation subtasks land.

**Organization**: Phase 3 (US1) is the MVP and the smallest coherent PR — a
consumer running `install-skills --agent claude` gets a working, self-contained
hook. Phase 4 (US2) and Phase 5 (US3) are each a reviewable follow-on slice.

**Revision note**: T008 and T025 were added after `/speckit.analyze` found two
verification gaps (FR-015 and SC-005 had implementing tasks but no test) —
`checklists/analysis-report.md` findings E1 and E2. Every task after T007 is
renumbered from the pre-analysis version.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: different files, no dependency on an incomplete task
- **[Story]**: US1 / US2 / US3, from spec.md

---

## Phase 1: Setup

- [X] T001 Confirm a clean starting point: `uv run pytest -q && uv run ruff check wfctl/ tests/ && uv run mypy wfctl/` — merge gate before any change lands

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: the pure JSON-merge module and the shared constants every story's
install/uninstall/doctor code path calls into. Adapted from variant C per
`research.md`'s decision — no `wfctl.*` import, no I/O, so it is testable as
dict literals.

**⚠️ CRITICAL**: No user story task may start until this phase's checkpoint passes.

- [X] T002 [P] Create `wfctl/_settings.py`: `MANAGED_PREFIX = "wfctl hook "`, `_is_managed`, `managed_command`, `merge_hook`, `remove_hooks` — pure functions over an already-parsed settings dict, per `data-model.md`'s Managed hook entry section; verify with T003
- [X] T003 Write `tests/test_settings_merge.py`: dict-literal round-trip suite — `merge_hook` on an empty file, on a file with foreign hooks in the same and a different event, on an already-current entry (no-op), on a stale entry (replace not duplicate), on two hand-duplicated managed entries (collapse to one); `remove_hooks` pruning group → event → `hooks` key upward, and leaving a foreign command in a shared group untouched (depends on T002); verify with `uv run pytest tests/test_settings_merge.py -q`
- [X] T004 [P] Add merge-mode constants to `wfctl/cli.py`: a `(path, event)` target list for `.claude/settings.json` / `UserPromptSubmit` under `claude` only (no embedded skill list, per `research.md`'s command-name decision; no entry for any other agent, per FR-015) and `HOOK_COMMAND = "wfctl hook user-prompt"`; verify with `uv run mypy wfctl/`
- [X] T005 Checkpoint — validate Foundational phase: `uv run pytest tests/test_settings_merge.py -q && uv run ruff check wfctl/_settings.py tests/test_settings_merge.py && uv run mypy wfctl/_settings.py` — merge gate

---

## Phase 3: User Story 1 - Install the hook without disturbing what's already there (Priority: P1) 🎯 MVP

**Goal**: `install-skills --agent claude` adds the managed hook entry and leaves
every other byte of `.claude/settings.json` alone, creating the file if absent
and failing loudly-but-locally on invalid JSON.

**Independent Test**: start from a settings file with the consumer's own
permissions and hooks, run install, diff the file with the wfctl entry
excluded — zero diff. Separately: no file at all → a valid one is created;
invalid JSON → that target fails alone, every other target still installs.

**Verification**:

- Automated: `tests/test_install_hook_merge.py`, `tests/test_skill_cross_references.py`
- Manual: `quickstart.md` — "Install into a clean repo", "Confirm the hook has something to say"
- Evidence: `.claude/settings.json` diff before/after install, `wfctl hook user-prompt` stdout

### Tests for User Story 1 ⚠️

> Write these first; confirm each fails for "not implemented" before Implementation.

- [X] T006 [P] [US1] Write `tests/test_install_hook_merge.py`: `install-skills --agent claude` against a settings file with foreign permissions/hooks preserves them byte-for-byte and adds one managed entry; against no file creates a valid one containing only the managed entry; against invalid JSON warns and leaves the target untouched while every other install target still completes (spec.md US1 scenarios 1-3)
- [X] T007 [P] [US1] Extend `tests/test_skill_cross_references.py`: a fixture skill directory with `digest.md` produces one bullet in `wfctl hook user-prompt`'s output; a fixture skill without one contributes nothing; zero digest-bearing skills → exit 0, no output (contracts/hook-command.md; does not depend on #111 merging — use a local fixture digest, not the real `conversation-response-shape` one)
- [X] T008 [P] [US1] Extend `tests/test_install_hook_merge.py`: `install-skills --agent codex` (and `--agent bob`) writes no `.claude/settings.json` and adds no `merged` manifest record — merge mode is claude-only (FR-015; analysis finding E1)

### Implementation for User Story 1

- [X] T009 [US1] Implement `_read_settings` / `_write_settings` / `_json_indent` in `wfctl/cli.py`: missing file → `({}, "", None)`; unparseable or non-object top level → a refusal, never a silent `{}`; write preserves the source's indent width and trailing newline (data-model.md; FR-002, FR-010); verify with the malformed-JSON and missing-file cases in T006
- [X] T010 [US1] Implement `_merge_hooks` in `wfctl/cli.py`, calling `_settings.merge_hook` per Foundational target, writing only when it reports a change, recording a `merged` list per agent layer sibling to `items` (data-model.md Merged-path record; FR-001, FR-003, FR-014) — depends on T002, T004, T009; verify with the foreign-entries-preserved case in T006 and the manifest-shape check in T008
- [X] T011 [US1] Wire `_merge_hooks` into `install_skills_cmd`: call after the existing copy loop, save the `merged` record into the manifest, print a merge confirmation naming the file (no gitignore entry added, per FR-013) and surface any parse problem as a warning that does not abort the rest of the install — depends on T010; verify with `uv run pytest tests/test_install_hook_merge.py -q` and `quickstart.md` "Install into a clean repo"
- [X] T012 [US1] Implement the `wfctl hook user-prompt` command in `wfctl/cli.py`: scan `.agents/skills/*/digest.md` in the repo (not the bundle), print per `contracts/hook-command.md`'s format, exit 0 in every case including "not in a repo" — depends on T004; verify with T007 and `quickstart.md` "Confirm the hook has something to say"
- [X] T013 [US1] Checkpoint — validate User Story 1: `uv run pytest tests/test_install_hook_merge.py tests/test_skill_cross_references.py -q && uv run ruff check wfctl/ tests/ && uv run mypy wfctl/`, plus a manual run of `quickstart.md`'s first two sections — merge gate

**Checkpoint**: User Story 1 is independently functional — a consumer can
install and the hook has real content whenever a digest exists.

---

## Phase 4: User Story 2 - Reinstalling keeps the hook current, never duplicated (Priority: P2)

**Goal**: repeated installs converge to exactly one managed entry per event,
never opening the file when nothing changed, and `wfctl doctor` reports when an
installed entry is missing or no longer matches what the current wfctl would
install.

**Independent Test**: install once, reinstall with nothing changed → file not
reopened; hand-edit the entry to something else, reinstall → replaced in place,
never duplicated; run `doctor` against a missing/behind/current entry → each
state reported correctly.

**Verification**:

- Automated: `tests/test_install_hook_merge.py` (reinstall + doctor cases)
- Manual: `quickstart.md` — "Reinstall is idempotent", "Doctor reports drift"
- Evidence: `git diff` showing no change on a no-op reinstall; `wfctl doctor` output naming the fix command

### Tests for User Story 2 ⚠️

- [X] T014 [P] [US2] Extend `tests/test_install_hook_merge.py`: a second `install-skills --agent claude` run with an already-current entry does not rewrite the file (assert mtime/content unchanged); a run against a hand-edited stale command replaces that one entry in place, never adds a second (spec.md US2 scenarios 1-2)
- [X] T015 [P] [US2] Extend `tests/test_install_hook_merge.py`: `wfctl doctor` reports "current" (silent), "missing" (no entry present), and "behind" (command present but not matching `HOOK_COMMAND`), each naming `wfctl install-skills --agent claude` as the fix (spec.md US2 scenario 3; design.md doctor behavior)

### Implementation for User Story 2

- [X] T016 [US2] Confirm `_merge_hooks`' write-only-on-change behavior is reachable through `install_skills_cmd` with no additional file touch when `merge_hook` reports no change — depends on T011; verify with the no-op-reinstall case in T014
- [X] T017 [US2] Implement `_check_managed_hooks` in `wfctl/cli.py`: for each `merged` manifest record, compare the file's actual command (via `_settings.managed_command`) against `HOOK_COMMAND`, reporting missing / behind / current, silent only when current — depends on T004, T011; verify with T015
- [X] T018 [US2] Wire `_check_managed_hooks` into `doctor_cmd` — depends on T017; verify with `uv run pytest tests/test_install_hook_merge.py -q -k doctor` and `quickstart.md` "Doctor reports drift"
- [X] T019 [US2] Checkpoint — validate User Story 2: `uv run pytest tests/test_install_hook_merge.py -q -k "reinstall or doctor" && uv run ruff check wfctl/ && uv run mypy wfctl/`, plus `quickstart.md`'s reinstall and doctor sections — merge gate

**Checkpoint**: User Stories 1 and 2 both work independently — install, and
staying current across reinstalls with visible drift reporting.

---

## Phase 5: User Story 3 - Uninstall removes only what wfctl owns (Priority: P3)

**Goal**: `uninstall-skills --agent claude` removes wfctl's managed entry and
nothing else — a hand-written hook sharing the same event group survives, and a
now-empty group is pruned only when it truly holds nothing else.

**Independent Test**: install the hook alongside a hand-written hook in the same
event group, uninstall, confirm wfctl's entry is gone, the hand-written one
remains, and the group is pruned only when it was wfctl's alone.

**Verification**:

- Automated: `tests/test_install_hook_merge.py` (uninstall cases)
- Manual: `quickstart.md` — "Uninstall leaves foreign hooks alone"
- Evidence: settings file diff showing only wfctl's entry removed

### Tests for User Story 3 ⚠️

- [X] T020 [P] [US3] Extend `tests/test_install_hook_merge.py`: uninstall with wfctl's entry alone in its group prunes the group; uninstall with a foreign command sharing the group removes only wfctl's entry and keeps the group; uninstall with no wfctl entry present does not open the file for writing (spec.md US3 scenarios 1-3)

### Implementation for User Story 3

- [X] T021 [US3] Implement `_unmerge_hooks` in `wfctl/cli.py` using `_settings.remove_hooks`, deleting the settings file only when the `merged` record's `created` flag is true and the result is empty, and skipping the write entirely when `remove_hooks` reports no change — matching T010's install-side write-only-on-change wording (data-model.md Merged-path record; FR-008; analysis finding E5) — depends on T002, T004; verify with T020
- [X] T022 [US3] Wire `_unmerge_hooks` into `uninstall_skills_cmd`: call before the manifest's agent layer is dropped, print an unmerge confirmation naming how many files changed — depends on T011, T021; verify with `uv run pytest tests/test_install_hook_merge.py -q -k uninstall` and `quickstart.md` "Uninstall leaves foreign hooks alone"
- [X] T023 [US3] Checkpoint — validate User Story 3: `uv run pytest tests/test_install_hook_merge.py -q -k uninstall && uv run ruff check wfctl/ && uv run mypy wfctl/`, plus `quickstart.md`'s uninstall section — merge gate

**Checkpoint**: All three user stories now work independently and together.

---

## Phase 6: Polish & Cross-Cutting Concerns

- [X] T024 [P] Run every section of `quickstart.md` end to end against a scratch consumer repo (not this repo) and confirm all six scenarios match their documented "Expect" — evidence: the diff/output pairs quickstart.md names
- [ ] T025 Manual: run a live Claude Code session against a repo with the hook installed (T011, T012 complete); confirm `wfctl hook user-prompt` fires on more than one `UserPromptSubmit` turn within that session, and that its stdout matches a standalone invocation — the decay-closing claim in SC-005 and spec.md's own Validation Strategy, not exercised by any single-invocation quickstart step (analysis finding E2); evidence: a transcript excerpt showing the digest present at two different turns
- [X] T026 Full-suite gate for the feature: `uv run pytest -q && uv run ruff check wfctl/ tests/ && uv run mypy wfctl/` — merge gate matching AGENTS.md's Definition of done

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: no dependencies
- **Foundational (Phase 2)**: depends on Setup — BLOCKS every user story
- **US1 (Phase 3)**: depends on Foundational only — the MVP slice
- **US2 (Phase 4)**: depends on Foundational; T016 additionally depends on US1's T011 (there is nothing to reinstall or find current before install exists)
- **US3 (Phase 5)**: depends on Foundational; T022 additionally depends on US1's T011 (nothing to uninstall before install exists)
- **Polish (Phase 6)**: depends on US1, US2, US3 all complete

### Within Each Story

Tests written and confirmed failing before their matching Implementation task.
Within US1: T009 (I/O helpers) before T010 (merge wiring) before T011 (CLI
wiring); T012 (hook command) is independent of T009-T011 and can run in
parallel with them. T008's assertion depends on T011 existing to be meaningful,
but is written alongside T006/T007 per the phase's TDD ordering.

### Parallel Opportunities

- T002 and T004 (Foundational)
- T006, T007, and T008 (US1 tests)
- T014 and T015 (US2 tests)
- T012 in parallel with T009/T010/T011 within US1 — different function, same file, no shared state
- US2 and US3 implementation work (T016-T018 vs T021-T022) can proceed in
  parallel once US1's T011 lands — they touch different command handlers
  (`doctor_cmd` vs `uninstall_skills_cmd`)

---

## Logical PR Boundaries

- **PR 1 — Foundational + US1** (T001-T013): the MVP. `_settings.py`, the merge
  wiring, and the hook command. Reviewable as one coherent capability: install
  now does something a consumer can observe end to end.
- **PR 2 — US2** (T014-T019): currency and `doctor` drift reporting. Depends on
  PR 1 merged.
- **PR 3 — US3** (T020-T023): uninstall safety. Depends on PR 1 merged;
  independent of PR 2, so could land before or after it.
- **PR 4 — Polish** (T024-T026): the full quickstart pass and the live-session
  check, gated on all three stories landing.

Do not treat this as final — `/speckit.decompose` makes the binding PR/issue
call via `speckit-delivery-plan`. This section is a starting hypothesis for it.

---

## Implementation Strategy

### MVP First

1. Phase 1 (Setup) → Phase 2 (Foundational) → Phase 3 (US1)
2. Stop, validate US1 independently against `quickstart.md`'s first two sections
3. That is a mergeable, demonstrable increment on its own

### Incremental Delivery

1. Foundational → US1 → demo (a consumer's hook now fires and re-anchors a real skill)
2. Add US2 → demo (drift no longer goes unnoticed)
3. Add US3 → demo (uninstall is safe next to hand-written hooks)
4. Polish

### Parallel Team Strategy

Once Foundational (T001-T005) is green, US2 and US3's Tests subtasks (T014,
T015, T020) can be written in parallel with US1 implementation — they exercise
behavior on top of US1 but the test *files* have no code dependency on it. Their
Implementation subtasks (T016-T018, T021-T022) do need US1's T011 merged first.
