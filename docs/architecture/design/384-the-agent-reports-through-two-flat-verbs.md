---
status: proposed
supersedes: 364-the-block-report-is-its-own-verb
---

# The agent reports through two flat verbs, `report-action` and `report-block`, and the old names go

## Context

`wfctl-records-outward-actions-and-never-gates-them` (proposed, level 2) keeps
two facts the agent tells wfctl: that an action was taken, and that the host
refused one. Today they arrive through `wfctl notify` and `wfctl blocked`, whose
shapes were set by the grant.

`364-the-block-report-is-its-own-verb` made `blocked` a separate verb because
`notify`'s grant check stood in front of every other spelling, and later added
`--clear` because `notify`'s release was unreachable from a run holding no grant.
With the grant removed, `notify --declined` means nothing (a decline was
authority the run held and did not use), `--clear` duplicates recording the
action, and "notify" is the proxy word level 2 removes.

## Verified

- `cli.py` `notify_cmd` calls `action_grant` before both of its paths, and
  `blocked_cmd` never calls it.
- `_session.py:657`: `standing_blocks` already treats a later `notify-action` as
  a release (#364 FR-020), so recording the action lifts a hold with no clearing
  verb.
- `_restart.py:313` folds `notify-action` and `notify-declined` into the
  handoff. `notify-declined` has no other reader.
- Skill call sites: `end-session` (`notify push`, `blocked issue-close`),
  `speckit-delivery-plan` (`notify issue-create --declined`,
  `blocked issue-create`), `speckit.analyze.md` (`blocked issue-create`), and the
  `allowed-tools` lines of `end-session.md` and `speckit.decompose.md`.
- `README.md:19` and `docs/reference.md:602-629` document both verbs.

## Assumed

- **A repo that upgrades wfctl refreshes its installed skills before calling a
  removed verb.** `/start-session` runs `doctor`, which reports the drift, and
  then `install-skills`. Falsified by a repo that upgrades the tool and runs a
  skill without starting a session: the skill's `wfctl notify` fails with `No
  such command`, loudly and without side effects.

## Direct baseline

Keep both names. Strip `action_grant` and `--declined` from `notify`, and leave
`blocked`, with its `--clear`, as it is. The smallest diff to the CLI, and no
skill has to change a verb.

## Decision

Two top-level commands, and nothing else records either fact:

```
wfctl report-action <action>                  → event notify-action
wfctl report-block  <action> --reason "…"     → event blocked; holds the step
```

`notify`, `blocked`, `--declined` and `--clear` are removed with no aliases. The
stored event names do not change. `standing_blocks` still reads `block-cleared`,
which is no longer written, so a block cleared in an old log stays cleared rather
than coming back to hold a step.

## Diagram

```
          baseline                                   decision

agent     notify <a>  notify --declined               report-action <a>   report-block <a>
          blocked <a> --reason   blocked --clear              │                  │
            │            │          │       │                 │                  │
════ wfctl CLI (published) ═══════════════════════════════════╪══════════════════╪═══
            │            │          │       │                 │                  │
wfctl       ▼            ▼          ▼       ▼                 ▼                  ▼
         action     declined     blocked  cleared          action             blocked
            └───────── one per-action timeline ───┘           └── one per-action timeline ──┘
```

The graphs differ in how many ways each fact can arrive. The baseline keeps four
spellings for three facts: "taken" and "cleared" both say the action now
happened, and "declined" is a fact about a grant that no longer exists. The
decision has one spelling per fact, and the success spelling is also the release.

## Considered

- **The baseline: keep `notify` and `blocked`, strip the grant.** It loses on
  vocabulary and on duplication. The verb would still be named for notifications
  the maintainer does not want, and `--clear` would stay as a second way to say
  what `notify <a>` already says.
- **A group, `wfctl report action | block`.** Equally sound, and it reads the
  same aloud. It loses on fit: a group with two members adds a level to `--help`
  that an agent has to open before it finds either one, and the shared prefix
  already puts both next to each other at the top level. The maintainer chose
  the flat pair.
- **Hidden aliases for `notify` and `blocked`.** They would keep skills installed
  from an older wheel working until the next `install-skills`. Rejected because
  the `notify` alias would silently change meaning from gated to ungated, and
  `doctor` at the next `/start-session` already closes that window.
- **Rename the events as well (`action`, `action-blocked`).** It would line the
  log up with the verbs. It breaks `_restart`'s reader and every existing log, to
  rename storage that no person types.

## Consequences

Every skill call site and both docs change in the same commit as the CLI. Tests
that assert `notify` refuses without a grant are deleted rather than inverted,
because the property they pinned no longer exists. `_restart`'s late-event fold
drops `notify-declined`.

The agent can now lift its own hold with `report-action`. That is no weaker than
before — `blocked --clear` was equally typable — and level 2 states the ceiling.

## Verification

- `wfctl --help` lists `report-action` and `report-block`, and lists neither
  `notify` nor `blocked`.
- A test: `report-block push --reason x` holds the current step, and a later
  `report-action push` releases it.
- A test: a log holding `blocked` followed by `block-cleared` for the same action
  reads as no standing block.
- `grep -rnE "wfctl (notify|blocked)" wfctl docs README.md AGENTS.md` returns
  only superseded records.

## Log

- 2026-09-15  proposed  — #384 level 3; the grant that shaped `notify` and
  `blocked` is removed, and the maintainer chose the `report-` pair
