# Delivery Plan: Scan files for clarify and analyze (307)

**Feature**: `307-clarify-findings-in-repo` | **Date**: 2026-09-09
**Source**: `<spec-root>/307-clarify-findings-in-repo/tasks.md` (21 tasks)
**Parent issue**: #307

---

## PR Decomposition

| PR | Tasks | Files Touched | Size | Merge Condition |
|----|-------|--------------|------|----------------|
| #TBD | T001–T018 | `docs/architecture/the-scan-is-attested-where-the-reviewer-reads.md` (created), `docs/architecture/design/307-the-coverage-map-is-the-evidence.md` (created), `docs/architecture/scans/307-clarify.md` (created), `docs/architecture/scans/307-analyze.md` (created), `wfctl/agents/commands/speckit.clarify.md` (modified), `wfctl/agents/commands/speckit.analyze.md` (modified), `AGENTS.md` (modified), `tests/test_scan_files.py` (created) | S | The four commands in AGENTS.md § Definition of done green, plus the manual exercise of the changed wrappers |

**Rationale**: Single PR. The two wrapper edits are one instruction written twice
and share every test; splitting them would open a change whose only reviewer
question — "does the other one say the same thing?" — cannot be answered from
either half. The records and scan files are already on the branch and are the
evidence the wrapper edits are argued from, so they cannot land separately
without the argument arriving after the change it justifies.

**PR closes**: `Closes #307`

---

## Issue Grouping Map

| Issue | Tasks | Title | Estimate | Closes With |
|-------|-------|-------|----------|-------------|
| #307 | T001–T018 | `[307] clarify and analyze write a scan file into the repository` | S | PR #TBD |

**Grouping pattern**: Single issue
**Rationale**: One instruction, two wrappers, one test file. Nothing in the task
list is independently shippable — a wrapper that writes a scan file no test
asserts, or a test asserting an instruction no wrapper carries, is half a change
in either direction.

---

## Parallelization

One wave. No task in the list is blocked on another finishing except the tests
(T010–T012), which need T007 and T008 to exist to assert against, and the manual
exercise (T015), which needs all three installed.

---

## Issue creation

Not attempted. `wfctl status` reports:

```
will not notify anyone — nobody has allowed it for this work
```

No row above is waiting on a key — the grouping is single-issue and #307 already
exists — so the refusal costs this plan nothing. It is recorded because a plan
that created no issues and a plan that was not allowed to read identically.
