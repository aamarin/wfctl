# Quickstart: check the round cap end to end

This is the manual check in the spec's Validation Strategy, item 5. It runs
against this worktree's wfctl. `uv run` finds its project from the current
directory, so from step 2 on, every `wfctl` command runs from the scratch clone
with `--project` pointing back here:

```bash
WT=/Users/andremarin/Development/wfctl/wt/626-review-round-cap
wf() { uv run --project "$WT" wfctl "$@"; }
```

The steps below write `wf` for that.

1. Install the skills from this checkout:

   ```bash
   uv run wfctl install-skills --agent claude
   ```

   Then read `opening-a-change` Step 1 and the `fanning-out-code-review` example
   header in `.claude/skills/`, and confirm they describe one run per group per
   round.

2. Make the scratch clone with `git clone` from a remote that already has
   commits on `main`, so it records `origin/HEAD`. A remote added with `git
   remote add`, or a clone of an empty repository, has none, and step 10 would
   then show the fallback. Check it before going on:

   ```bash
   git symbolic-ref refs/remotes/origin/HEAD   # prints refs/remotes/origin/main
   ```

   If it prints nothing, run `git remote set-head origin --auto`. Then check
   out a branch that names an open issue, and add one commit.
3. Run three rounds. Each round goes like this:

   ```bash
   wf review start security   # header reads round N of 3
   # write each expected report, then
   wf review check security
   wf review start code
   # write each expected report, then
   wf review check code
   git commit --allow-empty -m "fix"     # gives the next round something to review
   ```

4. Start a fourth round:

   ```bash
   wf review start security
   ```

   It exits 1 with `security has run 3 of 3 rounds on this branch`, and no
   `runs/004` folder exists.
5. In your own terminal, sign off through the head. Run it there, not through
   the agent, since the guard refuses the sign-off command from an agent.
6. Run `wf review start security` again. It exits 0 and prints
   `the sign-off at <sha> covers every commit left to review`.
7. Merge the trunk cleanly with `git merge origin/main` (make one trunk commit
   first if it has none), and run `wf review start security` again. It still
   exits 0 with the same line, naming the same signed-off commit, since the
   clean merge isn't in the range.
8. Confirm the worktree guard would allow the PR, without opening one. Pipe it
   the payload it would get for `gh pr create`:

   ```bash
   echo '{"tool_input": {"command": "gh pr create --draft"}, "cwd": "'"$PWD"'"}' \
     | wf hook worktree-guard
   ```

   It exits 0 and prints no `✗` line.
9. Set `"review": {"rounds": 5}` in the branch's `wfctl.json` without
   committing it to `main`. `review start` prints the mismatch warning and
   still uses 3.
10. Add one commit to the branch, so the sign-off from step 5 no longer covers
    it. Push the branch's head to `origin` as `loose`, with `"review":
    {"rounds": 9}` in its `wfctl.json`, then set `"trunk": "loose"` in this
    branch's working tree. Run `wf review start security`. It prints the trunk
    warning and outcome 4 reading `3 of 3`, which shows the cap came from
    `origin/main`. Then run step 8's guard command again. It refuses and lists
    the new commit under security, which shows the range is still measured from
    `main`. If wfctl used `loose` as the trunk, that commit would be on the
    trunk and the guard would allow the PR.
