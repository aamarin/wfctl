# Data Model: A new task reopens the `implement` step

## Completion record

The file `checklists/implement-complete.md` in the feature directory. It says
the `implement` step is finished, even when some boxes are still unticked.

Written by `wfctl step complete implement` in this shape:

````
Implementation complete: 2026-10-09

## Tasks at completion

~~~~markdown
- [x] T001 Create project structure
- [ ] T002 Migrate old records
~~~~
````

1. The first line is unchanged from the record written by hand, with the
   local date in ISO form.
2. The `## Tasks at completion` heading marks where the copy starts. The
   reader looks for it outside any fence.
3. The copy sits inside a tilde fence one longer than the longest fence
   marker of either character in the copy, and at least four long
   (research R4).

A record has one of two shapes when read:

| Shape | How it reads |
| --- | --- |
| With a copy | The heading is present and a fenced block follows it |
| Without a copy | Anything else: a one-line record from before this change, a hand-written one, or one whose block is missing |

A record that can't be read is treated as a record without a copy.

## Copy of the task list

The text of `tasks.md` when the record was written. A copy read back equals
the original, with one final newline (research R5).

## Task

One line in a task list whose quoted-out form holds a checkbox.

| Field | Source |
| --- | --- |
| state | Incomplete if the quoted-out line holds `[ ]`, ticked if it holds `[x]` or `[X]` |
| description | The raw line with the first checkbox, the ID right after it, and the `[P]` and `[USn]` tags right after the ID removed, whitespace collapsed, ends stripped (research R2, R3) |

For example, `- [ ] T004 [P] [US2] Add the reader` has the description
`- Add the reader`, the same as `- [ ] T007 [US3] Add the reader`.

## New work

The incomplete tasks in the live list that the copy does not account for,
counted by description. Written as multisets:

```
new = Counter(incomplete descriptions in tasks.md)
    - Counter(incomplete descriptions in the copy)
```

The step is open when `new` holds anything.

## How the `implement` step reads, by record shape

| Task list | No record | Record without a copy | Record with a copy |
| --- | --- | --- | --- |
| No task at all | open (#308) | closed | closed |
| Every task ticked | closed | closed | closed |
| Some task incomplete | open | open | open only if `new` holds anything |

"Closed" here is the tasks reading closed. Where a definition of done is
configured, it still decides whether `implement` is done.

The `tasks` step reads `skipped` for a task list with no task and a record of
either shape, unchanged.
