# Implementation Plan: Read review.commands from the trunk

**Branch**: `711-review-commands-from-trunk` | **Date**: 2026-11-03 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `specs/711-review-commands-from-trunk/spec.md`

## Summary

`wfctl review start` takes each non-Claude reviewer's command from `wfctl.json`
on the trunk, the same ref `trunk_rounds` reads `review.rounds` from. It warns
once per model whose command differs between the branch and the trunk. A model
with no command on the trunk is left out as unavailable. A trunk whose
`wfctl.json` can't be read, or whose commands aren't valid, stays refused by the
group check `review start` already runs first (research R4). The design is in
`docs/architecture/review-commands-from-trunk.md`, and `design.md` records that
level 3 needed no record.

## Technical Context

**Language/Version**: Python 3.11+
**Primary Dependencies**: `typer` and `rich`, already in use; nothing new
**Storage**: N/A. `run.json` keeps its shape, and the `command` it records now comes from the trunk.
**Testing**: `uv run pytest -q`, with new tests in `tests/test_review.py` and the CLI tests for `review start`; `uv run ruff check wfctl/ tests/`; `uv run mypy`
**Target Platform**: macOS and Linux, wherever `wfctl` runs
**Project Type**: CLI
**Performance Goals**: One extra `ls-tree` and `git show` of `wfctl.json` per `review start` (research R2).
**Constraints**: Only `wfctl/_review.py`, `wfctl/_review_config.py`, the `review start` command in `wfctl/cli.py`, and the two docs below change, since #698, #700, and #707 edit other functions in the same files. Minimal-complexity bias.
**Scale/Scope**: One command, one config key

## Constitution Check

_GATE: Must pass before Phase 0 research. Re-check after Phase 1 design._

The repo has no `.specify/memory/constitution.md`, so the gates below come from
`AGENTS.md` (see Complexity Tracking).

- [x] Validation plan exists: `uv run pytest -q`, `uv run ruff check wfctl/ tests/`, `uv run mypy`, `uv run wfctl doctor`, and a manual `uv run wfctl review start security` with an edited `review.commands` and `WFCTL_STATE_DIR` set to a scratch folder, so it uses none of this branch's review rounds.
- [x] Complexity is justified: no new abstraction or dependency. One dataclass mirrors `TrunkRounds`, and one pure function swaps commands on a `Group`.
- [x] Ownership is stated: the trunk's `wfctl.json` holds the commands, and wfctl reads them there (`review-commands-from-trunk.md`). The branch's copy only feeds a warning.
- [x] Every change commits a release note (`AGENTS.md` Releasing): `changes/711.change.md`.
- [x] Test names are sentences and docstrings say why the test exists (`AGENTS.md` Testing conventions), and output assertions pin `NO_COLOR`.
- [x] Imports respect the Context Map: `_review` already imports `_review_config`, and `cli.py` is wiring.

Re-checked after Phase 1: unchanged.

## Design

### `_review_config.py`

1. `parse_commands(review) -> tuple[dict[str, str] | None, list[str]]` wraps the
   existing `_commands`, so the trunk's copy is validated by the same rules
   `check config` applies to the branch. A missing key returns `({}, [])`.
2. `load_commands(repo_root) -> dict[str, str] | None` returns the working
   tree's `review.commands` for the warning only. A missing file, `review` key,
   or `commands` key returns `{}`, so a branch that drops every command still
   gets a warning per trunk command (SC-002). It returns None only when the file
   can't be read or the commands aren't valid, which `load` has already
   refused.
3. `with_commands(group, commands) -> Group` returns the group with every
   non-Claude reviewer's `command` replaced by `commands.get(model)`, which is
   None when the trunk has none.

### `_review.py`

1. `TrunkCommands(commands, ref)` holds the trunk's commands and the short
   name of the ref they were read from.
2. `trunk_commands(repo_root, timeout, *, branch)` reads `review.commands` from
   the ref `trunk_refs` returns first, as `trunk_rounds` does. No file, no
   `review` key, or no `commands` key gives `{}`. A read failure, a `review`
   that isn't an object, or commands `parse_commands` rejects raise
   `ReviewError` naming the ref. `review start` never reaches that raise, since
   the group check refuses the same file first, but a later caller that skips
   the group check gets a refusal rather than an empty map that would read as
   "the trunk sets no commands".
3. `_availability` marks a non-Claude reviewer with no command as unavailable.
   `start` takes `commands_ref: str | None = None` and passes it through, and
   the reason reads "no command in wfctl.json on <ref>", or "no command in
   review.commands" when no ref is given. Today that state can't occur, since
   `load` refuses a non-Claude model with no command, so no existing behavior
   changes.
4. `command_differences(branch, trunk, ref) -> list[str]` returns one warning
   line per model whose command differs, sorted by model name, worded as in
   `contracts/review-start-output.md`.

### `cli.py`, `review start` only

After `trunk_rounds`, call `trunk_commands` inside the same `try` that turns a
`ReviewError` into a `✗` line, print each line from `command_differences` when
the branch's commands loaded, and replace `chosen` with
`with_commands(chosen, trunk.commands)` before `_review.start`, passing
`commands_ref=trunk.ref`.

### Docs that describe where the commands come from

1. `wfctl/agents/skills/fanning-out-code-review/SKILL.md`, "A reviewer on another
   model": the command comes from `review.commands` in `wfctl.json` on the
   trunk, so in a repository you don't own, read the trunk's copy of the key.
2. `AGENTS.md`, "Declaring reviewers": wfctl reads `commands` from the trunk's
   `wfctl.json`, like `review.rounds`, and warns when the branch differs.

### Tests

Written failing first, in `tests/test_review_cli.py` unless noted:

1. The trunk sets codex to one command and the branch to another: the roster
   and `run.json` carry the trunk's, and one `⚠` line names the difference.
2. The branch adds a gemini command and reviewers the trunk lacks: those
   reviewers read unavailable, with the trunk-ref reason and the difference
   warning.
3. The trunk lists a custom group with codex reviewers and a codex command, and
   the branch removes both: starting that group prints the trunk's command and
   a warning that the branch sets no command for codex (spec User Story 2,
   scenario 2).
4. The branch and trunk agree: no command warning.
5. Unit tests in `tests/test_review.py` for `trunk_commands` (absent file, key,
   and object give `{}`; an invalid map raises) and in
   `tests/test_review_config.py` for `with_commands` and `load_commands`.
6. Existing tests that declare `review.commands` only on the branch now also
   declare it on `main` with `declare_on_main`, since the branch's copy no
   longer supplies the command.

## Project Structure

### Documentation (this feature)

```text
specs/711-review-commands-from-trunk/
├── design.md
├── spec.md
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/review-start-output.md
└── tasks.md
```

### Source Code (repository root)

```text
wfctl/
├── _review.py          # trunk_commands, command_differences, _availability
├── _review_config.py   # parse_commands, load_commands, with_commands
└── cli.py              # review start only
tests/
├── test_review.py
└── the existing CLI tests for review start
changes/711.change.md
```

**Structure Decision**: Single project. No new module.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
| --- | --- | --- |
| Gates come from `AGENTS.md`, not a constitution | The repo has no constitution file | Borrowing another project's gates would be false |
