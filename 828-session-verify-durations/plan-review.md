# Plan Review Report

Review state: completed
Review type: re-review

## Reviewed inputs

| Artifact | Content identity | Role |
| --- | --- | --- |
| plan.md | 1865d0233de4ea21c31ad5e3a489ac3dd2ef158c | technical strategy |
| spec.md | b180226476208e6269db317b7ca5afe58fac9fc4 | requirements |
| .specify/memory/constitution.md | absent | constitution |
| design.md | ff8eb09c3ce363c583f2b91f18a1a99a048cbb8f | design-record index |
| docs/architecture/design/828-verify-measures-each-child.md | b302abfb437fa21f1b4cd5cc8e7890c9e3eedc04 | design record (level 3, proposed) |
| docs/architecture/worktree-span-read-from-git.md | aaa1c76d3d5e7b415252ae10402f09d0c169a629 | architecture record (level 2, proposed), cited by spec and plan |
| docs/architecture/wfctl-runs-the-verification.md | 737e16e5908bbf17a961af5a8099e731a9707f8e | accepted architecture record, substitute gate |
| research.md | 005ab4c7bbbb8ec122ef72ad737df7d4a6c278ac | planning evidence |
| data-model.md | 32e85081e266edf0ff2ddb8f11f59cbc0cddc1f0 | planning artifact |
| contracts/wfctl-timings.md | 459297a95f2131df40ef177c3aaa1f32c83ec104 | contract |
| contracts/events.md | dbc1d76ddf0db7f45dda77fda63b225b6a3d8357 | contract |
| quickstart.md | 59dd191bc0096f14da051eaa4786dbf77f959857 | manual verification |
| scans/clarify.md | da9200942e9cbabd3812780cbc0b7f17bc3f6ffd | clarify scan |
| plan-review.plan.md | 41bca0f8cbecb5f794f60f45de28271de0b58b27 | base of this re-review |

## Review scope

- Re-review: the plan copy's identity equals the earlier report's `plan.md` row (`41bca0f…`), so the review started from the earlier report and the copy.
- Changed since the earlier report: `plan.md §Technical Context` (file count), `§Part 1 step 4` (interrupt grace), `§Part 2 step 2` (span on the catch-all path), `§Part 3 steps 2 to 5` (open worktree's branch, span de-duplication, typed reads), `§Validation`, and `§Risks 1`. Reviewed together with `§Ownership`, `§Source Code`, and the requirement trace rows that point into them.
- Inputs changed besides plan.md, each re-read in full and the whole of plan.md reviewed against it: `spec.md` (two new edge cases), `research.md` (R5 relative-path note, new R8 and R9), `data-model.md`, `contracts/wfctl-timings.md`, `contracts/events.md`. `design.md`, both records, the substitute gate record, `quickstart.md`, and `scans/clarify.md` match their earlier identities.
- Lenses: requirements and traceability, architecture and boundaries (with dependency and scope), adversarial implementation and verification (with verification and risk)
- Conditional lenses: security and reliability applied in its reliability half only. The change runs inside the worktree removal hook, which guards a destructive operation, and now adds a call on the hook's catch-all path, so whether the hook's outcome or output can change was reviewed. No trust boundary, secret, authorization, or sensitive data is added.
- Design records: 1 listed in design.md (`docs/architecture/design/828-verify-measures-each-child.md`). The level-2 record `docs/architecture/worktree-span-read-from-git.md` was read because the spec and plan cite it. Both are `proposed`.
- Constitution: absent. The five substitute gates the plan names are each `status: accepted`.
- Existing code inspected: `wfctl/cli.py` (`worktree_remove_cmd` in full, `_save_unsaved`), `wfctl/_paths.py` (`resolve_branch`, `resolve_agent_dir`, `project_state_dir`, `worktree_branches`), `tests/test_verify.py` (`test_interruption_writes_nothing_and_preserves_the_previous_record`), `tests/test_worktree_remove.py` (test list, the catch-all and state-dir tests).
- Probe: a throwaway repository with a linked worktree stopped mid-rebase (git 2.44, macOS). The admin folder's `HEAD` held a commit, `rebase-merge/head-name` held `refs/heads/feat`, `git branch --show-current` printed nothing, `git worktree list --porcelain` printed `detached`, and `commondir`'s modified time carried nanoseconds.
- Reviewers: the lenses above, run in sequence by one agent
- No `[NEEDS CLARIFICATION`, TODO, or placeholder marker stands in spec.md, plan.md, research.md, data-model.md, or the contracts.

## Summary

BLOCKER: 0
MAJOR: 0
MINOR: 5

No BLOCKER findings identified in this review. All seven earlier findings are fixed. The five new findings are small and sit in the parts the revision added: which branch a span is filed under when HEAD is detached, how the catch-all path behaves when the branch was never resolved, the key and resolution the span de-duplication compares on, a few typed-read cases the reader rules leave unplaced, and an assertion the rewritten interrupt test drops.

## Findings

### PR-001: Removals that pass through the hook's catch-all write no span, though FR-007 says one is owed

- Priority: MINOR
- Category: Requirement / Plan Mismatch
- Status: fixed
- Evidence:
  - `plan.md §Part 2 step 2.2`: the span is now also written in the catch-all `except (Exception, SystemExit)`
  - `spec.md §Edge Cases`: "If the removal hook fails partway with an unexpected error, it still lets the removal go ahead, so it still writes the span when it can read the creation time"
  - `data-model.md §Worktree span event validation 1` and `contracts/events.md §worktree-span` agree
- Finding: The plan and spec now agree that both paths that let the removal go ahead owe a span.
- Why it matters: The spec and plan no longer disagree on which path writes.
- Suggested response: Fixed by the revised `plan.md §Part 2 step 2`. A residual case is PR-008.
- Corroborated by: requirements and traceability, reliability

### PR-002: The interrupt path's test mechanism is unstated, and the existing interrupt test stops intercepting

- Priority: MINOR
- Category: Verification Gap
- Status: fixed
- Evidence:
  - `plan.md §Part 1 step 4`: the `try` starts after `Popen` returns, keeps the 0.25-second grace by polling `os.wait4(pid, os.WNOHANG)`, then kills and reaps
  - `plan.md §Validation tests/test_verify.py 3`: a real `sleep 30` child, `os.wait4` patched to raise on its first blocking call only, `os.kill(pid, 0)` checked for `ProcessLookupError`, and the old test named as replaced
- Finding: The injection, the observation, the grace period, and the test's status are all stated. The patched `wait4` raises once, so the non-blocking polls and the reaping call pass through.
- Why it matters: Two implementers would now write the same test.
- Suggested response: Fixed by the revised plan. A residual assertion gap is PR-012.
- Corroborated by: adversarial implementation and verification

### PR-003: SC-002 asks for macOS and Linux, and the plan tests Linux only

- Priority: MINOR
- Category: Verification Gap
- Status: fixed
- Evidence:
  - `plan.md §Validation tests/test_verify.py 4`: the 200 MB allocation runs on whichever platform runs the suite
  - `plan.md §Validation tests/test_verify.py 5`: `_peak_bytes` with `sys.platform` patched to `darwin` and `linux`
- Finding: Both conversions are now tested on every run.
- Why it matters: A regression in the darwin branch now fails CI.
- Suggested response: Fixed.
- Corroborated by: requirements and traceability

### PR-004: How an open worktree maps to its branch for the no-span exclusion is not named

- Priority: MINOR
- Category: Missing Information
- Status: fixed
- Evidence:
  - `research.md §R8`: the branch comes from the admin folder's `HEAD`, or from `rebase-merge/head-name` or `rebase-apply/head-name` when detached mid-rebase, and `worktree_branches` is named as the alternative not taken
  - `plan.md §Part 3 steps 2 and 3`, `data-model.md §Timings summary` "Open worktree's branch"
  - The probe confirmed both files and their contents for a worktree stopped mid-rebase
- Finding: One source, the admin folder, now serves both the open-now count and the exclusion.
- Why it matters: The two lines can no longer disagree about which worktrees are open.
- Suggested response: Fixed. The writer side of the same question is PR-009.
- Corroborated by: adversarial implementation

### PR-005: The reader rules cover a line that isn't JSON, not a JSON event with a missing or wrong-typed field

- Priority: MINOR
- Category: Risk / Failure Mode
- Status: fixed
- Evidence:
  - `plan.md §Part 3 step 5`: "Every field is read by type … No event line can make `wfctl timings` raise"
  - `contracts/wfctl-timings.md §Reading rules 6`, `plan.md §Validation tests/test_timings.py` "wrong-typed fields"
- Finding: A wrong-typed field is now treated as absent, with a fixture for it, and the command is stated never to raise on an event line.
- Why it matters: One odd line no longer breaks the summary.
- Suggested response: Fixed. Cases the rule leaves unplaced are PR-011.
- Corroborated by: adversarial implementation, reliability

### PR-006: A removal that fails after the hook, or a hook run by hand, leaves a span for a worktree that still exists

- Priority: MINOR
- Category: Assumption Challenge
- Status: fixed
- Evidence:
  - `spec.md §Edge Cases`: the hook runs before workmux removes the worktree, and `wfctl timings` drops a span matching an open worktree and keeps the latest of duplicates
  - `research.md §R9`, `plan.md §Part 3 step 4`, `data-model.md §Worktree span event validation 4`, `contracts/wfctl-timings.md §Reading rules 5`, `contracts/events.md §worktree-span`
- Finding: The assumption is now stated in the spec and handled at read time.
- Why it matters: The silent skew in the median is closed.
- Suggested response: Fixed. The comparison the fix relies on is PR-010.
- Corroborated by: reliability

### PR-007: Small inaccuracies in the plan's scope and an unverified relative-path read

- Priority: MINOR
- Category: Missing Information
- Status: fixed
- Evidence:
  - `plan.md §Technical Context`: four source files changed, named, and one added
  - `research.md §R5`: a relative `gitdir` resolves against the admin folder that holds it; `plan.md §Risks 1` points to it
- Finding: Both parts are corrected.
- Why it matters: The open-now line no longer depends on the current directory.
- Suggested response: Fixed.
- Corroborated by: architecture and boundaries (dependency)

### PR-008: The catch-all path's "nothing to read" case is narrower in the spec than in the plan, and its guard is unstated

- Priority: MINOR
- Category: Requirement / Plan Mismatch
- Status: open
- Evidence:
  - `plan.md §Part 2 step 2.2`: "If the failure came before `repo_root` and `branch` were resolved, there's no worktree to read, and the hook writes nothing"
  - `spec.md §Edge Cases`: on an unexpected error the hook "still writes the span when it can read the creation time"; `spec.md §FR-009` exempts only a refusal or an unreadable creation time
  - `wfctl/cli.py` `worktree_remove_cmd`: `repo_root` and `branch` are first bound inside the `try`, at the `Path(root).resolve()` and `resolve_branch(repo_root)` lines, so neither name exists in the `except` when the failure came first
- Finding: When `repo_root` resolved and `resolve_branch` raised, the worktree is there and its creation time is readable, but the plan writes nothing because there's no state folder to name. The spec's edge case and FR-009 don't name that cause. Separately, the plan doesn't say the two names are bound before the `try`. An implementer who reads them in the `except` without that gets a `NameError`, which the span's own `try` catches and turns into a spurious `⚠ couldn't record this worktree's lifetime` line on a path FR-010 says the feature mustn't change.
- Why it matters: `resolve_branch` falls back to a short SHA and rarely raises, so the uncovered case is narrow. The spurious line is the likelier effect, and it lands on the hook's error path, where its output is already being read for a fault.
- Suggested response: Say in step 2.2 that `repo_root` and `branch` start as `None` before the `try`, and that the catch-all skips the call silently when either is `None`. Correct the reason to "no state folder to write to", or add that cause to FR-009.
- Corroborated by: requirements and traceability, reliability

### PR-009: A span written from a detached worktree is filed under a short SHA, though the reader maps the same worktree to its branch

- Priority: MINOR
- Category: Risk / Failure Mode
- Status: open
- Evidence:
  - `plan.md §Part 2 step 3`: the state folder is `resolve_agent_dir(repo_root, branch)`, with `branch` from `resolve_branch`
  - `wfctl/_paths.py` `resolve_branch`: returns `git rev-parse --short HEAD` when `git branch --show-current` prints nothing; `resolve_agent_dir` creates the folder
  - The probe: a worktree stopped mid-rebase prints nothing for `--show-current`
  - `research.md §R8`: the reader goes out of its way to map a mid-rebase worktree to its branch through `head-name`
- Finding: A worktree removed mid-rebase, or one on a detached HEAD, writes its span into a new state folder named for a commit. `wfctl timings` then counts that folder as a branch, and the real branch shows on the no-span line with its span missing. The plan applies R8 to the reader only and says nothing about the writer.
- Why it matters: The skew is a branch counted twice and one span misattributed, and removal mid-rebase is rare. But the plan treats the same detached case two ways, and the reader's care in R8 is undone for exactly the worktrees it was written for. `_save_unsaved` already files its folder by the same `branch`, so this follows existing behavior rather than breaking it.
- Suggested response: State which the span follows. Either accept `resolve_branch`'s name as the hook already does for `unsaved/`, and say so under Risks, or resolve the branch by R8's rules for the span.
- Corroborated by: adversarial implementation

### PR-010: The span de-duplication's match key and time resolution are not pinned, and the spec and plan state different keys

- Priority: MINOR
- Category: Missing Information
- Status: open
- Evidence:
  - `spec.md §Edge Cases`: "keeps only the latest of several spans with the same creation time"
  - `plan.md §Part 3 step 4`, `research.md §R9`, `data-model.md §Worktree span event validation 4`, `contracts/wfctl-timings.md §Reading rules 5`: keep the latest among spans "with the same branch and `created`", and drop a span whose `created` "equals an open worktree's creation time", with no branch
  - `data-model.md §Worktree span event`: `created` is "UTC to the second"
  - The probe: `commondir`'s `st_mtime_ns` was 1795141091932831837, so the open worktree's creation time has sub-second precision unless it's cut down
- Finding: Three details are left open. The spec de-duplicates on creation time alone and the plan on branch and creation time. The open-worktree drop ignores the branch, so a removed worktree on one branch created in the same second as an open worktree on another, as happens when several worktrees are created by a script, loses its span. And nothing says the open worktree's mtime is cut to the second, or whether the writer floors or rounds, before the two are compared for equality.
- Why it matters: An implementer who compares the raw float mtime with the parsed timestamp never matches, so the drop never fires and PR-006 comes back silently. One who rounds on one side and floors on the other matches about half the time. The tests in `plan.md §Validation` would catch the first only if the fixture's worktree is created at a sub-second offset.
- Suggested response: Name one rule in all four places: both sides floored to the second in UTC, the duplicate key as branch and `created`, and the open-worktree drop on branch and `created` when R8 yields a branch, `created` alone when it doesn't. Bring the spec's edge case in line.
- Corroborated by: requirements and traceability, adversarial implementation

### PR-011: The typed-read rules leave a few cases unplaced, and the plan and contract differ on per-entry or per-figure

- Priority: MINOR
- Category: Missing Information
- Status: open
- Evidence:
  - `plan.md §Part 3 step 5`: a command entry with a wrong-typed `seconds` or `peak_bytes` "is left out of that command's figures"
  - `contracts/wfctl-timings.md §Reading rules 6`: such an entry "is left out of that figure"
  - `data-model.md §Worktree span event validation 3` and `contracts/wfctl-timings.md §Reading rules 4`: a span with reversed or unparseable times means "its branch counts on the no-span line"; `spec.md §FR-014` defines that line as branches with no span
- Finding: The plan reads as dropping the whole entry and the contract as dropping one field, and neither says whether the entry still counts in the `runs` column. Three cases have no stated home: a command entry whose `command` isn't a string, a `commands` value that isn't a list, and an event whose `ts` won't parse, which decides the window. And a branch with one good span and one bad one is put on the no-span line by the rule as written while also contributing a span.
- Why it matters: The no-raise guarantee holds whatever the choice, so this is counts differing by a few between implementations, not a wrong verdict.
- Suggested response: Pick per-figure or per-entry in both places and say what `runs` counts. Add one line each for a non-string `command`, a non-list `commands`, and an unparseable `ts`. Say the no-span line counts a branch only when it has no valid span in the window.
- Corroborated by: adversarial implementation

### PR-012: The rewritten interrupt test drops the existing test's check that `verify.json` is left as it was

- Priority: MINOR
- Category: Verification Gap
- Status: open
- Evidence:
  - `tests/test_verify.py` `test_interruption_writes_nothing_and_preserves_the_previous_record`: writes a record first and asserts `record_path(...).read_bytes() == before` after the interrupt; its docstring says "A record that exists is proof a run completed"
  - `plan.md §Validation tests/test_verify.py 3`: checks the child is gone and that no `verify` event was written, and "replaces" the old test
  - `spec.md §FR-005`: `verify.json` MUST NOT change; `spec.md §Edge Cases`: an interrupted verify writes no event "as today"
  - `plan.md §Source Code`: the tree's comments still say `test_verify.py` covers "Linux bytes" and `test_worktree_remove.py` doesn't mention the catch-all span
- Finding: The replacement keeps the event half of the old test and loses the record half. Nothing else in the plan checks that an interrupt leaves an existing `verify.json` untouched.
- Why it matters: Part 1 rewrites the loop that sits between the commands and `write_record`. A reordering that writes the record before re-raising would pass the new test.
- Suggested response: Keep the old test's `before`/after assertion in the new one. Bring the two tree comments in line with `§Validation`.
- Corroborated by: adversarial implementation and verification

## Requirement-to-plan trace

| Requirement / criterion | Plan location | Review note |
| --- | --- | --- |
| FR-001 | plan.md §Part 1 steps 1 and 5 | covered |
| FR-002 | plan.md §Part 1 step 1, §Ownership | covered by the design record's probe |
| FR-003 | plan.md §Technical Context constraints; design record §Decision | covered |
| FR-004 | plan.md §Part 1 step 2 | covered |
| FR-005 | plan.md §Part 1 step 5, §Constitution Check | covered; PR-012 for the interrupt path |
| FR-006 | plan.md §Part 1 step 4, §Validation test 3 | covered |
| FR-007 | plan.md §Part 2 step 2 | covered; PR-008, PR-009 |
| FR-008 | plan.md §Part 2 step 1, research R1 | covered |
| FR-009 | plan.md §Part 2 step 2 | covered; PR-008 names a third no-span cause |
| FR-010 | plan.md §Part 2 step 2 | covered; PR-008 |
| FR-011 | plan.md §Part 3 step 1, research R3 | covered |
| FR-012 | contracts/wfctl-timings.md §Output, plan.md §Part 3 step 4 | covered; PR-010 |
| FR-013 | plan.md §Part 3 step 2, research R5 | covered |
| FR-014 | plan.md §Part 3 step 3, research R6 and R8 | covered; PR-009, PR-011 |
| FR-015 | data-model.md §Timings summary | covered |
| FR-016 | contracts/wfctl-timings.md §Reading rules 2 and 6 | covered |
| FR-017 | contracts/wfctl-timings.md §Reading rules 3 | covered |
| FR-018 | plan.md §Constitution Check, research R4 | covered |
| FR-019 | contracts/wfctl-timings.md §Reading rules 7 | covered |
| FR-020 | contracts/wfctl-timings.md §Output | covered |
| FR-021 | plan.md §Part 3 step 6, data-model.md §Timings summary | covered; PR-011 for an unparseable `ts` |
| FR-022 | contracts/wfctl-timings.md §Output | covered |
| SC-001 | quickstart.md step 1 | manual only, as the spec's validation strategy says |
| SC-002 | plan.md §Validation tests 4 and 5 | covered |
| SC-003 | quickstart.md step 3 | manual, run by the user |
| SC-004 | plan.md §Validation, research R4 | covered |
| SC-005 | contracts/wfctl-timings.md §Output | covered by inspection of the output shape |
| Edge: interrupt leaves no child | plan.md §Part 1 step 4 | covered |
| Edge: reversed span | data-model.md §Worktree span validation 3 | covered; PR-011 for a branch with another span |
| Edge: `--since 3w` refused | contracts/wfctl-timings.md §Exit codes | covered |
| Edge: command text changes | data-model.md §Timings summary, per command | covered |
| Edge: metadata rewritten after creation | research R1, plan.md §Risks 1 | covered for git 2.44; relative paths named |
| Edge: removal fails after the hook | plan.md §Part 3 step 4, research R9 | covered; PR-010 |
| Edge: unexpected error in the hook | plan.md §Part 2 step 2.2 | covered; PR-008 |

## Assumptions challenged

- A span's state folder names the branch. Implicit in `plan.md §Part 2 step 3`, and not true for a detached worktree, where `resolve_branch` returns a short SHA (PR-009).
- "Equals" between a span's `created` and an open worktree's creation time is well defined. The two come from the same file at different resolutions, and neither the rounding nor the key is stated (PR-010).
- Two worktrees on one branch can't share a creation second. Stated in `research.md §R9`, true for git without `--force`, and it covers the duplicate key only, not the open-worktree drop that ignores the branch (PR-010).
- Both records are `proposed`. `plan.md §Risks 3` says implementation waits on the user's decision on them. Tasks can be written against them, but a decision against either would reopen Part 1 or Part 2.

## Reviewer disagreement

- None identified.

## Strengths worth preserving

- `plan.md §Ownership` still names one place for each value and why the other side can't compute it, which keeps `wfctl timings` free of stored state.
- The catch-all span call keeps its own `try` and sits after the warning, so the hook's outcome on that path can't change; refusals raise `typer.Exit` before either call, and `_save_unsaved`'s own failures stop the removal through `typer.Exit` too.
- The new interrupt test patches only the first blocking `wait4`, which leaves the grace polls and the reaping call real, so the kill-then-reap path is actually exercised.
- R8 reads the branch from files R5 already lists, so the open-now line still needs one git call, not one per worktree, and the mid-rebase case it handles was confirmed by the probe.
- R9 fixes the stale-span case at read time instead of asking workmux for a post-removal hook.

## Source freshness

This review describes only the content identities listed under `## Reviewed inputs`. When `spec.md`, `plan.md`, a binding design record, or a material planning artifact changes, this report no longer describes the current plan, and a new review is needed before it counts as current evidence.
