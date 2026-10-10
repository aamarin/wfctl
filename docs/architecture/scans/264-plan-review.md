# Plan review scan for #264

## Review 2026-10-09T23:46Z

- Verdict: satisfied
- Reviewed: plan.md ffa7597574a89a97753a61209bc4776aed800e3f, spec.md 065f3733e0e3140eceef0336843d91aa811c1423, .specify/memory/constitution.md absent, design.md 5c686de27a6212a1692331fb32dcf695f7372772, docs/architecture/design/264-the-task-copy-lives-in-the-completion-record.md 73d6c1664f0986dd82400ff10a2165a1588547b9, docs/architecture/design/264-the-completion-command-is-a-step-verb.md 6938214375db57bbe96bd0992d114812fcf90749, docs/architecture/new-task-reopens-implement.md 800f96d21795ee68ef91441bb3373f62b82eea9e, research.md 25dee87fa74ae6ab9715ff5811edd63133f7040c, data-model.md aac2aa3e59090497e429651da8469dd2a2b5e76f, contracts/cli.md 0eacf07ff9625faad3e1e42f07d87a8a09a93642, quickstart.md 7c7eefea54d37ce9b806e11c8390a63dc9ec2438, checklists/requirements.md 3f61287371e0bafbc032dbdaa791ed2c1e3c3709
- Review type: full (no earlier report)
- Open: BLOCKER 0 · MAJOR 1 · MINOR 6 · Fixed since the earlier review: 0
- Detail: /Users/andremarin/Development/wfctl-specs/264-sentinel-goes-stale/plan-review.md

The review ran in a fresh-context subagent. The level-2 record
`new-task-reopens-implement` is named only in the prose of `design.md`, and it
was read because the plan rests on it.

### Coverage

| Check | Status |
| --- | --- |
| Deterministic checks | Outstanding (PR-003) |
| Requirements and traceability | Outstanding (PR-001) |
| Architecture and boundaries | Outstanding (PR-004) |
| Adversarial implementation and verification | Outstanding (PR-001, PR-002, PR-005, PR-006) |
| Security and reliability | Outstanding (PR-007) |

### Findings

- **PR-001, MAJOR, open.** A story that reopens with no `delivery.md` is sent
  to `decompose`, not to `implement`. Research R1 says the existing readers
  need no change, and the `decompose` reader reads `pending` once the tasks are
  open and no `delivery.md` exists. The hand reproduction in `quickstart.md`
  builds exactly that shape, and FR-003a would make `wfctl step complete
  implement` refuse there too. Stands because the plan does not say which
  behavior is intended. All 22 existing completion records in the spec store
  sit beside a `delivery.md`, so the impact falls on new features, other
  repositories, and the hand reproduction.
- **PR-002, MINOR, open.** The snapshot row `tasks-open-but-implemented` has no
  analysis report and stops at `analyze`, so its payload does not change and
  the proposed new row would be identical to it.
- **PR-003, MINOR, open.** The fence is sized against tilde fences only, which
  differs from the wording in FR-004 and the level-3 record. A tilde line nested
  inside a backtick block would close the outer fence early and truncate the
  task copy.
- **PR-004, MINOR, open.** `_completion` needs `quoted_out` from `_evidence`,
  and `_evidence` imports `_completion`, so the plan creates an import cycle
  without saying which way the dependency runs.
- **PR-005, MINOR, open.** Research R2 says matching by the first box can only
  reopen and never hide work. That is false for a line whose first box is ticked
  and a later box is incomplete.
- **PR-006, MINOR, open.** The plan does not say what the agent does when
  `wfctl step complete implement` refuses. A task list with no tasks always
  refuses, because `tasks` stays current until a completion record exists.
- **PR-007, MINOR, open.** The plan does not say the completion record is
  written with `write_atomic`, or that `tasks.md` is read once. Today
  `build_report` and the copy each read it separately.

## Review 2026-10-10T00:38Z

- Verdict: satisfied
- Reviewed: plan.md 597f94bc5473d1795b088140ad8bc913f6190e7a, spec.md b04b4d8e6441c8350a8a8b2f681e1b6f776c5291, .specify/memory/constitution.md absent, design.md 5c686de27a6212a1692331fb32dcf695f7372772, docs/architecture/design/264-the-task-copy-lives-in-the-completion-record.md 73d6c1664f0986dd82400ff10a2165a1588547b9, docs/architecture/design/264-the-completion-command-is-a-step-verb.md 6938214375db57bbe96bd0992d114812fcf90749, docs/architecture/new-task-reopens-implement.md 800f96d21795ee68ef91441bb3373f62b82eea9e, research.md 37b719254e4b58c5947b6f3c6a0f6ae2255a4e3f, data-model.md aac2aa3e59090497e429651da8469dd2a2b5e76f, contracts/cli.md 0eacf07ff9625faad3e1e42f07d87a8a09a93642, quickstart.md 1b6384fb8d4f74077512e8853124234990759a6d, checklists/requirements.md 3f61287371e0bafbc032dbdaa791ed2c1e3c3709, plan-review.plan.md ffa7597574a89a97753a61209bc4776aed800e3f (base)
- Review type: re-review (plan.md, spec.md, research.md, and quickstart.md edited for PR-001)
- Open: BLOCKER 0 · MAJOR 0 · MINOR 8 · Fixed since the earlier review: 2
- Detail: /Users/andremarin/Development/wfctl-specs/264-sentinel-goes-stale/plan-review.md

The review ran in a fresh-context subagent. Andre decided PR-001: a story that
reopens with no `delivery.md` keeps going to `/speckit.decompose` first, and
the artifacts record that as a limit instead of changing the `decompose`
reader.

### Coverage

| Check | Status |
| --- | --- |
| Deterministic checks | Outstanding (PR-003) |
| Requirements and traceability | Outstanding (PR-008; PR-001 fixed) |
| Architecture and boundaries | Outstanding (PR-004, PR-008) |
| Adversarial implementation and verification | Outstanding (PR-003, PR-005, PR-006, PR-009, PR-010; PR-001, PR-002 fixed) |
| Security and reliability | Outstanding (PR-007) |

### Findings

- **PR-001, MAJOR, fixed.** Fixed by `plan.md` § Summary and § Test Plan,
  research R1, a new edge case in `spec.md`, and the quickstart's set-up step.
  All four say that a story reopening with no `delivery.md` goes to
  `decompose` first. The tests that expect `implement` build a keyed
  `delivery.md`, and one new test pins the routing without it.
- **PR-002, MINOR, fixed.** Fixed by `plan.md` § Test Plan, which rebuilds
  both snapshot rows from `_ANALYZED` plus a keyed `delivery.md` so they reach
  `implement`.
- **PR-003, MINOR, open.** The fence is sized against tilde fences only, which
  differs from the wording in FR-004, and a tilde line nested inside a
  backtick block can cut the task copy short.
- **PR-004, MINOR, open.** `_completion.py` and `_evidence.py` import each
  other, and the plan does not say which way the dependency runs.
- **PR-005, MINOR, open.** Research R2 says matching by the first box can only
  reopen the step. A line with a ticked first box and a later incomplete box
  hides work instead.
- **PR-006, MINOR, open.** The plan does not say what the agent does when
  `wfctl step complete implement` refuses. The new limit adds one more case,
  a refusal that names `decompose`.
- **PR-007, MINOR, open.** The plan does not say the completion record is
  written with `write_atomic`, or that `tasks.md` is read once.
- **PR-008, MINOR, open.** FR-010 and the level-2 record still give
  `/speckit.implement` with no exception, while the new edge case pins
  `/speckit.decompose`. The two agree only if "reads open" means
  `in_progress` and not `pending`.
- **PR-009, MINOR, open.** The recorded limit is narrower than what the
  `decompose` reader does. The step is skipped while the tasks read closed,
  not while every box is ticked. A delivery plan with an unkeyed row also puts
  `decompose` in front of a reopened story, so `implement` becomes current
  once the rows are keyed, not once the plan exists.
- **PR-010, MINOR, open.** `uv run wfctl` run from a scratch repository
  resolves to the installed release, which has no `step complete`. The
  quickstart's `spec_tree` pointer also writes a plan review that does not
  clear `plan`.
