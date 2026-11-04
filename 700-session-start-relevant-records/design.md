# Session start loads the records for the branch's contexts

Contexts: architecture-records, evidence-and-derivation, session-continuity

## Problem Statement

Every session starts with `wfctl arch context`, which prints every accepted
architecture record. In the #432 worktree it printed about 3,700 tokens, the
largest single piece of the session start, and it grows with every record
accepted. Most of those records concern parts of wfctl the branch never changes.

The goal is for `/start-session` to print only the records that apply to what
the branch changes, say how many it left out and which command prints them, and
never leave out a record that binds the branch.

## Recommended Direction

The design checks already link records to contexts. A branch lists its contexts
in the `Contexts` line of `design.md`, and a record lists its contexts in its
`governs` field. `arch context` uses that link:

1. When the branch lists its contexts, it prints the accepted records whose
   `governs` field names one of them, plus every record with no `governs` field.
2. When it can't tell which records apply, it prints every one.
3. `--all` prints every accepted record, whatever the branch lists.

The session report's `Records` line gives the same count, from the same
function.

### How each open question in the handoff was answered

1. Which records apply. We took the handoff's recommendation: the `Contexts`
   line against each record's `governs` field, and a record with no `governs`
   field always prints.
2. What the first session loads. The handoff recommended printing every record
   until the branch has commits. We key on the `Contexts` line instead, since
   commits don't say which contexts a branch changes. A branch with no commits
   has no `design.md`, so it still prints every record, and a branch with
   commits but no `Contexts` line has nothing to narrow by. The two rules give
   the same result in every case the handoff named.
3. Records that bind every change. They always print, and a record says so by
   leaving the `governs` field out. The level-2 record settles this and says
   why a reserved name such as `repository` lost.

## Behavior (level 1)

Each state below is the literal output, judged true or false in that state.

### `arch context`, branch lists contexts, some records left out

```
# Architectural contract — 6 of 28 accepted decisions apply to this branch
Contexts: install-and-drift

a-rule-is-expressed-as-a-check
  …
(6 records)

22 accepted records govern only other contexts — `wfctl arch context --all` prints them
51 records not shown (45 proposed, 3 rejected, 3 superseded) — docs/architecture/
```

True. The header says the set is narrowed and by what. The count and the
command are on the line the agent reads after the records. The second footer
line is unchanged and still counts records by status.

### `arch context`, branch lists contexts, nothing left out

```
# Architectural contract — 28 accepted decisions
…
51 records not shown (45 proposed, 3 rejected, 3 superseded) — docs/architecture/
```

True. Printed exactly as today. Saying "28 of 28 apply" would add a line that
tells the agent nothing.

### `arch context`, no `design.md` or no `Contexts` line

```
# Architectural contract — 28 accepted decisions
…
Every accepted record is printed, since design.md lists no contexts for this branch yet.
51 records not shown (45 proposed, 3 rejected, 3 superseded) — docs/architecture/
```

True. This is the first session on a new branch and every branch that skips the
spec pipeline. The line says why nothing was left out, so the agent doesn't
assume the set was narrowed.

### `arch context`, `Contexts` line names something not on the domain page

```
# Architectural contract — 28 accepted decisions
…
⚠ Every accepted record is printed, since design.md lists sesion-continuity, which isn't on the domain page.
51 records not shown (45 proposed, 3 rejected, 3 superseded) — docs/architecture/
```

True. A misspelled name would leave out the records for the context it meant,
so wfctl prints them all and says why. The brainstorm gate already pauses on the
same misspelling, so the agent sees it twice.

### `arch context`, repository has no name list

Unchanged from today, with no extra line. A repository that never adopted
contexts sees no difference.

### `arch context --all`

```
# Architectural contract — 28 accepted decisions
…
51 records not shown (45 proposed, 3 rejected, 3 superseded) — docs/architecture/
```

True. Every accepted record, with no line about the branch's contexts.

### Session report `Records` line

Narrowed:

```
Records: 6 of 28 accepted apply to this branch · `wfctl arch context` prints them, `--all` prints every one
```

Not narrowed, for any of the reasons above:

```
Records: 28 accepted · `wfctl arch context` prints them
```

Both true. The narrowed line names the command that prints the rest, which is
the second half of the issue's Done when.

### `status --json --session`

The payload keeps `accepted_records`, and gains `applying_records`, the count
that applies to the branch, or `null` when the set wasn't narrowed. `null`
rather than the total, so a consumer can tell "every record applies" from
"wfctl couldn't tell".

### Level-3 consequences

1. One function computes the selection, so the header, the footer, and the
   `Records` line can't disagree.
2. The selection reports why it didn't narrow, as a value the two renderers
   print, so the reason strings live in one place.
3. `--all` bypasses the selection rather than passing an empty list through it,
   so "every record" never depends on what the domain page says.

## Boundaries and Ownership

wfctl decides which accepted records apply to the branch, from two lists it
doesn't write: the branch's `Contexts` line, written by the agent, and each
record's `governs` field, written by its author and accepted by the user. The
agent shouldn't choose which records to read, since it would be deciding which
rules bind its own work.

The level-2 record is
`docs/architecture/branch-contexts-select-records.md`.

## Structure (level 3)

| checked | assumed |
| --- | --- |
| `_session_report.py:198` counts accepted records itself | the import check passes `_session_report.py` importing `_evidence.py` with no new baseline line |
| `cli.py:2029` loads records separately in `arch_context_cmd` | |
| the Context Map draws `AR --> EV` and `EV --> SC`, and nothing from `AR` to `SC` | |
| `_contexts.listed` and `_contexts.names` read files and never call git | |
| `_paths.resolve_spec_dir` returns `None` when the branch has no spec folder | |
| 5 of 28 accepted records carry a `governs` field today | |
| an accepted record's body is never edited, so the other 23 can't gain one | |

`_contexts.select` holds the rule, and `_evidence.records_for_branch` gathers
the paths and records for it. Both `arch context` and the session report call
`records_for_branch`.

## Software design decisions

- docs/architecture/design/700-one-function-selects-records.md — one function selects the records that `arch context` prints and the session report counts

## Key Assumptions to Validate

- The import check accepts `_session_report.py -> _evidence.py`. Run
  `.github/scripts/check_imports.py` after the change.
- An agent reading the narrowed output reads the footer line. The
  `start-session` skill names `--all` in step 2, so the agent meets it in the
  skill as well as in the output.

## MVP Scope

1. `_contexts.select` and `_evidence.records_for_branch`.
2. `arch context` narrows by default, prints the reason lines, and takes
   `--all`.
3. The session report's `Records` line and the `applying_records` key.
4. `start-session` step 2 and step 7 mention the narrowing and `--all`.
5. `architecture-decisions` says that a record binding every change leaves the
   `governs` field out.
6. A release note.

## Not Doing (and Why)

- Adding `governs` to the 23 accepted records without it. An accepted record's
  body is never edited, and the `architecture-decisions` skill forbids
  backfilling a field across accepted records. Today only 5 records can be left
  out, so the saving in this change is small. It grows with every new record.
- Turning the domain page's "Where the accepted records land" table into names
  wfctl reads. The table places 13 older records in prose, and changing the
  domain page is the user's call. It's the follow-up that would make the saving
  real for the older records.
- Finding the branch's contexts from the files it changes. Most modules haven't
  moved into their package yet (#671).
- Narrowing the proposed records. `arch context` never printed them.

## Open Questions

- Whether to file the follow-up that places the 23 older records. This is the
  user's call, since it edits the domain page.
