# #309 — specify and plan prove only that a file is non-empty

## Problem Statement

How might we let `speckit-orchestrate` pass `specify` and `plan` unattended
without trusting a file whose only qualification is being longer than zero bytes?

Both steps carry `automatic`, and both predicates read file size. Constructed
against `_infer_steps` and reproduced on this branch: a `spec.md` whose entire
content is the character `x` reads `specify ●`; a `plan.md` of `x` reads
`plan ●`. That is not an adversarial case — it is what a truncated write, a
failed generation or a bare `touch` produces, and all three render green today.

`clarify` sits one rung higher for free: it requires a `## Clarifications`
heading, a structural read of the same file `specify` declines to inspect. The
missing check was never expensive. It was never asked for.

## Recommended Direction

Both predicates read the artifact's **shape**: whether it carries the sections
its template defines. The section names live in wfctl's code as constants, and a
test in wfctl's own suite holds them against the templates the same wheel ships.

`spec.md` must carry the four headings its template marks `_(mandatory)_`:

```
## User Scenarios & Testing
## Requirements
## Success Criteria
## Validation Strategy
```

`plan.md` must carry four its template defines. That template marks nothing
mandatory, so the list is wfctl's own choice from the template's own headings:

```
## Summary
## Technical Context
## Constitution Check
## Project Structure
```

`## Complexity Tracking` is deliberately absent, on the review panel's finding:
the template tells the author to fill it *only* where the Constitution Check found
violations, so requiring it would leave an author who followed that instruction
unable ever to clear the step. A required list may out-strict its template; it may
not contradict it.

Matching is stem-anchored, `^##[ \t]+<name>\b` over fence-blanked text — the
idiom `clarify` already uses. It has to be: the `_(mandatory)_` suffix survives
verbatim into 23 of the 25 specs on disk, so a full-line match would reject the
corpus it was measured against. `\b` keeps `## Requirements` from matching
`## RequirementsTODO`, and keeps it from matching `## Functional Requirements`,
which is the strictness the direction was chosen for.

Neither step accepts a document that is still its own template. Structure alone
cannot reject one — `setup-plan.sh` runs `cp plan-template.md plan.md`, so the
first act of `/speckit.plan` produces a file carrying every required heading and
no content. Both steps therefore also reject a document still carrying `ACTION
REQUIRED`, the templates' own instruction to the author. It appears in both
templates and in none of the 49 real artifacts on disk; `NEEDS CLARIFICATION`
would have been the symmetric choice and rejects real work, since three plans
discuss markers in prose.

A file that exists but carries no sections reads `in_progress`, annotated with
what it lacks, and routes back to the step's own command. Not `pending`: the
file is there, and saying otherwise would tell the agent to start over.

## Boundaries and Ownership

Recorded at `docs/architecture/required-sections-are-wfctls.md` (proposed).

wfctl owns *"must a spec carry these sections for the step to pass?"*. Upstream
cannot answer it — a template states what a document should contain and has no
claim on what a pipeline treats as sufficient evidence. The installed
`.specify/` tree cannot answer it either, for a plainer reason: it need not
exist. `wfctl status` works from a spec directory alone, so a predicate that
read the template would have to decide what a missing template means, and both
answers are wrong — passing restores this defect, failing blocks a repository
whose only fault is not having run `install-skills`.

So inference reads the spec directory and nothing else, exactly as it does
today. No new input.

`vendor-upstream-skills` is not superseded. Its subject is the file and who owns
its contents; no template is edited here. What this adds is that a fact *about*
an upstream document may be pinned in wfctl's code, provided a check holds the
pin against the document.

## Also in scope: clarify's silent skip

Folded in deliberately, on the user's call, having been raised as a separate
issue first.

When `spec.md` carries no `## Clarifications` heading and a `plan.md` exists,
`clarify` reads `skipped` — and `skipped` advances the pipeline exactly as
`done` does. `/speckit.clarify` writes that section on every run including a
clean scan, so a missing heading is unambiguous evidence the scan never ran. The
pass is a deliberate policy, not weak evidence, and it is silent.

The state does not change. `clarify` still reads `skipped` and still advances.
It gains an annotation saying why, through the slot `brainstorm`, `decompose`
and `implement` already use:

```
clarify   –  scan never ran
```

Kept as an annotation rather than a rung move because a diff that tightens two
predicates *and* relitigates a third step's verdict is one a reviewer cannot
take apart. This says the quiet part out loud and changes nothing else.

## Key Assumptions to Validate

| | Claim | Status |
|---|---|---|
| 1 | `_(mandatory)_` survives into real specs | **checked** — 23 of 25 carry it verbatim |
| 2 | the five plan headings appear unsuffixed | **checked** — 23 of 24 carry all five |
| 3 | non-conforming specs predate the pipeline | **checked** — the 3 are the oldest on disk, ported in |
| 4 | upstream has never renamed a heading here | **checked** — 1 commit on the template, the vendoring |
| 5 | nothing outside `_infer_steps` reads `plan` as done in a way this flips | assumed |
| 6 | `reason` gaining a `skipped` producer breaks no consumer | assumed |

Claims 5 and 6 are settled by the test suite rather than by reading, and are
what `/speckit.plan` is for.

## MVP Scope

- `_REQUIRED_SPEC_SECTIONS` and `_REQUIRED_PLAN_SECTIONS` beside the predicates.
- The `specify` and `plan` arms read them; `plan.md` is read as text for the
  first time, fence-blanked as `spec.md` already is.
- `clarify`'s `skipped` branch sets a reason, joining the two dicts at the foot
  of the loop.
- The rung comment at the top of `_pipeline.py` updated — `specify` moves to
  `1 + 2 + 3`, `plan` to `1 + 2`, `clarify` gains its annotation clause.
- A drift test comparing both constant lists against the shipped templates.
- Tests: the `x` case leaves both steps not-done; a real spec dir from
  `~/Development/wfctl-specs/` still reads done.

## Not Doing (and Why)

- **Flipping either flag to `review_required`** — out of scope in #309 and
  against #100's direction; it trades an unchecked pass for a human pause on
  every run.
- **Extending `wfctl.json`'s `verify` to these steps** — "is this spec adequate"
  has no executable answer, so the entry would be a command invented to have
  something to run, rendering in `status` as a strong badge over weak evidence.
- **A per-step sentinel file** — the agent that wrote the thin `spec.md` writes
  the sentinel.
- **Reading the required names from the template at inference time** — the
  absent-and-stale input above.
- **Editing the three legacy spec dirs to conform** — closed work on closed
  branches; rewriting finished history to satisfy a checker.
- **#308's `tasks`/`implement` gap** — same audit, different question, live
  branch already on it.

## Open Questions

None blocking. Claims 5 and 6 above are the two things `/speckit.plan` has to
settle before implementation.

## Software design decisions

No level-3 record. The matching idiom is `clarify`'s existing
`^##[ \t]+Clarifications\b` over fence-blanked text, taken as-is; no credible
structural alternative was weighed beyond what the level-2 record carries.
