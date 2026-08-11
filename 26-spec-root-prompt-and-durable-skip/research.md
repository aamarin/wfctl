# Phase 0 Research: spec-root prompt and durable-spec skip

**Date**: 2026-08-11
**Method**: direct experiment against `workmux` 	in a disposable git repo, not
inspection of its source or documentation. Every finding below is observed
behaviour. The probe repo was removed afterwards; no tmux session was created.

The specification named two unconfirmed assumptions and made FR-006 through
FR-008 depend on the first. Both are now resolved, and a third question — the one
that justifies the feature's scope — was answered as a side effect.

---

## R-001: Does a failing `pre_remove` hook abort the removal?

**Decision**: Yes. Refusing the removal is available and is the mechanism FR-006
through FR-008 will use.

**Evidence**. A probe repo with `pre_remove: - echo "HOOK RAN"; exit 1`, a
worktree holding a gitignored spec, and removal attempted **with `--force`**:

```
$ workmux remove 99-probe --force
Running pre-remove commands...
HOOK RAN

Failed to remove 1 worktree(s):
  - 99-probe: Failed to remove worktree
Error: Some worktrees could not be removed
exit: 1

$ ls wt/99-probe/specs/99-probe/design.md
design            # survived
```

**Rationale**: this was the load-bearing assumption. Had it failed, FR-006
through FR-008 would have needed redesigning around a warning-only model, and the
feature would have been reduced to the skip predicate plus the install prompt.

**Beyond what was asked**: `--force` does **not** bypass the hook. It suppresses
the confirmation prompt and the uncommitted-changes check, but a failing
pre-remove hook still aborts. This matters — the refusal in FR-006 cannot be
accidentally overridden by the flag users reach for most.

**Alternatives considered**: warn-and-proceed (`|| echo`), rejected once the
abort was confirmed available — it reports the loss after it has happened, which
is the current behaviour with better wording.

---

## R-002: Does the uncommitted-changes guard count untracked files?

**Decision**: Yes. Work that version control can see is already protected by the
removal tool, and is correctly out of scope for this feature.

**Evidence**. Same repo, hook changed to succeed, one untracked non-ignored file
added:

```
$ git -C wt/99-probe status --porcelain
?? forgotten.py

$ workmux remove 99-probe
The following worktrees have uncommitted changes:
  - 99-probe
Error: Cannot remove worktrees with uncommitted changes. Use --force to override.
exit: 1

$ ls wt/99-probe/forgotten.py
wt/99-probe/forgotten.py          # survived
```

**Rationale**: confirms the scope boundary in the specification's Assumptions is
structural, not a deferral. It also shrinks the separately-tracked untracked-work
issue to `--force` and the merge cleanup path.

---

## R-003: What happens to gitignored artifacts on a clean removal?

**Decision**: They are destroyed silently. This is the loss the feature exists to
prevent, and it is now demonstrated rather than argued.

**Evidence**. Same repo, untracked file removed so only the gitignored spec
remains, hook succeeding, no `--force`:

```
$ git -C wt/99-probe status --porcelain
                                  # empty — the worktree reads CLEAN

$ workmux remove 99-probe
Running pre-remove commands...
HOOK RAN (success)
✓ Removed worktree '99-probe' and branch '99-probe'
exit: 0

$ ls wt/99-probe/specs/99-probe/design.md
No such file or directory         # destroyed
```

**Rationale**: the three findings compose into the feature's whole justification.

| At risk | Worktree reads | Guarded by |
|---|---|---|
| tracked modifications | dirty | removal tool (R-002) |
| untracked, not ignored | dirty | removal tool (R-002) |
| **gitignored artifacts** | **clean** | **nothing — until this feature (R-003)** |

A check built on version-control status cannot see artifacts deliberately kept
out of version control. The gap is structural, and the pre-remove hook (R-001) is
the only place it can be closed.

**Alternatives considered**: un-ignoring `specs/` so the existing guard covers
them — rejected, it reintroduces exactly the repo pollution the ignore rule
exists to prevent, and would commit every spec tree to the project's history.

---

## R-006: Does the manual escape route actually work?

**Decision**: Yes for the case that matters, with two caveats that belong in the
message rather than in a user's afternoon.

**Evidence**. A worktree holding only a gitignored spec:

```
$ git worktree remove wt/99-probe
exit: 0                           # removed; git's dirty check ignores ignored files
$ git branch --list 99-probe
  99-probe                        # branch survives — hence the second command
```

The same worktree with one untracked non-ignored file added:

```
$ git worktree remove wt/99-probe
fatal: 'wt/99-probe' contains modified or untracked files, use --force to delete it
exit: 128
```

**Rationale**: FR-008 requires the refusal message to name a route out. A route
that fails with `fatal:` for a reachable input is not a route. The untracked case
is reachable precisely because the uncommitted-changes guard (R-002) means anyone
who reached an archive failure with untracked files present used `--force` to get
there.

Bypassing the removal tool also skips its tmux cleanup, orphaning a window or
session. Harmless, and worth one clause — unexplained orphans read as breakage.

**Alternatives considered**: printing only `git worktree remove` and letting the
`--force` hint come from git's own error. Rejected: it arrives mid-teardown,
after the user has already been refused once, which is the worst moment to learn
a second command was incomplete.

---

## R-004: Command aliasing without duplicating the implementation

**Decision**: Register the former name as an additional, hidden command name that
dispatches to the same function.

**Rationale**: FR-019 requires the old name to keep working because project
configuration files are repo-local and copies predating the rename persist
indefinitely. R-001 makes this urgent rather than polite: an unknown command name
exits non-zero, and a non-zero pre-remove hook now **aborts the removal**. Without
the alias, every repo with an older configuration would find its worktrees
unremovable — a worse failure than the silent loss being fixed.

**Alternatives considered**:

- A second function delegating to the first — more surface, two docstrings to
  keep synchronised, no benefit.
- No alias, relying on reinstallation — rejected: nothing forces reinstallation,
  and the failure is severe and delayed.
- A deprecation warning on the old name — deferred. It prints on every teardown
  in repos that have not reinstalled, which is noise for a condition the health
  check (FR-020) already reports in one place, on demand.

---

## R-005: Where the "already asked" record is read from

**Decision**: Read it with the same walk that resolves the spec location — this
checkout's record, then the project's primary checkout — and write it to the
primary checkout.

**Rationale**: FR-016 requires the record to be found from any worktree. Setup
runs automatically in every newly created worktree, where the record file is
regenerated from scratch, so a local-only read would re-ask in each one. The
project already has exactly this walk for the spec location, and reusing it keeps
one rule rather than two that can diverge.

**Alternatives considered**: writing to whichever checkout is current — rejected,
the record file is gitignored and dies with the worktree, so the answer would
evaporate.

---

## Residual risk

None of the above is now unverified. One item is deliberately deferred rather
than resolved: whether the merge cleanup path applies the same uncommitted-changes
guard as removal. It does not affect any requirement here — the pre-remove hook
runs in both paths — and it belongs to the separately tracked untracked-work
issue.
