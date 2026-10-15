# Quickstart: checking the feature works for real

The test suite builds a bare remote and two clones in a temporary folder. That
can't reproduce this repository's real layout, a separate clone of an orphan
branch outside the working tree, so these steps run the feature against it.
Run them from this worktree once the code is in.

## 1. Install what the branch ships

```bash
uv run wfctl install-skills --agent claude
uv run wfctl doctor
```

Doctor should be green, and `.claude/commands/store-specs.md` should exist.

## 2. See the pass name the store

With `implement` done and the spec dir holding uncommitted files:

```bash
uv run wfctl status
```

`implement` shows a `store-specs` row reading `uncommitted: N files`, and the
last line is `next: /store-specs`.

## 3. Store this branch's own spec dir

```bash
uv run wfctl store specs
git -C /Users/andremarin/Development/wfctl-specs log -1 --stat origin/specs-trunk
```

The first command prints `✓ stored N files → origin/specs-trunk (<sha>)`. The
second shows that commit on `origin/specs-trunk`, touching only
`359-push-specs-to-trunk/`. Its subject starts `specs(359): store`.

Then `uv run wfctl status` shows `store-specs` as done.

## 4. See `check specs` report what isn't stored

```bash
uv run wfctl check specs
echo "exit $?"
```

The older untracked spec dirs show under "not stored", this branch is no longer
listed, and other worktrees' dirs show under "In progress". It exits 1 while
any older dir is unstored. Those 58 dirs are not this branch's to commit.

## 5. Run `/store-specs` from the installed wrapper

Write a file into the spec dir, then run `/store-specs` in the session. It
stores the file and hands over to `speckit-orchestrate`.

## 6. Time the pass (SC-006)

SC-006 measures the pass by what it adds to `wfctl status`, so time the status
twice: once with the pass reading the real store, and once with the pass
declared not to apply. A claim from `wfctl step none` reads the pass `skipped`
without calling its reader, so the second run does everything the first does
except the pass's own git reads. Run this with `implement` done, as in step 2,
because the reader is not called before then and both runs would measure the
same thing.

```bash
time uv run wfctl status
uv run wfctl step none implement.store-specs --reason "timing status without the pass"
time uv run wfctl status
rm docs/architecture/step-claims/359-push-specs-to-trunk/implement.store-specs.md
```

The first run shows the `store-specs` row with its own reading, and the second
shows it `skipped`. The first run should take no more than 0.5 seconds longer
than the second. The last command removes the claim, so the pass reads the
store again and the claim never reaches a commit. Run `uv run wfctl status`
once untimed before the first `time`, since the first `uv run` of a session
also resolves the environment and would make the first run look slower.

## 7. Removal

Write a review file into the spec dir after the last store, then remove a
throwaway worktree with `wm remove`. The file lands on `origin/specs-trunk`, the
output has no "durable" in it, and `git diff` shows neither repository's
`.workmux.yaml` changed. Repeat with the network off: removal prints the "not
pushed" warning and the worktree is still removed.
