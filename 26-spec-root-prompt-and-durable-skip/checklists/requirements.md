# Specification Quality Checklist: spec-root prompt and durable-spec skip

**Purpose**: Validate specification completeness and quality before proceeding to planning
**Created**: 2026-08-10
**Feature**: [spec.md](../spec.md)

## Content Quality

- [x] No implementation details (languages, frameworks, APIs)
- [x] Focused on user value and business needs
- [x] Written for non-technical stakeholders
- [x] All mandatory sections completed

## Requirement Completeness

- [x] No [NEEDS CLARIFICATION] markers remain
- [x] Requirements are testable and unambiguous
- [x] Success criteria are measurable
- [x] Success criteria are technology-agnostic (no implementation details)
- [x] All acceptance scenarios are defined
- [x] Edge cases are identified
- [x] Scope is clearly bounded
- [x] Dependencies and assumptions identified

## Feature Readiness

- [x] All functional requirements have clear acceptance criteria
- [x] User scenarios cover primary flows
- [x] Feature meets measurable outcomes defined in Success Criteria
- [x] No implementation details leak into specification

## Notes

**Clarification resolved.** The health check for stale project configurations is
**in scope** (FR-020), so the compatibility shim in FR-019 has an observable end
condition. Recorded with it: the check is transitional, and the collective
removal of the project's several superseded-path checks is tracked as separate
work. Adding one more is acceptable only on that understanding.

**Validation iterations run**: 2.

Iteration 1 found three failures, all fixed inline:

- Implementation details leaked into the requirements — specific file paths, the
  tool's own command names, and manifest key names appeared in FR text. Rewritten
  in terms of behaviour ("record it where it survives worktree removal" rather
  than naming the file). Concrete names remain only in `design.md`, which is
  where they belong.
- Success criteria were phrased as internal system states rather than measurable
  outcomes. SC-001 through SC-007 rewritten as counts and guarantees observable
  without knowing the implementation.
- The untested removal-tool assumption was stated as fact in the requirements.
  Moved to Assumptions, marked as unconfirmed, and named as the first validation
  step — a load-bearing assumption presented as settled is how a spec misleads a
  planner.

Iteration 2 found one:

- FR-020 and FR-021 originally read as implementation chores rather than
  requirements. Restated as requirements about the project's recorded rationale,
  which is what makes them verifiable — and FR-021 in particular guards against a
  documented requirement and shipped behaviour silently contradicting each other,
  which is exactly the situation this feature exists to resolve.

**Deliberate non-standard entry**: the specification names an unvalidated
assumption as a blocking first step rather than hiding it. Marked here so a
reviewer sees it was a decision, not an oversight.
