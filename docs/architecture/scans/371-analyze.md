# Analyze scan — #371

## Session 2026-09-15

- Verdict: satisfied
- Scanned: spec.md, plan.md, tasks.md — all three present and read
- Findings: 4 · Critical: 0 · Acted on: 4 · Accepted: 0
- Detail: /Users/andremarin/Development/wfctl-specs/371-write-state-before-clear/checklists/analysis-report.md

Run unattended at the user's request ("run it unattended"). Every fix below is
confined to `spec.md` and `tasks.md` and decides nothing the design records had not.

### Coverage

| Pass | Status |
| --- | --- |
| A · Duplication | Resolved (1 LOW, spec fixed) |
| B · Ambiguity | Clear |
| C · Underspecification | Resolved (1 MEDIUM, 1 LOW, tasks fixed) |
| D · Constitution alignment | Clear (no constitution; plan's substituted gates from AGENTS.md and accepted records hold) |
| E · Coverage gaps | Clear |
| F · Inconsistency | Resolved (1 LOW, spec fixed) |
| G · Design-record contradiction | Clear (5 records read) |
| Requirement-to-task coverage | 100% |

### Findings

- **A · Duplication, LOW** — FR-010 restated FR-004's once-per-session rule for a successful send.
  → Fixed: FR-004 now owns the success path, including a session still over the threshold after a hold; FR-010 covers only retries of a send that failed or did not take. Decided against deleting FR-004: the plan and tasks cite it by number for the US1 rule.
- **C · Underspecification, MEDIUM** — T013 would test the hook in-process, but the worker waits for its parent pid to exit; pytest's never does, so the test would wait out the worker's 10 s cap and could not show the hook returns before the send.
  → Fixed: T013 runs the hook as a child process and asserts the child exits before the stub `workmux`'s send timestamp. Decided against passing a fake parent pid from the test: that exercises the worker (T012 already does) and not the hook's spawn.
- **C · Underspecification, LOW** — T001 and T034 wrote results to "implementation notes", which no artifact defines.
  → Fixed: T001 only confirms the three commands exit 0; T034 records its median in the PR description's testing section. Decided against adding a notes file to the plan: nothing downstream reads one.
- **F · Inconsistency, LOW** — the skip message's placeholder read `<worktree path>` in the spec and `<repo root>` in the contract.
  → Fixed: the spec reads `<repo root>`. Decided against changing the contract: the hook matches on the repo root it resolved (research R5), so that is what it can name.

Pass G, closest reading considered and not reported: `design/371-the-session-restart-sends-from-a-detached-worker` names `hook session-restart` in `cli.py` as the thin caller; T019 adds an `_entry.py` fast path beside that registration. The decision stays pure in `_restart.py` and `cli.py` still registers the command, so the task adds a caller rather than reversing where the decision lives.
