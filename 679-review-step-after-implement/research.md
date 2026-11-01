# Research: Review step after implement

## R1. The shared function returns an error value instead of raising

**Decision**: `_review.pending_at_head` returns a `HeadCoverage` and never raises a `ReviewError`. It carries six fields: `pending`, `since`, `capped`, `trunk_ref`, `error`, and `remedy`. `plan.md` Phase A step 1 and `data-model.md` define each one.

**Rationale**: The guard and status both need the same four calls, and they treat a failure differently. The guard refuses the command, and status shows the error as the review row's reason. If the function raised, status would have to catch `NoTrunk`, `NoRemoteTrunk`, `ShallowClone`, and the config problem separately, and a new error type added later would crash `wfctl status`. A returned value gives both callers one shape to handle.

**Alternatives considered**: Raising and letting each caller catch. We didn't choose this because status would have to track the guard's exception types, which is the drift the level-3 record exists to prevent.

## R2. The review field is computed only once implement reads done

**Decision**: `build_evidence` fills `Evidence.review` only when `implement(ev).state == "done"`.

**Rationale**: The review reading runs `git show` on the trunk's `wfctl.json` and one `git rev-list` per group. A branch at brainstorm or plan never shows a review row other than `pending`, so the reading would be wasted. It also keeps most of the test suite out of the review reading, since those fixtures never reach a done `implement`. Calling `implement(ev)` inside `build_evidence` is cheap, because it reads fields `build_evidence` has already computed.

**Alternatives considered**:
1. Compute it on every call. We didn't choose this because it costs git calls on every status for no displayed result, and SC-004 bounds the cost.
2. Compute it inside the review reader. We didn't choose this because readers take only `Evidence` and don't reach disk, which is the rule `build_evidence` exists to keep.

## R3. An unreviewed branch carries no reason, so the step stays automatic

**Decision**: When groups have unreviewed commits, the review reader returns `in_progress` with a display and no reason. Only a config or trunk error carries a reason.

**Rationale**: `next_step_content` treats any step with a reason as blocked, and a blocked step is never automatic. If unreviewed commits were a reason, an unattended run would stop at review instead of starting the panel, and FR-001 says it runs automatically. Implement uses the same shape for open tasks: `in_progress`, no reason, and the tally as display. A config error is different, since re-running the panel can't fix it and a person has to, so it blocks.

A group past its round cap blocks for the same reason. `review start` refuses that group until a person signs off, so an automatic row would send an unattended run into the same refusal on every pass, until the stall bound stopped it with no word about the sign-off. The reason names the capped group, and the remedy is the line `review start` prints for that refusal. `review.rounds` of 0 is the same case with every group capped from the start.

## R4. The payload version moves to 1.4

**Decision**: `STATUS_PAYLOAD_VERSION` becomes `"1.4"`.

**Rationale**: The payload's keys don't change for the ninth row, since step names aren't listed in the contract. But a consumer that treated `implement` as the last step, or a `null` `next_command` after implement as story complete, now reads a different meaning under the same keys. The new top-level `no_spec` key is an addition on top of that. A minor version bump says "same shape, new meaning and one new key", which matches how 1.3 was introduced for `warnings`.

## R5. `check-body` looks for the no-spec reason anywhere in the body

**Decision**: The no-spec reason joins `_design_exceptions.reasons`, and `check-body` looks for it anywhere in the PR body, the way it looks for every other exception's reason.

**Rationale**: FR-017 says the reason belongs in the "Needs a spec?" section. `check-body` deliberately names no section of its own, since a repository chooses its headings in `change_sections` and its PR template. A section-specific check would break that for one exception. The PR template puts the reason under "Needs a spec?", and `change_sections` already fails a PR whose "Needs a spec?" section is empty or a bare yes or no. Together the two checks give the result FR-017 asks for. FR-017's wording is updated to say "the PR body".

**Alternatives considered**: Read the "Needs a spec?" section through `_sections` and look for the reason there. We didn't choose this because it would make wfctl name a heading, which every other exception check avoids.

## R6. A stale "no" is a warning, not a reason

**Decision**: When `exceptions/spec.md` exists beside `design.md`, `spec.md`, `plan.md`, or `tasks.md`, the pipeline ignores the "no" and adds one entry to `warnings` that names the file to delete.

**Rationale**: The pipeline already reads correctly, since the artifacts outrank the answer. A reason would hold a step and route to it, and nothing about the step is wrong. `warnings` is the payload's place for a problem that doesn't hold the run, and `speckit-orchestrate` already displays it. The warning is filed against `brainstorm`, the first step the stale answer would have skipped.

## R7. A no-spec branch in a repo with no definition of done

**Decision**: No special case. With no `verify` commands configured, `verification_block` returns `None`, so `implement` reads done as soon as the "no" is recorded, and the branch goes straight to `review`.

**Rationale**: That repo has already chosen to have nothing that checks implement. A spec-pipeline branch there reads implement done once its tasks are ticked, which is the same trust. The review step still requires every group to review HEAD, so the branch can't be reported complete without the panel.

## R8. `store-specs` and `review`

**Decision**: No ordering change. The review reader checks `implement`'s own reading, not its roll-up with `store-specs`.

**Rationale**: `store-specs` is a pass under `implement`, so while it's outstanding, `implement` is the current step and routing goes to `/store-specs` first. The review row may already show its count during that time, which is accurate. Making review wait for the roll-up would need `_infer_steps` to pass the previous step's state into a reader, which no reader takes today.

## R9. Where the shared function lives

**Decision**: `_review.pending_at_head`.

**Rationale**: `_review` already holds `coverage_from_state`, `unreviewed`, and `pending_lines`, so the function joins the code it composes. `_review` already imports `_review_config` and `_paths` at the top of the file, and neither imports `_evidence` or `_pipeline`, so the new import from `_evidence` adds no cycle.

## R10. The stall digest covers the review state

**Decision**: `_stall.digest` hashes `ev.review` after the three artifacts, and a stall on `review` lists `review state` as unchanged.

**Rationale**: The digest reads only `spec.md`, `plan.md`, and `tasks.md`, which never change while `review` is current. Without the review state, a panel run that moves one group's last reviewed commit reads as no progress, and the stall bound stops a review that is moving. A stall message naming the three artifacts would also point the person at files the step doesn't read.

**Alternatives considered**: Leave the digest alone and accept stalls on `review`. We didn't choose this because the bound would fire after three panel runs that each completed a group, which is the working automation the bound is meant to leave alone.

## R11. The level-1 strings from design.md

**Decision**: The review annotation keeps the two strings design.md shows, with a count added to the first: `not reviewed yet (N commits)` and `N commits unreviewed since <short sha>`. The count is what FR-005 requires for every group. The `or, if it needs no spec: wfctl spec none --reason "…"` hint under `next` is dropped.

**Rationale**: The annotation strings are what the user approved at level 1, and `since` costs one field in `HeadCoverage` and up to three `git merge-base --is-ancestor` calls per pending group, made only for status. It's the newest of the group's last reviewed commit and the signed-off commit that's still on the branch. Every read is best-effort, and a failure gives `None`, which reads `not reviewed yet`. We didn't choose the first parent of the oldest unreviewed commit, because it fails on a root commit, names a merge after a merge from the trunk, and can land on a merged branch's side.

The hint is dropped because the spec question belongs before any code, where `/start-session` and `design-passes` step 1 already ask it with the three spec questions. A hint on every branch whose next step is brainstorm puts the skip one line below the default, where an agent reading the console could take it without answering the questions. An unattended run reads the payload and never sees the console hint, so the hint would reach only a person who already knows the command.

## R12. A blocked review row names the fix, not the panel

**Decision**: A config problem carries the remedy `fix review in the wfctl.json the error names, then run wfctl check config`. `pending_at_head` sets it where it catches the problem, since only that code knows the error's kind. The remedy doesn't name the trunk, because `required_at` also reports problems in the branch's own `wfctl.json`, and each problem already names its file. A trunk error carries no separate remedy, because its message already names the fix, such as `set trunk in wfctl.json` or `run git fetch --unshallow`. A capped reading carries the line `review start` prints when it refuses a capped group.

We didn't choose to pick the remedy in the review reader from the error text, because matching message text breaks when a message is reworded, and `498-the-fix-line-travels-with-the-reason.md` keeps the fix with the code that raises the reason.

**Rationale**: `next_step_content` returns a blocked step's own command, which here is `/fanning-out-code-review`. That command fails at `review start` on the same error, so a person reading only `next` is sent to a command that can't help. The remedy is the field every other blocked step uses to say what unblocks it.
