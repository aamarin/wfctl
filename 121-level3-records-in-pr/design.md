# Downstream consumption of level-3 design records

Issue: #326 (child of epic #121, scope item 6)
Mode: `auto_approve: true` — the four design gates were answered into the records
below rather than to a reader, and approval moves to the PR.

## Problem Statement

How might a plan, its tasks, and its implementation be written against the
structural decisions the brainstorm pass already argued out and committed —
rather than beside them?

## Recommended Direction

Seven level-3 records exist under `docs/architecture/design/` and nothing in the
pipeline reads any of them. `/speckit.brainstorm` writes them, `idea-refine`
lists their paths in `design.md`, and then the chain stops: `speckit-plan` loads
`spec.md` and the constitution, `speckit-tasks` loads `plan.md`,
`speckit-implement` loads `tasks.md`, and `speckit-analyze` runs six detection
passes over those three artifacts. A decision that was written down, committed,
and made visible in the PR is invisible to every step that acts on it.

The direction is the smallest one that closes the loop. Each downstream step asks
the feature's own one-pager — `wfctl feature-paths` for `FEATURE_DIR`, then the
paths listed in `design.md` under `## Software design decisions` — and reads what
comes back. `speckit-analyze` gains a seventh detection pass beside its six,
taking the same record set as one more input to the read it already performs.

The first version of this design derived the set from an issue-prefixed glob
instead. It was falsified on this branch during `/speckit.specify`: the branch is
named for the epic, the record for the child issue, and the glob loaded a record
from a different feature while missing the one written here.

Nothing new is built. No command is written, no field is added to the record
format, no section is added to `spec.md` or `plan.md`. The instruction lands in
the four command wrappers under `wfctl/agents/commands/`, which is where
`speckit.analyze.md` already puts its scan-file instruction for the same reason:
the skills are spec-kit-derived, and an in-place edit there is reverted by the
next upstream pull with no conflict to notice.

## Behavior — what each step renders

Level 1's gate, answered as the literal string each reachable state produces.

For `plan`, `tasks` and `implement`, one line in the step's closing report. Three
reachable states, because `design.md` can be absent as well as empty, and the two
are different truths — one says the design pass recorded nothing, the other says
no design pass ran:

```
Design records: 1 listed in design.md
  docs/architecture/design/326-contradiction-is-a-seventh-pass.md

Design records: none — design.md records no level-3 decision

Design records: unknown — no design.md at <FEATURE_DIR>
```

For `analyze`, one row in the scan file's existing coverage table, between
`F · Inconsistency` and the coverage percentage:

```
| G · Design-record contradiction | Clear (2 records read)  |
| G · Design-record contradiction | 1 CRITICAL              |
| G · Design-record contradiction | 1 warning               |
| G · Design-record contradiction | None listed             |
| G · Design-record contradiction | No design.md            |
```

The two empty states render rather than being omitted, and they render
differently. That is the level-1 decision carrying a level-3 consequence: the
read runs unconditionally rather than inside a branch that skips the row when it
finds nothing, and it distinguishes "the design pass recorded no decision" from
"no design pass ran" — because a step that found no records, a step whose input
was missing, and a step that never looked must not be the same output. #307's
argument, met one directory over.

The second level-1 decision with a level-3 consequence: the row and the report
line name records **by path**, never by summary. That is `design.md references,
never duplicates` applied one step downstream, and it forces the severity split
to read frontmatter — the pass parses each record's `status` rather than only
globbing filenames.

## Boundaries and Ownership

**Which design records apply to this feature's work?** — owned by `design.md`,
answered by the paths `idea-refine` wrote under `## Software design decisions`
at the moment the records were written.

A filename convention cannot compute it. The record template numbers a record
for the issue being implemented; a worktree is named for the issue that existed
when it was created; and a child issue is filed *during* the brainstorm pass,
after the worktree exists. On this branch those three rules produce a glob that
loads #122's record and misses the one written here — see the level-2 record for
the drawing. `spec.md` could carry a propagated list instead, and that loses on
price rather than correctness: `required-sections-are-wfctls` makes the section
list a constant checked against the shipped template, so every repo wfctl
installs into would carry a section most features leave empty.

**How severe is a contradiction?** — owned by the record's own frontmatter.
`status: approved` means a human ratified it, so a task reversing it is CRITICAL;
`status: proposed` means the decision was put but not ratified, so a task
reversing it is a warning. Gating on `approved` alone is the literal reading of
epic item 6 and would ship the pass dead: zero of seven records are approved, and
an unattended run approves none.

Written as records, not as sections here — `docs/architecture/design-md-indexes-the-records.md`
for the first, and the level-3 record below for the second.

## Software design decisions

- `docs/architecture/design/326-contradiction-is-a-seventh-pass.md` —
  contradiction detection is a seventh pass inside analyze, on the same read as
  the other six, rather than a `wfctl` command comparing declared invariants.

Level 2 answered with a record of its own:
`docs/architecture/design-md-indexes-the-records.md`. Level 1 produced no
level-3 record — its two decisions generated requirements the record above
already carries, and neither weighed a credible structural alternative.

## Key Assumptions to Validate

- [ ] A model reliably detects a prose contradiction between a record's
      `Decision` section and a task description. Test: write a task that
      deliberately reverses an approved record, run `/speckit.analyze`, confirm
      it reports CRITICAL and names the record. A clean verdict falsifies the
      whole direction.
- [ ] The `Decision` section is where a contradiction is detectable. Test: the
      same run against a record whose binding content sits in `Consequences`. If
      the pass misses it, the input is the whole record rather than one section.
- [ ] `## Software design decisions` is present and parseable in a `design.md`
      the four steps did not write. Test: run each step against this feature's
      own `design.md` and confirm it recovers the one path listed. This replaces
      the issue-prefixed glob assumption, which was not validated but falsified —
      on this branch, during this session.
- [ ] A record written by hand, with no brainstorm pass, still reaches the
      pipeline. It does not, by construction. Test: confirm the third render
      state above ("no design.md") makes that visible rather than silent, which
      is the whole mitigation.
- [ ] Loading records does not blow the context budget at `implement`. Test:
      measure with a feature carrying three records. Unmeasured, this is a bet,
      not a claim.

## MVP Scope

In:

- `speckit.plan.md`, `speckit.tasks.md`, `speckit.implement.md` — resolve the
  record set, read it, report it by path including the empty case.
- `speckit.analyze.md` — pass G, the severity split on `status`, and the scan
  file row.
- Tests that the four wrappers ship and cross-reference, in the shape the suite
  already checks skills with.

Out of the MVP, and everything below stays out of the change:

- Any change under `wfctl/` beyond the command wrappers. No predicate, no
  constant, no new CLI verb.
- Any change to the record format or its template.

## Not Doing (and Why)

- **`wfctl design check` / `wfctl design context`** — #121's out-of-scope
  section, for its own reason: a command written against a record schema that
  has survived no real use is a migration.
- **A machine-readable `invariant:` field on the record** — the same bet one
  level down. It would have to be invented and written into seven existing
  records before a single one has been contradicted.
- **Propagating the record list into `spec.md`** — costs a constant, a template
  edit and a test paid by every repo, to serve a section most features leave
  empty.
- **Cross-feature record references** — a task in feature B respecting a record
  written for feature A is not reached by an issue-scoped glob. No instance
  exists yet, and inventing the mechanism for it now is the catalog mistake at a
  smaller scale.
- **Making level-3 records binding** — `_arch.py` globs `*.md` non-recursive on
  purpose. `design/` stays invisible to `wfctl arch context`; wanting otherwise
  is level 2's territory.
- **Fixing the `_observe` exclusion gap** — real, and separate. See below.

## Open Questions

- **`cli.py:655` and `cli.py:450` exclude `<arch-root>/scans/` and not
  `design/`.** The comment at `cli.py:648` names this as pre-existing and leaves
  it deliberately. This change alters its weight rather than its answer: making
  downstream consumption real is what makes level-3 records routine on a branch,
  which turns `boundary` into a constant-true observation and the `record:`
  listing into one that names decisions the level-2 gate does not count. Same
  failure as #307, one directory over. Filed as **#327** and deliberately not
  folded in: `touched_on_this_branch` takes one `exclude` subtree, so the fix
  widens a signature, and the two call sites want opposite answers — the
  `record:` listing should arguably keep level-3 records and label them, while
  `boundary` should drop them to agree with `design_block`.
- **Whether `speckit-tasks` should cite records per-task.** Epic item 6 says the
  steps load "only the ones their tasks reference", which implies a per-task
  citation this design does not add — the glob is feature-scoped, not task-scoped.
  For a feature carrying one to three records the distinction buys nothing; it
  starts to matter at a scale no feature here has reached. Deferred rather than
  answered.
