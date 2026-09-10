# Phase 1 data model — #321

One existing entity gains one transition. No new entity, no new file, no new
persisted state.

## Record

Already defined at `wfctl/_arch.py:29`. Unchanged by this feature:

| Field | Meaning |
| --- | --- |
| `slug` | filename without extension; the record's identity |
| `path` | where it is on disk |
| `status` | one of `_arch.STATUSES`, or `""` when absent or unrecognised |
| `supersedes` | slug of the record this replaces, or `""` |
| `body` | the file as read |

## Status lifecycle

The closed set is unchanged. What this feature adds is the second edge, and the
guard that says which edges start where.

```
                    ┌──────────┐
  a record is       │ proposed │
  born here    ────►└────┬─────┘
                         │  accept()   ← this feature
                         ▼
                    ┌──────────┐
                    │ accepted │ ──── in force: projected by `arch context`
                    └────┬─────┘
                         │  supersede()
                         ▼
                   ┌────────────┐
                   │ superseded │
                   └────────────┘

   rejected, retired — defined in STATUSES, reachable by nothing.
                       Out of scope: no consumer, no demand.
```

`accept()` accepts an edge only from `proposed`. Every other source status is
refused, in three distinguishable ways:

| Current status | Refusal, because the reader's next action differs |
| --- | --- |
| `accepted` | nothing to do; a second `Log` line would claim a second agreement |
| `superseded`, `rejected`, `retired` | a decision binding again is a new record |
| `""` (absent or unrecognised) | fix the frontmatter; accepting would overwrite it |

`supersede()` keeps its current behaviour and gains no guard. It is not
idempotent-looking in the way `accept` is — its `Log` line names a successor, and
the question of which source statuses may be superseded is not this feature's.

## The `Log` line

Appended, never rewritten. One line per transition:

```
- <YYYY-MM-DD>  <status padded to 12>— <note>
```

`<YYYY-MM-DD>` is the UTC date (`spec.md § Clarifications`). `<note>` is the
citation for `accept` and the reason for `supersede`. The 12-character column is
what every existing record already uses; `supersede`'s current output is
`superseded` followed by exactly two spaces, which the padding reproduces.

## Citation

Not an entity and not a stored field. It is the free text a person passes, checked
for presence and for not being a `<placeholder>`, then written into the `Log` line
and never read back by wfctl. Its only consumer is a person reading the record.
