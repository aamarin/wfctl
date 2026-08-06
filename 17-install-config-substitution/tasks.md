# Tasks: install-config substitution

**Input**: Design documents from `/specs/17-install-config-substitution/`
**Prerequisites**: plan.md, spec.md, research.md, contracts/cli.md, quickstart.md

**Tests**: Pure transforms get unit tests with no fixtures — that isolation is the
stated reason for injecting values rather than resolving them inside the module.
Command-level behavior gets integration tests through `CliRunner`. `project_name`
gets the real-git regression test it has never had. User Story 1 is verified
manually because its implementation lives in another repository.

**Organization**: Grouped by user story. US2 and US3 are fully independent and may
land in either order. US1 is delivered upstream and appears here only as a
dependency gate plus verification.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: US1, US2, US3 — maps to spec.md user stories
- Every implementation task names its verification path

## Path Conventions

Single Python package at repository root: `wfctl/`, `tests/`. Per plan.md.

---

## Phase 1: Setup

**Purpose**: Create the shared module both stories add functions to, so neither
story races the other to create the file.

- [X] T001 Create `wfctl/_workmux.py` with a module docstring stating the constraint that it imports nothing from `wfctl.*` and never calls `subprocess`, and create `tests/test_workmux.py` importing it; verify with `uv run pytest -q tests/test_workmux.py`
- [X] T002 Validate Phase 1 with `uv run ruff check . && uv run mypy` — merge gate

---

## Phase 2: Foundational

**Purpose**: Promote the existing project-name helper and give it the regression
test it has never had. Blocking for US3; a cross-cutting rename to a shared module,
so it is not filed under a single story.

**⚠️ MUST complete before Phase 5 (US3).**

- [X] T003 Rename `_project_name` → `project_name` in `wfctl/_paths.py:194` and update its sole caller at `wfctl/_paths.py:228`; verify with `uv run pytest -q`
- [X] T004 Add `test_project_name_from_a_worktree` to `tests/test_paths.py` — create a real linked worktree via `git worktree add`, assert `project_name(wt) == repo_root.name` and `!= "9-x"`; verify with `uv run pytest -q tests/test_paths.py -k project_name`
- [X] T005 Validate Phase 2 with `uv run pytest -q && uv run mypy` — merge gate

**Checkpoint**: `project_name` is public and proven correct from inside a worktree —
the `--show-toplevel` trap can no longer regress silently.

---

## Phase 3: User Story 1 — Seeded repos protect their artifacts (P1)

**Goal**: A freshly seeded repo archives its planning artifacts at worktree teardown
instead of destroying them.

**Delivered by wf-skills#8, not this branch.** The change is a template edit in a
separate repository. No file in this repo changes. These tasks are the dependency
gate and the acceptance verification.

**Independent Test**: Seed a scratch repo, create a worktree holding a spec dir,
remove it, and confirm the artifacts survive in the state dir.

### Verification

- Manual only — the implementation is external and cannot be unit-tested from here.
- Baseline for comparison: `~/.local/state/wfctl/pfms/` currently holds 22 branches
  and 0 archives.

- [X] T006 [US1] Confirm wf-skills#8 has landed by inspecting `.agents/configs/workmux/.workmux.yaml:54` on wf-skills `main`; verify with `git ls-remote https://github.com/aamarin/wf-skills main` plus a fresh clone showing `pre_remove` invoking `archive-story`
- [X] T007 [US1] Manually verify end-to-end: `wfctl install-config workmux` in a scratch repo, `wm add 999-probe -b`, place a file at `specs/999-probe/spec.md`, `wm remove 999-probe`; verify the artifacts appear under `~/.local/state/wfctl/<project>/999-probe/archive/` with a generated README index
- [X] T008 [US1] Manually verify teardown is never blocked: repeat T007 with `wfctl` removed from `PATH`; verify the worktree is still removed and no error surfaces — merge gate

**Checkpoint**: US1 acceptance confirmed. Blocked on wf-skills#8; does not block
Phases 4 or 5.

---

## Phase 4: User Story 2 — Existing repos are warned and offered a fix (P2)

**Goal**: `wfctl doctor` reports a repo whose teardown hook is missing and offers a
two-line fix on confirmation, leaving every other line untouched.

**Independent Test**: Point `doctor` at a config whose `pre_remove` is disabled,
confirm the prompt, and verify the change is limited to that one hook.

### Verification

- Unit: `tests/test_workmux.py` for both predicates and the transform.
- Integration: `tests/test_remaining_commands.py` for both TTY paths, via
  monkeypatching `wfctl.cli._interactive`.
- Manual: `git diff --stat` against the real `pfms` config must show
  `2 insertions(+), 1 deletion(-)`.

- [X] T009 [P] [US2] Implement `pre_remove_wired(text) -> bool` in `wfctl/_workmux.py` — true only when a **non-comment** line contains `archive-story`; verify with `uv run pytest -q tests/test_workmux.py -k pre_remove_wired`
- [X] T010 [P] [US2] Add unit tests for `pre_remove_wired` in `tests/test_workmux.py` covering wired, `pre_remove: []`, and comment-only mention per contracts/cli.md §3; verify with `uv run pytest -q tests/test_workmux.py -k pre_remove_wired`
- [X] T011 [US2] Implement `wire_pre_remove(text) -> str | None` in `wfctl/_workmux.py` — patch only a line matching `^pre_remove:\s*\[\]\s*$`, return `None` for every other shape; verify with `uv run pytest -q tests/test_workmux.py -k wire_pre_remove`
- [X] T012 [US2] Add unit tests for `wire_pre_remove` in `tests/test_workmux.py` asserting the `[]` case patches one line into two, and that a custom list and an absent key both return `None`; verify with `uv run pytest -q tests/test_workmux.py -k wire_pre_remove`
- [X] T013 [US2] Add the lint to `doctor_cmd` in `wfctl/cli.py` — skip silently when `.workmux.yaml` is absent, warn naming the consequence and the resolved archive destination when the hook is unwired, and leave `exit_code` untouched per the `⚠ no pinned commit` precedent at `cli.py:1253`; verify with `uv run pytest -q tests/test_remaining_commands.py -k doctor`
- [X] T014 [US2] Add the interactive retrofit to `doctor_cmd` in `wfctl/cli.py` — guard with `_interactive()` (`cli.py:658`), prompt via `typer.confirm` following the tracker precedent at `cli.py:734`, apply `wire_pre_remove` on confirmation, print manual instructions when it returns `None`, and swallow `OSError` on write; verify with `uv run pytest -q tests/test_remaining_commands.py -k doctor`
- [X] T015 [US2] Add behavior integration tests to `tests/test_remaining_commands.py` covering: non-interactive warns and leaves the file byte-identical, interactive-confirmed patches exactly the hook, custom `pre_remove` refuses and leaves the file unchanged, absent `.workmux.yaml` is silent, and a declined prompt is not recorded; verify with `uv run pytest -q tests/test_remaining_commands.py -k doctor`
- [X] T015a [US2] Add output-content and negative assertions to `tests/test_remaining_commands.py` — these cover requirements that regress silently because nothing fails when they break; verify with `uv run pytest -q tests/test_remaining_commands.py -k doctor`
  - the warning names the resolved archive destination (FR-012a)
  - the non-interactive report names how to reach the fix (FR-013a)
  - `result.exit_code == 0` in every warning case (FR-016)
  - a config with `pre_remove` already wired but `<project>` still unsubstituted produces **no** output — doctor never reports the prefix (FR-013b)
- [X] T016 [US2] Manually verify against the real config: run `wfctl doctor` in `~/Development/pfms`, accept the prompt, then confirm `git diff --stat .workmux.yaml` reports `2 insertions(+), 1 deletion(-)` and that `window_prefix: 'pfms__'`, the `post_create` port arithmetic, and the `deploy` window are all unchanged
- [X] T017 Validate Phase 4 with `uv run pytest -q && uv run ruff check . && uv run mypy` — merge gate

**Checkpoint**: US2 independently deliverable. `pfms` is protected, and the change
is provably two lines.

---

## Phase 5: User Story 3 — Session names carry the project (P3)

**Goal**: Seeding writes the real project name into the session prefix, active and
correct from a worktree, with no placeholder left behind.

**Depends on Phase 2** (`project_name`).

**Independent Test**: Seed a scratch repo and confirm the prefix holds the project
name; repeat from inside a linked worktree and confirm it is still the project's
name, not the branch handle.

### Verification

- Unit: `tests/test_workmux.py`, no fixtures.
- Integration: `tests/test_install_config.py` end-to-end through `CliRunner`.
- Manual: seed a scratch repo and grep the result.

- [X] T018 [P] [US3] Implement `tmux_safe(name) -> str` in `wfctl/_workmux.py` as `re.sub(r"[.:]", "_", name)` — exactly the two characters tmux rewrites per research R3; verify with `uv run pytest -q tests/test_workmux.py -k tmux_safe`
- [X] T019 [P] [US3] Add unit tests for `tmux_safe` in `tests/test_workmux.py` asserting `.` and `:` are rewritten and that spaces, `$`, `-`, `_` survive verbatim per contracts/cli.md §3; verify with `uv run pytest -q tests/test_workmux.py -k tmux_safe`
- [X] T020 [US3] Implement `patch_seed(text, *, agent, project) -> str` in `wfctl/_workmux.py` — rewrite `^\s*#?\s*window_prefix:` to an **active** `window_prefix: '<project>__'` with `'` escaped by doubling, and move the `agent:` logic verbatim from `wfctl/cli.py:1138-1146`; verify with `uv run pytest -q tests/test_workmux.py -k patch_seed`
- [X] T021 [US3] Add unit tests for `patch_seed` in `tests/test_workmux.py` covering active prefix substitution, apostrophe escaping, resolved agent, `None` agent leaving `# agent: claude`, and an absent key leaving the line untouched — relocating the agent assertions currently at `tests/test_install_config.py:148`; verify with `uv run pytest -q tests/test_workmux.py -k patch_seed`
- [X] T022 [US3] Wire the substitution into `install_config_cmd` in `wfctl/cli.py` — call `project_name`, then `tmux_safe`, print the `ℹ` notice only when sanitizing changed the name, then call `patch_seed`; verify with `uv run pytest -q tests/test_install_config.py`
- [X] T023 [US3] Add the post-write placeholder check to `install_config_cmd` in `wfctl/cli.py` — warn if the literal `<project>` survives anywhere in the file, naming the remediation line with the resolved name, and never flag `<agent>`; verify with `uv run pytest -q tests/test_install_config.py -k placeholder`
- [X] T024 [US3] Add integration tests to `tests/test_install_config.py` covering the real project name landing active in `window_prefix`, the sanitize notice appearing only when the name changed, the placeholder warning firing when the fixture template omits `window_prefix`, and — the assertion that guards a silent regression — that a template retaining `<agent>` produces **no** warning, since `<agent>` is the worktree tool's own runtime token (FR-009c); verify with `uv run pytest -q tests/test_install_config.py`
- [X] T025 [US3] Manually verify from a worktree: run `wfctl install-config workmux` inside a linked worktree of a scratch repo and confirm `grep window_prefix .workmux.yaml` shows the project name, not the branch handle
- [X] T026 Validate Phase 5 with `uv run pytest -q && uv run ruff check . && uv run mypy` — merge gate

**Checkpoint**: US3 independently deliverable. No placeholder ships, and a worktree
seed produces the same name as a root-checkout seed.

---

## Phase 6: Polish & Cross-Cutting

- [X] T027 [P] Confirm no runtime dependency was added — `wfctl/_workmux.py` must import only from the standard library; verify with `grep -n "^import\|^from" wfctl/_workmux.py` showing only `re`, and `grep -c "" <<< "$(sed -n '/^dependencies/,/]/p' pyproject.toml)"` unchanged
- [X] T028 [P] Confirm `wfctl/_workmux.py` calls no `subprocess` and imports nothing from `wfctl.*`; verify with `grep -n "subprocess\|from wfctl\|import wfctl" wfctl/_workmux.py` returning nothing
- [X] T029 Run the full suite and both linters; verify with `uv run pytest -q && uv run ruff check . && uv run mypy` — expect ≥227 tests plus this feature's additions, all passing — merge gate

---

## Dependencies

```
Phase 1 (Setup)
   │
   ├──────────────┬─────────────────┐
   ▼              ▼                 ▼
Phase 2      Phase 4 (US2)     Phase 3 (US1)
(Foundational)    │            [blocked: wf-skills#8]
   │              │                 │
   ▼              │                 │
Phase 5 (US3)     │                 │
   │              │                 │
   └──────────────┴─────────────────┘
                  ▼
            Phase 6 (Polish)
```

- **US2 and US3 are independent.** Either may land first.
- **US3 depends on Phase 2**; US2 does not.
- **US1 blocks nothing.** It is external and its verification can run whenever
  wf-skills#8 lands.

## Parallel Opportunities

**Within Phase 4 (US2)**: T009 and T010 touch different files and may run in
parallel. T011 must follow T009 (same file).

**Within Phase 5 (US3)**: T018 and T019 touch different files and may run in
parallel. T020 must follow T018 (same file).

**Across phases**: Phase 4 and Phase 5 may proceed concurrently once Phase 1 and
Phase 2 are complete — they touch disjoint functions in `_workmux.py` and disjoint
commands in `cli.py`.

**Phase 6**: T027 and T028 are independent greps and may run in parallel.

## Implementation Strategy

**MVP is User Story 2, not User Story 1.** US1 is the highest-value story but its
implementation is upstream — this branch cannot deliver it. The smallest complete
increment this branch can ship is Phases 1, 2 and 4: `wfctl doctor` reports and
fixes an unprotected repo. That alone protects `pfms`, which is exposed today.

Recommended order:

1. **Phases 1–2** — module scaffold plus the `project_name` promotion and its
   missing regression test.
2. **Phase 4 (US2)** — ship the retrofit. Run it once against `pfms`. This is the
   increment with real-world consequence.
3. **Phase 5 (US3)** — the prefix substitution. Cosmetic by the spec's own value
   ranking, and safe to land later.
4. **Phase 3 (US1)** — verify once wf-skills#8 lands.
5. **Phase 6** — polish gates.

**Task count**: 30 total — Setup 2, Foundational 3, US1 3, US2 10, US3 9, Polish 3.

T015a was added after `/speckit.analyze` found five requirements named in task
prose but asserted by no test — four of them negative or output-content
requirements, which regress without failing anything. See
`checklists/analysis-report.md` findings C1–C5.
