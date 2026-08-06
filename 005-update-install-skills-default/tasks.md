# Tasks: update-install-skills-default

**Input**: Design documents from `/specs/005-update-install-skills-default/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/cli.md, quickstart.md

**Tests**: Every implementation task names its verification path. The suite is
`uv run pytest`; 194 cases pass before this feature begins. New cases land in
`tests/test_install_skills.py` unless noted.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: US1–US4, mapping to the user stories in spec.md

### A note on parallelism

Nearly every task touches `wfctl/cli.py` or `tests/test_install_skills.py`. Two
tasks editing the same file are not parallel, so `[P]` appears only where the
files genuinely differ (README, `pyproject.toml`). This feature is a sequential
refactor of one module, not a fan-out.

## Path Conventions

Single Python package: `wfctl/` and `tests/` at the repository root.

---

## Phase 1: Setup

**Purpose**: Establish the baseline the whole feature is measured against.

- [x] T001 Record the green baseline: run `uv run pytest -q` and confirm 194 passing before any edit
- [x] T002 Capture today's Claude layout as the regression reference. `wfctl` on PATH is installed from this worktree, so the comparison build must come from the remote: `uvx --from git+https://github.com/aamarin/wfctl.git@master wfctl install-skills --agent claude` in a scratch repo, saving `find . -path ./.git -prune -o -print | sort` to a scratch file; verify at T029 by diffing the new code's output against it (SC-007 requires byte-for-byte reproduction)

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: The layer split itself. Every user story reads from these structures.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete.

- [x] T003 Add the disjoint-destination test to `tests/test_install_skills.py`: assert every destination across `_BASE_TARGETS` and all `_AGENT_TARGETS` entries is unique — covers FR-004, SC-006; verify with `uv run pytest -q -k disjoint` and confirm it FAILS against the current overlapping dicts before T004
- [x] T004 Extract `_BASE_TARGETS` in `wfctl/cli.py` (`.agents/skills` → `.agents/skills`, `.agents/commands` → `.agents/commands`) and strip agent-agnostic destinations from every `_AGENT_TARGETS` entry so each owns a unique root; verify with the T003 test now passing
- [x] T005 Update the plan loop in `install_skills_cmd` to iterate `[*_BASE_TARGETS, *targets, *_RUNTIME_TARGETS]` so an agent layer always installs on top of the base layer; verify with `uv run pytest -q tests/test_install_skills.py`
- [x] T006 Write the base layer to a `base` manifest key alongside per-agent entries in `wfctl/cli.py`; verify with a new test asserting `list(manifest) == ["base"]` after a bare install
- [x] T007 Treat `base` as a reserved key everywhere agents are enumerated in `wfctl/cli.py` (`cli.py:761`, `cli.py:944`), matching how `tracker` is already skipped; verify with `uv run pytest -q tests/test_remaining_commands.py`
- [x] T008 Delete the stale known-limitation comment above `_AGENT_TARGETS` in `wfctl/cli.py` — the collision it documents is now structurally impossible, and T003 enforces that; verify by grepping that no comment claims agents share `.agents/skills`
- [x] T009 Validate Phase 2 with `uv run pytest -q` — merge gate

**Checkpoint**: Layers are disjoint and recorded separately. Stories can begin.

> **Deviation from plan, recorded during implementation.** T019 (union
> `prior_items` across manifest entries) and T020 (uninstall touches only its
> own layer) were planned for Phase 4 but had to land here. The moment T006
> moved `.agents/*` from the agent entry to `base`, a re-install saw those
> paths as foreign and aborted at the overwrite prompt — two existing tests
> went red. The plan's Complexity Tracking predicted the cause ("ownership
> moves between entries") but scheduled the fix a phase too late: it is a
> prerequisite of the layer split, not a follow-up to it.

---

## Phase 3: User Story 1 - Install without declaring an agent (Priority: P1) 🎯 MVP

**Goal**: A bare `wfctl install-skills` writes only agent-agnostic content, reports what it did in countable terms, and names the opt-in commands.

**Independent Test**: Run `wfctl install-skills` in a scratch repo; confirm no assistant-specific directory exists and the manifest lists only `.agents/*` and `.specify/*` paths.

**Verification**:

- Automated: `uv run pytest -q tests/test_install_skills.py`
- Manual: `quickstart.md` §1
- Evidence: `.wf-skills-manifest.json` contains a `base` entry and no agent entry; `.claude/` absent

### Tests for User Story 1 ⚠️

> Write these first; confirm they fail against the current default.

- [x] T010 [US1] Test in `tests/test_install_skills.py`: a bare install creates `.agents/skills` and `.agents/commands` and no `.claude/` — covers FR-001, FR-002, SC-001
- [x] T011 [US1] Test in `tests/test_install_skills.py`: the install summary reports per-layer, per-kind counts and never a single combined total; assert a zero-item layer is omitted rather than printed as `0` (`--agent none` produces no second line) — covers FR-011, SC-004

### Implementation for User Story 1

- [x] T012 [US1] Change the `--agent` default from `"claude"` to `"none"` in `install_skills_cmd` in `wfctl/cli.py` and add `"none": []` to `_AGENT_TARGETS`; verify with the T010 test
- [x] T013 [US1] Replace the `✓ Installed N item(s)` line in `wfctl/cli.py` with the per-layer summary from `contracts/cli.md` (`base 25 skills · 23 commands · 8 runtime · 1 tracker`), following that file's counting rules: classify target-derived items by source directory, count the tracker config separately since it is appended outside the targets loop, and omit any layer or kind with zero items; verify with the T011 test
- [x] T014 [US1] Print the opt-in hint naming `--agent claude|bob|copilot` after an install that added no agent layer, in `wfctl/cli.py`; verify with a test asserting the hint appears bare and is absent with `--agent claude` — covers FR-010
- [x] T015 [US1] Update the existing cases in `tests/test_install_skills.py` that assume the old default installs `.claude/commands`; verify with `uv run pytest -q tests/test_install_skills.py`
- [x] T016 [US1] Validate User Story 1 with `uv run pytest -q` and `quickstart.md` §1 — merge gate

**Checkpoint**: The default flip is complete and demonstrable on its own.

---

## Phase 4: User Story 2 - Upgrade an existing repo without alarm (Priority: P2)

**Goal**: A repo installed under the old default upgrades silently — no overwrite prompt, no backups of wfctl's own content — while genuine user files are still protected.

**Independent Test**: Build a manifest in the old shape (`.agents/skills/*` recorded under `claude`), run the install, and confirm no prompt and no new backup entries.

**Verification**:

- Automated: `uv run pytest -q tests/test_install_skills.py`
- Manual: `quickstart.md` §2 — the absence of a `ℹ Backed up N pre-existing file(s)` line
- Evidence: `.wf-skills-backup/` unchanged across the upgrade

### Tests for User Story 2 ⚠️

- [x] T017 [US2] Test in `tests/test_install_skills.py`: a manifest in the old shape upgrades with no overwrite prompt and no new backups — covers FR-005, SC-002; must FAIL before T019
- [x] T018 [US2] Test in `tests/test_install_skills.py`: a file the user authored at a destination path is still detected, backed up, and restorable — covers FR-006, and guards T019 from over-relaxing detection

### Implementation for User Story 2

- [x] T019 [US2] **(pulled into Phase 2 — blocker, see note)** Build `prior_items` from every manifest entry rather than only `manifest[agent]` in `wfctl/cli.py`; verify with T017 and T018 — this is the Complexity Tracking exception recorded in plan.md
- [x] T020 [US2] Confirm `uninstall-skills --agent claude` removes only `.claude/*` and leaves `.agents/skills` intact in `wfctl/cli.py`, adjusting the existing uninstall test in `tests/test_install_skills.py` for the changed behavior — covers FR-007. Sits in US2 rather than US3 because it is the same ownership change as T019: both prove that the base layer's paths stop belonging to the `claude` entry
- [x] T021 [US2] Validate User Story 2 with `uv run pytest -q` and `quickstart.md` §2 — merge gate

**Checkpoint**: Existing repos upgrade invisibly; new repos are unaffected.

---

## Phase 5: User Story 3 - Add support for a specific assistant (Priority: P3)

**Goal**: Each supported assistant installs its own layer in one command; an assistant with no repo-local path is told so and still gets a working install.

**Independent Test**: Run the install once per assistant in separate scratch repos and confirm each produces only its own layout.

**Verification**:

- Automated: `uv run pytest -q tests/test_install_skills.py`
- Manual: `quickstart.md` §3, §4, §5 — and §7, the live Copilot discovery check
- Evidence: `diff -r .agents/skills .github/skills` is empty; `--agent codex` exits 0

### Tests for User Story 3 ⚠️

- [x] T022 [US3] Test in `tests/test_install_skills.py`: `--agent copilot` writes `.github/skills/<name>/SKILL.md` byte-identical to the source, in one command, on a repo with no prior install — covers FR-003, SC-003
- [x] T023 [US3] Test in `tests/test_install_skills.py`: `--agent codex` exits 0, installs the base layer, writes no `codex` manifest entry, and mentions `AGENTS.md` — covers FR-008
- [x] T024 [US3] Test in `tests/test_install_skills.py`: an unrecognised `--agent` exits non-zero listing accepted names, and `--agent none` still resolves — covers FR-009

### Implementation for User Story 3

- [x] T025 [US3] Add `"copilot": [(".agents/skills", ".github/skills")]` to `_AGENT_TARGETS` in `wfctl/cli.py`; verify with T022
- [x] T026 [US3] Add a notice map for assistants with no repo-local path, resolving `codex` to an empty layer and printing why before the install proceeds, in `wfctl/cli.py`; verify with T023
- [x] T027 [US3] Confirm the unknown-agent branch still lists accepted names now that `_AGENT_TARGETS` includes notice-only entries, in `wfctl/cli.py`; verify with T024
- [x] T028 [US3] Run the live Copilot discovery check in `quickstart.md` §7 and record the outcome in `research.md`; if it fails, stop and re-plan the `copilot` entry against the `.agent.md` fallback before continuing
- [x] T029 [US3] Validate User Story 3 with `uv run pytest -q` and `quickstart.md` §3–§5 — merge gate

**Checkpoint**: All three assistants and the notice-only case work independently.

---

## Phase 6: User Story 4 - Choose an issue tracker deliberately (Priority: P4)

**Goal**: The tracker prompt keeps working after the layer split.

**Already implemented** in commit `b636356` on this branch. This phase is regression and documentation only — no new behavior.

**Independent Test**: Run the install interactively answering both ways, then with stdin redirected; confirm the prompt fires exactly once and never without a tty.

**Verification**:

- Automated: `uv run pytest -q tests/test_install_skills.py -k tracker`
- Manual: `quickstart.md` §1, §6
- Evidence: no `.agents/trackers/` after a declined or non-interactive install

- [x] T030 [US4] Confirm the tracker prompt still fires only on a first interactive install now that the manifest has a `base` key — the `"tracker" not in manifest` guard must not be confused by the new key — covers FR-012; verify with the existing `test_install_skills_prompts_for_tracker`
- [x] T031 [US4] Confirm a non-interactive install still writes no tracker after the layer split — covers FR-013; verify with the existing `test_install_skills_no_tracker_without_a_human`
- [x] T032 [US4] Confirm declining still prints both routes back (the `--tracker github` one-liner and the `/scaffold-tracker` flow) — covers FR-014; verify with the `("n\n", False)` case of `test_install_skills_prompts_for_tracker`, which asserts both `--tracker github` and `/scaffold-tracker` appear in the output
- [x] T033 [US4] Confirm an existing tracker choice and local edits to its config survive an install that now also writes a `base` entry — covers FR-015; verify with the existing `test_install_skills_keeps_existing_tracker_config`
- [x] T034 [US4] Confirm the tracker config is still exempt from `.gitignore` while base-layer paths are added, in `wfctl/cli.py`; verify with the existing `test_install_skills_does_not_gitignore_tracker_config`
- [x] T035 [US4] Validate User Story 4 with `uv run pytest -q` and `quickstart.md` §6, confirming no `.agents/trackers/` after a declined or non-interactive install — covers SC-005 — merge gate

**Checkpoint**: Tracker consent survives the restructure.

---

## Phase 7: Polish & Cross-Cutting Concerns

- [x] T036 [P] Rewrite the install section of `README.md` for the new default, the opt-in commands, the codex notice, and the changed uninstall behavior — covers FR-016; verify by reading it against `contracts/cli.md`
- [x] T037 [P] Bump the version in `pyproject.toml` and `wfctl/__init__.py` as a minor release, with the breaking default called out; verify with `uv run wfctl --version`
- [x] T038 Update `.agent/spec.md` and `specs/005-update-install-skills-default/research.md` with the T028 Copilot outcome so the assumption is closed rather than open; verify by grepping that no artifact still calls it unvalidated
- [x] T039 Validate the whole feature with `uv run pytest -q` and a full `quickstart.md` pass — merge gate

---

## Dependencies

### Phase Order

- **Setup (Phase 1)** → **Foundational (Phase 2)** → user stories → **Polish (Phase 7)**
- Foundational blocks everything: US1–US4 all read `_BASE_TARGETS` / `_AGENT_TARGETS`.

### User Story Dependencies

- **US1 (P1)**: after Phase 2. No dependency on another story.
- **US2 (P2)**: after Phase 2. Independent of US1, but its value is only visible once the default has flipped — demo it after US1.
- **US3 (P3)**: after Phase 2. Independent.
- **US4 (P4)**: after Phase 2. Already implemented; verifies the restructure didn't break it.

### Within Each Story

- Tests before implementation, and confirmed failing first.
- T019 (union detection) must land before T020's uninstall assertions are meaningful.
- T028 gates T038: the Copilot check's outcome is what closes the assumption.

## Parallel Opportunities

Deliberately few. `wfctl/cli.py` and `tests/test_install_skills.py` are edited by nearly every task, so most work is strictly sequential.

- T036 and T037 are `[P]` — `README.md` and `pyproject.toml` share no file with anything else.
- T001 and T002 in Setup can overlap.
- Across stories, US2 / US3 / US4 could be developed by different people **only** after Phase 2 lands and only if they keep to separate regions of `cli.py`; in practice a single implementer is simpler here.

## Implementation Strategy

### MVP (User Story 1 only)

1. Phase 1 Setup
2. Phase 2 Foundational — the layer split
3. Phase 3 US1 — default flip, summary, hint
4. **Stop and validate**: bare install writes only `.agents/*`; `quickstart.md` §1

That alone closes issue #5's primary complaint. US2 is required before release, though — shipping the default flip without the union check makes every existing repo's first upgrade look destructive.

### Incremental Delivery

1. Setup + Foundational → layers disjoint
2. + US1 → default flipped (MVP)
3. + US2 → upgrades silent (**required before release**)
4. + US3 → copilot, codex, unknown-agent
5. + US4 → tracker regression confirmed
6. + Polish → docs, version, assumption closed

## Notes

- The plan's Complexity Tracking entry maps to exactly one task, T019. If that task ever looks unnecessary, re-read why ownership moves between manifest entries in this version.
- T028 is the only task that can invalidate the design. It has a defined fallback (`.agent.md` transform from issue #5) that changes only the `copilot` entry and adds an extras hook.
- Commit after each task or logical group; stop at any checkpoint to validate a story independently.
- Do not decide PR boundaries here — `/speckit.decompose` owns that.
