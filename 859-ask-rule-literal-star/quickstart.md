# Quickstart: seeing the settings question

At a desktop terminal, in this worktree:

1. Remove the `wfctl hook worktree-guard` entry under `PreToolUse` from
   `.claude/settings.json` by hand, so there's a change to make. Use a hook
   rather than a rule, since install refuses outright over a missing rule it
   has a receipt for.
2. Run `uv run wfctl doctor`. It warns that the hook is pending and prints the
   install command. It exits 0 if nothing else is wrong.
3. Run `uv run wfctl install-skills --agent claude < /dev/null`. The file is
   unchanged, and install prints the skipped-change warning.
4. Run `uv run wfctl install-skills --agent claude`. It lists the change and
   asks. Answer `n` and check the file is unchanged.
5. Run it again and answer `y`. The hook is back, and doctor is quiet.
