# Research: Drop unloaded skills

## 1. Which brainstorm entry point stays

- Decision: `/speckit.brainstorm` is the step's only listing entry. The
  `brainstorm` skill and wrapper are deleted, and `speckit-brainstorm` leaves the
  Claude mirror but keeps shipping under `.agents/skills/`.
- Rationale: `wfctl status` prints `/speckit.brainstorm`, and since #473 the
  wrapper is model-invocable, so the mirror #361 added is a second line in the
  listing. `docs/architecture/design/698-brainstorm-listed-once.md` holds the
  argument.
- Alternatives considered: putting `disable-model-invocation` back on the
  wrapper, which brings back #361's failure; keeping both entries; and renaming
  the skill to share the wrapper's name, which brings back #170's tie.

## 2. How an existing project loses a dropped skill

- Decision: through the orphan rule the installer already has. No code change.
- Rationale: checked on 2026-11-03 in a scratch repo. An install from `main`,
  then an install from a bundle without `using-superpowers`, reported three
  orphans and removed nothing. `doctor` printed them with the `--prune` command
  for each layer. `install-skills --agent claude --prune` removed all three,
  left a hand-authored `.claude/skills/my-own` and `.agents/trackers/github.json`
  in place, and `doctor` was green afterwards. `/start-session` runs that repair
  with `--yes` whenever `doctor` reports drift.
- The handoff's warning that `--prune` deletes the tracker config was #209. The
  installer now carries the active tracker's files forward on a bare run (the
  `active_tracker` block in `cli.py`), so the config is never an orphan.
- Alternatives considered: pruning on every bare install, which deletes a copy
  the project edited, since the manifest stores no content hash; and pruning only
  unchanged copies, which needs a new manifest field.

## 3. What replaces `verification-before-completion` at level 4

- Decision: `wfctl verify`.
- Rationale: `wfctl-runs-the-verification` (accepted) says wfctl runs the
  repo-declared checks, records the verdict, and the agent never certifies its
  own completion. The skill asked the agent to do that certification itself, and
  no session loaded it in five weeks.
- Alternatives considered: keeping the skill as a file read by path. It would
  still restate a job `wfctl verify` owns, and only `design-levels` and
  `python-pattern-selection` name it.

## 4. Which tests pin the names

- `tests/test_install_skills.py`: `_SUPPRESSED_ON_A_MIRRORING_LAYER` pins
  `brainstorm`, `using-superpowers`, and `verification-before-completion`.
- `tests/test_skill_cross_references.py`:
  `test_brainstorm_is_mirrored_onto_the_native_discovery_path` pins
  `speckit-brainstorm` in the mirror.
- `tests/test_architecture_design_skill.py`: a comment names
  `verification-before-completion`.
- `tests/test_skill_attribution.py` checks `NOTICES.md` against
  `vendor-upstream-skills.md`, so both lose the same two names.
