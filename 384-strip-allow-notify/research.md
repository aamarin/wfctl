# Research: Strip allow-notify

Nothing in Technical Context was marked NEEDS CLARIFICATION. What follows are
the choices the plan had to make that the spec left open.

## R1. The new wording of the host-permission line (FR-013)

- **Decision**: `your agent decides which commands may run — wfctl can't see\nits rules and says nothing about them`
- **Rationale**: The current line, "the agent has permission rules *of its own*", only made sense next to wfctl's grant. Without the grant, "of its own" suggests a second set of rules that doesn't exist. The new line says who decides, and keeps the second half ("can't see … says nothing"), which is still true. It is broken into two lines at the em dash, the same way as `_IRREVERSIBLE_NOTICE`, for the reason given in the comment there.
- **Alternatives considered**: deleting the line. Rejected: without the notify line, this is the only place `status` says a refusal can come from somewhere other than wfctl, and `report-block` depends on the reader knowing that.

## R2. What `report-action` prints

- **Decision**: `✓ recorded: <action>`. When the event lifts a standing hold, a second line follows: `  lifted the hold on <step> — it reads from its own artifacts again`. If that hold held no step (it was filed with no spec dir), the line is `  lifted the hold on <action>`.
- **Rationale**: This is the clarify answer. The wording reuses what `blocked --clear` prints today, so the release reads the same as before. `standing_blocks` is read before the append to find the matching hold, so the message is about the hold that was actually standing.
- **Alternatives considered**: reading holds after the append and comparing. That is two log reads to get the same answer.

## R3. Where `wfctl issue` gets the action name

- **Decision**: `_tracker.py` records `f"issue-{verb}"` for `verb in _RECORDED_VERBS = {"comment", "create", "label", "close"}`, and only when `section == "verbs"` and the command exited 0. This is the same condition that guards the recording today.
- **Rationale**: `384-an-action-is-named-by-the-verb-that-takes-it`. The `issue-` prefix is the CLI group name, so it matches what the skills already write.
- **Alternatives considered**: see that record's Considered section. Normalising the name when reading it was rejected because `_restart` would print a different name from the one the skills use.

## R4. What happens to leftover grant state

- **Decision**: nothing reads or deletes `notify.json`, `notify-resolved`, `notify-grant` or `notify-refused`. `wfctl log` still prints them as history.
- **Rationale**: Deleting files from a user's state dir is a destructive side effect that nothing asked for, and an unread file is harmless. `standing_blocks` never read those events, so no hold changes.
- **Alternatives considered**: a one-time cleanup in `wfctl start`. It would add code only to delete something that does no harm.

## R5. How skills behave at the three unattended sites

- **Decision**: in `end-session` step 5, `speckit-delivery-plan` step 6 and the "Filing" section of `speckit.analyze`, the "read `notify` first" block is replaced with one rule. Ask as the step already does. If nobody answers, try the action. If the host refuses, run `wfctl report-block issue-<verb> --reason "<what the host said>"`. The "Record what wfctl cannot see" paragraph in `end-session` keeps `wfctl report-action push` and drops the `--declined` line.
- **Rationale**: FR-015 and the first clarification. `speckit-delivery-plan`'s "a plan with unkeyed rows is a legitimate state" paragraph stays, but its cause becomes "the host refused the create", not "nobody granted".
- **Alternatives considered**: none were credible after level 1 settled Option A.

## R6. Architecture records

- **Decision**: add one log line, pointing to `wfctl-records-outward-actions-and-never-gates-them`, on `the-agent-reports-the-block-wfctl-never-saw`, `wfctl-classes-the-action-not-the-command` and `design/364-the-block-report-is-its-own-verb` (its successor is already named in the #384 level-3 record's frontmatter). Read `readiness-is-not-a-step-state`, `the-repo-names-the-fields-a-change-must-carry`, `design/299-facts-render-as-a-block` and `design/200-session-id-rides-on-the-start-event`. Add a log line only where the record states the grant as current behaviour. No status changes.
- **Rationale**: FR-018, and the precedent from last session: a successor that nobody has accepted doesn't get to mark its predecessor superseded.

## R7. Test files

- **Decision**:
  - Delete `test_notify_{dispatch,flag,declined,grant,status}.py`.
  - Rewrite `test_blocked_{cli,holds_step,events}.py` against `report-block` and `report-action`. Rename them `test_report_block_cli.py`, `test_report_block_holds_step.py` and `test_report_events.py`, and drop the `--clear` cases, keeping one test that an old `block-cleared` still lifts a hold.
  - In `test_four_facts.py`, drop the fourth fact and assert there are three. Rename the file to `test_status_facts.py`.
  - Edit the single-mention files: `test_agent_session`, `test_auto_approve_mode`, `test_change_cli`, `test_console_plaintext`, `test_decompose_issues`, `test_pipeline_commands`, `test_pipeline_payload_snapshot`, `test_pipeline_sections`, `test_pipeline_state_names`, `test_restart_hook_cli`, `test_session_is_open`, `test_skill_cross_references`, `test_stall`, `test_tasks_hold_a_task`, `test_tracker`, `test_unattended_pause_rules`, `test_worktree_guard`.
- **Rationale**: the spec's Validation Strategy. A test that checked the refusal is deleted rather than flipped. Each single-mention file is read before editing, because several of them only set up a grant in a fixture.
