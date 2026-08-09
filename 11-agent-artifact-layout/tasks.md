# Tasks: Agent Artifact Layout

**Branch**: `11-agent-artifact-layout` | **Date**: 2026-08-05
**Input**: [plan.md](./plan.md), [spec.md](./spec.md), [research.md](./research.md), [data-model.md](./data-model.md), [contracts/cli.md](./contracts/cli.md), [quickstart.md](./quickstart.md)

## Format: `[ID] [P?] [Story] Description`

- **[P]**: parallelizable — different files, no dependency on an incomplete task
- **[US1]/[US2]/[US3]**: the user story this task serves; setup, foundational and polish tasks carry none

## Path Conventions

Two repositories. Paths are written relative to each repository's root and
prefixed with the repository name, because the ordering constraint runs between
them:

- `wfctl/…` — the **consumer** side. Reads artifacts. **Lands first.**
- `wf-skills/…` — the **producer** side. Writes artifacts. Lands second.

Landing the producer first strands step inference at brainstorm indefinitely
(`_pipeline.py:75` would look for a file nothing writes). This is the single
hard ordering constraint in the feature.

---

## Phase 1: Setup (Shared Infrastructure)

- [X] T001 Capture the pre-change baseline recorded in quickstart.md — run `git -C wf-skills grep -cE '\.agent/'` and `grep -rn '"\.agent"\|\.agent/' wfctl/wfctl/ wfctl/tests/`, and paste both outputs into the implementation PR description; verify with the expected counts in quickstart.md ("Known-good baseline": 21 across 6 files, 4 source + 4 test)
- [X] T002 [P] Confirm the tooling test suite is green before any edit — `cd wfctl && uv run pytest -q`; verify exit code 0
- [X] T003 Validate setup with both baseline commands reporting the documented counts and a green suite — merge gate

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: All consumer-side changes. Every user story below depends on these
landing first, because each one changes a path the tooling reads.

- [X] T004 Add `("design.md", "1-design.md")` as the first entry of `_SPEC_MAP` in `wfctl/wfctl/_archive.py`; verify with `uv run pytest tests/test_archive_story.py -q`
- [X] T005 Delete the `_DESIGN_DOC` constant and the branch in `_plan()` that appends it (`wfctl/wfctl/_archive.py:26`, `:98-100`); verify with `grep -c _DESIGN_DOC wfctl/wfctl/_archive.py` returning 0
- [X] T006 Point step inference at the new path — replace `repo_root / ".agent" / "spec.md"` with the spec-dir-relative `design.md` in `wfctl/wfctl/_pipeline.py:75`; verify with `uv run pytest tests/test_start_atomic.py -q`
- [X] T007 [P] Update the fixtures that build the old path in `wfctl/tests/conftest.py:30,39`; verify with `uv run pytest -q`
- [X] T008 [P] Update the old-path fixture in `wfctl/tests/test_archive_story.py:47`; verify with `uv run pytest tests/test_archive_story.py -q`
- [X] T009 [P] Update the old-path fixture in `wfctl/tests/test_start_atomic.py:17`; verify with `uv run pytest tests/test_start_atomic.py -q`
- [X] T010 Add a regression test asserting the archive's numbered sequence is contiguous from `1-design.md` with nothing the map should have named left under `extra/`, in `wfctl/tests/test_archive_story.py`; verify the test fails against the pre-T004 code and passes after
- [X] T011 [P] Update the docstrings naming the old path in `wfctl/wfctl/_archive.py:3` and `wfctl/wfctl/cli.py:280`; verify with `grep -rn '\.agent/' wfctl/wfctl/` returning nothing
- [X] T012 Add the skew diagnostic to `doctor_cmd` in `wfctl/wfctl/cli.py` — when a `.agent/` directory exists in the repo, emit a `⚠` line naming the superseded path and the resolving action, per contracts/cli.md; verify with a new test asserting the warning appears with the directory present and is absent without it
- [X] T013 Validate the foundation with `cd wfctl && uv run pytest -q` green and `grep -rn '"\.agent"\|\.agent/' wfctl/wfctl/ wfctl/tests/` returning **only** the T012 deprecation lint and its tests — merge gate

  **Retained exception.** As first written this gate demanded the grep return
  nothing, which T012 makes impossible: a lint that detects `.agent/` must name
  `.agent/`. The criterion is amended to name the survivor, so it is achievable
  as written. What must return nothing is any reference that *reads or writes*
  the path as an artifact location — verify with
  `grep -rn '\.agent/spec\.md\|"\.agent" /' wfctl/wfctl/ wfctl/tests/`.

**Checkpoint**: The tooling reads the new layout and warns about the old one. The
producer side can now change without stranding inference.

---

## Phase 3: User Story 1 - One directory holds a branch's artifacts (Priority: P1) 🎯 MVP

**Goal**: Every per-branch artifact lives in `specs/<branch>/`. `.agent/` is
never created.

**Independent Test**: Run `/brainstorm` through `/speckit.plan` on a fresh
branch; confirm no `.agent/` appears and every artifact lands in
`specs/<branch>/`.

**Verification**:

- `git -C wf-skills grep -nE '\.agent/'` returns nothing
- `wfctl status` on a branch with a design document reports `brainstorm ●`
- Archive of a mid-pipeline worktree contains `1-design.md` with no gaps

### Implementation for User Story 1

- [ ] T014 [US1] Repoint the 9 design-document references in `wf-skills/.agents/skills/speckit-specify/SKILL.md` (`:18`, `:23`, `:26`, `:33`, `:39`, `:42`, `:43`, `:48`, `:50`) to `specs/<branch>/design.md`; verify with `git grep -cE '\.agent/' -- .agents/skills/speckit-specify/SKILL.md` returning 0
- [ ] T015 [P] [US1] Repoint the pipeline diagram and prose in `wf-skills/.agents/skills/speckit-delivery-plan/SKILL.md:23,28`; verify with `git grep -cE '\.agent/' -- .agents/skills/speckit-delivery-plan/SKILL.md` returning 0
- [ ] T016 [P] [US1] Repoint the brief location and the escalation instruction in `wf-skills/.agents/skills/agent-brief/SKILL.md:18,36,66`, renaming `checkpoint.md` to `escalation.md` per research R3; verify with `git grep -nE '\.agent/|checkpoint\.md' -- .agents/skills/agent-brief/SKILL.md` returning nothing
- [ ] T017 [P] [US1] Repoint the description in `wf-skills/.agents/commands/speckit.brief.md:3`; verify with `git grep -cE '\.agent/' -- .agents/commands/speckit.brief.md` returning 0
- [ ] T018 [US1] Repoint the two design-document references in `wf-skills/.agents/commands/brainstorm.md` frontmatter — the `description` (`:3`) and the handoff `prompt` (`:7`) — to `specs/<branch>/design.md`; verify with `git grep -nE '\.agent/' -- .agents/commands/brainstorm.md` showing only the lines owned by T020 and T024 remaining
- [ ] T018a [US1] Add `mkdir -p specs/<branch>/` to `/brainstorm` before it writes, per FR-012 (`wf-skills/.agents/commands/brainstorm.md`); verify by running `/brainstorm` in a worktree with no spec directory and confirming the design document is written rather than erroring
- [ ] T019 [US1] Validate User Story 1 — `git -C wf-skills grep -nE '\.agent/'` returns nothing, and `wfctl status` on a branch with `specs/<branch>/design.md` reports `brainstorm ●` — merge gate

**Checkpoint**: The artifact move is complete and independently demonstrable.

---

## Phase 4: User Story 2 - Project overrides survive being committed (Priority: P2)

**Goal**: A maintainer's instructions live at `AGENTS.md`, committed, and
`/brainstorm` reads them.

**Independent Test**: In a repo with a committed root `AGENTS.md` carrying a
distinguishing instruction, run `/brainstorm` and confirm it is applied.

**Verification**:

- `/brainstorm` in a repo with `AGENTS.md` applies its content
- `/brainstorm` in a repo without one proceeds silently and creates nothing
- The file survives a fresh clone with no local setup step

### Implementation for User Story 2

- [ ] T020 [US2] Repoint the override read in `wf-skills/.agents/commands/brainstorm.md:11` from `.agent/AGENT.md` to the repository-root `AGENTS.md`, keeping the read-if-present semantics required by FR-005; verify by running `/brainstorm` in a repo with and without the file and confirming both paths behave per contracts/cli.md
- [ ] T021 [P] [US2] Create `wf-skills/AGENTS.md` with this repository's own project overrides; verify with `git check-ignore -v AGENTS.md` exiting non-zero, proving it is committable
- [ ] T022 [US2] Validate User Story 2 — the override is read when present, absence is silent, and nothing creates the file — merge gate

**Checkpoint**: Overrides have a durable, committed home.

---

## Phase 5: User Story 3 - Each artifact has exactly one writer (Priority: P3)

**Goal**: No artifact is written by two producers. Order-independent — this
phase may land before Phases 3 and 4, since it is deletion at whatever path is
current.

**Independent Test**: Run `/brainstorm` to completion and confirm the approved
design survives the sharpening step; write a brief, run `/speckit.plan`, confirm
the brief is byte-identical.

**Verification**:

- A search for writers of each artifact path returns exactly one
- `shasum specs/<branch>/brief.md` is unchanged across a `/speckit.plan` run

### Implementation for User Story 3

- [ ] T023 [US3] Delete step 3 "Agent context update" from `wf-skills/.agents/skills/speckit-plan/SKILL.md:147-148`; verify with `git grep -nE 'brief\.md' -- .agents/skills/speckit-plan/SKILL.md` returning nothing, and by confirming a `/speckit.plan` run leaves an existing brief byte-identical
- [ ] T024 [US3] Collapse the two writes in `wf-skills/.agents/commands/brainstorm.md:13,15` into a single write of the final artifact, per the absorbed #10 PR 3; verify by running `/brainstorm` to completion and confirming the approved design is present in the written file rather than overwritten by the sharpening step
- [ ] T025 [P] [US3] Repoint the destination and delete the "and commit" instruction in `wf-skills/.agents/skills/brainstorming/SKILL.md:29,106` per FR-011; verify with `git grep -nE 'docs/superpowers|and commit' -- .agents/skills/brainstorming/SKILL.md` returning nothing
- [ ] T026 [P] [US3] Repoint the destination in `wf-skills/.agents/skills/idea-refine/SKILL.md:32,140`; verify with `git grep -nE 'docs/ideas' -- .agents/skills/idea-refine/SKILL.md` returning nothing
- [ ] T027 [US3] Validate User Story 3 — each artifact path has exactly one writing instruction across `.agents/`, and a `/speckit.plan` run leaves a brief unchanged — merge gate

**Checkpoint**: All three stories are independently functional.

---

## Phase 6: Polish & Cross-Cutting Concerns

- [X] T028 [P] Remove the now-unnecessary `.agent/` entry from `wfctl/.gitignore:19` — a hand-written consumer-repo line, not something the installer seeds (`_ensure_gitignored`, `cli.py:633`, covers only the manifest, backup dir, install targets and `wt/`); verify with `grep -c '\.agent/' wfctl/.gitignore` returning 0 and `git -C wfctl status --short` clean after a pipeline run
- [ ] T030 Run the full-pipeline smoke from quickstart.md in a scratch repo — `/brainstorm` through `/speckit.plan`, then `wm remove` — and confirm no `.agent/` appears and the archive contains `1-design.md`; verify against the "Full pipeline smoke" section
- [ ] T031 Validate the feature — every success criterion SC-001 through SC-007 demonstrated by its quickstart command — merge gate

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 1 (Setup)** → no dependencies
- **Phase 2 (Foundational)** → depends on Phase 1. **Blocks Phases 3–5.** This is the cross-repository ordering constraint, not a convention
- **Phase 3 (US1)** → depends on Phase 2
- **Phase 4 (US2)** → depends on Phase 2. Independent of Phase 3
- **Phase 5 (US3)** → depends on Phase 2 only nominally; the deletions are valid at either path, so this phase may land first among the story phases
- **Phase 6 (Polish)** → depends on Phases 3–5

### User Story Dependencies

- **US1** — independent once the foundation lands
- **US2** — independent of US1 and US3; touches a different file and a different lifetime of artifact
- **US3** — independent; pure deletion. The lowest-risk phase and a reasonable first merge

### Within Each User Story

Repointing tasks marked `[P]` touch disjoint files and may run together. The
non-`[P]` tasks in each phase either share a file with a sibling or are the
phase's merge gate.

### Parallel Opportunities

- Phase 2: T007, T008, T009, T011 — four disjoint files
- Phase 3: T015, T016, T017 — three disjoint files
- Phase 5: T025, T026 — two disjoint files
- Phase 6: T028, T029

---

## Logical PR Boundaries

Advisory only — `/speckit.decompose` decides the actual grouping. Recorded here
because the cross-repository constraint is not visible from task IDs alone.

1. **Tooling foundation** (Phases 1–2, T001–T013) — in the `wfctl` repository.
   Must merge and release before anything below. Self-contained: the tooling
   reads the new path and warns about the old, both harmless until a producer
   changes.
2. **`brainstorm.md`, entire file** (T018, T018a, T020, T024) — in `wf-skills`.
   **Grouped deliberately.** These four tasks belong to three different user
   stories but edit one file; split across three PRs they would conflict on every
   rebase. One PR owns the file, and its description should note that it serves
   US1, US2 and US3 so reviewers do not expect single-story coherence.
3. **Remaining one-writer deletions** (T023, T025, T026, T027) — in `wf-skills`.
   Pure deletion, valid at either path. Reasonable to merge first if the tooling
   release lags.
4. **Remaining artifact-move repointing** (T014–T017, T019) — in `wf-skills`.
   Requires boundary 1 to have shipped.
5. **`AGENTS.md` creation** (T021, T022) — in `wf-skills`. Independent of
   boundaries 3 and 4.
6. **Polish** (Phase 6, T028, T030, T031) — after everything else. Note T028 is a
   `wfctl` file, so it either rides with a later tooling PR or stands alone.

**Why boundary 2 exists**: `brainstorm.md` is the only file touched by more than
one story. Grouping it costs a PR whose tasks span three phases; not grouping it
costs three PRs racing on the same lines. The former is a documentation problem,
the latter a merge problem.

---

## Parallel Example: Phase 2

```bash
# Four disjoint files — fixtures and docstrings
T007  wfctl/tests/conftest.py
T008  wfctl/tests/test_archive_story.py
T009  wfctl/tests/test_start_atomic.py
T011  wfctl/wfctl/_archive.py:3 + wfctl/wfctl/cli.py:280
```

---

## Implementation Strategy

### MVP First (User Story 1 only)

Phases 1 → 2 → 3 delivers the feature's reason for existing: one directory, no
confusable second one. Stop there and it is a coherent, shippable increment.

### Incremental Delivery

Recommended merge order — **US3 before US1**, contrary to priority order:

1. Tooling foundation — unblocks everything, ships alone safely
2. US3 — pure deletion, lowest risk, removes a live data-loss defect (the
   brainstorm double-write destroys the design document)
3. US1 — the move itself
4. US2 — overrides
5. Polish

Priority reflects value; this order reflects risk. US3 fixes something that
currently destroys work on every `/brainstorm` run, so it should not wait behind
the larger change.

### Parallel Team Strategy

Limited. Phase 2 is one repository and one reviewer's context; Phases 3–5 touch
disjoint files and could be split across agents once the foundation lands.

---

## Notes

- **The ordering constraint is real, not stylistic.** Producer-first strands step
  inference at brainstorm with no error message. See contracts/cli.md, "Breaking
  change".
- **`checkpoint.md` → `escalation.md`** is a rename inside the move, justified in
  research R3 — the tooling's own `checkpoint` subcommand already means something
  unrelated.
- **No dual-path reading.** Resolved during clarification: skew is reported, not
  accommodated. T012 is the whole of that decision.
- Line numbers cited throughout were measured 2026-08-05 against
  `wf-skills@c7d0708` and `wfctl@2232f35`. Re-verify before editing if either has
  moved.
- **T029 was removed** during analysis remediation. It asked to update
  `using-wfctl/SKILL.md` "if it documents the superseded layout"; that file
  contains no `.agent/` reference, so the task was a no-op. The ID is left
  vacant rather than renumbering, so the analysis report's task references stay
  valid.
- **FR-006 is intentionally uncovered here.** Nothing in this feature writes
  `AGENTS.md` — the installer never seeds it, and the managed region belongs to
  wf-skills#16. The requirement is recorded as a constraint that work inherits,
  not as a gap in this task list.
