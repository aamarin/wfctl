---
status: accepted
---

# The source tree is `wfctl/agents/`; the dotted trees are install output

## Context

wfctl installs its own skills into the repository that develops it. The result
is that `.agents/skills/start-session/SKILL.md` and
`wfctl/agents/skills/start-session/SKILL.md` hold the same bytes, and only the
second one ships.

Editing the first is a silent failure. It reads correctly, the suite passes, and
the change reaches nothing — `.agents/` is gitignored install output, recreated
by the next `install-skills` and destroyed with the worktree.

## Decision

Source is committed package data under `wfctl/agents/` and `wfctl/specify/`.
Every dotted directory at the repo root is generated, gitignored, and never
edited by hand.

| Path | Owner | Committed |
| --- | --- | --- |
| `wfctl/agents/`, `wfctl/specify/` | source — package data, edit here | yes |
| `.agents/` | base layer, installed output | no |
| `.claude/`, `.bob/`, `.github/skills/` | one agent's native layer, additive | no |
| `.specify/` | speckit runtime, installed output | no |

The source trees carry no leading dot because `.gitignore` ignores `.agents/`
and `.specify/` unanchored — a dotted source tree would match at any depth and
be silently untracked.

Only skills the installer names in `_MIRRORED_SKILLS` are mirrored into
`.claude/skills/`. Everything else reaches the agent as a slash command only —
reachable, but only when the reader types it.

Mirroring is therefore opt-in per skill and declared outside the skill files,
which is what lets a derived skill opt in: which layer a file lands in is a fact
about this project's install and not about the file, so it belongs to the
installer even for a file the project wrote every line of. The one fact that
does go inside a derived file is where it came from, and
`vendor-upstream-skills` puts it there and nowhere else.

## Owns truth

`wfctl/agents/` owns skill content. `install-skills` owns what lands in each
layer, recorded in `.wf-skills-manifest.json`.

The dotted trees cannot: output that is also an editable copy is a fork nobody
declared, and the copy that loses is the one a release ships.

## Considered

- A dotted source tree, matching the installed layout — silently untracked, per
  the unanchored ignore rules above. Invisible until someone clones.
- One tree per agent with no base layer — every agent tree then carries its own
  copy of the shared skills, and they drift.
- Committing the install output so both copies are visible — generated files in
  every skills diff, and two editable copies of one file.

## Log

- 2026-08-28  accepted    — relocated from `AGENTS.md`, where it was the rule most often got wrong
- 2026-08-29  amended     — mirroring is opt-in, not a bar on always-on output styles; the exclusion the record described was upstream's key on a vendored file (#99)
- 2026-08-30  amended     — the switch moved from each skill's frontmatter into the installer, so a vendored skill can be mirrored without editing it (#59)
