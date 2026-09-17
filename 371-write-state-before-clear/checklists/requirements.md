# Specification Quality Checklist: Session restart that writes its handoff first

**Purpose**: Validate specification completeness and quality before proceeding to planning
**Created**: 2026-09-15
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

- The reader of this feature is a developer running wfctl, so its user-facing
  surface is itself technical: the `wfctl hook session-restart` name, the
  `WFCTL_RESTART_THRESHOLD` variable, the pane messages and the `/end-session
  restart` argument are what the user sees and sets. They are kept as behavior.
  Module names, process mechanics beyond "after the hook exits", and file paths
  are left to the plan.
- SC-004 and SC-005 name tool-internal quantities (seconds per reply end, rows per
  subcommand) because they are what a developer of this tool observes; there is no
  more user-level measure of either.
- No clarification markers: run under `auto_approve: true`, and every open choice
  had a default already decided in the design records or the brainstorm ledger.
  Defaults taken at this step are in the spec's Assumptions and Edge Cases:
  `/end-session restart` sent at most once per session; hold reported once per send;
  two panes on one branch not guarded.
