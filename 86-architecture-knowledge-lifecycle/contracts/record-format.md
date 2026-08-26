# Contract: Architecture Decision Record Format

The on-disk shape of one record. This is the contract between the skill that
writes records and the code that reads them.

## Literal example

```markdown
---
status: accepted
supersedes: agent-runs-the-check
---

# wfctl runs the verification, not the agent

## Context

Completion was accepted from a file the agent wrote when it believed it was
finished. Nothing checked that the work passed.

## Decision

wfctl runs the verification command and records the result. The agent never
reports its own completion.

## Owns truth

wfctl owns "did the check pass, and against which tree?".
The agent cannot: a self-report is unfalsifiable.

## Considered

- agent writes `implement-complete.md` — unfalsifiable, the failure being fixed
- trust-but-audit after the fact — the audit never runs

## Consequences

The record binds to a commit sha and a dirty flag, so any drift after the run
marks the result stale rather than passing.

## Log

- 2026-03-14  accepted    — self-report is cheap, start there
- 2026-08-11  superseded  — unfalsifiable; verification moves to wfctl
```

## Parsing rules

Frontmatter is read by line scan, not a YAML parser — wfctl's runtime
dependencies are `typer` and `rich`. Mirrors `_skill_deployment`
(`wfctl/cli.py:786-799`).

```
line 1 is not exactly "---"        → no frontmatter; status absent
scan until the next "---"          → frontmatter body
line starts with "status:"         → value = rest, stripped of quotes
line starts with "supersedes:"     → value = rest, stripped of quotes
key absent                         → status absent
```

## Status values

| Parsed value | In force |
| --- | --- |
| `accepted` | **yes** |
| `proposed`, `superseded`, `rejected`, `retired` | no |
| absent, empty, or unrecognised | **no** |

The last row is the load-bearing one and differs deliberately from
`_skill_deployment`, which defaults to the common case. Here the default is the
conservative case: an unparseable record is never treated as binding, because
presenting an unreviewed decision as in force is the failure the field exists to
prevent.

## Required sections

A record reaching `accepted` must carry `Context`, `Decision`, `Owns truth`,
`Considered`, and `Log`. `Consequences` is optional.

`Owns truth` is the field this feature exists to capture. A record without it is
not a lighter record — it is the 0-of-11 failure mode with a new filename.

## Immutability

Once `accepted`, only two things change in a record, ever:

```
status:  accepted → superseded | retired
Log:     one line appended
```

The body is never edited. A changed decision is a new record. Git holds the edit
history; the file holds only what git cannot answer.

## Identity

The slug is the filename without extension: `wfctl-runs-the-check.md` →
`wfctl-runs-the-check`. No sequence number. `supersedes` names a slug.

Renaming a record breaks every inbound `supersedes`, so records are not renamed.
