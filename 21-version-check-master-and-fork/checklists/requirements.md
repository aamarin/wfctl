# Specification Quality Checklist: version check — default branch and fork

**Purpose**: Validate specification completeness and quality before proceeding to planning
**Created**: 2026-08-17
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

Two iterations were needed. Both fixes are recorded here rather than silently
absorbed, because each was a real leak the first draft would have carried into
planning:

1. **Implementation detail leaked into requirements.** FR-002 and FR-003 named
   `direct_url.json`, PEP 610, and `git ls-remote --symref` — mechanism, not
   requirement. Rewritten as "read from local install metadata, with no network
   access" and "resolved from the remote rather than assumed". The mechanism
   survives in `design.md`, which is where it belongs; the spec now states the
   property that must hold, and planning is free to satisfy it differently.

2. **A success criterion was unverifiable as written.** An earlier SC counted
   lines of code changed, which is neither user-facing nor a measure of success.
   Replaced by SC-006, which is verifiable against two recorded incidents.

Both open questions carried over from `design.md` were resolved before writing,
by evidence rather than assumption, and are recorded in the Edge Cases and
Assumptions sections:

- **Exit code safety** — a repo-wide search found no CI step, script, or skill
  gating on `wfctl doctor`'s exit status; the only consumers read its output.
  FR-006 is therefore safe.
- **Build ahead of tip** — documented as accepted imprecision under Edge Cases,
  with the reasoning for why it is unreachable through any supported install
  path.

FR-005's requirement that the printed reinstall command be *verified* to
re-resolve the branch is deliberately phrased as an obligation on the
implementation, not an assumption. It is the one requirement whose failure would
make the whole feature unactionable, and it is called out again in the Validation
Strategy so it cannot be marked done by inspection.
