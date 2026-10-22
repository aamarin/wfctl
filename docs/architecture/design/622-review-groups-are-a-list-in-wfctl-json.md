---
status: proposed
---

# A repository declares its review groups as a list under `review` in `wfctl.json`

## Context

The accepted record on review coverage has wfctl write a run record listing the
expected reviewers for each group, and lets a repository declare its own groups
in `wfctl.json`. wfctl ships two groups, security and code, and they always run
first. A repository can change their reviewers but can't remove them.

A reviewer is a model and a count. Claude runs inside the current agent. Any
other model, such as Codex, runs as its own process, so wfctl needs the command
that starts it. The count is exact: wfctl expects that many reports and marks
the run incomplete with fewer.

The declaration lives in `wfctl.json` for the same reason `change_check` and
`steps` do. The `.agents/` folder is gitignored and rewritten by
`install-skills`, so a policy written there vanishes with no error.

## Verified

- `_declared.py` reads `steps` as an object keyed by pipeline step, and rejects
  a key that isn't in `_STEP_NAMES`: "'{key}' is not a pipeline step". The keys
  there are a closed set that wfctl defines.
- `_change.py` reads `change_check` as a list.
- `_paths.trunk_branch` already reads a `trunk` key from `wfctl.json`, so the
  review check can find the trunk branch without a new key.

## Assumed

- No group needs a setting per reviewer beyond a model and a count. A per-reviewer
  skill or prompt would falsify this, and the reviewer objects have room for a
  new field.

## Direct baseline

Key everything by name in plain objects. A top-level `models` object maps each
model to its command, and each group is a key under `review` whose value maps a
model to a count:

```json
"review": {
  "models": { "codex": "codex exec --sandbox read-only" },
  "security": { "claude": 2, "codex": 2 },
  "code": { "claude": 2, "codex": 2 }
}
```

## Decision

`review` holds two keys. `commands` maps each model other than Claude to the
command that starts it. `groups` is a list of objects. Each one names its group
with `group`, may name a review skill with `skill`, and lists its `reviewers` as
objects carrying `name` and `count`:

```json
"review": {
  "commands": { "codex": "codex exec --sandbox read-only" },
  "groups": [
    { "group": "security",
      "reviewers": [ { "name": "claude", "count": 2 }, { "name": "codex", "count": 2 } ] },
    { "group": "code",
      "reviewers": [ { "name": "claude", "count": 2 }, { "name": "codex", "count": 2 } ] },
    { "group": "money-rules", "skill": "money-rules-review",
      "reviewers": [ { "name": "claude", "count": 2 } ] }
  ]
}
```

`money-rules` is an example of a group a project adds. wfctl doesn't ship it.

Security and code run first whether or not the list names them, and a group the
list doesn't name gets 3 Claude reviewers. The other groups run in the order the
list gives. Reviewer ids are the group's first letter plus a number, such as
`s1`, `c1`, and `m1`. The `wfctl check config` command flags two groups that
share a first letter, a reviewer whose model has no command, and a count below
one.

## Diagram

```
             baseline                                decision

          ┌──────────────────────────┐            ┌──────────────────────────┐
          │ wfctl.json review        │            │ wfctl.json review        │
          │  models, <group>: {m: n} │            │  commands, groups[]      │
          └──────▲────────▲──────────┘            └──────▲────────▲──────────┘
                 │        │ reads models                 │        │ reads groups[]
═══ wfctl.json is the repository's ══════════════════════╪════════╪══════════
                 │        │ and every other key          │        │
reads models     │   ┌────┴─────────┐     reads commands │   ┌────┴─────────┐
          ┌──────┴─┐ │ run record   │             ┌──────┴─┐ │ run record   │
          │launcher│ │ writer       │             │launcher│ │ writer       │
          └────────┘ └──────────────┘             └────────┘ └──────────────┘
```

The divider is the existing rule that a repository's own policy lives in
`wfctl.json`. Both graphs have the same two readers and the same two arrows. They
differ in what each arrow reads. In the baseline the run record writer has to
read `models` to tell a group key from the model key, and treat every other key
under `review` as a group, so adding any setting under `review` later changes
what counts as a group. In the decision each reader has one key, and a new
setting under `review` touches neither arrow.

## Considered

- Key everything by name, as the direct baseline describes. We didn't choose it
  for three reasons Andre gave while revising the shape.
  1. A top-level `models` key was confusing, because it meant both the commands
     and each group's reviewer list. `commands` says what it holds.
  2. Groups keyed by name sit beside `models` as siblings, so every key under
     `review` other than one is a group. A list keeps groups apart from settings.
  3. The groups run in order after security and code, and JSON doesn't promise
     the order of an object's keys. A list does.
- Name a group with `name`, like each reviewer. Andre changed it to `group`, so
  that `name` means only the reviewer.
- Write the count as `max-inst`. We didn't choose this because the number is
  exact rather than a ceiling. A run with fewer reports is incomplete.
- Key groups by name the way `steps` keys passes by step. That works for `steps`
  because the keys there are a closed set of pipeline steps wfctl defines.
  Review groups are an open set that each repository names.

## Consequences

- A repository adds a group by appending to a list, and changes the reviewers of
  security or code by listing that group.
- A repository with no `review` key gets today's panel plus the security group,
  with 3 Claude reviewers each, and the report doesn't mention other models.
- A model the list names that can't run is a warning, not a failure. The review
  continues, `wfctl check config` flags the missing command, and the roster marks
  those reviewers `✗` with one `⚠` line saying why.

## Verification

- `wfctl check config` tests cover each finding: two groups sharing a first
  letter, a reviewer with no command, a count below one, and a `groups` value
  that isn't a list.
- A test with no `review` key asserts that the run record lists `s1`, `s2`,
  `s3`, `c1`, `c2`, and `c3`, all Claude.
- A test with a custom group listed before `code` asserts that security and
  code still run first.

## Log

- 2026-10-21  proposed  — #622 level 3, after three revisions of the shape by
  Andre in the brainstorm.
