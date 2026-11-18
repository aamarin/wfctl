# A security control change gets its threat model before code

Contexts: design-method, worktree-guard, evidence-and-derivation, architecture-records

Mode: written under `auto_approve`. Each gate's answer is below and in the
records it points at, and the user approves them at the PR.

## Problem Statement

A change to a security control has a threat model the user accepted before any
code is written, and the security reviewers judge the change against it. Today
the only threat-model step runs at review time, so on #792 the coordinator
wrote the bar into the brief, the bar was stricter than the guard's accepted
one, and three security rounds chased forms the guard had already given up.

## Recommended Direction

A change that adds, removes, or narrows a security control answers the spec
pipeline's design-decision question yes, so it goes through brainstorm. At
level 2 it writes a `## Threat model` section into its record, with four parts:

1. Defends against: who the control stops, and who it doesn't.
2. Must keep catching: concrete forms the control refuses, each pinned by a test.
3. Accepts: forms the control gives up, and why.
4. Must let through: ordinary work the control must not refuse. Optional.

The user accepts the record. The security reviewers find the section, judge
each finding against it, and name the record in their report. The coordinator
writes no security bar into the brief.

The accept check's threat model moves out of R-013 into
`accept-check-threat-model.md`, with the two lists R-013 lacked.

## Level 1: what each reader sees

The agent at step 1 of `design-passes`, under the design-decision question:

```
A change that adds, removes, or narrows a security control is a yes to this
question, however small. A narrowed control can let through an action that
can't be undone, such as an accepted record or a merged PR.
```

True: the change goes to `/speckit.brainstorm`. Level-3 consequence: the
security case is a sentence inside question 2, not a fourth question, since
`every-change-answers-spec-question.md` is accepted with three.

The agent at level 2 of `design-levels`, on a security control change:

```
When the change adds, removes, or narrows a security control, the record
carries a `## Threat model` section. Write it before any code, following
`.agents/skills/architecture-decisions/references/threat-model.md`.
```

True for the author. Level-3 consequence: the section's shape lives in one
reference that both the author and the reviewer read.

The security reviewer, in its report, when the commits change a control that
has a threat model:

```
Judged against: docs/architecture/accept-check-threat-model.md (proposed)
```

When the commits change a control and no record carries a threat model for it:

```
# Finding 1: Security control changed with no threat model: `wfctl/_review_gate.py:290`
```

When a form the reviewer found is in the record's "Accepts" list, the reviewer
doesn't report it as a finding, and notes it under the judged-against line.

All three are true. Level-3 consequence: the reviewer needs a fixed heading to
search for, and a test that keeps the reviewer's headings and the reference's
headings the same.

The review coordinator's brief, after the change: it names the reviewer's id,
the reports folder, and the six dispatch bullets, and states no security bar.
The `fanning-out-code-review` skill says so beside the bullets.

## Boundaries and Ownership

Level 2 wrote two records, both proposed:

- `docs/architecture/security-change-needs-threat-model.md` governs
  design-method. The user sets the security bar by accepting a record, the
  author writes it before code, and the reviewer reads it. The coordinator
  doesn't write one.
- `docs/architecture/accept-check-threat-model.md` governs worktree-guard,
  evidence-and-derivation, and architecture-records. The user decides which
  forms the accept check must keep catching and which it gives up. The guard
  decides whether one command's text runs the accept.

The method was `architecture-design`: the contested thing is a quality,
safety under a stated adversary, with simple ownership rules, so
`model-the-domain` doesn't apply. The ranked driver is that a change to a
security control is judged against a bar the user accepted, under the
condition that nobody is at the prompt. The baseline in each record is a brief
line pointing at a research note, and it loses because the note isn't printed
at session start.

## Software design decisions

- docs/architecture/design/799-threat-model-in-the-record.md — the threat model is a section of the level-2 record, shaped by one reference both skills link

The worktree guard, evidence and derivation, and architecture records contexts
make no structural choice: their record states what the guard already does,
and the only new code is a test.

## Level 3: checked and assumed

| Checked | Assumed |
|---|---|
| An extra `## Threat model` section changes no record check (`_records.py:58` reads the tier from `Owns truth`) | A reviewer searching `wfctl arch-root` at the head finds every threat model |
| `security-and-hardening` is loaded only by `reviewing-security` (grep) | A reviewer told to name the record does so in a line wfctl doesn't count |
| `_review_gate.read` takes a command string, so a test can run each listed form | |
| Every "Must keep catching" form is refused and every "Must let through" form runs, at `c45fafb` (probe script) | |
| Every "Accepts" form passes the text check, at `c45fafb` | |
| A backticked `wfctl doctor` in a commit message is refused today, so it stays off the "Must let through" list until #792 | |

## Key Assumptions to Validate

- The skills' wording triggers the step. The walkthrough after
  `install-skills` checks this on a pretend control change.
- A reviewer told to judge against a record will drop a finding inside its
  "Accepts" list. The panel on this branch is the first test.

## MVP Scope

1. `design-passes` step 1: the security control sentence under question 2.
2. `design-levels` level 2: the paragraph sending a control change to the
   reference.
3. `architecture-decisions/references/threat-model.md`: the four parts, how to
   write each, and wfctl's own list of controls as examples.
4. `architecture-decisions/SKILL.md`: one line pointing at the reference.
5. `reviewing-security`: a section on finding and judging against the threat
   model, and the missing-threat-model finding.
6. `fanning-out-code-review`: the coordinator writes no security bar.
7. Two tests: the heading agreement, and the accept check's lists.
8. The two level-2 records and the level-3 record above.
9. A release note, `changes/799.change.md`.

## Not Doing (and Why)

- Editing `security-and-hardening`. It's vendored, and the next upstream pull
  reverts the edit.
- A wfctl check that refuses a branch changing control files without a threat
  model. Whether a change narrows a control is a judgment of meaning, so the
  reviewers report it instead.
- Threat models for `review sign-off` and `arch approve-imports`. Each one gets
  its own the next time a change narrows it.
- Fixing #792's two false refusals. That issue owns them, and its fix adds each
  form to the "Must let through" list.

## Open Questions

None that block the plan. The user accepts or rejects the two level-2 records
at the PR.
