# Quickstart: checking the change by hand

Run these from an issue worktree, then again from the `main` checkout.

1. Install the working tree's skills and tracker scripts:

   ```bash
   uv run wfctl install-skills --tracker github --agent claude --yes
   ```

2. Read the report:

   ```bash
   uv run wfctl status --session
   ```

   In the worktree, check that it shows the issue, the parent when there is one, the PR when there is one, the whole handoff, and the last stop. Check that it shows how many commits the branch is ahead of the trunk. On `main`, check that the issue, parent, and PR lines each read `not-applicable`.

3. Check that `doctor --session` leaves out other issues' claim notices:

   ```bash
   uv run wfctl doctor --session
   ```

4. Start a new conversation and run `/start-session`. Check that it runs four wfctl commands, runs neither `issue list` nor `change list`, and names the same step 8 row the old skill named. The one exception is an issue branch whose handoff names no first action. There the new skill doesn't ask, unless the evidence disagrees, and names the evidence it used: the commit count, the pipeline position, and the issue.

5. Measure the token cost before and after, as the spec's Validation Strategy describes, and record both figures in the PR.
