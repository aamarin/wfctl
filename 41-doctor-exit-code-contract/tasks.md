# Tasks: doctor exit-code contract

**Input**: Design documents from `41-doctor-exit-code-contract/` in the recorded spec root
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/doctor-exit-code.md, quickstart.md

**Tests**: This feature's entire deliverable is a behavioural contract, so every
task carries an automated verification path. Two tasks additionally carry an
end-to-end check, because the defect they fix — a loop between a command and the
report about it — is not observable from unit tests.

**Organization**: Grouped by user story. US2 precedes US1 despite both being P1:
US2's template correction is what allows the check deleted in US1 to be removed.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependency on incomplete work)
- **[Story]**: US1–US4, mapping to spec.md
- All paths are repository-relative to `/Users/andremarin/Development/wfctl/wt/41-doctor-exit-code-contract`

## Path Conventions

Single Python package: `wfctl/` and `tests/` at the repository root. No `src/`.

---

## Phase 1: Setup

**Purpose**: Establish the baseline every later gate is measured against.

- [X] T001 Confirm the branch is current with `origin/master` at `271bb2c` and record baseline gate results; verify with `uv run --frozen --extra dev pytest -q` (expect 395 passing), `uv run --frozen --extra dev ruff check .` (expect clean), `uv run --frozen --extra dev mypy` (expect clean over 11 files)

---

## Phase 2: Foundational (Blocking Prerequisites)

**No tasks.** The package, test harness, CI gates, and every module this feature
touches already exist. There is no shared scaffolding to build, and no single
change blocks all four stories — US4 depends on nothing in the others. Story
phases begin at Phase 3.

Recorded rather than omitted so `/speckit.analyze` sees the phase was considered
and found empty, not skipped.

---

## Phase 3: User Story 2 — A newly set-up repository reports clean (P1)

**Goal**: A repository whose configuration was just seeded produces no findings
about that configuration.

**Independent Test**: Seed a fresh repository's workmux configuration, run
`doctor`, confirm nothing in the output refers to `.workmux.yaml`.

**Why first**: The shipped template names the superseded command, so
`_check_stale_archive_hook` still has a live consumer and cannot be deleted in
Phase 4 until this lands. It is also the story that would break every freshly
configured repository once US1's contract makes findings fail a build.

### Verification

- Unit: `uv run --frozen --extra dev pytest tests/test_bundle.py -q -k stale`
- End-to-end: seed a scratch repository and run `doctor` against it, per quickstart.md
- Regression direction: revert the template and confirm the test fails

### Tasks

- [X] T002 [US2] Replace `archive-story` with `archive-specs` on the `pre_remove` hook line and in the comment above it in `wfctl/agents/configs/workmux/.workmux.yaml`; verify with T003
- [X] T003 [US2] Add `test_seeded_workmux_config_does_not_trip_doctors_own_stale_hook_check` to `tests/test_bundle.py`, asserting through `_workmux.pre_remove_uses_former_name` and `_workmux.pre_remove_wired` rather than a copied literal; verify with `uv run --frozen --extra dev pytest tests/test_bundle.py -q -k stale`
- [X] T004 [US2] Confirm the test fails on the pre-fix template by temporarily reverting the hook line and re-running the same command, then restore
- [X] T005 [US2] Verify end to end in a scratch repository: `git init`, `wfctl install-config workmux`, `wfctl doctor`; expect no finding mentioning `.workmux.yaml`
- [X] T006 [US2] Validate Phase 3 with `uv run --frozen --extra dev pytest -q` — merge gate

---

## Phase 4: User Story 1 — A build can trust what doctor's exit code means (P1)

**Goal**: One exit-code convention across every check, with could-not-determine
contributing zero.

**Independent Test**: Run `doctor` against a repository with one known piece of
drift and confirm a non-zero exit; remove the drift and confirm zero; disconnect
the network and confirm zero.

**Depends on**: Phase 3 (T002 unblocks T007).

### Verification

- `uv run --frozen --extra dev pytest tests/test_install_skills.py -q -k doctor`
- `uv run --frozen --extra dev pytest tests/test_remaining_commands.py -q -k doctor`
- `uv run --frozen --extra dev mypy` — the `-> bool` conversions are annotation changes
- Contract reference: `contracts/doctor-exit-code.md`

### Tasks

- [X] T007 [US1] Delete `_check_stale_archive_hook` from `wfctl/cli.py` and its call site in `doctor_cmd`; verify with T008
- [X] T008 [US1] Delete `test_doctor_does_not_fail_over_a_stale_hook_name` from `tests/test_remaining_commands.py`, and reshape `test_doctor_reports_a_pre_remove_still_naming_the_former_command` into `test_doctor_leaves_a_hook_on_the_former_name_alone` rather than deleting it — it carries the only doctor-level assertion of FR-007. Asserted as an output equivalence between an old-name and a current-name repo, not against message text; verify with `uv run --frozen --extra dev pytest tests/test_remaining_commands.py -q`
- [X] T009 [US1] Keep `_workmux.pre_remove_uses_former_name` and its tests in `tests/test_workmux.py` — T003 now depends on it — and assert `pre_remove_wired` still treats *both* command names as wired, so deleting the stale-hook check cannot take FR-007's protection with it; verify with `uv run --frozen --extra dev pytest tests/test_workmux.py -q`
- [X] T010 [US1] Change `_check_workmux_hook` in `wfctl/cli.py` to `-> bool`, returning `False` on every early return and on a successfully applied fix, `True` when the hook stands unwired; verify with T014
- [X] T011 [US1] Change `_check_spec_root_migration` in `wfctl/cli.py` to `-> bool`, returning `True` only when stranded spec directories are reported; verify with T015
- [X] T012 [US1] Change `_check_legacy_agent_dir` in `wfctl/cli.py` to `-> bool`, returning `True` when `.agent/` is present; verify with T016a
- [X] T013 [US1] OR all three results into `exit_code` at the call sites in `doctor_cmd` (`wfctl/cli.py`), and record the contract — including that could-not-determine returns `False` — in a comment where the checks are defined. Used `any([...])` over a list rather than `a or b or c`: `or` short-circuits, which would suppress every check after the first finding; verify with T014 and T015
- [X] T014 [US1] Replace `test_doctor_exit_code_is_unchanged_by_this_warning` in `tests/test_remaining_commands.py` with three tests covering the interactive fix path: accepted exits 0 (and asserts the hook is actually wired), declined exits 1, non-interactive exits 1; verify with `uv run --frozen --extra dev pytest tests/test_remaining_commands.py -q`
- [X] T015 [US1] Rewrite `test_doctor_exit_code_is_unchanged_by_the_spec_root_warning` in `tests/test_install_skills.py` as `test_doctor_fails_over_stranded_specs_and_passes_without_a_recorded_root`, asserting both states against one repo; verify with `uv run --frozen --extra dev pytest tests/test_install_skills.py -q -k stranded`
- [X] T016 [US1] FR-003's both-halves assertion already existed as `test_doctor_warns_on_a_record_without_a_fingerprint` (exit 0 **and** the message). No new test written; docstring extended to record its role in the contract, so a later edit does not drop the output assertion as redundant
- [X] T016a [US1] Rewrote `test_doctor_exit_code_is_unchanged_by_the_superseded_dir` in `tests/test_remaining_commands.py` — it existed and asserted the *opposite* convention — as `test_doctor_fails_over_the_superseded_dir_and_passes_without_it`, covering both states; verify with `uv run --frozen --extra dev pytest tests/test_remaining_commands.py -q -k superseded`
- [X] T017 [US1] Confirm `_check_wfctl_version` is untouched. The task's `grep -c` returns 1, not 0 — it matches the contract comment that *names* the function to explain the exclusion. Verified properly by extracting the function from both revisions and comparing: byte-identical, 28 lines — FR-013 boundary against PR B holds
- [X] T018 [US1] Validate Phase 4 with `uv run --frozen --extra dev pytest -q && uv run --frozen --extra dev mypy && uv run --frozen --extra dev ruff check .` — merge gate. 396 passing, mypy and ruff clean. Also confirmed end to end: a clean scratch repo exits 0, the same repo with a `.agent/` directory exits 1

---

## Phase 5: User Story 3 — What the tool abandoned is surfaced (P2)

**Goal**: `doctor` names entries inside its own installation trees that it
installed but no longer records.

**Independent Test**: Install, rename a bundled file, install again, run `doctor`,
confirm the old path is named.

**Depends on**: Phase 4 (adopts the contract from T013).

### Verification

- `uv run --frozen --extra dev pytest tests/test_install_skills.py -q -k abandoned`
- Scan set defined in data-model.md; exclusions in research.md

### Tasks

- [X] T019 [US3] Implement `_check_abandoned_entries(repo_root, manifest) -> bool` in `wfctl/cli.py`, reporting entries absent from the record. **Scans fixed destinations derived from `_BASE_TARGETS` + `_RUNTIME_TARGETS`, not the parents of recorded paths** — deriving them from the record has a hole: a directory whose last recorded entry falls out drops out of the scan with it, silently, in exactly the case worth reporting. Found while testing; see T019a; verify with T021
- [X] T019a [US3] **Design defect found during T021.** `.agents/trackers/` holds both `github.json` (recorded by `install-skills --tracker github`, `cli.py:1206`) and hand-authored `<name>.json` files that `/scaffold-tracker` documents. The recorded-parent scan would have reported a repo's own Jira config as abandoned and failed its build over a file wfctl never wrote — the assumption analyze recorded as needing validation, invalidated. The fixed-destination scan excludes it by construction. Latent rather than active: this repo has no `.agents/trackers/` at all. **Closed here, no follow-up** — nothing else in wfctl enumerates that directory (every access is by exact filename: `cli.py:1206`, `:1313`, `:1594`), so this scan was the only thing the mixed ownership could have broken. Splitting the two kinds of config would be tidier and fixes nothing
- [X] T020 [US3] Call it from `doctor_cmd` after the manifest gate in `wfctl/cli.py`, OR'd into `exit_code`, so it never runs when nothing is installed; verify with T021
- [X] T021 [US3] Add tests to `tests/test_install_skills.py`: an abandoned file is named and exits 1; an abandoned directory holding several files is one finding (SC-007); a file in `.claude/commands/` is never reported; a hand-authored `.agents/trackers/jira.json` is never reported; an orphan is still found when it was its directory's last recorded entry; a fully recorded repository is silent and exits 0; an empty manifest skips the scan entirely; **and every reported entry is still on disk after `doctor` returns** — FR-010 is report-only, and it is the one requirement here whose violation destroys user data; verify with `uv run --frozen --extra dev pytest tests/test_install_skills.py -q -k "abandoned or record or removes or finding or tracker_config or orphan"`
- [X] T022 [US3] Verify against this repository: `wfctl doctor` reports no abandoned entries. Exits 0 with a `⚠` for a layer predating content hashing — a live demonstration of the could-not-determine rule
- [X] T023 [US3] Validate Phase 5 with `uv run --frozen --extra dev pytest -q && uv run --frozen --extra dev mypy` — merge gate. 404 passing, mypy and ruff clean

---

## Phase 6: User Story 4 — The pipeline never names a command that does not exist (P3)

**Goal**: A `_STEP_COMMAND` entry naming an unshipped command fails the build.

**Independent Test**: Point a table entry at a name that is not shipped; the build
fails and names the entry.

**Depends on**: nothing. Touches no production code and can be done at any point.

### Verification

- `uv run --frozen --extra dev pytest tests/test_pipeline_commands.py -q`

### Tasks

- [X] T024 [P] [US4] Create `tests/test_pipeline_commands.py` asserting every `_STEP_COMMAND` value in `wfctl/_pipeline.py` has a matching `wfctl/agents/commands/<name>.md` in the shipped bundle, with the failure naming the entry and the nearest shipped name via `difflib.get_close_matches`; verify with `uv run --frozen --extra dev pytest tests/test_pipeline_commands.py -q`
- [X] T025 [US4] Confirm the assertion is one-way — the bundle may ship commands the table does not name — by asserting only over the table's values, not the directory listing. Pinned by its own test, which fails if the assertion is ever tightened to a two-way match
- [X] T026 [US4] Confirm the test catches real drift by temporarily renaming one entry in `_STEP_COMMAND` and re-running, then restoring. Reproduced #23 exactly: `brainstorm: /brainstorm — nearest shipped: /speckit.brainstorm`
- [X] T027 [US4] Validate Phase 6 with `uv run --frozen --extra dev pytest -q` — merge gate

---

## Phase 7: Polish & Cross-Cutting Concerns

- [X] T028 [P] Update `doctor_cmd`'s docstring in `wfctl/cli.py` to state the exit-code contract, since it currently describes only the output markers; verify with `uv run --frozen --extra dev pytest -q`
- [X] T029 [P] Confirm no test added in this feature performs network I/O, keeping SC-006. Ran the full suite under a pytest plugin blocking `socket.connect`/`create_connection`/`getaddrinfo` — 407 passing. Guard proven live by a deliberate connection failing under it. Three tests carry `real_version_check` (not two, as the task assumed); all three stub `subprocess.run` themselves. Limit: the guard is in-process and would not catch a subprocess shelling out — covered instead by conftest's autouse stub and #43 removing the install-time clone
- [X] T030 Run the whole gate set: `uv run --frozen --extra dev pytest -q`, `uv run --frozen --extra dev ruff check .`, `uv run --frozen --extra dev mypy` — merge gate. 407 passing, both clean
- [X] T031 Run `wfctl doctor` in this repository and confirm `exit=0`, per quickstart.md's whole-feature check

---

## Dependencies

```
Phase 1 (T001)
   │
Phase 3 · US2 ── T002 ─→ T003 ─→ T004 ─→ T005 ─→ T006
   │                                                │
   │  T002 unblocks the deletion in T007            │
   ▼                                                ▼
Phase 4 · US1 ── T007 ─→ T008 ─→ T009
                   │
                   ├─ T010 ─┐
                   ├─ T011 ─┼─→ T013 ─→ T014, T015, T016, T016a ─→ T017 ─→ T018
                   └─ T012 ─┘
   │
   │  T013 defines the contract US3 adopts
   ▼
Phase 5 · US3 ── T019 ─→ T020 ─→ T021 ─→ T022 ─→ T023

Phase 6 · US4 ── T024 ─→ T025 ─→ T026 ─→ T027     (independent of all above)

Phase 7 ── T028, T029 ─→ T030 ─→ T031
```

**Story completion order**: US2 → US1 → US3. US4 anywhere.

## Parallel Opportunities

- **T024 (US4)** runs in parallel with any other phase. It creates a new test file
  and touches no production code, so it cannot conflict.
- **T028 and T029** are independent of each other — different files, different
  concerns.
- **T010, T011, T012** are *not* parallel despite being three separate functions:
  all three edit `wfctl/cli.py`, and T013 depends on all three.

## Implementation Strategy

**MVP**: Phase 3 + Phase 4 (US2 + US1). That is the stated defect fixed — one
exit-code convention, and no repository failing it on the day it is configured.
Phases 5 and 6 add checks that the contract exists to serve, and either could
land separately if review runs long.

**Increment order**: each phase ends at a merge gate where the full suite, types,
and lint are green, so any phase boundary is a safe stopping point.

**Scope boundary held throughout**: `_check_wfctl_version` is not modified. T017
verifies this explicitly, because a tidiness-driven sweep across all checks is the
likely accident and it would collide with the separate #21/#35 rewrite.

## Delivery Note

These are implementation checklist items, not PR boundaries. `/speckit.decompose`
decides grouping. The design already records the intent — one PR — but that
decision belongs to decompose, not here.
