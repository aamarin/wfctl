# Tasks: record leads with drawing

**Input**: Design documents from `specs/109-record-leads-with-drawing/`
**Prerequisites**: `plan.md`, `spec.md`, `research.md`, `data-model.md`, `contracts/`, `quickstart.md`

**Tests**: The refusals *are* the feature (spec, Validation Strategy), so a suite
covering only the success path has not tested it. Every phase names its
verification, and the two things the suite cannot reach — a skills change reading
well, and mermaid rendering on github.com — are manual tasks rather than implied
coverage.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: different file, no dependency on an incomplete task
- **[Story]**: `[US1]` `[US2]` `[US3]`, mapping to `spec.md`
- Every implementation task names its verification path

## Path Conventions

Single project. `wfctl/` and `tests/` at the repository root, per `plan.md`'s
Structure Decision. Records live under `uv run wfctl arch-root`, which in this
repository is `docs/architecture/`.

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: capture the baseline the "nothing else moved" criteria are measured
against. There is no project to initialize — `uv run` resolves the environment
from `uv.lock` on first use (AGENTS.md).

- [X] T001 Capture the pre-change projection: `uv run wfctl arch context > /tmp/109-context-before.txt`; this is the fixture SC-006 and FR-011 are compared against in T034
- [X] T002 [P] Capture the five accepted records' hashes: `git ls-files -s docs/architecture/*.md > /tmp/109-records-before.txt`; SC-002 is compared against it in T035
- [X] T003 Confirm the baseline is green: `uv run pytest -q && uv run ruff check wfctl/ tests/ && uv run mypy wfctl/` — a red baseline makes every later verification unreadable

**Checkpoint**: baseline recorded, suite green.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: the declared kind and the section scanner. Both US1 and US2 read
them — US1's refusal names the kinds (FR-005) and US2's finding validates them
(FR-003) — so per the data-model rule for an entity serving two stories they land
here rather than in either.

**⚠️ CRITICAL**: no user story work begins until this phase is complete.

- [X] T004 Add `DIAGRAM_KINDS: tuple[str, ...] = ("data-flow", "component", "state")` to `wfctl/_arch.py` beside `STATUSES`, with a comment saying why it is a tuple where `STATUSES` is a frozenset — the refusal prints it and print order is the guidance's order (data-model.md, Diagram kind); verify with `tests/test_arch_diagram.py::test_the_three_kinds_are_the_ones_the_template_names` from T007
- [X] T005 Add `diagram: str = ""` to `Record` in `wfctl/_arch.py` and lift `front.get("diagram", "")` onto it in `parse_record`, carrying the value **verbatim** rather than normalising an unrecognised one to `""`; the docstring says why this differs from `status` (research R-001); verify with `tests/test_arch_diagram.py` from T007
- [X] T006 Generalise `_log_bounds` in `wfctl/_arch.py` into `_section_bounds(lines, heading)` and make `_log_bounds` a call to it with `"## log"`, keeping both reasons its docstring already gives — fenced examples are skipped, and the section ends at the next `## ` rather than at end of file (research R-003); verify with the existing `tests/test_arch*.py` suite plus `tests/test_arch_sections.py` from T008
- [X] T007 [P] Write `tests/test_arch_diagram.py` covering FR-001 (a declared kind is read back), FR-002 (absent reads as `""`, never a default) and a value outside the set surviving parsing verbatim; docstrings name the failure each test catches, per the repository's testing conventions
- [X] T008 [P] Write `tests/test_arch_sections.py` asserting `_section_bounds` finds `## Boundary`, stops at the next `## `, and skips a `## Boundary` quoted inside a fence — the case `contracts/record-format.md` is itself an instance of
- [X] T009 Validate Phase 2 with `uv run pytest -q tests/test_arch_diagram.py tests/test_arch_sections.py && uv run mypy wfctl/` — merge gate

**Checkpoint**: the kind is readable and one section scanner serves both headings. User stories can begin.

---

## Phase 3: User Story 1 — A record cannot be accepted without its drawing (Priority: P1) 🎯 MVP

**Goal**: `wfctl arch accept` refuses a record that carries no drawing, says what
to add, and changes nothing on disk. The promotable listing stops offering
records whose own suggested command would fail.

**Independent Test**: take any proposed record with no drawing, run `uv run wfctl
arch accept <slug> --agreed "test"`, read the refusal, add a drawing, run it
again, watch it succeed. Nothing else in the feature has to exist.

**Verification**:

- Automated: `tests/test_arch_accept_drawing.py`, one test per acceptance
  scenario including all four refusals
- Manual: the refusal read cold by someone who has not opened
  `architecture-decisions/SKILL.md` — SC-005's bar is that they can produce a
  conforming record from it alone (T017)
- Evidence: `git diff --stat docs/architecture/` empty after every refusal

### Tests for User Story 1 ⚠️

> Write these first and confirm they fail before implementing.

- [X] T010 [P] [US1] Write `tests/test_arch_accept_drawing.py` covering spec scenarios 1–4: a proposed record with no drawing is refused and the file is unchanged; one with a drawing and a kind accepts as it does today; an accepted record with no drawing is never read or modified (FR-006); the promotable listing excludes a record acceptance would refuse (FR-007)
- [X] T011 [P] [US1] Add to the same file the two kind refusals — a drawing with no declared kind (FR-005) and a drawing whose kind is outside `DIAGRAM_KINDS` — asserting the refusal text names the three permitted values, per `contracts/cli.md`

### Implementation for User Story 1

- [X] T012 [US1] Add `_drawing(record) -> str` to `wfctl/_arch.py`, returning the interior of the first fenced block under `## Boundary` via `_section_bounds` and `_md.walk_lines`, `""` otherwise; content is never inspected (clarification Q2); verify with `tests/test_arch_sections.py` and `tests/test_arch_accept_drawing.py`
- [X] T013 [US1] Add `accept_blockers(record) -> list[str]` to `wfctl/_arch.py`, returning the four blockers of `data-model.md` in reading order, with the docstring saying why status is not among them; verify with `tests/test_arch_accept_drawing.py`
- [X] T014 [US1] Rewrite `acceptable` as `record.status == "proposed" and not accept_blockers(record)`, keeping the docstring's existing account of why a second copy of the rule is the failure it exists to prevent (research R-002); verify with the listing test in T010
- [X] T015 [US1] Make `accept` raise when `accept_blockers` is non-empty, following `_set_status`'s precedent that the module owns the invariant and every caller gets it; verify with `tests/test_arch_accept_drawing.py`
- [X] T016 [US1] Implement the refusal in `wfctl/cli.py`'s `arch accept` — call `accept_blockers` before `_arch.accept`, print each blocker and the kind table exactly as `contracts/cli.md` shows, exit 1 writing nothing, after the existing status and citation refusals; verify with `tests/test_arch_accept_drawing.py` and by running the Independent Test above
- [X] T017 [US1] Read the refusal cold against SC-005 — can a reader who has not opened the skill produce a conforming record from it alone? Record the judgment in the PR body; this is a manual check and no assertion covers it
- [X] T018 [US1] Validate Phase 3 with `uv run pytest -q && uv run ruff check wfctl/ tests/ && uv run mypy wfctl/` — merge gate

**Checkpoint**: the gate is real. Shipped alone this changes the corpus permanently.

---

## Phase 4: User Story 2 — The record says which kind of drawing it carries (Priority: P2)

**Goal**: an unrecognised kind is reported rather than ignored, and the author
can name the kind their decision needs without asking anyone.

**Independent Test**: write a record declaring each of the three kinds in turn
and confirm each reads back; declare a fourth word and confirm `uv run wfctl
doctor` names it. Testable without the accept gate existing.

**Verification**:

- Automated: `tests/test_arch_diagram.py` for VR-006,
  `tests/test_arch_sections.py::test_kinds_match_the_shipped_template` for FR-010
- Manual: `uv run wfctl install-skills --prune --yes --agent claude`, then write
  a record start to finish from the installed template (T023) — a green suite is
  not evidence about a skills change (AGENTS.md)
- Evidence: a record declaring `dataflow` appears as `✗` in `wfctl doctor`; the
  installed `record-template.md` carries the `diagram:` line

### Tests for User Story 2 ⚠️

- [X] T019 [P] [US2] Add VR-006 tests to `tests/test_arch_diagram.py`: a kind outside `DIAGRAM_KINDS` is an `error`-level `Finding` naming the record and the value (FR-003), and it fires on accepted records too because it reads frontmatter, which VR-005 does not freeze
- [X] T020 [P] [US2] Add `test_kinds_match_the_shipped_template` to `tests/test_arch_sections.py` — every value in `DIAGRAM_KINDS` appears in the packaged `record-template.md` and the template names no kind the constant lacks, loading the template through `importlib.resources.files` as `tests/test_pipeline_sections.py` does (FR-010, research R-009)

### Implementation for User Story 2

- [X] T021 [US2] Add VR-006 to `_arch.validate` — an `error` `Finding` for a `diagram` value outside `DIAGRAM_KINDS`, with a comment saying why it runs on every status where VR-007 does not; verify with `tests/test_arch_diagram.py`
- [X] T022 [US2] Update `wfctl/agents/skills/architecture-decisions/record-template.md`: add `diagram: <data-flow | component | state>` to the frontmatter, and rewrite `## Boundary`'s placeholder from "Optional… Delete the section if…" to required, keeping the heading name (FR-009); verify with T020's drift test
- [X] T023 [US2] Add the kind table to `wfctl/agents/skills/architecture-decisions/SKILL.md` — which kind suits which decision, in `DIAGRAM_KINDS` order (FR-012), and a line in its verification list for the drawing; verify by T024's end-to-end pass
- [X] T024 [US2] Run `uv run wfctl install-skills --prune --yes --agent claude`, then write one record end to end from the installed template and accept it; only `uv run` wfctl, never the bare one, or the change being tested is not what gets installed (AGENTS.md)
- [X] T025 [US2] Validate Phase 4 with `uv run pytest -q && uv run wfctl doctor` — merge gate

**Checkpoint**: an author reaching for the template gets the kind and the requirement together.

---

## Phase 5: User Story 3 — A drawing that says something the prose does not is surfaced (Priority: P3)

**Goal**: a drawing label whose words appear nowhere else in the record is
reported as a warning, alongside the record findings `doctor` already prints.

**Independent Test**: run `uv run wfctl doctor` over this repository's records
and read every `⚠` it produces. The test of this story is whether a reader agrees
with the findings, which is why it is a warning rather than a refusal.

**Verification**:

- Automated: `tests/test_arch_labels.py`, including the corpus run
- Manual: SC-004's judgment — more than two findings a reader calls wrong and the
  check is miscalibrated and does not ship (T031)
- Evidence: Phase 0 measured 1 finding over the 4 records in range against a
  ceiling of 2 (research R-004); the run is repeated here against whatever the
  corpus holds then

### Tests for User Story 3 ⚠️

- [X] T026 [P] [US3] Write `tests/test_arch_labels.py` covering spec scenarios 1–3: a drawing using only words the record uses reports nothing; a label whose content words appear nowhere else is reported with the label and the record named; a reported record still accepts (FR-008 — the report never refuses)
- [X] T027 [P] [US3] Add scope tests to the same file: VR-007 fires on `proposed` only, and a record with a drawing whose labels are unreadable — an ASCII sketch — produces no finding rather than a false one (research R-004's stated limit, R-005's scope)

### Implementation for User Story 3

- [X] T028 [US3] Add `_labels(drawing) -> list[str]` to `wfctl/_arch.py` — text inside `"…"`, `[…]`, `{…}`, or after `:` on a transition line, with `<br/>` as whitespace and `[*]` yielding nothing; verify with `tests/test_arch_labels.py`
- [X] T029 [US3] Add VR-007 to `_arch.validate` — a `warning` `Finding` for a label none of whose content words appears elsewhere in the record, with the docstring carrying why the whole-phrase and per-word mechanisms were rejected and the counts that rejected them (research R-004); verify with `tests/test_arch_labels.py`
- [X] T030 [US3] Add the corpus test to `tests/test_arch_labels.py` — every `proposed` record in `docs/architecture/` with a `## Boundary`, asserting the finding count stays at or below SC-004's ceiling so the check cannot silently drift into noise
- [X] T031 [US3] Run `uv run wfctl doctor`, read every `⚠` it produces and judge each against SC-004. More than two a reader calls wrong: the check does not ship, and this phase is reverted rather than tuned — that is the spec's own instruction and the level-3 record's Verification
- [X] T032 [US3] Validate Phase 5 with `uv run pytest -q && uv run ruff check wfctl/ tests/ && uv run mypy wfctl/` — merge gate

**Checkpoint**: all three stories functional and independently verifiable.

---

## Phase 6: Polish & Cross-Cutting Concerns

- [X] T033 Append a Log line to `docs/architecture/design/109-traceability-is-label-agreement.md` recording that its stated mechanism was falsified by measurement and narrowed to the one in research R-004, with the counts. The body above the Log stays as written — the record is `proposed`, so its Decision section is editable and the narrowing belongs there too; verify by reading it beside R-004
- [X] T034 Compare `uv run wfctl arch context` against `/tmp/109-context-before.txt` from T001 — identical, per FR-011 and SC-006
- [X] T035 Compare `git ls-files -s docs/architecture/*.md` against `/tmp/109-records-before.txt` from T002 — the five accepted records byte-identical, per SC-002
- [ ] T036 Open a record carrying a mermaid `## Boundary` on github.com and confirm it renders. No automated check covers this and none is proposed (spec, Edge Cases)
- [X] T037 Run `quickstart.md` start to finish as written, fixing the document where it and the code disagree
- [X] T038 Run the review panel over the whole branch before opening a change, per `fanning-out-code-review`; applied findings become commits and every unapplied finding goes under Additional Context in the PR body
- [X] T039 Assert FR-013 in `tests/test_arch_diagram.py`: no per-repository setting gates VR-006, VR-007 or the accept blockers — the checks read a record's status and its file, and nothing reads `wfctl.json`, the tracker config or the manifest. A negative requirement needs a test naming it, or the first opt-in added later breaks nothing visible; verify with `uv run pytest -q tests/test_arch_diagram.py`
- [X] T040 Validate the whole feature with `uv run pytest -q && uv run ruff check wfctl/ tests/ && uv run mypy wfctl/ && uv run wfctl doctor` — merge gate

---

## Dependencies & Execution Order

### Phase Dependencies

```
Phase 1 Setup
   └─► Phase 2 Foundational        DIAGRAM_KINDS · Record.diagram · _section_bounds
         ├─► Phase 3 US1 (P1)      the gate                       ── MVP
         ├─► Phase 4 US2 (P2)      VR-006 · template · guidance
         └─► Phase 5 US3 (P3)      VR-007 · the corpus run
               └─► Phase 6 Polish
```

### User Story Dependencies

- **US1 (P1)**: after Phase 2. Depends on no other story.
- **US2 (P2)**: after Phase 2. Its scenario 4 — a drawing with no declared kind
  is refused — is implemented in US1's `accept_blockers` (T013) because it is a
  refusal, and US2's own Independent Test is written not to need it.
- **US3 (P3)**: after Phase 2. Reads `_drawing` from T012, which is US1's. Taken
  alone, US3 needs T012 and nothing else of US1 — the two touch `validate` and
  `accept` respectively and do not overlap.

### Within Each Story

Tests first and failing; then the module; then the console. `wfctl/_arch.py`
before `wfctl/cli.py` every time — the module owns whether, the console owns how
it reads (research R-002).

### Parallel Opportunities

- T007 and T008 — different test files, both against Phase 2 code
- T010 and T011 — same file, sequential; T010/T011 parallel with T019/T020 and
  T026/T027 only if the stories are staffed separately
- T034, T035 and T036 — three independent checks over a finished tree

## Logical PR Boundaries

Phases 2+3 are one reviewable slice and the MVP: the field, the scanner and the
gate. Split at Phase 2 and the first PR ships a frontmatter key nothing reads,
which is not demonstrable end to end.

Phase 4 is its own slice — it changes `wfctl/agents/`, which carries a manual
verification step the code phases do not, and mixing it into the gate PR means a
reviewer cannot tell which half T024 exercised.

Phase 5 is its own slice and the only one that can be dropped whole. Its merge
gate is a human judgment (T031), and a PR that carries it alongside the gate
would have to be reverted in part rather than declined.

`/speckit.decompose` owns the final boundaries; this section is input to it.

---

## Parallel Example: Phase 2

```bash
# Two test files, no shared state:
Task: "Write tests/test_arch_diagram.py — the declared kind reads back, absent is not a default"
Task: "Write tests/test_arch_sections.py — _section_bounds finds Boundary and skips a fenced example"
```

---

## Implementation Strategy

### MVP first

1. Phase 1 Setup — capture the baseline
2. Phase 2 Foundational — the field and the scanner
3. Phase 3 US1 — the gate
4. **Stop and validate**: run the Independent Test by hand, confirm the refusal
   reads well cold (T017)

That is the whole of what the issue asks for that a machine can hold, and it
changes the corpus permanently on its own.

### Incremental delivery

1. Setup + Foundational → the kind is readable
2. + US1 → a record without a drawing cannot become binding (MVP)
3. + US2 → the author is told which kind to pick, and a typo is named
4. + US3 → a drawing that disagrees with its prose is surfaced, if it passes
   SC-004

### Notes

- `uv run` for every command, never a bare `wfctl` — this repository has two
  installs and only `uv run` answers the question it cares about (AGENTS.md).
- Tests assert on console output, so anything touching output pins `NO_COLOR`.
- Test names are sentences and docstrings say why the test exists, naming the
  failure it caught.
- Comments explain why this shape, not what the line does. A comment that only
  makes sense beside the diff belongs in the commit message.
- The ruff rule set stays `E4,E7,E9,F`. Do not enable `I`, `UP`, `PL` or `RUF`
  as a drive-by (#14).
