# Research: design gate (#648)

Every decision below was checked against the code on `648-design-gate` at
`53f5dfd`.

## R1. The pass sits between `architecture` and `design-doc`

Decision: `_STEPS["brainstorm"].sub_steps` becomes `architecture`,
`software-design`, `design-doc`.

Rationale: `_infer_steps` takes the first outstanding pass as the step's reason
(`_pipeline.py:455`, `next(s for s in step_state.sub_steps if s.state ==
"in_progress")`). Ordered this way, a branch missing both answers is told about
architecture first, then software design, which is the order `design-levels`
asks them in.

Alternatives considered: after `design-doc`. We didn't choose this because
`design.md` is written last and lists the level-3 records, so asking for it
before the record inverts the order the skill writes them in.

## R2. The reader mirrors `_architecture_answered`

Decision: `brainstorm_software_design(ev)` returns `done` when `spec.md` exists.
Otherwise it calls `touched_on_this_branch(repo_root, arch / DESIGN_DIR)`, maps
the result to a verdict the way `_architecture_answered` does
(`_evidence.py:838-845`), and holds only when `blocks(verdict, "ambient")` is
true. A held pass returns `Assessment("in_progress", SOFTWARE_DESIGN_REASON,
remedy=...)`.

Rationale: the two questions have the same shape. Both ask whether the branch
wrote something under one folder, and both are answered by git. An inconclusive
answer doesn't hold for the reason `blocks` gives: a git fact wfctl can't
compute isn't something the user can supply.

Alternatives considered: counting only records the branch adds, like
`_judge_drawings` does with `added_only=True`. We didn't choose this because a
branch that edits a proposed record it wrote earlier on the same branch would
still count as added, and one that edits an older record has still answered the
question for this change. The architecture pass counts modifications too, and
the two passes should agree.

## R3. The remedy is built by the pass

Decision: the reader returns its own `remedy`, formatted from a new
`SOFTWARE_DESIGN_HELP` constant with the `design/` location filled in.
`_infer_steps` already prefers an outstanding pass's remedy
(`_pipeline.py:460-461`), so `_design_remedy` stays unchanged.

Rationale: this is how `_judge_drawings` already hands back its fix. Keying
`_design_remedy` on a second reason would put a second pass's rendering in a
function written for one.

## R4. `arch_location` moves to `_paths`

Decision: move `arch_location` from `_pipeline.py:673` to `_paths.py`, beside
`is_in_tree` and `arch_root`, and import it back into `_pipeline` so every
existing caller keeps working.

Rationale: the reader in `_evidence` needs it to print the `design/` location.
`_evidence` imports nothing from `_pipeline` today, and `_pipeline` imports
`_evidence` at module scope (`_pipeline.py:26`), so importing it the other way
would add a cycle. The function only uses `is_in_tree` and `Path`, which are
already in `_paths`.

Alternatives considered: building the path string inline in the reader. We
didn't choose this because the location format would then be written in two
places. `arch_location` also holds two special rules, an absolute path outside
the tree and no `./` for a root at the repo root, but neither can fire in this
reader. The pass only holds when git can answer, which needs an arch root
inside the tree, and `<arch-root>/design` is never the repo root itself. So
the move is the simplest way to get the repo-relative path, not a way to
inherit those two rules.

## R5. The claim needs no new code

Decision: no change to `step_none_cmd` or to claim reading.

Rationale: `_declared.load` starts from `_builtin_only()` (`_declared.py:100`),
which includes every built-in pass, so `step none` resolves
`brainstorm.software-design` with no `wfctl.json`.
`test_the_built_in_plan_review_can_be_claimed_away_and_a_person_still_starts_tasks`
(`tests/test_step_none.py:251`) already proves this for `plan.plan-review`.

## R6. A repository can't declare its own `software-design`

Decision: no change. `_declared._load_step` already reports
`brainstorm.software-design is wfctl's own pass; rename the declared one`
(`_declared.py:147-148`) and drops the declared pass. `wfctl check config`
prints that problem.

## R7. The pass name column fits the longest name

Decision: `status_cmd` computes the pass column width once, from every pass in
the payload, as `2 + longest + 2`, and uses it for every pass row.

Rationale: the column is `ljust(16)` today (`cli.py:829`), which leaves
`software-design` (15 characters) and `plan-walkthrough` (16) touching their
glyph. Computing from every pass, shown or hidden, keeps the column in the same
place between `wfctl status` and `wfctl status --all`.

This departs from FR-007 on purpose. FR-007 sizes the column to the longest
pass name shown, and this sizes it to every pass in the payload. Sizing to the
shown names would move the column whenever `--all` reveals a hidden pass.

The payload always carries every built-in pass, and `plan-walkthrough` is 16
characters, so the width is 20 in every repository. That means every pass row
moves four columns right, even in a repository that declares nothing, and
`tests/test_cli_status.py:56` changes with it. That's expected, not a
regression. We dropped the earlier floor of 16, since it could never apply.

## R8. The release note is a `change`

Decision: `changes/648.change.md`, not `addition` as `design.md` first said.

Rationale: `AGENTS.md` says `change` is for something an existing user relies
on that behaves differently. A branch that used to leave brainstorm with
`design.md` and an architecture answer now stops there. That's a change in
behaviour the user will notice, even though the pass is new.

## R9. Existing tests that build a branch past brainstorm

Decision: tests that stage `design.md` and an architecture answer in a git
repository with a trunk, and expect specify to be current, get a design record
or a claim added to their setup. Tests in a directory with no trunk, or no git
repository at all, are now affected too, since R10 holds both checks there.

The `storyctl_dir` fixture does have a trunk. It commits on its default branch
and never switches, so `trunk_branch` finds that branch, `trunk...HEAD` is
empty, and the pass holds. Any test built on `storyctl_dir` that stages
`design.md` and an architecture answer and expects to move on is affected.

Rationale: `make_spec_artifact` and `stage_upstream_of` (`tests/conftest.py`)
build in `tmp_path` and don't commit. How many other fixtures also set up a
trunk isn't checked yet, so the exact list is found by running the suite once
the pass exists. Known now:

1. `tests/test_declared.py:25`, `:388`, and `:395` assert the brainstorm pass
   list.
2. `tests/pipeline_payload_snapshot.json` holds step rows and no `sub_steps`,
   so what changes there is a verdict, not a pass list. Its
   `design-with-record` row comes from a repository with one uncommitted
   top-level record, and after this change that row holds on
   `software-design`. `test_the_matrix_reaches_both_design_states` asserts the
   row is `done` with no reason. The `recorded` repository gets a record under
   `design/` so the assertion keeps its meaning, and a new row records the
   hold. Don't regenerate the snapshot on the belief that only a list moved,
   since that defeats the test.
3. `tests/test_cli_status.py:56` asserts pass rows at today's width (R7).
4. `README.md:45-47` shows the brainstorm passes in its `wfctl status` example.
5. `tests/test_pipeline_state_names.py`
   `test_a_written_record_with_no_design_doc_leaves_exactly_one_pass_outstanding`
   stages a record and no `design.md`, and asserts the outstanding passes are
   exactly `["design-doc"]`. Its setup gains a claim on
   `brainstorm.software-design`, so it still proves `design-doc` is reported
   when it's the last thing missing. Swapping the expected name would remove
   that proof.

## R10. Both checks hold when git can't answer

Decision: when git can't tell whether the branch changed the architecture
folder, the architecture check and the software design check both hold
brainstorm. A new `wfctl.json` setting, `design_record_checks`, set to
`"off"`, turns both checks off for a repo where git can never answer. This
came out of the plan walkthrough, where Andre chose it for both checks.

Rationale: `promised-evidence-blocks-on-silence.md` let a branch through when
git couldn't answer, because nothing the user could do would produce the
missing answer. That is no longer true for these two checks:

1. A repo with no `main` names its base branch with `trunk`, which
   `trunk_branch` already reads first.
2. A repo whose architecture folder sits outside the project sets
   `design_record_checks` to `"off"`.
3. A git command that fails means a broken checkout, which the user fixes
   outside wfctl.

So both checks pass `"repo-declared"` to `blocks` instead of `"ambient"`, and
the record is amended to say why. `blocks` itself doesn't change, and every
other check that reads git still lets the branch through. `decompose` is the
other `"ambient"` caller, and its question is about the tracker, which neither
setting reaches.

The setting is a new key rather than `trunk` set to `"none"`. "No base branch"
and "an architecture folder git can't see" are different situations, and a
repo with an outside folder still has a base branch the other checks use.

The setting is needed rather than a convenience. `wfctl arch none` writes its
declaration under the arch root and is found through git, so it can't release a
check when the folder is outside the project. A claim can release either check,
since `wfctl step none brainstorm.architecture` and `wfctl step none
brainstorm.software-design` are both read from disk. But that costs one claim
per branch, forever, and a claim written under an arch root outside the project
is never committed, so the PR reviewer never sees it.

A typo in the value leaves both checks on and is a `check config` finding, so
a mistake never turns a check off.

Tests affected, beyond those R9 lists:

1. `tests/test_design_gate_drawing.py`, the #508 section from line 601. Its
   no-trunk tests before `spec.md` now see a held branch. Those past `spec.md`
   escape before git is asked and don't change.
2. Tests that stage `design.md` in a `tmp_path` that isn't a git repository,
   and expect brainstorm to finish. A branch past `spec.md` escapes first, so
   only tests that stop between brainstorm and specify are affected. The
   suite finds them, as in R9.
3. `tests/test_evidence.py:129`,
   `test_every_inconclusive_verdict_goes_through_blocks`. Both checks still go
   through `blocks`, so this passes unchanged, and it still finds a reader that
   never calls `blocks`. It doesn't look at order, so plan test 8d is what
   checks that `blocks` is asked before the reason is chosen.
4. `tests/test_design_gate_drawing.py`
   `test_a_failing_record_under_an_arch_root_outside_the_repository_is_not_judged`
   (line 584, before the section item 1 names). It's the only test that a
   failing record under an outside arch root isn't judged, so it needs
   rewriting rather than a flipped assertion: its setup turns the checks off
   or answers the architecture check, so the rule it proves still runs.
5. `tests/test_pipeline_commands.py`
   `test_an_unreadable_arch_root_advances_the_design_step`, documented as "the
   ambient rule end to end". It's rewritten to assert the hold and the remedy,
   and its docstring points the ambient rule at `decompose`, the remaining
   ambient caller.
