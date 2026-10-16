---
description: Store this branch's spec dir in its spec store and push it, by running `wfctl store specs` and reporting what it printed.
allowed-tools: Bash(wfctl store specs*) Bash(wfctl report-block*)
---

## User Input

```text
$ARGUMENTS
```

The pipeline names this command once `implement` is done and the spec dir is
not stored yet. One command does the whole store, `wfctl store specs`. It
commits only this branch's folder, merges the spec store's upstream branch, and
pushes. Run that command and nothing else that writes. Do not run `git add`,
`git commit`, or `git push` in the spec store yourself, because a commit made by
hand can take in another branch's staged files.

## 1. Run the store

```bash
wfctl store specs
```

Report what it printed, word for word, and go to section 4.

## 2. When your host refuses the command

`wfctl store specs` pushes to a remote, so your host can refuse to run it.
Claude Code's auto-mode classifier is one host that does. wfctl records nothing
in that case, because its process never started. Report the refusal yourself:

```bash
wfctl report-block store-specs --reason "<what your host said>"
```

That holds `implement`, and the next `wfctl status` names `/store-specs` with
`auto: false`, so the run stops for a person. A person who then runs
`wfctl store specs` in their own shell lifts the hold when the store commits or
pushes something, since a successful store records the `store-specs` action
itself. If another branch's store already pushed this spec dir, the store
prints that it was already stored and records nothing, so the hold stays. In
that case, `wfctl report-action store-specs` lifts it.

Then stop trying, and go to section 4. Do not push another way, such as with
`git push` or another client. The host is the only gate on a push, and wfctl
keeps none of its own.

## 3. When the store exits 1

Exit 1 means the spec dir is not backed up yet. The first line of the output
says why, such as an unreachable remote or a refused push, and the lines under
it say what to do. Report the output and do not run the store again from this
command. While the pass reads `in_progress`, `speckit-orchestrate` names
`/store-specs` again, and its stall count is what stops a run that keeps
failing to push.

Exit 0 means the spec dir is stored, was already stored, or sits in a layout
with nowhere to push. In the last case the output says where the files are.

Any of those can end with an `ℹ` line naming files the spec store's ignore rules
left out. They were never stored and never will be, and it is not a failure.
Include the line when you report.

## 4. Hand back

Invoke `speckit-orchestrate` once the store has run, or once the refusal is
reported. Whether the pipeline goes on is the payload's answer, not this
command's.
