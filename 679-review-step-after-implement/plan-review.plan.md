# Implementation Plan: Review step after implement

**Branch**: `679-review-step-after-implement` | **Date**: 2026-10-31 | **Spec**: `spec.md` in this feature folder
**Input**: `spec.md`, `design.md`, and the level-3 records `docs/architecture/design/679-review-is-its-own-step.md` and `docs/architecture/design/679-no-spec-skips-spec-rows.md`

## Summary

Currently, `wfctl status` reports a story complete as soon as implement is done, and the review panel runs only when someone remembers it. After this change, `review` is a ninth step after `implement`. It reads done only when every required review group has reviewed HEAD, or a person's sign-off covers it. It gets that answer from the same function the PR guard calls.

A branch that needs no spec records that with `wfctl spec none --reason "…"`. The pipeline then reads brainstorm through decompose as skipped, judges `implement` by `wfctl verify` alone, and sends the branch on to `review`. The terminal shows the seven skipped rows as one line, and the JSON payload carries the reason once, in a new `no_spec` field.

The work has four phases:

1. Phase A adds the shared review function and moves the guard onto it, with no visible change.
2. Phase B adds the review row.
3. Phase C adds the no-spec route.
4. Phase D covers docs, skills, the release note, and the real-flow check.

## Technical Context

**Language/Version**: Python 3.11+
**Primary Dependencies**: `typer` and `rich`, no new ones
**Storage**: Files. The review state in the branch's state folder (`reviews/<group>/last-reviewed.json` and `reviews/sign-off.json`), which this change reads and never writes. One new exception file, `exceptions/spec.md`, in the spec folder.
**Testing**: `uv run pytest -q`, `uv run ruff check wfctl/ tests/`, `uv run mypy`, then `uv run wfctl verify` and `uv run wfctl doctor`
**Target Platform**: macOS and Linux, wherever wfctl runs
**Project Type**: CLI
**Performance Goals**: SC-004, `wfctl status` within half a second of today on this branch once implement is done, with the branch's commit count recorded beside the timing. The review reading runs only once `implement` reads done (research R2), so a branch earlier in the pipeline pays nothing.
**Constraints**: Flat module layout, since #671 reorganizes it later. No new runtime dependency. Minimal-complexity bias.
**Scale/Scope**: Two review groups by default, `security` and `code`. One status call reads one `last-reviewed.json` per group and runs one `git rev-list` per group.

## Constitution Check

_GATE: Must pass before Phase 0 research. Re-check after Phase 1 design._

The repo has no `.specify/memory/constitution.md`. The gates below come from `AGENTS.md` and the accepted records, and Complexity Tracking records the substitution.

- [x] Validation plan exists: the Validation Strategy in `spec.md`, plus the test files named under Project Structure.
- [x] Complexity is justified: one new function in `_review`, one `Step` field, two `Evidence` fields, and one CLI command. The two level-3 records argue each against its direct baseline.
- [x] Ownership is stated: see "Who computes what" below.
- [x] `session-state-is-re-derived`: the review answer and the no-spec answer are read from files on every call, and nothing is cached.
- [x] `pipeline-state-is-one-payload`: `build_report` computes the review row and `no_spec`, and both views render them. The terminal's single skipped line reads the payload and computes nothing of its own.
- [x] `a-rule-is-expressed-as-a-check`: `check-body` checks the "no spec" reason, and the review row uses the guard's own function.
- [x] `vendor-upstream-skills`: no spec-kit-derived skill is edited. `speckit-orchestrate` is wfctl's own.
- [x] `an-absent-artifact-is-claimed-not-inferred`: the no-spec route starts only from a written answer, never from a missing spec folder.
- [x] The agent never marks review done. Only `wfctl review check` and `wfctl review sign-off` write the files the row reads (FR-007).

### Who computes what

| Value | Computed by | Why not the other side |
| --- | --- | --- |
| Which commits each group hasn't reviewed | wfctl, from the review state files and git | The agent running the panel would be grading its own work |
| Whether a run is complete | `wfctl review check`, unchanged | Same reason, since it counts the reports against the roster |
| Whether a change needs a spec | The agent, answering the three spec questions | It's a judgment with no objective test, so wfctl records it and the human reviewer checks it in the PR body |
| Whether the "no" is still in effect | wfctl, from the four spec artifacts on disk | An agent that switched to yes and forgot the file would otherwise skip the pipeline |

## Implementation

### Phase A: one review function for the guard and status (no visible change)

1. **`wfctl/_review.py`** gets `pending_at_head`:

   ```python
   class HeadCoverage(NamedTuple):
       pending: dict[str, tuple[str, ...]]  # group -> unreviewed commits, oldest first
       since: dict[str, str | None]         # group -> commit its count starts after, None if none
       capped: tuple[str, ...]              # pending groups with no review rounds left
       trunk_ref: str | None                # the trunk ref call 2 resolved, None if it failed
       error: str | None                    # why coverage can't be computed
       remedy: str | None                   # the fix for `error`, when its message doesn't name one

   def pending_at_head(
       repo_root: Path, branch: str, timeout: float | None = None,
       *, head: str | None = None, for_status: bool = False,
   ) -> HeadCoverage: ...
   ```

   The function lives in `_review`, which already imports `_review_config` and `_paths` at the top of the file. Neither of those imports `_evidence` or `_pipeline`, so the new import from `_evidence` adds no cycle.

   It makes the calls `_review_gate._judge` makes today, in the same order:
   1. `head_commit(repo_root, timeout)`, only when no `head` is passed. The guard passes the head it has already checked. Status passes none, so a branch with no commits gets an `error` instead of crashing status.
   2. `trunk_refs(repo_root, timeout, branch=branch)[0]`
   3. `_review_config.required_at(repo_root, head, trunk_ref, timeout)`
   4. `_paths.resolve_agent_dir(repo_root, branch, create=False, timeout=timeout)`
   5. `unreviewed(..., *coverage_from_state(agent_dir, groups), timeout, branch=branch)`

   With `for_status=True`, it then works out `since` and `capped`, which only status shows. Status passes it, and the guard leaves it off, so the guard runs none of the extra git reads and its cost and refusals stay what they are today. Without it, `since` is empty and `capped` is an empty tuple.

   `since` holds, for each pending group, the newest reviewed commit still on the branch, so a person knows where to start reading. It's computed from the two commits `coverage_from_state` already returns:
   1. Take the group's last reviewed commit and the signed-off commit, keeping each one that exists and is an ancestor of HEAD.
   2. When both are kept, take the one that descends from the other. When neither descends from the other, take `None`.
   3. When one is kept, take it. When none is, take `None`, and the group reads `not reviewed yet`.

   Every git read in this calculation is best-effort. A read that fails, such as `merge-base --is-ancestor` on a commit `git gc` has pruned, gives `None` for that group and never sets `error`, so an unusual history can't block the review row. `None` is also the answer after a rebase that dropped the reviewed commits, since the branch no longer has them. After a merge from the trunk, `since` stays the last reviewed commit, and the merged trunk commits aren't in the count. The count itself always comes from `pending`, so `since` names where the reviewed history ends and never changes the count.

   A pending group is capped when the rounds it has started reach the round cap. The count is the same one `review start` uses: the larger of `runs_started(agent_dir, group)` and `rounds_tallied(resolve_round_dir(repo_root, branch, create=False), group)`, compared with `trunk_rounds(repo_root, timeout, branch=branch).cap`. `create=False` keeps status from creating the round-tally folder, since this change reads review state and never writes it. A cap of 0 caps every pending group. A sign-off that covers a group's commits already removes the group from `pending`, so `capped` never names a group that a sign-off has cleared.

   Errors come back as values, with the remedy set where the error is caught, since only that code knows which error it has (`498-the-fix-line-travels-with-the-reason.md`):
   1. A config problem returns `error` as `can't read the review config: <first problem>`, and `remedy` as `fix review in the wfctl.json the error names, then run wfctl check config`. `required_at` reports problems from the trunk's `wfctl.json` and from the branch's own, and each problem already names its file as `wfctl.json at <ref>`. A remedy that always named the trunk would send a person to the wrong file when the problem is on the branch.
   2. A `ReviewError` raised by any call returns its message as `error` and no `remedy`. The trunk errors already name their fix in the message, such as `set trunk in wfctl.json` or `run git fetch --unshallow`, so a separate remedy would repeat it.

   The function never raises a `ReviewError`, so no caller can forget to catch one.
2. **`wfctl/_review_gate.py` `_judge`** calls `pending_at_head(..., head=head)` in place of its four calls. It keeps the checks it runs before them (the trunk is the judged branch, the branch is checked out elsewhere, the head isn't a commit), and turns `error` into `_Failed(error)`. The `NoTrunk` path stays where it is, since `_judge` raises it before the shared call. The guard reads `pending` for its review refusal, and passes `trunk_ref` to `_record_gate.refusal` as it does today, so it reads the trunk once and its refusals don't change.
3. **Tests** in `tests/test_review.py`:
   - `pending_at_head` returns each group's commits, returns none after `review check` writes `last-reviewed.json` at HEAD, returns none after a sign-off at HEAD, and returns one commit after one more commit.
   - It returns an `error` for an unreadable config, and for a branch with no commits.
   - With `for_status=True`, `capped` names a group after one round with `review.rounds` at 1, names every pending group with `review.rounds` at 0, and is empty once a sign-off covers HEAD. Without it, `capped` is empty and the round-tally folder isn't created.
   - A config problem on the trunk and one on the branch each return an `error` naming that file, and the same `remedy`. A missing trunk returns its message and no `remedy`.
   - `trunk_ref` is the ref the trunk resolved to.
   - With `for_status=True`, `since` names the last reviewed commit after a run, the signed-off commit for a group with a sign-off and no completed run, and the signed-off commit for a group reviewed at one commit and then signed off at a later one. It stays the last reviewed commit after a merge from the trunk. After a rebase that drops the last reviewed commit, it's `None`. A last reviewed commit that no longer exists gives `None` and no `error`. Without the flag, `since` is empty.
   - Each test builds a feature branch with its own commits off a local `main`. With no `origin`, the trunk falls back to the local `main`, so a branch with no commits of its own has nothing to review.
   - `tests/test_review_gate.py` stays green with no edits, which shows the move changed nothing.

### Phase B: the review row

1. **`wfctl/_evidence.py`**:
   - `Evidence` gets `review: _review.HeadCoverage | None = None`, defaulted and last, so an `Evidence` built by hand in a test still compiles.
   - `build_evidence` builds the `Evidence` as today. When `implement(ev).state == "done"`, it replaces it with `dataclasses.replace(ev, review=_review.pending_at_head(repo_root, resolve_branch(repo_root), for_status=True))`. Before implement is done, the field stays `None` and costs nothing (research R2).
   - A new reader, `review(ev) -> Assessment`, returns one of five readings:
     1. `implement(ev).state` isn't `done`: `Assessment("pending")`.
     2. `ev.review.error` is set: `Assessment("in_progress", error, error, remedy=ev.review.remedy)`. The reason blocks the step, so it routes with `auto: false`, since a person has to fix the cause (FR-006). The remedy, when there is one, names the fix rather than the panel, which would fail on the same error (research R12).
     3. `ev.review.capped` isn't empty: `Assessment("in_progress", reason, remedy="  Ask the user to run `wfctl review sign-off` in their own terminal.")`, with no display, so the step line shows the reason. The reason names each capped group, such as `security has used its 3 review rounds, so a person has to sign off`, or `review.rounds is 0, so a person has to sign off` for a cap of 0. The reason blocks the step, so an unattended run stops instead of starting a panel that `review start` refuses (research R3). The remedy is the line `review start` prints for the same refusal.
     4. `ev.review.pending` is empty: `Assessment("done")`.
     5. Otherwise: `Assessment("in_progress", None, display)`. It has no reason, so the step stays automatic and an unattended run starts the panel (research R3).
   - `display` is one line per distinct state, with the groups that share it joined, in the form design.md shows. A group whose `since` is `None` reads `not reviewed yet (N commits)`. Any other group reads `N commits unreviewed since <short sha>`, with `1 commit` for one. For example, `security, code: not reviewed yet (4 commits)`, or `security, code: 1 commit unreviewed since 3f2a1c9`. A branch a person signed off with no completed run reads the second form, counted from the signed-off commit, since the sign-off covers everything before it.
2. **`wfctl/_pipeline.py`**: `_STEPS` gets `"review": Step("/fanning-out-code-review", _AUTOMATIC, _evidence.review)` after `implement`. `STATUS_PAYLOAD_VERSION` moves to `"1.4"`.
3. **`wfctl/_declared.py`** refuses a `steps.review` key in `wfctl.json`, with the problem `'review' takes no declared passes; its groups are set under the review key`. A repository already sets its review groups under the `review` key, and a second way to add review work would be a new public option nobody decided on. `wfctl check config` reports it like any other unknown step.
4. **`wfctl/_stall.py`**: `digest` hashes one more part after the three artifacts, which is `ev.review` written as sorted JSON when it's set, and nothing when it isn't. Without it, a panel run that moves one group's last reviewed commit reads as no progress, and the stall bound stops a review that is moving. `find_stall` names `review state` in `unchanged` when the stalled step is `review`, and the three artifacts otherwise (research R10).
5. **The status payload contract**. Regenerating `wfctl/contracts/status-payload.json` must come out as a minor bump to 1.4. The existing fixture states still reach story complete. With no `origin`, the trunk falls back to the local default branch, and the fixture branch sits at the same commit, so `review` has nothing to review and reads done. One fixture change is needed: a new `no_spec` state writes `exceptions/spec.md` with no spec artifacts, so the payload records the `no_spec` object with `reason` and `path`. Without it, `no_spec` is only observed as `null`.

   `payload_of` in `tests/conftest.py` gets the `no_spec` key. After regenerating, `test_status_contract.py` passes and `bump` returns minor. A major bump means a fixture state is missing, not that the version should be 2.0.
6. **`wfctl/cli.py`**:
   - `step complete implement` accepts `review` as the current step, beside `implement` and `None` (FR-013).
   - `report-block` falls back to `"implement"` by name instead of `_STEP_NAMES[-1]` (FR-014).
   - Before this phase closes, grep for every other `_STEP_NAMES[-1]` and every literal `"implement"` that means "the last step". Change each hit, or note why it's correct.
7. **Tests**:
   - `tests/test_evidence.py`: the review reader's five readings with their remedies, the display strings for one group and for two groups with different states, and that `build_evidence` doesn't compute the review field while implement isn't done.
   - `tests/test_pipeline_commands.py`: User Story 1's five scenarios through `wfctl status --json`. Each scenario builds a feature branch with its own commits off the local `main`, since the `storyctl_dir` fixture stays on the default branch, where `review` always reads done. Scenario 5 also has no level-2 record, so the guard's record check has nothing to refuse. On it, the review row reads done exactly when the guard finds no unreviewed commits, with and without a sign-off (FR-004, SC-001). With `review.rounds` at 0, `auto` is false and the remedy names `wfctl review sign-off`.
   - `tests/test_declared.py`: `steps.review` in `wfctl.json` is a `check config` finding.
   - `tests/test_stall.py`: the digest changes when one group's last reviewed commit moves, and a stall on `review` lists `review state` as unchanged.
   - `tests/test_report_block_holds_step.py`: a block filed on a complete story holds `implement`.
   - `step complete implement` succeeds while `review` is current.
   - `tests/pipeline_payload_snapshot.json` and every test that lists the step names get the ninth row.
   - The tests that drive a branch to story complete in a git repository keep passing with no edit, since their branch has no commits beyond the local trunk and `review` reads done. That holds for `tests/test_pipeline_commands.py` (around lines 221, 897, and 1444), `tests/test_warnings_after_gate.py`, and `tests/test_report_verbs.py`.
   - Four tests assert story complete with `tmp_path` as the repository root, and `tmp_path` isn't a git repository. There the review row reads an error, so they stop passing. They are `tests/test_pipeline_state_names.py` (`test_a_finished_story_has_neither_a_current_step_nor_a_command`, around line 235), `tests/test_decompose_issues.py` (around line 246), `tests/test_tasks_hold_a_task.py` (around line 138), and `tests/test_completion_record.py` (around line 442). Each one calls `git_repo(tmp_path)` from `tests/conftest.py` before building the report, which gives the folder one commit on the default branch, and sets `WFCTL_BRANCH` to a feature branch name with `monkeypatch`, as `storyctl_dir` does. HEAD then sits on the trunk, so `review` has nothing to review and reads done for the same reason as above. Without `WFCTL_BRANCH`, the branch under review is the trunk, and `trunk_refs` refuses it. A sign-off can't fix these tests, since a folder with no commits has no HEAD to sign off.
   - Before this phase closes, grep `tests/` for `Story complete`, `current is None`, and `(None, None)`, and check each hit's repository root against the two cases above.

### Phase C: the no-spec route

1. **`wfctl/_design_exceptions.py`** gets `SPEC = "spec"` and `spec(spec_dir) -> str | None`, which reads `exceptions/spec.md` the way `boundary` reads `boundary.md`. `reasons` adds `("spec", reason)` when the file exists and none of `SPEC_ARTIFACTS` exists beside it, so `check-body` requires the reason in the PR body with no change beyond its message (FR-017, research R5). `reasons` applies the same artifact check as `build_evidence`, through one shared helper, `_design_exceptions.spec_in_effect(spec_dir) -> str | None`. Otherwise `check-body` would ask for a no-spec reason in the body of a PR that has a spec. `SPEC_ARTIFACTS` lives in `_design_exceptions` for that reason, and `_evidence` imports it. The name has no dot, so `passes` never reads it as a pass exception.
2. **`wfctl/_evidence.py`**:
   - `SPEC_ARTIFACTS = ("design.md", "spec.md", "plan.md", "tasks.md")`, imported from `_design_exceptions`.
   - `Evidence` gets `no_spec: str | None = None` and `stale_no_spec: str | None = None`. `build_evidence` reads `_design_exceptions.spec(spec_dir)`. When there's a reason and none of the four artifacts exists, `no_spec` holds the reason. When there's a reason and an artifact exists, `no_spec` stays `None`, and `stale_no_spec` holds the first artifact's name (FR-012).
   - `implement`: when `ev.no_spec` is set and `tasks.md` is missing, it skips the tally and reads the verification record alone. It returns `in_progress` with the verification reason, or `done` (FR-011). The existing `next_step_content` arm for a blocked `implement` with no open tasks then routes to `wfctl verify`.
   - `fact_artifacts_written` reads `n/a` with the detail `no spec recorded` when `ev.no_spec` is set. The three artifacts aren't missing on that branch, since the branch recorded that it has none, so `unmet` would contradict a finished story.
3. **`wfctl/_pipeline.py`**:
   - `Step` gets `spec_step: bool = False`, set on the seven rows from `brainstorm` to `decompose`.
   - In `_infer_steps`, when `ev.no_spec` is set, each `spec_step` row reads `skipped` with the annotation `no spec`, without calling its reader, and doesn't set `cascade`. Its passes still come from `_pass_states(name, passes, None, "skipped", claims)`, whose existing `skipped` arm marks every pass `skipped` without calling its reader. Every step keeps listing all of its passes, as `_PipelineStep.sub_steps` promises, so `brainstorm`'s three passes, `plan-review`, and this repo's `plan-walkthrough` read `skipped` rather than disappearing.
   - `PipelineReport` gets `no_spec: NoSpec | None = None`, with `NoSpec(reason: str, path: str)`. `build_report` fills it from `ev.no_spec` and `_design_exceptions.path(spec_dir, SPEC)`.
   - When `ev.stale_no_spec` is set, `build_report` appends `StepWarning("brainstorm", None, "exceptions/spec.md says no spec, but <artifact> exists", "rm <path>")` after `collect_warnings`. It's a warning and not a reason, since the pipeline already reads correctly (research R6).
4. **`wfctl/cli.py`**:
   - `status --json` always emits `no_spec`, as `{"reason": …, "path": …}` or `null` (FR-010).
   - The console view prints one line, `brainstorm … decompose  –  skipped: no spec`, in place of the consecutive rows that read `skipped` with the annotation `no spec`. It leaves the reason out.
   - A new `spec` command group with one command, `wfctl spec none --reason "…"`. It refuses an empty reason and a placeholder with the same checks as `arch none`, moved into one shared helper rather than copied. It refuses when any of `SPEC_ARTIFACTS` exists in the branch's spec folder, and names the file. On success it writes through `_design_exceptions.write(feature_dir, SPEC, reason)` and prints `✓ Recorded: no spec needed — "<reason>"`, the path, and `Put the reason in the PR body.` (FR-008, FR-009).
   - `check-body`'s message for the `spec` label reads `the no-spec reason isn't in the body: "<reason>"`.
5. **Tests**:
   - `tests/test_design_exceptions.py`: `spec` reads the file and ignores an empty one. `reasons` includes it with no spec artifact, and leaves it out with `design.md` present.
   - `tests/test_pipeline_commands.py`: `spec none` success and each refusal, the seven skipped rows and the single console line, `no_spec` in the JSON, `implement` routing to `wfctl verify`, `review` current once verified, and the stale-answer warning with `design.md` present.
   - On a no-spec branch, `--json` lists every pass of the seven rows as `skipped`, including `plan-walkthrough` declared in `wfctl.json`, and the `artifacts written` fact reads `n/a`.
   - `check-body` fails a body missing the no-spec reason, passes one carrying it, and asks for nothing once `design.md` exists.

### Phase D: docs, skills, release note, and the real flow

1. **README.md**: the steps description names `review` as the ninth step, and lists `spec none` beside `arch none`.
2. **`wfctl/agents/skills/speckit-orchestrate/SKILL.md`**: the story-complete branch says the story is complete only after `review`. Nothing else changes, since the row is automatic and routes like any other.
3. **`wfctl/agents/skills/fanning-out-code-review/SKILL.md`**: it already reads `no_spec` from the payload (commit 1a0e668). Check the field name matches what Phase C emits.
4. **`wfctl/agents/skills/design-passes/SKILL.md`** and **`start-session/SKILL.md`**: both already teach `wfctl spec none`. Check their example output matches what Phase C prints.
5. **AGENTS.md**: the pipeline line in "What this is" gets `→ review`.
6. **`changes/679.addition.md`** via `uv run towncrier create`.
7. Run `uv run wfctl install-skills --prune --yes --agent claude` and `uv run wfctl doctor`, then the scratch-branch walk in `quickstart.md`, then the real flow on this branch.
8. Measure SC-004 on this branch once implement is done, since that's where the review reading runs. Time `uv run wfctl status` five times, then time the `main` checkout's wfctl five times on the same branch with `uv run --project <main checkout> wfctl status`, and compare the medians. The difference must stay under half a second. Record the branch's commit count beside the timing, since the review reading's cost grows with the commits each group has left. Step 5 of the first walk in `quickstart.md` has the commands.

## Project Structure

### Documentation (this feature)

```text
<spec-root>/679-review-step-after-implement/
├── design.md
├── spec.md
├── plan.md            # this file
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   └── cli.md
└── tasks.md           # /speckit.tasks
```

### Source Code (repository root)

```text
wfctl/
├── _review.py              # pending_at_head, HeadCoverage (A)
├── _review_gate.py         # _judge calls pending_at_head (A)
├── _evidence.py            # review reader, Evidence fields, implement change, artifacts fact (B, C)
├── _pipeline.py            # review row, spec_step, NoSpec, payload 1.4 (B, C)
├── _declared.py            # refuses steps.review (B)
├── _stall.py               # digest covers review state (B)
├── _contract.py            # no_spec fixture state (B)
├── _design_exceptions.py   # SPEC, SPEC_ARTIFACTS, spec(), spec_in_effect(), reasons() (C)
├── cli.py                  # step complete, report-block, status, spec none, check-body (B, C)
├── contracts/status-payload.json
└── agents/skills/
    ├── speckit-orchestrate/SKILL.md
    └── fanning-out-code-review/SKILL.md   # check only

tests/
├── test_review.py
├── test_review_gate.py            # unchanged, must stay green
├── test_evidence.py
├── test_declared.py
├── test_stall.py
├── conftest.py                    # payload_of gets no_spec
├── test_pipeline_commands.py
├── test_report_block_holds_step.py
├── test_design_exceptions.py
├── test_pipeline_payload_snapshot.py
├── pipeline_payload_snapshot.json
├── test_pipeline_state_names.py   # story-complete tests get a git repository
├── test_decompose_issues.py       # same
├── test_tasks_hold_a_task.py      # same
└── test_completion_record.py      # same

README.md
AGENTS.md
changes/679.addition.md
```

**Structure Decision**: The flat layout as it stands. No module moves, since #671 reorganizes them after this ships.

## Complexity Tracking

| Item | Why needed | Simpler alternative rejected because |
| --- | --- | --- |
| Gates taken from `AGENTS.md` and accepted records | The repo has no constitution | A gate with no source checks nothing |
| `HeadCoverage` NamedTuple | The guard needs the error text, and status shows it as a reason | Raising would make status catch the guard's exception types, and a bare dict can't carry the error |
| `capped` in `HeadCoverage` | Past the round cap, only a person's sign-off clears the review, so the row has to stop an unattended run | Leaving the row automatic sends the run into a panel that `review start` refuses, until the stall bound stops it with no word about the sign-off |
| Review computed only once implement is done | SC-004, and most branches never reach implement | Computing it on every call runs git once per group on every `status`, including on branches that have nothing to review yet |

## Design records

Design records: 2 listed in design.md
  docs/architecture/design/679-review-is-its-own-step.md
  docs/architecture/design/679-no-spec-skips-spec-rows.md
