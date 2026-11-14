# Research: Move the old review scans into their spec folders

The spec and design left no `NEEDS CLARIFICATION` in the Technical Context.
Each entry below settles a decision the plan depends on, read from the code at
`cfeff0e`.

## R1. Reuse `store()` for another feature's folder

- **Decision**: Call `_spec_store.store(folder, folder.name, repo_root)` once
  per folder, passing the folder's own name as `branch`.
- **Rationale**: `store()` takes the spec dir's path, reads the layout from its
  parent, and uses `branch` in two places only: the `StoreResult` and the
  commit subject. `_subject` reads the issue key from `branch`, so passing the
  folder name gives `specs(412): store scans/clarify.md and 1 other`, which
  matches the `specs(<issue>):` commits already on `specs-trunk`. Passing this
  branch's name would file 45 commits under `specs(759)`.
- **Alternatives considered**: One commit for every folder and a single push.
  We didn't choose this because `store()` already commits by pathspec, merges,
  pushes, and holds the lock, and a second commit path would duplicate all of
  it for a temporary command. The design accepts a few minutes of per-folder
  pushes and names batching as the fallback if it's much slower.

## R2. Put the module in a new `wfctl/evidence/` package

- **Decision**: Create `wfctl/evidence/__init__.py` and
  `wfctl/evidence/_scan_move.py`. The `__init__.py` re-exports `move_scans` and
  the result types lazily, the way `wfctl/arch/__init__.py` does.
- **Rationale**: `check_imports.py` gives a module under a context's package
  directory that context's ownership with no baseline line. The domain page
  already names `evidence` as the package for evidence and derivation, so the
  directory adds no context-to-package pair. A flat `wfctl/_scan_move.py`
  fails the check as `unplaced-module` until a placement line is added, and a
  new baseline line waits for the user to run `wfctl arch approve-imports`.
  Imports from the package into `_spec_store` stay inside one context, and
  `_paths` and `_tracker` are shared.
- **Alternatives considered**: Adding the functions to `_spec_store.py`. We
  didn't choose this because the worktree guard imports that module before
  every shell command, and the command is temporary, so its removal should be
  one module and not an edit inside a 1,000-line one. A flat module with a
  baseline line. We didn't choose this because it needs a person's approval
  for a line #671 would then delete.
- **To verify in implement**: `python3 .github/scripts/check_imports.py` passes
  with no baseline change. If it reports the new package, stop and ask before
  adding a line, since that line needs `approve-imports`.

## R3. Read the folder name from a `Detail` line

- **Decision**: For each line matching `^-\s+Detail:\s+(\S+)`, strip any
  backticks from the path, split it on `/`, and take the first segment matching
  `^(<key_pattern>)-.+$`, rejecting `.` and `..`. The key pattern comes from
  `_tracker.load_key_pattern`.
- **Rationale**: This is the rule the user chose in clarify. It finds
  `412-clean-code-skill` in `/Users/…/wfctl-specs/412-clean-code-skill/spec.md`
  and `650-bob-pr-review-guard` in `/esw/rch/san5/aamarin/wfctl/specs/…`, and
  stops before `checklists/` in `…/checklists/analysis-report.md`. 16 of
  wfctl's review scans wrap the path in backticks, such as
  `` `<spec-root>/299-four-facts-in-the-payload/spec.md` ``, and pfms has
  several more. Without stripping them, a path that starts or ends at the
  folder would give a folder name with a backtick in it.
- **Why the first match is enough**: every `Detail` path in wfctl and pfms has
  exactly one segment of this shape, and it's the spec folder. pfms's paths
  were read for this, and they all name a folder under `pfms-specs/`, except
  three that say `$FEATURE_DIR/…` and fall back to the issue number (R4). The
  rule goes wrong only when a matching segment sits above the spec folder. For
  example, an in-repo `specs/` inside a worktree named `656-foo` gives
  `…/wt/656-foo/specs/649-bar/plan.md`, and the rule takes `656-foo`. Neither
  repository has a path like that, so we didn't add a stricter rule.
- **Why not `extract_issue_key` itself**: it accepts a bare key with no slug
  (`342`) and an underscore separator. A bare-key segment would match any
  number in a path, such as a year directory `2026`. The new regex requires
  the hyphen and a slug, and uses the same configured pattern.
- **Two `Detail` lines naming different folders**: the scan isn't placed, and
  the command reports both names. No wfctl scan does this, so it's a guard,
  not a case to handle.
- **Out of scope**: spec folders whose names carry no issue key. #760 tracks
  that, and this rule changes with it.

## R4. Fall back to the issue number

- **Decision**: When no `Detail` line names a folder, list the spec root's
  directories whose name starts with `<key>-`. Place the scan only when
  exactly one matches.
- **Rationale**: In wfctl, 4 scans name no folder in `Detail`:
  `121-clarify.md`, `121-analyze.md`, `188-clarify.md`, and `711-analyze.md`.
  Each matches one folder (`759-scan-names-its-folder`, Verified). In pfms, the
  three scans whose `Detail` says `$FEATURE_DIR/…` take this path. Zero or two
  or more matches are reported, never guessed.

## R5. Order, conflicts, and a rerun after a failed store

- **Decision**: Scans are processed in ascending issue order, using a natural
  sort on the key so `999` comes before `1000`. Within one issue the order is
  clarify, plan review, analyze. Each write compares against the destination
  as it is at that moment, so a scan written earlier in the same run counts as
  an existing file for a later one.
- **A destination that already holds what this scan would write counts as
  written.** For a plain or `--overwrite` write, that means the destination
  starts with the scan's text. For `--append`, it means the destination
  already contains the block the append would add. This is what makes a rerun
  safe without a rollback: a store that failed leaves the written files in the
  spec store, and the rerun finds them, writes nothing, and stores again.
  Without it, the rerun would report a conflict on the command's own output,
  or append the same sections twice.
- **Why "starts with" and not "identical"**: two scans can share one
  destination. In wfctl, `649-plan-review.md` is written to
  `649-design-checks-by-context/scans/plan-review.md`, and then
  `656-plan-review.md` is appended to it. If that folder's store fails, the
  rerun finds #649's text followed by #656's block. An identical-content check
  would report #649's scan as a conflict, and both printed remedies would
  damage the file: `--append` would add #649's sections a second time, and
  `--overwrite` would drop #656's. Checking that the destination starts with
  #649's text, and contains #656's block, finds both already there.
- **`--overwrite` never replaces a destination written earlier in the same
  run.** It's held as a conflict instead. With `--overwrite
  656-plan-review.md` on wfctl's first run, #649's plan review would otherwise
  be written and then replaced before any store, and `649-plan-review.md`
  would still be deleted, so #649's text would reach no stored folder. The
  rerun, after #649's scan is stored, overwrites as asked.
- A destination that starts with a scan's text and wasn't written by this
  command would also count as already there. That only happens when someone
  copied the scan by hand, and then the copy is already in place.
- **Alternatives considered**: Rolling back each written file when its
  folder's store fails. We didn't choose this because a store can fail after
  committing (`not_pushed`), where the scan is already in a local commit and a
  rollback would leave the store's working tree disagreeing with it.

## R6. When a scan counts as stored

- **Decision**: Delete a scan from the code repository when its write is
  `written`, `appended`, `overwritten`, or `already_there`, and its folder's
  `StoreResult.outcome` is `stored`, `already_stored`, or
  `committed_not_backed_up`. Every other case keeps the scan. The rule is per
  scan, not per folder, because one folder can hold a ready scan and a
  conflicted one. On wfctl's first run without `--append`, folder
  `649-design-checks-by-context` gets `649-plan-review.md` written and
  `656-plan-review.md` as a conflict. The store succeeds, and only #649's scan
  is deleted.
- **Rationale**: The first two mean the folder is on the upstream. The third
  means the store has no upstream and committed locally, which is what
  `store_no_upstream` allows and what `wfctl store specs` reports as exit 0.
  The scan is in a git commit, and the code repository's deletion is
  uncommitted, so nothing is lost. The table shows that row as `committed, not
  pushed`, so the user knows to push.
- **Before any write**, the command reads `layout(spec_root, repo_root)`.
  Anything other than `store` or `store_no_upstream` moves nothing and exits 1
  with the store's own wording (FR-010).

## R8. A failed store, and when to stop storing

- **Decision**: The Stored cell shows a short label per failed outcome, and
  the store's own `report_lines` for that failure print once under the table,
  so the user gets the same remedy lines `wfctl store specs` prints. Those
  lines tell the user to rerun `wfctl store specs`, which stores only the
  current branch's folder and never deletes a moved scan. So the command
  replaces `wfctl store specs` with `wfctl store scans` in each line before
  printing it. The labels:

  | Outcome | Cell |
  | --- | --- |
  | `not_pushed` | `✗ not pushed` |
  | `push_refused` | `✗ push refused` |
  | `conflict` | `✗ merge conflict` |
  | `merge_blocked_staged` | `✗ staged changes` |
  | `merge_refused` | `✗ merge refused` |
  | `merge_in_progress` | `✗ merge in progress` |
  | `locked` | `✗ locked` |
  | `git_failed` | `✗ git failed` |

- **Decision**: After the first failed outcome, whichever of the eight it is,
  the command stops storing (FR-014). The folders it hasn't stored yet show
  `– not tried` in the Stored cell, and their scans stay in the code
  repository. Their files are already written to the spec store, so the rerun
  finds them (R5) and stores them.
- **Rationale**: Almost every failed outcome describes the spec store or its
  remote, not the folder. An unreachable remote, a held lock, an unfinished
  merge, or a merge conflict fails every store after it the same way, since
  the store's own conflict text says a conflict stops every store. Without
  stopping, wfctl's 45 rows would each print the same failure, and with a
  remote that hangs, each would wait up to 60 seconds. Since only one failure
  happens per run, the output never has to group repeated failures.
- **Alternatives considered**: Stopping only on the outcomes that are always
  store-wide, and carrying on past the rest. We didn't choose this because the
  two groups aren't cleanly separable (`conflict` and `merge_refused` read as
  one folder's but block every store), and the rerun recovers the same way
  either way.

## R9. Recording the pushes

- **Decision**: For each folder whose outcome is `stored`, the command calls
  `record_outward_action(agent_dir, branch, "store-scans")`, the way `wfctl
  store specs` records `store-specs`. `branch` is the branch the command runs
  on, not the folder's name, since the event log belongs to that branch's
  session.
- **Rationale**: The command makes up to 45 pushes from a session that can be
  restarted partway. The event log is the only trace of a push a restarted
  session can read (`AGENTS.md`, Safety). `cli.py` makes the call, since the
  module returns results and doesn't write session state.

## R7. The append block

- **Decision**: The appended block is the old scan's text with its first line
  removed when that line is a `# ` heading, then stripped of leading blank
  lines, joined to the destination with one blank line.
- **Rationale**: `scan_reason` reads the whole file, so the appended
  `## Session` sections, each with its own `- Verdict:` line and coverage rows,
  count. A second `# ` title in the middle of the file would make the file read
  as two documents.
