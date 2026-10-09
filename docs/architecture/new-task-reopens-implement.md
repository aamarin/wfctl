---
status: proposed
diagram: data-flow
---

# A new task reopens the `implement` step

**What does this record decide?**
When implementation finishes, wfctl saves a copy of the task list. If a new
unticked task shows up later, wfctl reopens implementation. wfctl finds it by
comparing the task list against the copy, and never asks the agent.

## Context

Implementation is finished in one of two ways. Either every box in `tasks.md`
is ticked, or the agent writes a finish file, `checklists/implement-complete.md`,
that says the work is done over boxes nobody ticked. The finish file exists
because checkboxes are unreliable; work done outside the implement skill
leaves them empty even when the work is real.

wfctl only checks that the finish file exists, and nothing ever removes it. So
a story that finishes and later gains a task still reads finished:

```
round 1   tasks.md: - [x] T001            implement finishes, writes the finish file
round 2   tasks.md: - [x] T001            scope grows, /speckit.tasks re-run
                    - [ ] T002 new work   the finish file is not touched
```

With a definition of done configured, wfctl sends the agent to run
verification instead of to T002. That is safe, but it is the wrong next step.
With none configured, wfctl reports the story complete while showing `1/2 done`
beside it.

wfctl cannot tell an unticked box that was finished outside the skill from an
unticked box that was added later. Both look the same in `tasks.md`. To tell
them apart, wfctl needs to know which tasks existed when implementation
finished, and nothing records that today.

## Direct baseline

wfctl compares file timestamps. The finish file counts only while it is newer
than `tasks.md`; once `tasks.md` is newer, implementation reads open and the
boxes decide. There is no new file, no new format, and no new command.

In the code, `_tasks_open` would compare two `stat().st_mtime` values before
trusting the finish file.

## Decision

When the `implement` step finishes, it runs a wfctl command that writes the
finish file. The file holds a copy of `tasks.md` as it was at that moment.

Each time wfctl reports, it compares the current `tasks.md` against that copy.
An unticked task that was not unticked in the copy is new work, so
implementation reopens with `/speckit.implement` as the next step. This holds
whether or not a definition of done is configured. For example, the copy holds
T001 ticked and T002 unticked, because T002 was done outside the implement
skill. Later, T003 is added unticked. T002 was already unticked in the copy, so
it stays covered. T003 was not in the copy, so implementation reopens.

Ticking a box, fixing a typo, or adding a note does not reopen it, since none
of these adds a new unticked task. A finish file with no copy in it, such as
every one written before this change, is ignored, and wfctl counts the boxes
instead.

## Owns truth

wfctl owns "is there an unticked task the finish did not cover?".

The agent cannot answer that. The question comes up whenever `tasks.md` grows,
by a re-run of `/speckit.tasks` or by hand, and the agent that finished is not
running then. An answer it gave later would be the agent grading its own edit.
The agent is wfctl's main user, so a judgment left to it is a judgment taken
unattended, and `wfctl-runs-the-verification` refuses a self-report for the
same reason.

A timestamp cannot answer it either. Restoring a feature folder from
`specs-trunk` stamps every file with the same moment, which is the reason
`plan-edit-requires-new-review` already rejected timestamps.

The finish command owns "what did `tasks.md` say when implementation
finished?". It runs at the only moment that question can be answered. Once
`tasks.md` has changed, nothing on disk says what it held before.

## Boundary

```mermaid
flowchart TD
  subgraph agent["implement step (agent), once"]
    work["does the work, ticks some boxes"]
    finish["runs the finish command"]
  end
  subgraph cmd["finish command (wfctl), once"]
    save["writes the finish file<br/>with a copy of tasks.md"]
  end
  subgraph wfctl["wfctl, every time it reports"]
    exists{"finish file<br/>with a copy?"}
    boxes{"any unticked task<br/>in tasks.md now?"}
    cmp{"an unticked task in tasks.md now<br/>that was not unticked in the copy?"}
    open["implement ▶<br/>next: /speckit.implement"]
    closed["tasks read finished<br/>definition of done, if configured, decides"]
  end
  work --> finish
  finish --> save
  save -. "implement-complete.md" .-> exists
  exists -- "with a copy" --> cmp
  exists -- "no copy inside" --> boxes
  cmp -- "open work" --> open
  cmp -- "nothing new" --> closed
  boxes -- "open work" --> open
  boxes -- "every box ticked" --> closed
```

A dotted edge is a file read later. The left side runs once, when
implementation finishes. The right side runs on every `wfctl status` and
`wfctl next`, whether or not anyone has edited `tasks.md` since, and an
unedited file simply finds nothing new. No box in the drawing asks anyone
whether an edit mattered; wfctl asks only which unticked tasks exist.

## Considered

- **Compare file timestamps,** the direct baseline. It needs no format and no
  command. It loses because a checkout, a copy, or a restore from `specs-trunk`
  rewrites timestamps, so a stale finish can read as fresh and a fresh one as
  stale.
- **Fingerprint `tasks.md` and offer a sign-off,** the shape plan review uses.
  The finish file records a hash of `tasks.md`, any change makes it stale, and a
  command with a reason re-confirms a harmless edit. It is sound, and it is the
  usual answer in build tools. It loses on fit: every ticked box or fixed typo
  reopens implementation, and the sign-off asks the agent to judge whether its
  own edit mattered, which is the judgment this record takes away from it. For
  a story whose boxes were never ticked, a false reopen sends the agent to
  redo finished work.

## Consequences

A repository with no definition of done gets a test, since that is where a
story was reported complete over open work and no test covered it. The test
holds a finish file, one unticked task added after it, and no definition of
done configured. It fails if a later change trusts the finish file by
existence again.

The implement instructions change. Step 9b runs the finish command instead of
writing the file itself. An agent that writes the file itself anyway, with no
copy inside, gets a finish that covers nothing, so its unticked boxes read as
open, which is the safe direction.

A finish file written before this change covers no task. A story finished over
unticked boxes before this change reopens the next time wfctl reads it. That
cost is accepted while Andre is wfctl's only user; a second user reopens it.

The copy lives in the spec folder and can be edited by hand. This record makes
the finish file current, not unforgeable. Where a definition of done is
configured, it still has the last word.

This covers one link of the chain, from the task list to implementation. A
plan edited without re-running `/speckit.tasks` is the link above it, and
#502 owns that. This is the fourth place wfctl compares something it recorded
against something live, after the install manifest, `wfctl verify`, and plan
review. It reuses the saved-copy shape plan review already keeps, so #502's
general answer should be able to absorb it.

## Log

- 2026-10-09  proposed    — #264. A story that gained a task after
  implementation finished reported the old verdict, and with no definition of
  done configured it reported the story complete.
