# Phase 1 Data Model: Architecture Knowledge Lifecycle

## Entity: Architecture Decision Record

One file, one decision. Identified by its slug — the filename without extension —
carrying no sequence number, so records created concurrently in separate
worktrees never collide.

| Field | Required | Source | Notes |
| --- | --- | --- | --- |
| `slug` | yes | filename | Stable identity. Renaming breaks inbound `supersedes`, so it is not renamed |
| `status` | yes | frontmatter | One of the five below. Absent or unrecognised → excluded from the in-force set |
| `supersedes` | no | frontmatter | Slug of the record this replaces |
| `title` | yes | first `#` heading | Human-readable |
| `Context` | yes | body section | Why the decision was needed |
| `Decision` | yes | body section | What was decided |
| `Owns truth` | yes | body section | **The wfctl-specific field.** Which side owns the question, and why the other side cannot compute it |
| `Considered` | yes | body section | Rejected alternatives, each with why |
| `Consequences` | no | body section | What follows, including requirements this generates |
| `Log` | yes | body section | One line per transition: date, new status, reason |

### Validation rules

- **VR-001** — `status` MUST parse to one of the closed set. Anything else, or
  absent, excludes the record from the in-force set. It is never treated as
  `accepted` by default.
- **VR-002** — A record whose `status` is `superseded` SHOULD be named by some
  other record's `supersedes`. A superseded record with no successor pointing at
  it is a warning, not an error — it usually means the successor is unmerged.
- **VR-003** — `supersedes` MUST name a slug that resolves to a file in the same
  architecture root. A dangling value is an error, since the reason the
  predecessor fell is what it points at.
- **VR-004** — Two records MUST NOT both name the same `supersedes` target. This
  is the split-supersession case from the spec's edge cases; it means a decision
  was replaced twice independently and a human has to reconcile it.
- **VR-005** — An `accepted` record's body is immutable. Changing a decision
  writes a new record; only the predecessor's `status` and `Log` change.
- **VR-006** — `Owns truth` MUST be present and non-empty on any record reaching
  `accepted`. It is the field the feature exists to capture; a record without it
  is the failure mode being corrected, not a lighter record.

## Entity: Status

A closed set of five. Only `accepted` puts a record in force.

| Value | Meaning | In force |
| --- | --- | --- |
| `proposed` | Written, not yet agreed | no |
| `accepted` | Currently binding | **yes** |
| `superseded` | Replaced by a named successor | no |
| `rejected` | Considered and not adopted | no |
| `retired` | Governed the work, then ended with no successor | no |

### State transitions

```
                  ┌──────────────┐
   (new record) ──►   proposed   │
                  └──────┬───────┘
                         │
              ┌──────────┴──────────┐
              ▼                     ▼
        ┌──────────┐          ┌──────────┐
        │ accepted │          │ rejected │  (terminal)
        └────┬─────┘          └──────────┘
             │
     ┌───────┴────────┐
     ▼                ▼
┌────────────┐  ┌──────────┐
│ superseded │  │ retired  │   (both terminal)
└────────────┘  └──────────┘
  successor       no successor
  required        required
```

`rejected` and `retired` are distinct and not interchangeable: `rejected` means
never adopted, `retired` means it governed the work for a period and then ended.
Collapsing them loses the fact that the decision was once binding — the
`wfctl checkpoint` removal is the worked example.

No transition returns to `proposed`, and none leaves `rejected`. Reviving a
rejected idea writes a new record; the rejected one stays as the reason not to
re-litigate it.

**These transitions are a convention checked at review, not enforced by wfctl.**
Records are hand-edited markdown and wfctl only reads `status` — it does not
mediate changes to it. What wfctl does enforce is the link integrity in VR-002,
VR-003 and VR-004, because those are checkable from the record set alone. A
status edited to an illegal value is caught by VR-001, which excludes anything
outside the closed set; a status edited along an illegal *path* is not caught,
and is a review concern.

## Entity: Architecture Root

The resolved directory holding a repository's records.

| Property | Value |
| --- | --- |
| Resolution order | `WFCTL_ARCH_DIR` → this repo's manifest `arch_root` → main checkout's manifest `arch_root` → `<repo_root>/docs/architecture` |
| Default | In-tree and version-controlled |
| Out-of-tree | Honoured, with a warning (FR-002a) |
| Existence | Never required, never created by resolution |

Resolution mirrors `spec_root` (`wfctl/_paths.py:233-264`), including its rule
that resolution neither checks the directory exists nor creates it — that check
is what broke the spec-root create path, and adding it back here would rebuild
the same bug.

## Entity: In-Force Set

Derived, never authored. The projection of records whose `status` is `accepted`.

| Property | Value |
| --- | --- |
| Source of truth | The record files |
| Computed by | wfctl |
| Empty case | Reports an empty set; not an error |
| Ordering | By slug, stable across runs |

## Ownership

Which side computes each piece of state, and why the other cannot.

**Record status** — the record file owns it. An agent cannot derive it from
content: given a directory of markdown, nothing distinguishes a decision that
binds from one replaced last month.

**Architecture root** — the repo's manifest owns it. An environment variable
cannot: it is process-global, so exporting it from a shell profile redirects
every repository wfctl touches.

**Whether the design step produced a record** — wfctl owns it, by checking the
filesystem. The agent cannot: a self-report of completion is unfalsifiable, the
same reasoning already applied in #69.

**Whether a change drew a new boundary** — the *author* owns it, declared
explicitly, and wfctl records the declaration without verifying it. Unlike
completion, this has no objective test; it is a judgment. wfctl's job is to stop
the question going unanswered, not to catch a wrong answer (FR-010a).

**The in-force set** — wfctl owns the projection. The agent cannot be handed the
directory and trusted to filter: superseded records read as live, which is the
confusion `status` exists to prevent.

**Placement of a piece of knowledge** — decided by scope, then by what is
constrained: a fact about one file belongs to that file, a constraint on the
system belongs in a record, guidance for the worker belongs in `AGENTS.md`.
