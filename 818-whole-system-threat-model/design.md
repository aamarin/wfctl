# Ship a whole-system threat model and check for it before a per-control one

Contexts: design-method, evidence-and-derivation, install-and-drift

## Problem Statement

Every repository that uses wfctl has a whole-system threat model committed at its root before it writes its first per-control threat model. A per-control threat model then builds on a map of what the rest of the system exposes, instead of assuming one exists.

Currently, nothing builds that map. Since #799, a change to a security control writes a threat model for that control in its level-2 record (`security-change-needs-threat-model.md`). wfctl's own repository has three of them (accept-check, approval-mode, and auto-approve-grant) and no whole-system threat model, so each was written without a picture of the attack surface around it. A repository adopting wfctl starts from the same place.

This is for two readers:

1. The agent writing a per-control threat model, which needs the whole-system one to cite.
2. The human reviewer judging that per-control threat model in the PR, who needs to read the baseline it cites.

Success means a branch that writes a `## Threat model` section can't finish brainstorm until `THREAT_MODEL.md` is committed at the repository root, or the user has said the pass doesn't apply.

## Recommended Direction

wfctl ships Anthropic's `threat-model` skill unedited, from `anthropics/defending-code-reference-harness`, along with its `_lib/` helper folder. The skill reads the code and git history, works through Shostack's four questions, and writes `THREAT_MODEL.md` with a table of threats, their actors, and their controls. Both folders are mirrored into `.claude/skills/`, since upstream calls its helper by the fixed path `.claude/skills/_lib/checkpoint.py`. They install through `wfctl install-skills`, like every other skill.

A new wfctl skill, `threat-baseline`, layers over upstream's skill and adds three parts upstream doesn't have:

1. If auto-approve is on, the agent still works through the four questions after the bootstrap. It answers them itself, prints each answer, and turns anything the code can't answer into an open question in the file. `/plan-walkthrough` stays off under auto-approve, since it tests the person, but this walkthrough tests the threat model.
2. The file gets a ninth section after upstream's eight, listing fixes that were considered and rejected, with the trade-off for each.
3. The file opens with one line saying it's a working map that gets revised, not a decision record. That way "risk accepted" in a threat row isn't read as an accepted architecture record.

The brainstorm row gets a new pass, `threat-baseline`, between `architecture` and `software-design`, and its command is `/threat-baseline`. wfctl pauses brainstorm on the pass when a branch's level-2 record has a `## Threat model` section and no `THREAT_MODEL.md` is committed at the repository root. The pass is done once the file is committed, or once the user runs `wfctl step none brainstorm.threat-baseline --reason "…"`. A branch with no such record skips the pass.

This branch ends by running `/threat-baseline` on wfctl itself, from the installed tree, and committing wfctl's own `THREAT_MODEL.md`.

## Boundaries and Ownership

wfctl checks whether a branch that writes a per-control threat model has a committed whole-system threat model to build on. It reads both facts from the branch: the record's heading and the file at the repository root. The agent shouldn't answer this, since it would be grading its own work. A bootstrap run takes several minutes and spawns a batch of subagents, so the session writing the record is the one most tempted to skip it. That's why the decision is a check rather than an instruction (`a-rule-is-expressed-as-a-check.md`), and it's recorded in `docs/architecture/security-record-needs-baseline.md`.

wfctl checks only that the file exists, never its contents. If wfctl checked the contents against upstream's schema, it would own that schema, and every upstream schema change would become a wfctl release. The upstream skill already enforces its own schema when it writes the file.

The file lives at the repository root, not the arch root. Upstream writes `<target-dir>/THREAT_MODEL.md`, and the target directory is also what it analyzes, so pointing it at the arch root would analyze the docs folder.

The user decides when the pass doesn't apply, such as a repository whose whole-system threat model is kept somewhere else. That reason goes in the PR body, where `wfctl check-body` checks for it and the reviewer reads it.

## Key Assumptions to Validate

- [ ] Claude Code skips a folder under `.claude/skills/` that has no `SKILL.md`, as upstream ships `_lib/`. Test it by installing and listing skills in a Claude Code session. If Claude Code lists `_lib` as a broken skill, the helper moves and the mirror entry changes with it.
- [ ] Claude Code reads `allowed-tools` written as a YAML list, as upstream writes it. Test it by running the bootstrap and checking that the checkpoint calls run without a permission prompt.
- [ ] A design session on one control doesn't load `threat-model` once `design-levels` names `threat-baseline` as the whole-system skill. Test it with a design-time prompt about one control, run against the installed tree. If it loads `threat-model`, the trigger has to be separated some other way, since the upstream description stays as written.
- [ ] The installed helper runs from its mirrored path. `python3 .claude/skills/_lib/checkpoint.py load ./.threat-model-state` prints `{"status": "absent"}` after `uv run wfctl install-skills --agent claude`.

## MVP Scope

In scope:

1. Vendor `threat-model` (`SKILL.md`, `README.md`, `bootstrap.md`, `interview.md`, `schema.md`) and `_lib/checkpoint.py` unedited, under Apache-2.0, and list both in `vendor-upstream-skills`.
2. Add `threat-model` and `_lib` to the mirrored skills, and add `.threat-model-state/` to the ignore entries `install-skills` writes.
3. Write the `threat-baseline` skill with the three additions.
4. Add the `threat-baseline` pass to the brainstorm row, with its evidence reader and `step none` support.
5. Update the security-control part of `design-levels` to name `threat-baseline`, and to say not to load `threat-model` while writing one control's section.
6. Add tests:
   1. Every `.claude/skills/...` path a shipped skill names resolves after install.
   2. The own-files test recognizes upstream's "in this directory" wording, so it fails if `interview.md`, `bootstrap.md`, or `schema.md` is missing.
   3. The frontmatter test allows `argument-hint`, an upstream Claude Code key.
   4. The new pass reads skipped, paused, and done in the right cases.
7. Run `/threat-baseline` on wfctl and commit its `THREAT_MODEL.md`.

The branch is done when the suite, ruff, mypy, and `doctor` are green, `changes/818` carries a release note, the installed helper runs, the design-time prompt doesn't load `threat-model`, and wfctl's `THREAT_MODEL.md` is committed.

## Not Doing (and Why)

- An instruction in `design-levels` alone. A missing baseline is visible in the branch's own files, so the rule ships as a check (`a-rule-is-expressed-as-a-check.md`). With an instruction alone, an agent that skips the paragraph leaves nothing that notices.
- A nudge that never pauses the pipeline. The user started there, then decided the baseline gets built first, before the first per-control threat model.
- Blocking the PR in the worktree guard. The guard runs after implementation, and the baseline has to exist before the per-control threat model and the code are written against it.
- Asking every repository for a baseline, through `wfctl doctor` or a pass on every branch. Most branches never change a security control, and `doctor` reports drift in what wfctl installed, not gaps in a repository's own documents.
- Counting an uncommitted `THREAT_MODEL.md`. The PR wouldn't carry it, so the reviewer couldn't read the baseline the per-control threat model cites.
- Editing upstream's `SKILL.md` or `schema.md`. The next upstream pull reverts the edit without a conflict.
- A `/threat-model` command wrapper that adds wfctl's parts. wfctl suppresses a wrapper whose name matches a mirrored skill, so it would never install for Claude.
- Fixing upstream's broken references to `../../../docs/security.md` and a `vuln-pipeline`. They're accepted as written, the same as `security-and-hardening`'s citations, since editing them breaks the plain upstream diff.

## Open Questions

- The writer subagent's `wfctl arch accept --dry-run` was blocked last session by a hook saying `.claude/settings.json` is missing the rule that makes Claude Code ask. The same command ran fine in the main session. This may only affect subagents after #833, and it's worth checking if it happens again during implementation.

## Software design decisions

- docs/architecture/design/818-threat-baseline-layers-over-upstream.md — a new wfctl skill, `threat-baseline`, holds wfctl's additions and runs upstream's `threat-model` unedited
