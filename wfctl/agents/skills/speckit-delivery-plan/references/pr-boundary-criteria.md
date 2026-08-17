# PR Boundary Criteria — Detailed Guide

## The 4-Signal Framework

Each signal asks a yes/no question. More YES answers → stronger case to split.
More NO answers → bundle everything in one PR.

### Signal 1: File Conflict Risk

**Question:** Do two groups of tasks edit the same file?

| Scenario | Action |
|----------|--------|
| Different groups edit different files only | Safe to bundle or split — no conflict risk |
| Two groups edit the same file, but sequentially | Bundle; the second group depends on the first |
| Two groups edit the same file concurrently | Must bundle or coordinate carefully |

**Example (bundle):**
T004 creates a route-registration module and T005 modifies the entry point to call
it. Different files → no conflict → bundle.

**Example (split candidate):**
Story A adds a new model to `schema.ts` and Story B adds a different model to `schema.ts`.
Both groups edit the same file but the changes are independent → could split but
sequencing is simpler → bundle.

### Signal 2: Reviewability

**Question:** Can a reviewer assess the correctness of a subset without seeing the rest?

A reviewer needs to verify:
- Does the feature work end-to-end?
- Are authorization rules correct?
- Are the tests sufficient?

If one story's PR makes no sense without the other (e.g., "extract routes" without
"verify no routes remain in index.ts"), bundle them. If each story is a complete,
demonstrable increment, split is viable.

**Rule of thumb:** A PR should tell a complete story. "I added accounts API" is a
complete story. "I added the accounts model but not the route" is not.

### Signal 3: Mergeable Increment

**Question:** If we merge only this subset, does the feature remain in a working,
testable state?

- Merging Story A alone leaves the feature 50% done but **working**: merge candidate.
- Merging Story A alone leaves the codebase **broken** (TypeScript errors, missing
  imports): bundle required.

**Example:** Creating the route-registration module without updating the entry point
to call it would leave the app broken — the module exists but nothing invokes it.
Not a mergeable increment → bundle.

### Signal 4: Story Independence

**Question:** Are the acceptance criteria and runtime paths completely separate?

Independent stories:
- Have separate acceptance scenarios in spec.md
- Touch different data models or API paths
- Can be tested completely without the other story's code

Example:
- US1 (routes reachable) and US2 (developer experience) share the same code change.
  US2 literally verifies what US1 implemented. Not independent → bundle.

---

## Decision Tree

```
Are any files touched by >1 story? ──YES──→ Can they be sequenced? ──YES──→ Bundle
         │                                           │
         NO                                          NO → Coordinate (rare)
         │
Can each story be merged independently without breaking the build?
         │
        YES ──→ Are all acceptance criteria verifiable independently?
         │               │
         │              YES ──→ Split candidate
         │               │
         │               NO ──→ Bundle
         │
         NO ──→ Bundle
```

---

## Worked Examples

### XS Feature (2 files) → Always single PR

2 files, mutually dependent.
Verdict: 1 PR, 1 issue.

### S Feature (4 files, 2 stories) → Usually single PR

Feature: Add accounts API (model + service + route + test).
Signal 1: All files different — no conflict.
Signal 2: Model alone is not reviewable (no route to test against).
Signal 3: Model alone is not mergeable (service imports it but route doesn't exist).
Signal 4: Stories are sequential (model → service → route).
Verdict: 1 PR, 1 issue.

### M Feature (6 files, 2 independent stories) → Possible split

Feature: Add accounts + add categories (truly independent domains).
Signal 1: Different files per story — no conflict.
Signal 2: Each story reviewable on its own.
Signal 3: Each story mergeable without the other.
Signal 4: Fully independent acceptance criteria.
Verdict: 2 PRs (one per story), each with its own issue.

### L Feature (10 files) → Split required

Feature: Full onboarding flow (interview + persistence + recovery).
Signal 1: All stories share `OnboardingProgress` model.
Resolution: Put model in Story 1 (foundational), subsequent stories depend on it.
Verdict: 2–3 PRs by dependency order, one issue per PR under a parent epic.
