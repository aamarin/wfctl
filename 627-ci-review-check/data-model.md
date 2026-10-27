# Data model: CI review check

## Review note

A git note is text that Git attaches to a commit without changing it. wfctl
keeps its review notes under `refs/notes/wfctl-review`, one note per commit.

- **Where**: `refs/notes/wfctl-review` in the repository's common git dir, so
  every worktree on one machine shares it. Pushed to `origin` under the same
  name.
- **Content**: one line per event, in any order:
  - `reviewed by <group>`, where `<group>` is the group's name as
    `wfctl.json` spells it, such as `reviewed by security`.
  - `signed off by a person`.
- **Rules**:
  1. A note holds no line twice. `record` reads the note and skips a line
     already in it (research R6).
  2. A line carries no run number, time, or machine name, so two machines
     recording the same event write the same line.
  3. A reader ignores blank lines and any line it doesn't recognize, and
     ignores a group line for a group neither the trunk's nor the head's `wfctl.json` lists.
  4. Only wfctl writes a note. The guard refuses an agent's `git notes` writes
     and its pushes of any notes ref.
- **Lifecycle**: a line is added when a run completes on the commit or a
  person signs off on it. No line is ever removed. A note on a commit that
  later leaves the branch, after a rebase, stays in the ref and is never read
  for that branch again (R3).

Example, a commit both groups reviewed and a person signed off on:

```
$ git notes --ref=wfctl-review show 9f8e7d6
reviewed by security
reviewed by code
signed off by a person
```

## Coverage

What the counting function takes as input, built by one of two readers.

| Field | Type | From the state directory | From the notes |
| --- | --- | --- | --- |
| `last_reviewed` | `Mapping[str, str \| None]`, group name to commit | `reviews/<group>/last-reviewed.json` | the first branch commit, in topological order, whose note has `reviewed by <group>` |
| `signed_off` | `Sequence[str]` | `reviews/sign-off.json`, zero or one commit | every branch commit whose note has `signed off by a person` |

"Branch commit" means a commit the head reaches and the trunk refs don't
(research R3). A group with no reviewed commit maps to `None`, and
`commit_range` then starts at the merge base with the trunk.

## Unreviewed commit

A commit that `commit_range(head, last_reviewed[group])` lists for a group,
and that is neither a signed-off commit nor an ancestor of one. The result
maps each group with any such commit to its commits, oldest first, and leaves
out a group with none. This is the existing return shape of `unreviewed`.

## Outward actions

Each successful notes push is recorded with `record_outward_action` under the
action name `store-reviews`, the same way `store specs` records
`store-specs`. A rerun of a CI job isn't recorded, since it changes no
repository state.
