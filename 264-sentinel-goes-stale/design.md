# A new task reopens the `implement` step

Design for #264. Levels 1, 2, and 3 were approved by Andre on 2026-10-09.

## Problem Statement

How might wfctl notice that a finished story has gained new work, without
trusting file timestamps or asking the agent to judge its own edits?

Today the completion record, `checklists/implement-complete.md`, is written
once and never invalidated. A story that finishes and later gains a task still
reads as finished, and with no definition of done configured, wfctl reports
the story complete beside `1/2 done`.

## Behavior

A story finished with T001 ticked. Later, `/speckit.tasks` is re-run and adds
T002, which is incomplete.

Before, with a definition of done configured, the agent is sent to
verification instead of to T002. This is safe, but it's the wrong next step:

```
implement          in_progress   "1/2 done  unverified — run `wfctl verify`"
next               wfctl verify
```

Before, with no definition of done, the story reads as complete while its own
line says a task is open. This is the case that lies:

```
implement          done          "1/2 done"
current step       complete
next               story complete
```

After, both cases read the same way, and the agent is sent to the new task:

```
implement    ▶  1/2 done  ← current
next: /speckit.implement
```

These edits do not reopen the step, since none of them adds a new incomplete
task:

1. Ticking a box.
2. Adding a note to a task.
3. Editing the wording of a task that is already ticked.

Rewording an incomplete task does reopen it, because wfctl can't tell a
reworded task from a new one. The agent is sent back to look at that task
again, which is the safe direction.

A completion record written before this change has no copy, so it can't show
which tasks are new. Any incomplete task in that story reopens the step. A
story whose task list holds no tasks at all stays finished, and the `tasks`
step still reads `skipped`.

## Recommended Direction

When the `implement` step finishes, the agent runs `wfctl step complete
implement`. The command writes the completion record with a copy of
`tasks.md` as it was at that moment. Each time wfctl reports status, it
compares the live `tasks.md` against that copy. An incomplete task that was
not incomplete in the copy is new work, and it reopens the step.

Tasks are matched by their description, word for word, and not by their
spec-kit ID. Spec-kit numbers tasks in execution order, and a re-run of
`/speckit.tasks` writes the file again from the top, so a new task can take
an old task's ID. Matching by ID would then hide new work, while matching by
description can only reopen the step when it didn't need to.

wfctl owns this answer because the agent shouldn't grade its own work, and
timestamps can't answer it, since restoring a feature folder from
`specs-trunk` gives every file the same timestamp. The full argument is in the
level-2 record, `docs/architecture/new-task-reopens-implement.md`.

## Structure

The completion record becomes one file with two parts:

````
Implementation complete: 2026-10-09

## Tasks at completion

~~~~markdown
- [x] T001 Create project structure
- [ ] T002 Migrate old records
~~~~
````

The fence around the copy is one character longer than the longest fence in
`tasks.md`, so the copy can hold code blocks of its own. The writer and the
reader live in one module, so the format has one owner.

The changes, by place:

1. `wfctl/cli.py` gains `step complete`, beside `step none` and `step
   sign-off`. It accepts only `implement` and refuses any other step with a
   message naming the one it supports.
2. `wfctl/_evidence.py`, `_tasks_open`, stops trusting the record by
   existence. With a copy, it looks for incomplete tasks that weren't
   incomplete in the copy. Without one, any incomplete task is open work. With
   no tasks at all, any completion record closes the step, which keeps it in
   agreement with the `tasks` reader.
3. The `tasks` reader's `skipped` arm in `wfctl/_evidence.py` is unchanged. It
   still reads the record by existence, because a task list with no tasks has
   nothing new to find.
4. `wfctl/agents/commands/speckit.implement.md` tells the agent to run `wfctl
   step complete implement` in place of step 9b, and adds the command to its
   `allowed-tools` line. `speckit-implement/SKILL.md` is not edited, since
   `vendor-upstream-skills` says to layer changes over a derived skill rather
   than edit it. An agent that follows the old step 9b writes a record with no
   copy, which is safe.
5. Task text is compared after `quoted_out`, the same way `_task_tally` reads
   it, so a task shown inside a code example is never counted.

| Checked in the code | Still assumed |
|---|---|
| `_evidence.py:590` returns "not open" when the record exists, before counting any box | No task list holds a fence the writer can't wrap |
| `_evidence.py:1460` reads the record by existence for a task list with no tasks | No other step will need a completion command soon |
| `_md.py`, `closes_fence`, closes a fence only on the same character and at least the same length | A re-run of `/speckit.tasks` that rewords every task is rare enough that reopening is an acceptable cost |
| `_archive.py:70` already carries `checklists/implement-complete.md` | |
| `test_tasks_hold_a_task.py:118` expects a task-free story with a record to read complete, and the adjusted rule keeps it passing | |
| Plan review keeps its plan copy in a separate file, made with `cp` (`plan-review.md:168`) | |

## Key Assumptions to Validate

- [ ] A copy written and read back is identical to the original, including a
  `tasks.md` that holds its own fences. A round-trip test proves it.
- [ ] Both readers agree on every state. A test covers a record with a copy,
  a record without one, and a task list with no tasks.
- [ ] The repository with no definition of done reopens the step. This is the
  arm the issue says no test covers, and it gets one.
- [ ] Both arms behave as described when reproduced by hand, with and without
  a definition of done, as the handoff requires.

## MVP Scope

The command, the copy inside the record, the comparison in `_tasks_open`, the
instruction change in the implement command file, and the tests above.

## Not Doing (and Why)

- A plan edited without re-running `/speckit.tasks`. That's the link above
  this one, and #502 handles it. Each step watches only the step above it.
- Protecting the copy from tampering. The copy lives in the spec folder and
  anyone can edit it. Where a definition of done is configured, verification
  still makes the final call.
- Migrating old completion records. They have no copy, so a story finished
  with incomplete tasks reopens once. That cost is accepted while Andre is
  wfctl's only user.
- Editing `speckit-implement/SKILL.md`. Changes are layered on through the
  command file instead.

## Open Questions

None. Every level-3 question was answered on 2026-10-09.

## Software design decisions

- docs/architecture/design/264-the-task-copy-lives-in-the-completion-record.md — the copy of `tasks.md` lives inside the completion record, not in a second file
- docs/architecture/design/264-the-completion-command-is-a-step-verb.md — the completion record is written by `wfctl step complete implement`, beside `step sign-off`
