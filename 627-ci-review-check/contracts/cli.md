# CLI contract

Output is plain text with no markup, and tests pin `NO_COLOR`. A short hash is
seven characters.

## `wfctl check reviews`

Reads the review groups, the coverage from the notes, and prints whether
every commit on the branch is reviewed. It needs no network, so it runs the
same locally as in CI.

The groups are every group the trunk's `wfctl.json` lists, plus every group
the head commit's `wfctl.json` adds (FR-015, research R13). It reads both with
`git show <ref>:wfctl.json`, never from the working tree, so an uncommitted
edit changes nothing. A missing file, or one with no `review` key, gives the
default groups.

`--base <branch>` sets the trunk to `origin/<branch>` and ignores the `trunk`
key in `wfctl.json` (FR-015a, research R14). CI always passes it. Without it,
the trunk is found the way the guard finds it.

Every commit is covered, exit 0:

```
✓ Every commit on this PR has been reviewed.
```

A commit isn't covered, exit 1. Each commit is listed once, oldest first, with
the groups that haven't reviewed it:

```
✗ 2 commits haven't been reviewed:
    9f8e7d6 test: cover an empty note   (security, code)
    1a2b3c4 fix: drop the stale ref     (code)
  Run the review panel. If you already did, run `wfctl store reviews`.
```

"1 commit hasn't" for one commit, "N commits haven't" for more. Each subject
is padded to the longest one, so the group lists line up.

It can't work out the range, exit 1, with one line naming the cause:

```
✗ can't check reviews: this clone is shallow, so wfctl can't see every commit on the branch; run git fetch --unshallow
✗ can't check reviews: can't find the trunk branch; set trunk in wfctl.json
✗ can't check reviews: origin/<branch> doesn't exist
✗ can't check reviews: the trunk branch is <branch>, the branch under review
✗ can't check reviews: can't read the note on 9f8e7d6: <git's message>
✗ can't check reviews: wfctl.json at origin/main: <a problem in its review key>
```

The first two reuse the messages of `ShallowClone` and `NoTrunk` in
`_review.py`, so the cause text matches what the guard says for the same
condition. The second can't happen with `--base`, which never looks the trunk
up. A `review` key problem names the commit or trunk ref whose `wfctl.json`
holds it.

## `wfctl store reviews`

Sends `refs/notes/wfctl-review` to `origin`, then reruns a failed `review`
job on the branch's open PR.

| Situation | Output | Exit |
| --- | --- | --- |
| Pushed | `✓ sent review notes to origin` | 0 |
| Pushed after joining remote notes | `✓ joined origin's review notes with this machine's and sent them` | 0 |
| Local and remote match, or no local notes | `✓ nothing to send; origin has every review note` | 0 |
| No `origin` | `✗ no origin remote to send review notes to` | 1 |
| Second push rejected, or a network error | `✗ couldn't send review notes: <git's message>` | 1 |

A rerun adds one line after a successful send, and after `nothing to send`
too. The CI failure tells the user to run `store reviews`, and the notes can
reach `origin` while that check is still running, so the check stays failing
unless something reruns it:

```
↻ reran the failed review check on PR #651
```

A rerun that fails adds a warning and leaves the exit code as it was. wfctl
doesn't retry it, and the warning doesn't name `store reviews`, which would
have nothing left to send:

```
⚠ couldn't rerun the review check on PR #651: <gh's message>
  The notes are on origin. Rerun the review check on the PR to pick them up.
```

## `wfctl review check <group>` (changed)

Unchanged output while the run is incomplete. When the run is complete, it
also records `reviewed by <group>` on the run's head, sends the notes, and
reruns a failed job, adding the `store reviews` lines above. A failed send
adds this and leaves the exit code at 0:

```
⚠ couldn't send review notes: <git's message>
  The note is saved here. Run `wfctl store reviews` to send it.
```

If writing the note locally fails, for example because another worktree holds
the lock on the notes ref, it adds this, sends nothing, and leaves the exit
code at 0. The run is still complete in the state directory, and the next
`review check` on it records the note again, since recording skips a line
that's already there (research R6):

```
⚠ couldn't write the review note: <git's message>
  Run `wfctl review check <group>` again to record it.
```

## `wfctl review sign-off` (changed)

After `✓ signed off through <sha>`, it records `signed off by a person` on the
head, sends, and reruns, with the same added lines and the same warning on a
failed send.

If writing the note locally fails, it adds this, sends nothing, and leaves the
exit code at 0. The sign-off is in the state directory, so the guard allows
the PR, but CI reads only the note:

```
⚠ couldn't write the review note: <git's message>
  Run `wfctl review sign-off` again to record it.
```

Signing off again then finds nothing unreviewed, since the state directory's
sign-off covers the head. When that sign-off is the head and the head's note
lacks the line, it records and sends the note instead of stopping (PR-009):

```
✓ recorded the sign-off through 9f8e7d6 as a review note
✓ sent review notes to origin
```

When the note already holds the line, it prints `nothing unreviewed; no
sign-off needed` as before and writes nothing.

## Which groups the local commands use (changed)

The guard and `wfctl review sign-off` require the same groups as `wfctl check
reviews`: the trunk's list plus the head commit's additions (FR-010). Their
output doesn't change, but a group the branch removed from `wfctl.json` now
shows up in the guard's refusal until it's reviewed.

`wfctl review start <group>`, `wfctl review groups`, and `wfctl relay`
accept that list plus any group in the working tree's `wfctl.json` (FR-010a).
A name in neither still prints `✗ no review group named '<group>'` and exits 1.
`wfctl review check <group>` loads no list. It accepts any name `PLAIN_NAME`
matches that has a run, so a broken `review` key on the trunk can't stop a
completed run from recording its note (PR-024). FR-010a still holds, since
every group on the list is accepted. `relay` refuses a reviewer id whose first
letter matches two groups. That happens when a group is renamed on the branch:
the trunk still lists `money-rules`, the branch lists `money`, and both number
their reviewers `m1`, `m2`. The trunk still requires its group, so the
refusal names the branch's as the one to rename:

```
✗ reviewer m2 matches two groups, money-rules and money.
  main still requires money-rules, so rename money in wfctl.json to start with a different letter.
```

When neither group is one the trunk requires, it asks to rename either one:

```
✗ reviewer m2 matches two groups, money-rules and money; rename one in wfctl.json
```

## Guard refusals (new)

```
✗ wfctl writes review notes itself when a run completes or a person signs off.
  To send a note that didn't reach origin, run `wfctl store reviews`.
```

This one line covers both a `git notes` write and a `git push` naming
`refs/notes/` or carrying `--mirror`.
