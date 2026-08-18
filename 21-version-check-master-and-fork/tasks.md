# Tasks: version check — default branch and fork

**Input**: Design documents from `specs/21-version-check-master-and-fork/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/

**Tests**: Required. This is branching logic in a health check that no consumer
can see behind — a wrong verdict is silent by nature. Every state in
`data-model.md` E3 gets a test, all offline, all under the existing
`real_version_check` marker so `tests/conftest.py`'s autouse stub steps aside.

**A note on parallelism**: this feature lives in one function in one file
(`wfctl/cli.py`), so genuine `[P]` opportunities are rare and are not invented
here. Test-writing tasks parallelize; implementation tasks in the same function
do not. Marking them otherwise would produce merge conflicts, not speed.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: US1, US2, US3 — maps to the user stories in spec.md
- Paths are repository-relative

---

## Phase 1: Setup

**Purpose**: Capture the pre-change behavior so the fix is provable, not asserted.

- [X] T001 Record baseline evidence: run `wfctl doctor` and `echo $?` on the current stale build and paste both into the PR description; this machine reports `✓ wfctl 0.14.0 — latest` at exit 0 while the branch tip is `271bb2c` (0.15.0, untagged). Verify by confirming the captured output contains `— latest` and the exit code is 0.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: The two readers every story depends on — local build identity, and
remote branch/tag state. No story can be implemented before both exist.

**⚠️ CRITICAL**: Blocks Phases 3, 4, and 5.

- [X] T002 Create `tests/test_doctor_version.py` with the `@pytest.mark.real_version_check` marker applied to every test and helpers that stub both `importlib.metadata` reads and `subprocess.run` for `git ls-remote`; verify with `pytest tests/test_doctor_version.py` collecting successfully and running offline.
- [X] T003 [P] Write failing tests for `_installed_build()` covering the E1 happy path — a VCS install returns `(url, commit)` — in `tests/test_doctor_version.py`; verify the tests fail with `AttributeError`/`ImportError` before implementation exists.
- [X] T004 Implement `_installed_build() -> tuple[str, str] | None` in `wfctl/cli.py` near `_WFCTL_REPO` (line ~1616), reading `direct_url.json` via `importlib.metadata.distribution("wfctl").read_text(...)`, per `data-model.md` E1 rules R-1 to R-4; verify with `pytest tests/test_doctor_version.py -k installed_build`.
- [X] T005 [P] Write failing tests for remote-state parsing — the `ref: refs/heads/<name>\tHEAD` symref line, the `HEAD` tip row, and `refs/tags/vX.Y.Z` rows from one `ls-remote` response — in `tests/test_doctor_version.py`; verify they fail before the parser exists.
- [X] T006 Extend the `ls-remote` invocation in `_check_wfctl_version` (`wfctl/cli.py:1636`) to `--symref --refs <url> HEAD 'refs/tags/v*'` and parse branch name, tip, and tags from the single response per `data-model.md` E2. **In the same task**, update the existing `_fake_ls_remote_tags` helper (`tests/test_install_skills.py:663`) to emit the symref line as well as tags — without it the two tests it feeds (`:679`, `:690`) keep passing while silently routing through the FR-009a warning path instead of the path they were written for. Verify with `pytest tests/test_doctor_version.py -k remote_state` and `pytest tests/test_install_skills.py -k check_wfctl_version`, confirming the latter two still assert the verdict and not a warning.
- [X] T007 Validate Phase 2 with `pytest && ruff check && mypy` — merge gate.

**Checkpoint**: Both readers exist and are typed. Stories can now proceed.

---

## Phase 3: User Story 1 — A branch build learns it is stale (Priority: P1) 🎯 MVP

**Goal**: A build behind the branch tip says so, names both commits, names the
skills consequence, and prints a remedy that works.

**Independent Test**: Install from a commit behind the tip, run `wfctl doctor`,
confirm the drift block appears and the exit code is 1.

**Verification**:

- Automated: `pytest tests/test_doctor_version.py -k "drift or at_tip or suppress"`
- Manual: `quickstart.md` "Verify the fix" against this machine's live stale build
- Evidence: doctor output moves from `✓ … — latest` to the drift block, and back to `✓` after the reinstall

- [X] T008 [P] [US1] Write failing tests for the three US1 states — drift found (block rendered, exit 1), commit at tip (`✓ wfctl X — latest` byte-identical to today, exit 0), and newer tag present (drift line suppressed, only the upgrade line, exit 1) — in `tests/test_doctor_version.py`, asserting the exact line shapes in `contracts/doctor-tool-freshness.md`. Include an explicit negative assertion for FR-008: no digit-plus-"commits" phrasing appears in the drift block. Verify all three fail first.
- [X] T009 [US1] Implement the drift comparison and block in `_check_wfctl_version` (`wfctl/cli.py`): compare `_installed_build()`'s commit against the resolved tip, render `⬆ build behind <branch> — <short> → <short>`, the `bundled skills are from this build too` line, and `reinstall: uv tool install --force <recorded-url>`, returning drift per `data-model.md` E3 R-9; verify with `pytest tests/test_doctor_version.py -k drift`.
- [X] T010 [US1] Implement release-verdict precedence so a newer tag suppresses the drift line (E3 R-8) and the `✓` string is `— latest` alone but `— latest release` when the drift block follows (E3 R-11), in `wfctl/cli.py`; verify with `pytest tests/test_doctor_version.py -k "suppress or at_tip"`.
- [X] T011 [US1] Validate Phase 3 with `pytest && ruff check && mypy` — merge gate.

**Checkpoint**: The defect from issue #21 is fixed and provable end to end.

---

## Phase 4: User Story 2 — Installs that cannot drift are not nagged (Priority: P2)

**Goal**: Pinned, editable, and index installs are silently skipped; fork
installs are compared against their own origin, with tags still upstream and
every printed remedy naming the fork.

**Independent Test**: Run the check against each install shape from
`quickstart.md`'s table and confirm the branch comparison runs only where it
should, against the right repository, and that no printed command names a
repository the user did not install from.

**Verification**:

- Automated: `pytest tests/test_doctor_version.py -k "skip or fork or remedy"`
- Manual: the install-shape table in `quickstart.md` (pinned, editable, index)
- Evidence: no drift line for the four skip shapes; a fork's upgrade *and* reinstall lines both name the fork

- [X] T012 [P] [US2] Write failing tests for the four skip shapes — no `direct_url.json`, `dir_info` (editable), `requested_revision` present (pin), and malformed JSON — each asserting no drift line and an unchanged exit code, in `tests/test_doctor_version.py`; verify they fail first. Fixtures must use real recorded payloads from `research.md` R2/R3/R5, not invented ones.
- [X] T013 [P] [US2] Write failing tests for fork targeting: a recorded URL differing from `_WFCTL_REPO` queries that URL for branch tip while tags come from `_WFCTL_REPO`, producing exactly two `ls-remote` invocations; and an upstream install produces exactly one (FR-009, SC-005); verify they fail first.
- [X] T014 [P] [US2] Write a failing test that **both** remedy lines follow the recorded origin (FR-012, US2 scenario 5) — a fork install with a newer upstream tag must print its own origin in the upgrade command, not `_WFCTL_REPO`; verify it fails against today's hardcoded `wfctl/cli.py:1647`.
- [X] T015 [US2] Implement query-target selection in `_check_wfctl_version` (`wfctl/cli.py`): branch tip from the recorded URL, tags always from `_WFCTL_REPO`, second call issued only when the two differ, per `data-model.md` E2 R-5/R-6; verify with `pytest tests/test_doctor_version.py -k fork`.
- [X] T016 [US2] Implement FR-012 in `wfctl/cli.py`: both the upgrade line (currently hardcoded to `_WFCTL_REPO` at line 1647) and the new reinstall line take the recorded origin URL, falling back to `_WFCTL_REPO` when no origin is recorded; verify with `pytest tests/test_doctor_version.py -k remedy`.
- [X] T017 [US2] Validate Phase 4 with `pytest && ruff check && mypy` — merge gate.

**Checkpoint**: No install shape receives a claim doctor cannot back up, and no remedy points at someone else's repository.

---

## Phase 5: User Story 3 — The check degrades quietly when it cannot run (Priority: P3)

**Goal**: Exactly one warning line per report, naming every comparison that
could not run. No silent omission, no second warning line.

**Independent Test**: Force each query to fail independently and confirm the
single-line contract holds in all three combinations.

**Verification**:

- Automated: `pytest tests/test_doctor_version.py -k warning`
- Manual: run `wfctl doctor` with networking disabled; expect one `⚠` line, exit 0
- Evidence: the three warning strings in `contracts/doctor-tool-freshness.md`

- [X] T018 [P] [US3] Write failing tests for the three partial-failure states — both queries fail, tags succeed and branch fails, branch succeeds and tags fail — asserting exactly one `⚠` line, its text naming what could not run, and exit 0 (FR-009a), in `tests/test_doctor_version.py`; verify they fail first.
- [X] T019 [US3] Implement failure tracking and single-warning composition in `_check_wfctl_version` (`wfctl/cli.py`), distinguishing "no tags" from "could not reach the tag source" per `data-model.md` E2 R-7 and E3 R-10; verify with `pytest tests/test_doctor_version.py -k warning`.
- [X] T020 [US3] Update `test_doctor_skills_verdict_survives_an_offline_release_check` (`tests/test_install_skills.py:638`), whose `assert "couldn't check latest" in result.output` T019 invalidates by changing that string. **Must land in this phase, before T021** — T019 turns it red and T021 runs the full suite. Keep the test in that file: it is a skills test that carries the marker only because it needs the release check live in order to kill the network. Verify with `pytest tests/test_install_skills.py -k offline_release_check`.
- [X] T021 [US3] Validate Phase 5 with `pytest && ruff check && mypy` — merge gate.

**Checkpoint**: All three stories independently functional, suite green.

---

## Phase 6: Polish & Cross-Cutting Concerns

- [X] T022 [P] Update `README.md` (~line 247) where doctor is described as comparing "installed version vs latest release tag", to describe both comparisons and show the drift block; verify by re-reading the section against `contracts/doctor-tool-freshness.md` line shapes.
- [X] T023 [P] Move the two pure unit tests of `_check_wfctl_version` — `test_check_wfctl_version_upgrade_available` (`tests/test_install_skills.py:679`) and `test_check_wfctl_version_latest` (`:690`) — plus both helpers they own, `_fake_ls_remote_tags` (`:663`, already updated by T006) and `_plain` (`:673`, whose only two call sites are these two tests), into `tests/test_doctor_version.py`. Pure move, no behavior change. Leave the test at `:638` where it is. Verify with `pytest -m real_version_check` collecting every previous case plus the new ones, and `pytest` green.
- [X] T024 Satisfy FR-013: convert `_check_wfctl_version`'s return from `int` to `bool` meaning "found drift", and update its fold at its call site in `doctor_cmd` (`wfctl/cli.py`, currently `exit_code = _check_wfctl_version()`) to OR into the exit code — the contract issue #41 assigns to this branch ("PR B converts it to `bool` as the last step of its own rewrite"). Do this last, on code the earlier tasks have already rewritten; verify with `pytest && mypy`, and confirm no other check's call site is touched — #41 scopes those to PR A explicitly.
- [ ] T025 **FR-005 gate** — run `quickstart.md`'s "Verify the fix" against the real HTTPS origin: `uv tool install --force git+https://github.com/aamarin/wfctl.git`, then confirm the recorded `commit_id` in the installed `.dist-info/direct_url.json` advanced to the branch tip and `wfctl doctor` returns to `✓ … — latest` at exit 0. If it did not advance, add `--reinstall` to the printed command in `wfctl/cli.py`, amend `research.md` R4, and re-run. Verify by diffing `direct_url.json` before and after.
- [ ] T026 Validate the whole feature with `pytest && ruff check && mypy`, plus one `wfctl doctor` run confirming the live drift block (SC-006) — merge gate.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (T001)**: no dependencies; capture before any code changes or the baseline is lost.
- **Foundational (T002-T007)**: blocks all stories.
- **US1 (T008-T011)**: depends on Phase 2. The MVP.
- **US2 (T012-T017)**: depends on Phase 2. Independent of US1 — the skip rules, fork targeting, and remedy URLs are testable whether or not the drift block exists, though the *observable* effect of a skip is best asserted alongside US1's rendering.
- **US3 (T018-T021)**: depends on Phase 2. Independent of US1 and US2. **T020 must precede T021** — T019 invalidates an assertion in `test_install_skills.py`, and T021 runs the full suite.
- **Polish (T022-T026)**: T022/T023 depend on nothing beyond Phase 5; T024 (FR-013) must come after all three stories, since it rewrites the returns they add; **T025 depends on all stories being merged**, since it runs against a real installed build.

### Cross-issue coordination

This branch is "PR B" in issue #41's plan, which coordinates five issues that
each touch `doctor`. Two constraints follow, neither of which originates in this
feature's own documents:

- **#41 assigns the exit-code contract's last step here** (T024, spec FR-013): `_check_wfctl_version` returns `bool`, OR'd into `doctor_cmd`'s exit code.
- **#41 forbids this branch from touching the other four checks.** PR A (#36, #31, #38) converts those; the two branches are deliberately kept ~12 lines apart in `cli.py` to avoid a signature conflict. If a task here appears to need an edit at `doctor_cmd`'s other check call sites, stop — that is PR A's scope.

Line numbers in #41 and #35 predate the #47/#49 merge: `_check_wfctl_version`
is now at `cli.py:1626` (was 1599) and `_WFCTL_REPO` at `cli.py:1616` (was 1330).
Both issues carry a comment recording this.

### Within Each Story

- Tests are written first and must fail before implementation.
- The readers (Phase 2) precede every consumer.
- Rendering precedes precedence rules, which precede failure composition.
- A task that invalidates an existing assertion fixes it in the same phase, before that phase's gate.

### Parallel Opportunities

Honest accounting — every `[P]` marker in this file, and nothing else:

- **T003, T005** — different test cases, before any implementation exists
- **T008, T012, T013, T014, T018** — test authoring for different stories, if staffed separately
- **T022, T023** — README versus test file

Everything else touches `_check_wfctl_version` in `wfctl/cli.py` and must be
sequential. Three developers on three stories would spend more time on conflicts
in one function than they would save.

---

## Implementation Strategy

### MVP (User Story 1 only)

1. Phase 1 → Phase 2 → Phase 3.
2. **Stop and validate**: the live stale build on this machine must move from `✓ latest` to the drift block.
3. That alone closes issue #21's acceptance criterion — a stale build missing merged pipeline logic is detectable from doctor's output alone.

### Incremental Delivery

US1 fixes the defect. US2 keeps the fix from becoming noise for install shapes
that cannot drift, and keeps every remedy pointed at the user's own repository.
US3 keeps a failed check from masquerading as a passing one. Each is
independently valuable and independently reviewable; none breaks the previous.

---

## Notes

- `tests/conftest.py`'s autouse fixture stubs this check for every unmarked test. A new test without `@pytest.mark.real_version_check` will silently exercise the stub and pass while proving nothing. This is the single most likely mistake in this feature.
- The second most likely: a test that passes for the wrong reason. T006 folds the `_fake_ls_remote_tags` update in for exactly this — a helper that stops matching the code under test produces green tests that assert nothing.
- Fixtures should use the real payloads recorded in `research.md`, including uv's and pip's differing key spacing — the reason the file is parsed as JSON rather than pattern-matched.
- No new dependency, no packaging change, no new module. If any task appears to require one, stop: `research.md` removed three such paths already and the finding is likely a fourth.
- Commit after each task or logical group.
