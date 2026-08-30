# Holding pen — not a feature directory yet

`design.md` and `phase-entry-is-observed-not-recorded.md` were produced on
2026-08-28 by the T021 trial for #86: a design session asked only to design
phase-age reporting, which reached the level-2 gate and wrote the record on its
own. They are the trial's output, kept because the design is real.

They are here rather than in place because neither has a home yet:

- The directory is unnumbered. `wfctl` resolves a feature dir by branch name,
  so this becomes `<issue>-phase-age` once the issue exists.
- The record's home is `<repo>/docs/architecture/`, which is in-tree and
  therefore per-branch. Filing it there today would attach a different
  feature's decision to whichever PR is open.

Both were written in `wt/94-stacked`, a throwaway worktree stacking PRs #95,
#97 and #98 to test the capture path. That worktree is disposable; these files
are not.

Status is `proposed`. It is not in force and `wfctl arch context` will not
present it as such until someone accepts it.
