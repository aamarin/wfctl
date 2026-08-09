# Delivery Plan: Agent Artifact Layout (11)

**Feature**: `11-agent-artifact-layout` | **Date**: 2026-08-05
**Source**: `specs/11-agent-artifact-layout/tasks.md` (31 tasks)
**Parent issue**: #11

---

## PR Decomposition

| PR | Tasks | Files Touched | Size | Merge Condition |
|----|-------|--------------|------|----------------|
| PR 1 (`aamarin/wfctl`) | T001–T013, T028 | `wfctl/_archive.py` (mod), `wfctl/_pipeline.py` (mod), `wfctl/cli.py` (mod), `tests/conftest.py` (mod), `tests/test_archive_story.py` (mod), `tests/test_start_atomic.py` (mod), `.gitignore` (mod) | M (7) | `uv run pytest -q` green; `grep -rn '"\.agent"\|\.agent/' wfctl/ tests/` returns nothing |
| PR 2 (`aamarin/wf-skills`) | T014–T027, T030–T031 | `.agents/commands/brainstorm.md` (mod), `.agents/commands/speckit.brief.md` (mod), `.agents/skills/speckit-specify/SKILL.md` (mod), `.agents/skills/speckit-delivery-plan/SKILL.md` (mod), `.agents/skills/agent-brief/SKILL.md` (mod), `.agents/skills/speckit-plan/SKILL.md` (mod), `.agents/skills/brainstorming/SKILL.md` (mod), `.agents/skills/idea-refine/SKILL.md` (mod), `AGENTS.md` (created) | L (9) | `git grep -nE '\.agent/'` returns nothing; full-pipeline smoke passes |

**Rationale**: Multiple PRs — two, one per repository, because a single PR cannot
span two repos. The split is imposed by repository boundaries, not chosen for
size.

PR 2 is L (9 files) and was flagged rather than auto-split. It stays whole
deliberately: every change in it is a mechanical path repoint of the same
constant, a reviewer assessing one needs to see all of them to confirm none was
missed, and `.agents/commands/brainstorm.md` is edited on behalf of all three
user stories. Splitting PR 2 puts that file in two PRs racing on the same lines —
the conflict risk recorded as finding F2 in the analysis report. One PR dissolves
it instead of documenting it.

**PR 1 closes**: `Closes aamarin/wfctl#24`
**PR 2 closes**: `Closes #17` and, as the final PR of the epic, `Closes #11`

---

## Issue Grouping Map

| Issue | Tasks | Title | Estimate | Closes With |
|-------|-------|-------|----------|-------------|
| #11 (parent epic) | — | `[11] Consolidate agent artifact layout` | — | PR 2 (final) |
| aamarin/wfctl#24 | T001–T013, T028 | `[11] Read artifacts from specs/<branch>/ and report layout skew` | 2–3 hours | PR 1 |
| #17 | T014–T027, T030–T031 | `[11] Write artifacts to specs/<branch>/; overrides to AGENTS.md` | 3–4 hours | PR 2 |

**Grouping pattern**: Sub-feature split under a parent epic.

**Rationale**: Clarify Q1 established that one issue spans both repositories and
is done only when both merge. The delivery rule is that one PR closes exactly one
issue. Two repositories force two PRs, so the only structure satisfying both is
#11 as a parent epic with one sub-issue per repository — #11 closes when its
children do, which is precisely the recorded decision.

### Getting this spec into a sub-issue worktree

`specs/` is gitignored in this repository, so `--base` will not carry this
directory into a sub-issue worktree — `--base` conveys branch ancestry, not
untracked files, and a fresh worktree is a clean checkout.

**Copy `specs/11-agent-artifact-layout/` into each sub-issue worktree by hand.**
`speckit-orchestrate` step 0 then globs `specs/*/delivery.md`, matches the
branch's issue key against the table above, and takes that row's `Tasks` column
as the sub-issue's range.

Skip the copy and `wfctl status` reports `brainstorm` for a story that is fully
planned. That is the symptom; this is the cause.

For the `aamarin/wfctl` sub-issue the copy is required regardless, since that
repository has no history in common with this spec at all.

---

## Parallelization Waves

| Wave | Mode | Tasks | Gate / Notes |
|------|------|-------|-------------|
| 0 | Parallel | T001 ‖ T002 | Baseline capture and green-suite check. Read-only, no edits |
| 0g | Sequential | T003 | Setup merge gate — baseline counts match, suite green |
| 1 | Parallel | (T004 → T005) ‖ T006 ‖ T007 ‖ T008 ‖ T009 | T004/T005 share `_archive.py`, so they sequence. The rest are disjoint files |
| 2 | Sequential | T011 → T012 | Both touch `cli.py`; T011 is a docstring, T012 adds the diagnostic. Coordinate rather than parallelize |
| 3 | Sequential | T010 | Regression test for the archive sequence; depends on T004 having landed |
| 3g | Sequential | T013 | **wfctl merge gate — PR 1 ships here.** Must release before Wave 4 |
| 4 | Parallel | T014 ‖ T015 ‖ T016 ‖ T017 ‖ T021 ‖ T023 ‖ T025 ‖ T026 | Eight disjoint files. The largest parallel opportunity in the feature |
| 5 | Sequential | T018 → T018a → T020 → T024 | All four edit `.agents/commands/brainstorm.md`. Strictly sequential — this is finding F2, contained |
| 6 | Parallel | T019 ‖ T022 ‖ T027 | Per-story merge gates, independent of each other |
| 7 | Sequential | T028 → T030 → T031 | Polish, full-pipeline smoke, success-criteria sweep |

**Hard constraint**: Wave 3g must merge *and release* before Wave 4 begins.
Landing the producer side first strands step inference at brainstorm with no
error message (`_pipeline.py:75`). This is the single ordering dependency in the
feature and it crosses a repository boundary, so it cannot be enforced by CI.

**Single-agent order**: T001 → T002 → T003 → T004 → T005 → T006 → T007 → T008 →
T009 → T011 → T012 → T010 → T013 → *(release wfctl)* → T014 → T015 → T016 →
T017 → T021 → T023 → T025 → T026 → T018 → T018a → T020 → T024 → T019 → T022 →
T027 → T028 → T030 → T031

*(T029 is vacant — removed during analysis remediation.)*

---

## Agent Fanning Instructions

Wave 4 is the only wave where fanning pays. Waves 1 and 2 are small and share
review context; Waves 5–7 are strictly sequential.

**Wave 4 fanning (2 agents):**

**Agent A prompt:**

```
In aamarin/wf-skills, repoint agent artifact paths from `.agent/` to
`specs/<branch>/`. Work only these files:

  .agents/skills/speckit-specify/SKILL.md        (9 refs: :18 :23 :26 :33 :39 :42 :43 :48 :50)
  .agents/skills/speckit-delivery-plan/SKILL.md  (2 refs: :23 :28)
  .agents/skills/agent-brief/SKILL.md            (3 refs: :18 :36 :66)
  .agents/commands/speckit.brief.md              (1 ref:  :3)

`.agent/spec.md` becomes `specs/<branch>/design.md`. `.agent/brief.md` becomes
`specs/<branch>/brief.md`. `.agent/checkpoint.md` becomes
`specs/<branch>/escalation.md` — a RENAME, justified in research.md R3: wfctl
already has a `checkpoint` subcommand meaning something unrelated.

Do NOT touch .agents/commands/brainstorm.md — another agent owns it.

Verify: `git grep -nE '\.agent/|checkpoint\.md' -- <your four files>` returns
nothing.
```

**Agent B prompt:**

```
In aamarin/wf-skills, remove duplicate artifact writers and repoint two handoff
destinations. Work only these files:

  .agents/skills/speckit-plan/SKILL.md      delete step 3 "Agent context update" (:147-148)
  .agents/skills/brainstorming/SKILL.md     :29 :106 — destination becomes specs/<branch>/design.md;
                                            DELETE the "and commit" instruction (the path is gitignored)
  .agents/skills/idea-refine/SKILL.md       :32 :140 — destination becomes specs/<branch>/design.md
  AGENTS.md                                 CREATE at repo root with this repo's project overrides

speckit-plan's step 3 is deleted, not repointed — plan.md already holds the plan
summary, and the second copy is what overwrote agent-brief's scope contract.

Do NOT touch .agents/commands/brainstorm.md — another agent owns it.

Verify: `git grep -nE 'brief\.md' -- .agents/skills/speckit-plan/SKILL.md`
returns nothing; `git check-ignore -v AGENTS.md` exits non-zero.
```

**Fan-in gate after Wave 4:**

```bash
git -C wf-skills grep -nE '\.agent/'   # only brainstorm.md lines should remain, for Wave 5
```

Wave 5 must run single-agent afterwards — four tasks, one file.
