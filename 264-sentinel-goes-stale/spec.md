# Feature Specification: A new task reopens the `implement` step

**Feature Branch**: `264-sentinel-goes-stale`
**Created**: 2026-10-09
**Status**: Draft
**Input**: User description: "From the brainstorm output at design.md (issue #264: a story that gains new tasks reports the old verdict)"

## Clarifications

### Session 2026-10-09

- Q: When wfctl matches a task against the copy, do the `[P]` and `[USn]` tags count as part of its description? → A: No. The checkbox, the ID, and both tags are removed, and whitespace is collapsed, before descriptions are compared.
- Q: Should `wfctl step complete implement` refuse to run before the pipeline reaches `implement`? → A: Yes. It refuses, and writes nothing, while a step before `implement` is current. It runs when `implement` is current or already finished, since the implement instructions run it on every finish, including one where every box is ticked and the pipeline has already moved past `implement`.

## User Scenarios & Testing _(mandatory)_

### User Story 1 - A story that gains a task after it finished is sent back to implement (Priority: P1)

A story finishes its `implement` step, and the agent writes a completion
record. Later the scope grows, `/speckit.tasks` is re-run, and the task list
gains a new incomplete task. Today wfctl keeps reading the story as finished,
because it trusts the completion record just because the record exists.

After this change, wfctl notices the new task and reopens the `implement`
step. The next command it gives is `/speckit.implement`, whether or not the
repository configures a definition of done.

For example, the copy saved at completion holds T001 ticked. A re-run adds
T002, which is incomplete. `wfctl status` then reads:

```
implement    ▶  1/2 done  ← current
next: /speckit.implement
```

**Why this priority**: This is the bug. With no definition of done
configured, wfctl reports a story complete while its own line says `1/2
done`, so open work reads as finished. With a definition of done, the agent
is sent to verification instead of to the new task.

**Independent Test**: Build a feature whose completion record holds a copy
with T001 ticked, then add an incomplete T002 to `tasks.md`. Read `wfctl
status` and `wfctl next` once with a definition of done configured and once
without one. Both runs give `implement` as the current step and
`/speckit.implement` as the next command.

**Acceptance Scenarios**:

1. **Given** a completion record whose copy holds T001 ticked, a live
   `tasks.md` holding T001 ticked and a new incomplete T002, and no definition
   of done configured, **When** `wfctl status` runs, **Then** `implement` is
   the current step, the story is not reported complete, and the next command
   is `/speckit.implement`.
2. **Given** the same tree with a definition of done configured, **When**
   `wfctl next` runs, **Then** the next command is `/speckit.implement`, not
   `wfctl verify`.
3. **Given** a copy holding T001 ticked and T002 incomplete, because T002 was
   done outside the implement skill, **When** a new incomplete T003 is added,
   **Then** the `implement` step reopens because of T003 alone. T002 was
   already incomplete in the copy, so it is not new work.
4. **Given** a re-run of `/speckit.tasks` inserts a new task in the middle of
   the list, so it takes the ID an old task had, **When** wfctl compares the
   task list against the copy, **Then** the new task is read as new work,
   because tasks are matched by their description and not by their ID.

---

### User Story 2 - The implement step writes its completion record through wfctl (Priority: P1)

The comparison in Story 1 needs a copy of the task list as it was when the
`implement` step finished. That moment is the only point when the copy can be
taken, since previous versions of `tasks.md` are not preserved once it
changes.

The agent records completion by running `wfctl step complete implement`. The
command writes the completion record with a copy of `tasks.md` inside it. The
implement command file tells the agent to run it in place of writing the file
by hand.

**Why this priority**: Story 1 has nothing to compare against without it. It
is P1 for that reason, and it is a separate story because it can be shown
working on its own: run the command, then read the record it wrote.

**Independent Test**: In a feature with a `tasks.md`, run `wfctl step complete
implement`, then read `checklists/implement-complete.md`. It holds the
completion line and an exact copy of `tasks.md`, and reading it back yields
the text wfctl read from `tasks.md`, including a `tasks.md` that holds code
fences of its own. Line endings are read as newlines on both sides, so a CRLF
file is recorded with LF endings, which changes no task.

**Acceptance Scenarios**:

1. **Given** a feature with a `tasks.md`, **When** the agent runs `wfctl step
   complete implement`, **Then** `checklists/implement-complete.md` holds an
   "Implementation complete: <date>" line followed by a copy of `tasks.md`.
2. **Given** a `tasks.md` that contains a fenced code block, **When** the copy
   is written and read back, **Then** the text read back is identical to the
   original.
3. **Given** any step name other than `implement`, **When** the agent runs
   `wfctl step complete <step>`, **Then** the command refuses, names
   `implement` as the one step it supports, and writes nothing.
4. **Given** a pipeline whose current step comes before `implement`, such as
   `analyze`, **When** the agent runs `wfctl step complete implement`,
   **Then** the command refuses, names the current step, and writes nothing.
5. **Given** every box in `tasks.md` is ticked and no definition of done is
   configured, so the pipeline has already moved past `implement`, **When**
   the agent runs `wfctl step complete implement`, **Then** the command
   writes the completion record as usual.
6. **Given** the implement command file as installed, **When** the agent
   reaches the point where the `implement` step finishes, **Then** it is told
   to run `wfctl step complete implement`, and the command is in that file's
   allowed tools.

---

### User Story 3 - Ordinary edits leave a finished story finished (Priority: P2)

Most edits to a finished task list are not new work: ticking a box, adding a
note under a task, or fixing the wording of a task that's already done. None
of these reopen the `implement` step, since none of them adds a new
incomplete task.

**Why this priority**: Without it, Story 1 would send the agent back to
finished work after every edit. That costs time rather than hiding open work,
so it ranks below Story 1.

**Independent Test**: Start from a finished story whose copy matches
`tasks.md`. Apply each edit below in turn and confirm `implement` still reads
finished after each one.

**Acceptance Scenarios**:

1. **Given** a finished story, **When** an incomplete task that was already
   incomplete in the copy is ticked, **Then** the step stays finished.
2. **Given** a finished story, **When** a note is added under a task, **Then**
   the step stays finished.
3. **Given** a finished story, **When** the wording of a ticked task changes,
   **Then** the step stays finished.
4. **Given** a finished story, **When** the wording of an incomplete task
   changes, **Then** the step reopens. wfctl can't tell a reworded task from a
   new one, so the agent is sent back to look at it again, which is the safe
   direction.

---

### User Story 4 - Completion records written before this change still read safely (Priority: P2)

Every completion record written before this change has no copy inside it, so
it can't show which tasks are new. wfctl treats any incomplete task in that
story as open work. A story whose task list holds no tasks at all stays
finished, and the `tasks` step still reads `skipped`.

**Why this priority**: Existing features carry records with no copy. They have
to read in a defined, safe way, and the `tasks` and `implement` readers have
to agree on them. Two readers disagreeing about the same record is the
problem an earlier change already fixed.

**Independent Test**: Build a feature with a completion record that holds only
the completion line. Read `wfctl status` once with an incomplete task in
`tasks.md`, once with every task ticked, and once with a `tasks.md` that holds
no tasks.

**Acceptance Scenarios**:

1. **Given** a completion record with no copy and one incomplete task in
   `tasks.md`, **When** `wfctl status` runs, **Then** `implement` is the
   current step and the next command is `/speckit.implement`.
2. **Given** a completion record with no copy and every task ticked, **When**
   `wfctl status` runs, **Then** `implement` reads finished.
3. **Given** a completion record, with or without a copy, and a `tasks.md`
   holding no tasks, **When** `wfctl status` runs, **Then** `implement` reads
   finished and `tasks` reads `skipped`.

---

### Edge Cases

- A task shown inside a code example in `tasks.md` is not a task. It is never
  counted as new work, the same way the task tally already ignores it.
- A task that was ticked in the copy and is incomplete now counts as new work,
  since it was not incomplete in the copy. Someone unticked it, so the agent
  is sent back to it.
- Two tasks with the same description are matched by count. If the copy held
  one incomplete task with a given description and `tasks.md` now holds two,
  one of them is new work.
- Running `wfctl step complete implement` a second time replaces the record,
  and its copy, with the task list as it is at that moment.
- Running `wfctl step complete implement` in a feature with no `tasks.md`
  refuses and writes nothing, since there is no task list to copy.
- An agent that follows the old instruction and writes the completion record
  by hand produces a record with no copy. That record reads as in Story 4,
  which errs on the safe side.
- Stories 1 and 4 assume the feature has a delivery plan whose rows are all
  keyed, or a delivery plan in a repository that declares no tracker. Without
  `delivery.md`, the `decompose` step is skipped only while the tasks read
  closed, so a story that reopens is sent to `/speckit.decompose` first. A
  delivery plan with an unkeyed row under a configured tracker does the same.
  `implement` becomes current once a delivery plan exists and either every row
  in it is keyed or the repository declares no tracker. This change leaves
  that routing as it is.
- A copy that someone edited by hand is read as written. This feature keeps
  the completion record in step with the task list, and it does not protect
  the record from tampering. Where a definition of done is configured,
  verification still makes the final call.

## Requirements _(mandatory)_

### Functional Requirements

- **FR-001**: wfctl MUST provide `wfctl step complete implement`, which writes
  `checklists/implement-complete.md` with an "Implementation complete: <date>"
  line followed by a copy of `tasks.md` as it is when the command runs.
- **FR-002**: `wfctl step complete` MUST refuse any step other than
  `implement`, name `implement` in its message, exit non-zero, and write
  nothing.
- **FR-003**: `wfctl step complete implement` MUST refuse, exit non-zero, and
  write nothing when the feature has no `tasks.md`.
- **FR-003a**: `wfctl step complete implement` MUST refuse, exit non-zero,
  and write nothing while a step before `implement` is the current step. Its
  message names the current step. It MUST run when `implement` is current or
  the pipeline has already moved past it. A record written early would save
  every task as incomplete, so no task would ever count as new work, and with
  no definition of done the story would read complete with nothing built.
- **FR-004**: The copy MUST read back identical to the `tasks.md` it was taken
  from, including a `tasks.md` that holds fenced blocks of its own. A
  `tasks.md` that does not end in a newline reads back with one added, which
  changes no task. The fence
  around the copy is one character longer than the longest fence inside it.
- **FR-005**: When the completion record holds a copy, wfctl MUST read the
  `implement` step as open if `tasks.md` holds an incomplete task that was not
  incomplete in the copy, and as finished otherwise.
- **FR-006**: wfctl MUST match a task in `tasks.md` to the copy by its
  description, word for word, and never by its spec-kit ID such as T003. A
  task's description is its line with the checkbox, the ID, and spec-kit's
  `[P]` and `[USn]` tags removed, and runs of whitespace collapsed to one
  space. Tasks sharing a description are matched by count. For example,
  `- [ ] T004 [P] [US2] Add the reader` and `- [ ] T007 [US3] Add the reader`
  are the same task. A task ticked since the copy was taken uses up one
  incomplete task with its description in the copy. For example, when the
  copy holds `- [ ] T002 Update docs` and one edit ticks T002 and adds
  `- [ ] T003 Update docs`, T003 is new work.
- **FR-007**: When the completion record holds no copy, wfctl MUST read the
  `implement` step as open if `tasks.md` holds any incomplete task. The step
  MUST carry a reason that says the record holds no copy and names
  `wfctl step complete implement`, so `wfctl next` does not route to
  `/speckit.implement` automatically.
- **FR-008**: When `tasks.md` holds no tasks, any completion record MUST close
  the `implement` step, with or without a copy, and the `tasks` step MUST
  still read `skipped`.
- **FR-009**: A task that appears only inside a code example in `tasks.md` or
  in the copy MUST NOT be counted, matching how the task tally reads the
  file.
- **FR-010**: When the `implement` step reads open under FR-005 or FR-007,
  for a feature whose `decompose` step reads done or skipped, the next command
  MUST be `/speckit.implement`, whether or not a definition of done is
  configured.
- **FR-011**: The implement command file that wfctl ships MUST tell the agent
  to run `wfctl step complete implement` where the `implement` step finishes,
  and MUST list the command in its allowed tools. The derived
  `speckit-implement` skill MUST NOT be edited, since changes are layered over
  a derived skill rather than made inside it.
- **FR-012**: The `implement` step's reading MUST NOT depend on any file's
  modification time.
- **FR-013**: The test suite MUST cover a repository with no definition of
  done, a completion record present, and a task added after it. The test
  fails if wfctl goes back to trusting the record just because it exists.

### Key Entities

- **Completion record**: The file `checklists/implement-complete.md` in the
  feature directory. It says the `implement` step is finished, even when some
  boxes in `tasks.md` are still unticked, because work done outside the
  implement skill leaves its boxes unticked. After this change it also
  carries a copy of the task list.
- **Copy of the task list**: The text of `tasks.md` as it was when the
  `implement` step finished, held inside the completion record below the
  completion line. A record written before this change has none.
- **Task**: One checkbox line in `tasks.md`. It has a state (ticked or
  incomplete), a spec-kit ID such as T003, optional `[P]` and `[USn]` tags,
  and a description. Only the description and the state take part in the
  comparison.
- **New work**: An incomplete task in `tasks.md` that was not incomplete in
  the copy.

## Success Criteria _(mandatory)_

### Measurable Outcomes

- **SC-001**: In the reproduction from the issue (copy with T001 ticked, live
  list adding an incomplete T002), `wfctl status` and `wfctl next` give
  `/speckit.implement` as the next command in 2 of 2 configurations: with a
  definition of done and without one.
- **SC-002**: With no definition of done configured, a story that has an
  incomplete task added after completion is reported complete 0 times.
- **SC-003**: Each of the 3 ordinary edits in Story 3 (ticking a box, adding a
  note, and rewording a ticked task) leaves the `implement` step finished.
- **SC-004**: The `tasks` and `implement` readers agree on every one of the 3
  record shapes: a record with a copy, a record without one, and a task list
  with no tasks.
- **SC-005**: A `tasks.md` holding fenced blocks round-trips through the
  completion record with 0 differences.

## Validation Strategy _(mandatory)_

All three checks are green, run through `uv run` so the pinned dev
dependencies apply:

```bash
uv run pytest -q
uv run ruff check wfctl/ tests/
uv run mypy wfctl/
```

Then run `uv run wfctl doctor`, and `uv run wfctl install-skills` followed by
a read of the installed implement command file, since a change under
`wfctl/agents/` is not verified by the suite alone.

New tests cover:

1. The round trip of a copy, including a `tasks.md` holding its own fences.
2. Both readers on all three record shapes (SC-004).
3. The repository with no definition of done, a completion record present,
   and a task added after it (FR-013).
4. Matching by description when a re-run gives a new task an old task's ID.
5. The three ordinary edits in Story 3, and the reworded incomplete task.
6. `wfctl step complete` refusing a step other than `implement`, refusing a
   feature with no `tasks.md`, and refusing while a step before `implement`
   is current. A finish with every box ticked and no definition of done still
   writes the record.

Tests asserting on console output pin `NO_COLOR`.

Both arms are also reproduced by hand. Build a feature whose `tasks.md` holds
one ticked task and one incomplete task added after a completion record was
written, then read `wfctl status` and `wfctl next` with a definition of done
configured and again with none. A run that saw only the configured arm has
tested the safe half.

## Assumptions

- Pre-specify design context loaded from
  `/Users/andremarin/Development/wfctl-specs/264-sentinel-goes-stale/design.md`.
  Its level-2 record, `docs/architecture/new-task-reopens-implement.md`, and
  its two level-3 records govern where this spec is silent.
- No task list holds a fence the writer can't wrap.
- A re-run of `/speckit.tasks` that rewords every task is rare enough that
  reopening the step is an acceptable cost.
- Completion records written before this change are not migrated. A story
  finished with incomplete tasks reopens once. That cost is accepted while
  Andre is wfctl's only user.
- A plan edited without re-running `/speckit.tasks` is out of scope. That's
  the link above this one, and #502 handles it.
