# Reachable spec roots, and an archive that knows what it is for

Closes #26, Closes #27.

## The behaviour change to know about

**A failed archive now aborts `workmux remove`.** Under the previous `|| true` no
user has ever seen this hook block a removal. Afterwards, a full disk or an
unreadable spec file stops teardown instead of silently destroying the design
work.

That is the point of the change, not a side effect. The refusal is narrow — it
fires only when artifacts that would have been destroyed could not be preserved.
A durable spec root, nothing to archive, a missing worktree, a non-git directory,
or any unrelated internal failure all still exit 0, so an unrelated bug cannot
strand a worktree. wfctl not being installed at all also proceeds: blocking there
would strand every worktree on that machine.

`workmux remove --force` does **not** bypass the hook — verified, not assumed —
so every refusal prints the manual route out, in full:

```
✗ 3 spec file(s) could not be archived — removal aborted, nothing lost.
  Cause: [Errno 13] Permission denied: '…/specs/43-refuse/spec.md'

  Retry:         workmux remove 43-refuse
  Remove anyway: git worktree remove …/wt/43-refuse && git branch -D 43-refuse
                 (add --force to the first if the worktree has untracked
                  files; leaves the tmux window workmux would have closed)
```

## Why this exists

A worktree holding only gitignored design artifacts reads **clean** to
`git status`, so every version-control-based check sees nothing to protect and
`workmux remove` destroys them without complaint. Work git *can* see — tracked
edits, untracked files — already stops the removal on its own. This covers
exactly the set nothing else can.

Demonstrated, not argued:

```
$ git -C wt/99-probe status --porcelain     # empty — reads CLEAN
$ workmux remove 99-probe
✓ Removed worktree '99-probe' and branch '99-probe'
$ ls wt/99-probe/specs/99-probe/design.md
No such file or directory
```

## What changed

**One predicate** — is this artifact inside the worktree being removed — decides
what gets copied, whether a failure blocks teardown, and what the message says.

| Source | At risk | Archived |
|---|---|---|
| `<spec_dir>/*` under the default `<repo>/specs` | yes | yes, unchanged |
| `<spec_dir>/*` under an external `spec_root` | no | no |
| `<spec_dir>/*` under a `spec_root` resolving back *inside* | yes | yes |
| `<worktree>/.agent/spec.md` (superseded path) | yes | yes |

Path containment, never "is `spec_root` set" — row three is the case a flag would
get wrong, and it has a regression test that passes both before and after.

**`archive()` is promote-on-success.** It previously displaced `archive/` before
copying, so a mid-copy failure left an unindexed partial under the canonical name
while the complete result sat under a timestamp reading as superseded. Since a
failed archive now prompts a retry, that retry pushed the partial into the
timestamped pool where nothing distinguished it from a real previous run — the
safety mechanism manufacturing the ambiguity. Nothing reaches `archive/` until
every copy has landed.

**`archive-story` → `archive-specs`**, with the old name kept as a hidden alias.
Not politeness: `.workmux.yaml` is repo-local, copies predating the rename
persist, and with the hook now able to abort a removal an unknown command name
would make those repos' worktrees **unremovable**. `wfctl doctor` reports a
`pre_remove` still naming the old command, so the alias has an end condition
rather than becoming permanent (#36 tracks removing it with the other four
transitional checks).

**`install-skills` asks where specs live**, once, on first interactive install,
beside the tracker question. `spec_root` shipped in #25 with nothing pointing a
project at it. Keeping specs in the repo records no `spec_root` at all — the
default *is* the absence of the key, so that answer resolves byte-identically to
never having been asked.

## Verification

327 → 347 tests. Full suite, ruff and mypy green.

Verified against real `workmux remove` runs, not only unit tests:

- clean worktree holding only gitignored specs → archived, removal proceeds
- durable `spec_root` → no archive created, live specs untouched, removal proceeds
- unreadable spec file → exit 1 → removal aborted, worktree and specs intact,
  state dir empty (staging discarded, no partial)
- wfctl off `PATH` → warns, exits 0, removal proceeds
- the printed escape route, pasted verbatim, removes the worktree and branch
- a `.workmux.yaml` still naming `archive-story` → still archives; doctor reports
  it and exits 0

That escape-route check found a bug the tests could not: rich was wrapping the
path across three lines, so the command could not be pasted. Every assertion
still passed, because they match short substrings while the path is what splits.

## Two docstrings were rewritten, deliberately

`_archive.py` argued that archiving a durable spec root "is still worth running"
because the flattened snapshot has value independent of risk. That was a reviewed
position from #24, and it is reversed here rather than quietly contradicted. The
numbering and index stay — they are how the archive reads — but they stopped
being why it exists.

`cli.py` promised "Never exits non-zero". Combined with `|| true`, that guarantee
meant a failed archive was silent and the worktree was destroyed anyway: the
exact failure the command exists to prevent, delivered by its own error handling.

Also reconciles `aamarin/wf-skills#11` FR-013 ("no component reads both artifact
locations") against the legacy `.agent/spec.md` read, at the code, since that epic
is closed and there is nowhere else for it to live.

🤖 Generated with [Claude Code](https://claude.com/claude-code)
