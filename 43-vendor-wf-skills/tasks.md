# Tasks: Vendor wf-skills

**Input**: Design documents from `/Users/andremarin/Development/wfctl-specs/43-vendor-wf-skills/`
**Prerequisites**: [plan.md](./plan.md), [spec.md](./spec.md), [research.md](./research.md), [data-model.md](./data-model.md), [contracts/cli.md](./contracts/cli.md), [quickstart.md](./quickstart.md)

**Tests**: `pytest` + `ruff` + `mypy` exist and gate every phase. This feature adds
two kinds of check the repo does not have: a fingerprint unit test, and a
**wheel-level** check — the existing suite runs against the source tree, where the
bundled files and their exec bit are present whether or not the wheel ships them.

**Organization**: Grouped by user story. Phase boundaries are chosen so each one
leaves the tool in a working state; where a phase leaves a *degraded but safe*
state, that is called out explicitly.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- Paths are relative to the repo root unless absolute

---

## Phase 1: Setup (Vendor the content)

**Purpose**: Get the files into the package and prove the wheel carries them.
Nothing here touches `cli.py`, so the tool keeps working throughout.

- [X] T001 Copy the wf-skills tree into the package from a **fresh clone**, not this repo's installed `.agents/` (which has no `trackers/` or `configs/`): `wfctl/agents/{skills,commands,trackers,configs}` and `wfctl/specify/{scripts,templates}`, leading dots stripped — see [quickstart.md](./quickstart.md) §1; verify with `ls wfctl/agents wfctl/specify` matching the tree in [data-model.md](./data-model.md) §1
- [X] T002 Stage the tree and assert git recorded mode `100755` on `wfctl/specify/scripts/bash/*.sh`, applying `git update-index --chmod=+x` if not; verify with `git ls-files -s wfctl/specify/scripts/bash`
- [X] T003 Add `[tool.setuptools.package-data]` to `pyproject.toml` (the file has no such section today); verify with T004. **The globs need a `.*` twin per tree** — `wfctl = ["agents/**/*", "agents/**/.*", "specify/**/*", "specify/**/.*"]`. setuptools globs with Python's `glob`, which excludes dot-prefixed names from `*`, so the two-entry form shipped 65 of 66 files and dropped `agents/configs/workmux/.workmux.yaml` — the only file `install-config workmux` copies. Caught by T004 on the first build
- [X] T004 Build a wheel and assert it carries the bundled files with the exec bit intact, per [quickstart.md](./quickstart.md) §2 — `uv build --wheel` then inspect `external_attr`. **A zero-file result here means T003's globs are wrong and every later phase would build on nothing.**
- [X] T005 Confirm `importlib.resources.files("wfctl")` resolves to a real directory under a clean install of that wheel on Python 3.11 — the floor version ([research.md](./research.md) §2); verify with a one-line `uv run --python 3.11` check against the installed wheel, not the source tree

**Checkpoint**: [X] T006 Validate setup with `uv build --wheel` + the wheel inspection from T004 — merge gate. The tool's behaviour is unchanged at this point; only the package got bigger. **Done**: 66/66 files in the wheel, all five `.sh` exec, `369 passed` unchanged.

---

## Phase 2: Foundational (The bundle seam)

**Purpose**: The module every later phase imports, and the test seam that lets the
suite point at fake content. Blocks all four stories.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete.

- [X] T007 Create `wfctl/_bundle.py` with `BUNDLE_ROOT: Path` (module-level, resolved via `importlib.resources.files("wfctl")` — read through a module-global lookup at call time, never bound as a default argument) and `content_hash(root: Path) -> str`; annotate both, since `disallow_untyped_defs` is on and `[tool.mypy] files = ["wfctl"]` covers the new module; verify with T008–T010
- [X] T008 [P] Write `tests/test_bundle.py::test_content_hash_is_stable_for_identical_trees` — two directories with identical content built in different creation order hash equal, **and** a fixed fixture tree hashes to a hardcoded expected digest. The hardcoded value is the part that satisfies FR-010: equality-within-one-run passes even if macOS and Linux disagree, and CI is `ubuntu-latest` only (`ci.yml:19`, `:75`) while development happens on darwin. Running on both matrix Pythons covers the cross-version half (FR-010)
- [X] T009 [P] Write `tests/test_bundle.py::test_content_hash_changes_on_edit_and_on_rename` — editing a byte changes it, and moving a file to a new path with identical bytes also changes it (FR-009)
- [X] T010 [P] Write `tests/test_bundle.py::test_content_hash_covers_every_sourceable_directory`, **parametrized over all six**: `agents/skills`, `agents/commands`, `agents/trackers`, `agents/configs`, `specify/scripts`, `specify/templates`. Modifying one file in each must change the hash. `agents/trackers` is the case per-layer hashing would miss ([data-model.md](./data-model.md) §2); the other five catch a hash that silently skips a subtree (FR-008, FR-019)
- [X] T011 Add an autouse `bundle` fixture to `tests/conftest.py` that builds a minimal fake bundle in a temp dir (`agents/skills/test-skill/SKILL.md`, `agents/commands/test-cmd.md` — **undotted**, matching the new source paths) and `monkeypatch.setattr("wfctl._bundle.BUNDLE_ROOT", root)`, returning the path so tests that need custom content can add to it. Autouse so no test silently reads the real bundle; verify with T012

**Checkpoint**: [X] T012 Validate foundation with `uv run pytest -q tests/test_bundle.py` and `uv run mypy` — merge gate. **Done**: 11 bundle tests pass, `380 passed` overall, mypy and ruff clean.

---

## Phase 3: User Story 1 - Same result every time (Priority: P1) 🎯 MVP

**Goal**: Both install commands source from the package. No network, no `--repo`/`--ref`, no resolved-commit pin.

**Independent Test**: With the machine offline, `wfctl install-skills` and `wfctl install-config workmux` complete and install the full tree; two repos on the same wfctl version get byte-identical content.

**Verification**:

- Automated: `uv run pytest -q` (whole suite, offline), `tests/test_install_skills.py`, `tests/test_install_config.py`, `tests/test_tracker.py`
- Manual: [quickstart.md](./quickstart.md) §3 — clean wheel install into a scratch repo, then §5 for the no-op re-install
- Evidence: no `Cloning…` line; `✓ Installed from wfctl <version>`; sub-second run (SC-003)

**Note on scope**: deleting `--repo`/`--ref` removes the variables `cli.py:1262-1269` writes into the manifest, so the manifest **write** side lands here, not in US2. After this phase `doctor` still reads `commit` and finds none — it takes its existing "no pinned commit on record" warning branch (`cli.py:1874-1879`) and exits unchanged. Degraded, not broken; US2 replaces it.

### Tests for User Story 1 ⚠️

- [X] T013 [P] [US1] Convert `_make_wf_skills_repo` in `tests/test_install_skills.py:22` from a git repo to a plain directory builder (drop `git init`/`add`/`commit`, drop the `subprocess` import at line 4 if unused) and rename its tree to the undotted `agents/…` layout
- [X] T014 [P] [US1] Same conversion for `_make_wf_skills_repo_with_config` in `tests/test_install_config.py:18`
- [X] T015 [P] [US1] Same conversion for `_make_wf_skills_repo_with_tracker` in `tests/test_tracker.py:260`
- [X] T016 [US1] Drop `--repo`/`--ref` from every `runner.invoke` call site across the three test files (~63 lines in `test_install_skills.py`, ~15 in `test_install_config.py`, ~4 in `test_tracker.py`), pointing them at the `bundle` fixture from T011 instead; verify with `grep -rn -- "--repo\|--ref" tests/` returning nothing
- [X] T017 [US1] Delete `test_install_skills_bad_repo_exits_one` (`tests/test_install_skills.py:251`) — it exercises the flag being removed, and is the suite's last unstubbed network call ([research.md](./research.md) §5)
- [X] T018 [US1] Add `tests/test_install_skills.py::test_removed_source_options_are_an_error` asserting `install-skills --repo X` and `install-config workmux --ref Y` each exit 2 naming the offending flag (FR-004, [research.md](./research.md) §6 — typer's built-in behaviour, no product code)
- [X] T019 [US1] Add a test asserting no module under `wfctl/` contains the string `aamarin/wf-skills` (SC-006, FR-003), excluding the vendored `wfctl/agents/` and `wfctl/specify/` trees, whose own content may legitimately mention it

### Implementation for User Story 1

- [X] T020 [US1] Repoint the `src` half of `_BASE_TARGETS` (`cli.py:630`), `_AGENT_TARGETS` (`cli.py:641`), `_RUNTIME_TARGETS` (`cli.py:672`) and `_CONFIG_SOURCES` (`cli.py:682`) from `.agents/…`/`.specify/…` to `agents/…`/`specify/…`. **Destinations are untouched**; `_kind_of` (`cli.py:764`) reads the source basename, which the dot-strip preserves; verify with `tests/test_install_skills.py::test_layer_destinations_are_disjoint` and the copy tests
- [X] T021 [US1] Delete the `--repo`/`--ref` options from `install_skills_cmd` (`cli.py:964-969`), the clone and `git rev-parse HEAD` block (`cli.py:1129-1141`), and the now-unused function-local `subprocess as sp` / `tempfile` imports (`cli.py:993-994`), sourcing the plan from `wfctl._bundle.BUNDLE_ROOT`; verify with `tests/test_install_skills.py`
- [X] T022 [US1] Reword the `--tracker github` not-found warning (`cli.py:1206-1210`), which interpolates `{repo}@{ref}` — names that stop existing — to name the wfctl version; verify with `tests/test_tracker.py`
- [X] T023 [US1] Replace `repo`/`ref`/`commit` with `wfctl_version` (from `importlib.metadata.version("wfctl")`) and `content_hash` in the manifest write (`cli.py:1262-1269`), leaving `installed_at` and `items` untouched (FR-007, FR-016); verify with an assertion on the written manifest replacing `test_install_pins_resolved_commit` (`tests/test_install_skills.py:448`)
- [X] T024 [US1] Change the provenance line at `cli.py:1316` to `✓ Installed from wfctl {version}`; verify with `tests/test_install_skills.py::test_install_skills_reports_what_it_installed`
- [X] T025 [US1] Delete `install-config`'s duplicate `--repo`/`--ref` (`cli.py:1445-1448`) and its clone (`cli.py:1474-1487`, carrying the `# ponytail: dup'd clone` note), reword the `✗ Config 'x' not found` error that interpolates them, drop the unused `sp`/`tempfile` imports (`cli.py:1458-1459`), and change the provenance line at `cli.py:1552`; verify with `tests/test_install_config.py` **plus a new assertion there that `install-config workmux` leaves `.wf-skills-manifest.json` absent or byte-unchanged** — this task edits that function's body and nothing else guards FR-017 / IC-2 against a manifest write creeping in

**Checkpoint**: T026 Validate US1 with `uv run pytest -q`, `uv run ruff check .`, `uv run mypy`, then [quickstart.md](./quickstart.md) §3 offline — merge gate. Installs are network-free and deterministic; `doctor` warns rather than reports.

---

## Phase 4: User Story 2 - Knowing when a repo has fallen behind (Priority: P2)

**Goal**: `doctor` compares the recorded fingerprint against the running bundle and names the remedy, entirely locally.

**Independent Test**: Install skills, mutate the recorded `content_hash`, run `wfctl doctor` — stale, with `update: wfctl install-skills`.

**Verification**:

- Automated: the doctor tests in `tests/test_install_skills.py` (`:462`, `:471`, `:488`, `:495`, `:998`)
- Manual: [quickstart.md](./quickstart.md) §4 — all four states reachable by hand
- Evidence: exact remedy text asserted per state; `doctor` runs with wifi off

### Tests for User Story 2 ⚠️

- [X] T027 [P] [US2] Rewrite `test_doctor_reports_up_to_date` (`tests/test_install_skills.py:462`) for the current state: `✓ {layer}: skills current (wfctl {v})`, exit 0
- [X] T028 [P] [US2] Replace `test_doctor_reports_behind_with_diff` (`:471`) with `test_doctor_reports_stale_across_versions` — hash differs and `wfctl_version` differs: both versions named, remedy line present, exit 1 (FR-012, FR-013)
- [X] T029 [P] [US2] Add `test_doctor_reports_stale_at_the_same_version` — hash differs, versions equal: `⬆ {layer}: bundled skills changed since install`, no upgrade implied. This is the *primary* case under an editable dev install ([data-model.md](./data-model.md) §3)
- [X] T030 [P] [US2] Add `test_doctor_skills_verdict_survives_an_offline_release_check` — stub `_check_wfctl_version` to the `⚠ … couldn't check latest (offline?)` path and assert the skills verdict is still reported and still authoritative (FR-014, D-2)

### Implementation for User Story 2

- [X] T031 [US2] Replace the per-layer block in `doctor_cmd` (`cli.py:1871-1907`) with the four-state local comparison from [data-model.md](./data-model.md) §3, and delete the now-unused `subprocess as sp` / `tempfile` imports at `cli.py:1845-1846` — both exist solely for the `ls-remote` and diff-clone being removed; verify with T027–T030
- [X] T032 [US2] Confirm a layer that installs nothing still writes no entry and is never reported (edge case in [spec.md](./spec.md); existing behaviour); verify with `tests/test_install_skills.py::test_bare_install_writes_agents_only` and `::test_asked_marker_is_not_mistaken_for_an_installed_layer`

**Checkpoint**: T033 Validate US2 with `uv run pytest -q` and [quickstart.md](./quickstart.md) §4 walked end to end — merge gate.

---

## Phase 5: User Story 3 - Existing repos keep working (Priority: P3)

**Goal**: A manifest written before this change warns once, migrates in one command, and loses no backup pointer.

**Independent Test**: Pre-change record → `doctor` warns → `install-skills` → `doctor` reports current → `uninstall-skills` still restores.

**Verification**:

- Automated: `tests/test_install_skills.py` migration tests
- Manual: [quickstart.md](./quickstart.md) §4, final block
- Evidence: no traceback on the old record; `repo`/`ref`/`commit` absent after rewrite; restored file contents byte-identical

### Tests for User Story 3 ⚠️

- [X] T034 [P] [US3] Rewrite `test_doctor_warns_when_no_commit_pinned` (`tests/test_install_skills.py:495`) as `test_doctor_warns_on_a_record_without_a_fingerprint` — a manifest carrying `repo`/`ref`/`commit` and no `content_hash` produces one `⚠ … installed before content hashing` line, does not raise, and leaves the exit code unchanged (FR-015)
- [X] T035 [P] [US3] Add `test_reinstall_migrates_a_pre_change_record` — after `install-skills`, `repo`/`ref`/`commit` are gone and `wfctl_version`/`content_hash` are present (FR-016)
- [X] T036 [P] [US3] Add `test_uninstall_restores_backups_recorded_before_the_change` — build a pre-change manifest whose `items` carry `backup` pointers, migrate it, then uninstall and assert the original file contents come back (FR-016, M1 — the invariant most likely to break silently)

### Implementation for User Story 3

- [X] T037 [US3] Make the manifest rewrite drop unknown legacy provenance keys while preserving `items`, `backup` and the non-layer scalars `tracker`/`spec_root`/`spec_root_asked` (`_NON_LAYER_KEYS`, `cli.py:693`); verify with T035, T036 and `::test_install_preserves_spec_root`
- [X] T038 [US3] Confirm the pre-layer manifest upgrade path (`tests/test_install_skills.py:660 test_upgrade_from_pre_layer_manifest_is_silent`) still passes unchanged — two migrations now stack, and this one predates layers entirely; verify by running that test

**Checkpoint**: T039 Validate US3 with `uv run pytest -q` — merge gate.

---

## Phase 6: User Story 4 - Packaging regressions caught before release (Priority: P4)

**Goal**: CI exercises the built artifact, so a dropped directory or a lost exec bit fails a build instead of a user's machine.

**Independent Test**: Remove one entry from `[tool.setuptools.package-data]` and confirm CI fails naming what is missing (SC-008).

**Verification**:

- Automated: the new `wheel` job in `.github/workflows/ci.yml`
- Manual: the SC-008 removal experiment, once
- Evidence: job fails on a deliberately broken declaration; passes on a correct one

### Implementation for User Story 4

- [X] T040 [US4] Add a `wheel` job to `.github/workflows/ci.yml` that runs `uv build --wheel` and installs it into a clean environment (**not** `uv sync`, which installs editable and would pass against the source tree), then asserts `wfctl/agents/**` and `wfctl/specify/**` are present **in `site-packages`**. Deliberately *not* running `install-skills` here: this half must be able to run before US1 lands, when the command still clones — see T051 for the end-to-end half; verify by running the job on this branch
- [X] T041 [US4] Assert in that job that `site-packages/wfctl/specify/scripts/bash/*.sh` are mode `755` — the one failure mode that is invisible to the source-tree suite and breaks every speckit command at runtime ([research.md](./research.md) §1, B2); verify by `chmod -x` on one script locally, rebuilding, and confirming the check fails

  Both negative cases confirmed to fail: `chmod -x common.sh` → `NOT EXECUTABLE`,
  and narrowing the globs to `["agents/**/*", "specify/**/*"]` → `MISSING
  .workmux.yaml`. Neither reproduces without `rm -rf build dist wfctl.egg-info`
  first — `build_py` copies with `update=1` so a `chmod` (mtime untouched) never
  reaches the wheel, and `SOURCES.txt` re-includes what the narrowed glob dropped.
  CI checks out fresh and has neither cache. This also retires the SC-008 removal
  experiment T044 asks for; only the push remains.
- [X] T042 [US4] Remove the `GIT_TERMINAL_PROMPT: "0"` env block (`.github/workflows/ci.yml:70-71`) and its comment, now that the test it guarded is gone (T017); verify with a green `test` job
- [X] T043 [US4] Update the "Configure git for the test suite" comment (`.github/workflows/ci.yml:56-59`), which says the suite "builds throwaway repos as install sources and asserts on `--ref master`" — both untrue after T013–T016. The `git config` steps themselves stay: `conftest.py` still `git init`s destination repos
- [X] T051 [US4] Extend the `wheel` job with the end-to-end half T040 defers: run `wfctl install-skills` in a scratch git repo and diff the installed tree against `wfctl/agents`/`wfctl/specify`, asserting the `.sh` exec bit survived `shutil.copy2` into the repo (FR-018, SC-002). **Depends on US1** — until T020/T021 land, `install-skills` clones, so this would diff upstream `main` against the vendored copy: network-dependent, and green only while upstream happens to match; verify by running the job on this branch after T026

**Checkpoint**: T044 Validate US4 by pushing the branch and confirming all three jobs pass, then performing the SC-008 removal experiment once — merge gate. T040/T041's half of this gate is reachable from Phase 1; T051's is not.

---

## Phase 7: Polish & Cross-Cutting Concerns

- [X] T045 [P] Update `README.md` per the Documentation debt table in [plan.md](./plan.md) — 11 lines describing clone-and-pin provenance; verify by grepping for `wf-skills@main`, "pinned commit" and "upstream" and finding no stale claim
- [X] T046 [P] Update `wfctl/_manifest.py` docstring line 9, which describes layer entries as "objects with `items` and a pinned commit"; verify by reading the file
- [X] T047 [P] Add `wfctl/agents/` and `wfctl/specify/` to the mental model in `README.md`'s repo-layout section if one exists, and confirm `.gitignore:12-14` still ignores the *installed* `.agents/`/`.specify/` without touching the new package dirs; verify with `git status --porcelain` showing the vendored tree as tracked
- [X] T048 Run [quickstart.md](./quickstart.md) end to end on a clean machine state, including §5's no-op re-install against a repo installed from the same wf-skills tip; verify each step's stated expectation
- [X] T049 Bump `version` in `pyproject.toml` and confirm `doctor` reports the version-differs stale state against a repo installed by the prior version; verify with [quickstart.md](./quickstart.md) §4

  Bumped 0.14.0 → 0.15.0. **The stated check does not apply to this release** and
  the task's premise was wrong: v0.14.0 predates the vendored trees (`git ls-tree
  v0.14.0 wfctl/` lists no `agents/`), so a real 0.14.0 install cloned and left a
  record with no `content_hash` — the *unmeasurable* state, exercised in §4's last
  block. Against a 0.14.0 build carrying this branch's bundle, `doctor` reports
  `✓ base: skills current (wfctl 0.15.0)`, which is right: the bundle is byte-identical
  across the bump, so there is nothing to re-install. Version-differs needs the
  content to differ too — held by `test_doctor_reports_stale_across_versions`,
  which edits the bundle for real, and by §4's second block.

**Checkpoint**: T050 Validate the whole feature with `uv run pytest -q`, `uv run ruff check .`, `uv run mypy`, and all three CI jobs green — merge gate.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 1 (Setup)**: No dependencies. T004 gates everything — if the wheel ships nothing, later phases build on sand.
- **Phase 2 (Foundational)**: Depends on Phase 1. **Blocks all stories.**
- **Phase 3 (US1)**: Depends on Phase 2.
- **Phase 4 (US2)**: Depends on **US1**, not just Foundational — `doctor` reads the `content_hash` that US1's manifest write produces. This is the one genuine cross-story dependency.
- **Phase 5 (US3)**: Depends on US1 (the rewrite) and US2 (the warning branch it asserts).
- **Phase 6 (US4)**: Depends on Phase 1 only for T040–T041 — which is why they are scoped to `site-packages` and not to an `install-skills` run. T042–T043 and T051 depend on US1.
- **Phase 7 (Polish)**: Depends on all four stories.

### Deviation from the usual "stories are independent" shape

US2 and US3 are not independently deliverable here, and pretending otherwise would
produce a merge order that breaks `doctor`. The chain is US1 → US2 → US3, because
each consumes the manifest shape the previous one writes. US4 is the exception: it
is independent of all three and can be built in parallel from Phase 1 onward.

### Parallel Opportunities

- **T008, T009, T010** — three independent test files' worth of assertions in one new file
- **T013, T014, T015** — three different test files, no shared state
- **T027–T030** — four doctor states, independent assertions
- **T034–T036** — three migration tests
- **T040–T041** — can be built against the Phase 1 wheel while Phases 2–5 proceed; T051 cannot, it needs US1
- **T045, T046, T047** — three different files

## Parallel Example: User Story 2

```bash
# Four doctor states, written together before touching cli.py:
Task: "test_doctor_reports_up_to_date in tests/test_install_skills.py:462"
Task: "test_doctor_reports_stale_across_versions in tests/test_install_skills.py"
Task: "test_doctor_reports_stale_at_the_same_version in tests/test_install_skills.py"
Task: "test_doctor_skills_verdict_survives_an_offline_release_check in tests/test_install_skills.py"
```

---

## Implementation Strategy

### MVP (Phases 1–3)

Vendored content, working offline installs, deterministic results. This is the
defect in wfctl#43 fixed. `doctor` degrades to a warning on the skills line, which
is safe and self-explanatory, but the repo should not sit here long — US2 is what
makes vendoring's new failure mode visible.

### Incremental Delivery

1. **Phase 1** → the wheel carries the content. Zero behaviour change; safe to merge alone.
2. **Phase 2** → the seam exists. Still zero behaviour change.
3. **Phase 3 (US1)** → installs are offline and deterministic. **MVP.**
4. **Phase 4 (US2)** → `doctor` tells the truth again.
5. **Phase 5 (US3)** → old repos migrate cleanly.
6. **Phase 6 (US4)** → the regression that made all of this invisible can no longer happen.
7. **Phase 7** → docs stop lying.

Phases 1 and 2 are genuinely safe standalone merges, which is worth using: they
put the largest diff in a PR that changes no behaviour and can be reviewed by
looking at `pyproject.toml` and the wheel check. That diff is **64 files** —
what this repo's installed `.agents/` + `.specify/` holds today — plus the
trackers and configs the installed tree lacks; under 100, and the exact count
lands when T001 runs.

[delivery.md](./delivery.md) takes this up — PR 1 is Phases 1–2 plus T040/T041
pulled forward from Phase 6, since the packaging half of that job is what proves
the bundle ships. T051 stays behind with US1.

### Notes

- Commit after each task or logical group.
- Verify tests fail before implementing — particularly T027–T030, which are easy to write in a way that passes against the old code.
- The vendored tree is large; keep it in its own commit so the behavioural diff stays readable.
