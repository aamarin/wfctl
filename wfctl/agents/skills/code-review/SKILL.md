---
name: code-review
description: Comprehensive adversarial code review across six lenses — correctness, security, architecture, readability, performance, and over-engineering. Reviews any target (working changes, a specific commit, a commit range, or a PR) with fresh context and severity-classified findings (BLOCKER / WARNING / NIT). Use before merging, after a feature or bug fix, when asked to "review this commit / PR / diff", or to check code another agent produced. For acting on review feedback you *received*, use receiving-code-review instead.
---

# Code Review

Adversarial review of a diff. **Assume the change contains defects and prove
them** — do not validate that work was done. One authoritative pass that folds
in correctness bug-hunting, the five quality axes, over-engineering, and
simplification, so a change gets *one* review instead of four overlapping ones.

**Approval standard:** approve when the change *definitely improves overall code
health*, even if imperfect. Don't block because it isn't how you'd have written
it. But don't rubber-stamp — a soft review is a failed review.

## When to run

- Before merging any change to a shared branch
- After completing a feature or a bug fix (review the fix **and** its regression test)
- When asked to review a specific commit, range, or PR
- When evaluating code another agent or model produced (needs *more* scrutiny, not less)

## Step 1 — Pick the review target

A review is always the diff between two points. Resolve the target the user named
(ask if ambiguous):

| Target | Diff to review |
|--------|----------------|
| Working (uncommitted) changes | `git diff HEAD` (add `--staged` for staged-only) |
| A specific commit `<sha>` | `git show <sha>` (i.e. BASE=`<sha>~1`, HEAD=`<sha>`) |
| A commit range | `git diff <base>..<head>` |
| A branch / PR | `git diff <base-branch>...HEAD` |

Nothing requires the changes to be yours or uncommitted — the target is whatever
diff you were asked to review.

## Step 2 — Gather context first

Before reading the diff, establish intent and rules:

- **What is this change trying to do?** Its spec/task/PR description. Under wfctl,
  read `specs/<branch>/spec.md` and `plan.md` (`wfctl feature-paths` prints them).
- **Project rules:** read `CLAUDE.md`/`AGENTS.md` and skim `.agents/skills/` — follow
  project conventions, security requirements, and naming. Review *against the
  project's* standards, not external preference.
- **Read the tests first.** They reveal intent and coverage. Do they test behavior
  (not implementation)? Are edge cases covered? Would they catch a regression?

## Step 3 — Review with fresh context

Evaluate the *work product*, not the author's reasoning. If your harness can
dispatch a subagent, hand a reviewer **only the diff + the requirements + the
project rules** — never your session history. Fresh context is the point: an
author (you included) is blind to their own assumptions; a reviewer primed only
by the code and the spec catches what the author rationalized past.

If you can't dispatch a subagent, run the passes yourself as a deliberate,
skeptical pass — re-read the diff cold, don't lean on what you "know" it does.

## Step 4 — The six passes

Run every pass. Trace called functions, not just the changed lines.

**1. Correctness** (adversarial — assume it's broken)
- Does it do what the spec/task claims? Match requirements, not vibes.
- Edge cases: null, empty, boundary, zero/negative, unicode, concurrent access.
- Error paths handled, not just the happy path. No swallowed exceptions.
- Off-by-one, race conditions, state inconsistency, incorrect async ordering.
- "Compiles" and "tests pass" are **not** proof of correctness.

**2. Security**
- User/external input validated and sanitized at the boundary.
- No secrets in code, logs, or history. Auth/authz checked where needed.
- Parameterized queries (no string-built SQL); outputs encoded (no XSS).
- Treat all data from APIs/config/user content as untrusted.

**3. Architecture**
- Fits existing patterns; a new pattern must be justified.
- Clean module boundaries, dependencies flowing one way (no cycles).
- Duplication that should be shared; coupling that shouldn't exist.

**4. Readability & simplification** (preserve behavior — this is review, not rewrite)
- Names describe content (`validationErrors`, not `data`/`temp`/`result`).
- Guard clauses over deep nesting (3+ levels); split 50+ line functions.
- No nested ternaries, boolean-flag params, clever tricks that need a mental pause.
- Comments explain *why*, never *what*; delete `// increment counter`.
- Apply Chesterton's Fence: understand why code exists (git blame) before calling it removable.

**5. Performance**
- N+1 queries, unbounded loops/fetches, missing pagination on lists.
- Sync work that should be async; large allocations in hot paths; needless re-renders.
- Quantify: "N+1 adds ~50ms/item" beats "might be slow".

**6. Over-engineering** (the diff's best outcome is getting *shorter*)
One line per finding — `<file>:L<n>: <tag> <what>. <replacement>.`:
- `delete:` dead code, unused flexibility, speculative feature → nothing replaces it.
- `stdlib:` hand-rolled thing the standard library ships → name the function.
- `native:` dep/code doing what the platform already does → name the feature.
- `yagni:` abstraction with one implementation, config nobody sets, layer with one caller.
- `shrink:` same logic, fewer lines → show the shorter form.
- A single smoke test / `assert` self-check is the minimum, **not** bloat — never flag it.

## Step 5 — Classify and report

Every finding carries a severity and a concrete fix. Order most-severe first.

| Severity | Meaning | Author action |
|----------|---------|---------------|
| **BLOCKER** | Incorrect behavior, security hole, or data-loss risk | Must fix before merge |
| **WARNING** | Degrades quality, maintainability, or robustness | Should fix |
| **NIT** | Style/naming/formatting preference | Optional — author's call |

Write findings to `REVIEW.md` in the feature dir (`specs/<branch>/REVIEW.md`) when
one exists, else print them. Each finding: `SEVERITY file:Lline — defect → fix`.
End with the over-engineering metric `net: −<N> lines possible` (or `Lean already.`)
and a verdict: **Approve** or **Request changes**.

```
## Review: <target>

BLOCKER  auth.py:L42 — token compared with == (timing leak) → hmac.compare_digest
WARNING  api.py:L88 — N+1: fetches user per row (~50ms/item) → join / prefetch
WARNING  repo.py:L12 — yagni: AbstractRepository, one impl → inline until a 2nd exists
NIT      util.py:L5 — name `data` → `parsedRows`

net: −34 lines possible
Verdict: Request changes (1 blocker)
```

## Step 6 — Act, then verify

- **BLOCKER** → fix before proceeding. **WARNING** → fix, or defer only with written
  justification (file a follow-up; "clean it up later" without a ticket doesn't count).
  **NIT** → author's discretion.
- Re-run the target's tests + build after fixes. Confirm BLOCKERs are gone.
- Separate refactoring from feature work — if the review surfaces cleanup beyond the
  change's scope, file it, don't smuggle it into this diff.

## Honesty (this is where reviews fail)

- **Don't rubber-stamp.** "LGTM" without evidence helps no one.
- **Don't soften real issues.** "Might be a minor concern" about a production bug is dishonest.
- **Don't go soft on severity** to seem agreeable — a downgraded BLOCKER is a shipped bug.
- **Quantify** problems; comment on the code, not the person.
- **Accept override gracefully.** If the author has full context and disagrees with reasoning, defer.

## Red flags in your own review

- Only checking that tests pass (ignoring the other five passes).
- Reading the changed file but not the functions it calls.
- Stopping at surface issues (`console.log`, empty catch) and assuming the rest is sound.
- Findings without a severity, or without a concrete fix.
- A bug-fix diff with no regression test.
