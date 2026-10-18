# Delivery Plan: Release automation (571)

**Feature**: `571-release-automation` | **Date**: 2026-10-16
**Source**: `specs/571-release-automation/tasks.md` (48 tasks)
**Parent issue**: #571

---

## PR Decomposition

| PR | Tasks | Files Touched | Size | Merge Condition |
|----|-------|--------------|------|----------------|
| #602 | T001 - T048, except T044 | `.github/scripts/check_release_note.py` (created), `.github/scripts/release.py` (created), `.github/rulesets/main.json` (created), `.github/workflows/ci.yml` (modified), `.github/pull_request_template.md` (modified), `changes/571.none.md` (created), `pyproject.toml` (modified), `uv.lock` (modified), `wfctl.json` (modified), `AGENTS.md` (modified), `tests/conftest.py` (modified), `tests/test_release_note_check.py` (created), `tests/test_release_script.py` (created), `tests/test_ruleset.py` (created), `tests/test_install_config.py` (modified), `tests/test_shape.py` (modified) | L | `uv run pytest -q`, `uv run ruff check wfctl/ tests/`, `uv run mypy wfctl/`, and `uv run wfctl verify` all pass, and the `release-note` job's pass line names `#571` |

**Rationale**: Single PR. The change touches 16 files, which is past the size where the delivery skill asks for a split to be discussed, and Andre chose one PR on 2026-10-16. The check that requires a note and the script that reads the notes are two halves of one release process. About half of the 16 files are one-line edits: the lock file, `wfctl.json`, the note, the PR template, and a test comment.

We didn't split the check into its own PR, even though it is useful on its own. Splitting would mean a second issue and a second description for a change the plan, the records, and #602 already treat as one.

T044 is not part of the PR. Andre applies the ruleset after merge, because a required `release-note` check that no pull request reports yet would block every merge, this one included.

**PR closes**: `Closes #571`

---

## Issue Grouping Map

| Issue | Tasks | Title | Estimate | Closes With |
|-------|-------|-------|----------|-------------|
| #571 | T001 - T048 | `[571] Automate the release from a release note on every change, with main protected` | L | PR #602 |

**Grouping pattern**: Single issue
**Rationale**: One PR delivers the whole feature, so one issue tracks it, and that issue already exists.

---

## Parallelization Waves

| Wave | Mode | Tasks | Gate / Notes |
|------|------|-------|-------------|
| 0 | Sequential | T001 → T002 → T003 → T004 | T003 reads what T002 adds. T004 is the merge gate. |
| 1 | Sequential | T005 → T006 | The helper copies the towncrier table, so it needs T003. |
| 2 | Parallel | T007 - T011 ‖ T019 - T024 ‖ T038 ‖ T041 ‖ T045 | Each group writes a different file. The new tests must fail before Wave 3 starts. |
| 3 | Parallel | T012 → T013 → T014 → T015 → T016 → T017 → T018 ‖ T025 → T026 → T027 → T028 → T029 → T030 → T031 | The check and the release script share no file. Each track builds one file in order and ends on its merge gate. |
| 4 | Parallel | T032 → T033 → T034 → T035 ‖ T042 → T043 | Both need T017. T032 edits `ci.yml` after T017 has, and T034 uses a release commit that T028 can make. |
| 5 | Sequential | T036 → T037 → T039 → T040 | AGENTS.md describes both scripts, so this waits on Waves 3 and 4. T036 changes the drift test because `main`'s version of it fails once T037 lands. |
| 6 | Sequential | T046 → T047 → T048 | The full definition of done. |
| After merge | Andre | T044 | Andre applies the ruleset and reads it back. |

**Single-agent order**: T001 → T002 → T003 → T004 → T005 → T006 → T007 - T011 → T012 → T013 → T014 → T015 → T016 → T017 → T018 → T019 - T024 → T025 → T026 → T027 → T028 → T029 → T030 → T031 → T032 → T033 → T034 → T035 → T041 → T042 → T043 → T036 → T037 → T038 → T039 → T040 → T045 → T046 → T047 → T048, then T044 after merge.

---

## Agent Fanning Instructions

The only real parallelism is in Waves 2 and 3, where the check and the release script are built side by side. Every other wave is short or touches a file both tracks need, so one agent runs it.

**Wave 2 and 3 fanning (2 agents):**

**Agent A prompt:**
```
Build the release note check for #571 in the 571-release-automation worktree.
Read tasks.md, contracts/check-release-note.md, data-model.md, and research.md
in the feature folder (`uv run wfctl feature-paths` prints it). Do T007 - T011
first and confirm the tests fail, then T012 - T018 in order. Touch only
tests/test_release_note_check.py, .github/scripts/check_release_note.py,
wfctl.json, changes/571.none.md, and .github/workflows/ci.yml. Do not push.
```

**Agent B prompt:**
```
Build the release script for #571 in the 571-release-automation worktree.
Read tasks.md, contracts/release-script.md, data-model.md, and research.md in
the feature folder (`uv run wfctl feature-paths` prints it). Do T019 - T024
first and confirm the tests fail, then T025 - T031 in order. Touch only
tests/test_release_script.py and .github/scripts/release.py in the repository,
and contracts/release-script.md and plan-review.md in the feature folder. Do
not push.
```

**Fan-in gate after Wave 3:** `uv run pytest -q && uv run ruff check wfctl/ tests/ && uv run mypy wfctl/ && uv run wfctl verify`
