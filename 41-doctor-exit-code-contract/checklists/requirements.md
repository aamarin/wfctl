# Specification Quality Checklist: doctor exit-code contract

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

- Items marked incomplete require spec updates before `/speckit.clarify` or `/speckit.plan`

### Validation pass — 2026-08-17

Two items failed on the first pass and were fixed in the spec before this
checklist was marked complete:

1. **No implementation details** — failed. FR-001 through FR-004 named a return
   type and an operator (`-> bool`, OR'd into the exit code), and the Key Entities
   section named specific functions and file paths. These are the *how*. Rewritten
   as the three outcomes a check can report and the rule relating them to the exit
   code, which is the *what* and is testable without knowing the signature.

2. **Success criteria are technology-agnostic** — failed. An early SC cited a test
   count as the outcome. Test counts measure the work, not the result. Replaced
   with SC-001, which states the observable behaviour (one problem present →
   non-zero; removed → zero) and quantifies coverage across checks.

Two deliberate retentions, both judged in-scope rather than leaks:

- The Validation Strategy section names concrete commands. The template requires
  it to ("state the commands or checks that will prove the feature works"), so
  this is the one section where specificity is the requirement.
- FR-013 states that the version-freshness check must be left unmodified. This
  reads as an implementation constraint, but it is a scope boundary: it keeps this
  work non-conflicting with separate work already scoped against the same
  function. Recorded as a requirement because violating it costs a merge conflict,
  not a design error.

Zero [NEEDS CLARIFICATION] markers. The one genuinely open question — whether the
stranded-spec-directory check is transitional or permanent — affects a docstring
and no behaviour, so it is recorded as an assumption rather than a blocker.

### Clarify pass — 2026-08-17

Three questions asked and answered; recorded in the spec's `## Clarifications`
section. All three closed gaps that would have surfaced as rework during
implementation rather than review:

1. **Reporting granularity.** FR-008 said "files", but the install record stores
   directories too — a renamed skill directory would have produced one finding per
   file inside it. Resolved to report at the recorded unit. Added FR-008a and
   SC-007, and normalized "abandoned file" to "abandoned entry" throughout, since
   the old term contradicted the answer.

2. **Drift fixed during the run.** One check can offer a fix and apply it if
   accepted, leaving the repository clean by the time the run ends. Nothing said
   which exit code that produces. Resolved: the code describes the repository's
   state at exit. Added two acceptance scenarios, two edge cases (declined, and no
   interactive terminal), and a validation entry.

3. **"Closest shipped name."** Implied hand-written fuzzy matching. Resolved to an
   existing standard-library facility, which also removes matching code from the
   scope.

One vague criterion was fixed in the same pass: SC-005 read "zero findings that
are not genuine drift", which is circular and unmeasurable. Rewritten as zero
false positives, noting that one of the two reference repositories carries real
drift and is expected to produce findings.
