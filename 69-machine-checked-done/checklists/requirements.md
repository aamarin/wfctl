# Specification Quality Checklist: Machine-checked done

**Purpose**: Validate specification completeness and quality before proceeding to planning
**Created**: 2026-08-23
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

Validation ran once; one item failed and was fixed inline.

**Failed on first pass — "Success criteria are measurable".** SC-002 read
*"remains fast enough to run on every session start without the user noticing
it."* Unfalsifiable: no observation distinguishes passing from failing. Rewritten
to *"executes zero configured commands, and adds at most a constant number of
repository queries"* — both countable.

**Judgment calls recorded, not silently passed:**

- *No implementation details* — the spec uses version-control vocabulary
  (commit, working tree, uncommitted changes). Kept: that is the feature's
  problem domain, not a technology choice. No file names, formats, command
  names, or languages appear outside the Validation Strategy section, which
  names checks by role rather than by tool.
- *Non-technical stakeholders* — the reader of this spec is a developer, and the
  product is a developer tool. Read as "no insider knowledge of this codebase
  required", which holds: nothing references an internal module or symbol.

**Zero clarification markers.** Four questions were left open by `design.md`.
Three had defensible defaults and were resolved into the Assumptions section
with their reasoning; the fourth was a test-design question that belongs to
task breakdown, and is recorded in the Validation Strategy instead.

**One consequence surfaced at spec time, not in design.** FR-006 requires a
clean working tree for a complete report. That was implied by the design's
staleness rule but never stated, and it is a real behavior change: a project can
only report implementation complete on committed code. Recorded in Assumptions
and as SC-007 so it is reviewed rather than discovered.
