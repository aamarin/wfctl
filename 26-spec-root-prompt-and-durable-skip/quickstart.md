# Quickstart: verifying this feature by hand

Every step below was executed during Phase 0 research against a disposable repo.
Reproduce it the same way — never against a repo whose worktrees you care about.

## Setup

```bash
cd "$(mktemp -d)" && mkdir probe && cd probe
git init -q . && printf 'specs/\n' > .gitignore
cat > .workmux.yaml <<'YAML'
main_branch: main
base_branch: main
worktree_dir: wt
worktree_naming: full
pre_remove:
  - if command -v wfctl >/dev/null; then wfctl archive-specs "$WM_WORKTREE_PATH" "$WM_HANDLE"
    else echo "⚠ wfctl not on PATH — specs in $WM_WORKTREE_PATH not archived"; fi
YAML
git add -A && git commit -qm init && git branch -M main
git worktree add -q wt/99-probe -b 99-probe
mkdir -p wt/99-probe/specs/99-probe
printf 'design\n' > wt/99-probe/specs/99-probe/design.md
```

## 1. The loss this feature prevents (baseline, before implementing)

```bash
git -C wt/99-probe status --porcelain     # empty — reads CLEAN
workmux remove 99-probe
```

Expected today: removal succeeds, exit 0, `design.md` gone. A gitignored artifact
is invisible to any version-control-based check, so nothing stops this. Confirmed
in R-003.

## 2. Default layout still archives everything (FR-001, SC-002)

With no `spec_root` recorded, recreate the worktree and remove it. The archive
directory under the state dir must contain the same numbered set as before the
change. This is the regression that matters most — most repos are here.

## 3. Durable location is skipped (FR-002, SC-001)

```bash
wfctl spec-root /tmp/probe-specs
mkdir -p /tmp/probe-specs/99-probe && printf 'design\n' > /tmp/probe-specs/99-probe/design.md
workmux remove 99-probe
```

Expected:

```
✓ spec dir is durable (/tmp/probe-specs/99-probe) — nothing was at risk, nothing archived
```

Then confirm both: no archive directory was created, and
`/tmp/probe-specs/99-probe/design.md` is untouched in place.

## 4. Containment, not the setting (FR-003)

Point `spec_root` at a path that resolves back **inside** the worktree. The specs
must still be archived — the test is where the files are, never whether a setting
exists. This is the case an on/off flag gets wrong.

## 5. Failure refuses the removal (FR-006, FR-008, SC-003)

Make preservation fail — an unwritable state directory is the easiest — with
at-risk artifacts present.

```bash
workmux remove 99-probe        # expect: non-zero, worktree survives
ls wt/99-probe/specs/99-probe/design.md
```

The message must name the cause, the retry, and the manual removal route. Then
repeat with `--force`: **it must still refuse.** `--force` suppresses the
confirmation prompt and the uncommitted-changes check, but not the hook (R-001).

## 5a. A failed run leaves the previous result intact (FR-023, SC-008)

Archive once successfully. Then edit a spec file, make preservation fail, and run
teardown again.

```bash
ls "$(wfctl state-dir)"
```

Expected: `archive/` still holds the **complete** earlier result with its
`README.md`, and there is no partial directory of any kind. Then free the space
and retry:

```bash
workmux remove 99-probe        # now succeeds
ls "$(wfctl state-dir)"
```

Expected: exactly one `archive/` (complete, current) and one `archive-<stamp>/`
(complete, previous). No third directory from the failed attempt.

Before this change the failed run left an unindexed partial at `archive/`, and
the retry pushed it into the timestamped pool where nothing distinguished it from
real history.

## 5b. The tool-absent branch proceeds (FR-009)

The one path that still lets a removal complete after artifacts went unarchived.
It exists so a machine that never had `wfctl` does not end up with worktrees it
cannot remove — which makes it worth confirming, not worth assuming.

```bash
env PATH=/usr/bin:/bin workmux remove 99-probe        # wfctl not on PATH
```

Expected: the hook prints

```
⚠ wfctl not on PATH — specs in <path> not archived
```

and the removal **proceeds**, exit 0. Contrast with step 5, where the tool is
present and failing, and the removal is refused. Both outcomes are correct; the
difference is whether anything could have been preserved.

## 6. Backward compatibility (FR-019, SC-007)

Restore the old hook line — `wfctl archive-story "$WM_WORKTREE_PATH" "$WM_HANDLE"`
— and remove a worktree. It must behave identically. Failure here means aborted
removals in every repo carrying an older configuration, which is worse than the
bug being fixed.

Then `wfctl doctor` on that repo must report the stale hook, without changing its
exit code (FR-020).

## 7. Asked once (FR-015, FR-016, SC-005)

```bash
wfctl install-skills            # interactive: expect the question
wfctl install-skills            # expect: silent
wfctl install-skills --yes      # expect: silent, first run too
```

Then, from a **worktree** of a project answered in its primary checkout, run
`install-skills` interactively — it must stay silent. That is the case a
local-only read gets wrong (R-005).

## 8. The default is indistinguishable (FR-012, SC-006)

Answer option 1, then confirm `wfctl spec-root` reports
`default (no spec_root recorded)` and that `feature-paths` resolves exactly as it
did before the question existed.

## Cleanup

```bash
workmux remove 99-probe --force 2>/dev/null
cd / && rm -rf "$OLDPWD" /tmp/probe-specs
tmux ls | grep probe          # expect nothing
```

## Automated equivalents

Steps 2 to 7 each map to a test named in the specification's Validation Strategy.
Step 1 has no automated form — it documents the pre-change behaviour and stops
being reproducible once the feature ships.
