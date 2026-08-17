---
name: speckit-delivery-plan
description: Delivery decomposition skill for the speckit workflow. Use when you have a complete tasks.md and need to decide PR boundaries, group tasks into GitHub issues, and map parallelization waves before creating issues. Enforces the canonical workflow with decompose as the default terminus.
---

# Speckit Delivery Plan

**Purpose:** Transform a completed `tasks.md` into a structured delivery plan — PR
boundaries, issue grouping map, parallelization waves — and create GitHub issues using
that plan via `/speckit.decompose`.

**Position in workflow:** After `analyze`, before issue creation.

---

## Canonical Speckit Workflow

This is the enforced order. Do not skip steps.

```
brainstorm → specify → clarify → plan → tasks → analyze → decompose
     ↓          ↓         ↓        ↓       ↓        ↓          ↓
design.md   spec.md  clarified plan.md tasks.md quality  delivery.md
                     spec.md                    gate     + GH issues
```

**`brainstorm` is the recommended entry point** — run `/speckit.brainstorm`
before `specify`. It writes to `specs/<branch>/design.md`; `specify` picks it up
automatically (step -1 gate).

**`analyze` is mandatory** — it is the quality gate that catches numbering bugs,
wrong file paths, and missing verification. Always run it before decompose.

**`decompose` is the default terminus** for features.

**Branch/spec naming is `{key}-{slug}`** — `speckit-specify` never mints a
number; the branch must already be named for an issue that exists. The branch
`251-extract-api-routes` and spec dir `specs/251-extract-api-routes/` match the
issue key exactly (GitHub `251`, or a configured `key_pattern` like `PROJ-123`
for other trackers). See `speckit-specify` for details.

### Pre-decompose Checklist

```
Before running /speckit.decompose, verify all of these:
- [ ] spec.md exists with no [NEEDS CLARIFICATION] markers
- [ ] plan.md exists with Constitution Check all ticked
- [ ] tasks.md exists with at least one task
- [ ] /speckit.analyze was run — checklists/requirements.md updated, no CRITICAL issues open
```

---

## When to Use This Skill

- You have a complete `tasks.md` and are about to create GitHub issues
- You need to decide: one PR or multiple?
- You need to decide which `tasks.md` tasks form each PR-sized deliverable issue
- You need to plan which tasks can fan to parallel agents
- You are invoking `/speckit.decompose` and want the decision framework

**Do NOT use when:**
- `tasks.md` does not exist yet → run `/speckit.tasks` first
- `analyze` has CRITICAL issues open → resolve them first
- You want simple 1:1 task→issue mapping → use `/speckit.decompose` (it handles that case)

---

## Process (5 Steps)

**Step 1 — Read artifacts** (read-only, no code changes)
Load `tasks.md`, `spec.md`, `plan.md`. Do not write anything yet.

**Step 2 — Build file-touch matrix**
For each task, list which files it creates or modifies. This drives PR sizing.

```
Example matrix:
T004 → CREATE src/routes/index.{ext}
T005 → MODIFY src/entry-point.{ext}
T006 → READ ONLY (type or build check)
```

**Step 3 — Apply PR boundary signals** → output PR count with rationale

**Step 4 — Apply issue grouping rules** → output task→issue map

**Step 5 — Build parallelization wave table** → output wave assignments,
then write `delivery.md` and create GitHub issues.

---

## PR / Task Sizing Guidelines

| Size | Files Touched | PR Strategy | Issue Strategy |
|------|--------------|-------------|----------------|
| XS | 1–2 | Single PR | 1 issue |
| S | 3–5 | Single PR | 1 issue |
| M | 5–8 | Single PR | 1 issue |
| L | 8–12 | **Flag for discussion** — do not auto-split | Present scope to user; if split agreed: 1 issue + 1 PR per sub-feature |
| XL | 12+ | Break down further first | Cannot decompose until smaller |

---

## PR Boundary Decision Framework

Apply all 4 signals. If any YES → consider splitting into multiple PRs.

1. **File conflict risk** — Do two groups of tasks edit the same file?
   If yes and they can be sequenced, keep in one PR. If concurrent edits
   to the same file are unavoidable, split.

2. **Reviewability** — Would a reviewer need all tasks together to assess
   correctness? If yes → bundle. A reviewer should be able to understand
   the full change from a single PR.

3. **Mergeable increment** — Can a subset be merged without leaving the
   feature broken or untestable? If no → bundle.

4. **Story independence** — Are user stories truly independent (separate
   acceptance criteria, separate runtime paths, no shared state)? If yes
   → split candidate.

**Default**: bundle into one PR. If signals suggest a split is warranted, **stop and
flag it** — present the scope concern to the user and discuss whether two issues and
two PRs make sense. Do not auto-split. If a split is agreed: each PR gets exactly one
issue. **Never close multiple issues from one PR.**

---

## Issue Grouping Rules

**The rule: one PR closes exactly one issue.** Always.

| Pattern | When to use | Result |
|---------|------------|--------|
| **Single issue** *(default)* | All XS/S/M features; one PR delivers the full feature | 1 issue, 1 PR |
| **Sub-feature split** | L features too large for one PR; decompose into sub-features | 1 issue per sub-feature, 1 PR each — tracked under a parent epic issue |
| **Phase-grouped** | Infrastructure/refactor with no clear user stories | 1 issue per phase, 1 PR each |

**Do not use:**
- Story-grouped (N issues → 1 PR) — creates tracking ambiguity; hard to see what's done
- Task-per-issue (N issues = N tasks) — issue noise; tasks belong in the issue body, not as separate issues

**Issue key format**: the Issue Grouping Map's `Issue` column must lead with the
tracker's native key exactly as returned (GitHub `#251`; other trackers per their
`key_pattern`, e.g. `PROJ-123`, no `#`). See `assets/delivery-plan-template.md`.

---

## Parallelization Opportunities

| Type | Signal | Action |
|------|--------|--------|
| **Safe (parallel)** | Tasks touch different files, no shared state | Mark [P] in wave table |
| **Safe (parallel)** | Grep / type-check / read-only verification tasks | Mark [P] in same wave |
| **Sequential** | B reads the output of A | A must complete before B |
| **Sequential** | Build/test gate (fan-in) | All Wave N tasks complete before Wave N+1 |
| **Coordinate** | Tasks share an API contract or type boundary | Draft together, type-check together |

**Wave numbering convention:**
- Wave 0: prerequisites (baseline checks, no edits)
- Wave 1+: implementation waves (parallel where possible)
- Final wave: polish and validation sweep

---

## Common Rationalizations

| Excuse | Rebuttal |
|--------|---------|
| "It's a small change, no need to decompose" | Small changes still need PR strategy and issue grouping; decompose takes 2 minutes |
| "All tasks are clearly sequential, no parallelism" | Even sequential flows have parallel verification tasks; wave analysis prevents missed opportunities |
| "One issue per task is fine" | 13 issues for a 2-file refactor creates noise; one issue per PR is the rule |
| "Multiple issues make it easier to track stories" | Multiple issues per PR make it harder — you can't tell what's done until all close; put stories in the issue body |
| "We can figure out PR boundaries during implementation" | Mid-implementation PR decisions cause history rewrites and confusing reviews |
| "analyze is optional for small features" | analyze catches task-count and numbering errors a human reading the same file skims past — always run it |
| "I'll skip clarify, the spec is clear enough" | Unclarified specs generate plans that need rework; clarify is the cheapest step |
| "I don't need decompose for a simple feature" | decompose handles simple 1:1 cases too and writes delivery.md — always use it |

---

## Red Flags

Stop and reassess if any of these appear:

- File-touch matrix shows 8+ files → L/XL scope; flag for user discussion before proceeding
- All tasks land in one wave (no parallelism detected) → re-examine task definitions
- Issue count > PR count → a PR closes multiple issues → restructure; split or merge issues
- PR count > issue count → an issue spans multiple PRs → restructure; one issue per PR
- `analyze` has CRITICAL issues open → do not proceed to decompose
- `delivery.md` already exists and was not reviewed → verify it matches current tasks.md

---

## Verification Checklist

Before marking decompose complete:

- [ ] `delivery.md` written to `specs/{key}-{feature}/delivery.md`
- [ ] PR count justified with rationale (single vs. multiple)
- [ ] Issue count equals PR count — one issue per PR, no exceptions
- [ ] Every task assigned to exactly one wave
- [ ] GitHub issues created and numbered
- [ ] Each issue's `Closes` line references exactly one PR
- [ ] Sub-feature issues linked to parent epic issue (if L-size split)

---

## When to Load References

**Load `references/pr-boundary-criteria.md` when:**
- Feature has 8+ files touched and the split decision is non-obvious
- Two user stories share a file but could potentially be separate PRs
- You need a worked example of the 4-signal framework

**Load `references/issue-grouping-patterns.md` when:**
- Unsure whether to use single-issue, sub-feature split, phase-grouped, or hierarchical pattern
- Multi-PR feature where parent/child relationships need clarification
- Feature has user stories that don't map cleanly to tasks

**Load `references/agent-fanning-guide.md` when:**
- Feature is M or larger and real parallelism is available
- You need copy-paste agent prompts for Wave 2+ fanning
- Coordinating 3+ parallel agents across shared type boundaries

**Load `assets/delivery-plan-template.md` when:**
- Writing `delivery.md` manually (not via `/speckit.decompose`)
- Verifying that a generated delivery.md has all required sections

---

## References

- **references/pr-boundary-criteria.md** — detailed PR split signals with examples
- **references/issue-grouping-patterns.md** — 1:1 / grouped / hierarchical patterns
- **references/agent-fanning-guide.md** — wave-based parallelization and agent prompts
- **assets/delivery-plan-template.md** — blank `delivery.md` template to copy
