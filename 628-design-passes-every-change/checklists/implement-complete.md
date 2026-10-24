Implementation complete: 2026-10-24

## Tasks at completion

~~~~markdown
---
description: 'Task list for #628: every change runs the design passes and records whether it needs a spec'
---

# Tasks: Every change runs the design passes and records whether it needs a spec

**Input**: Design documents in this feature's spec dir (`wfctl feature-paths` prints it)
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/cli.md, contracts/skills.md, quickstart.md

**Design records read before writing these tasks.** No task below reverses one of them.

- `docs/architecture/design/628-design-passes-own-skill.md`: the four passes live in `design-passes`, and the route to implementation points to it.
- `docs/architecture/design/628-early-answer-in-commit-trailer.md`: rejected, so no task writes a `Needs-spec:` trailer.
- `docs/architecture/design/628-spec-answer-in-pr-body.md`: `check-body` reads required sections from `change_sections` in `wfctl.json`, and wfctl hardcodes no section name.

**Tests**: Required. The check is critical-path logic with a byte-identical output promise (SC-003). The skill edits are covered by cross-reference tests that have to fail before the edits land.

**Organization**: One phase per user story, in spec order. US1 and US2 share no code and can run in parallel. US3 edits the same file as US1 (`design-levels/SKILL.md`), so it runs after US1.

**Edits go to `wfctl/agents/`, never to `.agents/` or `.claude/`** (`layer-model`). No task edits `opening-a-change` (FR-013) or a Spec Kit-derived skill (`vendor-upstream-skills`).

**Load the `writing-style` skill before any task that writes prose.** That covers every skill file, `AGENTS.md`, the PR template comment, docstrings, code comments, commit messages, and the release note.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: can run in parallel (different files, no dependency on an unfinished task)
- **[Story]**: US1, US2, or US3, from spec.md

---

## Phase 1: Setup

**Purpose**: A known-green baseline, so a later failure belongs to this change.

- [X] T001 Run `uv run pytest -q`, `uv run ruff check wfctl/ tests/`, and `uv run mypy wfctl/` before any edit, and note the pass count; verify all three exit 0
- [X] T002 Save today's `check-body` output for SC-003. Write the five bodies from quickstart.md §1 (answered, N/A, comment only, heading deleted, bare "No.") from `.github/pull_request_template.md` into the scratchpad. The template has no "## Needs a spec?" section until T027, so add that heading and its body to each file by hand, using the comment in `contracts/cli.md §The template comment` for the comment-only body. Run `NO_COLOR=1 uv run wfctl check-body <file>` on each, and save stdout and the exit code per body. Verify that five saved outputs exist

---

## Phase 2: Foundational

None. US1 is skills and prose, US2 is a new module and its wiring, and neither needs anything from the other. The one file they share is `AGENTS.md`, edited in different sections by T013 and T036, so those two tasks run in sequence.

---

## Phase 3: User Story 1 - A change that bypasses Spec Kit still runs the design passes (Priority: P1) 🎯 MVP

**Goal**: A new `design-passes` skill, reached by path from every place that used to send a small change straight to implementation. Four "Not for" lines exclude a change by whether it moves a boundary, so the route has no loop and no dead end.

**Independent Test**: Install the skills and give an agent only a handoff for a one-line fix with the new route line. The agent runs `design-passes` and answers the spec question before editing code, and the branch has a failing-test commit before the fix commit (SC-001).

**Verification**:

- Automated: `uv run pytest tests/test_skill_cross_references.py -q`, covering the two new tests and `test_every_referenced_skill_ships`
- Manual: quickstart.md §2 (the skill, for real) and §3 (the mutation check)
- Evidence: both new tests fail before T007 and pass after T013. On the throwaway branch, `git log --reverse` shows the test commit first, and no file appears under `docs/architecture/declarations/`

### Tests for User Story 1 ⚠️

> Write these first and run them. Both must fail on the current tree before any skill edit.

- [X] T003 [US1] Add `test_every_route_around_spec_kit_names_design_passes` to `tests/test_skill_cross_references.py`. It reads the four sections listed in plan.md §The cross-reference tests, each from its start marker to its end marker. It reads the three skill files through `_AGENTS`, and `AGENTS.md` from the checkout root next to `tests/`. It asserts that each section contains `.agents/skills/design-passes`, and a missing start marker fails the test. The docstring names the failure it guards against: a later edit that drops the pointer leaves no phrase for a search to find. Verify by running `uv run pytest tests/test_skill_cross_references.py -q -k design_passes` and confirming it fails on all four files
- [X] T004 [US1] Add `test_no_shipped_file_sends_a_change_straight_to_implementation` to `tests/test_skill_cross_references.py`. It reads every `.md` under `_AGENTS` plus `AGENTS.md`, collapses whitespace, lowercases the text, and asserts "straight to implementation" is absent. The docstring says why it collapses whitespace (`architecture-design` wraps the phrase across two lines) and why it lowercases (`worktree-handoff` capitalizes it). Verify by running `uv run pytest tests/test_skill_cross_references.py -q -k straight_to_implementation` and confirming it fails on `architecture-design` and `worktree-handoff`

### Implementation for User Story 1

- [X] T005 [US1] Create `wfctl/agents/skills/design-passes/SKILL.md` per `contracts/skills.md §design-passes`. The frontmatter is `name: design-passes`, with a description naming a change that bypasses Spec Kit. The body carries the six numbered parts in order: spec question, level 2, level 3, test first, refactor, and hand-off. Name every skill it hands to by its full `.agents/skills/<name>` path (FR-002). Step 1 says a yes goes to `/speckit.brainstorm` and is final. Step 2 reads `wfctl arch context` and `<arch-root>/domain/`, sends a change to a modeled term's meaning to `model-the-domain` first, and says not to run `wfctl arch none` (FR-012). Say once that Andre hasn't decided where the spec line falls, so each answer gives its own reason and the reviewer judges it. Add no command wrapper (research R8). Verify with `uv run pytest tests/test_skill_cross_references.py -q -k every_referenced_skill_ships`. Then read the skill back against US1 scenarios 2 to 4: a yes in step 1 sends the change to `/speckit.brainstorm` and runs none of the four passes; a change inside an existing boundary writes no file; and a change to a modeled term's meaning goes to `model-the-domain` before `architecture-design`
- [X] T006 [US1] Commit T003, T004, and T005 together, so the branch shows the failing tests before the pointers; verify that `git log -1 --stat` lists only `tests/test_skill_cross_references.py` and the new skill
- [X] T007 [US1] Rewrite item 3, "Which route this work takes", in `wfctl/agents/skills/worktree-handoff/SKILL.md` per the `worktree-handoff` row in `contracts/skills.md §The four places`. It opens "Through `.agents/skills/design-passes`, or through the spec pipeline", and ends "A bug fix or a copy edit runs `.agents/skills/design-passes` before any code is written. That skill decides whether the change needs a spec." Leave the item's other sentences as they are, since PR-016 is still open and waiting on Andre. Verify with T003 and T004 for this file
- [X] T008 [US1] Replace the "Not for" paragraph at `wfctl/agents/skills/design-levels/SKILL.md:22-24` with the text in `contracts/skills.md §design-levels/SKILL.md:22-24`. Replace the level-2 exit paragraph at `:174-177` with the text in `§design-levels/SKILL.md:174-177`. The docstring of `test_a_feature_with_no_design_step_is_not_gated` in `tests/test_pipeline_commands.py` says "`design-levels` excludes bug fixes and copy edits", so reword it to say the skill excludes a change that moves no boundary. Verify with T003 for this file, and read both paragraphs back to confirm a change `design-passes` sent here stays here (FR-004, US1 scenario 7)
- [X] T009 [P] [US1] Replace the "Not for" paragraph at `wfctl/agents/skills/architecture-design/SKILL.md:46-50` with the text in `contracts/skills.md §architecture-design/SKILL.md:46-50`; verify with T003 and T004 for this file (US1 scenario 6)
- [X] T010 [P] [US1] Replace the "Not for" paragraph at `wfctl/agents/skills/model-the-domain/SKILL.md:125-129` with the text in `contracts/skills.md §model-the-domain/SKILL.md:125-129`. Verify with `uv run pytest tests/test_skill_cross_references.py -q -k every_referenced_skill_ships`, and read the paragraph back to confirm it gives no kind of change as the reason to leave
- [X] T011 [P] [US1] Replace the "Not for" paragraph at `wfctl/agents/skills/architecture-decisions/SKILL.md:29-31` with the text in `contracts/skills.md §architecture-decisions/SKILL.md:29-31`. Verify with `uv run pytest tests/test_skill_cross_references.py -q -k every_referenced_skill_ships`, and read the paragraph back to confirm a boundary-moving fix gets a record (US1 scenario 6)
- [X] T012 [US1] Check the line numbers T008 to T011 used against the files as they stand, since the contract took them on 2026-10-23; verify with `grep -n "Not for" wfctl/agents/skills/{design-levels,architecture-design,model-the-domain,architecture-decisions}/SKILL.md` showing one replaced paragraph per file
- [X] T013 [US1] Edit the "Not every change needs the spec pipeline." paragraph in `AGENTS.md`, at about line 391. Add "Every change runs the design passes, either through the pipeline or through `.agents/skills/design-passes`.", and stop quoting the `design-levels` wording that T008 removed (PR-026). Verify with T003 and T004 for `AGENTS.md`
- [X] T014 [US1] Run quickstart.md §3. `uv run pytest tests/test_skill_cross_references.py -q` passes. Then remove every occurrence of `.agents/skills/design-passes` from the `architecture-design` "Not for" paragraph, which names the path twice (PR-017). Rerun, confirm the section test fails and names that file, and restore the paragraph. Verify with the output of the two pytest runs
- [x] T015 [US1] Run `uv run wfctl install-skills --prune --yes --agent claude`, then quickstart.md §2 on a throwaway worktree with a one-line fix and only a handoff carrying the new route line. Verify against SC-001 and the evidence in §2: the agent answers the spec question before any code edit, the first commit is a failing test, and no file appears under `docs/architecture/declarations/`. The worktree guard refuses work in a second worktree, so ask Andre before this step
- [x] T016 [US1] Validate US1 with `uv run pytest -q`, `uv run ruff check wfctl/ tests/`, and `uv run mypy wfctl/` — merge gate

**Checkpoint**: US1 works on its own. The route reaches `design-passes`, and no "Not for" line sends a change back.

---

## Phase 4: User Story 2 - A PR with no spec answer can't pass `check-body` (Priority: P1)

**Goal**: A `change_sections` key in `wfctl.json`, and a pure `_sections` module that reads it and checks a body. `check-body` and `check config` call that module, this repo's template and config opt in, and the review panel gains a fifth dispatch bullet.

**Independent Test**: In a repo that lists "Needs a spec?", run `check-body` on the five quickstart bodies. The answered body passes, and each of the other four prints one finding and exits 1. With the key removed, all five print exactly what T002 saved.

**Verification**:

- Automated: `tests/test_sections.py` (new), `tests/test_shape.py`, `tests/test_cli_status.py`, and `tests/test_review_fanout_skill.py`
- Manual: quickstart.md §1, §4 (SC-005), and §5 (the panel)
- Evidence: `uv run wfctl check config` exits 0 on this repo. The four bad bodies print the strings in `contracts/cli.md`. With the key removed, the output matches T002's byte for byte

### Tests for User Story 2 ⚠️

> Write these first and run them. Each must fail, because `wfctl/_sections.py` doesn't exist yet or isn't called yet.

- [X] T017 [P] [US2] Create `tests/test_sections.py` with `load_required` cases from `data-model.md §change_sections`: key absent, `[]`, a valid list, a duplicate kept once, `"x"`, an int entry, and an empty entry. Each case asserts the exact problem strings listed there. Verify by running `uv run pytest tests/test_sections.py -q` and confirming it fails on import
- [X] T018 [US2] Add `body_findings` cases to `tests/test_sections.py` from `data-model.md §Section finding` and research R4 and R5:
  - missing
  - empty, from a single-line and from a multi-line HTML comment
  - N/A, as `N/A`, `n/a`, `NA`, and `N/A.`
  - a bare answer, as `No.`, `YES`, and `no!`
  - answered, as "No, small change." and as the full example in the spec
  - a matching heading inside a fenced block, which doesn't count
  - a match at `###`, and a match in another case
  - a section that ends at the next heading of the same or a higher level, but not at a lower one

  Each case asserts the exact finding line. Verify by running the file and confirming the new cases fail
- [X] T019 [US2] Add `templates` and `template_problems` cases to `tests/test_sections.py` from research R6 and `data-model.md §Template finding`, using `tmp_path`: no template found; one template missing a listed section; a `PULL_REQUEST_TEMPLATE/` directory where only one of two templates has the section, which gives one finding naming the other file; a template under `.git`, which is ignored; and a template four levels deep, which isn't found. Verify by running the file and confirming the new cases fail
- [X] T020 [P] [US2] Add `check-body` CLI cases to `tests/test_shape.py`, one per row of the table in `contracts/cli.md §wfctl check-body`, with `NO_COLOR` pinned. Each case writes `wfctl.json` and a body into a temporary git repo, then asserts the output and the exit code. For the no-key row, run the four bad bodies with no `change_sections` key, and assert each prints only `✓ <path>: the drawings look right` and exits 0, which is today's output for a body with no drawing finding (SC-003). T030 compares against the real saved output from T002. The outside-a-git-repo row asserts there's no section finding. Verify by running `uv run pytest tests/test_shape.py -q` and confirming the listed-section rows fail
- [X] T021 [P] [US2] Add `check config` cases to `tests/test_cli_status.py`. A listed section the template lacks prints the line in `contracts/cli.md §wfctl check config` and exits 1. `change_sections: "x"` prints the `load_required` problem. Listed sections with no template print the no-template line. A valid key that every template covers adds no line to the success output. Verify by running `uv run pytest tests/test_cli_status.py -q -k change_sections` and confirming the cases fail

### Implementation for User Story 2

- [X] T022 [US2] Create `wfctl/_sections.py`. Its module docstring follows the shape of `wfctl/_change.py`'s, where a key's schema lives with the feature that reads it. Add `CONFIG_KEY = "change_sections"` and `load_required(repo_root)`, following `wfctl/_change.py:131` line for line with "section heading" in place of "field name". Verify with `uv run pytest tests/test_sections.py -q -k load_required`
- [X] T023 [US2] Add `body_findings(body, required)` to `wfctl/_sections.py`. It collects ATX headings outside fences with the `walk` function in `wfctl/_md.py`, and matches a heading by its trimmed text, ignoring case. Each section runs to the next heading of the same or a higher level. It strips HTML comments and then whitespace, and classifies what's left per `data-model.md §Section finding`. It reads no file. The plan doesn't say whether comments or headings are handled first (PR-007), so pick an order and say why in a comment. Verify with `uv run pytest tests/test_sections.py -q -k body_findings`
- [X] T024 [US2] Add `templates(repo_root)` and `template_problems(repo_root, required)` to `wfctl/_sections.py` per research R6. A comment names the `find` in Step 2 of `opening-a-change` as the search this one mirrors. `template_problems` reports only missing sections, since a template's sections are meant to be empty. Verify with `uv run pytest tests/test_sections.py -q`
- [X] T025 [US2] Change `check_body_cmd` in `wfctl/cli.py`, at about line 6511, so `found` is `_shape.body_findings(body)`, then the `load_required` problems, then `_sections.body_findings(body, required)`, then `_verification_finding()`. Outside a git repo it reads no sections, the same way `_verification_finding` returns nothing there. Update its docstring in two places: it no longer checks "Only the drawing rule", and after T008 `design-levels` no longer sends bug fixes around the pipeline. Verify with `uv run pytest tests/test_shape.py -q`
- [X] T026 [US2] Change `check_config_cmd` in `wfctl/cli.py`, at about line 6305, to add the `_sections.load_required` problems and the `_sections.template_problems` findings under the existing `✗ wfctl.json:` header. Add `change_sections` to the docstring's list of keys it validates. Verify with `uv run pytest tests/test_cli_status.py -q`
- [X] T027 [US2] Add the "## Needs a spec?" section and its HTML comment to `.github/pull_request_template.md` after Issue Links, copied exactly from `contracts/cli.md §The template comment`. Verify by reading the file back, and with the `check config` run in T028
- [X] T028 [US2] Add `"change_sections": ["Needs a spec?"]` to `wfctl.json`, beside `change_check`; verify that `uv run wfctl check config` exits 0
- [X] T029 [US2] Add the fifth dispatch bullet from `contracts/skills.md §fanning-out-code-review Step 2` to Step 2 of `wfctl/agents/skills/fanning-out-code-review/SKILL.md`, and change "these four" to "these five". Keep the bullet's bold lead on one line. The counting test matches `^- \*\*(.+?)\*\*` one line at a time, so the contract's bold lead, which closes on its second line, isn't counted (PR-020). Shorten the bold lead to fit, such as "**Report any design decision nothing on the change covers:**", and keep the rest of the contract's text after it. Verify with `uv run pytest tests/test_review_fanout_skill.py -q -k dispatch_list_requires_the_coverage`
- [X] T030 [US2] Run quickstart.md §1: `uv run wfctl check config`, then the five bodies, each printing the line and exit code given there. Then remove the key from `wfctl.json`, run the five again, and diff against the output T002 saved (SC-003). Restore the key. Verify that the diff is empty
- [X] T031 [US2] Run quickstart.md §4 in a fresh-context subagent, given only the N/A body and its finding line. Verify against SC-005 that its first rewrite holds a yes or no and a one-sentence reason, and that `check-body` then prints `✓`
- [x] T032 [US2] Run quickstart.md §5 on a throwaway branch: a fix that has the worktree guard read a new `wfctl.json` setting with no record, reviewed with `.agents/skills/fanning-out-code-review`. Verify that at least one reviewer reports the new setting (US2 scenario 8), and that no reviewer reports it once a record covering it is committed. The throwaway branch needs Andre for the same reason as T015, so ask first
- [x] T033 [US2] Validate US2 with `uv run pytest -q`, `uv run ruff check wfctl/ tests/`, and `uv run mypy wfctl/` — merge gate

**Checkpoint**: US2 works on its own. In this repo, a PR with no reasoned answer can't pass `check-body`. In a repo that lists no sections, nothing changes.

---

## Phase 5: User Story 3 - Both routes start level 2 by reading the records and the domain model (Priority: P3)

**Goal**: Level 2 of `design-levels` opens with the same step as level 2 of `design-passes`.

**Independent Test**: Read the installed `design-levels` skill. Level 2's first step names `wfctl arch context` and the `domain/` folder, in the same wording as `design-passes`.

**Verification**:

- Automated: `uv run pytest tests/test_skill_cross_references.py -q`. It already holds the level-2 tests, such as `test_the_level_2_gate_names_the_domain_modeling_method`, and they must stay green
- Manual: a side-by-side read of the two level-2 openings
- Evidence: the two paragraphs match, apart from what each skill calls itself

### Implementation for User Story 3

- [X] T034 [US3] Add the level-2 first step to `wfctl/agents/skills/design-levels/SKILL.md` per `contracts/skills.md §design-levels level 2`, in the wording of step 2 of `design-passes` from T005. It reads the accepted records with `wfctl arch context` and the domain model under `<arch-root>/domain/` before choosing a method, and sends a change to a modeled term's meaning to `model-the-domain` first. Copy only that opening. Don't copy the line telling the agent not to run `wfctl arch none`, since the Spec Kit design step still requires a record or a declaration (FR-012), and `design-levels` tells the agent to run it further down level 2. This task depends on T008, which edits the same file. Verify with `uv run pytest tests/test_skill_cross_references.py -q -k level_2`
- [X] T035 [US3] Compare the two openings with `grep -n -A6 "wfctl arch context" wfctl/agents/skills/design-levels/SKILL.md wfctl/agents/skills/design-passes/SKILL.md`, and confirm the wording matches (US3 scenario 1). Then validate with `uv run pytest -q` — merge gate

**Checkpoint**: All three stories work on their own.

---

## Phase 6: Polish and cross-cutting

- [X] T036 Add `change_sections` to the "Declaring what a change must carry" section of `AGENTS.md`, beside `change_check`. Say what it lists, that it lives in `wfctl.json` for the same reason `change_check` does, and that `wfctl check config` validates it. This task runs after T013, which edits the same file. Verify by reading the section back, and with `uv run wfctl check config`
- [X] T037 [P] Create the release note with `uv run towncrier create 628.addition.md --content "…"`, written for an existing user of wfctl, with the `writing-style` skill loaded; verify with `uv run wfctl verify`
- [X] T038 Run `uv run wfctl install-skills --prune --yes --agent claude`, then `uv run wfctl doctor`; verify that every layer reports ✓
- [x] T039 Validate the feature with `uv run pytest -q`, `uv run ruff check wfctl/ tests/`, `uv run mypy wfctl/`, and `uv run wfctl check config` — merge gate

---

## Dependencies and execution order

### Phase dependencies

- **Setup (Phase 1)**: no dependencies. T002 runs before any US2 code, since it saves today's output.
- **Foundational (Phase 2)**: empty.
- **US1 (Phase 3)** and **US2 (Phase 4)**: each starts after Setup, independently of the other.
- **US3 (Phase 5)**: after T005, whose wording it copies, and T008, which edits the same file.
- **Polish (Phase 6)**: after the stories it touches. T036 runs after T013, and T038 runs after every skill edit.

### Within each story

- Tests are written, run, and failing first: T003 and T004 before T005 to T013, and T017 to T021 before T022 to T029.
- In US2, the module (T022 to T024) comes before the commands call it (T025 and T026), and the commands come before the repo opts in (T027 and T028).
- Each story ends at its merge-gate task.

### Same-file sequences

- `tests/test_skill_cross_references.py`: T003, then T004.
- `tests/test_sections.py`: T017, T018, then T019.
- `wfctl/_sections.py`: T022, T023, then T024.
- `wfctl/cli.py`: T025, then T026.
- `wfctl/agents/skills/design-levels/SKILL.md`: T008, then T034.
- `AGENTS.md`: T013, then T036.

## Parallel opportunities

- US1 and US2 can run at the same time. The only file they share is `AGENTS.md`, edited by T013 and T036.
- In US1, T009, T010, and T011 each edit a different skill file.
- In US2, T017, T020, and T021 each edit a different test file. T029 edits only `fanning-out-code-review` and can run any time after Setup.

### Parallel example: User Story 2

```text
Task: "Create tests/test_sections.py with load_required cases (T017)"
Task: "Add check-body CLI cases to tests/test_shape.py (T020)"
Task: "Add check config cases to tests/test_cli_status.py (T021)"
```

### Parallel example: User Story 1

```text
Task: "Replace the Not for paragraph in architecture-design (T009)"
Task: "Replace the Not for paragraph in model-the-domain (T010)"
Task: "Replace the Not for paragraph in architecture-decisions (T011)"
```

## Implementation strategy

### MVP

US1 alone gives every change that bypasses Spec Kit the design passes, but nothing records the spec answer. US2 alone records and checks the answer, but the route still says "straight to implementation". Both are P1, and the feature needs both. If one has to land first, build US2 first. It's the only check, and US1's route text tells the agent that the answer goes in the PR.

### Incremental delivery

1. Setup (T001 and T002).
2. US2 (T017 to T033): the check, compared against the saved output.
3. US1 (T003 to T016): the skill and the pointers.
4. US3 (T034 and T035).
5. Polish (T036 to T039).

## Open items from the plan review

These are MINOR findings in `plan-review.md`. Each one changes a task's text if Andre decides it, and none of them blocks starting.

- PR-023: the no-reason rule applies to every listed section, so a repo can't list a section where a bare yes or no is a complete answer.
- PR-024: an emphasized "**No.**" passes the no-reason check in T023, since emphasis isn't stripped.
- PR-022: T029 edits `fanning-out-code-review`, which #622 is also redesigning.
- PR-019: after a restart, brainstorm may send a "yes" change back to `design-passes` for one hop.
- PR-016: T007 leaves two sentences in the handoff's route item that contradict the new route.
- The plan's Scale line says it edits four skills, and it now edits six. Its Testing line doesn't name `tests/test_review_fanout_skill.py`. Neither is fixed in plan.md, because any edit there changes the plan's hash, and the plan review would then read as stale.
~~~~
