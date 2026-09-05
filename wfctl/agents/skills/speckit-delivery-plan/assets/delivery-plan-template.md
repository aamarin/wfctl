# Delivery Plan: {Feature Name} ({NNN})

**Feature**: `{NNN}-{feature-name}` | **Date**: {DATE}
**Source**: `specs/{NNN}-{feature-name}/tasks.md` ({N} tasks)
**Parent issue**: #{PARENT_ISSUE}

---

## PR Decomposition

| PR | Tasks | Files Touched | Size | Merge Condition |
|----|-------|--------------|------|----------------|
| #{PR_NUMBER} | {task range} | `{file1}` ({created/modified}), `{file2}` ({created/modified}) | {XS/S/M/L} | {condition} |

**Rationale**: {Single PR / Multiple PRs}. {One sentence explaining why — mutual dependency, independent stories, etc.}

**PR closes**: `{Closes #{issue-for-this-PR}}`

If this is the final PR for a parent epic and all parent acceptance criteria are
satisfied, add the parent close separately: `{Closes #{parent}}`.

---

## Issue Grouping Map

The **Issue** column must lead with the tracker's native key exactly as returned
— no other format. GitHub: `#251`. Other trackers (per their `key_pattern` in
`.agents/trackers/<name>.json`): e.g. `PROJ-123`, no `#` prefix. Tooling that
reconciles pipeline state against this table (e.g. an epic sub-issue resolving
its inherited spec dir) regex-matches on this key, so a consistent leading
position matters more than the label that follows it.

| Issue | Tasks | Title | Estimate | Closes With |
|-------|-------|-------|----------|-------------|
| {issue-key} (Issue A) | {task IDs} | `[{NNN}] {group description}` | {estimate} | PR #{N} |
| {issue-key} (Issue B) | {task IDs} | `[{NNN}] {group description}` | {estimate} | PR #{N} |
| {issue-key} (Issue C) | {task IDs} | `[{NNN}] {group description}` | {estimate} | PR #{N} |

**Grouping pattern**: {Single issue / Sub-feature split / Phase-grouped / Hierarchical / 1:1 explicit}
**Rationale**: {One sentence explaining the pattern choice}

### Getting this spec into a sub-issue worktree

{Omit this section for a single-issue grouping.}

Run `wfctl feature-paths` in the sub-issue worktree and read `FEATURE_DIR`. If
this repo records a spec root outside the working tree, the epic's spec dir is
already at a stable absolute path every worktree can read, and there is nothing
to move.

**Otherwise specs live in-repo and untracked: copy `{NNN}-{feature-name}/` into
the new worktree's spec dir by hand.** A fresh worktree is a clean checkout, so a
directory that was never committed does not come across.

Either way, `resolve_spec_dir` is what resolves it: it scans the spec root for
a `delivery.md` whose Issue Grouping Map names the branch's issue key, and
`speckit-orchestrate` takes that row's `Tasks` column as the sub-issue's range.
That scan reads the **first cell of each row in the first table under the
heading** — which is why the key leads that cell.

Skip the copy in the in-repo case and `wfctl status` reports `brainstorm` for a
story that is fully planned. That is the symptom; this is the cause.

---

## Parallelization Waves

| Wave | Mode | Tasks | Gate / Notes |
|------|------|-------|-------------|
| 0 | Sequential | {tasks} | {gate condition or "no dependencies"} |
| 1 | Parallel | {task} ‖ {task} | {constraint or "no dependencies"} |
| 2 | Parallel | {task} ‖ {task} | {constraint} |
| 3 | Sequential | {task} | {gate condition} |
| 4 | Sequential | {task} → {task} | {ordering reason} |

**Single-agent order** (recommended for {XS/S} features):
{T001} → {T002} → ... → {T013}

---

## Agent Fanning Instructions

{For XS features:}
Single agent recommended for this {size} feature. Wave table above provided for
reference and template reuse.

{For M+ features:}
**Wave {N} fanning ({N} agents):**

**Agent A prompt:**
```
{copy-paste agent prompt}
```

**Agent B prompt:**
```
{copy-paste agent prompt}
```

**Fan-in gate after Wave {N}:** `{command}`
