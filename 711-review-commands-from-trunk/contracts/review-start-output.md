# Contract: `wfctl review start` output

New lines, printed after the existing trunk and `review.rounds` warnings and before the run header.

Branch and trunk set different commands:

    ⚠ this branch sets review.commands.codex to `codex exec --sandbox none`, but wfctl runs `codex exec --sandbox read-only` from origin/main until the change merges

Branch sets a command the trunk doesn't:

    ⚠ this branch sets review.commands.gemini to `gemini -p`, but origin/main sets no command for gemini, so its reviewers are left out until the change merges

Branch drops a command the trunk sets, reached through a group the trunk lists and the branch removed:

    ⚠ this branch sets no command for codex, but wfctl runs `codex exec --sandbox read-only` from origin/main until the change merges

A trunk whose `wfctl.json` can't be read or whose commands aren't valid is refused before these lines, unchanged:

    ✗ wfctl.json at origin/main: review.commands must map each model to a command string

A reviewer whose model has no trunk command, in the roster and after it:

    s4 gemini ✗ unavailable
    ⚠ gemini: no command in wfctl.json on origin/main; s4 left out of this run
