# Delivery Plan: A security review panel runs before every change opens (622)

**Feature**: `622-security-review-panel` | **Date**: 2026-10-24
**Source**: `/Users/andremarin/Development/wfctl-specs/622-security-review-panel/tasks.md` (76 tasks)
**Parent issue**: #622

---

## PR Decomposition

| PR | Tasks | Files Touched | Size | Merge Condition |
|----|-------|--------------|------|----------------|
| PR A | T057 - T064 | `tests/test_skill_attribution.py` (modified), `wfctl/agents/skills/security-and-hardening/SKILL.md` (created), `wfctl/agents/skills/security-and-hardening/references/hardening-patterns.md` (created), `wfctl/agents/skills/security-and-hardening/references/security-checklist.md` (created), `wfctl/agents/skills/reviewing-security/references/security-review.md` (created), `wfctl/agents/skills/reviewing-security/SKILL.md` (created), `wfctl/agents/skills/NOTICES.md` (modified), `docs/architecture/vendor-upstream-skills.md` (modified), its own release note (created) | M (9 files) | T064 green. No dependency on PR B. |
| PR B | T001 - T019, T043, T044, T046 - T056 | `wfctl/_paths.py` (modified), `wfctl/_review_config.py` (created), `wfctl/_review.py` (created), `wfctl/cli.py` (modified), `AGENTS.md` (modified), `tests/test_paths.py` (modified), `tests/test_review_config.py` (created), `tests/test_review.py` (created), `tests/test_review_cli.py` (created), `tests/test_review_store.py` (created), its own release note (created) | L (11 files) | T056 green. No dependency on PR A. |
| PR C | T020 - T042, T045, T065 - T076 | `wfctl/_review_gate.py` (created), `wfctl/_hook.py` (modified), `wfctl/_review.py` (modified), `wfctl/cli.py` (modified), `AGENTS.md` (modified), `wfctl/agents/skills/fanning-out-code-review/SKILL.md` (modified), `wfctl/agents/skills/opening-a-change/SKILL.md` (modified), `tests/test_review_gate.py` (created), `tests/test_review.py` (modified), `tests/test_review_cli.py` (modified), `tests/test_guard_entry.py` (modified), `tests/test_review_fanout_skill.py` (modified), `tests/test_opening_a_change_panel.py` (modified), `tests/test_skill_commands.py` (modified), its own release note (created) | L (15 files) | T076 green, and PR A and PR B both merged first. |

**Rationale**: Multiple PRs. The feature touches 29 distinct files, which is past the 12-file line, and Andre chose three PRs on 2026-10-24 over one or two.

The split follows three reasons, one per boundary:

1. PR A shares no file with PR B or PR C. It vendors two upstream security reviews and adds the `reviewing-security` skill that wraps them. Nothing calls that skill until PR C rewrites `fanning-out-code-review`, so it is inert when it merges. Its text names `wfctl review start`, which PR B adds, but no test checks that a command named in skill text exists, so PR A can merge before PR B.
2. PR B adds the review records, the relay, and the `review` config key. These are new commands and a new config key, and nothing in the repo calls them yet. It refuses nothing, so a flaw in it can't block another PR.
3. PR C adds the review check to the worktree guard, the sign-off command, `wfctl review groups`, and the two skill rewrites. The check and the rewrites ship together because the check refuses the `gh pr create` line the current `opening-a-change` Step 5 uses. If the check merged first, every PR in this repo would be blocked until someone ran the review groups by hand.

Splitting PR B from PR C costs one more issue, release note, and PR cycle. It also means PR B's records are first used end to end in PR C (T071, T074). If that run finds a design flaw in the records, the fix lands in PR C on code that has already merged. We accepted that cost so the guard check gets a review of its own instead of sharing one with the plumbing.

Five files appear in both PR B and PR C: `wfctl/cli.py`, `wfctl/_review.py`, `tests/test_review.py`, `tests/test_review_cli.py`, and `AGENTS.md`. PR C only adds to them (sign-off, `review groups`, the Safety section), and PR C starts after PR B merges, so they never conflict.

**PR closes**: each PR closes exactly its own sub-issue, `Closes #636`, `Closes #637`, and `Closes #638`.

PR C is the final PR for the epic. When all parent acceptance criteria hold after T074, PR C also carries `Closes #622`.

### Changes from tasks.md

The split moves or repeats three tasks. Everything else runs as written.

1. T001 writes `changes/622.addition.md`. Each PR instead creates its own note named for its own sub-issue, because the `release-note` check fails a branch that adds no note for its own issue. PR B runs T001 as written, with the issue number and content changed. PR A and PR C each create theirs as their first task, and each note describes only what that PR ships. T075 rereads PR C's note.
2. T045 tests that the review check allows a `wfctl relay` command whose report file quotes `gh pr create`. That test needs the check, so it moves to PR C and runs after T020. T047 in PR B verifies with T044 alone.
3. T002 measures the guard's baseline timing before PR B changes any code. It writes to `guard-timing.md` in the spec dir, which every worktree reads at the same absolute path, so T040 in PR C repeats it against that number.

### Where the design commits land

This branch, `622-security-review-panel`, holds 33 commits of design records and scan files and no code. PR B branches from this branch rather than from `main`, so those commits reach `main` with the records they describe. PR A branches from `main`, since none of those commits are about vendoring. PR C branches from `main` after PR A and PR B merge.

---

## Issue Grouping Map

| Issue | Tasks | Title | Estimate | Closes With |
|-------|-------|-------|----------|-------------|
| #636 (Issue A) | T057 - T064 | `[622] Vendor the security reviews and add the reviewing-security skill` | S | PR A |
| #637 (Issue B) | T001 - T019, T043, T044, T046 - T056 | `[622] Record which commits each review group covered, with relay and reviewer config` | L | PR B |
| #638 (Issue C) | T020 - T042, T045, T065 - T076 | `[622] Refuse opening or merging a PR with unreviewed commits, and rewrite the review skills` | L | PR C |

**Grouping pattern**: Sub-feature split under the parent epic #622.
**Rationale**: Each PR closes one issue, and the three issues are tracked as sub-issues of #622 so the epic shows what is done.

### Getting this spec into a sub-issue worktree

This repo records a spec root outside the working tree, so the epic's spec dir is already at `/Users/andremarin/Development/wfctl-specs/622-security-review-panel/` for every worktree, and nothing needs copying. Run `wfctl feature-paths` in the sub-issue worktree and check that `FEATURE_DIR` is that path. The `resolve_spec_dir` function finds it by scanning for this table's row that names the branch's issue, and `speckit-orchestrate` takes that row's `Tasks` column as the sub-issue's range.

---

## Parallelization Waves

PR A and PR B run at the same time in two worktrees. PR C waits for both to merge.

| Wave | Mode | Tasks | Gate / Notes |
|------|------|-------|-------------|
| 0 | Sequential | B: T002 | Baseline timing before any code changes. |
| 1 | Parallel | A: note, T057 ‖ B: T001, T004 ‖ T006 | A and B share no file. |
| 2 | Parallel | A: T058 ‖ T059 ‖ B: T005, T007 → T008 | T058 and T059 touch different files. |
| 3 | Parallel | A: T060 → T061 → T062 ‖ B: T009 ‖ T012 ‖ T013, then T010 → T011 | T009, T010, and T011 share `tests/test_review.py`, so they run in order. |
| 4 | Parallel | A: T063 → T064 ‖ B: T014 → T015 → T016 → T017 → T018 → T019 | PR A's merge gate is T064. |
| 5 | Sequential | B: T043 ‖ T044 → T046 → T047 → T048 → T049 | US4 and US5 both edit `_review.py` and `cli.py`, so US4 finishes first. |
| 6 | Sequential | B: T050 ‖ T051 ‖ T052 → T053 → T054 → T055 → T056 | PR B's merge gate is T056. |
| 7 | Gate | PR A and PR B merged to `main` | PR C branches from `main` here. |
| 8 | Parallel | C: note, T020 → T021 → … → T027 → T045 ‖ T028 ‖ T029 ‖ T030 | The `tests/test_review_gate.py` tasks share one file and run in order. |
| 9 | Sequential | C: T031 → T032 → T033 → T034 → T035 → T036 → T037 → T038 → T039 → T040 → T041 → T042 | Each `_review_gate.py` task builds on the one before, and T037 wires the check in. |
| 10 | Parallel | C: T065 ‖ T066 ‖ T067 | Different test files. |
| 11 | Sequential | C: T068 → T069 → T070 → T071 → T072 → T073 → T074 → T075 → T076 | T074 needs Andre for steps that only run in his terminal. |

---

## Agent Fanning Instructions

Use one agent per PR. Within each PR the parallel tasks are small test files, and splitting them across agents costs more in shared context than it saves.

The parallelism that matters is PR A and PR B running at once, each in its own worktree created with `workmux add <issue>-<slug> --base <base>`, with a handoff written first per `worktree-handoff`. PR A's base is `main`. PR B's base is `622-security-review-panel`. Each worktree's session runs `/start-session` and then `/speckit.implement`, which reads its task range from the Issue Grouping Map.

**Fan-in gate before PR C:** both PRs merged, then `git fetch` and fast-forward local `main` before running `workmux add` for PR C.
