# Tasks: reply over-explains

**Input**: Design documents from `<spec root>/102-reply-over-explains/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/, quickstart.md, judgment-test.md

**Tests**: `tests/test_response_shape_invariants.py` is new and required by FR-012.
It enforces the invariants this feature introduces; without it
`contracts/skill-structure.md` is documentation of rules nothing checks. Three of
its four assertions are **red today** and go green as their phase lands.

**Organization**: grouped by user story. Note the constraint that shapes
everything below.

## The parallelism constraint

Almost nothing here is parallel, and the reason is structural rather than
incidental:

```
       US1  US2  US3  US5          US4        FR-012
        │    │    │    │            │            │
        └────┴────┴────┘            │            │
               │                    │            │
               ▼                    ▼            ▼
   conversation-response-           .github/     tests/test_response_
   shape/SKILL.md                   pull_        shape_invariants.py
   ── ONE file, four stories ──     request_
                                    template.md
```

Four of five stories edit the same 388-line file. `[P]` is therefore reserved for
the three tasks that genuinely touch a different path. Treating same-file prose
edits as parallel would produce conflicts an agent cannot merge, because prose has
no merge semantics.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: different file, no dependency on an incomplete task
- Paths are repository-relative from `wfctl` repo root
- Source is `wfctl/agents/`. **Never edit `.agents/`** — it is gitignored install
  output and an edit there passes the suite and ships nothing (`layer-model`)

---

## Phase 1: Setup

**Purpose**: capture the baselines the later checks compare against. Nothing is
edited in this phase.

- [x] T001 Record the pre-change baseline to the feature dir: `wc -l wfctl/agents/skills/conversation-response-shape/SKILL.md` (expect 388) and the C-6 violation list from `awk '/^```/{f=!f} f && /wfctl/' wfctl/agents/skills/conversation-response-shape/SKILL.md` (expect 4 lines across blocks at 207 and 292); verify by diffing against the counts recorded in `research.md` §4 and `plan.md` Complexity Tracking
- [x] T002 Confirm the working tree is green before any edit: `uv run pytest -q`, `uv run ruff check wfctl/ tests/`, `uv run mypy wfctl/`; verify all three exit 0 — a failure here is pre-existing and must be separated from this feature's diff
- [x] T003 Confirm the baselines from T001 are written to the feature dir and the working tree carries no uncommitted change from this feature yet (`git status --short` shows nothing under `wfctl/` or `.github/`) — merge gate

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: create the two rule slots and the test file every later phase writes
into. US1 and US5 both append to the precedence list; doing that once prevents
two stories racing on the same lines.

**⚠️ No user story work can begin until this phase is complete**

- [x] T004 Append rules 4 and 5 as headings and list entries only — no bodies yet — to the Precedence section and the section sequence of `wfctl/agents/skills/conversation-response-shape/SKILL.md`, keeping rules 1-3 at their current numbers; verify with T006
- [x] T005 Delete the sentence "Terseness is the default, not a ceiling — a reader who asks for understanding gets it in full, and compressing that deletes the answer. But the ceiling is lifted by the asking, never by the topic." from rule 3's body in `wfctl/agents/skills/conversation-response-shape/SKILL.md` (conflict 3, FR-003); verify with `grep -c "Terseness is the default" wfctl/agents/skills/conversation-response-shape/SKILL.md` returning 0
- [x] T006 Create `tests/test_response_shape_invariants.py` with C-3 (headings `## 1.`, `## 2.`, `## 3.` still carry their current titles) and C-7 (file ≤ 450 lines), each with a docstring naming the failure it catches per this repo's test conventions; verify with `uv run pytest tests/test_response_shape_invariants.py -q` passing
- [x] T007 Validate Phase 2 with `uv run pytest -q && uv run ruff check wfctl/ tests/ && uv run mypy wfctl/` — merge gate

---

## Phase 3: User Story 5 — Establish the subject (Priority: P1)

**Goal**: a reply says what it is talking about before it argues about it.

**Sequenced before US1 despite equal priority.** Rule 4 precedes rule 5 in the
file, and establishing the subject is a precondition for judging whether material
needs a decision — you cannot tell a side-note is volunteered until you know what
it is about (`research.md` §2).

**Independent Test**: read a reply cold and answer J1 and J4 of
`judgment-test.md` — can I name what this is about, and act, without asking?

**Verification**
- Automated: `uv run pytest -q`; C-3 in `tests/test_response_shape_invariants.py` confirms rules 1-3 did not move
- Manual: J1-J4 of `judgment-test.md` read cold against rule 4's body and its example
- Gate: T011

- [x] T008 [US5] Write rule 4's body in `wfctl/agents/skills/conversation-response-shape/SKILL.md`: the rule statement per FR-011, the three-row precedence table from `data-model.md` distinguishing it from rules 1 and 2, and the observable check per FR-011b; verify with T011
- [x] T009 [US5] Add a worked example to rule 4 abstracted from the #556 exchange in `design.md` — a reply that passes answer-first and plain-language and still fails — using no wfctl vocabulary per FR-006; verify with the C-6 check in T024
- [x] T010 [US5] Add one entry to the Failure modes list and one question to the Pre-send check for rule 4 in `wfctl/agents/skills/conversation-response-shape/SKILL.md`, matching the existing shape of both sections; verify by reading both lists for parallel structure
- [x] T011 [US5] Validate Phase 3: `uv run pytest -q` green, and rule 4's body answers J1-J4 of `judgment-test.md` when read cold — merge gate

---

## Phase 4: User Story 1 — The register rule (Priority: P1)

**Goal**: finished, verified work is reported as finished; nothing that needs no
decision gets a paragraph.

**Independent Test**: J3 of `judgment-test.md` on issue #88 — does the reply argue
anything #88 already settled? A yes is a failure.

**Verification**
- Automated: `uv run pytest -q`
- Manual: rule 5's body states the rule, names the "two things worth naming" heading as the tell, and draws the boundary against rule 1
- Gate: T015

- [x] T012 [US1] Write rule 5's body in `wfctl/agents/skills/conversation-response-shape/SKILL.md`: the rule statement per FR-001, the "two things worth naming" heading named as the tell, and the boundary against rule 1 per FR-002 — rule 1 governs justification of the answer, rule 5 governs volunteered side-notes on completed work; verify with T015
- [x] T013 [US1] Add a worked example to rule 5 showing volunteered justification cut to one line, abstracted out of wfctl vocabulary per FR-006; verify with the C-6 check in T024
- [x] T014 [US1] Add one entry to the Failure modes list and one question to the Pre-send check for rule 5 in `wfctl/agents/skills/conversation-response-shape/SKILL.md`; verify by reading both lists for parallel structure
- [x] T015 [US1] Validate Phase 4: `uv run pytest -q` green, and the register rule's body states the rule, the tell, and the boundary against rule 1 — merge gate

---

## Phase 5: User Story 2 — Reply shape and form selection (Priority: P2)

**Goal**: the material picks the drawing, so the table rule stops winning by
default.

**Independent Test**: J5 and J6 of `judgment-test.md` — are #88's four reachable
states drawn, and does the form match the material?

**Verification**
- Automated: C-5 in `tests/test_response_shape_invariants.py` (selection table appears exactly once under `wfctl/agents/`); `wc -l` ≤ 450 (C-7); `grep -c "getting long"` and `grep -c "does not replace the explanation"` both 0
- Manual: the selection table covers all five material shapes in `data-model.md`, and both genre openings are present
- Gate: T021

- [x] T016 [US2] Replace "Reach for it when the description is getting long because it is doing spatial or structural work." in the *Show* section of `wfctl/agents/skills/conversation-response-shape/SKILL.md` with the draw test per FR-005 — draw when the reader has to hold a set, a location, a count, or a branch to follow the sentence (conflict 1); verify with `grep -c "getting long" wfctl/agents/skills/conversation-response-shape/SKILL.md` returning 0
- [x] T017 [US2] Replace "The artifact does not replace the explanation" in the *Show* section with the caption formulation per FR-003 conflict 2 — the drawing carries the argument, the line under it is a caption; verify with `grep -c "does not replace the explanation" wfctl/agents/skills/conversation-response-shape/SKILL.md` returning 0
- [x] T018 [US2] Add the five-row form-selection table from `data-model.md` to the *Show* section per FR-005a, naming two-column as the most frequent form and *before / after* as one filling of it rather than the default; verify with T021
- [x] T019 [US2] Add the reply composition per FR-004 and FR-004a — the two genre openings, one drawing per question the reader has rather than one per reply, one caption line each — to the *Show* section; verify with T021
- [x] T020 [US2] Add the C-5 assertion to `tests/test_response_shape_invariants.py`: the form-selection table's header row appears exactly once across `wfctl/agents/**/*.md`, with a docstring naming #556's two incoming pointers as the drift this catches; verify with `uv run pytest tests/test_response_shape_invariants.py -q` passing
- [x] T021 [US2] Validate Phase 5: `uv run pytest -q` green, `wc -l` on the skill ≤ 450, and the selection table covers all five material shapes in `data-model.md` — merge gate

---

## Phase 6: User Story 3 — Examples carry no wfctl vocabulary (Priority: P3)

**Goal**: the skill reads correctly in a repo that is not wfctl. Closes #80.

**Larger than #80 describes.** `research.md` §4 found wfctl vocabulary in two
example blocks, not one. T023 is the biggest single piece of prose work in this
feature — the whole example is a wfctl scenario, not a swappable identifier, and
the rewrite must preserve the decision-trace shape `design.md` keeps it for.

**Independent Test**: the C-6 check returns empty; a reader unfamiliar with wfctl
can follow every example.

**Verification**
- Automated: C-6 in `tests/test_response_shape_invariants.py` — red with 4 hits before this phase, green after
- Manual: both rewritten examples teach the same rule they taught before, and T023 preserves its name-and-separate structure and consequence trace
- Gate: T025

- [x] T022 [US3] Rewrite the literal-output example at `wfctl/agents/skills/conversation-response-shape/SKILL.md:207` — currently `wfctl end` / `Session closed` — using a domain-agnostic command; verify with the C-6 check in T024
- [x] T023 [US3] Rewrite the *Untangling compressed explanations* worked example at `wfctl/agents/skills/conversation-response-shape/SKILL.md:292`, which is built entirely on `wfctl status`, `wfctl verify` and `implement-complete.md`, preserving its two-part name-and-separate structure and its consequence trace; verify with the C-6 check in T024
- [x] T024 [US3] Add the C-6 assertion to `tests/test_response_shape_invariants.py`: no fenced example block in the skill contains the string `wfctl`, with a docstring recording that it was red with 4 hits before this phase; verify with `uv run pytest tests/test_response_shape_invariants.py -q` passing
- [x] T025 [US3] Validate Phase 6: `awk '/^```/{f=!f} f && /wfctl/' wfctl/agents/skills/conversation-response-shape/SKILL.md` returns empty, and `uv run pytest -q` green — merge gate

---

## Phase 7: User Story 4 — The pull request template points, never restates (Priority: P3)

**Goal**: one owner for the draw test. The template states the obligation and
defers the choice of form.

**Independent Test**: the template contains no copy of the draw test or the
selection table, and names the skill.

**Verification**
- Automated: `grep -rn "The material is" .github/ wfctl/agents/` returns only the skill
- Manual: the template's diagram guidance names `conversation-response-shape` rather than restating its test
- Gate: T027

- [x] T026 [P] [US4] Replace "Two small diagrams beat one that tries to be complete. If a diagram takes longer to read than the prose it replaced, delete it." at `.github/pull_request_template.md:33-34` with a pointer to `conversation-response-shape` for when to draw and which form, per FR-007 and conflict 4; verify with T027
- [x] T027 [US4] Confirm single ownership: `grep -rn "The material is" .github/ wfctl/agents/` returns only the skill, and the template's diagram guidance names the skill rather than restating its test — merge gate

---

## Phase 8: Polish and Cross-Cutting

**Purpose**: the checks the suite cannot make, and the validation that runs after
the edit rather than gating it.

- [x] T028 Install and exercise: `wfctl install-skills` then `wfctl doctor`, then load the changed skill in a fresh session — a change under `wfctl/agents/` is not verified by the suite alone (`CLAUDE.md`); verify `doctor` reports no finding that still stands, and read the *Show* section once end to end confirming a reader can state what a reply is composed of from a single pass (SC-006)
- [x] T029 Check the line budget: `wc -l wfctl/agents/skills/conversation-response-shape/SKILL.md` ≤ 450. If over, cut *"Render the literal output, not a description of it"* per `plan.md`'s named lever and no other passage; verify with `uv run pytest tests/test_response_shape_invariants.py -q` (C-7)
- [x] T030 Score issue #88 against `judgment-test.md` in a fresh context — seven yes/no questions, any no in J1-J4 is a failure; record prose word count alongside (baseline 203) and never as the verdict per SC-012; verify by writing the scored result to `<spec root>/102-reply-over-explains/checklists/judgment-88.md`
- [x] T031 [P] Read #90, #76, #85 and #61 unscored for J5 and J6 only — they have no per-task baseline and scoring them would overstate what is known (`research.md` §1); verify by recording which form each reply chose against the material's actual shape, with no delta claimed against the 3-of-5 baseline (SC-009, which counts a different thing)
- [x] T032 Exercise the genre split FR-004 introduces: put one *question about current state* to the edited skill — every benchmark task is a change proposal, so J8 is otherwise never run — and score J8, no manufactured "what changed" (SC-010); verify by recording the reply and its J8 verdict beside T030's result
- [x] T033 Guard T005's deletion: put one prompt that explicitly asks for reasoning or a tradeoff ("explain why…", "what are the tradeoffs between X and Y") to the edited skill and confirm the full reasoning survives (SC-005). This is the only check on the one assumption the experiment never tested — `spec.md` records that no variant tested deleting the ceiling sentence against a question that genuinely asks for depth. A compressed answer here is a finding against the design, not a task failure; verify by recording the reply beside T030's result
- [x] T034 Confirm scope and the two prohibitions: `git diff --name-only origin/main...HEAD` lists exactly three paths, and neither `speckit-delivery-plan` nor `finishing-a-development-branch` is among them (#556 owns those); confirm FR-008 by checking the *Show* section gained no per-form trigger prose, and FR-012a by checking `tests/test_response_shape_invariants.py` asserts nothing about frontmatter keys or precedence-list contiguity (#60 owns those); verify with the diff and a read of both files
- [x] T036 Add rule 6 to `wfctl/agents/skills/conversation-response-shape/SKILL.md` — the answer plus at most one supporting block of **prose**, with a drawing the selection table warrants explicitly excluded from the count, and the counted lead-in named as the tell; append to the precedence list as rule 6 per `whole-reply-cap.md`; verify with T037
- [x] T037 Re-run arm B of `whole-reply-cap.md` against the reworded rule on the same report task, confirming the answer-first gain holds **and** the three-file table returns — the unreworded version lost the drawing in both runs; verify by writing the reply to `replies/B2-rules1-6-reworded-report.md` and comparing against `replies/A-rules1-5-report.md` and `replies/B-rules1-6-report.md`
- [x] T035 Validate the whole feature with `uv run pytest -q && uv run ruff check wfctl/ tests/ && uv run mypy wfctl/` and `wfctl doctor` — merge gate

---

## Dependencies

```
Phase 1  Setup ─────────────────────────► baselines recorded
   │
   ▼
Phase 2  Foundational ──────────────────► rule slots 4 and 5 exist
   │                                       test file exists (C-3, C-7)
   ├──────────────┬──────────────┬─────────────────┐
   ▼              ▼              ▼                 ▼
Phase 3 (US5)  Phase 4 (US1)  Phase 5 (US2)   Phase 7 (US4)
subject rule   register rule  draw test        PR template
                              + selection      ── independent,
                                + C-5             different file
   │              │              │                 │
   └──────────────┴──────────────┤                 │
                                 ▼                 │
                          Phase 6 (US3)            │
                          example rewrites  ◄──────┘
                          + C-6           (must follow 3-5: the new
                                           examples are subject to C-6)
                                 │
                                 ▼
                          Phase 8  Polish
```

**Story order deviates from priority once**: US5 before US1, both P1. Rule 4
precedes rule 5 in the file and is its precondition.

**Phase 6 is last among the stories** because T024's C-6 assertion must run
against every example the feature adds, including those written in Phases 3-5.

## Parallel opportunities

Three tasks, and only three:

| Task | Why it parallelizes |
| --- | --- |
| T026 [US4] | `.github/pull_request_template.md` — different file, no dependency |
| T031 | reading four issues, no file written |
| Phase 7 entire | can run against `main` alongside any other phase |

Everything else edits `wfctl/agents/skills/conversation-response-shape/SKILL.md`
or the one new test file.

## Implementation strategy

**MVP is Phase 2 + Phase 3 + Phase 4** — the two rules the issue was filed for,
with the file's structure intact and the suite green. That is a shippable
increment: it fixes the reported defect and closes nothing else.

**Phase 5** is the largest bet and the least evidenced — `spec.md` records the
form-selection claim as inferred from two cases and never run. It is separable; if
T030 shows the rules landing without it, it can be split out and evidenced first.

**Phase 6** closes #80 and is separable from everything else.

**Phase 7** closes the template contradiction and is one line.

## Verification summary

| Phase | Automated | Manual |
| --- | --- | --- |
| 1 | three-command suite | — |
| 2 | C-3, C-7 in the new test file | — |
| 3 | `pytest -q` | J1-J4 read cold |
| 4 | `pytest -q` | J3 on #88 |
| 5 | C-5, `wc -l` ≤ 450 | selection table completeness |
| 6 | C-6 (red→green) | example legibility without wfctl |
| 7 | `grep` for single ownership | template names the skill |
| 8 | full suite + `wfctl doctor` | `judgment-test.md` J1-J7 on #88, J8 on a state question, and one depth-asking prompt |

**Task count**: 37. US1 4, US2 6, US3 4, US4 2, US5 4; setup 3, foundational 4,
polish 10.

**T036/T037 were added after `/speckit.analyze`**, from an experiment run during
implementation (`whole-reply-cap.md`). Rules 1-5 each govern one piece of a
reply; nothing counted the pieces, and a reply carrying all five still buried
its answer under two bolded side-sections. Rule 6 caps the whole. T037 exists
because the first wording lost a warranted drawing in both arms — the rule must
be re-run after rewording, not assumed fixed.

**Phase 8 grew by two after `/speckit.analyze`.** T032 exercises the genre split
on a state question — every benchmark task is a change proposal, so J8 would
otherwise never run. T033 is the guard on T005: the feature deletes the sentence
that existed to prevent over-compression, and nothing else checks for
over-compression.
