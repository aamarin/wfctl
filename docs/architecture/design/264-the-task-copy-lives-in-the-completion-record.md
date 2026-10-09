---
status: proposed
---

# The copy of `tasks.md` lives inside the completion record

## Context

`new-task-reopens-implement` (proposed, level 2) decides that the completion
record holds a copy of `tasks.md` as it was when the `implement` step
finished. wfctl compares the live task list against that copy to find new
incomplete tasks. This record decides where the copy is stored on disk.

Two places work. The copy can sit inside `checklists/implement-complete.md`,
below the line that says when implementation finished, or in a second file
beside it. Plan review already keeps its copy of the plan in a second file,
so that is the shape this repository has used before.

## Verified

- `wfctl/agents/commands/plan-review.md:168` makes the plan copy with
  `cp "FEATURE_DIR/plan.md" "FEATURE_DIR/plan-review.plan.md"`, a separate file.
- `wfctl/_archive.py:70` copies `checklists/implement-complete.md` when a
  feature folder is archived, and names no other file under `checklists/`.
- `wfctl/specify/templates/tasks-template.md` holds a fenced code block, so a
  copy of a real `tasks.md` can hold fences of its own.
- `wfctl/_md.py:47-60`, `closes_fence`, closes a fence only on a line using the
  same character, at least as long as the opener, and with no info string. A
  `~~~~` fence is therefore not closed by a ```` ``` ```` line inside it.

## Assumed

- That no task list holds a fence longer than any the writer can pick. The
  writer picks a fence one character longer than the longest run in the copy,
  so this fails only if the copy itself cannot be read, which is a broken file
  rather than a large one.

## Direct baseline

Keep the copy in a second file, `checklists/implement-complete.tasks.md`,
written with a byte-for-byte copy the way plan review writes
`plan-review.plan.md`. The completion record keeps its one line. wfctl reads
the second file when it exists, and treats a record without one as a record
with no copy. `_archive.py` gains one row so an archived feature keeps both.

## Decision

The copy goes inside the completion record. The command writes one file: the
existing "Implementation complete: <date>" line, a `## Tasks at completion`
heading, and the full text of `tasks.md` inside a fence longer than any fence
in that text.

````
Implementation complete: 2026-10-09

## Tasks at completion

~~~~markdown
- [x] T001 Create project structure
- [ ] T002 Migrate old records
~~~~
````

The writer and the reader live in one module, so the format has one owner.

## Diagram

```
          baseline                          decision

          ┌───────────────┐                 ┌───────────────┐
          │ wfctl status  │                 │ wfctl status  │
          └───────────────┘                 └───────────────┘
            │ reads   │ reads                       │ reads
            ▼         ▼                             ▼
  ┌──────────────┐ ┌──────────────┐        ┌──────────────────┐
  │ completion   │ │ tasks copy   │        │ completion record│
  │ record       │ │ (new file)   │        │ with tasks copy  │
  └──────────────┘ └──────────────┘        └──────────────────┘
            ▲ writes  ▲ writes                      ▲ writes
          ┌─┴─────────┴───┐                 ┌───────┴───────┐
          │ step complete │                 │ step complete │
          └───────────────┘                 └───────────────┘
            ▲ copies  ▲ copies                      ▲ copies
          ┌─┴─────────┴───┐                 ┌───────┴───────┐
          │ archive       │                 │ archive       │
          └───────────────┘                 └───────────────┘
```

The baseline has two files where the decision has one, so it has two more
arrows: a second read, a second write, and a second archive copy. Each extra
arrow is a place where the record and its copy can fall out of step, for
example a record written while the copy failed, or an archive made before the
new row existed. No boundary moves in either graph.

## Considered

- A second file beside the record, the direct baseline. It needs no fence
  handling and follows plan review's shape. It lost because the record and the
  copy can then exist separately, and because the archive needs a new row to
  keep them together. A record whose copy went missing is still safe, since it
  reads as a record with no copy, but it reopens the step for no reason.
- A hash of `tasks.md` instead of a copy. Rejected at level 2: a hash cannot
  say which tasks are new, only that something changed.

## Consequences

One file is written in one step, so a record can never lose its copy, and the
archive carries both with no change. The cost is the fence: the writer has to
pick a fence that the copy cannot close, and the reader has to use the shared
walker in `_md.py` rather than a regex of its own.

## Verification

- A round-trip test: write a record from a `tasks.md` that holds its own
  fences, read the copy back, and compare it byte for byte with the original.
- A test that a record with the old one-line format reads as having no copy.

## Log

- 2026-10-09  proposed  — #264 level 3. Andre chose the copy inside the
  record over a second file.
