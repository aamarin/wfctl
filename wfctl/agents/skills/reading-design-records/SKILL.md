---
name: 'reading-design-records'
description: 'Resolve the level-3 design records a feature was written against, from the list its design.md carries. Use when /speckit.plan, /speckit.tasks, /speckit.implement or /speckit.analyze needs the structural decisions the brainstorm pass recorded, before doing its own work.'
---

# Reading a feature's design records

`/speckit.brainstorm` writes one level-3 record per structural choice that
weighed a credible alternative, and `idea-refine` lists their paths in the
feature's `design.md`. Four steps downstream have to read that list, and until
they did, a plan was written against decisions its author could not see.

This skill owns *how the list is resolved and reported*. What it does not own is
what each step then does with the records — that stays in the wrapper that sent
you here, because it is the one part the four steps do not share.

**Here rather than in `speckit-plan/SKILL.md` and its three siblings.** Those are
`github/spec-kit`-derived, and `vendor-upstream-skills` prefers a layer to an
edit: an in-place change is reverted by the next upstream pull with no conflict
to notice, and the behaviour then regresses in a diff that mentions neither the
step nor the rule. **And here rather than pasted into four wrappers**, which is
the shape this started as — forty-odd lines copied four times, already drifted
on the commit that introduced them, with one copy carrying three sentences the
others had lost. `writing-a-scan-file` is the same layer for the same reason and
is the precedent this follows.

## Resolve the list

```bash
eval "$(wfctl feature-paths)"    # binds FEATURE_DIR and REPO_ROOT
```

Read `<FEATURE_DIR>/design.md` and find the section headed
`## Software design decisions`. Every **list item** of the form
`- <path> — <text>` names a record. Read each one.

**Prose in that section names no records.** The section carries prose by design —
`/speckit.brainstorm` requires a level answered with no record to say so in one
line rather than delete the heading — and that prose may name a *level-2* record.
A level-2 record read as level-3 binds nothing while looking like it does, which
is the failure `software-design-decisions` names in its own Escalation section.

**A path may be written absolute or repo-relative, and may be wrapped in
backticks.** Strip the backticks; resolve a relative path against `REPO_ROOT`,
never against the directory holding `design.md`. That directory is the one base
that cannot work: `FEATURE_DIR` resolves outside the working tree in any repo
that records a `spec_root` there, so resolving a record path against it finds
nothing and reports every record as missing.

The producer's template writes `<arch-root>/design/<issue>-<decision>.md`, and
`wfctl arch-root` prints an absolute path — so both forms are already in
circulation, and accepting both is cheaper than a migration of every `design.md`
already written.

**Do not glob `<arch-root>/design/` by issue number instead.** That was the first
mechanism and it is silently wrong on any branch cut from an epic: the worktree
carries the epic's number, the record carries the child issue's, so the glob
loads another feature's record and misses this one. Neither failure raises
anything. `docs/architecture/design-md-indexes-the-records.md` carries the
argument.

## Four states, and none of them is silence

| What is on disk | State |
| --- | --- |
| the section, with one or more entries | `listed` |
| the section, carrying no entries | `none` |
| a `design.md` with no such section | `unknown` |
| no `design.md` at `FEATURE_DIR` | `unknown` |

A missing section is `unknown` and not `none`, on the producer's own ruling:
`/speckit.brainstorm` requires the section even when a level was answered with no
record, "rather than being deleted — a missing section reads as a level nobody
ran." So its absence says the pass predates that rule, not that the pass found
nothing. Reading it as `none` asserts something about a design pass that never
happened, and it is the *majority* state — most `design.md` files on disk today
have no such section.

`none` and `unknown` are different facts and are never collapsed. One says a
design pass ran and recorded no structural decision, which is a legitimate answer
— the record threshold exists so that not every choice earns a file. The other
says nothing is known either way. A step that reports neither reproduces #307's
defect one directory over, where a run that found nothing and a run that never
looked are the same output.

## Report it, always

In the step's own closing report, including when there was nothing:

```
Design records: 2 listed in design.md
  <path>
  <path>

Design records: none — design.md records no level-3 decision

Design records: unknown — no design.md at <FEATURE_DIR>

Design records: unknown — design.md at <FEATURE_DIR> has no
  `## Software design decisions` section
```

A listed path that will not read gets its own line reading
`<path> — listed, not found`, and does not stop the step. That covers a record
that moved and a record
whose path does not resolve; it does **not** cover a path outside the working
tree, which is a supported configuration — `arch_root` is overridable, `wfctl
arch-root` warns and exits 0, and the records there read fine. Reporting a
readable out-of-tree record as missing would apply to the records the very
argument that `design-md-indexes-the-records` rejects for `design.md`.

Report paths, never a summary. A digest of a record is a second copy of it, and
the copy is what drifts — `design.md`'s own rule, one step downstream.

## Verification

- [ ] The list came from `design.md`'s bullet entries, not from a glob and not
      from prose in the same section.
- [ ] A relative path was resolved against `REPO_ROOT`.
- [ ] The report names every path, and states which of the four states was found.
- [ ] `none` and `unknown` were not collapsed, and a missing section reported
      `unknown`.
