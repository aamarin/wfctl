---
name: requesting-code-review
description: Proactively request review of your OWN work before problems compound — dispatch a fresh-context reviewer after a task, before a merge, after a complex bug fix, or when stuck. This is the trigger and hand-off; the reviewer runs the code-review skill. For reviewing a diff yourself, use code-review. For acting on feedback you received, use receiving-code-review.
---

# Requesting Code Review

Review early, review often. When you finish a chunk of work, hand it to a
**fresh-context reviewer** instead of grading your own homework. You're blind to
your own assumptions — you already "know" the code is right because you reasoned
yourself into it. A reviewer that never saw your reasoning, only the diff and the
spec, catches what you rationalized past.

This skill is the *trigger and the hand-off*. The reviewer itself follows the
[code-review](../code-review/SKILL.md) skill (the six-pass rubric). Use
**code-review** to review a diff directly; use **receiving-code-review** to act
on feedback someone gave *you*.

## When to request

**Do it:**
- After each task in subagent- or plan-driven development, before the next task builds on it
- After completing a feature
- Before merging to a shared branch

**Worth it:**
- When stuck — a fresh perspective unblocks
- After fixing a complex bug — review the fix **and** its regression test

Skipping review because "it's simple" is the most common way simple bugs ship.

## How to request

**1. Define the diff the reviewer will see** (any code-review target works):
```bash
BASE_SHA=$(git rev-parse origin/main)   # or HEAD~1, or the task's start commit
HEAD_SHA=$(git rev-parse HEAD)
```
For a single commit, a range, or working changes, see code-review Step 1.

**2. Dispatch a reviewer with CLEAN context.** Hand it only:
- the diff (`BASE_SHA..HEAD_SHA`),
- what the change is *supposed* to do — the spec/task/plan (under wfctl, `specs/<branch>/spec.md` + `plan.md`; `wfctl feature-paths` prints them),
- the project rules (`CLAUDE.md`, conventions),
- the instruction: **follow the code-review skill; return BLOCKER / WARNING / NIT findings.**

**Never** hand it your session history — that primes it with your assumptions and
defeats the purpose. If your harness can't spawn a subagent, run the review as a
deliberate cold pass per the code-review skill instead.

**3. Act on the findings:**
- **BLOCKER** → fix before proceeding.
- **WARNING** → fix, or defer only with a filed follow-up.
- **NIT** → your discretion.
- Reviewer wrong? Push back with technical reasoning and code/tests that prove it — demonstrate, don't argue.

## Red flags

- Skipping review because "it's simple" or "AI wrote it" (AI-generated code needs *more* scrutiny, not less).
- Handing the reviewer your chat log instead of just the work product.
- Proceeding past a BLOCKER, or treating every NIT as mandatory.
