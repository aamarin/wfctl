---
status: accepted
governs: install-and-drift
---

# The brainstorm step is listed once, as its command

## Context

Every skill and model-invocable command the Claude layer installs adds a line to
the listing that every session loads. The brainstorm step currently has three
lines in that listing:

1. The `brainstorm` skill, a pre-speckit dialogue that nothing in `wfctl/` names.
2. The `speckit-brainstorm` skill, mirrored to `.claude/skills/` by
   `_MIRRORED_SKILLS` in `cli.py`.
3. The `/speckit.brainstorm` command, which `wfctl status` prints as the next
   step and whose body says to read `speckit-brainstorm`'s `SKILL.md`.

The `brainstorm` skill can be dropped outright, since nothing points at it.
Choosing between the other two takes a structural decision, because the mirror
and the command were each added to solve a real failure.

The mirror was added in #361. At that time every pipeline-step wrapper carried
`disable-model-invocation: true`. An agent that read `/speckit.brainstorm` from
`wfctl status --json` found nothing it could invoke, so the mirror gave it a
skill to call. Then #473 removed that flag from the eight step wrappers, so the
wrappers became model-invocable. Since #473, Claude reaches every other step
through its dotted command alone, and none of their skills is mirrored. The
brainstorm mirror is the one left over.

`mirror-supersedes-the-wrapper` (proposed) covers a mirror and a wrapper that
share one name. These two names differ by a dot, so that record doesn't apply.

## Verified

- `wfctl/agents/commands/speckit.brainstorm.md` has no
  `disable-model-invocation` key, and its `allowed-tools` matches the
  `speckit-brainstorm` skill's list exactly.
- `wfctl/_pipeline.py` `_STEPS["brainstorm"].command` is `/speckit.brainstorm`.
- `docs/architecture/mirror-supersedes-the-wrapper.md` Log, 2026-09-24: "the
  eight pipeline-step wrappers dropped `disable-model-invocation`".
- `_MIRRORED_SKILLS` holds no other `speckit-<step>` skill except
  `speckit-orchestrate`, and the `speckit.orchestrate` wrapper carries
  `disable-model-invocation: true`, so that step is listed once.
- In the #698 session on 2026-11-03, `Skill("speckit.brainstorm")` loaded the
  wrapper, and the wrapper sent the agent to the skill by path.
- Outside its own folder, `speckit-brainstorm` is named in prose by
  `speckit.clarify.md` and `design-levels`. Neither one tells an agent to invoke
  it as a skill.

## Assumed

- Claude Code keeps listing a command with no `disable-model-invocation` and
  lets the Skill tool load it. If a release stops doing that, every pipeline
  step loses its model route at once, not just brainstorm, and the fix belongs
  to all eight wrappers.
- No agent was trained by habit on `Skill(speckit-brainstorm)`. If one calls it,
  the call fails, and `wfctl status` still prints `/speckit.brainstorm`. A
  session that stops on that is the evidence that would reopen this record.

## Direct baseline

Leave both entries. `speckit-brainstorm` stays in `_MIRRORED_SKILLS`, and
`/speckit.brainstorm` stays model-invocable. The listing carries the step twice,
and both lines lead to the same `SKILL.md`.

## Decision

The `/speckit.brainstorm` command is the brainstorm step's only listing entry.
`speckit-brainstorm` leaves `_MIRRORED_SKILLS`. The skill still ships under
`.agents/skills/`, where the command reads it by path, the same way every other
step reads its skill. The command's `description` takes over the trigger wording
the two dropped skills carried, so an agent starting a feature that needs
design thinking still finds the step.

## Diagram

The change this is built to absorb is a new pipeline step. In the baseline, a
step can get two listing lines, depending on whether its skill was mirrored. In
the decision, every step gets one line, its command.

```
          baseline                              decision

                 ┌──────────────────────┐            ┌──────────────────────┐
                 │ SKILL.md under       │            │ SKILL.md under       │
                 │ .agents/skills/      │            │ .agents/skills/      │
                 └──────────────────────┘            └──────────────────────┘
                   ▲ copies          ▲ reads by path           ▲ reads by path
                   │                 │                         │
════ listing ══════╪═════════════════╪═════════════════════════╪══════════════
                   │                 │                         │
  ┌────────────────┴───┐ ┌───────────┴─────────┐   ┌───────────┴─────────┐
  │ .claude/skills/    │ │ /speckit.brainstorm │   │ /speckit.brainstorm │
  │ speckit-brainstorm │ │ (command)           │   │ (command)           │
  └────────────────────┘ └─────────────────────┘   └─────────────────────┘
```

The divider is the listing a session loads, which is already in force: whatever
sits below it costs every session a line. The baseline puts two components
below the divider and the decision puts one, so the decision removes one
`copies` arrow and one listed component. Adding a step touches one arrow in the
decision and up to two in the baseline.

## Considered

- Add `disable-model-invocation: true` back to `/speckit.brainstorm` and keep
  the mirror. We didn't choose this because `wfctl status` prints the command,
  and an agent that invokes what `status` printed is refused. That is #361's
  failure, which #473 fixed for every step.
- Keep both entries, the baseline. We didn't choose this because the second line
  costs every session tokens and buys no route the command doesn't already
  give.
- Rename the skill so the mirror and the command share one name, then let
  `_mirror_supersedes_wrapper` drop the wrapper. We didn't choose this because
  the skill would then own the step's route, the wrapper's `handoffs` key
  would stop being read, and it reopens the same-name tie #170 was filed about.

## Consequences

The listing loses one line in every project that installs the Claude layer.
Brainstorm reads like every other step: the command is listed, and the skill is
a file it points at.

The failure mode is an agent that calls `Skill(speckit-brainstorm)` by name.
That call now fails. The test that pinned the mirror is replaced by one that
pins the command as model-invocable, since that's now the only route.

## Verification

- `tests/test_skill_cross_references.py` asserts that
  `/speckit.brainstorm` carries no `disable-model-invocation` and that
  `speckit-brainstorm` is not in `_MIRRORED_SKILLS`.
- After `uv run wfctl install-skills --agent claude --prune`,
  `.claude/skills/` has no `speckit-brainstorm` and `.claude/commands/` has
  `speckit.brainstorm.md`.
- `claude -p hi` in a clone with the change installed lists the brainstorm step
  once.

## Log

- 2026-11-03  proposed  — #698, which drops what sessions never load from the
  listing
- 2026-11-03  accepted  — Andre, in the #698 implement session on 2026-11-03 —
  https://claude.ai/code/session_01KazJLvL514SyXQabSb8nw6
