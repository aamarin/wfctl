# Specification Quality Checklist: save-uncommitted-on-remove

**Purpose**: Validate specification completeness and quality before proceeding to planning
**Created**: 2026-10-14
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

- wfctl is a command-line tool, so its commands, flags, `wfctl.json` keys, and
  output are the user-facing surface. The spec names them for that reason, and
  they don't count as implementation details here. The same holds for git
  terms such as "untracked" and "staged", which are what a wfctl user already
  reads.
- FR-021's staging folder is the one requirement that describes how rather
  than what. It stays because the guarantee it gives, no partial `unsaved/`
  after a failed copy, is only testable when the spec says the copy is
  atomic.
- FR-019, copying an untracked symlink as a link, was not decided in
  `design.md`. It is a default chosen so a link to a large outside folder
  can't pull that folder into the state dir. Clarify can revisit it.
