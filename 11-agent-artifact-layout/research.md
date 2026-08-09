# Research: Agent Artifact Layout

**Branch**: `11-agent-artifact-layout` | **Date**: 2026-08-05

Three unknowns carried out of specification. All resolved against source; none
required a spike.

---

## R1 — Can the health check report component version skew? (FR-014)

**Decision**: Yes, and it already does — for both directions. FR-014 needs a
targeted addition, not a new mechanism.

**Rationale**: `wfctl doctor` runs two independent freshness checks today.

| Direction | Existing check | Output |
| --- | --- | --- |
| Tool behind skills | `_check_wfctl_version` (`cli.py:1223`) compares the installed version against remote semver tags | `⬆ wfctl 0.13.0 → 0.14.0 available` + `upgrade: uv tool install --upgrade …` |
| Skills behind tool | `doctor_cmd` (`cli.py:1366-1400`) compares the manifest's pinned commit against the remote ref tip | `⬆ <agent>: skills behind — abc1234 → def5678` + `update: wfctl install-skills` |

Both already name the corrective action. What neither does is connect a stale
component to *this* incompatibility — a user sees "skills behind" without
learning that their pipeline is stalled at brainstorm because of it.

The cheapest signal is positive evidence rather than version arithmetic: **the
presence of a `.agent/` directory in a repo is proof that a component still
writing the old path is installed.** It requires no capability-version
negotiation, no manifest schema change, and it self-clears — once every
component is current, no `.agent/` is ever created and the check goes quiet
permanently.

**Alternatives considered**:

- *Declare a minimum tool version in the skills manifest*, mirroring upstream
  spec-kit's `requires.speckit_version`. Correct and general, but it adds a
  manifest field, a comparison path, and a contract to maintain, to detect one
  transitional condition. Deferred — if a second incompatibility ever appears,
  this is the mechanism to reach for.
- *Dual-path reading.* Rejected during clarification: it is compatibility code in
  two modules with a deletion nobody is holding.
- *Do nothing.* Rejected: the stall is silent, and the spec's SC-007 requires the
  mismatch be reported rather than inferred.

---

## R2 — Does the checkpoint file have readers?

**Decision**: No automated reader. It is a write-only handoff signal to a human.

**Rationale**: `agent-brief/SKILL.md` is the only file that mentions it, and all
four mentions are writes or instructions to write (`:36`, `:46`, `:60`, `:61`).
Nothing parses it, nothing lists it, and it is absent from wfctl's archive map.

**Consequence for the move**: the least constrained of the three files. Nothing
breaks from relocating it; only the instruction text changes.

---

## R3 — "Checkpoint" already means something else in the tooling

**Decision**: Rename `agent-brief`'s file to `escalation.md`. Do not carry the
name `checkpoint.md` into the shared directory.

**Rationale**: `wfctl checkpoint` is an existing subcommand (`cli.py:207`) that
writes `checkpoint-<n>.md` and `checkpoint-<n>.patch` into the session state dir
(`_session.py:122-146`) — a numbered git-diff snapshot taken before a risky
change, so it can be unwound. `agent-brief`'s `checkpoint.md` is unrelated: a
one-shot escalation record written when an agent hits a hard stop and needs a
human.

Two different concepts, one word. Today they are separated by living in
different directories, which is precisely the accident this feature removes —
after the move, a reader sees `checkpoint.md` beside artifacts that the tooling's
own `checkpoint` command has nothing to do with.

`escalation.md` describes what the file actually records and collides with
nothing. The rename costs the same edit the move already required.

**Alternatives considered**:

- *Keep `checkpoint.md`.* Free, but consolidating two meanings into one directory
  is a worse end state than the split this feature exists to fix.
- *Rename the wfctl subcommand instead.* Larger blast radius — it is a public CLI
  verb with an event type (`cli.py:241`) and user muscle memory, and it is the
  older claim on the word.
- *Namespace it, e.g. `brief-checkpoint.md`.* Preserves the confusing word for no
  benefit.

**Scope note**: this is a rename inside the file set this feature already moves,
not new scope. It touches the same lines.

---

## Findings that change earlier assumptions

1. **FR-014 shrinks.** Both skew directions are already reported. The work is one
   targeted check, not a version-negotiation mechanism.
2. **A fourth file is renamed, not just moved.** `checkpoint.md` →
   `escalation.md`, per R3. The specification's Key Entities names the entity
   "Checkpoint"; the plan uses "Escalation record" and the spec should follow.
