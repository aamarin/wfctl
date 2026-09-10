# Tasks: promote a decision to accepted (#321)

**Input**: `plan.md`, `spec.md`, `data-model.md`, `contracts/arch-accept.md`,
`research.md`, `quickstart.md`
**Records**: `docs/architecture/a-human-accepts-a-decision.md` (level 2),
`docs/architecture/design/321-one-status-mutation.md` (level 3) — both committed.

`[P]` marks tasks that touch no file another `[P]` task in the same phase touches.

---

## Phase 1: Setup

- [x] **T001** Confirm the definition of done is green on the branch as it stands,
      before any code changes: `uv run pytest -q`, `uv run ruff check wfctl/ tests/`,
      `uv run mypy wfctl/`. A failure here belongs to something else, and finding
      that out after the change costs the bisect.

## Phase 2: Foundational — the shared mutation

**Blocks every user story.** `accept` cannot exist before the body it calls.

- [x] **T002** Extract `_set_status(record, status, date, note)` in `wfctl/_arch.py`
      from `supersede`'s body, carrying its four hazard comments verbatim: the
      `newline=""` open, the backwards scan for the last `status` key,
      the missing-final-newline fix, and `write_atomic`. Write the `Log` line as
      `f"- {date}  {status:<12}— {note}{eol}"` and name the column in a comment —
      `supersede`'s literal two spaces are that padding, unnamed.
      **Verification**: `uv run pytest -q tests/test_arch_records.py` — the existing
      supersede tests are the regression suite for this move and must pass
      unchanged, with no edit to any of them.
- [x] **T003** Reduce `supersede` to a caller of `_set_status`, keeping its
      docstring's VR-005 paragraph on the public function where a caller reads it.
      **Verification**: same suite, still unedited; plus
      `git diff --stat wfctl/_arch.py` showing the body moved rather than grown.

## Phase 3: User Story 1 — a maintainer makes a decision binding (P1)

**Goal**: one record moves `proposed → accepted` with its citation in the file.
**Independent test**: accept a record; the contract projects it and the file
differs by exactly two lines.

- [x] **T004** Add `_arch.accept(record, date, citation)` calling `_set_status`
      with `"accepted"`, guarded to refuse any current status but `proposed`.
      Raise `ValueError` carrying the current status, so the caller can render the
      three distinguishable refusals (`data-model.md`). The guard lives here and
      not in `cli` per `knowledge-placement` — it is a fact about the record.
- [x] **T005** [P] `tests/test_arch_records.py`: a `proposed` record accepted gains
      `status: accepted` and one `Log` line, and nothing else in the file differs.
      Name the test for the property, and say in the docstring that VR-005 is what
      it protects.
- [x] **T006** [P] `tests/test_arch_records.py`: a CRLF record keeps its line
      endings and differs by two lines. This is the hazard a copied mutation body
      loses first (`321-one-status-mutation` § Verification).
- [x] **T007** [P] `tests/test_arch_records.py`: a record whose frontmatter repeats
      `status:` has the **last** one changed — the one `_frontmatter` reads — so
      the log and the record cannot disagree.
- [x] **T008** [P] `tests/test_arch_records.py`: a record with no `## Log` section
      and one with no `status:` key each raise and write nothing.
- [x] **T009** Add the `accept` command to `arch_app` in `wfctl/cli.py`: optional
      `SLUG`, `--agreed` enforced after slug resolution, UTC date, the success line
      quoting the `Log` entry it wrote. Follow `contracts/arch-accept.md` for every
      string.
- [x] **T010** Command test: accepting a record exits 0, prints the quoted `Log`
      line, and `arch context` then projects the slug while its withheld count
      drops by one. Pin `NO_COLOR`.
      **Verification**: this is SC-003, end to end through the real command.

## Phase 4: User Story 2 — a second acceptance is refused (P1)

**Goal**: no record ever gains a `Log` line claiming an agreement that did not
happen.
**Independent test**: run every refusal and confirm the file is byte-identical
after each.

- [x] **T011** [P] `tests/test_arch_records.py`: accepting an already-`accepted`
      record raises and appends no second `Log` line.
- [x] **T012** [P] `tests/test_arch_records.py`: `superseded`, `rejected` and
      `retired` are each refused, parameterized, and the file is unchanged.
- [x] **T013** [P] `tests/test_arch_records.py`: a record with an unrecognised or
      absent status is refused rather than overwritten.
- [x] **T014** Command tests for the three refusal messages, asserting each is
      distinguishable — already-accepted names the date when the record carries an
      `accepted` `Log` line and omits it when it does not; ended says a decision
      binding again is a new record; unreadable says to fix the frontmatter. Pin
      `NO_COLOR`.
      **Verification**: SC-004 — assert byte-identity of the record file after each
      refusal, not just the exit code.
- [x] **T015** Command tests for the citation guards: `--agreed` absent, empty, and
      a `<placeholder>`. Each exits 1 and writes nothing.

## Phase 5: User Story 3 — the unaccepted set is nameable (P2)

**Goal**: someone acting on the backlog reaches the right slug without reading the
directory.
**Independent test**: ask to accept with no slug and get the promotable list.

- [x] **T016** Bare `wfctl arch accept` lists promotable slugs and exits 1; with no
      promotable record it says so and exits 0 (`contracts/arch-accept.md`).
- [x] **T017** An unknown slug prints near matches when there are any, and the
      promotable list when there are none.
- [x] **T018** [P] Command tests for both, with `NO_COLOR` pinned.

## Phase 6: Polish and cross-cutting

- [x] **T019** Run the full definition of done: `uv run pytest -q`,
      `uv run ruff check wfctl/ tests/`, `uv run mypy wfctl/`, `uv run wfctl doctor`.
      All four green is the bar (`AGENTS.md`).
- [x] **T020** Walk `quickstart.md` end to end against this working tree, including
      the negative case at step 6. The suite does not test what a person reads.
- [ ] **T021** *(the maintainer's — see below)* Accept `a-human-accepts-a-decision` itself, by the route this change
      built, once a human has agreed — the recursion the handoff names. Not done
      unattended: this is the one act the `auto_approve` mode is not permitted to
      perform, and the record says so in its own Consequences.
- [x] **T022** Confirm the fourteen pre-existing proposed records are untouched:
      `git diff --name-only origin/main...HEAD -- docs/architecture/` names only
      this branch's own files.

---

## Dependencies

```
T001
  └─► T002 ─► T003 ─────┐
                        ├─► T004 ─► T005..T008 [P]
                        │      └──► T009 ─► T010
                        │              └──► T011..T015
                        │              └──► T016..T018
                        └─────────────────────► T019 ─► T020 ─► T021, T022
```

Stories 2 and 3 both depend on the command from T009 and on nothing from each
other; their test tasks run in parallel once it exists.

## Parallel execution

- After T004: T005, T006, T007, T008 — four tests, one file, no shared fixture
  state. Written together, run together.
- After T009: the story-2 block (T011–T015) and the story-3 block (T016–T018) are
  independent.

## Implementation strategy

**MVP is Phase 3.** A maintainer who can accept one record with a citation has the
whole rule; every phase after it is refusals and discovery.

Phase 4 is not optional despite being after the MVP — the second-acceptance lie is
silent, and a feature that records agreements which did not happen is worse than
the gap it replaced. Phase 5 is the one that could ship separately and is included
because it answers the cost the issue names against this whole approach: fourteen
records nobody remembered.
