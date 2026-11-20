---
description: 'Task list for #407, auto-approve has its own command'
---

# Tasks: Auto-approve has its own command

**Input**: Design documents from the feature's spec folder (`wfctl feature-paths`)
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/cli.md, quickstart.md

**Tests**: Every acceptance scenario in User Stories 1, 2, and 4 gets a unit
test, as the spec's Validation Strategy asks. Tests that touch output pin
`NO_COLOR` (`conftest.py`). Test names are sentences, and each docstring says
which failure the test catches.

**Design records**: none. `design.md` records no level-3 decision. This work
honors two level-2 records: `approval-mode-is-stored-intent`, which is
accepted, and `auto-approve-grant-asks-first`, which is proposed and needs the
user's acceptance before the PR opens.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: can run in parallel, since it changes a different file and doesn't
  depend on an unfinished task
- **[Story]**: the user story from spec.md

---

## Phase 1: Setup

**Purpose**: The release note the definition of done requires.

- [X] T001 Create `changes/407.addition.md` with `uv run towncrier create 407.addition.md --content "…"`, naming `wfctl auto-approve [on|off]`, the creation hook line, and the Claude Code prompt; load `writing-style` first; verify with `uv run wfctl verify` reporting the release note check green

---

## Phase 2: Foundational (blocks every user story)

**Purpose**: Every story reads or writes the mode through the evidence
package. The grant helper gains the `session` field, the event-first write
order, and the skip for a repeated `on`. The two readers the CLI needs go
beside it.

**⚠️ No user story starts until this phase passes.**

### Verification

- `uv run pytest -q tests/test_auto_approve_mode.py tests/test_auto_approve_command.py`
- `uv run mypy`

### Tests first

- [X] T002 [P] Add failing tests in `tests/test_auto_approve_mode.py`: a grant with `session="abc"` writes `session` on the `mode` event; a grant with `session=None` writes no `session` key; `on` while `mode.json` reads on and the newest `mode` event is a grant appends nothing and leaves `review_count` unchanged (FR-001, FR-014); `on` while `mode.json` reads on from a hand edit, with no event or with a revocation as the newest event, writes the grant; `on` after a revocation writes a new grant and restarts the count; `off` always writes; the event is appended before `mode.json` is written, so an `OSError` from `append_event` leaves `mode.json` as it was; an `OSError` from `write_atomic` after a successful append leaves the event in the log and `mode.json` at its old value (spec Edge Cases, first bullet)
- [X] T003 [P] Add failing tests in `tests/test_auto_approve_mode.py` for `last_change(agent_dir)`: it returns None with no `mode` events; it returns the newest event with no `by` field as a `ModeChange(on, ts, session)`; it skips the review cap's revocation (`by: "wfctl"`); an event written before this change, with no `session`, reads as `session=None`. Add tests for `newest_is_grant(agent_dir)`: False with no events, True when the newest `mode` event is a grant, False when it's a person's `off`, and False when it's the cap's revocation

### Implementation

- [X] T004 Change `grant_auto_approve(agent_dir, granted, session=None)` in `wfctl/evidence/_mode.py`: append the `mode` event, with `session` only when it isn't None, before `write_atomic`; when `granted` is True, `auto_approve(agent_dir)` reads on, and `newest_is_grant(agent_dir)` is True, write nothing; verify with T002
- [X] T005 Add `ModeChange` (a frozen dataclass with `on`, `ts`, and `session`), `last_change(agent_dir)`, and `newest_is_grant(agent_dir)` to `wfctl/evidence/_mode.py`, reading `events.jsonl` the way `review_count` already does and treating a malformed line as absent; verify with T003
- [X] T006 Export `ModeChange`, `last_change`, and `newest_is_grant` from `wfctl/evidence/__init__.py`, in both the lazy map and `__all__`; verify with `uv run python .github/scripts/check_imports.py` and `uv run mypy`
- [X] T007 Route `start --auto-approve` and `--no-auto-approve` in `wfctl/cli.py` (`start_cmd`, at its `grant_auto_approve(agent_dir, auto_approve)` call) through the changed helper with `session=caller`. Keep the call before `build_report` and the "Already initialized" return. Catch `OSError` and print `✗ Couldn't record the auto-approve change: <error>`, exit 1 (FR-008). Verify with a new test in `tests/test_auto_approve_mode.py` that `start --auto-approve` writes `session`, and that a second `start --auto-approve` doesn't reset `review_count`
- [X] T008 Create `tests/test_auto_approve_command.py`, where the plan places FR-009, with tests that `start` never reads `WFCTL_AUTO_APPROVE`. With the variable set to `1` and the mode revoked, `start` with no flag leaves the mode off (FR-009, US3 scenario 4, the record's "Must keep catching" case 5). With the variable set to `0` and the mode on, `start` with no flag leaves the mode on and appends no `mode` event (the record's "Must let through" case 5)
- [X] T009 Validate Phase 2 with `uv run pytest -q tests/test_auto_approve_mode.py tests/test_auto_approve_command.py` and `uv run mypy` — merge gate

---

## Phase 3: User Story 1, turn the mode on or off mid-session (P1) 🎯 MVP

**Goal**: `wfctl auto-approve on` and `off` change the mode from inside a
session, with no "Already initialized" line.

**Independent Test**: In a worktree with an open issue and a started session,
run `wfctl auto-approve on` and check that `wfctl status --json` reports
`auto_approve: true`. Run `off` and check that it reports `false`.

### Verification

- `uv run pytest -q tests/test_auto_approve_command.py`
- Quickstart's "Turn the mode on and off mid-session", run by hand

### Tests first

- [X] T010 [P] [US1] Add failing tests to `tests/test_auto_approve_command.py` for `on`: it grants, appends a `mode` event naming this session, and prints `✓ auto-approve — …` with no "Already initialized" line (scenario 1); a repeated `on` exits 0, prints the notice, and appends nothing (scenario 3); `session_holder == "other"` refuses with the two lines in contracts/cli.md, exits 1, and leaves the mode unchanged, both when another conversation holds the branch and when this conversation ran `wfctl end` (scenario 4, FR-004); a closed issue and a branch naming no issue refuse with `start`'s message and fix line (scenario 5, FR-005); a caller with no identity is allowed (scenario 6, FR-006); an `OSError` from the append prints `✗ Couldn't record the auto-approve change: <error>` and exits 1
- [X] T011 [P] [US1] Add failing tests to `tests/test_auto_approve_command.py` for `off`: it turns the mode off and appends a `mode` event (scenario 2); it runs while another session holds the branch, on a closed issue, and on a branch that names no issue (FR-002); it prints `✓ auto-approve off — design gates and review stops wait for a human`. Also test that an argument other than `on` or `off` exits 2

### Implementation

- [X] T012 [US1] Add the `auto-approve` command to `wfctl/cli.py` beside `start_cmd`, with an optional `on` or `off` argument. For `on`, run `_refuse_unless_the_issue_allows_a_session()` first, then `_resolve_context()`, then refuse when `build_report(...).session_holder == "other"`, then call `grant_auto_approve(agent_dir, True, session=caller)`. For `off`, run no check and call `grant_auto_approve(agent_dir, False, session=caller)`. Print the notices in contracts/cli.md. Verify with T010 and T011
- [X] T013 [US1] Validate User Story 1 with `uv run pytest -q tests/test_auto_approve_command.py tests/test_auto_approve_mode.py` and quickstart's first block run by hand — merge gate

---

## Phase 4: User Story 1, continued: Claude Code asks before the grant (FR-015)

**Goal**: In Claude Code, the user approves a prompt before the agent's `wfctl
auto-approve on` runs. This narrows the record's accepted case of an agent
granting itself the mode, so it belongs with the story that adds the command.

**Independent Test**: After `uv run wfctl install-skills --agent claude`,
`.claude/settings.json` carries both ask rules, and the agent's `wfctl
auto-approve on` prompts.

### Verification

- `uv run pytest -q tests/test_settings_merge.py tests/test_install_hook_merge.py`
- The manual Claude Code prompt check in T034

### Tests first

- [X] T014 [P] [US1] Add failing tests in `tests/test_settings_merge.py`: `merge_permission`, `permission_present`, `remove_permission`, and `related_rules` take a list name and work on `ask` the same way they work on `deny`; removing the last `ask` rule removes `ask`, and then an empty `permissions`; a manifest receipt with no kind reads as `deny`
- [X] T015 [P] [US1] Add failing tests in `tests/test_install_hook_merge.py`: `install-skills --agent claude` adds both ask rules and records each with the kind `ask`; deleting an ask rule from settings makes the next install refuse with `it now asks for:` and no mention of `cd`; `doctor` warns `⚠ claude: Bash(wfctl auto-approve on:*) is gone from .claude/settings.json` with the ask rule's own explanation; `uninstall-skills` removes both; an existing install upgraded to this version announces only the two ask rules, not `Bash(cd:*)`

### Implementation

- [X] T016 [US1] Change the permission helpers in `wfctl/install/_settings.py` (`_deny`, `permission_present`, `merge_permission`, `remove_permission`, and `related_rules`) to take the list name, `"deny"` or `"ask"`, instead of assuming `deny`. Update the module docstring's `permissions.deny` paragraph to cover both lists. Verify with T014
- [X] T017 [US1] Change `_managed_permissions` in `wfctl/cli.py` to return each rule with its list kind and its own explanation, and add `Bash(wfctl auto-approve on:*)` and `Bash(uv run wfctl auto-approve on:*)` as `ask` rules for `claude`. Record the kind in the manifest receipt, and read a receipt with no kind as `deny`. Verify with T014 and T015
- [X] T018 [US1] Update every caller of `_managed_permissions` in `wfctl/cli.py`: the install merge and refusal (near line 4450), uninstall (near line 4495), the install announcement (near line 5852), and `_check_managed_permissions` (near line 8586). Each prints the rule's own explanation. The announcement names only the rules this run added. The refusal lists related rules under `it now denies:` or `it now asks for:`. Verify with T015
- [X] T019 [US1] Validate Phase 4 with `uv run pytest -q tests/test_settings_merge.py tests/test_install_hook_merge.py tests/test_bob_settings_merge.py` — merge gate

---

## Phase 5: User Story 2, see who turned the mode on (P1)

**Goal**: `wfctl auto-approve` with no argument prints the mode and which
session made the last change, and never prints a session ID.

**Independent Test**: Grant the mode from one session, then run `wfctl
auto-approve` from that session and from a second one, and compare the
outputs.

### Verification

- `uv run pytest -q tests/test_auto_approve_command.py`

### Tests first

- [X] T020 [P] [US2] Add failing tests to `tests/test_auto_approve_command.py` for the bare command:
  1. "by this session" (scenario 1), and "by another session" (scenario 2).
  2. "by an unknown session" for an event written before this change, and for a caller with no identity (scenario 3).
  3. After the cap's revocation, the first line is `_revocation_line`'s form, and the second shows the grant the cap ended (scenario 4).
  4. "no grant on record" when the mode was never granted (scenario 5), and when `mode.json` reads on and the newest event isn't a grant, including a hand edit after a revocation.
  5. "turned off outside wfctl" when the mode reads off, wasn't revoked, and the last change turned it on.
  6. A person's `off` prints `turned off <ts> UTC by <relation>`.
  7. No output contains the session ID (scenario 6).
  8. The command creates no state dir on a branch wfctl never used, and exits 0 on a branch that names no issue.

### Implementation

- [X] T021 [US2] Add the bare form to the `auto-approve` command in `wfctl/cli.py`. Resolve the state dir with `resolve_agent_dir(create=False)` and skip `_remove_session_fossils`. Print the mode line as `_AUTO_APPROVE_NOTICE`, `auto-approve off`, or `_revocation_line(reason)`. Print the second line from `last_change` and `newest_is_grant` by the rules in contracts/cli.md, comparing `ModeChange.session` with the caller for the relation (research.md §4). Verify with T020

---

## Phase 6: User Story 3, start a scripted run in the mode (P2)

**Goal**: `WFCTL_AUTO_APPROVE=1 workmux add` brings a worktree up with the mode
on, and any other value leaves it attended.

**Independent Test**: Create one worktree with the variable set to `1` and one
without it, and compare `wfctl status --json` in each.

### Verification

- `uv run pytest -q tests/test_workmux.py`
- The manual `workmux add` check in T025

### Tests first

- [X] T022 [P] [US3] Add a failing test in `tests/test_workmux.py` that reads the grant line from the shipped `wfctl/agents/configs/workmux/.workmux.yaml` and runs it with `sh -c` against a stub `wfctl` on `PATH` that records its arguments. Run it with `WFCTL_AUTO_APPROVE` unset, `0`, `true`, `01`, and `1`. Only `1` calls `wfctl auto-approve on`, and every case exits 0, including with a stub that exits 1 (US3 scenarios 1 - 3, FR-010)

### Implementation

- [X] T023 [US3] Add `- cd "$WM_WORKTREE_PATH" && [ "$WFCTL_AUTO_APPROVE" = 1 ] && wfctl auto-approve on || true` as the last `post_create` entry in `wfctl/agents/configs/workmux/.workmux.yaml`; verify with T022
- [X] T024 [US3] Add the same entry, with `uv run wfctl`, as the last `post_create` entry in this repo's `.workmux.yaml`; verify by reading the file, and after T027 by checking that `uv run wfctl auto-approve` prints no note
- [x] T025 [US3] Hand the user the manual check, since the worktree guard refuses an agent running in a second worktree. From the main checkout, on a throwaway open issue, they run `WFCTL_AUTO_APPROVE=1 workmux add <issue>-auto-approve-check --base main` and check that `uv run wfctl status --json` in the new worktree reports `auto_approve: true`. They repeat it without the variable and expect `false`. Record their result — merge gate for US3

---

## Phase 7: User Story 4, find out an existing repo is missing the grant line (P3)

**Goal**: The bare `wfctl auto-approve` prints an `ℹ` note with the line to add
when `post_create` has no live grant line, and `doctor` says nothing about it.

**Independent Test**: Run `wfctl auto-approve` in a repo whose `.workmux.yaml`
lacks the line, add the line, and run it again.

### Verification

- `uv run pytest -q tests/test_workmux.py tests/test_auto_approve_command.py`

### Tests first

- [X] T026 [P] [US4] Add failing tests. In `tests/test_workmux.py`, `post_create_grants` is True for a live line under `post_create:`, and False for a commented-out line, for the line under another key, and for a file with no `post_create:`. In `tests/test_auto_approve_command.py`, the bare command prints the note with the entry unbroken (`soft_wrap`) when the line is missing (scenarios 1 - 3), prints no note when there's no `.workmux.yaml` (scenario 4), `on` and `off` print no note (scenario 6), the exit code is 0 either way, and `wfctl doctor` prints nothing about the line (scenario 5, FR-011)

### Implementation

- [X] T027 [US4] Add `GRANT_LINE` and `post_create_grants(text)` to `wfctl/install/_workmux.py` beside `post_create_wired`, using `_live_lines(text, "post_create")` and matching `auto-approve on`. Export both from `wfctl/install/__init__.py`, and print the note from the bare command in `wfctl/cli.py`. Verify with T026 and `uv run python .github/scripts/check_imports.py`
- [X] T028 [US4] Add a test in `tests/test_workmux.py` that `GRANT_LINE` equals the entry in the shipped `.workmux.yaml`, so the note can't drift from the seed. Then validate with `uv run pytest -q tests/test_workmux.py tests/test_auto_approve_command.py` — merge gate

---

## Phase 8: User Story 5, the agent's skills name the new command (P3)

**Goal**: An agent reading the installed skills learns `wfctl auto-approve
on|off`, the rule against granting the mode unasked, and how `install-config`
behaves.

**Independent Test**: After `uv run wfctl install-skills`, search the installed
skills for `start --auto-approve` and for the `install-config` explanation.

### Verification

- `uv run pytest -q tests/test_skills_reference_auto_approve.py`
- `uv run wfctl install-skills --agent claude`, then a read of the installed
  `using-wfctl` and `plan-walkthrough`

### Tests first

- [X] T029 [P] [US5] Create `tests/test_skills_reference_auto_approve.py` with failing tests: the shipped `using-wfctl` carries `auto-approve on` near "only when"; no shipped skill under `wfctl/agents/` tells the agent to run `wfctl start --auto-approve` to set the mode (SC-005); `plan-walkthrough`'s refusal names `wfctl auto-approve off`; `using-wfctl` says that `install-config` writes once and that `--force` replaces the repo's edits (FR-013)

### Implementation

Load `writing-style` before editing either skill.

- [X] T030 [P] [US5] Edit `wfctl/agents/skills/using-wfctl/SKILL.md`:
  1. Add a `wfctl auto-approve [on|off]` row to the command table.
  2. Cut the `wfctl start` row's `--auto-approve` sentence down to say the flag still works and to point at the new command.
  3. Under `## Commands`, after the table, add a paragraph telling the agent to run `wfctl auto-approve on` only when a person in this conversation asked for an unattended run or started it with `WFCTL_AUTO_APPROVE=1`, never on its own judgment, and that `off` is always allowed.
  4. Add the `install-config` explanation.

  Verify with T029
- [X] T031 [P] [US5] Edit the refusal in `wfctl/agents/skills/plan-walkthrough/SKILL.md` near line 40 so it names `wfctl auto-approve off` in place of `wfctl start --no-auto-approve`, and points at `using-wfctl`'s rule; verify with T029
- [X] T032 [US5] Run `uv run wfctl install-skills --agent claude`, read the installed `using-wfctl` and `plan-walkthrough` end to end, and check that the new text reads well and that the ask rules landed in `.claude/settings.json` — merge gate for US5

---

## Phase 9: Polish and cross-cutting

- [X] T033 [P] Update `docs/reference.md`: point the `start --auto-approve` mentions near lines 64, 113, and 338 at `wfctl auto-approve on`, and add a `wfctl auto-approve` command row; load `writing-style` first; verify with `grep -n "start --auto-approve" docs/reference.md` showing only the mention that says the flag still works
- [X] T034 Hand the user the Claude Code prompt check (PR-009). After `uv run wfctl install-skills --agent claude`, the agent runs `wfctl auto-approve on` and `uv run wfctl auto-approve on`, in the default permission mode and in auto mode, and the user records whether each one prompted. Record the four results in `scans/` beside the plan review so the PR body can cite them. The check is the last bullet of spec.md's Validation Strategy
- [X] T035 Run `uv run pytest -q`, `uv run ruff check wfctl/ tests/`, `uv run mypy`, and `uv run wfctl verify`
- [X] T036 Run `uv run wfctl doctor` and `uv run wfctl check config`, and confirm both are green
- [ ] T037 Run `wfctl store specs` to store the spec folder, which is implement's `store-specs` sub-step

---

## Phase 10: Codex and Bob Shell ask too

The user asked during T034 for the same protection in Codex and Bob Shell.
Codex reads a `prompt` rule from the project's `.codex/rules/`. Bob Shell can't
ask, so the guard refuses the command there. `auto-approve-grant-asks-first`
carries the decision and the threat model.

- [X] T038 Add failing tests in `tests/test_auto_approve_other_agents.py`: `codex execpolicy check` prompts on both forms of `on` and not on `off` or the read; `install-skills --agent codex` writes `.codex/rules/wfctl.rules`, records it, leaves a project rules file alone, and names the trust step; the guard refuses `on` and `start --auto-approve` for Bob Shell's two tool names, lets `off` through, and leaves Claude Code's `Bash` to its prompt
- [X] T039 Ship `wfctl/agents/codex/rules/wfctl.rules`, give `_AGENT_TARGETS["codex"]` the `.codex/rules` target, rewrite the Codex install notice, and add the Bob Shell refusal to `wfctl/guard/_hook.py`; rewrite the two `test_install_skills.py` tests that assumed Codex installs nothing
- [X] T040 Update `using-wfctl`, the release note, and `auto-approve-grant-asks-first`; load `writing-style` first
- [ ] T041 Hand the user the Codex and Bob Shell checks: in a trusted project, the Codex agent runs `wfctl auto-approve on` and the user records whether Codex asked; the Bob Shell agent runs it and the user records the refusal. Record both in `scans/manual-checks.md`

---

## Dependencies and execution order

- Phase 1 has no dependency.
- Phase 2 blocks every story, since every story reads or writes the mode
  through the grant helper and its readers.
- Phase 3 (US1) needs Phase 2.
- Phase 4 (FR-015) needs Phase 3 only for the command it guards. Its code is in
  `install/_settings.py` and the install paths of `cli.py`, so it can run
  alongside Phase 5.
- Phase 5 (US2) needs Phase 3, since it adds the bare form to the same command.
- Phase 6 (US3) needs Phase 3, since the grant line runs `wfctl auto-approve
  on`.
- Phase 7 (US4) needs Phase 5 for the bare form, and Phase 6 for the shipped
  line that `GRANT_LINE` must match.
- Phase 8 (US5) needs Phase 3 for the command it documents, and can run
  alongside Phases 4 to 7.
- Phase 9 comes last. T034 needs Phase 4 installed.

## Parallel opportunities

- T002 and T003 add tests to one file, so write them together. Neither blocks
  the other.
- T010 and T011 can be written together.
- Once Phase 3 is done, Phase 4 (T014 - T019), Phase 6's T022 - T023, and Phase
  8's T029 - T031 change different files and can run in parallel.
- T030 and T031 edit different skills.

## Implementation strategy

The MVP is Phases 1 to 3. They close the gap #407 reports: a grant made
mid-session from inside the workflow, with no "Already initialized" line.

Phase 4 comes next and has to land before the PR, since the proposed record
`auto-approve-grant-asks-first` describes it. Phases 5 to 8 follow in order,
and Phase 9 comes last.

T025 and T034 need the user at the keyboard. Hand each one over as soon as its
phase is done, so neither holds up Phase 9.
