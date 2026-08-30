# Specification Quality Checklist: reply over-explains

**Purpose**: Validate specification completeness and quality before proceeding to planning
**Created**: 2026-08-29
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

- Items marked incomplete require spec updates before `/speckit.clarify` or `/speckit.plan`

**On "no implementation details":** the deliverable of this feature *is* two text
files, so FR-003, FR-006, FR-007 and FR-009 name them. Naming the artifact under
change is not a tech-stack leak — there is no stack choice being pre-empted, and
the Validation Strategy section is required to state commands.

**On SC-006** ("a reader can state what a reply is composed of after one read"):
qualitative, and deliberately so. The composition either lands on first read or it
is not doing its job; a count would not measure that.

**Revised 2026-08-29** after a live #99 exchange was brought in as evidence.
FR-004/FR-005 were rewritten, FR-004a/FR-005a added, and FR-008's *reason* was
replaced — the conclusion (no per-form trigger) stands, but the argument that
"stated rules do not fire" did not survive its own control, which moved the table
rule and the fan-out rule together. Re-validated: all items still pass.

**Revised again 2026-08-29** after a second live exchange (#556) was brought in.
Added User Story 5, FR-011/011a/011b, SC-011/SC-012, and one edge case. The
substantive change is that **prose word count is no longer the headline metric** —
the observed reply that failed the reader scored 40 words and passed every other
rule in the spec. SC-012 makes word count non-reportable on its own.
Re-validated: all items still pass.

**Carried into planning, not blocking here:**
- FR-001 and SC-001 need the design experiment's fixed tasks and the recorded
  variant-A baseline (~203 prose words) to be re-runnable. The replies from the
  original runs were in an ephemeral scratchpad; the findings survive on #102.
- SC-005 is the guard on the one assumption the experiment did not test —
  whether deleting the "ceiling" sentence over-compresses a question that
  genuinely asks for depth.
- SC-011 is the only check in this spec that reads the *reader's* next message
  rather than the reply itself. Planning needs to decide whether the benchmark
  harness can capture that, or whether it stays a manual read.
- SC-009 tests FR-005a's central claim — that a form-selection step beats the
  table rule — which is inferred from two cases and has never been run. If
  planning cannot make SC-009 runnable, FR-005a ships on inference and should
  say so.
