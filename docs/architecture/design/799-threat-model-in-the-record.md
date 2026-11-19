---
status: proposed
governs: design-method
---

# The threat model is a section of the level-2 record

## Context

`security-change-needs-threat-model.md` requires a threat model before code for
any change to a security control, and requires the security reviewers to judge
against it. Two skills have to agree on where the threat model is and what it
holds: the design skills write it, and `reviewing-security` reads it. If each
skill describes the section in its own words, the two copies drift, and the
reviewer looks for a heading the author never wrote.

`vendor-upstream-skills.md` rules out editing `security-and-hardening`, the one
skill that already has a threat-model step, since it's vendored from another
project.

## Verified

- `wfctl/arch/_records.py:58` reads a level-2 record's tier from its
  `Owns truth` heading alone, so an extra `## Threat model` section changes no
  check.
- `wfctl arch context` projects only the first paragraph of `Decision`, so the
  threat model prints only as far as the decision names it. The reviewer reads
  the section from the record file.
- `grep -rl "security-and-hardening" wfctl/agents/` finds it loaded only by
  `reviewing-security`, so no design skill reads its threat-model step today.
- `reviewing-security` lets a reviewer run read-only commands such as
  `git show` and `rg`, which is enough to find a record by its heading.
- The guard's `read` function in `wfctl/_review_gate.py` takes a command string
  and returns the refusals, so a test can run each listed form through it
  without a shell.

## Assumed

- A reviewer finds the threat model by searching every markdown file for the
  heading at the commit the branch left the trunk at, at the trunk, and at the
  run's head, and keeps the hits with a `status` in their frontmatter. The
  search doesn't use `wfctl arch-root`, because that reads a manifest the
  branch can commit, and a branch could point it away from an accepted
  record. If a repository keeps its records outside the repository, the
  search finds nothing, and the reviewer reports the change as missing a
  threat model, which is the safe direction.

## Direct baseline

Write the threat-model instructions twice: a paragraph in `design-levels`
saying what the section holds, and a paragraph in `reviewing-security` saying
what to look for. No new file. Each change to the section's shape then edits
both skills, and nothing notices when only one is edited.

## Decision

The threat model is a `## Threat model` section in the change's level-2 record,
with four `###` parts: `Defends against`, `Must keep catching`, `Accepts`, and
`Must let through`. The last part is optional.

One reference file, `architecture-decisions/references/threat-model.md`, says
what each part holds and how to write it. `design-levels` level 2 links it for
the author. `reviewing-security` links it for the reviewer and names the four
headings it reads. A test in wfctl's suite checks that the reference and
`reviewing-security` name the same headings.

A second test reads the "Must keep catching" and "Must let through" lists in
`accept-check-threat-model.md` and runs each form through the guard. That keeps
the record and the guard in agreement, and it's specific to this repository.

## Diagram

```
          baseline                          decision

stable                                ┌──────────────────────┐
                                      │ threat-model.md (new)│
                                      └──────────────────────┘
                                         ▲ links         ▲ links
════ vendored skills stay unedited ══════╪═══════════════╪══════
                                         │               │
volatile ┌──────────────┐ ┌───────────┐ ┌┴─────────────┐ ┌┴──────────────────┐
         │ design-levels│ │reviewing- │ │ design-levels│ │ reviewing-security│
         │ (own copy)   │ │security   │ └──────────────┘ └───────────────────┘
         └──────────────┘ │(own copy) │
                          └───────────┘
```

The baseline has two copies of the section's shape and no arrow between them,
so a change to the shape has to find both. The decision has one copy and two
arrows into it, so a change to the shape edits one file, and the heading test
fails if `reviewing-security` falls behind.

## Considered

- A new skill, `threat-modeling`, triggered by its description. We didn't
  choose this because a description-triggered skill can fail to fire, and the
  step has to run at a fixed point in level 2. A reference linked from that
  point runs every time `design-levels` reaches it.
- A separate template file, `threat-model-template.md`, beside
  `record-template.md`. Equally sound, but the threat model is a section of a
  record rather than a document of its own, and a second template invites a
  second file.
- Adding the section to `record-template.md` for every record. We didn't choose
  this because most records aren't about a security control, and an empty
  section on every record reads as a step that was skipped.

## Consequences

- The section's shape lives in one file, and a change to it reaches both the
  author and the reviewer.
- The heading test fails if `reviewing-security` stops naming a heading the
  reference defines, so the two can't drift silently.
- A repository other than wfctl gets the reference and the reviewer's
  instructions, but not the test that reads a record's lists. That test reads
  this repository's guard.

## Verification

- `tests/` gains a test comparing the `###` headings in the reference with the
  headings `reviewing-security` names.
- `tests/` gains a test that runs each form in the accept check's lists through
  `_review_gate.read` and checks it's refused or let through as listed.
- Walking a pretend security control change through `design-levels` reaches the
  reference at level 2, and the reviewer instructions find the section by its
  heading.

## Log

- 2026-11-18  proposed  — #799 level 3: where the threat model's shape lives so
  the author and the reviewer agree on it.
