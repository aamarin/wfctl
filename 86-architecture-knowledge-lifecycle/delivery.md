# Delivery Plan: Architecture Knowledge Lifecycle (86)

**Feature**: `86-architecture-knowledge-lifecycle` | **Date**: 2026-08-26
**Source**: `specs/86-architecture-knowledge-lifecycle/tasks.md` (42 tasks)
**Parent issue**: #86 (epic)

---

## PR Decomposition

| PR | Base | Closes | Tasks | Files Touched | Size | Merge Condition |
|----|------|--------|-------|--------------|------|----------------|
| PR 1 | `main` | #91 | T001–T015 | `tests/test_arch_root.py` (created), `wfctl/_paths.py` (modified), `tests/test_arch_records.py` (created), `wfctl/_arch.py` (created), `wfctl/cli.py` (modified), `wfctl/_session.py` (modified), `README.md` (modified), `tests/test_promote.py` (deleted), `tests/test_agent_session.py` (modified) | **L** | T015 gate green |
| PR 2 | PR 1 | #92 | T016–T022 | `tests/test_skill_cross_references.py` (modified), `wfctl/agents/skills/architecture-decisions/record-template.md` (created), `.../architecture-decisions/SKILL.md` (created), `wfctl/agents/skills/design-levels/SKILL.md` (modified), `docs/architecture/*.md` (created, 2 seeds) | M | T022 gate green |
| PR 3 | PR 1 | #93 | T023–T032 | `tests/test_remaining_commands.py` (modified), `wfctl/cli.py` (modified), `wfctl/agents/skills/start-session/SKILL.md` (modified), `tests/test_pipeline_commands.py` (modified), `wfctl/_pipeline.py` (modified) | S | T032 gate green |
| PR 4 | PR 3 | #94 | T033–T042 | `docs/architecture/{layer-model,install-modes,no-hardcoded-agent,vendor-upstream-skills,knowledge-placement}.md` (created), `AGENTS.md` (modified), `CLAUDE.md` (modified), `README.md` (modified) | M | T042 final gate green |

**Rationale**: Four stacked PRs. Not the two named in `design.md` — that split
predates `tasks.md` and undercounted; the file-touch matrix puts each of its
halves at 14 files, which the sizing guideline refuses to auto-split.

**The stack**

```
main
 └── PR1  complete _arch.py, arch-root, delete promote
      ├── PR2  ADR skill, level-2 gate, 2 seed records
      └── PR3  arch context, arch none, advance check
           └── PR4  relocation, placement record, docs
```

Create each worktree from its base:

```bash
workmux add <branch> --base main            # PR 1
workmux add <branch> --base <pr1-branch>    # PR 2
workmux add <branch> --base <pr1-branch>    # PR 3
workmux add <branch> --base <pr3-branch>    # PR 4
```

**Why PR 1 ships `_arch.py` complete.** An earlier arrangement had PR 1 create the
module, PR 2 add supersession, and PR 3 add the projection filter. That gave PR 2
and PR 3 a shared edit to `wfctl/_arch.py` and `tests/test_arch_records.py`, so
they could not branch off PR 1 in parallel without conflicting — and PR 3 would
have had two parents, which cannot be expressed as a `--base`. Finishing the
module in PR 1 makes PR 2 and PR 3 pure consumers on disjoint file sets.

**⚠️ PR 1 is L (9 files) — flagged rather than split.** Four of the nine are the
orphaned-`promote` removal, which is pure deletion. Moving it into another PR
pushes that one to L instead; giving it its own PR yields a fifth issue for
deleting dead code. Recommendation is to accept, but this is the discussion the
guideline asks for.

**Seed records pinned at two.** `spec.md` allows "two or three"; two holds PR 2 at
M.

**PR closes**: each PR closes exactly one issue. PR 4, as the last in the stack,
additionally closes the parent epic if all of #86's acceptance criteria are met.

---

## Issue Grouping Map

| Issue | Tasks | Title | Estimate | Closes With |
|-------|-------|-------|----------|-------------|
| #91 (Issue A) | T001–T015 | The record module: root resolution, parsing, validation, projection, and retiring promote | L | PR 1 |
| #92 (Issue B) | T016–T022 | The capture path: the ADR skill and the level-2 gate that writes records | M | PR 2 |
| #93 (Issue C) | T023–T032 | The consumption path: in-force projection, session delivery, and the design-step check | S | PR 3 |
| #94 (Issue D) | T033–T042 | Consolidation: relocate misplaced knowledge and make the placement rule durable | M | PR 4 |

### Branch and worktree creation

Branch names follow `{key}-{slug}`. Each worktree bases on the previous PR's
branch, not `main`:

```bash
workmux add 91-record-module      --base main
workmux add 92-capture-path       --base 91-record-module
workmux add 93-consumption-path   --base 91-record-module   # parallel with 92
workmux add 94-consolidation      --base 93-consumption-path
```

**Grouping pattern**: Sub-feature split, tracked under parent epic #86.
**Rationale**: #86 states outright that it implements none of its scope items
directly; each sub-feature is a mergeable increment with its own acceptance
criteria and verification path. Task ranges are contiguous so
`speckit-orchestrate` step 0 can scope a sub-issue worktree from the `Tasks`
column.

### Getting this spec into a sub-issue worktree

This repo records a spec root outside the working tree
(`/Users/andremarin/Development/wfctl-specs`), so the epic's spec dir is already
at a stable absolute path every worktree can read. Nothing to copy.

`speckit-orchestrate` step 0 resolves it: it globs the spec root for
`*/delivery.md`, matches the branch's issue key against the table above, and takes
that row's `Tasks` column as the sub-issue's range.

---

## Parallelization Waves

Waves are scoped per PR, since each PR is its own worktree.

**PR 1** (`main`)

| Wave | Mode | Tasks | Gate / Notes |
|------|------|-------|-------------|
| 0 | Sequential | T001 | Baseline, read-only |
| 1 | Parallel | T002 ‖ T004 ‖ T014 | Different files; T014 only deletes |
| 2 | Sequential | T003 ‖ T005 | Different files, each after its own tests |
| 3 | Sequential | T006 → T007 → T008 → T009 → T010 → T011 → T012 | All extend `_arch.py` or its one test file; strictly ordered |
| 4 | Sequential | T013 → T015 | Command, then merge gate |

**PR 2** (base PR 1) and **PR 3** (base PR 1) — run in parallel with each other

| Wave | Mode | Tasks | Gate / Notes |
|------|------|-------|-------------|
| 1 | Parallel | T016 ‖ T017 (PR 2) — and T023 ‖ T027 (PR 3) | Disjoint across both PRs |
| 2 | Sequential | T018 → T019 → T020 (PR 2); T024 → T025 (PR 3), T028 → T029 (PR 3) | `cli.py` is edited by T024 and T029 in the same PR — sequence them |
| 3 | Sequential | T021 → T022 (PR 2); T026, T030, T031 → T032 (PR 3) | Manual verification cannot parallelize |

**PR 4** (base PR 3)

| Wave | Mode | Tasks | Gate / Notes |
|------|------|-------|-------------|
| 1 | Parallel | T033 ‖ T034 ‖ T035 ‖ T036 ‖ T037 ‖ T040 | Five new record files plus README — all disjoint |
| 2 | Sequential | T038 → T039 | Strip the guidance file, then the SC-004 trial |
| 3 | Sequential | T041 → T042 | Quickstart sweep, then final gate |

**Single-agent order**: T001 → T002 → … → T042, phase by phase.

---

## Agent Fanning Instructions

**PR 1, Wave 1 fanning (3 agents):**

**Agent A prompt:**
```
Write failing tests for architecture root resolution in tests/test_arch_root.py.
Cover all six legs from tasks.md T002. Mirror the existing tests/test_spec_root.py
structure. Pin NO_COLOR in any test asserting on console output. Do not implement
arch_root() — the tests must fail.
```

**Agent B prompt:**
```
Write failing tests for architecture record parsing in tests/test_arch_records.py
per tasks.md T004: five status values, absent status, unrecognised status, missing
frontmatter delimiter, supersedes extraction. Read contracts/record-format.md in
the feature spec dir for the exact format. Do not create wfctl/_arch.py — the
tests must fail.
```

**Agent C prompt:**
```
Remove the orphaned promote path per tasks.md T014: the promote command in
wfctl/cli.py, promote() in wfctl/_session.py, the WFCTL_CANDIDATES_FILE row in
README.md, all of tests/test_promote.py, and the promote cases in
tests/test_agent_session.py. Verify with: grep -rn
"memory-candidates\|WFCTL_CANDIDATES_FILE\|promote" wfctl/ tests/ README.md —
no hits — then uv run pytest -q green.
```

**Fan-in gate after PR 1 Wave 1:** `uv run pytest -q` (new tests fail, everything
else green)

**Cross-PR fanning:** once PR 1 merges, PR 2 and PR 3 can be handed to two agents
in separate worktrees, both based on the PR 1 branch. Their file sets do not
intersect, so no coordination is needed until both merge.

**Final gate:** `uv run pytest -q && uv run ruff check wfctl/ tests/ && uv run mypy wfctl/ && wfctl doctor`
