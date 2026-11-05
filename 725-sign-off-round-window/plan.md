# Implementation Plan: A sign-off opens a new window of review rounds

**Branch**: `725-sign-off-round-window` | **Date**: 2026-11-05 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `spec.md` in this folder

## Summary

A sign-off now records each review group's round count, and `review start` and `wfctl status` count a group's rounds from the latest sign-off through one function, `rounds_in_window`. The window size stays the cap `review start` reads. The sign-off still covers the commits it lists. Because a sign-off doesn't move a group's last reviewed commit, the first round in a new window reviews the commits the sign-off covered.

Design records read before this plan:

- `docs/architecture/review-round-window.md` (level 2, proposed): the behavior.
- `docs/architecture/design/725-sign-off-records-round-counts.md` (level 3, proposed): the sign-off stores each group's count, and one function counts the window. The plan follows it with no departure.

## Technical Context

**Language/Version**: Python 3.11+  
**Primary Dependencies**: `typer`, `rich`; nothing new  
**Storage**: `reviews/sign-off.json` in the branch's state folder gains a `rounds` object. The run records and the issue's round tally are unchanged.  
**Testing**: `uv run pytest -q`, with new unit tests in `tests/test_review.py`, CLI tests in `tests/test_review_cli.py`, and a status test in `tests/test_review_gate.py` or wherever `_capped` is tested today  
**Target Platform**: macOS and Linux shells, as today  
**Project Type**: CLI  
**Performance Goals**: no new git calls. The sign-off adds a few directory listings.  
**Constraints**: `_review.py` is imported by the guard on every matched command, so it keeps importing nothing that loads `typer` or `rich`. Minimal-complexity bias.  
**Scale/Scope**: one module (`wfctl/_review.py`), two commands in `wfctl/cli.py`, one skill (`opening-a-change`), one release note

## Constitution Check

_GATE: Must pass before Phase 0 research. Re-check after Phase 1 design._

The repository has no `.specify/memory/constitution.md`. The gates below come from `AGENTS.md`'s definition of done and code style, and that substitution is recorded under Complexity Tracking.

- [x] Validation plan exists: `uv run pytest -q`, `uv run ruff check wfctl/ tests/`, `uv run mypy`, `python3 .github/scripts/check_imports.py`, `uv run wfctl install-skills` then `uv run wfctl doctor`, plus the tests named in the Testing line and the quickstart walk.
- [x] Complexity is justified: one new function and one new field. The function exists so that `start` and `_capped` can't count the window differently (level-3 record).
- [x] Ownership is stated: wfctl counts the rounds since the latest sign-off, and the user opens a window by signing off (level-2 record, Owns truth). The agent can't count, since the cap exists to stop its loop.
- [x] New functions are annotated (`disallow_untyped_defs`).
- [x] Tests are named as sentences, with docstrings saying why they exist (`AGENTS.md`, Testing conventions).
- [x] No new import between contexts. Everything stays in `_review.py` and `cli.py`.

Re-checked after Phase 1: all gates still pass.

## Project Structure

### Documentation (this feature)

```text
725-sign-off-round-window/
├── design.md
├── spec.md
├── plan.md              # this file
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   └── cli-output.md
└── checklists/requirements.md
```

### Source Code (repository root)

```text
wfctl/
├── _review.py           # sign_off records rounds; rounds_in_window; start and _capped use it;
│                        # RoundCapReached and Started name the sign-off
├── cli.py               # review sign-off passes the round folder; review start's header and
│                        # sign-off line read the window
└── agents/skills/opening-a-change/SKILL.md   # the cap paragraph says a sign-off opens a window

tests/
├── test_review.py       # window counting, old sign-off file, no stacking, start after sign-off
├── test_review_cli.py   # header and refusal wording after a sign-off
└── test_review_gate.py  # status capped agrees with start (or the file that tests _capped today)

changes/725.change.md
```

**Structure Decision**: single project, no new module. The change sits in `wfctl/_review.py`, where the count and the sign-off already live.

## Implementation notes

1. `sign_off(agent_dir, sha, rounds_dir=None)`. With no `rounds_dir`, it counts in `agent_dir` alone, the same convention `start` uses. It writes `{"sha", "at", "rounds": {group: count}}`, where the groups are every name under `reviews/*/runs` in `agent_dir` or under `rounds/*` in the round folder, and the count is `max(runs_started, rounds_tallied)`.
2. `signed_off_rounds(agent_dir) -> dict[str, int]` reads the `rounds` object. A missing object, a value that isn't an object, or an entry that isn't a whole number of 0 or more reads as no entry, so the window falls back to the whole branch. That fails closed.
3. `rounds_in_window(agent_dir, group, rounds_dir) -> int` returns `max(0, used - recorded)`, where `used` is `max(runs_started, rounds_tallied)`.
4. `start` replaces its `rounds = max(...)` with `rounds_in_window`, keeps `rounds` as the window count on `Started`, and adds `Started.since`, the signed-off commit when the sign-off recorded a count for that group, otherwise None. `_tally_round` still receives the total count, not the window count, since the tally's own numbering is the total.
5. `RoundCapReached` takes an optional `since` and words its message as "… rounds since the sign-off at abc1234" when it's set.
6. `_capped` calls `rounds_in_window`.
7. In `cli.py`, `review sign-off` passes `resolve_round_dir(repo_root, branch)` to `sign_off`. `review start`'s header reads "round N of cap since the sign-off at abc1234" when `started.since` is set. The "the sign-off covers every commit left" line uses the same wording.
8. Existing tests that sign off at the cap and expect no run now get a run, since the window is open. They're rewritten so the sign-off comes before the runs that use the window, which keeps what each test was written to prove.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
| --- | --- | --- |
| Gates from `AGENTS.md` rather than a constitution | The repository has no constitution file. | A gate with no source is decorative. |
