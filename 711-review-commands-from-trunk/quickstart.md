# Quickstart

1. In this worktree, change `review.commands.codex` in `wfctl.json` to another command. Leave it uncommitted.
2. Run `WFCTL_STATE_DIR=<scratch folder> uv run wfctl review start security`. The override pins the run records and the round tally to the scratch folder, so the run uses none of this branch's three security rounds.
3. Check the output prints `main`'s codex command beside each codex reviewer, and a `⚠` line naming the difference.
4. Revert `wfctl.json` with `git checkout wfctl.json`, after making sure nothing else in it is uncommitted.
