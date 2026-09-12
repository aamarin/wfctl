# Specification Quality Checklist: recycle context between tasks

**Purpose**: Validate specification completeness and quality before proceeding to planning
**Created**: 2026-09-11
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

Two items were argued rather than ticked on sight, and the reasoning is worth
keeping because both would read as failures to a reviewer scanning quickly.

**"No implementation details"** — FR-001 says wfctl computes the verdict "from the
agent transcript it is already handed", and FR-004 names
`speckit-orchestrate` and its two neighbouring branches. Both name components
rather than technologies, and both are constraints the level-2 records already
bind (`wfctl-owns-the-recycle-verdict`, `wfctl-names-the-reset-it-cannot-perform`).
A spec that omitted them would leave the ownership question open after it had
been decided, which is the failure `design-levels` puts at level 2. They stay.

**"No [NEEDS CLARIFICATION] markers"** — none were written, and the run was under
`auto_approve`, where a question is answered from the codebase and the tracker
with its basis recorded rather than left as a marker. Two questions that would
otherwise have been markers are carried as open questions in `design.md`: the
threshold's denominator, and whether `/end-session` earns its cost at a mid-run
boundary. Neither blocks planning, and both are bets the design names in its
`Assumed` column rather than gaps in the spec.
