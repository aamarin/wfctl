# Implementation Plan: Scan files in the spec folder

**Branch**: `598-scans-in-spec-folder` | **Date**: 2026-11-11 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `spec.md` in this folder.

## Summary

Clarify, plan review, and analyze write their scan file to
`FEATURE_DIR/scans/<step>.md` and stop committing it. wfctl's step readers in
`_evidence.py` check that file, so a step that skipped its scan stays current.
The plan review sign-off writes to the same file. Evaluation scans keep their
old path. The decision is `docs/architecture/scans-live-in-spec-folder.md`,
which supersedes `the-scan-is-attested-where-the-reviewer-reads`.

## Technical Context

**Language/Version**: Python 3.11+  
**Primary Dependencies**: `typer`, `rich`; no new ones  
**Storage**: Markdown files in the spec folder  
**Testing**: `uv run pytest -q`, `uv run ruff check wfctl/ tests/`,
`uv run mypy`, `python3 .github/scripts/check_imports.py`  
**Target Platform**: macOS and Linux shells  
**Project Type**: CLI  
**Performance Goals**: The check reads one small file per step; no target  
**Constraints**: No new imports between contexts. `_evidence.py` already
imports `_paths` and `_plan_review`. Minimal-complexity bias.  
**Scale/Scope**: Three step readers, one CLI command, one skill, three wrappers,
AGENTS.md, and their tests

## Design records

| Record | State | Bearing on the plan |
|---|---|---|
| `docs/architecture/scans-live-in-spec-folder.md` | proposed (this branch) | Sets the path, the check, and the warning for older features |
| `the-scan-is-attested-where-the-reviewer-reads` | superseded (this branch) | Its readers of the arch root keep excluding `scans/` |
| `a-rule-is-expressed-as-a-check` | accepted | The skipped scan is now visible in an artifact, so it becomes a check |
| `vendor-upstream-skills` | accepted | The spec-kit-derived `speckit-clarify` and `speckit-analyze` skills stay unedited; the change goes in the wrappers |
| `design-exceptions-live-with-specs` | accepted | Precedent for a per-branch file wfctl reads from the spec folder |

No level-3 record. `design.md` lists the three `brainstorm.software-design`
claims.

## Constitution Check

_GATE: Must pass before Phase 0 research. Re-check after Phase 1 design._

This repository has no `.specify/memory/constitution.md`. The gates come from
`AGENTS.md`, recorded in Complexity Tracking.

- [x] Validation plan exists: the four commands above, plus `wfctl doctor`,
      `wfctl check config`, `install-skills`, and one scan walked through the
      new path. Tests are listed under Project Structure.
- [x] Complexity is justified: two helper functions, one path function, one
      event reader, and three reason constants. No new module, class, or
      dependency.
- [x] Ownership is stated: wfctl checks whether a scan file exists with a
      verdict and a coverage row. The agent shouldn't answer, since it would be
      grading its own work, and the PR reviewer can't see the file.
- [x] Release note: `changes/598.change.md`.
- [x] Tests are sentences with a docstring saying why they exist, and pin
      `NO_COLOR` where they read output.
- [x] No edit to `check_imports.py` or `review.yml`, which CI takes from `main`.

## Project Structure

### Documentation (this feature)

```text
<FEATURE_DIR>/
├── design.md
├── spec.md
├── plan.md
├── scans/clarify.md
├── checklists/requirements.md
└── tasks.md            (next step)
```

No `research.md`, `data-model.md`, or `contracts/`. The one data shape is the
scan file's, and `writing-a-scan-file` already defines it.

### Source Code (repository root)

```text
wfctl/_paths.py
  SCANS_DIR stays. Its comment says new pipeline scans live in the spec folder,
  and the arch-root subtree holds older ones and evaluation scans.
  New: spec_scan(spec_dir, step) -> Path, returning spec_dir / SCANS_DIR / f"{step}.md".

wfctl/_evidence.py
  New: SCAN_MISSING, SCAN_NO_VERDICT, SCAN_NO_ROWS reason constants.
  New: scan_reason(spec_dir, step) -> str | None.
    1. File missing → SCAN_MISSING.
    2. No line matching ^- Verdict: (satisfied|unsatisfied|inconclusive)\b → SCAN_NO_VERDICT.
    3. No table row whose last cell starts with Clear|Resolved|Deferred|Outstanding
       → SCAN_NO_ROWS.
    The whole file is read (spec Clarifications).
  One private helper, _scan_hold(spec_dir, step, later_done, command):
    No scan reason → None (the caller returns its own done).
    A reason and later_done → Assessment("done", reason, remedy=f"  run {command}").
    A reason otherwise → Assessment("in_progress", None, reason).
    The held reading puts the text in `display` with `reason` None, exactly
    as plan_review holds today. A reason on the current step makes it blocked
    and never automatic (_pipeline.build_report, next_step_content), so an
    unattended run would stop instead of going back to the step (PR-002).
  clarify(): where it returns "done", call _scan_hold(..., "clarify",
    plan.md exists, "/speckit.clarify").
  analyze(): report present → _scan_hold(..., "analyze", delivery.md exists,
    "/speckit.analyze").
  plan_review(): at both points it returns "done" (the sign-off row and the
    last row) → _scan_hold(..., "plan-review", bool(ev.tasks_text), "/plan-review").
  The display strings are the three constants, unchanged, in all three steps.

wfctl/_plan_review.py
  append_sign_off(scan_path, identity, reason, compared, issue) takes the issue
  for the heading, since the name is now plan-review.md. With issue "unknown"
  the heading is "# Plan review scan".
  New: sign_off_reasons(agent_dir, branch) -> list[str], read from the same
  `sign-off` events sign_offs reads.

wfctl/cli.py
  step sign-off: scan = spec_scan(spec_dir, "plan-review"). Drop the
    touched_on_this_branch check, its undo, the "Commit it" line, and the
    no-issue-key refusal, whose reason was the old file name. Print
    "Written to <scan>".
  _exception_findings (check-body): also report each sign_off_reasons entry
    the body doesn't carry, as "the plan sign-off's reason isn't in the body".
    It reads the state dir through _resolve_context's agent dir.

wfctl/agents/skills/writing-a-scan-file/SKILL.md
  Destination: FEATURE_DIR/scans/<step>.md from `wfctl feature-paths`.
  No commit, no arch check. The step reader checks the file, and
  `wfctl store specs` saves it. States the `- Verdict: <value>` line and a
  coverage table as what the reader matches (PR-007).
  The `#unknown` and out-of-tree arch root refusals move under the evaluation
  section, which is the only kind still written under the arch root (PR-005).
  Evaluation: keeps <arch-root>/scans/<issue>-evaluation.md, the mkdir, the
  scoped commit, and `wfctl arch check`.

wfctl/agents/commands/speckit.clarify.md, speckit.analyze.md, plan-review.md
  File lines, descriptions, allowed-tools, and the commit sentences.
  Every sentence that says the PR reviewer reads the scan now says wfctl's
  step reader does (analyze around lines 232, 287, 333 - 341; clarify around
  line 123) (PR-005).
  plan-review.md §1: a mode row for `no scan file`, `scan file has no verdict`,
  and `scan file has no coverage rows`: write the scan section from the
  existing report, with no new review and no plan copy (PR-003).

wfctl/agents/skills/opening-a-change/SKILL.md
  Copy each plan sign-off reason into the PR body beside the design
  exceptions' reasons.

AGENTS.md
  The scans/ paragraph under Architectural constraints, and the step
  sign-off's PR body rule beside `step none`'s.

changes/598.change.md

tests/conftest.py (PR-006)
  New write_scan(feature, step). write_plan_review writes the plan-review scan
  too, since a review that ran writes both. stage_upstream_of writes the
  clarify scan with the spec and the analyze scan with the analysis report.
  Every test that stages these steps through the helpers keeps passing.

tests/test_scan_files.py, tests/test_plan_review_signoff.py,
tests/test_plan_review_skill.py, and a new tests/test_scan_reader.py
  Reader states from spec User Stories 2 and 3, and that a held reading
  routes automatically. Sign-off and check-body from Story 4. Skill and
  wrapper text from Stories 1 and 5.
```

**Structure Decision**: The helper sits in `_evidence.py` beside the readers
that call it. `_paths.spec_scan` holds the path so the sign-off in `cli.py` and
the readers can't disagree about it.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
| --- | --- | --- |
| Gates taken from `AGENTS.md` instead of a constitution | The repo has no constitution file | A gate with no source is decorative |
