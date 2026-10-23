---
status: proposed
---

# `wfctl check-body` checks the spec answer in the PR, and each repo names the section in `wfctl.json`

## Context

Under `every-change-answers-spec-question`, every PR says whether the change
needs a spec in a "Needs a spec?" section, and `wfctl check-body` fails a body
that leaves the section empty or N/A. This record decides how `check-body`
knows a repo requires that section.

`check-body` ships to every repo that uses wfctl, but each repo owns its PR
template. Most templates won't have this section. The check needs to fail a
body with no answer in a repo that asks for one, and stay quiet everywhere
else.

## Verified

- `check_body_cmd` (`wfctl/cli.py:6439`) checks drawings against the "Choosing
  a drawing" rule and adds a verification finding. Today it doesn't look up any
  section of the body by name.
- Its docstring says it "gates nothing — nothing runs this but the author", and
  that it exits 1 so "the finding is hard to walk past".
- `opening-a-change` runs `wfctl check-body "$BODY"` in Step 5, before `gh pr
  create`, so the skill needs no new step for the check.
- `wfctl.json` already has a `change_check` list naming the fields `wfctl
  change check` requires on an open change. `AGENTS.md` says it lives there
  because `.agents/` is gitignored and `install-skills` rewrites it.
- `.github/scripts/release.py` calls `gh pr create` directly and never runs
  `check-body`.

## Assumed

- `check-body` can find a template section in a body by its heading text. If a
  body renames the heading, `check-body` reports the section as missing. That
  errs on the safe side, since the check fails instead of passing.

## Direct baseline

`check-body` looks for a "Needs a spec?" heading in every PR body. If the
heading is there and the section is empty or N/A, it reports a finding. If the
heading is missing, it says nothing.

## Decision

A repo lists the sections every PR has to answer in `wfctl.json`, under a key
next to `change_check`. `check-body` reports a finding when a listed section is
missing from the body, has nothing but HTML comments, or only says N/A. wfctl
doesn't hardcode any section names. `wfctl check config` reports any listed
section that's missing from the repo's template.

This repo lists "Needs a spec?".

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

The two graphs differ by one arrow and by where the section name lives. In the
baseline, wfctl hardcodes the name. In the decision, the repo holds it, and
wfctl reads it. The decision is built to handle a second required section, or a
repo that names the section differently. In the baseline, either change means
editing wfctl and cutting a release. In the decision, it's a one-line edit to
`wfctl.json`.

## Considered

- **The direct baseline above.** It's the smallest change and needs no config.
  We didn't choose it because a body that deletes the heading passes, which
  defeats the point of the check. It also hardcodes one repo's template
  wording into a tool every repo runs.
- **Read the required sections from the template itself.** This keeps a single
  source of truth, since the template already has the heading. We didn't choose
  it because the template's own rule is "N/A over deletion" for every section,
  so the template can't mark which sections need a real answer. Templates also
  live in several places, and `check-body` would have to duplicate how
  `opening-a-change` finds one.
- **A separate command, run alongside `check-body`.** This keeps `check-body`'s
  scope unchanged. We didn't choose it because Step 5 of `opening-a-change`
  already runs `check-body` on every change, and a second command would mean
  adding a line to a file #622 is redesigning.

## Consequences

Other repos opt into the check by adding one line to `wfctl.json`. A repo that
doesn't add it sees no change.

This is `check-body`'s first rule about what a section says. Its docstring says
a rule the command can't settle doesn't belong in it. This one does, because
the reviewer judges the answer in the section itself, not a report that some
other work happened.

## Verification

- A test runs `check-body` on a body whose listed section says "N/A", one where
  the section holds only its HTML comment, and one with the heading deleted,
  and checks that each reports a finding.
- A test runs it on the same bodies with nothing listed in `wfctl.json`, and
  checks that none of them reports a finding.
- A test runs `wfctl check config` with a listed section that's missing from
  the template, and checks that it reports a finding.

## Log

- 2026-10-22  proposed  — #628: the spec answer needs a check that fires in a
  repository that asks for it, and nowhere else
- 2026-10-22  proposed  — revised before review: this record first put a
  boundary check in `wfctl verify`, which Andre replaced with the pull request
  section
