# Quickstart: checking the review step and the no-spec route by hand

These two walks check the change end to end once the tests pass. Run them with `uv run wfctl`, so the working tree's code is the one under test.

## 1. The review step, on this branch

This is the real-flow check from the handoff, run before the PR.

1. Finish implement and run `uv run wfctl verify`. `uv run wfctl status` shows `review` as current, with each group's unreviewed count, and `next: /fanning-out-code-review`.
2. Run the panel with `/fanning-out-code-review`. Once `wfctl review check` completes each group, `uv run wfctl status` shows `review ●` and "Story complete".
3. Make one commit, such as the release note. `uv run wfctl status` shows `implement` stale, with `next: wfctl verify`, and `review ○`.
4. Run `uv run wfctl verify`. `uv run wfctl status` shows `review` current again, with `security, code: 1 commit unreviewed since <sha>`.
5. Measure SC-004 while `review` is current. Run `time uv run wfctl status >/dev/null` five times, then `time uv run --project /Users/andremarin/Development/wfctl wfctl status >/dev/null` five times, which runs the `main` checkout's wfctl on this branch. The medians must differ by less than half a second. Record `git rev-list --count origin/main..HEAD` beside the two medians.

This walk doesn't run `gh pr create` to compare with the guard, since a guard that allowed it would open a real PR. The tests in Phase B check that the review row and the guard agree on the same fixtures.

## 2. The no-spec route, on a scratch issue branch

The fresh-worktree check needs a person, since the worktree guard refuses running commands in a second worktree. Run these steps from a scratch worktree for an open issue with no spec folder.

1. `uv run wfctl spec none --reason "<a real reason>"` refuses the placeholder. Run it again with a real reason that answers each spec question by name. It prints the path.
2. `uv run wfctl status` shows `brainstorm … decompose  –  skipped: no spec`, `implement` current with `next: wfctl verify`, and `review ○`.
3. `uv run wfctl status --json | jq .no_spec` prints the reason and path, and `jq '.steps[] | select(.name == "plan") | .sub_steps'` lists `plan-review` and `plan-walkthrough` as `skipped`.
4. Make a commit and run `uv run wfctl verify`. `uv run wfctl status` shows `review` current.
5. Create an empty `design.md` in the spec folder. `uv run wfctl status` shows the full pipeline with `brainstorm` current, and a warning naming `exceptions/spec.md` to delete.
6. `uv run wfctl spec none --reason "…"` now refuses, naming `design.md`.

## 3. Session start on a branch with no spec folder

After `uv run wfctl install-skills --prune --yes --agent claude`, start a session on the scratch branch before step 1 above. The step 7 report states the spec answer and which spec question decided it. On `main`, the report asks no spec question.
