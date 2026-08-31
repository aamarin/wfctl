# Specification Analysis Report: deployment key metadata

**Date**: 2026-08-30
**Artifacts**: spec.md, plan.md, tasks.md (+ research.md, data-model.md, contracts/, quickstart.md)
**Constitution**: none present. `AGENTS.md` documents the substitution to
`wfctl arch context`; plan.md records it in Complexity Tracking as the template
requires. Not treated as a violation.

**Verdict**: no CRITICAL findings. One HIGH, worth fixing before implementation
because it will produce a false red across a quarter of the bundle.

**Status: all 10 findings remediated on 2026-08-30.** The table below records
each finding as found; the Remediation Applied section records what changed. The
post-remediation metrics supersede the original ones.

## Findings

| ID | Category | Severity | Location(s) | Summary | Recommendation |
| --- | --- | --- | --- | --- | --- |
| G1 | Coverage | **HIGH** | tasks.md T010; `wfctl/agents/skills/speckit-*` | The FR-010 conformance test as described will false-fail 7 shipped skills. They carry `metadata:` with nested `author:` / `source:` children. A key scan that does not distinguish indentation reads those children as top-level keys, none of which is in the allowed set. | Amend T010 to state the parser contract: count only unindented lines between the opening and closing `---`, and stop at the closing delimiter. `_skill_deployment()` already did both; the replacement must not lose that. |
| G2 | Coverage | MEDIUM | spec.md FR-008; tasks.md | FR-008 ("discoverability MUST NOT be read from a previously installed skill tree") maps to zero tasks and zero tests. It is true by construction today, but nothing would fail if a future change made the mirror read the installed tree. | Either add an assertion that the mirror hook's source path descends from `BUNDLE_ROOT`, or restate FR-008 as an assumption rather than a requirement. A requirement nothing can falsify is documentation. |
| G3 | Coverage | MEDIUM | spec.md SC-006; tasks.md T017 | SC-006 claims installs for **every** other agent are **byte-identical** before and after. T017 checks `bob` only, asserts presence/absence rather than byte equality, and never exercises `codex`, `copilot` or `none`. | Either strengthen T017 to install with the pre-change build and the post-change build into two scratch repos and `diff -r` them, or narrow SC-006 to what T017 actually proves. |
| G4 | Coverage | MEDIUM | spec.md SC-003; tasks.md T013–T016 | SC-003 (discoverable skills go 6 → 7) is verified only by the manual exercise in `quickstart.md` §3. T014 tests the *mechanism* against a synthetic skill; no automated check asserts the real set's contents. | Accept as manual — the autouse `bundle` fixture replaces the real bundle, so an automated assertion would test the fixture. Record the reason in T016 so the gap reads as chosen rather than missed. |
| T1 | Traceability | MEDIUM | tasks.md (all phases) | FR-001, FR-002, FR-003, FR-008 and SC-004, SC-005, SC-006, SC-007 are not cited by identifier in any task. All but FR-008 and SC-004/007 are covered semantically, but the mapping is inferred rather than declared. | Add the identifiers to the task text where coverage exists. Cheap, and it makes the next analyze run deterministic instead of inferential. |
| G5 | Coverage | LOW | spec.md SC-004, SC-007 | Neither has a verification task. SC-004 (the declaration reads in under ten lines) is trivially true at seven names; SC-007 (net-negative line count) is checkable but unchecked. | Fold both into T029 as a two-line check: `git diff --stat` for SC-007, and reading the constant for SC-004. |
| V1 | Verification | LOW | tasks.md T028 | The only task with no declared verification path. Commenting on #59 is outward-facing and its completion is observable. | Add "verify by re-reading the issue thread" or similar, so the format rule holds across all 29 tasks. |
| I1 | Inconsistency | LOW | plan.md Complexity Tracking; tasks.md T019 | Complexity Tracking justifies the FR-010 conformance test as the one addition beyond the minimum, but the FR-005 declaration guard (T019) is also an addition the bare change does not require. | Add a row, or state that the guard is required by the design rather than beyond it. It converts a risk the design created into a check, which is a defensible framing — but it should be written down. |
| D1 | Duplication | LOW | spec.md FR-001, FR-010 | FR-001 states the property (no key outside the allowed set); FR-010 states its enforcement (a check that fails when one appears). Complementary, but they read as near-duplicates on a skim. | Keep both. Optionally cross-reference FR-001 → "enforced by FR-010" so the relationship is explicit. |
| A1 | Ambiguity | LOW | tasks.md T024 | "the message must read as drift rather than as an error" is a subjective acceptance condition. | Quote the expected `doctor` output fragment instead, the way T002 and T011 quote theirs. |

## Coverage Summary

| Requirement | Has Task? | Task IDs | Verification? | Notes |
| --- | --- | --- | --- | --- |
| FR-001 | Yes | T008, T009, T010 | Automated | Not cited by ID (T1) |
| FR-002 | Yes | T004, T005 | Automated | Not cited by ID (T1) |
| FR-003 | Yes | T006, T013 | Manual + automated | Not cited by ID (T1) |
| FR-004 | Yes | T014, T015 | Automated + manual | |
| FR-005 | Yes | T019 | Automated | |
| FR-006 | Yes | T017 | Manual | See G3 |
| FR-007 | Yes | T016 | Manual | |
| FR-008 | **No** | — | **None** | G2 |
| FR-009 | Yes | T020, T021 | Manual | Doc amendment; manual read is the only possible check |
| FR-010 | Yes | T010 | Automated | See G1 — the test as described misfires |
| SC-001 | Yes | T002, T011 | Measured, before/after | |
| SC-002 | Yes | T010, T011 | Automated + measured | |
| SC-003 | Yes | T013, T016 | Manual only | G4 |
| SC-004 | **No** | — | **None** | G5 |
| SC-005 | Yes | T019 | Automated | Not cited by ID (T1) |
| SC-006 | Partial | T017 | Manual, weaker than the claim | G3 |
| SC-007 | **No** | — | **None** | G5 |

## Constitution Alignment Issues

None. The repository has no `.specify/memory/constitution.md`; plan.md substitutes
the five accepted records from `wfctl arch context` plus the template's three
project-independent gates, and records the substitution in Complexity Tracking.
All eight gates are checked with a stated reason.

A `wfctl arch none` declaration was filed during design, so the design gate is
satisfied by a declared absence rather than by silence.

## Unmapped Tasks

None. Every task maps to at least one requirement, success criterion, or the
project's own definition of done in `AGENTS.md`.

## Verification Gaps

- FR-008 — no test, no manual check (G2).
- SC-004, SC-007 — no verification task (G5).
- T028 — the only task with no declared verification path (V1).

Every user story has both an `Independent Test` and a `Verification` block. 28 of
29 tasks declare a verification path.

## Metrics

| Metric | Value |
| --- | --- |
| Total functional requirements | 10 |
| Total success criteria | 7 |
| Total tasks | 29 |
| Requirement coverage (FR with ≥1 task) | 9/10 — 90% |
| Success criterion coverage (SC with ≥1 task) | 5/7 full, 1 partial — 71% full |
| Tasks with a declared verification path | 28/29 — 97% |
| Ambiguity findings | 1 |
| Duplication findings | 1 |
| Critical issues | 0 |
| High issues | 1 |

## Next Actions

No CRITICAL issues; `/speckit.decompose` is not blocked.

**Fix before implementation** — G1. It is not a documentation defect: T010 as
written produces a red suite on 7 untouched skills, and the natural reaction to
that red is to widen the allowed set, which would defeat the test's purpose.

**Fix before `/speckit.decompose`** — G2 and G3, both of which are requirements
claiming more than any task proves. Each is one edit to `tasks.md` or one
sentence in `spec.md`.

**Optional** — T1, G4, G5, V1, I1, D1, A1. None affects execution order.

Suggested: manually edit `tasks.md` for G1, G3, G5, V1 and T1; manually edit
`spec.md` for G2 (restate FR-008) or add the assertion. No re-run of
`/speckit.specify` or `/speckit.plan` is warranted — the artifacts are
structurally sound.


---

# Remediation Applied — 2026-08-30

All ten findings addressed. `tasks.md` was rewritten rather than patched, because
G2 added a task and inserting it mid-sequence would have desynchronised every
later identifier. Task count went 29 → 31.

| ID | Severity | What changed |
| --- | --- | --- |
| G1 | HIGH | T012 gained an explicit parser contract: count only unindented lines, stop at the closing `---`. It names the seven `speckit-*` skills that carry nested `metadata:` children, and instructs that a red run naming them means the parser is wrong — **not** that the allowed set should be widened. That wrong reaction was the actual risk. |
| G2 | MEDIUM | FR-008 restated in falsifiable form in `spec.md`: a skill present in the installed tree but absent from the bundle MUST NOT reach the native discovery path. New task T007 tests exactly that, so the requirement is no longer unverifiable. |
| G3 | MEDIUM | SC-006 now proven by byte comparison rather than presence. New task T003 captures pre-change installs for `none`, `codex`, `bob` and `copilot`; T019 installs the post-change build into four fresh repos and `diff -r`s each pair. A new cross-phase dependency is documented: T003's repos must survive until T019. |
| G4 | MEDIUM | T018 now records that SC-003's 6 → 7 count is verified manually and nowhere else, and why — the autouse `bundle` fixture replaces the real bundle, so an automated assertion would test the fixture. The gap is documented as chosen. |
| T1 | MEDIUM | Every task now cites the requirement identifiers it covers inline. Verified mechanically: all 10 FRs and all 7 SCs appear in at least one task. |
| G5 | LOW | T031 folded in both checks: `git diff --stat` net-negative for `wfctl/` excluding tests (SC-007), and the constant reading in under ten lines (SC-004). |
| V1 | LOW | T030 gained a verification path — re-read the issue thread and confirm the comment states both the rejected proposal and the reason. T025 was also tightened during the mechanical sweep, which caught it as the one remaining task without an explicit check. |
| I1 | LOW | `plan.md` Complexity Tracking gained a row for the FR-005 declaration guard, framed as restoring a property the frontmatter mechanism had by construction rather than adding a new one. |
| D1 | LOW | FR-001 now cross-references FR-010 — property and enforcement, explicitly related rather than near-duplicate. |
| A1 | LOW | T026 replaced the subjective "reads as drift rather than as an error" with the concrete expectation: a cyan ⬆ line naming the `base` layer, not a red `✗`, and capture the literal line. |

## Post-Remediation Metrics

| Metric | Before | After |
| --- | --- | --- |
| Total tasks | 29 | 31 |
| Requirement coverage (FR with ≥1 task) | 9/10 — 90% | **10/10 — 100%** |
| Success criterion coverage | 5/7 full, 1 partial | **7/7 full** |
| Tasks with a declared verification path | 28/29 — 97% | **31/31 — 100%** |
| Requirements cited by identifier in tasks | 9/17 | **17/17** |
| Critical issues | 0 | 0 |
| High issues | 1 | **0** |

Verified mechanically: task identifiers are sequential T001–T031 with no gaps,
every task carries a verification phrase, and every FR and SC appears in at least
one task.

## Residual Risk

Two items remain by choice rather than oversight, and both are written into the
artifacts so they are not rediscovered as surprises:

- **SC-003 is verified manually.** An automated assertion on the real
  `_MIRRORED_SKILLS` contents would run against the autouse fixture's bundle, not
  the shipped one. Documented in T018.
- **#110 and #60 stay open.** Removing a name later leaves a stale native copy
  nothing reports, and the upstream reference validator is not adopted here.
  Neither is in scope; both are filed.
