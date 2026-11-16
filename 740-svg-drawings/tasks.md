---
description: 'Task list for SVG drawings (#740)'
---

# Tasks: SVG drawings

**Input**: Design documents from `wfctl-specs/740-svg-drawings/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/cli.md, quickstart.md

**Tests**: Every story writes its tests first and sees them fail before the code that makes them pass. The suite, `ruff`, `mypy`, and the import check gate every phase.

**Organization**: Tasks are grouped by user story. Paths are relative to the worktree root, except `<scratchpad>`, which is the session's scratchpad directory and is never committed.

**Commit messages**: Once the guard refuses `wfctl arch accept` (T041), a commit message that names the command is refused too. Write the message to a file and commit with `git commit -F <file>`.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependency on an incomplete task)
- **[Story]**: Which user story the task belongs to (US1 to US6)

---

## Phase 1: Setup

**Purpose**: Capture today's results before any code changes, and commit the release note.

- [X] T001 Write `<scratchpad>/drawing_corpus.py`, which dumps `accept_problems` and the `validate` findings for every record in `docs/architecture/` to `<scratchpad>/before.json` or `after.json` and diffs the two (research R-010). Run `uv run python <scratchpad>/drawing_corpus.py before` before the first edit to `wfctl/arch/_records.py`; verify `before.json` holds an entry for every record `load_records` returns
- [X] T002 [P] Create `changes/740.addition.md` with `uv run towncrier create 740.addition.md --content "…"`, saying what a user of wfctl notices: a record's drawing can be an SVG in `drawings/`, wfctl checks it, and accepting a record signs off its drawing (FR-018); verify with `uv run wfctl verify`'s release-note check

---

## Phase 2: Foundational

**Purpose**: Exclude `drawings/` from the record readers, and move the fence reading behind the `Drawing` summary with no change in behavior. Every story builds on this.

**⚠️ CRITICAL**: No story work starts until this phase passes.

- [X] T003 Add a test to `tests/test_design_gate_drawing.py`: a branch whose only change under the arch root is an SVG in `drawings/` hasn't answered the boundary question (spec US1 scenario 5). Run `uv run pytest tests/test_design_gate_drawing.py -q` and see it fail
- [X] T004 Add `DRAWINGS_DIR = "drawings"` to `wfctl/_paths.py` beside `VIEWS_DIR`, add `arch / DRAWINGS_DIR` to `non_record_subtrees`, and say in a comment that the one folder is temporary until #761 (FR-010, FR-019); verify T003 now passes
- [X] T005 Create `wfctl/arch/_drawing.py` with the frozen `Drawing` and `Problem` dataclasses from `data-model.md`, and move `_labels` (as `fence_labels`), `_draws_a_failure`, and their regular expressions and docstrings from `wfctl/arch/_records.py` unchanged. Add `read_fence(text) -> Drawing`, which sets `failure_fix` to today's fence text (`740-one-drawing-reader`); verify with `uv run pytest tests/test_arch_labels.py -q` after T006
- [X] T006 Change `tests/test_arch_labels.py` to import `fence_labels` from `wfctl.arch._drawing` instead of calling `_records._labels`, with every assertion unchanged; verify with `uv run pytest tests/test_arch_labels.py -q`
- [X] T007 Change `_drawing(record)` and `_drawings(record)` in `wfctl/arch/_records.py` to return `Drawing` through `read_fence`, keeping their heading rules. Change `validate`, `_sequence_drawing`, `_drawing_refusals`, and `accept_blockers` to read `labels`, `shows_failure`, and `failure_fix` from the summary, and build the failing-step line as `f"a sequence drawing with no step that fails: {drawing.failure_fix}"`; verify with `uv run pytest tests/test_arch_accept_drawing.py tests/test_arch_diagram_kinds.py tests/test_arch_labels.py -q`, all unchanged
- [X] T008 Validate Phase 2 with `uv run pytest -q`, `uv run ruff check wfctl/ tests/`, `uv run mypy`, and `python3 .github/scripts/check_imports.py`, then `uv run python <scratchpad>/drawing_corpus.py after` showing no difference from `before.json` — merge gate

**Checkpoint**: The fence path runs through the summary, and nothing a user sees has changed.

---

## Phase 3: User Story 1 - A record whose drawing is an SVG can be accepted (Priority: P1) 🎯 MVP

**Goal**: A record whose only drawing is an SVG in `drawings/`, linked as a markdown image, passes acceptance, and a broken link gets one line naming the problem.

**Independent Test**: A throwaway record with `diagram: data-flow` whose only drawing is a linked SVG passes `wfctl arch accept --dry-run`. Delete the SVG, and it refuses, naming the missing path.

**Verification**:

- Automated: `tests/test_arch_drawing_svg.py`, `tests/test_arch_diagram_kinds.py`, `tests/pipeline_payload_snapshot.json`
- Manual: quickstart §3, the dry run with the SVG renamed
- Evidence: the problem line replaces `no drawing` and is never printed beside it

### Tests for User Story 1 ⚠️

> Write these first and see them fail.

- [X] T009 [P] [US1] In `tests/test_arch_drawing_svg.py`, test that `read_svg` finds an SVG link outside a fence, ignores a URL, a `data:` URI, and a non-`.svg` image, and returns `format="svg"` with no problem for a valid file in `drawings/` (research R-007)
- [X] T010 [P] [US1] In `tests/test_arch_drawing_svg.py`, test each problem in `data-model.md`: a missing file, a link outside `drawings/`, a leading-slash link, a symlink in `drawings/` pointing elsewhere, a DOCTYPE, a UTF-16 file carrying a DOCTYPE, a UTF-8 file declaring `encoding="UTF-16"`, invalid XML, a directory named `x.svg`, a heading with both an SVG and a fence, and a heading with two SVG links (FR-001 to FR-003, FR-025, research R-001, R-008, R-009)
- [X] T011 [P] [US1] In `tests/test_arch_drawing_svg.py`, test the full `accept_problems` list for a one-kind and a multi-kind record with a problem, showing the problem line where `no drawing` or `doesn't draw one` would sit, and never beside it (`contracts/cli.md`, PR-002)
- [X] T012 [P] [US1] In `tests/test_arch_drawing_svg.py`, test that `validate` warns with the problem text for a one-kind proposed record in each problem case (PR-003)

### Implementation for User Story 1

- [X] T013 [US1] Add `read_svg(link, record_dir) -> Drawing` to `wfctl/arch/_drawing.py`: reject a leading slash, resolve against `record_dir`, check containment in `record_dir / DRAWINGS_DIR` after resolving, read bytes, decode as UTF-8, refuse a DOCTYPE in the decoded text, and parse that text with `xml.etree.ElementTree.fromstring`. `ParseError`, `OSError`, and `ValueError` become the `can't be read` problem (research R-001, R-002, R-008); verify with T009 and T010
- [X] T014 [US1] In `wfctl/arch/_records.py`, teach the heading logic in `_drawing` and `_drawings` to find markdown image links outside fences with `_md.walk_lines`, choose `read_svg` or `read_fence`, and set a problem for both formats or two SVG links under one heading (research R-007, R-009); verify with T009 and T010
- [X] T015 [US1] In `wfctl/arch/_records.py`, have `accept_problems`, `_drawing_refusals`, and `accept_blockers` print `<problem>: <fix>` for a one-kind record, and `Refusal("### <kind>: <problem>", <fix>)` for a multi-kind one, in place of the missing-drawing line. Have the failing-step and label checks skip a drawing with a problem; verify with T011
- [X] T016 [US1] In `validate` in `wfctl/arch/_records.py`, add the problem warning for a one-kind proposed record; verify with T012
- [X] T017 [US1] Reword the `no drawing` fix to `add an SVG image or a fenced block under '## Boundary'`, and update its two occurrences in `tests/pipeline_payload_snapshot.json` (FR-011); verify with `uv run pytest tests/test_pipeline_payload_snapshot.py -q`
- [X] T018 [US1] Reword each `_DRAWING_FIX` entry in `wfctl/arch/_records.py` to the text in `contracts/cli.md`, and update the two `sequence` assertions in `tests/test_arch_diagram_kinds.py` (lines 207-213 and 299-307) with no other assertion changed (FR-011, PR-015); verify with `uv run pytest tests/test_arch_diagram_kinds.py -q`
- [X] T019 [US1] Validate US1 with `uv run pytest -q`, `uv run ruff check wfctl/ tests/`, `uv run mypy`, and quickstart §3 on a scratch record — merge gate

**Checkpoint**: An SVG-only record can be accepted, and every fence record behaves as before.

---

## Phase 4: User Story 2 - wfctl checks what an SVG drawing shows (Priority: P1)

**Goal**: The label check and the failing-step rule read an SVG through the summary.

**Independent Test**: A proposed record with a sequence SVG carrying a label missing from the prose and no `failing-step` class gets both doctor warnings, and `wfctl arch accept --dry-run` refuses for the failing step. Adding the class and the word clears both.

**Verification**:

- Automated: `tests/test_arch_drawing_svg.py`
- Manual: none
- Evidence: each check passes once with an SVG summary and once with a fence summary, with no format code in the check

### Tests for User Story 2 ⚠️

- [X] T020 [P] [US2] In `tests/test_arch_drawing_svg.py`, test that labels come from each `<text>` with its `<tspan>` text joined by spaces, that `class="arrow failing-step"` counts as the failing step, that a `refused-edge` class changes nothing, and that `failing-step` on a non-sequence kind changes nothing (FR-004, FR-006, FR-007)
- [X] T021 [P] [US2] In `tests/test_arch_drawing_svg.py`, run the label check and the failing-step check once with an SVG summary and once with a fence summary, and test the SVG wording of the failing-step refusal and the doctor warning from `contracts/cli.md` (FR-005, FR-006)

### Implementation for User Story 2

- [X] T022 [US2] In `read_svg` in `wfctl/arch/_drawing.py`, fill `labels` from `<text>` and `<tspan>`, `shows_failure` from any element whose class list includes `failing-step`, and `failure_fix` as `add class="failing-step" to the element that fails`; verify with T020 and T021
- [X] T023 [US2] Confirm the label check in `validate` and `_sequence_drawing` read only the summary, and that the doctor warning prints `declares a sequence diagram with no step that fails — <failure_fix>`; verify with T021 and `grep -n "ElementTree\|<text" wfctl/arch/_records.py` finding nothing
- [X] T024 [US2] Validate US2 with `uv run pytest -q`, `uv run ruff check wfctl/ tests/`, and `uv run mypy` — merge gate

**Checkpoint**: Both P1 stories work, and an SVG gets the same checks as mermaid.

---

## Phase 5: User Story 3 - doctor warns about a label running off the drawing (Priority: P2)

**Goal**: `wfctl doctor` warns about a proposed record's label whose estimated width puts it past the drawing's edge.

**Independent Test**: A proposed record with an SVG 400 units wide and a 40-character label at x=380 gets the warning. Moving it to x=20 clears it.

**Verification**:

- Automated: `tests/test_arch_drawing_svg.py`
- Manual: quickstart §4, the "file missi" recreation
- Evidence: the warning fires on `<text x="708" y="180" class="label">file missing</text>` in a 760-wide `viewBox` and not on the corrected label

### Tests for User Story 3 ⚠️

- [X] T025 [P] [US3] In `tests/test_arch_drawing_svg.py`, test the edge with each `text-anchor`, from `viewBox` and from `width` with `px` stripped, no warning with a percentage width or neither attribute, the font-size lookup order from research R-005 including a selector list and a rule inside `@media` being skipped, a label in a transformed group measured as written, and the "file missi" fixture (FR-008, research R-003 to R-006, SC-005)
- [X] T026 [P] [US3] In `tests/test_arch_drawing_svg.py`, test that an accepted record with the same SVG gets no edge warning, and a multi-kind record gets the edge check on each kind's SVG

### Implementation for User Story 3

- [X] T027 [US3] In `read_svg` in `wfctl/arch/_drawing.py`, read the edge, resolve each label's font size, estimate its extent as `len(text) × 0.6 × font_size` from its anchor, and fill `past_edge` (research R-003 to R-006); verify with T025
- [X] T028 [US3] In `validate` in `wfctl/arch/_records.py`, warn `drawing label '<text>' runs past the drawing's edge` for each `past_edge` entry on a proposed record; verify with T025 and T026
- [X] T029 [US3] Validate US3 with `uv run pytest -q`, `uv run ruff check wfctl/ tests/`, `uv run mypy`, and quickstart §4 — merge gate

---

## Phase 6: User Story 6 - Accepting a record is the user's sign-off on its drawing (Priority: P2)

**Goal**: Accepting a record writes each SVG's fingerprint, doctor warns when one changes, a redraw signs it off again, an agent can't run the real accept, and a redraw-only branch doesn't count as changing a record.

**Independent Test**: Accept a record with an SVG from a real terminal and see the fingerprint on its Log line. Edit the SVG, and doctor warns. Accept again, and the warning clears. The same accept from the agent's shell is refused.

**Verification**:

- Automated: `tests/test_arch_drawing_fingerprint.py`, `tests/test_review_gate.py`, `tests/test_arch_accept.py`, `tests/test_redraw_only.py`, `tests/test_paths_redraw.py`, `tests/test_record_gate.py`, `tests/test_design_gate_drawing.py`, `tests/test_scan_files.py`
- Manual: quickstart §6, run by the user in a scratch clone from their own terminal
- Evidence: SC-007 and SC-008

### Tests for User Story 6 ⚠️

- [X] T030 [P] [US6] In `tests/test_arch_drawing_fingerprint.py`, test that the `accepted` Log line ends with each SVG's link and fingerprint in heading order, a fence record's line is unchanged, and CRLF and LF copies of one SVG get the same fingerprint (FR-020)
- [X] T031 [P] [US6] In `tests/test_arch_drawing_fingerprint.py`, test that doctor warns about an accepted record whose SVG changed or has a problem, not about one that matches or has no fingerprint, and not about a superseded or retired record (FR-021)
- [X] T032 [P] [US6] In `tests/test_arch_drawing_fingerprint.py`, test that accept on a changed accepted record appends a `redrawn` line, leaves `status: accepted`, keeps `accepted_on` at the original date, and clears the warning; that a redraw of an SVG with no fingerprint on the Log writes the line; that a redraw is refused when the edited SVG dropped `failing-step`; and that accept on a matching record refuses as today (FR-022)
- [X] T033 [P] [US6] In `tests/test_review_gate.py`, test that `wfctl arch accept x --agreed y` and `uv run wfctl arch accept x --agreed y` are refused, `wfctl arch accept --dry-run -- x` isn't, a `--dry-run` on one command doesn't let a second accept through, `--dry-run` inside a quoted citation doesn't count, and a part `shlex` can't split is refused (FR-023)
- [X] T034 [P] [US6] In `tests/test_arch_accept.py`, test that accept without `--dry-run` refuses before writing when stdin or stdout isn't a terminal (FR-024)
- [X] T035 [P] [US6] Create `tests/test_redraw_only.py`, covering `arch.redraw_only` without git. Each case breaks one condition and returns false: a proposed record, an empty diff, a `redrawn`-shaped bullet added under `## Decision`, an added line that isn't a `redrawn` line, and a removed line. A Log whose last line had no newline still reads as a redraw, even though the re-added last line doesn't match `REDRAWN_LINE`. A line `_append_log` writes matches `REDRAWN_LINE` (research R-014, PR-026, PR-027)
- [X] T036 [P] [US6] Create `tests/test_paths_redraw.py`, running `record_change` and `decided_on_this_branch` on a real git repo: an uncommitted edit beside a committed redraw counts, an untracked record counts, a record deleted in the working tree counts, and a record with no trunk to compare against counts (PR-025)
- [X] T037 [P] [US6] Extend `tests/test_record_gate.py` and `tests/test_design_gate_drawing.py`: a branch whose only record change is a `redrawn` line passes the record gate with "no boundary moved" in place, and the design gate still reads that answer; an `accepted` line added beside the `redrawn` line still counts; and a redraw as the only arch-root change with no exception reads as unanswered, once with a domain-page name list and once without (FR-026, PR-020)
- [X] T038 [P] [US6] Extend `tests/test_scan_files.py`: a redraw-only branch prints no `record:` line for that record, and its `Boundary` line reads `unanswered` (FR-026)

### Implementation for User Story 6

- [X] T039 [US6] Add `fingerprint(path) -> str` to `wfctl/arch/_drawing.py`, the first 12 hex digits of SHA-256 over the bytes with CRLF replaced by LF (research R-011); verify with T030
- [X] T040 [US6] In `wfctl/arch/_records.py`, extract `_append_log` from `_set_status` so both write a Log line one way, add `REDRAWN_LINE` beside `_LOG_STATUS_WIDTH`, and have accept append ` · drawing <link> sha256:<hex>` per SVG to the citation (research R-011, R-012); verify with T030 and `uv run pytest tests/test_arch_accept.py -q`
- [X] T041 [US6] In `wfctl/_review_gate.py`, add `ACCEPT_REFUSAL` and refuse a command matching `\bwfctl\s+arch\s+accept\b` unless the same `_SEPARATOR` part carries `--dry-run` as a whole `shlex` word (research R-013); verify with T033
- [X] T042 [US6] In `arch_accept_cmd` in `wfctl/cli.py`, call `_at_terminal()` after every existing refusal and immediately before the write, refusing with the line in `contracts/cli.md`. Patch `_at_terminal` to return true in the real-accept tests in `tests/test_arch_accept.py`, `tests/test_arch_accept_drawing.py`, and `test_a_citation_pasted_from_a_bullet_is_a_citation_and_not_a_flag` in `tests/test_arch_accept_dry_run.py` (R-013, PR-021); verify with T034 and `uv run pytest tests/test_arch_accept.py tests/test_arch_accept_drawing.py tests/test_arch_accept_dry_run.py -q`
- [X] T043 [US6] In `arch_accept_cmd` and `wfctl/arch/_records.py`, add the redraw path for an accepted record in the order `contracts/cli.md` gives: rerun every acceptance check, append a `redrawn` line when an SVG doesn't match or has no fingerprint, and otherwise refuse as today. The `redrawn` write sits behind the same `_at_terminal()` check T042 adds, so the redraw path can't write without a terminal either. `--dry-run` says which row it would take (FR-022, FR-024); verify with T032 and T034
- [X] T044 [US6] In `validate` in `wfctl/arch/_records.py`, warn for an accepted record's drawing problem and for each SVG whose fingerprint differs from the last `accepted` or `redrawn` line naming it (FR-021, `data-model.md` "Reading it back"); verify with T031
- [X] T045 [US6] Add `redraw_only(diff, text) -> bool` to `wfctl/arch/_records.py` with the four conditions in research R-014, and export it from `wfctl/arch/__init__.py`; verify with T035
- [X] T046 [US6] In `wfctl/_paths.py`, add `record_change`, `decided_on_this_branch`, and the `skip` keyword on `records_on_this_branch`, as research R-014 describes; verify with T036
- [X] T047 [US6] Pass `skip=arch.redraw_only` in `_record_gate.touched` (through the guard's session, so a git error refuses), `_evidence.branch_records`, `_evidence._level_records`, and the `record:` lines in `wfctl/cli.py`. Switch `_evidence._architecture_answered` and `cli._observe`'s `Boundary` line to `decided_on_this_branch` (R-014, PR-020); verify with T037, T038, and `python3 .github/scripts/check_imports.py`
- [X] T048 [US6] Validate US6 with `uv run pytest -q`, `uv run ruff check wfctl/ tests/`, `uv run mypy`, and `python3 .github/scripts/check_imports.py` — merge gate

**Checkpoint**: The user's sign-off is enforced, and a layout fix on a later branch doesn't trip the gates.

---

## Phase 7: User Story 4 - The skills teach SVG in one style (Priority: P2)

**Goal**: The style is written once and linked from the four skills that teach drawing, and the templates ask for SVG by default.

**Independent Test**: After `uv run wfctl install-skills`, an agent draws one record's SVG from `architecture-decisions`, renders it, and it meets each rule in the style file.

**Verification**:

- Automated: `tests/test_drawing_style_links.py`
- Manual: quickstart §5, the agent drawing and the two greps
- Evidence: SC-006

### Tests for User Story 4 ⚠️

- [ ] T049 [P] [US4] Create `tests/test_drawing_style_links.py`, failing when any of the four links to `design-levels/references/drawing-style.md` points at a file that doesn't exist (FR-014)

### Implementation for User Story 4

- [ ] T050 [US4] Write `wfctl/agents/skills/design-levels/references/drawing-style.md`, covering every rule FR-012 lists, the layout-only rule for an accepted record's SVG, avoiding `transform` on text (research R-006), and a pointer to #761 saying the one folder and the name convention are temporary (FR-019, `740-drawing-style-one-file`); verify by reading it against FR-012's list
- [ ] T051 [P] [US4] Rewrite `wfctl/agents/skills/design-levels/SKILL.md:371-374` as the plan's skill-prose table gives, with one sentence in "Rendering the gate's answer" linking the style file (FR-013); verify with T049
- [ ] T052 [P] [US4] Rewrite the five `wfctl/agents/skills/architecture-decisions/SKILL.md` passages in the plan's table (`:92-105`, `:119-124`, `:139-140`, `:230-237`, `:284-289`) and link the style file; verify with T049 and the quickstart §5 mermaid grep
- [ ] T053 [P] [US4] Link the style file from `wfctl/agents/skills/software-design-decisions/SKILL.md`; verify with T049
- [ ] T054 [P] [US4] Rewrite `wfctl/agents/skills/model-the-domain/SKILL.md:250` and `wfctl/agents/skills/model-the-domain/references/visual-language.md:3-7` as the plan's table gives, keeping mermaid for domain documents until #761; verify with T049 and the quickstart §5 mermaid grep
- [ ] T055 [P] [US4] Make `wfctl/agents/skills/architecture-decisions/record-template.md` and `wfctl/agents/skills/software-design-decisions/design-record-template.md` ask for an SVG drawing by default and say a mermaid block still passes (FR-015); verify by reading both after `uv run wfctl install-skills`
- [ ] T056 [P] [US4] Do the same in `wfctl/agents/skills/architecture-design/views/system-context.md`, `container.md`, and `component.md` (FR-015); verify by reading the three after `uv run wfctl install-skills`
- [ ] T057 [US4] Validate US4: `uv run pytest -q`, `uv run wfctl install-skills`, `uv run wfctl doctor`, the two greps in quickstart §5, then have a fresh agent draw one record's SVG from the installed `architecture-decisions` skill, render it with `qlmanage -t -s 1200 -o <scratchpad> <file>.svg`, and check it against each rule in `drawing-style.md` — merge gate

---

## Phase 8: User Story 5 - This feature's own record drops its mermaid copy (Priority: P3)

**Goal**: `record-drawing-can-be-svg.md` relies on its SVG alone.

**Independent Test**: With the mermaid block and the sentence about it removed, `wfctl arch accept --dry-run -- record-drawing-can-be-svg` reports nothing about the drawing.

**Verification**:

- Automated: none beyond the suite
- Manual: quickstart §3
- Evidence: SC-003

- [ ] T058 [US5] Remove the mermaid block and the "crossed in the mermaid copy" wording from `docs/architecture/record-drawing-can-be-svg.md` (FR-016); verify with `uv run wfctl arch accept --dry-run -- record-drawing-can-be-svg` and `uv run wfctl doctor` reporting no drawing finding for it
- [ ] T059 [US5] Validate US5 with quickstart §3, including the rename that refuses with `drawing links drawings/record-drawing-can-be-svg-data-flow.svg, which doesn't exist` and no `no drawing` line — merge gate

---

## Phase 9: Polish & Cross-Cutting

- [ ] T060 [P] Document in `docs/reference.md` that a drawing can be a linked SVG in `drawings/`, the `failing-step` class, the fingerprint on the Log line, and the redraw (FR-017); verify by reading it against `contracts/cli.md`
- [ ] T061 Run `uv run python <scratchpad>/drawing_corpus.py after` and confirm the only differences from `before.json` are the `no drawing` wording and `record-drawing-can-be-svg` (SC-002, research R-010); keep the summary line for the PR's verification notes
- [ ] T062 Run `uv run pytest -q`, `uv run ruff check wfctl/ tests/`, `uv run mypy`, `python3 .github/scripts/check_imports.py`, `uv run wfctl install-skills`, `uv run wfctl doctor`, `uv run wfctl check config`, and `uv run wfctl verify`; all pass and report nothing new
- [x] T063 Ask the user to run quickstart §6 from their own terminal in a scratch clone, since the guard refuses the real accept from an agent (SC-007, SC-008)
- [ ] T064 Ask the user to run quickstart §7, the phone check in light and dark mode, before the PR merges

---

## Dependencies & Execution Order

### Phase dependencies

- **Setup (Phase 1)**: T001 runs before any edit to `wfctl/arch/_records.py`. T002 can run any time.
- **Foundational (Phase 2)**: depends on T001, and blocks every story.
- **US1 (Phase 3)**: depends on Phase 2.
- **US2 (Phase 4)**: depends on US1, since `read_svg` and the heading logic come from T013 and T014.
- **US3 (Phase 5)**: depends on US1 for `read_svg`. Independent of US2.
- **US6 (Phase 6)**: depends on US1 for SVG links. T041, T042, and T046 depend only on Phase 2 and can start earlier. T045 also needs T040, since `redraw_only` matches the `REDRAWN_LINE` that T040 adds and T035 checks it against `_append_log`. T047 needs T045 and T046.
- **US4 (Phase 7)**: depends on US1, since a skill can't teach SVG as the default while acceptance refuses it. The prose tasks don't depend on US2, US3, or US6.
- **US5 (Phase 8)**: depends on US1 and US2.
- **Polish (Phase 9)**: depends on every story.

### Within each story

- Tests are written first and seen failing.
- `_drawing.py` changes come before the `_records.py` checks that read them.
- T045 and T046 come before T047, which wires them in.

### Parallel opportunities

- All test tasks marked [P] in a phase can be written together.
- In US6, the guard and terminal work (T041, T042), the fingerprint work (T039, T040, T043, T044), and the redraw exclusion (T045 to T047) touch different code and can run side by side, though T040 and T045 both edit `_records.py` and T042 and T047 both edit `cli.py`.
- In US4, T051 to T056 each edit a different file.

## Parallel Example: User Story 6

```bash
Task: "Fingerprint tests in tests/test_arch_drawing_fingerprint.py"
Task: "Guard tests in tests/test_review_gate.py"
Task: "redraw_only tests in tests/test_redraw_only.py"
Task: "record_change tests in tests/test_paths_redraw.py"
```

## Implementation Strategy

### MVP first

1. Phase 1 and Phase 2.
2. US1. Stop and validate: an SVG-only record can be accepted, and every fence record is unchanged.

### Incremental delivery

1. US2, so the SVG gets the same checks as mermaid. With US1, this is the issue's goal.
2. US3 and US6, the edge warning and the sign-off.
3. US4, the skills and templates.
4. US5, the feature's own record.
5. Polish, then the user's two manual checks.

## Design records

Design records: 2 listed in design.md
  docs/architecture/design/740-one-drawing-reader.md
  docs/architecture/design/740-drawing-style-one-file.md
