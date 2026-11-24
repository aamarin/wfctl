Implementation complete: 2026-11-23

## Tasks at completion

~~~~markdown
# Tasks: Install asks before changing a settings file

**Input**: Design documents from the spec folder for `859-ask-rule-literal-star`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/install-question.md, quickstart.md
**Design records**: `docs/architecture/design/settings-changes-ask-once.md` (level 3, proposed), bound by `docs/architecture/settings-edit-asks-first.md` (accepted)

**Tests**: Every task names its test. New tests go in `tests/test_settings_ask.py`, with `NO_COLOR` pinned and `_interactive` patched for each case. Write each story's tests first and watch them fail before the implementation task that follows them.

Two points the last plan review left open are settled here, so the implementer doesn't need to choose:

1. Every file that ends `declined`, `skipped`, or `failed` gets the `left unchanged` warning, printed once by `_save_settings`'s caller. The plan's later sentence that names only `declined` and `skipped` is superseded (PR-015).
2. `_rule_removed` checks that the file exists with `path.exists()`, the same test `_permission_drift` uses today, not `copy.existed`. A dangling settings symlink then behaves as it does today (PR-016).

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story the task belongs to (US1 to US4)

---

## Phase 1: Setup

**Purpose**: The test file and its fixtures, shared by every story.

- [X] T001 Create `tests/test_settings_ask.py` with fixtures that build a temporary repo holding a `.claude/settings.json` (and a `.bob/settings.json` variant), a manifest with receipts, a helper that patches `wfctl.cli._interactive`, and a helper that patches `typer.confirm` to return an answer or raise; verify with `uv run pytest tests/test_settings_ask.py -q` collecting with no errors

---

## Phase 2: Foundational (the shared copy)

**Purpose**: The four passes stop reading and saving the file themselves and edit one copy per file. Install behaves exactly as today at the end of this phase, since the save step saves without asking. That keeps the refactor reviewable on its own, with the existing suite as its check.

**⚠️ CRITICAL**: No user story work starts until this phase is complete.

- [X] T002 Add `_SettingsChange` (NamedTuple: `sign`, `kind`, `entry`, `why`) and `_SettingsCopy` (dataclass: `rel`, `existed`, `settings`, `problem`, `read_bytes`, `parsed`, `changes`) beside `_read_settings` in `wfctl/cli.py`, per `data-model.md`; verify with `uv run mypy`
- [X] T003 Add `_load_settings(repo_root, rel) -> _SettingsCopy` in `wfctl/cli.py`. `existed` is `exists() or is_symlink()`. A file holding zero bytes or only whitespace reads as `{}` with `parsed` false, without calling `_read_settings`. Any other file goes through `_read_settings`, and `read_bytes` holds the bytes read; verify with new tests in `tests/test_settings_ask.py` for a missing file, a zero-byte file, a whitespace-only file, a valid file, and an unparseable file
- [X] T004 Add `_rule_removed(repo_root, copy, receipts, rule, kind) -> bool` in `wfctl/cli.py`. It's true only when the rule has a receipt (any `added` value), `(repo_root / copy.rel).exists()` is true, `copy.parsed` is true, and the rule isn't in `copy.settings`. Rewrite `_permission_drift` to call it so the two can't drift apart; verify with the existing `_permission_drift` tests passing unchanged, plus new tests in `tests/test_settings_ask.py` for a fresh clone with a committed manifest, a zero-byte file with receipts, an unparseable file, a dangling symlink, and a removed rule with `added` true and false
- [X] T005 Change `_merge_hooks` in `wfctl/cli.py` to take `copies: dict[str, _SettingsCopy]`, call `merge_hook` and `prune_unshipped` on the copy, and append `+`, `~`, or `-` changes. The `why` for `+` and `~` is the hook's `_HOOK_GONE` line with the leading "is gone — " trimmed. A `ValueError` from `merge_hook` stays this pass's own printed problem. A copy with `settings is None` is skipped, and the prior receipts are returned; verify with `uv run pytest tests/test_install_hook_merge.py -q`
- [X] T006 Change `_merge_permissions` in `wfctl/cli.py` to take the copies, call `merge_permission` on the copy, append `+` with `_ManagedRule.cost`, and skip a rule `_rule_removed` reports unless `--force` is set; verify with `uv run pytest -q -k permission`
- [X] T007 Change `_retire_permissions` in `wfctl/cli.py` to take the copies, call `remove_permission` on the copy, and append `-` with "wfctl no longer ships this". Keep its shipped-path and symlink checks; verify with `uv run pytest -q -k retire`
- [X] T008 Change `_unmerge_bob_tool_allows` in `wfctl/cli.py` to take a copy for `.bob/settings.json`, call `remove_tool_allow` on it, and append `-` changes. Keep its outside-the-repo and symlink checks. In `uninstall_skills_cmd`, build that copy and save it with `_write_settings` directly, so uninstall still doesn't ask (FR-012); verify with `uv run pytest -q -k bob` and a new test in `tests/test_settings_ask.py` where `uninstall-skills --yes` with `_interactive` false removes wfctl's entries from both settings files and never calls `typer.confirm` (Accepts 4)
- [X] T009 Add `_save_settings(copies, *, ask: bool) -> dict[str, str]` in `wfctl/cli.py`. In this phase it saves every changed copy and returns `saved` or `created`, or `failed` on `OSError`. Wire install to load each copy once, run the four passes in today's order, and call it once. Leave the existing summary block printing for now; verify with `uv run pytest -q` all green, which is this phase's evidence that behavior didn't change
- [X] T010 Add a test in `tests/test_settings_ask.py` asserting that one install that changes three hooks and eight rules calls `_write_settings` once per path (SC-003, FR-003); verify with `uv run pytest tests/test_settings_ask.py -q`
- [X] T011 Validate Phase 2 with `uv run pytest -q`, `uv run ruff check wfctl/ tests/`, and `uv run mypy` — merge gate

**Checkpoint**: The passes share one copy, install saves each file once, and nothing a user sees has changed.

---

## Phase 3: User Story 1 - Approve settings changes at a terminal (Priority: P1) 🎯 MVP

**Goal**: At a terminal, install lists every change for an existing settings file and asks once. A yes saves once, and a no leaves the file byte-identical.

**Independent Test**: In a repo whose settings file is missing one shipped rule, patch `_interactive` to true. A yes adds the rule in one save, and a no leaves the file byte-identical.

**Verification**:

- Automated: `uv run pytest tests/test_settings_ask.py -q -k "terminal or question"`
- Manual: the user runs `uv run wfctl install-skills --agent claude` in this worktree at a desktop terminal and answers the question.
- Evidence: one question per file, one save on a yes, and byte-identical bytes on a no.

### Tests for User Story 1 ⚠️

- [X] T012 [P] [US1] Test: a yes with hooks and rules pending asks once and saves once, counting `typer.confirm` and `_write_settings` calls per path (Must let through 1), in `tests/test_settings_ask.py`
- [X] T013 [P] [US1] Test: a no leaves the file byte-identical, the manifest keeps the prior receipts for it, and the `left unchanged` warning names the command (US1 scenario 4). A second install at a terminal then lists the same changes again (spec edge case "The user declines"). An empty answer at a real `typer.confirm` prompt, fed through `CliRunner(input="\n")`, is a no (FR-005), in `tests/test_settings_ask.py`
- [X] T014 [P] [US1] Test: the question's text matches `contracts/install-question.md`, with each `+` and `~` line carrying its cost line and each `-` line saying "wfctl no longer ships this" (US1 scenario 2), in `tests/test_settings_ask.py`
- [X] T015 [P] [US1] Test: a `{}` settings file holding every retired rule and a pruned hook yields changes of every kind, and none has an empty `why` (FR-013); and every `_HOOK_GONE` value starts with "is gone — ", in `tests/test_settings_ask.py`
- [X] T016 [P] [US1] Test: `typer.Abort`, `EOFError`, and `KeyboardInterrupt` raised from the patched confirm each leave the file byte-identical, and the manifest still records the copied skills, in `tests/test_settings_ask.py`
- [X] T017 [P] [US1] Tests for the two `failed` cases, in `tests/test_settings_ask.py`:
  1. A file changed from inside the patched confirm before a yes is left as changed, and install prints the contract's changed-during-the-question line and then the `left unchanged` warning.
  2. A yes whose `_write_settings` raises `OSError` leaves the file's old content, keeps the prior receipts, prints the path and the error and then the warning, and install exits 0 (spec edge case "Saving the file fails").
- [X] T018 [P] [US1] Test: rule text in a manifest receipt holding rich markup prints literally in the question, in `tests/test_settings_ask.py`
- [X] T019 [P] [US1] Test: a zero-byte settings file is asked about, and a yes writes the managed entries into it, in `tests/test_settings_ask.py`
- [X] T020 [P] [US1] Test: with both settings files pending, an install under `--agent bob` and then one under `--agent claude` each ask once about their own file. `--agent` takes one value, so US1 scenario 5 is two runs, in `tests/test_settings_ask.py`

### Implementation for User Story 1

- [X] T021 [US1] In `_save_settings` in `wfctl/cli.py`, when `ask` is true and the file existed, print the question per `contracts/install-question.md`, with every `entry` and `why` through `escape()` and `soft_wrap=True`, then call `typer.confirm("Apply them?", default=False)`. A yes is `saved`, and a no is `declined`; verify with T012, T013, T014, and T018
- [X] T022 [US1] In `_save_settings`, treat `typer.Abort`, `EOFError`, and `KeyboardInterrupt` from the prompt as `declined` and move on to the next file; verify with T016
- [X] T023 [US1] In `_save_settings`, before a yes is saved, read the file again and compare it with `read_bytes`. If it differs, print the contract's changed-during-the-question line, write nothing, and return `failed`; verify with T017
- [X] T024 [US1] In `install_skills_cmd` in `wfctl/cli.py`, call `_save_settings(copies, ask=_interactive())`. For each file ending `declined`, `skipped`, or `failed`, replace the passes' receipts for that path with the manifest's prior receipts (FR-007) and print the `left unchanged` warning with the change count and the command from `_runner(repo_root)`, carrying `--from` when the run had one (FR-008). `--yes` is never passed to `_save_settings` (FR-002); verify with T013 and T017
- [X] T025 [US1] In `install_skills_cmd`, print `✓ <path> updated (N changes)` after a `saved` file. The old "Merged wfctl's managed entries into …" block stays until T035 removes it, so the existing tests that assert on it stay green in between; verify with T012
- [X] T026 [US1] Validate US1 with `uv run pytest tests/test_settings_ask.py -q` — merge gate

**Checkpoint**: At a terminal, install asks once per file and saves once on a yes.

---

## Phase 4: User Story 2 - An unattended install leaves the file alone (Priority: P1)

**Goal**: With no terminal, install copies the skills, leaves an existing settings file byte-identical, and prints one warning per file.

**Independent Test**: Run each "Must keep catching" command from `settings-edit-asks-first.md` against an existing settings file that needs a change, and compare the bytes before and after.

**Verification**:

- Automated: `uv run pytest tests/test_settings_ask.py -q -k unattended`
- Evidence: byte-identical files for all six items, skills still copied, and exit 0.

### Tests for User Story 2 ⚠️

- [X] T027 [P] [US2] Tests, one per "Must keep catching" item (SC-001), each with `_interactive` patched false and the settings bytes compared before and after, in `tests/test_settings_ask.py`:
  1. `install-skills --yes --agent claude` adding an entry
  2. `install-skills --agent claude` with stdin from `/dev/null`
  3. `install-skills --prune --yes --agent claude`
  4. `install-skills --force --yes --agent claude` with a receipted rule removed
  5. `install-skills --yes --agent claude` removing a retired rule
  6. `install-skills --yes --agent bob`
- [X] T028 [P] [US2] Test: the same unattended run prints one `left unchanged` warning per file with the change count and the command, still copies every skill, template, and script, and exits 0 (US2 scenarios 2 and 3), in `tests/test_settings_ask.py`

### Implementation for User Story 2

- [X] T029 [US2] In `_save_settings`, when `ask` is false and the file existed, return `skipped` without opening the file for writing. In the same task, the existing tests that run install on an existing settings file and expect it changed get `_interactive` patched true and a yes, since this is the task that stops them saving; verify with T027, T028, and `uv run pytest -q` green
- [X] T030 [US2] Update the `--yes` option's help text in `wfctl/cli.py` to say it skips the overwrite prompt and never answers the settings question; verify with `uv run wfctl install-skills --help`
- [X] T031 [US2] Validate US2 with `uv run pytest tests/test_settings_ask.py -q` — merge gate

**Checkpoint**: No unattended run changes an existing settings file.

---

## Phase 5: User Story 3 - A new worktree still gets its settings file (Priority: P1)

**Goal**: A settings file that doesn't exist is created with every shipped hook and rule, without a question, and the user sees what was added.

**Independent Test**: Run install with no terminal in a repo with no settings file, and check that the file is created with every shipped hook and rule.

**Verification**:

- Automated: `uv run pytest tests/test_settings_ask.py -q -k created` and `uv run pytest tests/test_install_hook_merge.py -q`
- Evidence: the file exists with every entry, no prompt was called, and the change list printed.

### Tests for User Story 3 ⚠️

- [X] T032 [P] [US3] Test: no settings file and no terminal creates the file with every shipped hook and rule, never calls `typer.confirm`, and prints the change list followed by `✓ <path> created (N changes)` (Must let through 2, US3 scenario 1), in `tests/test_settings_ask.py`
- [X] T033 [P] [US3] Test: a committed manifest with receipts and no settings file creates the file with every receipted rule, in `tests/test_settings_ask.py`
- [X] T034 [P] [US3] Test: an install with `--yes` and no terminal that changes no settings file copies the skills and prints no settings warning (Must let through 3, US3 scenario 2), in `tests/test_settings_ask.py`

### Implementation for User Story 3

- [X] T035 [US3] In `_save_settings`, save a copy whose file didn't exist without asking, return `created`, and have install print the same change list the question would show, without the `Apply them?` line, then `✓ <path> created (N changes)`. Remove the "Merged wfctl's managed entries into …" block and its "It also now denies", "asks", and "No longer asks" lines, and rewrite the comment above the merge that says it runs without a prompt; verify with T032 and T033
- [X] T036 [US3] In the same change as T035, rewrite the three tests in `tests/test_install_hook_merge.py` that assert on the removed summary block (lines 927, 1446, and 1518) to assert on the change list. The test at line 1533 asserts the block's absence and needs no change; verify with `uv run pytest tests/test_install_hook_merge.py -q`
- [X] T037 [US3] Validate US3 with `uv run pytest tests/test_settings_ask.py tests/test_install_hook_merge.py -q` — merge gate

**Checkpoint**: A new worktree comes up with the guard's hook and the ask rules, and the user sees each one.

---

## Phase 6: User Story 4 - Doctor reminds the user of pending changes (Priority: P2)

**Goal**: Doctor lists each pending settings change as a warning with the install command, and never fails the run over it.

**Independent Test**: Skip a change with an unattended install, run doctor, and check that it warns, prints the command, and exits 0.

**Verification**:

- Automated: `uv run pytest tests/test_settings_ask.py -q -k doctor`
- Manual: `uv run wfctl doctor` in this worktree before and after the user's attended install.
- Evidence: the warning lines match the contract's doctor block, and the exit code is 0 when nothing else is wrong.

### Tests for User Story 4 ⚠️

- [X] T038 [P] [US4] Test: doctor reports a missing hook, a shipped rule never added, and a retired rule still present, each in the contract's doctor format with the command, and exits 0 (Must let through 4, US4 scenarios 1 to 3, SC-004), in `tests/test_settings_ask.py`
- [X] T039 [P] [US4] Test: with nothing pending, doctor prints no settings line (US4 scenario 4), in `tests/test_settings_ask.py`
- [X] T040 [P] [US4] Test: doctor doesn't list a receipted rule the user removed as pending, and `_check_managed_permissions` warns about it once, with `added` true and with `added` false, in `tests/test_settings_ask.py`
- [X] T041 [P] [US4] Test: an unparseable settings file is reported once by install and once by doctor, and stays byte-identical, in `tests/test_settings_ask.py`

### Implementation for User Story 4

- [X] T042 [US4] Add `_check_pending_settings(repo_root, manifest) -> None` in `wfctl/cli.py`. For each agent layer on record with a settings file (`claude`, `bob`), it loads the copies, runs the four passes with the manifest's receipts and no `--force`, and prints each file's changes in the contract's doctor format with the run-in-your-terminal line. It reports an unparseable file once, never saves, and never touches the exit code; verify with T038, T039, and T041
- [X] T043 [US4] Replace `_check_managed_hooks` and `_check_retired_permissions` with `_check_pending_settings` in doctor in `wfctl/cli.py`, and remove both from doctor's exit-code list (FR-011); verify with T038
- [X] T044 [US4] Change `_check_managed_permissions` in `wfctl/cli.py` to call `_rule_removed` and drop its `added` filter. For a receipt with `added` false, the warning says the rule is gone without saying wfctl installed it; verify with T040
- [X] T045 [US4] In the same change as T043, rewrite the existing tests that call `_check_managed_hooks` or `_check_retired_permissions`, or assert doctor exits 1 on a stale hook or a retired rule, to the new check and exit 0; verify with `uv run pytest -q`
- [X] T046 [US4] Validate US4 with `uv run pytest -q` — merge gate

**Checkpoint**: A skipped change shows up in every doctor run until the user applies it.

---

## Phase 7: Polish & Cross-Cutting Concerns

- [X] T047 [P] Rewrite `changes/859.fix.md` to say the next install asks before removing the old `--project` ask rule, and an install with nobody at a terminal leaves the file alone until the user runs install themselves (FR-014); verify with `uv run wfctl verify` passing its release-note check
- [X] T048 [P] Add a section to `wfctl/agents/skills/start-session/references/doctor-repair.md` saying a pending settings warning can't be repaired from the session. The agent reports it verbatim in step 7 and doesn't run install with a faked terminal; verify with `uv run wfctl install-skills --agent claude` and reading the installed copy under `.claude/skills/start-session/references/`
- [X] T049 [P] Update the merge mode section of `docs/reference.md`: install asks before changing an existing settings file, and `--yes` doesn't skip the question; verify by reading the rendered section
- [X] T050 File a follow-up issue to amend `docs/architecture/install-modes.md`, whose merge-mode sentence "A managed hook missing or wrong is a finding and exits 1" this change supersedes (FR-015 keeps it unedited here); verify with the issue number recorded in the PR body
- [X] T051 Run `uv run pytest -q`, `uv run ruff check wfctl/ tests/`, `uv run mypy`, `uv run wfctl verify`, and `uv run wfctl doctor` — merge gate
- [ ] T052 Run `quickstart.md`'s steps. The attended install is the user's to run at a desktop terminal, and with it the `! [ -t 0 ] && echo terminal || echo no terminal` check from `scans/clarify.md`; verify with the user's report of the question and its answer

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: no dependencies.
- **Foundational (Phase 2)**: depends on Setup, and blocks every story. T002 → T003 → T004 → T005 to T008 → T009 → T010 → T011.
- **US1 (Phase 3)**: depends on Phase 2.
- **US2 (Phase 4)**: depends on Phase 2. T029 touches `_save_settings` beside T021, so run it after US1 to avoid a conflict in one function.
- **US3 (Phase 5)**: depends on Phase 2 and on US1. T035 removes the summary block, and T036 rewrites the tests that assert on it in the same change, so the suite stays green.
- **US4 (Phase 6)**: depends on Phase 2 and on T004 (`_rule_removed`). It's independent of US1 to US3.
- **Polish (Phase 7)**: depends on every story.

### Within Each Story

- Tests first, and watch them fail before the implementation task.
- Every implementation task in this feature edits `wfctl/cli.py`, so implementation tasks run in order and none is marked [P].

### Parallel Opportunities

- Every test task in a story is marked [P]. They share `tests/test_settings_ask.py` but add separate functions, so two agents can draft them in parallel and merge cleanly.
- US4's implementation (T042 to T045) can run alongside US1 to US3 once Phase 2 is done, since it touches doctor's code rather than install's.
- T047, T048, and T049 touch separate files.

## Parallel Example: User Story 1

```bash
Task: "T012 yes asks once and saves once"
Task: "T013 no leaves the file byte-identical"
Task: "T016 an interrupted prompt counts as declined"
Task: "T017 a file changed during the question isn't overwritten"
```

---

## Implementation Strategy

### MVP First

1. Phase 1 and Phase 2. The existing suite stays green, and install saves each file once.
2. US1 and US2 together. Shipping US1 alone would still change files unattended, which is the defect this feature fixes, so the two land as one slice.
3. US3, since US1 removes the summary block a created file relied on.
4. US4, then Polish.

### Logical PR Boundaries

One PR carries the whole feature. Phase 2 is a refactor with no visible change, and landing it alone would leave the defect in place for a release. US1 to US3 change one function's behavior together, and US4 changes what doctor says about the same state.

## Notes

- Each implementation task names its test or command.
- `install-modes.md` and `auto-approve-grant-asks-first.md` are not edited (FR-015).
- The agent applying changes after the user approves at Claude Code's prompt is out of scope and tracked in #860.
~~~~
