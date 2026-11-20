# Quickstart: walking the change in Claude Code

The guard hook in `.claude/settings.json` runs the installed `wfctl`, so the
walk needs the branch build installed as the tool. Steps 0 and 12 are the
user's to run.

0. The user runs `uv tool install --force --from <this worktree> wfctl`.
1. `wfctl install-skills --agent claude`, then confirm the five `ask` rules are in `.claude/settings.json`.
2. Write a throwaway proposed record under `docs/architecture/`, with a drawing so the accept's checks pass. Run `wfctl arch check-accept <slug>` and confirm no prompt appears.
3. Ask the agent to accept it. Claude Code shows `wfctl arch accept <slug>` and waits. Decline, and confirm the record is still proposed.
4. Ask again and approve. Confirm the record is accepted and its Log line reads "approved at the permission prompt".
5. Ask the agent to run `bash -c "wfctl arch accept <slug>"`. Confirm the guard refuses it and names the plain command.
6. On a throwaway branch cut from `main` with one empty commit, never the feature branch, ask the agent to sign off. A sign-off on the feature branch would cover its implementation commits with no review panel. Decline once and confirm nothing was written. Ask again, approve, and confirm no sha was asked for. Delete the throwaway branch and its review note afterwards.
7. On the same throwaway branch, add a baseline line and ask the agent to run the installed `wfctl arch approve-imports`. Approve, and confirm the approval prints. Ask it to run `uv run wfctl arch approve-imports` and confirm the guard refuses.
7a. With Claude Code in auto mode, ask the agent to accept the throwaway record again on a fresh copy, and confirm the prompt still appears.
8. Run `wfctl auto-approve on`, ask the agent to sign off again, and confirm the guard refuses. Turn it back off.
9. Remove one rule from `.claude/settings.json`, run `wfctl doctor`, and confirm it names the rule and exits 1. Ask the agent to run that command and confirm the guard refuses. Reinstall.
10. In your own terminal, run the sign-off and confirm it still asks for the short sha.
11. Delete the throwaway record and revert the test commits.
12. The user reinstalls the tool from `main`.
