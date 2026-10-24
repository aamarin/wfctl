# Quickstart: one change through both review groups

This walks one branch from its first commit to an open pull request, in a
repository with no `review` key. Each step names what it shows working.

1. List the groups. The defaults appear with no configuration (SC-005).

   ```bash
   uv run wfctl review groups
   ```

2. Try to open the pull request. The guard refuses and lists the commits,
   because no group has reviewed them (US3 scenario 1).

   ```bash
   echo '{"tool_input":{"command":"gh pr create --fill"},"cwd":"'"$PWD"'"}' \
     | uv run wfctl hook worktree-guard; echo "exit $?"
   ```

3. Start the security group, launch `s1` - `s3` with the `reviewing-security`
   skill and the range it printed, and have each write
   `<reports>/<id>.md` with a `Reviewed: <head>` line and a verdict at the end.

   ```bash
   uv run wfctl review start security
   ```

4. Relay one report instead of writing it, to see the relay path (US4).

   ```bash
   printf 'Reviewed: %s\n\nNo findings.\n\nVerdict: Approve\n' "$(git rev-parse HEAD)" > s3-report.md
   uv run wfctl relay s3 --reason "write denied" --from s3-report.md
   ```

5. Check the run. The roster shows three ✓, one of them relayed, and the run
   completes (US2 scenario 3).

   ```bash
   uv run wfctl review check security
   ```

6. Commit a fix, then run the code group. Its range covers the fix commit
   (US1 scenario 2).

   ```bash
   uv run wfctl review start code
   uv run wfctl review check code
   ```

7. Repeat step 2. The guard still refuses, listing the fix commit under
   `security`, because every group has to review the newest commit (US3
   scenario 7). Run the security group again over the fix, then repeat step 2.
   It exits 0.

8. From your own terminal, sign off on a later commit instead of reviewing it.
   The command lists the commits and asks you to type the head's short sha.
   The guard then allows the pull request until another commit lands (US3
   scenarios 4 and 5).

   ```bash
   uv run wfctl review sign-off
   ```

9. Store the specs and read the commit it made. No file under `reviews/` is in
   it, because the reports live in the state directory (US2 scenario 5).

   ```bash
   uv run wfctl store specs
   ```
