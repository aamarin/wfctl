# Stop shipping skills that sessions never load

Contexts: design-method, install-and-drift

## Problem Statement

Every model-invocable skill and command the Claude layer installs adds a line to
the listing that every session loads. Two skills wfctl ships weren't loaded once
in 1,961 transcripts over five weeks, and the brainstorm step is listed three
times. A one-word prompt in a clone of `main` costs 39,789 tokens today (measured
2026-11-03, twice, same number both runs). The issue measured 38.8k earlier, so
the harness has grown about 1k since then.

## Recommended Direction

Drop what nothing reads, and list each pipeline step once.

| Skill or command | Loads in 5 weeks | Who names it in `wfctl/` | Decision |
|---|---|---|---|
| `using-superpowers` | 0 | `cli.py` mirror list, `NOTICES.md`, tests | Drop the skill and its wrapper |
| `verification-before-completion` | 0 | `cli.py`, `design-levels` §4, `python-pattern-selection` overview | Drop the skill and its wrapper, and point both skills at `wfctl verify` |
| `brainstorm` skill | 6 | its own wrapper and the `cli.py` mirror list | Drop the skill and its wrapper, since `/speckit.brainstorm` is the same entry point |
| `speckit-brainstorm` skill | listed beside its command | the `/speckit.brainstorm` command, by path | Keep the file and take it out of the Claude mirror (`698-brainstorm-listed-once`) |
| `/speckit.brainstorm` command | the step `wfctl status` prints | `_STEPS` in `_pipeline.py` | Keep, and its description takes over the dropped skills' trigger wording |
| `model-the-domain` | 2 | `design-levels` level 2, by path | Keep: it has loads and a named reader, and another repo may use it more |
| `python-pattern-selection`, `python-package-layout` | 0 by name, new | `design-levels`, `design-passes` | Keep, per the handoff: under five weeks old, and #697 linked both |
| `receiving-code-review` | 6 | `fanning-out-code-review` | Keep: five or more loads |

`verification-before-completion` is replaced by `wfctl verify` rather than kept
as a file, because `wfctl-runs-the-verification` (accepted) already says the
agent never certifies its own completion. `wfctl verify` is the command that
does the check, and the skill that asks the agent to do it is the part no
session loaded.

### Projects that already installed a dropped skill

Today's installer already handles this, and the change adds a test rather than
new behavior. I checked it on 2026-11-03 with a scratch repo: installed from
`main`, added a hand-authored `.claude/skills/my-own`, and installed again from
a bundle without `using-superpowers`.

1. The bare `install-skills` run listed the three dropped paths as no longer
   shipped and left them on disk.
2. `wfctl doctor` printed the same three paths and the `--prune` command for
   each layer.
3. `install-skills --agent claude --prune` removed all three. `my-own` stayed,
   and `.agents/trackers/github.json` stayed too.
4. `doctor` was green afterwards.

`/start-session` runs that `--prune --yes` repair whenever `doctor` reports
drift, so a project that uses the session skills loses a dropped skill on its
next session. The handoff warned that `--prune` deletes the tracker config. That
was #209, and the installer now keeps the active tracker's files on record, so
the warning no longer holds.

We didn't make a bare `install-skills` prune on its own. The manifest records
which paths wfctl wrote, but not their content, so a bare prune would delete a
copy the project edited by hand. Currently, `--prune` is the step where a person
or `/start-session` accepts that.

## Boundaries and Ownership

No boundary moves. Both contexts are declared with `wfctl arch none`:

- `install-and-drift`: the installer keeps its modes and its removal rule. A
  dropped skill becomes an orphan the manifest recorded, which is the existing
  case.
- `design-method`: level 4 points at `wfctl verify`, which
  `wfctl-runs-the-verification` already makes the owner of completion.

## Key Assumptions to Validate

- The `brainstorm` skill's six loads came from its description firing at the
  start of a feature. Moving that wording onto `/speckit.brainstorm`'s
  description keeps the trigger. If loads of the step drop after the change,
  this was wrong.
- Claude Code lists a command with no `disable-model-invocation` and lets the
  Skill tool load it. This session's `Skill("speckit.brainstorm")` call is the
  evidence.
- No repo declares a `wfctl.json` pass whose `command` is `/brainstorm`,
  `/using-superpowers`, or `/verification-before-completion`. `wfctl check
  config` reports such a pass as uninstalled after this change.

## MVP Scope

1. Remove `using-superpowers`, `verification-before-completion`, and
   `brainstorm` from `wfctl/agents/skills/` and `wfctl/agents/commands/`.
2. Remove those three and `speckit-brainstorm` from `_MIRRORED_SKILLS`, and
   update the comments that defend them.
3. Repoint `design-levels` §4 and `python-pattern-selection` at `wfctl verify`.
4. Move the `brainstorm` skill's trigger wording onto `/speckit.brainstorm`'s
   description.
5. Update `NOTICES.md` and the `vendor-upstream-skills` table, which
   `test_skill_attribution.py` checks against each other.
6. Update the tests that pin the mirror list and the suppressed wrappers, and
   add one install test: a dropped mirrored skill leaves both layers on
   `--prune`, and a hand-authored sibling skill and the tracker config stay.
7. Re-measure the "hi" baseline in a clone with the change installed.

## Not Doing (and Why)

- Trimming long descriptions, such as `model-the-domain`'s 764 characters. That
  changes when a skill fires, and the issue scopes this work to dropping skills.
- Pruning on a bare `install-skills`. See above.
- Editing `start-session`, which #700 is changing. It names none of the dropped
  skills.
- Plugins installed outside wfctl, per the issue.

## Open Questions

None. The handoff's two questions are answered above: `/speckit.brainstorm`
stays as the brainstorm entry point, and an existing install loses a dropped
skill through the `--prune` path that `doctor` and `/start-session` already use.

## Software design decisions

- docs/architecture/design/698-brainstorm-listed-once.md — the brainstorm step is listed once, as its `/speckit.brainstorm` command

The `design-method` context makes no structural choice, so it carries a
`brainstorm.software-design` claim instead of a record.
