# Data Model: Session Stopped, Not Finished

**Branch**: `352-session-stopped-not-finished` | **Date**: 2026-09-11

One entity changes shape. The other three are named because the spec names them
and because the routing rule reads across all four, not because this feature
introduces them.

## Stop record

One appended line in `<state-dir>/events.jsonl`. Written only by `wfctl end`.

| Field | Type | Written | Meaning |
|---|---|---|---|
| `ts` | string, `YYYY-MM-DDTHH:MM:SSZ` | always, by `append_event` | when the stop happened |
| `event` | string, `"end"` | always | *a session stopped here* |
| `step` | string | always | the pipeline step observed at the moment of the stop, annotation included |
| `continued` | boolean | **new** — always on lines written from now on | `true`: the work continues, the next session carries on. `false`: the session was wrapped up. |

**Absent `continued` reads as `false`.** A line on disk today carries no such
key, and nothing rewrites it — FR-008 forbids amending a stop already recorded,
and SC-005 requires every existing reader to reach the verdict it reaches today.
The absence is the migration, and there is no other one.

`false` and absent route identically and are not the same fact: one is a stop
that declared itself finished, the other predates the declaration existing. Only
a reader of the raw log can tell them apart, and none needs to.

**Validation**: none beyond the type. `continued` is *declared by the caller*,
not concluded by `end`. This is the line that separates it from `status:
complete`, which #70 removed because `end` wrote it on every run while being
able to observe nothing about it. `end` can observe that it was told; it cannot
observe that the work is unfinished, and it does not say so.

**Transitions**: none. Append-only. A stop is never amended, rewritten or
removed (FR-008).

## Branch history

The ordered sequence of stop records for one branch — every line in that
branch's `events.jsonl` whose `event` is `"end"`, in file order.

- **Its last element** answers *why did the last session stop* — the second
   question the routing rule asks, and on an issue branch it asks it of nothing
   (FR-007).
- **Its length** answers *how often was this run interrupted* (SC-004, User
  Story 3).
- **Empty** is a distinct answer and not a default: no session has stopped on
   this branch. On trunk it routes with *finished* rather than with continued —
   a branch nobody has stopped has nothing saying a run was cut off, and trunk's
   default is the question. On an issue branch it is not consulted.

## Handoff

`<state-dir>/session-summary.md`. Unchanged by this feature in every respect —
same template, same location, same write-once rule, same kept-file report
(FR-002).

Two observable states matter to `end --continued`, and they are the only two it
is allowed to distinguish:

```
not mine   no `**Step**:` reading       → end says nothing at all
unfilled   ## Next Session TODO absent, empty, or holding only
           `- [ ] (fill in)`            → end warns; step 9 will ask
filled     anything else                → end says nothing; step 9 judges
```

`not mine` is read first and it is the common case on a fresh worktree.
`worktree-handoff` forbids adding a `Next Session TODO` to a handoff, so every
one of them is `unfilled` by the narrower test — the file most likely to carry a
usable first action, warned about on the one branch shape #352 exists for. The
`**Step**:` reading is what `end` wrote and `end-session` is told to leave alone,
so it separates the two without either skill learning about the other.

`filled` is not a claim that the handoff names a usable first action. It is the
absence of the one thing `end` can see. The judgment stays in step 9, whose gate
is quoting a literal sentence, and no stop record relaxes it (FR-006).

## Branch kind

Not a stored entity either — read off the branch name by `extract_issue_key`,
which `wfctl status --json` surfaces as `issue`.

| Value | Means |
|---|---|
| a key (`352`, `PROJ-123`) | the branch exists for one tracked thing and names it |
| `unknown` | it does not — a trunk branch |

`unknown` is the literal, and reading it rather than judging the branch name is
the whole of the rule: the key is whatever this repo's `key_pattern` matches at
the *front* of the name, so `main-rewrite` is trunk and `develop-2` may not be.

## Routing input

Not stored anywhere — derived on every read, by `start-session` step 9, from the
three facts above. Stated here because it is the feature's actual output:

```
                     issue branch      trunk, last stop    trunk, last stop
                                       continued           finished or none

handoff names a
first action you     carry on          carry on            ask
can quote

no quotable          ask               ask                 ask
first action
```

**The branch is the first column, and on most branches it is the only one read.**
An issue branch is named for the work, so a session that wrapped up deliberately
there left the same issue open and the question has one answer either way. Trunk
carries no answer in its name and a handoff from every session that ever ended
on it, which is where the question belongs — and where a continued stop is the
one thing that can answer it with nobody present.

`session-state-is-re-derived` is why this is a table and not a field: all three
inputs are on disk, so the answer is recomputed at every session start and
nothing carries a conclusion forward. A context reset destroys the agent's
memory and changes none of it (FR-003).
