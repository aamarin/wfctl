# Tasks: `wfctl install-config`

**Spec:** `specs/install-config-workmux/spec.md` · **Plan:** `plan.md`
**Branch:** install-config-workmux · **Date:** 2026-07-21

Two-repo change. wf-skills path is absolute (separate repo):
`/Users/andremarin/Development/wf-skills`. All wfctl paths are repo-relative.

User stories (from spec scenarios):
- **US1 (P1, MVP)** — seed the config into a fresh repo (write `.workmux.yaml`, gitignore `wt/`).
- **US2 (P2)** — clobber safety (refuse when file exists; `--force` overwrites).
- **US3 (P3)** — input validation (unknown name; not a git repo).

---

## Phase 1: Setup

- [ ] T001 [P] Create the shipped source config `/Users/andremarin/Development/wf-skills/.agents/configs/workmux/.workmux.yaml` with the repo-agnostic skeleton from plan.md (worktree_dir wt, session mode, agent+term windows, `agent: claude`, `pre_create` issue-number guard, commented `window_prefix`/`post_create`/`files`); verify with `python3 -c "import yaml,sys; yaml.safe_load(open(sys.argv[1]))" /Users/andremarin/Development/wf-skills/.agents/configs/workmux/.workmux.yaml`

## Phase 2: Foundational (blocks all stories)

- [ ] T002 Add the `install-config` command skeleton to `wfctl/cli.py`: `_CONFIG_SOURCES = {"workmux": ".agents/configs/workmux"}`, the `@app.command("install-config")` signature (name arg, `--force`, `--repo`, `--ref`), `get_repo_root()` guard, and the `git clone --depth=1 --branch <ref>` into a `TemporaryDirectory` (reuse the pattern from `install_skills_cmd`), resolving the source dir; verify with `uv run wfctl install-config --help`
- [ ] T003 Add the test scaffold `tests/test_install_config.py`: a `_make_wf_skills_repo_with_config` helper (throwaway git repo containing `.agents/configs/workmux/.workmux.yaml`) mirroring `test_tracker.py`'s `_make_wf_skills_repo_with_tracker`; verify with `uv run pytest tests/test_install_config.py -q` (collects, no cases yet)
- [ ] T004 Validate Foundational with `uv run wfctl install-config --help && uv run pytest tests/test_install_config.py -q` — merge gate

## Phase 3: US1 — Seed config (P1, MVP)

**Goal:** `install-config workmux` writes `.workmux.yaml` and ensures `wt/` is gitignored.
**Independent Test:** run against a clean temp repo → `.workmux.yaml` matches source and `.gitignore` contains `wt/`.

- [ ] T005 [US1] Implement the copy step in `install_config_cmd` (`wfctl/cli.py`): for each file under the source dir, write it to `repo_root/<relpath>` (mkdir parents), then print the success line; verify with tests from T007
- [ ] T006 [US1] Implement the workmux `.gitignore` post-step in `install_config_cmd` (`wfctl/cli.py`): guarded on `name == "workmux"`, append a `wt/` line to `.gitignore` only if absent (create the file if missing) — idempotent; verify with tests from T008
- [ ] T007 [P] [US1] Add happy-path test to `tests/test_install_config.py`: clean temp repo → `.workmux.yaml` written and byte-matches source; verify with `uv run pytest tests/test_install_config.py -q`
- [ ] T008 [P] [US1] Add `.gitignore` idempotency tests to `tests/test_install_config.py`: absent→created with `wt/`; present-without→appended; already-has→unchanged (no duplicate line); verify with `uv run pytest tests/test_install_config.py -q`
- [ ] T009 [US1] Validate US1 with `uv run pytest tests/test_install_config.py -q` — merge gate

## Phase 4: US2 — Clobber safety (P2)

**Goal:** an existing `.workmux.yaml` is never silently overwritten.
**Independent Test:** seed once, run again → refuses non-zero and file unchanged; with `--force` → overwrites.

- [ ] T010 [US2] Implement the clobber check in `install_config_cmd` (`wfctl/cli.py`): before copying, collect dests that already exist; if any and not `--force`, print a red error listing them + the `--force` hint and `raise typer.Exit(1)` (no writes); verify with tests from T011/T012
- [ ] T011 [P] [US2] Add refuse test to `tests/test_install_config.py`: pre-existing `.workmux.yaml`, no `--force` → exit != 0, file unchanged, output names the path; verify with `uv run pytest tests/test_install_config.py -q`
- [ ] T012 [P] [US2] Add `--force` test to `tests/test_install_config.py`: pre-existing `.workmux.yaml` + `--force` → overwritten with source content; verify with `uv run pytest tests/test_install_config.py -q`
- [ ] T013 [US2] Validate US2 with `uv run pytest tests/test_install_config.py -q` — merge gate

## Phase 5: US3 — Input validation (P3)

**Goal:** clear errors for a bad config name or a non-repo cwd.
**Independent Test:** `install-config nope` and running outside a git repo both exit non-zero with a helpful message.

- [ ] T014 [US3] Implement the name/repo guards in `install_config_cmd` (`wfctl/cli.py`): unknown `name` → red error listing `_CONFIG_SOURCES` keys, exit 1; not a git repo → red error, exit 1 (mirror `install_skills_cmd`); verify with tests from T015/T016
- [ ] T015 [P] [US3] Add unknown-name test to `tests/test_install_config.py`: `install-config nope` → exit != 0, output lists `workmux`; verify with `uv run pytest tests/test_install_config.py -q`
- [ ] T016 [P] [US3] Add not-a-git-repo test to `tests/test_install_config.py` → exit != 0; verify with `uv run pytest tests/test_install_config.py -q`
- [ ] T017 [US3] Validate US3 with `uv run pytest tests/test_install_config.py -q` — merge gate

## Phase 6: Polish

- [ ] T018 Full suite green: `uv run pytest -q`
- [ ] T019 Manual smoke in a throwaway git repo: `wfctl install-config workmux --repo file:///Users/andremarin/Development/wf-skills --ref main` → `.workmux.yaml` present + `wt/` in `.gitignore`; re-run → refuses; `--force` → overwrites — merge gate

---

## Dependencies

- Phase 1 (T001) and Phase 2 (T002–T004) precede all stories.
- US1 → US2 → US3 share `install_config_cmd`, so their **implementation** tasks
  (T005/T006, T010, T014) touch the same function and are sequential. Their
  **test** tasks (T007, T008, T011, T012, T015, T016) are `[P]` — different
  assertions in the same new test file, independent once the scaffold (T003)
  exists.
- Stories are independently testable and independently valuable; US1 alone is a
  shippable MVP.

## Parallel example

After T003, the six `[P]` test tasks can be authored together, then the
implementation branches filled in to make them pass (TDD-friendly).

## MVP

Phases 1–3 (through T009): a working `wfctl install-config workmux` that seeds
the file and gitignores `wt/`. Clobber safety and validation (US2/US3) harden it.
