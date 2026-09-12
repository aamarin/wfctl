# Tasks: install-skills source

**Feature**: #146 | **Branch**: `146-install-skills-source`
**Input**: [plan.md](./plan.md), [spec.md](./spec.md), [research.md](./research.md), [data-model.md](./data-model.md), [contracts/cli.md](./contracts/cli.md), [quickstart.md](./quickstart.md)
**Revision**: 2 — incorporates the remediations from [checklists/analysis-report.md](./checklists/analysis-report.md) (C1, C2, C3, C4). Task IDs were renumbered; the report's original table refers to revision 1.

Run every command through `uv run --frozen --extra dev`, and every `wfctl`
through `uv run --frozen` — AGENTS.md requires one wfctl for both installing and
checking in this repo.

**FR-005 carries no task, deliberately.** The requirement is that the recorded
source never becomes committed project content. It is satisfied by construction:
`.wf-skills-manifest.json` is already gitignored, and research R1 chose it over
`wfctl.json` for exactly this reason. There is nothing to build and nothing that
could regress without the manifest's own ignore entry disappearing, which the
existing gitignore tests already cover.

---

## Phase 1: Setup

**Purpose**: Establish that the tree is green before anything changes, so a later
failure is attributable.

- [X] T001 Confirm the baseline is green by running the three recorded `verify` commands from `wfctl.json` (`pytest -q`, `ruff check wfctl/ tests/`, `mypy wfctl/`) plus `uv run --frozen wfctl doctor`

**Checkpoint**: Known-good starting point.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: The source-resolution seam. Both US1 and US2 read it; nothing else
can be built first.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete.

- [X] T002 [P] Write failing tests for source resolution in `tests/test_bundle.py`: a path holding `agents/` resolves to itself, a path holding `wfctl/agents/` resolves to `<path>/wfctl`, and a path holding neither raises `FileNotFoundError` naming both locations it looked in
- [X] T003 Implement `resolve_root(path) -> Path` as a public name in `wfctl/_bundle.py`, reusing `content_hash`'s existing `FileNotFoundError` message shape; verify with `tests/test_bundle.py`
- [X] T004 Validate Phase 2 with `uv run --frozen --extra dev pytest -q tests/test_bundle.py` — merge gate

**Checkpoint**: Foundation ready — user story work can begin.

---

## Phase 3: User Story 1 — Install skills from a checkout you name (Priority: P1) 🎯 MVP

**Goal**: `install-skills` accepts a source location, copies from it, records it,
and `doctor` reports the result as a state rather than as drift.

**Independent Test**: Point an install at a checkout whose skills differ from the
running tool's, then confirm the installed files match that checkout and `doctor`
exits 0 naming the source.

**Verification**:

- Automated: `tests/test_install_skills.py`, `tests/test_bundle.py`
- Manual: `quickstart.md` steps 1–2, 7 and 8
- Evidence: `.wf-skills-manifest.json` carries a resolved absolute `source`; `doctor` prints `✓ base: skills current (from <path>)` and exits 0

### Tests for User Story 1 ⚠️

> Write these first and confirm they fail before implementing.

- [X] T005 [P] [US1] Failing test in `tests/test_install_skills.py`: naming a source installs that source's content, not the running bundle's
- [X] T006 [P] [US1] Failing test in `tests/test_install_skills.py`: a named-source install records `source` as a resolved absolute path in each layer entry, and an install naming none writes no `source` key at all
- [X] T007 [P] [US1] Failing test in `tests/test_install_skills.py`: after a named-source install, `doctor` prints `skills current (from <path>)` and exits 0
- [X] T008 [P] [US1] Failing test in `tests/test_install_skills.py`: a source holding neither tree exits non-zero, copies nothing, and writes no manifest
- [X] T009 [P] [US1] Failing test in `tests/test_install_skills.py`: a bare install over a named-source install prints the replacement notice **even with `--yes`**, and the resulting record has no `source` key
- [X] T010 [P] [US1] Failing test in `tests/test_install_skills.py`: install naming a **relative** source, then run `doctor` with the working directory set to a subdirectory of the repo, and assert it still resolves and reports the source rather than failing to find it — this is FR-004's behavior, which asserting the stored path is absolute does not cover (analysis C1)
- [X] T011 [P] [US1] Failing test in `tests/test_install_skills.py`: `--prune` alongside a named source removes a recorded path that the **named source** no longer ships, guarding FR-012, which holds today only because the prune diff happens to read from the plan (analysis C2)

### Implementation for User Story 1

- [X] T012 [US1] Add the `--from` option to `install_skills_cmd` in `wfctl/cli.py` and resolve it through `_bundle.resolve_root` before the plan is built, so a bad source fails with the repo untouched; verify with T008's test
- [X] T013 [US1] Thread the resolved root through the three places `install_skills_cmd` reads `_bundle.BUNDLE_ROOT` for content in `wfctl/cli.py` — the layered copy loop, the tracker config copy, and the `content_hash` call; verify with T005's and T011's tests
- [X] T014 [US1] Write `source` into the per-layer manifest entry in `wfctl/cli.py` as a resolved absolute path when a source was named, and omit the key entirely when it was not; verify with T006's and T010's tests
- [X] T015 [US1] Print the replacement notice in `wfctl/cli.py` before the copy when the record names a source and this run names none, not gated on `--yes`; verify with T009's test
- [X] T016 [US1] In `doctor_cmd` in `wfctl/cli.py`, replace the single pre-computed bundle digest with a cache keyed on resolved source path, and add the "current, from a named source" branch; verify with T007's and T010's tests
- [X] T017 [US1] Validate User Story 1 with `uv run --frozen --extra dev pytest -q tests/test_install_skills.py tests/test_bundle.py` — merge gate

**Checkpoint**: A person can install from a named checkout and `doctor` stays quiet. This alone closes the issue's headline complaint.

---

## Phase 4: User Story 2 — Be told when the named source has moved on (Priority: P2)

**Goal**: `doctor` notices the recorded source changing, and the repair it prints
reinstalls from that same source.

**Independent Test**: Not independent of User Story 1 — it reads a record only
that story writes. Given a completed named-source install: change a file in that
checkout, run `doctor`, and confirm it reports the difference and prints a command
containing the recorded source.

**Verification**:

- Automated: `tests/test_install_skills.py`
- Manual: `quickstart.md` steps 3–4 — step 4 is the one that fails if the remedy line is wrong
- Evidence: the printed remedy contains `--from <recorded source>`, and running it verbatim leaves `doctor` green and still naming that source

### Tests for User Story 2 ⚠️

- [X] T018 [P] [US2] Failing test in `tests/test_install_skills.py`: when the recorded source's content changes, `doctor` reports `source changed since install` naming the path, and exits 1
- [X] T019 [P] [US2] Failing test in `tests/test_install_skills.py`: that report's remedy line contains `--from` with the recorded source, and a default-source layer's remedy line still does not

### Implementation for User Story 2

- [X] T020 [US2] Add the changed-source branch and its remedy line to `doctor_cmd` in `wfctl/cli.py`, following the existing per-layer remedy pattern that already names the agent; verify with T018 and T019's tests
- [X] T021 [US2] Amend step 2 of `wfctl/agents/skills/start-session/SKILL.md` to state that the command `doctor` printed governs over the literal examples beside it; verify by running `uv run --frozen wfctl install-skills` and reading the installed `.agents/skills/start-session/SKILL.md`, per AGENTS.md's rule that skill prose is not verified by the suite
- [X] T022 [US2] Validate User Story 2 with `uv run --frozen --extra dev pytest -q tests/test_install_skills.py` — merge gate

**Checkpoint**: The edit-install-test loop reports honestly, and its repair no longer destroys the test.

---

## Phase 5: User Story 3 — Get a truthful answer when the source is unreachable (Priority: P3)

**Goal**: A recorded source that no longer exists produces a warning, not a
failure and not a guess.

**Independent Test**: Not independent of User Story 1, for the same reason as User
Story 2. Given a completed named-source install: move the checkout away, run
`doctor`, and confirm it names the unreachable source and does not fail on that
account alone.

**Verification**:

- Automated: `tests/test_install_skills.py`
- Manual: `quickstart.md` step 5
- Evidence: `⚠ base: installed from <path> — source is gone, can't check`, with the exit code unchanged by this condition

### Tests for User Story 3 ⚠️

- [X] T023 [P] [US3] Failing test in `tests/test_install_skills.py`: an unreachable recorded source produces the warning naming it, and does not by itself make the run exit non-zero

### Implementation for User Story 3

- [X] T024 [US3] Catch the resolution failure per layer in `doctor_cmd` in `wfctl/cli.py` and emit the unreachable warning without contributing to the exit code, matching how `_warn_missing_bootstrap` already warns without becoming a finding; verify with T023's test
- [X] T025 [US3] Validate User Story 3 with `uv run --frozen --extra dev pytest -q tests/test_install_skills.py` — merge gate

**Checkpoint**: All four of `doctor`'s reachable states are implemented and covered.

---

## Phase 6: Polish & Cross-Cutting Concerns

- [X] T026 [P] Confirm the `--from` help text matches `contracts/cli.md` by running `uv run --frozen wfctl install-skills --help`
- [X] T027 Run `quickstart.md` end to end in a scratch worktree — all eight steps, with particular attention to step 4 (the remedy repairs rather than replaces), step 6 (the replacement notice survives `--yes`), and step 8 (a repo with no wfctl source tree, which is SC-005 and the only exercise of it); record the observed output
- [X] T028 Update the `Log` line of `docs/architecture/drift-is-measured-against-the-recorded-source.md` if implementation changed anything the record claims; leave `status: proposed` — acceptance is the reviewer's call, not this branch's
- [X] T029 Validate the whole feature with the three recorded `verify` commands plus `uv run --frozen wfctl doctor` — merge gate

---

## Dependencies

```
Phase 1  (T001)
   └─► Phase 2  (T002-T004)          resolve_root — blocks everything
          ├─► Phase 3  US1 (T005-T017)   MVP
          │      └─► Phase 4  US2 (T018-T022)   needs US1's recorded source
          │             └─► Phase 5  US3 (T023-T025)   needs US2's branch structure
          └─────────────────► Phase 6  (T026-T029)   after all stories
```

US2 and US3 are not independent of US1, and deliberately so: both are `doctor`
behaviors that read a record only US1 writes. US1 alone is a shippable increment;
US2 and US3 are not. spec.md's `Independent Test` entries say the same thing.

## Parallel opportunities

- **Phase 3**: T005–T011 are seven separate test functions written before any
  implementation — parallelizable as authoring work, though they land in the same
  file and should be committed together.
- **Phase 3 implementation**: T012–T016 touch overlapping regions of
  `install_skills_cmd` and `doctor_cmd`; treat as sequential despite the phase
  structure.
- **Phase 4**: T018 and T019 are independent test functions. T021 touches a
  different file entirely (`start-session/SKILL.md`) and can proceed alongside
  T020.
- **Phase 6**: T026 and T028 are independent of each other and of T027.

## Implementation strategy

**MVP is Phase 3.** After T017, a person can install from a named checkout and
`doctor` reports it as a state — which is the whole of issue #146's headline
complaint and closes #75's remaining half for consumer repos.

Phases 4 and 5 harden it. Phase 4 is the one that matters most in practice: it is
what stops an automated session-start repair from silently discarding a
named-source install, and its T021 is the only task in the feature that changes
shipped prose rather than code.

**Do not decide PR boundaries here.** `/speckit.decompose` owns that after
`/speckit.analyze` passes.

## Task summary

| Phase | Story | Tasks | Count |
|---|---|---|---|
| 1 Setup | — | T001 | 1 |
| 2 Foundational | — | T002–T004 | 3 |
| 3 User Story 1 | US1 (P1) | T005–T017 | 13 |
| 4 User Story 2 | US2 (P2) | T018–T022 | 5 |
| 5 User Story 3 | US3 (P3) | T023–T025 | 3 |
| 6 Polish | — | T026–T029 | 4 |
| **Total** | | | **29** |
