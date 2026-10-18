# Quickstart: checking that a removal saves unsaved work

Run these after the definition of done passes. Steps 1 - 3 can run in this
session. Step 4 needs Andre, because a session inside one worktree is refused
when it removes another.

## 1. The commands are where the help says

```bash
uv run wfctl --help            # lists archive and store, not archive-specs
uv run wfctl hook --help       # lists worktree-remove
uv run wfctl archive --help    # lists unsaved
```

## 2. `check config` reads `save_on_remove`

Add `"save_on_remove": ["../elsewhere"]` to `wfctl.json`, run
`uv run wfctl check config`, and check it reports the entry as outside the
repository. Then remove the key and check `check config` is green again.

## 3. The seeded template and doctor agree

```bash
uv run wfctl doctor
```

It reports this repository's `pre_remove` as wired, since it still calls
`archive-specs`. Then read the template's `pre_remove` block in
`wfctl/agents/configs/workmux/.workmux.yaml` and check it is the block form that
calls `wfctl hook worktree-remove`, with no `|| true`.

## 4. A real forced removal (Andre)

Install wfctl from this branch:

```bash
uv tool install --force --from /Users/andremarin/Development/wfctl/wt/40-save-uncommitted-on-remove wfctl
```

Then, from the main checkout:

1. `workmux add 40-scratch --base main`. In it, create `notes.md`, edit a
   tracked file, and commit something. Run `wm rm --force 40-scratch`. The
   removal stops and names the edit and the commit. The worktree is still there.
2. Revert the edit and reset the commit away. Run `wm rm --force 40-scratch`
   again. The removal goes ahead, and `notes.md` is in
   `$(wfctl state-dir --branch 40-scratch)/unsaved/`.
3. Repeat 1 and 2 with this repository's `pre_remove` line temporarily changed
   to `wfctl hook worktree-remove "$WM_WORKTREE_PATH" "$WM_HANDLE"`, and put the
   line back afterwards.

This also answers the two workmux assumptions in the spec: if step 1's removal
goes ahead, workmux 0.1.268 no longer runs `pre_remove` under `--force`, and
the feature needs a different trigger before it can ship. Check the hook's
environment for a `--keep-branch` signal while you are there (`env | grep WM_`
as a temporary first line of the hook).

Afterwards, reinstall the released wfctl:

```bash
uv tool install --force git+https://github.com/aamarin/wfctl.git
```
