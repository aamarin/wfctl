# Specification Quality Checklist: one predicate signature

**Purpose**: Validate specification completeness and quality before proceeding to planning
**Created**: 2026-09-09
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

Two items passed on a reading worth stating, because a later reader will
otherwise judge them against the wrong audience.

**"Written for non-technical stakeholders" and "technology-agnostic".** This
feature's user is a wfctl maintainer, and the outcome they buy is the shape of
the code they will edit next. So SC-002 and SC-005 are stated over diffs and
branches rather than over screens, and that is the user-facing outcome here
rather than an implementation detail leaking in. The spec still names no
language, no library and no identifier: it says "the function that walks the
steps", not the function's name. Identifiers appear only in Validation Strategy,
which is the section for the commands that prove it.

**Type names avoided on purpose.** FR-003 and FR-004 are the invariants the
design record settles with a specific construct. The spec states the property —
an incomplete declaration is rejected before the commit, a state outside the four
names is rejected — and leaves the construct to the plan. `uv run mypy wfctl/`
appears in Validation Strategy because it is the command that proves it.

**First validation pass, no iterations needed.** No item failed, so the spec was
not revised after writing. Two requirements have no success criterion of their
own and are covered elsewhere on purpose: FR-009 (no new read on a path that had
none) is carried by the first edge case and by the design record's `Assumed`
section, and FR-007 (no continuation flag moves) is carried by SC-001, since a
moved flag changes what a user sees.

Items marked incomplete require spec updates before `/speckit.clarify` or
`/speckit.plan`. None are.
