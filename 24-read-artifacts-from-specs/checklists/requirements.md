# Specification Quality Checklist: Read artifacts from specs/&lt;branch&gt;/

**Purpose**: Validate specification completeness and quality before proceeding to planning
**Created**: 2026-08-06
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

- **Named code symbols are deliberate.** `_SPEC_MAP`, `_DESIGN_DOC`, and the
  `.agent/` path are the subject of this feature, not incidental implementation
  choices — the change is *where tooling reads a file from*. The house style
  (`specs/configurable-issue-key/spec.md`) names call sites for the same reason.
  "No implementation details" passes on intent: nothing here prescribes an
  approach the plan phase should be free to choose.
- Zero clarification markers: issue #24 supplies the entry points and acceptance
  criteria, and the upstream epic's clarification session already settled the
  one open question (report skew vs. dual-path reading).
- Three judgment calls are recorded as assumptions rather than markers — skew
  check at repo root only, no auto-migration of an existing `.agent/spec.md`,
  and `.gitignore` cleanup (FR8). Each has a defensible default; reverse any of
  them in `/speckit.plan` if you disagree.
- **Revised after implementation review (2026-08-06).** Two requirements were
  wrong as first written and are now corrected in place:
  - **FR7** demanded the grep return *nothing*, which contradicts FR4 — a
    warning that says to remove `.agent/` must contain the string `.agent/`.
    Now scoped to "only the diagnostic, the sweep, and their tests".
  - **FR3** forbade reading both locations without distinguishing inference from
    preservation. Taken literally it made `archive-story` delete design docs at
    the old path on teardown, across 11 live worktrees. **FR3a** now draws the
    line: infer from one place, but never let a teardown hook be the reason a
    file stops existing.

  Both were caught by review, not by the spec. Worth noting that a spec written
  after the implementation still missed them — the tests and a manual teardown
  run found them.
