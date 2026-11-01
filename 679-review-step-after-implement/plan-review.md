# Plan Review Report

Review state: completed
Review type: re-review

## Reviewed inputs

| Artifact | Content identity | Role |
| --- | --- | --- |
| plan.md | a843ecf24f1f90a3dc68e5facd2a7a76d24bd434 | technical strategy |
| spec.md | f361e22239992c19c69256d8650b64f0d83eb0cb | requirements |
| .specify/memory/constitution.md | absent | constitution |
| design.md | baa914c455c5faea16f4e08d8a7efea379901b26 | design-record index |
| docs/architecture/design/679-review-is-its-own-step.md | 67753ae019ea66ade8dbedb4cc81217f72e9ba51 | design record |
| docs/architecture/design/679-no-spec-skips-spec-rows.md | b97f1ba3a4e2abe30373155a8674108d16916787 | design record |
| docs/architecture/review-step-reads-guard-state.md | 94ab0f6dbcfea44ae996a29e81922802fa25efec | level-2 record |
| docs/architecture/every-change-answers-spec-question.md | f5c2177ef30ae80b16043c1ecfc733f9102764f9 | level-2 record |
| docs/architecture/design/498-the-fix-line-travels-with-the-reason.md | bda01a0bf2a62ded2aa18ba6f33e2c2b0f34320e | related design record (remedy field) |
| research.md | e8b57079ccf7965671ed01c808a89e08746d28f9 | planning evidence |
| data-model.md | d6ccfe862d2e77d6c45920510f25470b4931cebe | planning evidence |
| contracts/cli.md | ebc4a49b51a1f63c4e42cc6977bedee2384cad3f | planning evidence |
| quickstart.md | 32368240bb1e255abb05557bd2a4f4fea8271ac7 | planning evidence |
| AGENTS.md | 5090e1cb455f4d0293a1938504fae5d200f59ae7 | substitute gates |
| plan-review.plan.md | 24def0b7e215005de4c46763809a60f63b4280e1 | base of this re-review |

## Review scope

- Re-review: the plan copy's identity equals the earlier report's `plan.md` row, so this run diffed the copy against `plan.md`.
- Changed in `plan.md`: `§Phase A` step 1 (the keyword `with_caps` is now `for_status`, and both `since` and `capped` are computed only behind it; `since` is redefined as the newest of the last reviewed commit and the signed-off commit still on the branch; every git read in that calculation is best-effort), `§Phase A` step 3 (the `capped` test names the new keyword, and the `since` tests add a merge from the trunk, a pruned last reviewed commit, and the flag left off), and `§Phase B` step 1 (`build_evidence` passes `for_status=True`). These were reviewed together with the sections that refer to them: `§Phase A` step 2 (the guard's call), `§Phase B` step 1 (the error reading and `display`), `§Phase B` step 4 (the stall digest hashes `ev.review`), the `HeadCoverage` type and its comments, Technical Context, and the requirement trace.
- Inputs that changed since the earlier report, each re-read in full with the whole of `plan.md` reviewed against it: `research.md` (R11's rationale now gives the new `since` rule and why the first-parent rule was dropped) and `data-model.md` (the `since` and `capped` rows, and the group state note under Review step states). Every other row matches its file.
- Checked for leftover wording: no input still describes `since` as the first parent of the oldest unreviewed commit, and none still says `with_caps`. The only hits are this report's earlier text and `plan-review.plan.md`, which this run replaces, and the committed scan file `docs/architecture/scans/679-plan-review.md`, whose earlier `## Review` section records what that review found and is never edited.
- `tasks.md` now exists in the feature directory. It isn't an input to this review and wasn't reviewed. A search for the old wording found none there, and its T004 to T007 and T016 use `for_status` and the new rule.
- Lenses: requirements and traceability, architecture and boundaries, adversarial implementation and verification.
- Conditional lenses: security and reliability applied, for the same reason as the earlier reviews: the feature sits on the line between what the agent may claim and what only `wfctl review check`, a person's sign-off, or the PR guard may decide. This revision takes the new reads out of the guard's path, which keeps the guard's refusals as they are today.
- The constitution is absent. The plan substitutes gates from `AGENTS.md` and the accepted records.
- Existing code inspected for the changed claims: `wfctl/_review.py` (`_git`, `is_commit`, `present_tips`, `is_under`, `_is_ancestor`, `commit_range`, `trunk_rounds`, `signed_off`, `coverage_from_state`, `unreviewed`) and `wfctl/_review_gate.py` (`refusal`, `_judge`).
- Reviewers: the lenses above, run in sequence by one agent in a fresh context.

## Summary

BLOCKER: 0
MAJOR: 0
MINOR: 0

No BLOCKER findings identified in this review. Both earlier open findings, PR-027 and PR-028, are fixed, and this run found nothing new. The guard now calls without `for_status`, so it makes exactly the calls `_judge` makes today and none of the reads `since` needs. The new `since` rule never comes from the oldest unreviewed commit, so a root commit, a clean merge, and a merged branch's side no longer move it, and a pruned commit is filtered by the existence check before any ancestry read. Two cases the rule handles in a way worth knowing are under Assumptions challenged.

## Findings

### PR-001: The review row routes an unattended run into a panel that the round cap refuses

- Priority: MAJOR
- Category: Risk / Failure Mode
- Status: fixed
- Evidence:
  - `plan.md §Phase A` step 1: `capped`, computed with the count and cap `review start` uses.
  - `plan.md §Phase B` step 1, reading 3: a capped group blocks the step with the sign-off remedy.
- Finding: The capped state has its own blocking reading, unchanged in substance by this revision.
- Why it matters: Fixed.
- Suggested response: Fixed in an earlier revision.
- Corroborated by: adversarial implementation, architecture and boundaries

### PR-002: User Story 1 scenario 5 promises agreement with the whole guard, and the shared function covers only the review half

- Priority: MAJOR
- Category: Requirement / Plan Mismatch
- Status: fixed
- Evidence:
  - `spec.md §User Story 1` scenario 5 and `contracts/cli.md §The worktree guard`: both scope the claim to unreviewed commits.
- Finding: Still fixed.
- Why it matters: Fixed.
- Suggested response: Fixed in an earlier revision.
- Corroborated by: requirements and traceability

### PR-003: The status payload contract can't record story complete or a filled `no_spec` with today's fixture states

- Priority: MAJOR
- Category: Verification Gap
- Status: fixed
- Evidence:
  - `plan.md §Phase B` step 5: the `no_spec` fixture state and the `payload_of` key.
- Finding: Still fixed, and the step no longer repeats the no-trunk premise.
- Why it matters: Fixed.
- Suggested response: Fixed in an earlier revision.
- Corroborated by: adversarial implementation and verification

### PR-004: Skipping `_pass_states` on a spec row drops every pass from the payload

- Priority: MAJOR
- Category: Architecture / Decision Conflict
- Status: fixed
- Evidence:
  - `plan.md §Phase C` step 3: passes come from `_pass_states(name, passes, None, "skipped", claims)`.
- Finding: Still fixed.
- Why it matters: Fixed.
- Suggested response: Fixed in an earlier revision.
- Corroborated by: architecture and boundaries

### PR-005: The HEAD read sits outside the function that promises never to raise

- Priority: MINOR
- Category: Risk / Failure Mode
- Status: fixed
- Evidence:
  - `plan.md §Phase A` step 1, call 1: `head_commit` runs inside `pending_at_head`.
- Finding: Still fixed. PR-022 covers what that error path now does to the `spec_tree` tests.
- Why it matters: Fixed.
- Suggested response: Fixed in an earlier revision.
- Corroborated by: adversarial implementation

### PR-006: `check-body` requires a "no spec" reason the pipeline is ignoring

- Priority: MINOR
- Category: Boundary / Ownership Concern
- Status: fixed
- Evidence:
  - `plan.md §Phase C` step 1: `spec_in_effect` is shared by `reasons` and `build_evidence`.
- Finding: Still fixed.
- Why it matters: Fixed.
- Suggested response: Fixed in an earlier revision.
- Corroborated by: architecture and boundaries

### PR-007: The stall digest can't see progress at the review step

- Priority: MINOR
- Category: Missing Information
- Status: fixed
- Evidence:
  - `plan.md §Phase B` step 4 and `research.md §R10`.
- Finding: Still fixed.
- Why it matters: Fixed.
- Suggested response: Fixed in an earlier revision.
- Corroborated by: adversarial implementation

### PR-008: The "artifacts written" fact reads unmet forever on a no-spec branch

- Priority: MINOR
- Category: Requirement / Plan Mismatch
- Status: fixed
- Evidence:
  - `plan.md §Phase C` step 2: the fact reads `n/a` with `no spec recorded`.
- Finding: Still fixed.
- Why it matters: Fixed.
- Suggested response: Fixed in an earlier revision.
- Corroborated by: requirements and traceability

### PR-009: Two level-1 strings from `design.md` don't reach the spec or plan

- Priority: MINOR
- Category: Requirement / Plan Mismatch
- Status: fixed
- Evidence:
  - `research.md §R11`, `design.md §What the user sees`, `contracts/cli.md §wfctl status`, and `plan.md §Phase B` step 1 now agree on `not reviewed yet (N commits)` and `N commits unreviewed since <short sha>`.
- Finding: Still fixed, with the count added in all four places.
- Why it matters: Fixed.
- Suggested response: Fixed in an earlier revision.
- Corroborated by: requirements and traceability

### PR-010: The spec's clarification and FR-017 disagree on where the reason must appear

- Priority: MINOR
- Category: Requirement / Plan Mismatch
- Status: fixed
- Evidence:
  - `spec.md §Clarifications`, first answer.
- Finding: Still fixed.
- Why it matters: Fixed.
- Suggested response: Fixed in an earlier revision.
- Corroborated by: requirements and traceability

### PR-011: SC-004 has no measurement step

- Priority: MINOR
- Category: Verification Gap
- Status: fixed
- Evidence:
  - `plan.md §Phase D` step 8 and `quickstart.md §1` step 5.
- Finding: Still fixed.
- Why it matters: Fixed.
- Suggested response: Fixed in an earlier revision.
- Corroborated by: adversarial verification

### PR-012: The import-cycle contingency can't happen

- Priority: MINOR
- Category: Assumption Challenge
- Status: fixed
- Evidence:
  - `plan.md §Phase A` step 1 and `research.md §R9`.
- Finding: Still fixed.
- Why it matters: Fixed.
- Suggested response: Fixed in an earlier revision.
- Corroborated by: architecture and boundaries

### PR-013: A config error routes to the panel with no remedy

- Priority: MINOR
- Category: Missing Information
- Status: fixed
- Evidence:
  - `plan.md §Phase A` step 1, error 1, and `§Phase B` step 1, reading 2.
- Finding: Still fixed. PR-023 covers the remedy's wording for one kind of config problem.
- Why it matters: Fixed.
- Suggested response: Fixed in an earlier revision.
- Corroborated by: adversarial implementation

### PR-014: `steps.review` becomes a valid declaration in `wfctl.json`

- Priority: MINOR
- Category: Scope Expansion
- Status: fixed
- Evidence:
  - `plan.md §Phase B` step 3 and `contracts/cli.md §wfctl check config`.
- Finding: Still fixed.
- Why it matters: Fixed.
- Suggested response: Fixed in an earlier revision.
- Corroborated by: architecture and boundaries

### PR-015: The no-spec design record contradicts its own decision about the reason

- Priority: MINOR
- Category: Architecture / Decision Conflict
- Status: fixed
- Evidence:
  - `docs/architecture/design/679-no-spec-skips-spec-rows.md`, unchanged since the fix.
- Finding: Still fixed.
- Why it matters: Fixed.
- Suggested response: Fixed in an earlier revision.
- Corroborated by: requirements and traceability

### PR-016: Computing `capped` inside the shared function adds a write and extra git work to the guard, which ignores the result

- Priority: MINOR
- Category: Risk / Failure Mode
- Status: fixed
- Evidence:
  - `plan.md §Phase A` step 1: `capped` is computed only with `for_status=True` (named `with_caps` when this was fixed), which status passes and the guard leaves off, and the tally folder is read through `resolve_round_dir(repo_root, branch, create=False)`.
  - `wfctl/_paths.py` `resolve_round_dir`: takes `create: bool = True` and passes it to `resolve_agent_dir` on both fallback paths, so `create=False` creates nothing on any path.
  - `plan.md §Phase A` step 3: a test that without `for_status` the tally folder isn't created.
- Finding: The guard no longer pays for the cap read, and status no longer writes the tally folder.
- Why it matters: Fixed.
- Suggested response: Fixed by `plan.md §Phase A` step 1.
- Corroborated by: architecture and boundaries, adversarial implementation

### PR-017: The error reading's remedy has to be recovered from the error text, and the trunk remedy doesn't fix the trunk error

- Priority: MINOR
- Category: Missing Information
- Status: fixed
- Evidence:
  - `plan.md §Phase A` step 1: `HeadCoverage.remedy` is set where the error is caught. A config problem gets a remedy, and a `ReviewError` gets none.
  - `research.md §R12`: the `git fetch origin` remedy is gone, and the reason for not matching message text cites `498-the-fix-line-travels-with-the-reason.md`.
  - `wfctl/_review.py` `TRUNK_MESSAGE` and `review_trunk`: the trunk errors name their fix in the message.
- Finding: The reader no longer matches text, and the wrong remedy is gone.
- Why it matters: Fixed.
- Suggested response: Fixed by `plan.md §Phase A` step 1 and `research.md §R12`.
- Corroborated by: adversarial implementation, architecture and boundaries

### PR-018: Fixtures without an `origin` don't hit a no-trunk error; the trunk falls back to the local `main`

- Priority: MINOR
- Category: Assumption Challenge
- Status: fixed
- Evidence:
  - `plan.md §Phase B` step 5 and step 7: no `origin`, no sign-off fixture, no `reviewed_at_head` helper, and scenario tests build a feature branch with its own commits.
  - `wfctl/_paths.py` `trunk_branch`: falls back to the first local `main`, `master`, or `dev`.
  - `wfctl/_contract.py` `_init_throwaway_repo`: one commit on the default branch, then `contract-fixture` checked out at the same commit. `tests/conftest.py` `storyctl_dir`: two commits on the default branch, which stays checked out, with `WFCTL_BRANCH=418-storyctl`.
  - `wfctl/_review.py` `trunk_refs` and `commit_range`: the trunk resolves to `refs/heads/<default>`, which differs from the branch name, and `merge-base HEAD <trunk>` is HEAD, so the range is empty.
- Finding: Verified for the two git-backed fixture shapes: `pending` is empty, and `review` reads done. The revision's statement is accurate for them. PR-022 covers the fixture shape it doesn't cover.
- Why it matters: Fixed.
- Suggested response: Fixed by `plan.md §Phase B` steps 5 and 7.
- Corroborated by: adversarial implementation and verification

### PR-019: `not reviewed yet` drops the count FR-005 requires, and FR-005 still calls the annotation a reason

- Priority: MINOR
- Category: Requirement / Plan Mismatch
- Status: fixed
- Evidence:
  - `spec.md §FR-005`: now says the status line names each group and how many commits it has, and carries no reason.
  - `plan.md §Phase B` step 1, `display`: `not reviewed yet (N commits)`, and a signed-off branch with no completed run counts from the signed-off commit.
- Finding: The spec and plan agree, and the signed-off case is decided.
- Why it matters: Fixed. PR-025 raises a separate case `since` gets wrong.
- Suggested response: Fixed by the FR-005 edit and the display rule.
- Corroborated by: requirements and traceability

### PR-020: The capped example in `contracts/cli.md` shows the reason on the step line, and the console prints the display there

- Priority: MINOR
- Category: Verification Gap
- Status: fixed
- Evidence:
  - `plan.md §Phase B` step 1, reading 3: no display, so the step line shows the reason.
  - `data-model.md §Review step states`: the capped row's annotation is the reason.
  - `contracts/cli.md §wfctl status`: the capped example shows the reason on the step line.
- Finding: The three artifacts agree.
- Why it matters: Fixed.
- Suggested response: Fixed by `plan.md §Phase B` step 1.
- Corroborated by: adversarial verification

### PR-021: SC-004 is measured on this branch, not on the longest open branch it names

- Priority: MINOR
- Category: Requirement / Plan Mismatch
- Status: fixed
- Evidence:
  - `spec.md §SC-004`: now names this branch once implement is done, and asks for the commit count.
  - `plan.md §Technical Context`, `§Phase D` step 8, and `quickstart.md §1` step 5: the same branch, with `git rev-list --count origin/main..HEAD` recorded.
- Finding: The criterion and its measurement match.
- Why it matters: Fixed.
- Suggested response: Fixed by the SC-004 edit.
- Corroborated by: requirements and traceability

### PR-022: The story-complete tests built on `spec_tree` have no git repository, so the review row reads an error there and they stop passing

- Priority: MAJOR
- Category: Verification Gap
- Status: fixed
- Evidence:
  - `plan.md §Phase B` step 7: names the four tests whose repository root is `tmp_path`, says each calls `git_repo(tmp_path)` and sets `WFCTL_BRANCH` with `monkeypatch`, and explains why a sign-off can't fix them. The grep step is back. Project Structure lists the four files.
  - `tests/conftest.py` `git_repo`: `init_git` plus one commit on the default branch, which stays checked out.
  - `wfctl/_paths.py` `trunk_branch`: with no `wfctl.json` trunk, no `origin/HEAD`, and no bare layout, it returns the first local `main`, `master`, or `dev`. `resolve_branch`: returns `WFCTL_BRANCH` when it's set.
  - `wfctl/_review.py` `trunk_refs`: refuses a trunk with the same name as the branch under review, which is why the plan needs `WFCTL_BRANCH`. With it set, the trunk is `refs/heads/<default>`, and `commit_range` takes `merge-base HEAD <trunk>`, which is HEAD, so the range is empty.
  - The experiment under `## Review scope`: all four tests pass with the review calls returning no commits, under both `main` and `master` as the default branch.
- Finding: The plan's response works as written. The git repository doesn't move any other reader in these tests off its current answer, since `current` and `next_command` stayed `None` in all four. `spec_tree` itself is unchanged, so its docstring stays true.
- Why it matters: Fixed.
- Suggested response: Fixed by `plan.md §Phase B` step 7.
- Corroborated by: adversarial implementation and verification

### PR-023: The config remedy always names the trunk, and a config problem can come from the branch's own `wfctl.json`

- Priority: MINOR
- Category: Risk / Failure Mode
- Status: fixed
- Evidence:
  - `plan.md §Phase A` step 1, error 1: the remedy is `fix review in the wfctl.json the error names, then run wfctl check config`, and the plan explains that each problem already names its file.
  - `wfctl/_review_config.py` `_parse_at`: labels each problem `wfctl.json at <ref>`, with a head commit shortened to seven characters, so the error does name the file.
  - `research.md §R12` and `contracts/cli.md §wfctl status`: the same remedy, and an example naming a branch commit.
  - `plan.md §Phase A` step 3: a test for a problem on each side, with the same remedy.
- Finding: The remedy now points at whichever file the error names.
- Why it matters: Fixed.
- Suggested response: Fixed by `plan.md §Phase A` step 1.
- Corroborated by: adversarial implementation

### PR-024: The guard's record check needs the trunk ref, and the shared function doesn't return it

- Priority: MINOR
- Category: Missing Information
- Status: fixed
- Evidence:
  - `plan.md §Phase A` step 1: `HeadCoverage.trunk_ref`, the ref call 2 resolved, `None` if it failed.
  - `plan.md §Phase A` step 2: `_judge` passes `trunk_ref` to `_record_gate.refusal` as it does today.
  - `wfctl/_review_gate.py` `_judge`: today's `trunk_ref` is `_review.trunk_refs(...)[0]`, the same value call 2 makes, and it's used only after `pending` comes back empty, which is after any error has already raised `_Failed`.
  - `data-model.md §In-memory types` and `research.md §R1`: both list the field.
- Finding: `_judge` keeps one `trunk_refs` call of its own, and gets the ref the record check needs from the shared result.
- Why it matters: Fixed.
- Suggested response: Fixed by `plan.md §Phase A` steps 1 and 2.
- Corroborated by: architecture and boundaries


### PR-025: `since` names the last reviewed commit even when a later sign-off, or a rebase, moved where the count starts

- Priority: MINOR
- Category: Requirement / Plan Mismatch
- Status: fixed
- Evidence:
  - `plan.md §Phase A` step 1: `since` is now the newer of the last reviewed commit and the signed-off commit, keeping only those still on the branch, so a later sign-off wins and a rebase that dropped both gives `None`.
  - `plan.md §Phase A` step 3: tests for a run followed by a later sign-off, and for a rebase that drops the last reviewed commit.
  - `data-model.md §Review step states`: after a run followed by a later sign-off, the short sha names the signed-off commit.
- Finding: Still fixed under the new rule, which reaches the same answers on a linear branch without the reads PR-027 and PR-028 raised.
- Why it matters: Fixed.
- Suggested response: Fixed by `plan.md §Phase A` step 1.
- Corroborated by: adversarial implementation

### PR-026: `research.md §R1` still gives `HeadCoverage` two fields

- Priority: MINOR
- Category: Verification Gap
- Status: fixed
- Evidence:
  - `research.md §R1`: names the six fields and points at `plan.md` and `data-model.md` for their meaning.
- Finding: Still fixed.
- Why it matters: Fixed.
- Suggested response: Fixed by the R1 edit.
- Corroborated by: requirements and traceability

### PR-027: Two git reads added for `since` can fail, and the plan's catch turns that into an error for the whole reading, in the guard too

- Priority: MINOR
- Category: Risk / Failure Mode
- Status: fixed
- Evidence:
  - `plan.md §Phase A` step 1: "With `for_status=True`, it then works out `since` and `capped`", "the guard leaves it off, so the guard runs none of the extra git reads", and "Without it, `since` is empty".
  - `plan.md §Phase A` step 2: `_judge` calls `pending_at_head(..., head=head)` with no `for_status`.
  - `wfctl/_review_gate.py` `_judge`: today it calls `trunk_refs`, `required_at`, `resolve_agent_dir`, `coverage_from_state`, and `unreviewed`, which are the five calls Phase A step 1 lists, with `head_commit` skipped because the guard passes `head`. Without the flag the guard makes no other read, so its calls and refusals stay what they are today. `refusal` turns any exception from `_judge`, `_Failed` or `ReviewError` alike, into `_error(str(e))`, so turning a `ReviewError` into `_Failed(error)` keeps the message.
  - `plan.md §Phase A` step 1: `since` keeps each commit "that exists and is an ancestor of HEAD", and "Every git read in this calculation is best-effort. A read that fails … gives `None` for that group and never sets `error`".
  - `wfctl/_review.py` `is_commit`: accepts exit codes 0, 1, and 128 and returns a bool, so a pruned commit is dropped before `_is_ancestor`, whose 128 would raise, is ever asked about it. This is the guard `commit_range` uses.
  - The rule no longer runs `rev-parse <sha>^`, so a root commit can't make it fail.
  - `plan.md §Phase A` step 3: "A last reviewed commit that no longer exists gives `None` and no `error`", and "Without the flag, `since` is empty".
- Finding: Both failing reads are gone or guarded, any other failure is caught as `None`, and the guard never runs the calculation.
- Why it matters: Fixed.
- Suggested response: Fixed by `plan.md §Phase A` steps 1 and 3.
- Corroborated by: adversarial implementation and verification, architecture and boundaries

### PR-028: The `since` cases disagree with the `None` rule, and a clean merge makes `since` a commit nobody reviewed

- Priority: MINOR
- Category: Assumption Challenge
- Status: fixed
- Evidence:
  - `plan.md §Phase A` step 1: one rule with three steps, in place of the case list. A rebase that dropped the reviewed commits gives `None`, and the test says the same.
  - `plan.md §Phase A` step 1: "After a merge from the trunk, `since` stays the last reviewed commit, and the merged trunk commits aren't in the count." `plan.md §Phase A` step 3 tests it.
  - `wfctl/_review.py` `commit_range`: when the last reviewed commit is an ancestor of HEAD, the range starts there, and `--not <trunk refs>` drops the merged trunk commits. A clean merge is dropped from the range. `since` is no longer derived from the range's oldest commit, so neither the dropped merge nor the date order of `unreviewed` can move it.
  - `wfctl/_review.py` `unreviewed`: drops every commit under a present sign-off. So whichever of the two commits `since` names, every counted commit is outside it, and the count and the short sha describe the same range.
  - `research.md §R11` and `data-model.md §In-memory types`: the same rule and the same `None` cases.
- Finding: The rule and its tests agree for a sign-off with no run, a run and a later sign-off, a merge from the trunk, and a rebase. The display in `plan.md §Phase B` step 1 reads correctly for each. A sign-off with no completed run shows `N commits unreviewed since <signed-off sha>`, counting the commits after the sign-off. A merge from the trunk shows the last reviewed commit, with only the branch's own later commits counted. A rebase that dropped the reviewed commits shows `not reviewed yet (N commits)`, counted from the merge base.
- Why it matters: Fixed.
- Suggested response: Fixed by `plan.md §Phase A` step 1.
- Corroborated by: adversarial implementation, requirements and traceability

## Requirement-to-plan trace

| Requirement / criterion | Plan location | Review note |
| --- | --- | --- |
| FR-001 | plan.md §Phase B step 2 | covered |
| FR-002 | plan.md §Phase A step 1, §Phase B step 1 | covered |
| FR-003 | plan.md §Phase B step 1, reading 1 | covered |
| FR-004 | plan.md §Phase A steps 1-3 | covered; the guard makes the same calls as today |
| FR-005 | plan.md §Phase B step 1, `display` | covered |
| FR-006 | plan.md §Phase A step 1, §Phase B step 1, reading 2 | covered |
| FR-007 | plan.md §Constitution Check | covered by design; no test named |
| FR-008 | plan.md §Phase C step 4 | covered |
| FR-009 | plan.md §Phase C step 4 | covered |
| FR-010 | plan.md §Phase C steps 3-4, §Phase B step 5 | covered |
| FR-011 | plan.md §Phase C step 2 | covered |
| FR-012 | plan.md §Phase C steps 1-3 | covered |
| FR-013 | plan.md §Phase B step 6 | covered |
| FR-014 | plan.md §Phase B step 6 | covered |
| FR-015 | plan.md §Phase B steps 2 and 5 | covered |
| FR-016 | plan.md §Phase D steps 1-2 | covered |
| FR-017 | plan.md §Phase C steps 1 and 4, research.md §R5 | covered |
| SC-001 | plan.md §Phase B step 7 | covered |
| SC-002 | plan.md §Phase A step 3, §Phase B step 7 | covered |
| SC-003 | plan.md §Phase C step 5 | covered |
| SC-004 | plan.md §Phase D step 8, quickstart.md §1 step 5 | covered |
| Edge case: rounds 0 or cap reached | plan.md §Phase A step 1, §Phase B step 1 reading 3 | covered |
| Edge case: no `origin` or no trunk ref | plan.md §Phase A step 1, error 2 | covered |
| Existing story-complete tests | plan.md §Phase B step 7 | covered; checked in the earlier review by running the four `spec_tree` tests with the plan's setup |
| User Story 4 | plan.md §Phase D step 4, quickstart.md §3 | covered by inspection and a manual walk |

## Assumptions challenged

- When the last reviewed commit and the signed-off commit are both on the branch and neither descends from the other, `since` is `None`, and the group reads `not reviewed yet (N commits)` though a review happened. The count is still right, since `unreviewed` measures from the last reviewed commit and drops what the sign-off covers. Reaching this takes a merge that joins two histories each carrying review state, such as merging back the pre-rebase branch after a run on it and a sign-off on the rebased one. The plan chose `None` on purpose and `data-model.md` says so, so this is noted and not filed. No test pins the case.
- `research.md §R11` puts the cost of `since` at up to three `merge-base --is-ancestor` calls per pending group. That holds when the signed-off commit's own check against HEAD runs once and is shared across groups: per group, the last reviewed commit against HEAD, then each direction between it and the sign-off. There are also up to two `cat-file -e` reads for the existence check. Status only, so it touches SC-004's timing and not the guard. Not filed.
- `plan.md §Technical Context` still says one status call runs one `git rev-list` per group. `commit_range` already runs several git reads per group today, and `for_status` adds the reads above and one `trunk_rounds`. The SC-004 measurement in `§Phase D` step 8 times the real cost, so the sentence misleads no one who runs it. Not filed.
- The plan's example of a failed read, `merge-base --is-ancestor` on a pruned commit, can't happen once step 1's existence check runs first. The catch-all is still what makes the rule safe for other failures, so the wording doesn't change what to build. Not filed.

## Reviewer disagreement

- None identified.

## Strengths worth preserving

- `plan.md §Phase A` step 1 puts every status-only read behind one keyword, and says outright that the guard's cost and refusals stay what they are today. The guard's behavior can then be checked by reading the call list alone.
- The new `since` rule reads the two commits `coverage_from_state` already returns, rather than deriving them from the commit range. The count and the short sha then can't drift apart on a history the range treats specially, such as a clean merge.
- `research.md §R11` records why the first-parent rule was dropped, naming the three histories it got wrong, so a later edit doesn't bring it back.

## Source freshness

This review describes only the content identities listed under `## Reviewed inputs`. When `spec.md`, `plan.md`, a binding design record, or a material planning artifact changes, this report no longer describes the current plan, and a new review is needed before it counts as current evidence.
