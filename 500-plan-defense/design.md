# plan-walkthrough

## Problem Statement

How might a person who is about to put their name on a plan or a change find
out, privately and before anyone else does, whether they can actually explain it?

## Recommended Direction

Plan walkthrough is a check a person runs for their own accountability. The agent
asks one material question at a time about what was written, and the person
answers. What comes out is a record of what they could explain and what they
could not, and that record stays on their machine unless they choose otherwise.
It tests the person, not the plan; a review of whether the plan holds together
is a different pass (#501).

wfctl ships the skill and a `/plan-walkthrough` command, and no placement of its
own. A repository that wants the check in its workflow declares it as a pass in
`wfctl.json`, under whichever step fits, such as after `plan` or after
`implement`:

```json
{ "steps": { "implement": [
  { "name": "plan-walkthrough", "command": "/plan-walkthrough",
    "evidence": "change-walkthrough.md", "needs_person": true }
] } }
```

This uses today's `steps` machinery plus one new field, `needs_person`. The
skill keeps the candidate's two modes: plan walkthrough before tasks exist, and
change walkthrough once code exists.

The answers never enter the feature directory. This repository archives feature
directories to `specs-trunk` and pushes them, and a repository that commits
`specs/` puts them in the pull request, so a result written there is public by
default. A check of a person's understanding is only answered honestly while its
result is private. The answers go to the branch's state directory, one file per
run, and the feature directory gets a marker naming what was walked through and when.

On an autonomous run the check does not happen, because an agent answering its
own questions proves nothing about the person. The declaration marks the pass
`needs_person`, and wfctl reads it as skipped while `auto_approve` is on, so
`wfctl status` shows the pass as skipped with its reason rather than as done.
Nothing is written, and the pass reads outstanding again once a person is back.

## Boundaries and Ownership

The person owns "who gets to see how well I walked through this work?". wfctl owns
"has this check run against the current plan?", which the marker answers without
exposing any answer. Both are argued in the level-2 record
`plan-walkthrough-is-private`. The repository owns "does this pass need a person?",
and wfctl owns "is this pass skipped right now?", argued in
`autonomous-agent-skips-human-checks`. The branch also carries
`autonomous-run-stop-condition`, which names the three stops an autonomous run
already has; it came out of this design and adds no stop of its own.

| Artifact | Location | Committed | Contents |
|---|---|---|---|
| Answers | `$(wfctl state-dir)/walkthrough/<mode>-<date-time>.md` | never | each challenge, the person's answer, its disposition, and the gaps |
| Marker | `FEATURE_DIR/plan-walkthrough.md` or `FEATURE_DIR/change-walkthrough.md` | as the repository treats `specs/` | the mode, what was walked through (the sha256 of `plan.md`, or the commit), and the date |
| Autonomous skip | none; wfctl reads it from `needs_person` and the approval mode | nothing to commit | the reason "needs a person; auto-approve is on", in `wfctl status` |

A person may lift a gap into the plan, worded as a gap in the plan, such as
"the plan does not say what step 3 does to `plan.md`", and never as a gap in the
person.

## Level-3 decisions

1. The skill lives at `wfctl/agents/skills/plan-walkthrough/` with a `/plan-walkthrough`
   command wrapper. `agents/openai.yaml` is dropped, since a per-vendor manifest
   inside a skill directory is a foreign shape under `layer-model`.
2. Answers are written one file per run, so repeated runs show how a person's
   understanding changed over time.
3. The marker carries no answers and no counts. The pass reader stays
   "file exists", so a plan changed after its walkthrough still reads `done`. The
   general fix for stale evidence is the separate issue #501 names, and building
   it here would decide that fix as a side effect.
4. The skill interviews only when a person invoked it. Under `auto_approve`,
   orchestrate reaches `/plan-walkthrough` only when the declaration lacks
   `needs_person`; the skill then asks nothing, writes nothing, and says the
   declaration needs that field. The skip itself is wfctl's, decided at level 2
   in `autonomous-agent-skips-human-checks`, which replaced the step claim this
   decision first chose.
5. Lenses 2 (rationale), 3 (assumptions), 4 (boundaries), and 7 (evidence) stop
   re-deciding what the records, `Considered`, the checked and assumed split, and
   verification already decided, and ask the person to explain it instead. Lens
   11 (comprehension) leads. Lenses 1, 5, 6, 8, 9, and 10 are unchanged.

## Key Assumptions to Validate

- [ ] A person answers more honestly when the result is private. Tested by
      running the check on this repository's own next change and comparing the
      answers with what the person would write in a pull request.
- [ ] A repository declares the pass with `/plan-walkthrough` as its command, so the
      skill can find its own qualified name in `wfctl status --json`. Tested by
      declaring it in this repository and running both modes.
- [ ] The state directory lasts long enough to be useful. It survives sessions
      and is not backed up; tested by whether a person ever goes back to an old
      run.

## MVP Scope

In:

- The skill and its references, moved from `docs/plan-defense/` in the main
  checkout into `wfctl/agents/skills/plan-walkthrough/`, with the artifact contract
  split into the answers file and the marker.
- The `/plan-walkthrough` command wrapper.
- The `needs_person` field on a declared pass: parsed and checked by
  `wfctl check config`, read as `skipped` while `auto_approve` is on and the
  evidence is absent, and carried in the sub-step payload.
- The lens pruning written into `interrogation-lenses.md`.
- The README's `steps` snippet, showing how a repository places the pass.
- This repository's own `wfctl.json` declares plan mode under `plan`, with
  `needs_person`. Change mode waits for #505.
- A line in `vendor-upstream-skills` saying the skill is wfctl's own.

Out: everything under Not Doing.

## Not Doing (and Why)

- A built-in sub-step under `plan` or `implement`. The check blocks nothing and
  belongs where the person wants it, and `steps` already places it.
- A gate on `tasks`, and any bound on revision rounds. A gate measures the plan,
  and this check measures the person.
- An agent answering from evidence when nobody is present. That is a review of
  the plan, which is #501's job.
- A scan file in `docs/architecture/scans/`. A scan records findings about a
  change, and this result is about a person. #501's design expects #500 to amend
  the scans record; it no longer does.
- A per-person override of `wfctl.json`. The declaration is per repository, and a
  per-person switch is new machinery no shared repository has asked for.
- Staleness checking on the marker. That is the general evidence-freshness fix
  in #502.
- Change mode in this repository's `wfctl.json`. Its marker names a
  commit, and code changes after review on almost every branch, so the pass
  would read done on code nobody walked through until #502 makes that visible (#505).

## Open Questions

- How long the private answers should last, and whether they can be kept
  somewhere durable and private.
- Whether `_MIRRORED_SKILLS` needs an entry. The mirror test in that set's own
  comment decides it during implementation.

## Software design decisions

- docs/architecture/design/autonomous-skip-is-a-claim.md — rejected; an autonomous skip written as a step claim, replaced by the level-2 record `autonomous-agent-skips-human-checks`
