# Analysis scan for #40

## Session 2026-10-15

- Verdict: satisfied
- Scanned: spec.md, plan.md, tasks.md — all three present and read
- Findings: 9 · Critical: 0 · Acted on: 3 · Accepted: 6
- Detail: /Users/andremarin/Development/wfctl-specs/40-save-uncommitted-on-remove/checklists/analysis-report.md

### Coverage

| Pass | Status |
| --- | --- |
| A · Duplication | Clear |
| B · Ambiguity | Clear |
| C · Underspecification | Outstanding (1 MEDIUM, 1 LOW) |
| D · Constitution alignment | Clear (no constitution; checked against the plan's gates from AGENTS.md and the in-force records) |
| E · Coverage gaps | Resolved (2 MEDIUM, 1 LOW, tasks fixed) |
| F · Inconsistency | Outstanding (1 HIGH, 2 MEDIUM) |
| G · Design-record contradiction | Outstanding (1 HIGH) |
| Requirement-to-task coverage | 100% |

### Findings

- **G · Design-record contradiction, HIGH** — T019, T023, and T028 let the `to_unsaved` outcome go ahead with the removal, which reverses the rule in a proposed record.
  Record: `docs/architecture/design/40-archive-is-a-command-group.md`
  Decision: "For the same reason, any result for a spec dir inside the worktree that isn't a finished copy-out stops the removal, so a store that skips that spec dir as not its concern can't delete the only copy."
  Task: "`stops_removal` and `exit_code` for every outcome, inside and outside the worktree; `not_applicable` inside the worktree stops removal and still exits 0 by hand; the main checkout reads `not_applicable` and a bare layout reads `to_unsaved`" (T019), with `to_unsaved` not stopping per research R7.
  → Accepted: the record is proposed, so changing the tasks to match it would ratify it, and only Andre does that. The reason behind the rule still holds, since the spec files are saved under `unsaved/`, so the likely fix is an exception in the record. Filed as #600.
- **F · Inconsistency, HIGH** — SC-004 promises a squash-merged branch is never stopped, and the merge check in T009 stops one once trunk has changed the same lines. The plan review reproduced the conflict on git 2.44, and T007 tests only the case that passes.
  → Accepted: the fix is either narrowing SC-004 or changing the check, and neither is decided in the artifacts. Filed as #600.
- **F · Inconsistency, MEDIUM** — plan.md says only `StoreResult` decides whether a spec dir stops removal, and T028's first phase decides it from the copy-out plan.
  → Accepted: choosing between a dry-run store result and a second named decider is a design choice. Filed as #600.
- **F · Inconsistency, MEDIUM** — T023's `store(worktree, branch, overwrite)` differs from #359's `store(spec_dir, branch, repo_root)`.
  → Accepted: the signature has to be agreed with #359, which is outside these artifacts. Filed as #600.
- **C · Underspecification, MEDIUM** — nothing says what happens when `git ls-files --others` fails. Read as FR-013's unanswerable check, every untracked file is deleted; read as a failed copy, the removal stops.
  → Accepted: picking fail-open or fail-closed is a decision the spec didn't make. Filed as #600.
- **C · Underspecification, LOW** — no rule covers overlap between `save_on_remove` folders, untracked files, and the spec dir, so a listed folder that isn't ignored is copied twice and stops every removal.
  → Accepted: the overlap rule is a choice the plan left open. Filed as #600.
- **E · Coverage gaps, MEDIUM** — FR-033 requires earlier numbered archives to be left in place, and no task tested it.
  → Fixed: T026 now includes "a numbered archive written by an earlier removal is left where it was (FR-033)". Decided against a separate task: the case belongs with the hook's other end-to-end tests.
- **E · Coverage gaps, LOW** — research R4 makes a failing `git status` an FR-013 warning, and no task tested it.
  → Fixed: T006 now adds a test that a failing `git status` warns, names the check, and exits 0. Decided against leaving it to T008's description: a warning path with no test is the one most likely to be skipped.
- **E · Coverage gaps, MEDIUM** — the template's `pre_remove` comment, this repository's `.workmux.yaml` comment, and the `_archive._plan` row in `docs/ponytail-debt.md` all describe the old hook, and no task updated them.
  → Fixed: T032 now rewrites both `.workmux.yaml` comments and leaves this repository's command line alone (SC-005), and T042 now removes the `_archive._plan` row and updates the line locations. Decided against a new task: both edits sit in files those tasks already touch.

### Filing

- **Design choices #40's plan leaves open** — the pass G finding, the three pass F findings, and the two pass C findings. Filed as #600.
