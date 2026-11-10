---
description: 'Task list for architecture views (#739) and diagram kinds (#738)'
---

# Tasks: architecture views

**Input**: Design documents in this folder: `plan.md`, `spec.md`, `research.md`, `data-model.md`, `contracts/cli.md`, and `quickstart.md`.
**Prerequisites**: `plan.md` and `spec.md`. Design records: none, since `design.md` records no level-3 decision.

**Tests**: Each phase writes its tests first and watches them fail. Tests that check console output set `NO_COLOR`. Test names are sentences, and each docstring says which failure the test catches.

**Organization**: One phase per user story, in the spec's priority order. User Stories 1 and 2 share `wfctl/arch/_views.py`, so User Story 2 starts after User Story 1. User Stories 3 and 4 don't touch the views and can run beside them.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel, since it changes a different file and depends on no unfinished task.
- **[Story]**: The user story the task belongs to, such as US1.

## Path Conventions

Single project. Code is under `wfctl/`, tests under `tests/`, shipped skills under `wfctl/agents/skills/`, and wfctl's own records under `docs/architecture/`.

---

## Phase 1: Setup

**Purpose**: The release notes, which `wfctl verify` and the `release-note` CI job require on every branch.

- [X] T001 [P] Create `changes/738.addition.md` with `uv run towncrier create 738.addition.md --content "…"`, saying that a record's `diagram` field takes a list of kinds with one drawing for each; verify with `python3 .github/scripts/check_release_note.py` or `uv run wfctl verify`
- [x] T002 [P] Create `changes/739.change.md` the same way, saying that `wfctl arch context` now lists the required views and marks missing and stale ones, and that the record and domain model templates changed shape; verify with the same check as T001

---

## Phase 2: Foundational

**Purpose**: Keep `views/` out of every reader of records before any view file exists (FR-008). A branch that edits only a view must not read as deciding a record.

**⚠️ CRITICAL**: No view file is written until this phase is done.

- [x] T003 Write a failing test in `tests/test_paths.py`, beside the tests for `declarations/` and `step-claims/`, asserting that `non_record_subtrees(arch)` includes `arch / "views"`, and that a branch whose only change is under `views/` isn't reported as deciding a record; run `uv run pytest tests/test_paths.py -q` and watch it fail (plan Note 1)
- [x] T004 Add `VIEWS_DIR = "views"` to `wfctl/_paths.py` and include it in `non_record_subtrees`, with a comment saying why views aren't records; verify with `uv run pytest tests/test_paths.py -q`
- [x] T005 Validate Phase 2 with `uv run pytest -q` and `python3 .github/scripts/check_imports.py` — merge gate

**Checkpoint**: A view file can be added without changing what any reader of records sees.

---

## Phase 3: User Story 1 - Every repository has the same required views (Priority: P1) 🎯 MVP

**Goal**: wfctl knows which views every repository needs, and ships a template for each one.

**Independent Test**: Fill each view template for a made-up capability, such as a library that lends books, and check that the result answers the template's question with no other guidance.

**Verification**:

- Automated: `tests/test_arch_views.py` (required views, contexts order, template match).
- Manual: `quickstart.md §1`, run after `uv run wfctl install-skills`.
- Evidence: The required views for a three-context domain page are the system context view, the container view, and three component views, and the FR-004 test fails when a template is renamed.

### Tests for User Story 1 ⚠️

> Write these first and watch them fail.

- [x] T006 [US1] In a new `tests/test_arch_views.py`, test `contexts(arch)`: it returns `None` with no accepted domain page or no `Contexts` line, returns a tuple in the line's order with repeats dropped, joins several accepted pages in file-name order, and leaves out names on the `Outside parties` line (R-002)
- [x] T007 [US1] In `tests/test_arch_views.py`, test the required views for a domain page with three contexts, with an empty `Contexts` line, and with no domain page or architecture folder at all. Each case expects `views/system-context.md` and `views/container.md`, and component views at `views/components/<context>.md` spelled exactly as on the `Contexts` line (FR-001, FR-002, data-model rules 1 to 3)
- [x] T008 [US1] In `tests/test_arch_views.py`, compare the required-view names with the files shipped under `wfctl/agents/skills/architecture-design/views/`, and fail when they disagree (FR-004). Also assert that each template carries a `covers` line in bracket form (FR-003c), that the container and component templates ask for a label on every arrow (FR-003b), and that both state the stability layout rule in words (FR-003a)

### Implementation for User Story 1

- [x] T009 [US1] Add `contexts(arch) -> tuple[str, ...] | None` to `wfctl/arch/_contexts.py`, reading only the `Contexts` line of accepted domain pages through `_accepted_pages` and `_entries`; verify with T006
- [x] T010 [US1] Create `wfctl/arch/_views.py` with a `RequiredView` value (name, path relative to the architecture root, present, covers) and a `required_views(arch)` function built on `contexts(arch)`. Read `covers` with a bracket-list helper in `wfctl/arch/_records.py` beside `split_names`, which strips one pair of brackets and splits on commas. T032 reuses the same helper for `Record.kinds`, and whichever of the two tasks lands first adds it. Re-export the new names lazily from `wfctl/arch/__init__.py` (R-001); verify with T007 and `python3 .github/scripts/check_imports.py`
- [x] T011 [P] [US1] Write `wfctl/agents/skills/architecture-design/views/system-context.md`: a `covers` frontmatter line, a plain summary, the one question the view answers (who and what the system interacts with), and a request for one mermaid drawing (FR-003, FR-003c, R-008); verify with T008
- [x] T012 [P] [US1] Write `wfctl/agents/skills/architecture-design/views/container.md`: the same opening, the question (which parts run or store data separately), the stability layout rule in plain words with stable parts in an upper subgraph above a labeled line, arrows toward the stable side, a wrong-way arrow in red through `linkStyle`, an instruction to draw the dependencies the code has rather than the intended ones, and a label on each arrow naming the import or call, such as `A -->|"imports _records"| B` (FR-003a, FR-003b, R-011); verify with T008
- [x] T013 [P] [US1] Write `wfctl/agents/skills/architecture-design/views/component.md` for one context, with the same layout rule and arrow labels as the container template; verify with T008
- [x] T014 [US1] Name the three view templates in the Inputs section of `wfctl/agents/skills/architecture-design/SKILL.md`, beside the current-state view (R-007); verify with `uv run pytest tests/test_architecture_design_skill.py tests/test_skill_cross_references.py -q`
- [x] T015 [US1] Validate User Story 1 with `uv run pytest -q`, `uv run ruff check wfctl/ tests/`, `uv run mypy`, and `python3 .github/scripts/check_imports.py`, then run `quickstart.md §1` after `uv run wfctl install-skills` — merge gate

**Checkpoint**: wfctl can list the required views for any repository, and each template stands on its own.

---

## Phase 4: User Story 2 - Session start points the agent at the views (Priority: P1)

**Goal**: `wfctl arch context` ends with a `Views` block naming each present view, each missing one, and each stale or unchecked one, filtered by the branch's contexts, and never refuses anything.

**Independent Test**: Run `wfctl arch context` in a test repository with some views present and some missing, and check that the output names each present path and each missing view, as `contracts/cli.md` shows.

**Verification**:

- Automated: `tests/test_arch_views.py` (filter, Views block, stale and unchecked marks, exit code).
- Manual: `quickstart.md §2`.
- Evidence: The Views block matches `contracts/cli.md` exactly with `NO_COLOR` set, and a commit to a covered path marks the view stale until the view is committed again (SC-006).

### Tests for User Story 2 ⚠️

> Write these first and watch them fail. Stale-view tests build a real git repository in `tmp_path` (plan Note 7).

- [x] T016 [US2] In `tests/test_arch_views.py`, test the branch filter for each row of the table in `data-model.md §View listing`: names all on the `Contexts` line, no `Contexts` line or an empty one, a name not on the line (including an `Outside parties` name), and no spec folder. Assert that the system context and container views always show (R-003)
- [x] T017 [US2] In `tests/test_arch_views.py`, test the `Views` block against `contracts/cli.md` exactly, with `NO_COLOR`, for a repository with some views present, with none present, with no architecture folder, and with `--all`. Check the order in contract rule 1, and that `arch context` exits 0 with every view missing (rule 3, FR-007)
- [x] T018 [US2] In `tests/test_arch_views.py`, build a real git repository and test freshness: a view is stale after a commit to a covered path and prints the count and the `covers` paths joined by `, ` (rule 5); it's current again after a commit to the view; an uncommitted edit to the view or the covered code changes neither; and a view with no commit yet prints as a plain path (rule 6, FR-006a, SC-006)
- [x] T019 [US2] In `tests/test_arch_views.py`, test the two unchecked reasons that don't come from `git` in `contracts/cli.md`: a view with no `covers` line or an empty one, and a view whose `covers` names a path that doesn't exist, naming the first such path (data-model `freshness`)
- [x] T020 [US2] In `tests/test_arch_views.py`, test an architecture root outside the working tree: view paths print absolute through `_paths.arch_location` (rule 4), and each present view prints as `unchecked: <path> (not in this repository's history)` rather than as current, including a view there with no `covers` line, since `plan.md §Validation Strategy` and R-010 say every present view under that root takes this reason. Also test a working directory that isn't a git repository, including a view there with no `covers` line, which prints the history reason because it comes first in the data-model order of `unchecked` reasons. Check that neither case changes the exit code (contract rule 7, data-model `unchecked (no history)`)

### Implementation for User Story 2

- [x] T021 [US2] Add the branch filter to `wfctl/arch/_views.py`, taking the domain page's contexts, the branch's `listed(spec_dir)`, and an `all` flag, and returning the present and missing views in the contract's order; verify with T016
- [x] T022 [US2] Add freshness to `wfctl/arch/_views.py`: `git log -1 --format=%H -- <view>` for the view's last commit, then `git rev-list --count <commit>..HEAD -- <covers paths>`, with the paths after `--`. Return current, stale with its count, or unchecked with its reason. Run the `git` calls before checking the `covers` line, so the history reason wins whenever it applies, then check for no `covers` line, then for a missing path (data-model order of `unchecked` reasons). Treat a view as having no commit yet only when `git log` exits 0 with empty output. When either `git` call exits non-zero, return unchecked with the reason `not in this repository's history` (R-010, contract rules 6 and 7); verify with T018, T019, and T020
- [x] T023 [US2] Print the `Views` block at the end of `arch_context_cmd` in `wfctl/cli.py`, after every line about records, with each path through `_arch_location` and the `missing:`, `stale:`, and `unchecked:` forms from `contracts/cli.md`. Pass `--all` through to the filter, and leave the exit code unchanged (R-009); verify with T017 and T020
- [x] T024 [US2] Add one sentence to step 2 of `wfctl/agents/skills/start-session/SKILL.md` saying that the `Views` block follows the records lines, that a missing, stale, or unchecked view is a reminder to draw or update it and never a refusal, and that the agent opens the views before changing a boundary (plan Note 9); verify with `uv run pytest tests/test_skill_cross_references.py -q` and by running `/start-session` after `uv run wfctl install-skills`
- [x] T025 [US2] Validate User Story 2 with `uv run pytest -q`, `uv run ruff check wfctl/ tests/`, `uv run mypy`, and `python3 .github/scripts/check_imports.py`. Run `grep -rn "_views" wfctl/` and confirm that only `wfctl/arch/` and `arch_context_cmd` in `wfctl/cli.py` use it, so the worktree guard, `wfctl verify`, and the brainstorm gate can't refuse because of a view (FR-007, contract §No refusals from views). Then run `quickstart.md §2` — merge gate

**Checkpoint**: Session start shows every view the branch needs, and nothing refuses because of one.

---

## Phase 5: User Story 3 - A record can carry more than one kind of diagram (Priority: P2)

**Goal**: A record's `diagram` field takes a list of kinds, and acceptance checks that each declared kind has its drawing under its own `### <kind>` heading, while every one-kind record behaves exactly as before.

**Independent Test**: Write a throwaway record declaring `[data-flow, sequence]` with both drawings and check that it passes. Delete one drawing and check that the refusal names the missing kind and the fix.

**Verification**:

- Automated: `tests/test_arch_diagram_kinds.py`, `tests/test_arch_sections.py`, and the existing `tests/test_arch_accept*.py` and `tests/test_arch_diagram.py`.
- Manual: `quickstart.md §3`.
- Evidence: Every fixture copy of a one-kind record gives the acceptance result saved beside it (SC-004), and each new refusal matches `contracts/cli.md` exactly.

### Tests for User Story 3 ⚠️

> T026 runs before any change to `wfctl/arch/_records.py` (plan Note 2). The others are written first and watched failing.

- [X] T026 [US3] Copy every one-kind record in `docs/architecture/` at the branch's base into `tests/fixtures/one-kind-records/`, save each one's `accept_blockers` and `validate` result beside it, and add a test in a new `tests/test_arch_diagram_kinds.py` that compares the fixture copies, never the live folder (SC-004); run it now and see it pass on unchanged code
- [X] T027 [US3] In `tests/test_arch_diagram_kinds.py`, test `Record.kinds` for a single kind, a bracket list, `[]`, an empty value, and a missing field, and test that `Record.diagram` stays verbatim (R-004, data-model §Diagram declaration)
- [X] T028 [US3] In `tests/test_arch_diagram_kinds.py`, test drawings per kind: a one-kind record passes drawn directly under `## Boundary` and under `### <kind>`; a two-kind record passes with both drawings; a `### data-flow` heading with no fence before `### sequence` is refused for the missing data-flow drawing, with and without `### Key` between them; a fence above the first `###` heading in a two-kind record counts for neither kind; and `### Sequence` matches `sequence` (R-005, data-model §Drawing per kind)
- [X] T029 [US3] In `tests/test_arch_diagram_kinds.py`, match each new refusal in `contracts/cli.md §wfctl arch accept` exactly with `NO_COLOR`: the missing drawing, a repeated kind, an undeclared `### <kind>` heading, and an unknown kind. Also test that a two-kind record with no fence at all prints one refusal per kind and no `no drawing` line, that a record with an old blocker and a new one prints the `cannot be accepted yet` block first, and that the sequence failure-step rule applies inside a multi-kind record (FR-012 to FR-014, R-013)
- [X] T030 [US3] In `tests/test_arch_diagram_kinds.py`, test `validate`: a proposed record gets a doctor warning for a repeated kind, a missing drawing, and an undeclared heading, in the shape `contracts/cli.md §wfctl doctor` shows; an accepted record gets none; and an unknown kind is an error on every status, named per kind (FR-015, R-006)
- [X] T031 [P] [US3] In `tests/test_arch_sections.py`, assert that the record template's `##` headings appear in the FR-017a order: `## Decision`, `## Boundary`, `## Context`, `## Direct baseline`, `## Owns truth`, `## Considered`, `## Consequences`, and `## Log`

### Implementation for User Story 3

- [X] T032 [US3] Add the `Record.kinds` property to `wfctl/arch/_records.py`, through the bracket-list helper T010 describes, adding it here if User Story 1 hasn't landed yet; verify with T027
- [X] T033 [US3] Add `_drawings(record)` to `wfctl/arch/_records.py`, built on `_section_bounds` for `## Boundary`, ending each kind's subsection at the next `###` or `##` heading and taking the first fence inside it. Keep `_drawing(record)` for one-kind records; verify with T028
- [X] T034 [US3] Add the four new refusals to `wfctl/arch/_records.py` as problem and fix pairs, kept apart from the strings `accept_blockers` returns so the existing block's output doesn't change. Suppress the `no drawing` blocker for a record declaring more than one kind, and run the sequence failure-step check on the sequence drawing from `_drawings`; verify with T026, T028, and T029
- [X] T035 [US3] Print the new refusals in `arch_accept_cmd` in `wfctl/cli.py` as `✗ <slug> <problem>.` lines with an indented `Fix:` line, after the existing `cannot be accepted yet` block, then the record's path. Make `acceptable(record)` and `--dry-run` count them; verify with T029 and `uv run pytest tests/test_arch_accept.py tests/test_arch_accept_dry_run.py tests/test_arch_accept_drawing.py -q`
- [X] T036 [US3] Extend `validate` in `wfctl/arch/_records.py` with the doctor warnings for proposed records, and check the unknown-kind error for each kind in the list; verify with T030 and `uv run pytest tests/test_arch_diagram.py -q`
- [X] T037 [US3] Reorder `wfctl/agents/skills/architecture-decisions/record-template.md` to the FR-017a order, matching the two proposed records already reordered, and show a two-kind `diagram: [data-flow, sequence]` example with a `### <kind>` heading for each drawing (FR-017, FR-017a, plan Note 8); verify with T031 and `uv run pytest tests/test_record_placement.py -q`
- [X] T038 [US3] Describe declaring and drawing more than one kind, and the new section order, in `wfctl/agents/skills/architecture-decisions/SKILL.md` (FR-017); verify with `uv run pytest tests/test_skill_cross_references.py -q` and by reading the installed skill after `uv run wfctl install-skills`
- [X] T039 [P] [US3] Document the `diagram` field's list form in `docs/reference.md`, and change nothing else there or in the README, since #735 owns them (FR-019); verify by reading `git diff main -- docs/reference.md README.md`
- [X] T040 [US3] Validate User Story 3 with `uv run pytest -q`, `uv run ruff check wfctl/ tests/`, and `uv run mypy`, then run `quickstart.md §3` — merge gate

**Checkpoint**: A two-kind record passes acceptance, and every one-kind record gives the same result as before.

---

## Phase 6: User Story 4 - The domain page template is easier to read (Priority: P3)

**Goal**: The domain model template uses short lists where wide tables used to be, and keeps the Bounded Contexts table and the Context Map's mermaid drawing.

**Independent Test**: Fill the new template for a made-up capability and check that only the Bounded Contexts list is a table.

**Verification**:

- Automated: `tests/test_record_placement.py`.
- Manual: Fill the template after `uv run wfctl install-skills`.
- Evidence: The template has exactly one markdown table (SC-005).

### Tests for User Story 4 ⚠️

- [x] T041 [US4] In `tests/test_record_placement.py`, assert that `wfctl/agents/skills/model-the-domain/domain-model-template.md` has exactly one markdown table, the Bounded Contexts table, and still carries the Context Map's mermaid drawing that `check_imports.py` reads (FR-016, SC-005, plan Note 3); watch it fail

### Implementation for User Story 4

- [x] T042 [US4] Rewrite `wfctl/agents/skills/model-the-domain/domain-model-template.md` so Evidence, Scenarios, Ubiquitous Language, Subdomains, the Context Map's relationship table, the Invariants and Aggregate tables, Implementation feedback, and Open questions are short lists. Leave wfctl's own domain page alone, since #745 brings it in line; verify with T041 and `python3 .github/scripts/check_imports.py`
- [x] T043 [US4] Validate User Story 4 with `uv run pytest -q`, and fill the installed template for a made-up capability — merge gate

**Checkpoint**: A domain page written from the template has one table.

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: wfctl's own views, drawn last from the finished templates as their worked example (plan Note 6), and the whole-branch checks.

- [x] T044 Draw `docs/architecture/views/system-context.md` from the installed system context template, with a `covers` line, a plain summary, and one mermaid drawing of wfctl, its user, and the outside systems from the domain page's `Outside parties` line (FR-018, SC-001); verify with `uv run wfctl arch context` showing its plain path
- [x] T045 Draw `docs/architecture/views/container.md` from the installed container template, with a `covers` line, the stability layout, and a label on every arrow naming the import or call that creates it. Check each label against the code (FR-018, FR-003b); verify with `uv run wfctl arch context` showing its plain path, and by looking up three arrow labels with `grep`
- [x] T046 Confirm `docs/architecture/views/current-state.md` stays unchanged as the optional module layers view, and that `wfctl arch context` never reports it (data-model rule 3); verify with `git diff main -- docs/architecture/views/current-state.md`
- [x] T047 Run all of `quickstart.md` after `uv run wfctl install-skills`, including the stale mark in §2 and the `covers` and arrow-label checks in §1
- [x] T048 Run `uv run wfctl doctor` and `uv run wfctl check config`, and confirm neither reports anything new
- [x] T049 Validate the branch with `uv run wfctl verify`, which runs `uv run pytest -q`, `uv run ruff check wfctl/ tests/`, `uv run mypy`, `python3 .github/scripts/check_imports.py`, and the release note check — merge gate

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies.
- **Foundational (Phase 2)**: Blocks every phase that writes a file under `views/`, which is Phase 7 and the tests in Phase 4 that create views.
- **User Story 1 (Phase 3)**: Depends on Phase 2.
- **User Story 2 (Phase 4)**: Depends on User Story 1, since it extends `wfctl/arch/_views.py`.
- **User Story 3 (Phase 5)**: Depends on Phase 1 only. It changes `wfctl/arch/_records.py` and the record template, which no other story touches.
- **User Story 4 (Phase 6)**: Depends on Phase 1 only.
- **Polish (Phase 7)**: Depends on every story. T044 and T045 need the finished templates from User Story 1 and the `Views` block from User Story 2.

### Within Each Story

- Tests first, watched failing. T026 is the exception: it pins today's behavior and passes before any change.
- `_contexts.py` before `_views.py`, and `_views.py` before `cli.py`.
- `Record.kinds` before `_drawings`, `_drawings` before the refusals, and the refusals before the CLI and doctor wiring.

### Shared files

- `tests/test_arch_views.py` holds T006 to T008 and T016 to T020, so those tasks run in order.
- `tests/test_arch_diagram_kinds.py` holds T026 to T030.
- `wfctl/cli.py` is changed by T023 and T035, in different functions. Run them one after the other to avoid a merge conflict.

## Parallel Example

```text
After Phase 2:
  US1 — T011, T012, T013 (the three view templates)
  US3 — T026, then T031 beside T027 to T030
  US4 — T041, then T042

Within US3, once T036 is done:
  T037 (record template), T039 (docs/reference.md)
```

## Implementation Strategy

### MVP first

1. Phase 1 and Phase 2.
2. User Story 1: the required views and their templates.
3. User Story 2: the `Views` block at session start. User Stories 1 and 2 are both P1, and the views are only useful to the agent once session start prints them.
4. Stop and run `quickstart.md §1` and `§2`.

### Incremental delivery

1. User Story 3 (#738) is its own slice and can land before or after the views.
2. User Story 4 is a template-only change.
3. Polish draws wfctl's two views last, as the worked example for the templates.

## Notes

- The tasks don't decide PR boundaries. `/speckit.decompose` does that after `/speckit.analyze`.
- Never run `wfctl arch accept` on the two proposed records without `--dry-run`. The user accepts them.
- Store the spec folder with `wfctl store specs` before the PR, never with a hand `git add`.
