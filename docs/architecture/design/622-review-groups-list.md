---
status: proposed
---

# A repository lists its review groups under `review` in `wfctl.json`

## Context

The accepted record on review coverage has wfctl write a run record that lists
the expected reviewers for each group. It also lets a repository declare its own
groups in `wfctl.json`. wfctl ships two groups, security and code, and they
always run first. A repository can change their reviewers but can't remove
them.

Each reviewer is a model and a count. Claude runs inside the current agent. Any
other model, such as Codex, runs as its own process, so wfctl needs the command
that starts it. The count is exact. wfctl expects that many reports and marks
the run incomplete if fewer arrive.

The declaration lives in `wfctl.json` for the same reason `change_check` and
`steps` do. The `.agents/` folder is gitignored and rewritten by
`install-skills`, so a policy written there disappears with no error.

## Verified

- `_declared.py` reads `steps` as an object keyed by pipeline step, and rejects
  a key that isn't in `_STEP_NAMES`: "'{key}' is not a pipeline step". wfctl
  defines every key there.
- `_change.py` reads `change_check` as a list.
- `_paths.trunk_branch` already reads a `trunk` key from `wfctl.json`, so the
  review check can find the trunk branch without a new key.

## Assumed

- No group needs a setting for each reviewer beyond a model and a count. A
  reviewer that needs its own skill or prompt would break this assumption, and
  the reviewer objects have room for a new field.

## Direct baseline

The simplest shape keys everything by name in plain objects. A top-level
`models` object maps each model to its command. Each group is a key under
`review`, and its value maps a model to a count:

```json
"review": {
  "models": { "codex": "codex exec --sandbox read-only" },
  "security": { "claude": 2, "codex": 2 },
  "code": { "claude": 2, "codex": 2 }
}
```

## Decision

`review` holds two keys:

1. `commands` maps each model other than Claude to the command that starts it.
2. `groups` is a list of objects. Each one names its group with `group`, can
   name a review skill with `skill`, and lists its `reviewers` as objects with a
   `name` and a `count`.

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

`money-rules` is an example of a group a project might add. wfctl doesn't ship
it.

Security and code run first whether or not the list names them. If the list
doesn't name one of them, it gets 3 Claude reviewers. The other groups run in
the order the list gives. Each reviewer id is the group's first letter plus a
number, such as `s1`, `c1`, and `m1`.

The `wfctl check config` command reports these problems:

1. Two groups that start with the same letter.
2. A group name that isn't lowercase letters, digits, and hyphens, starting
   with a letter.
3. A group whose `reviewers` list is empty, built-in or custom, and a custom
   group with no `reviewers` key. A built-in group gets its default only when
   the key is missing.
4. A reviewer whose model has no command.
5. A count below 1.

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

The line marks the existing rule that a repository's own policy lives in
`wfctl.json`. Both graphs have the same two readers and the same two arrows, and
they differ in what each reader reads. In the baseline, the run record writer
has to read `models` to skip it, and then treat every other key under `review`
as a group. So any setting added under `review` later would be read as a group.
In the decision, each reader reads one key, and a new setting under `review`
changes neither reader.

## Considered

- Key everything by name, as the direct baseline describes. We didn't choose
  this, for three reasons Andre gave while revising the shape:
  1. A top-level `models` key was confusing, because it meant both the commands
     and each group's reviewer list. `commands` says what it holds.
  2. When groups are keys under `review`, every key except `models` is a group.
     A list keeps the groups apart from the settings.
  3. The groups run in order after security and code, and JSON doesn't
     guarantee the order of an object's keys. A list does.
- Name a group with `name`, like each reviewer. Andre changed it to `group`, so
  that `name` means only the reviewer.
- Call the count `max-inst`. We didn't choose this because the number is exact,
  not a maximum. A run with fewer reports is incomplete.
- Key the groups by name, the way `steps` keys passes by step. That works for
  `steps` because wfctl defines every pipeline step. Each repository names its
  own review groups, so wfctl can't check the keys the same way.

## Consequences

- A repository adds a group by adding an entry to the list. It changes the
  reviewers for security or code by listing that group.
- A repository with no `review` key gets today's panel plus the security group,
  with 3 Claude reviewers each, and the report doesn't mention other models.
- If a listed model can't run, wfctl warns and the other reviewers carry on.
  `wfctl check config` reports a missing command entry, and the roster marks
  those reviewers `✗` with one `⚠` line saying why. A run in which no reviewer
  can run stays incomplete, so a group never completes with no review at all.

## Verification

- `wfctl check config` tests cover each problem it reports, plus a `groups`
  value that isn't a list.
- A test with no `review` key checks that the run record lists `s1`, `s2`,
  `s3`, `c1`, `c2`, and `c3`, all Claude.
- A test with a custom group listed before `code` checks that security and code
  still run first.

## Log

- 2026-10-21  proposed  — #622 level 3, after Andre revised the shape three times
  in the brainstorm.
- 2026-10-23  proposed  — #622 plan review. The `check config` list and the
  unavailable-model consequence now match the spec: a bad group name, an empty
  `reviewers` list on any group, and a run with no available reviewer staying
  incomplete. Andre approved folding in the second review's findings.
