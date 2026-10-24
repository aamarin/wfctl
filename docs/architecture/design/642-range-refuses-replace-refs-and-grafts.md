---
status: proposed
---

# The review range refuses any replace ref or grafts file, rather than judging each one

## Context

A review run lists the commits a group hasn't reviewed, and each reviewer reads those commits with a plain `git show <sha>`. The two reads have to see the same content. Otherwise a completed run marks a change reviewed that no reviewer read.

Git has two kinds of local state that change what a commit looks like without changing the commit:

1. A replace ref, made with `git replace`, swaps one object for another. It can swap a commit, a tree, or a file's blob, and `git replace --graft` swaps a commit for a copy with other parents.
2. A grafts file, `.git/info/grafts` or the file `GIT_GRAFT_FILE` names, gives a commit other parents. Git has deprecated it, but still reads it.

wfctl lists commits with both turned off: every call passes `--no-replace-objects` (#640), and `GIT_GRAFT_FILE` points at a file that can't exist. A reviewer's `git show` honors both. Neither is pushed by default, so the PR and the merge carry the real commits.

Previously, this branch refused only a replace ref that changed a commit's tree, and let a same-tree replacement through on the grounds that the reviewer still reads every change. The security review of this branch showed three ways past that check, each reproduced at 013b70d:

1. A replaced blob. `git show` prints the substituted file content.
2. `git replace --graft <commit> <decoy>`, where the decoy has the commit's own tree. `git show` prints the subject and an empty diff.
3. The same graft written as a grafts file line. `git show` again prints an empty diff.

The agent writing the change can create any of these, since `refs/replace/` and `info/grafts` sit in the common directory every worktree shares. A leftover graft from history surgery does the same by accident.

`review-covers-unreviewed-commits` constrains this: each review covers every commit since the last one. This record keeps that rule and changes only which local states the range refuses.

## Verified

- `git --no-replace-objects replace -l` lists replace refs on git 2.44, so the listing works under the flag `_git` always passes.
- `GIT_REPLACE_REF_BASE=refs/other/ git replace -l` lists nothing for a ref under `refs/replace/`, so `replace -l` reads the namespace the reviewer's git reads.
- `git rev-parse --git-path info/grafts` returns `GIT_GRAFT_FILE` when it is set, and fails with "Not a directory" under `_git`'s own override. `--git-path info` is not remapped, so the check asks for that and appends `grafts`.
- This repository has no replace refs (`git replace -l` prints nothing).
- `tests/test_review.py` reproduces all three cases above, plus the graft that cuts commits out (#640's case) and a whole-object replace of a listed commit and of its parent.

## Assumed

- No repository using wfctl's review depends on replace refs or a grafts file in the checkout it reviews from. A repository that does would see every `wfctl review start` refused until it removes them, and would need a way to review through them that this record doesn't provide.

## Direct baseline

Keep the existing per-object check and extend it to each case the review found. For each listed commit and each parent it is diffed against, refuse a replaced commit whose tree differs, or whose parents' trees match its own. Then walk each listed commit's tree for a replaced blob or tree, and parse the grafts file for lines naming a listed commit. Every new kind of replacement adds another case.

## Decision

`commit_range` refuses before it lists anything when `git replace -l` prints any ref, or when the grafts file has any content. The refusal names the remedy: `git replace -d <shas>`, `delete <path>`, or `unset GIT_GRAFT_FILE`.

wfctl's own calls keep `--no-replace-objects` and the `GIT_GRAFT_FILE` override, so the reads after the refusal still see the real objects.

## Diagram

No boundary in force runs between these components, so neither graph has a divider.

```
baseline

  commit_range ──calls──► per-commit tree check
  per-commit tree check ──reads──► replace refs, per listed commit and parent
  per-commit tree check ──reads──► each listed commit's tree, per blob
  per-commit tree check ──reads──► grafts file, per listed commit

decision

  commit_range ──calls──► _refuse_rewritten_history (new)
  _refuse_rewritten_history ──reads──► replace refs, any
  _refuse_rewritten_history ──reads──► grafts file, any content
```

The baseline has four arrows and the decision has three. The baseline's reads depend on the listed commits, so its cost grows with the range and its correctness depends on naming every kind of replacement. The decision's reads depend on nothing in the range. The change this absorbs is a kind of replacement nobody listed yet, which adds a case to the baseline and nothing to the decision.

## Considered

- The direct baseline. We didn't choose it because it is the shape that already failed: the first version checked one property of the replacement, and the review found three kinds it didn't name.
- Compare what the reviewer reads with what wfctl reads. For each listed commit, run `git show --format=` once as wfctl runs it and once in the reviewer's environment, and refuse when the two differ. This is exact, and it lets through a replace ref that changes nothing a reviewer reads. We didn't choose it because it doubles the git calls per commit for a state no reviewed repository is expected to have, and because a reviewer reads more than `git show`, such as `git log -p` or a file at the head, which the comparison doesn't cover.
- Keep seeing through, as #640 did, and tell reviewers to pass `--no-replace-objects` too. We didn't choose it because the instruction lives in a prompt and wfctl can't check that a reviewer followed it.

## Consequences

A completed run now means every reviewer's `git show` read the commit wfctl listed, whatever replace refs or grafts the repository held.

#640's case, a graft that cuts commits out, is now refused where it used to be listed through. The range was correct there, but each reviewer's diff spanned the commits the graft cut out, so the review read them as one change.

A repository with any replace ref is refused, even one that touches no listed commit. The remedy is one command, and the refusal prints it.

At the worktree guard, the refusal surfaces as "the review check failed", the same as a shallow clone or a missing trunk. That message tells an agent to stop and ask a person, which fits here, since a replace ref under review is either a mistake or an attempt to hide a change.

## Verification

- `test_range_refuses_any_replace_ref` covers a graft that cuts commits out, a same-tree graft, a replaced blob, and a whole-object replace of a listed commit and of its parent.
- `test_range_refuses_a_grafts_file` covers a grafts line onto `main` and onto a same-tree decoy.
- `test_range_refuses_a_grafts_file_named_by_the_environment` covers `GIT_GRAFT_FILE`.

## Log

- 2026-10-24  proposed  — written for #642, after the security review found three replacements the per-commit tree check let through
