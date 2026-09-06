---
status: proposed
---

# A mirrored skill's wrapper is suppressed from the mirroring layer, not from the bundle

## Context

A command wrapper is a five-line file whose body is "read
`.agents/skills/<name>/SKILL.md`". It exists because an agent cannot natively
discover a skill that lives only in `.agents/skills/` — the wrapper is the route
in.

`_MIRRORED_SKILLS` builds a second route for Claude: a named skill is copied to
`.claude/skills/<name>`, where it is discovered without being told. Eleven skills
are mirrored, and eight of them also shipped a wrapper under the same name.

That is one `/name` claiming two files. Claude Code's documentation says the
skill wins; a session on 2026-09-04 got the wrapper instead, whose
`disable-model-invocation: true` refused the Skill tool for the very skill the
wrapper points at, while a second session the same day on the same machine
resolved `worktree-handoff` to the skill and ran it (#170). A gate that holds
intermittently reads as a forgetful agent rather than as packaging.

The flag was not the mistake. It is on the wrapper so the model reaches the
skill rather than a file that only points at one — a correct intent whose
consequence is that the pointer, when it wins, refuses its own target.

Suppressing the wrapper costs no typed route only because a Claude Code skill is
itself typeable as `/name`, which is true from v2.1.101 and was checked against
the docs rather than recalled. On an older Claude Code the seven names would
become model-only. wfctl declares no floor and this record does not add one —
the observation is here so a reader who finds one knows what it would break.

## Decision

A skill named in `_MIRRORED_SKILLS` has its wrapper suppressed from the command
directory of the layer that mirrors it. The wrapper still ships, and every other
layer still installs it.

Per layer, never from the bundle. The redundancy is a property of one layer
having both files, not a property of the wrapper.

## Owns truth

`install-skills` owns "which files does this layer install?", and therefore
"does this layer have two files claiming one `/name`?". A file cannot own it: a
wrapper's frontmatter describes the wrapper, and the collision is a fact about a
directory that neither of the two colliding files can see.

`_MIRRORED_SKILLS` does **not** own "may the model invoke this skill
unprompted." That stays where `59-deployment-key-metadata`'s contract put it —
the skill's own frontmatter — and membership does not override it. `i-have-adhd`
is mirrored and still declines model invocation, because upstream's file says so.
Membership decides reachability; the file decides invocability.

## Considered

- **Delete the seven wrappers from the bundle.** The shortest diff, and wrong at
  a layer its argument never mentioned. `_AGENT_TARGETS` gives bob
  `.bob/commands/`, where `_copy_command_for_bob` strips the Claude-only key, and
  gives it no mirror to compensate. For `i-have-adhd` the wrapper is bob's only
  working route: the skills copy is a `copytree` that never reaches the strip, so
  `.bob/skills/i-have-adhd/SKILL.md` keeps `disable-model-invocation`, which this
  repo already records as making Bob Shell skip model invocation entirely — the
  body never executes. Three independent reviewers found this; the suite did not.
- **Drop `disable-model-invocation` from the seven wrappers.** Two files still
  claim one `/name`, so which `description` a reader sees stays a coin flip. It
  also cannot reach `i-have-adhd`, whose flag is upstream's and sits in the
  vendored skill: the one case that cannot be edited is the one it cannot fix.
- **Rename the wrapper**, as `wfctl` → `using-wfctl` already does. Sound, and it
  loses on cost rather than fault: a second name for one workflow, on a file
  whose whole content is "go read the sibling you already have", and #149 was
  unblocked by a human typing the current name.

## Consequences

- Adding a name to `_MIRRORED_SKILLS` changes what the mirroring layer installs,
  and that change is invisible to `doctor`: its staleness check hashes the
  bundle, which a suppression rule does not touch. A repo installed before the
  rule keeps its colliding file and reports `skills current`, so the repair runs
  only when someone reinstalls for another reason. Measured, not inferred.
- A suppressed wrapper must carry nothing its skill does not. Suppression drops
  the whole file, so a key like the `allowed-tools` on `end-session.md` would
  be revoked on the mirroring layer alone by the act of mirroring its skill.
  The remedy is to move the key onto the SKILL.md, which is where #204 put
  `start-session`'s — and moving it widens the key rather than relocating it,
  because a mirrored skill is reachable by the model and a wrapper is not.
  For `start-session` that hands a model-initiated invocation the
  `Bash(wfctl install-skills*)` pre-approval a human used to have to ask for.
  Sanctioned rather than incidental: AGENTS.md § Safety already decided that
  `/start-session` refreshes a stale mirror unattended, and the overwritten
  originals are backed up. It is a consequence to state, not a cost to hide.
- `conversation-response-shape` becomes reachable by the model on the Claude
  layer, which its own frontmatter comment has argued for since #99 and the
  colliding wrapper was intermittently denying.
- The wrappers' second line — "confirm activation in one line" — is unchanged,
  because the wrappers are unchanged. Only their destination narrowed.

## Log

- 2026-09-04  proposed    — #170; the wrapper's flag refused the skill it points at, for whichever session lost the tie
- 2026-09-06  amended     — #204; `start-session` mirrored, the eighth wrapper suppressed. First time the `allowed-tools` consequence above was paid rather than predicted.
