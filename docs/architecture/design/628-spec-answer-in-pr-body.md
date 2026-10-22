---
status: proposed
---

# `wfctl check-body` checks the spec answer in the pull request, and a repository names the section in `wfctl.json`

## Context

`every-change-answers-spec-question` decides that every pull request answers
whether the change needs a spec, in a "Needs a spec?" section, and that `wfctl
check-body` fails a body whose section is empty or N/A. This record decides how
`check-body` knows the section is required.

`check-body` ships to every repository that uses wfctl, while the pull request
template belongs to each repository. Most templates won't have this section. The
check must fail a body with no answer in a repository that asks for one, and
stay silent in a repository that doesn't.

## Verified

- `wfctl/cli.py:6439`, `check_body_cmd`, checks drawings against the "Choosing a
  drawing" rule and adds a verification finding. It reads no section of the body
  by name today.
- Its docstring says it "gates nothing — nothing runs this but the author", and
  that it exits 1 so "the finding is hard to walk past".
- `opening-a-change` Step 5 runs `wfctl check-body "$BODY"` before `gh pr
  create`, so the check needs no new step in that skill.
- `wfctl.json` already holds a `change_check` list, which names fields `wfctl
  change check` requires on an open change. The project instructions say it
  lives there because `.agents/` is gitignored and rewritten by `install-skills`.
- `.github/scripts/release.py` runs `gh pr create` itself and never runs
  `check-body`.

## Assumed

- A template section can be found in a body by its heading text. A body that
  renames the heading would then read as missing the section, which is the safe
  direction, since it fails rather than passes.

## Direct baseline

`check-body` looks for a heading named "Needs a spec?" in every body it reads.
When the heading is present and its section is empty or N/A, it reports a
finding. When the heading is absent, it says nothing.

## Decision

A repository lists the sections every pull request must answer in `wfctl.json`,
under a key beside `change_check`. `check-body` reports a finding when a listed
section is missing from the body, empty once its HTML comments are removed, or
holds only N/A. wfctl knows no section names of its own. `wfctl check config`
reports a listed section that the repository's template doesn't carry.

This repository lists "Needs a spec?".

## Diagram

```
                 baseline                                  decision

stable   ┌──────────────────────────────┐         ┌──────────────────────────────┐
         │ wfctl check-body             │         │ wfctl check-body             │
         │ (knows "Needs a spec?")      │         │ (knows no section names)     │
         └──────────────▲───────────────┘         └───────▲──────────────┬───────┘
                        │ reads                           │ reads        │ reads
════ wfctl / this repository ═════════════════════════════╪══════════════╪════════
                        │                                 │              │
volatile ┌──────────────┴───────────────┐         ┌───────┴──────┐ ┌─────▼──────────┐
         │ PR body                      │         │ PR body      │ │ wfctl.json     │
         └──────────────────────────────┘         └──────────────┘ │ sections (new) │
                                                                   └────────────────┘
```

The two graphs differ by one arrow and by where the section's name lives. In
the baseline, wfctl holds the name. In the decision, the repository holds it and
wfctl reads it. The change this is built to absorb is a second required section,
or a repository naming the section differently. In the baseline, either change
edits wfctl and ships a release. In the decision, it edits one line of
`wfctl.json`.

## Considered

- **The direct baseline above.** It is the smallest change and needs no
  configuration. We didn't choose it because a body that deletes the heading
  passes, which defeats a backstop. It also puts one repository's template
  wording into a tool every repository runs.
- **Read the required sections from the template itself.** It keeps one source,
  since the template already carries the heading. We didn't choose it because
  the template's own rule is "N/A over deletion" for every section, so the
  template can't say which sections must hold a real answer. Templates also live
  in several places, and `check-body` would have to repeat how `opening-a-change`
  finds one.
- **A separate command, run beside `check-body`.** It keeps `check-body`'s scope
  where it is. We didn't choose it because Step 5 of `opening-a-change` already
  runs `check-body` on every change, and a second command would need a new line
  in a file #622 is redesigning.

## Consequences

Other repositories get the check by adding one line to `wfctl.json`. A
repository that adds nothing sees no change.

`check-body` gains its first rule about a section's content. Its docstring says a
rule it can't settle doesn't belong in it. This one belongs because the answer
in the section is the thing a reviewer judges, not a report that some other
work happened.

## Verification

- A test runs `check-body` on a body whose listed section holds "N/A", one where
  it is empty under its HTML comment, and one where the heading is deleted, and
  checks that each reports a finding.
- A test runs it on the same bodies with nothing listed in `wfctl.json`, and
  checks that none of them reports a finding.
- A test runs `wfctl check config` with a listed section the template doesn't
  carry, and checks that it reports one.

## Log

- 2026-10-22  proposed  — #628: the spec answer needs a check that fires in a
  repository that asks for it, and nowhere else
- 2026-10-22  proposed  — revised before review: this record first put a
  boundary check in `wfctl verify`, which Andre replaced with the pull request
  section
