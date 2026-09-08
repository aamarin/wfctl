# Specification Quality Checklist: outward-facing authority

**Purpose**: Validate specification completeness and quality before proceeding to planning
**Created**: 2026-09-07
**Feature**: [spec.md](../spec.md)

## Content Quality

- [x] No implementation details (languages, frameworks, APIs)
- [x] Focused on user value and business needs
- [ ] Written for non-technical stakeholders
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

### What failed on the first pass, and what changed

Four items failed and were fixed in the spec rather than waived:

- **Implementation details / no leakage.** The unreadable-grant edge case cited a
  module and line number, and the assumptions named a specific third-party API
  surface. Both were rewritten to describe the behaviour rather than the code.
  The file-and-line detail belongs in `design.md`, which already carries it under
  *checked*.
- **Success criteria technology-agnostic.** SC-005 named another branch's parked
  implementation. Reworded to name the blocked step by what it is, so the
  criterion survives that branch being renamed or rebased.
- **Every functional requirement has an acceptance scenario.** FR-013 — the
  irreversible class stays unreachable — had none, which is the requirement most
  likely to be quietly dropped precisely because nothing exercises it. A scenario
  was added to User Story 3, and it asserts the *wording* too: refusing an
  ungrantable action must not read as a missing grant.

### The one item left unchecked, deliberately

**Written for non-technical stakeholders** — not met, and not fixable without
making the spec worse. The reader of this feature is the developer operating
wfctl; the spec names `wfctl status`, `main`, branches and trackers because those
are the surfaces the feature changes, not because they are implementation. A
version with those removed would describe nothing testable.

Recorded rather than ticked, because a checklist that gets ticked for tidiness
stops being evidence. The PM-facing framing of this feature exists — it is what
`design.md`'s level-1 walkthrough and the issue body carry — and it is a
different document from a spec.

### Standing risk carried into planning

`spec.md`'s assumptions name two unverified beliefs about how the tracker
notifies people: that tagging an issue notifies its watchers, and that moving it
between board columns does not. Both are load-bearing — the whole classification
rests on them, and one of them is what makes the proposed grant surface
self-bootstrapping. **They are not a clarification question for the spec; they
are a factual check somebody has to run**, and `design.md` asks for it before
`plan`. Listed here so `plan` cannot claim it was not told.
