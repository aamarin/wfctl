---
status: proposed
---

# The tracker flattens its own shapes; wfctl compares scalars

## Context

`wfctl change check` compares the fields set on an open change against the
fields set on the branch's issue. Both arrive from the backend, through a
`fields` verb the tracker config declares.

What varies is the shape the backend hands back. `the-repo-names-the-fields-a-
change-must-carry` puts every field name outside wfctl; it says nothing about
the *structure* those values arrive in, and a comparison written against a
nested one would need to know which key inside each element identifies it. That
is the same vocabulary arriving through a door the level-2 record left open.

## Verified

- `gh pr view 301 --json labels,assignees,milestone,projectItems,reviewRequests`
  returns `"labels":[{"id":"LA_kwDOTX0a188AAAACrnFbzg","name":"enhancement",
  "description":"New feature or request","color":"a2eeef"}]` — a list of objects,
  not of strings.
- `gh issue view 280 --json labels,assignees,milestone,projectItems` returns the
  same key names with the same object shapes, so both sides of the comparison
  have the problem.
- Unset reads as `"milestone":null` and `"projectItems":[]`, never as a missing
  key.
- `wfctl/_tracker.py:365` — `read_issue_labels` takes "one label per line of
  stdout, because the verb is declared to produce that and not because any
  backend's default output happens to look that way", and its docstring records
  what the alternative cost: an earlier version read `gh`'s own output and "read
  every other backend as having no labels, silently".
- `wfctl/_tracker.py:42` — `ALLOWED_CHANGES = {"list": set(), "view": {"id"}}`,
  so `fields` is a new key in both verb tables rather than a reshaping of one.

## Assumed

- `gh`'s `--jq` is present in whatever `gh` a consumer runs. Falsified by a build
  without it; the mitigation is already in the contract, since a tracker whose
  flattening needs more than one argv writes a script, which the `create` verb in
  this repo's own config already does.
- One argv can express a backend's flattening. Falsified by a backend needing two
  calls to assemble its fields — same mitigation.

## Direct baseline

wfctl unwraps. For each value the `fields` verb returns, if it is a list of
objects, pull an identifying key out of each element by trying a fixed sequence —
`name`, then `login`, then `title`, then `id`. Roughly ten lines in the
comparison, no contract change, and correct against GitHub today.

## Decision

The `fields` verb is contracted to return a flat JSON object whose values are
scalars or arrays of scalars. Unwrapping is the tracker config's job, expressed
in whatever the backend's own client already provides — `--jq` for `gh`. wfctl
reads the payload as strings and never descends into it.

## Diagram

```
              baseline                          decision

stable   ┌────────────────────┐            ┌────────────────────┐
         │   change check     │            │   change check     │
         │  unwraps: name ??  │            │  compares scalars  │
         │  login ?? title    │            │                    │
         └────────────────────┘            └────────────────────┘
                    ▲ reads                           ▲ reads
═══ wfctl decides │ the tracker supplies ═════════════╪═══════════════
                    │                                  │
volatile ┌────────────────────┐            ┌────────────────────┐
         │  tracker config    │            │  tracker config    │
         │  fields → objects  │            │  fields --jq       │
         └────────────────────┘            │  → scalars         │
                                           └────────────────────┘
```

The two graphs differ by which side of the divider the unwrapping sits on.
Nothing else moves — the same two components, the same single `reads` arrow,
the boundary already in force from the level-2 record.

## Considered

- **wfctl guesses an identifying key** — the direct baseline, and the fewest
  lines by a wide margin. Loses because the guess list *is* GitHub's vocabulary
  under another name: a backend whose label elements key on `slug` reads as
  having no labels, with no error, which is precisely the failure
  `read_issue_labels` was written to stop repeating.
- **`fields` returns one `key=value` line per field, matching the `labels` verb
  beside it** — sound, and the more consistent of the two with what already
  ships. Loses on the multi-value case: two labels need either a repeated key or
  an in-band separator, and a label containing that separator is a bug nobody
  finds until it bites.
- **wfctl declares a per-key identity mapping in `wfctl.json`** — keeps the
  vocabulary out of wfctl, so it satisfies the level-2 record just as well.
  Loses on ergonomics and on duplication: every consumer would write a mapping
  that `--jq` already expresses, leaving two half-descriptions of one shape in
  two files that can disagree.

## Consequences

Gained: the comparison is a set operation over strings, and wfctl parses no
nested structure on any path.

Harder: a tracker config line now carries logic as well as argv, and it is
longer. `tracker-check` can validate that the verb is a list of strings; it can
never validate that the flattening is correct, so a wrong `--jq` is found by
running the check rather than by validating the config.

Failure mode this introduces: a config whose flattening still yields objects.
wfctl then holds a dict where it expected a scalar. That must surface as a
finding naming the config, not as a traceback out of a comparison.

## Verification

- A test feeding `fields` output that contains a nested object, asserting a
  config finding rather than an exception.
- A test that a flat payload compares as a set difference, with the issue's
  values as the expected side.
- `uv run wfctl change check` against a real open PR with a real empty sidebar,
  then again with it filled — the second half is what shows the check can pass.

## Log

- 2026-09-09  proposed  — level-3 gate of the #302 design pass; the shape the
  backend returns was the one claim in the design that turned out to be wrong
  when checked.
