# Specification Analysis Report: Machine-checked done

**Latest pass**: 2 of 2 — 2026-08-25
**Artifacts**: spec.md, plan.md, tasks.md, plus design.md, research.md,
data-model.md, contracts/, quickstart.md
**Mode**: read-only. No artifact was modified by this analysis.

Pass 1 and its remediation are retained as an appendix below.

## Pass 2 — 2026-08-25

Re-run after remediation. Pass 1's twelve findings were re-checked individually:
ten hold as resolved, one was resolved incompletely, and the remediation record
itself carries a counting error. Three findings are new — two of them introduced
by the remediation, which is the usual place to find them.

**No CRITICAL findings. One HIGH, two MEDIUM, two LOW.**

### Findings

| ID | Category | Severity | Location(s) | Summary | Recommendation |
| --- | --- | --- | --- | --- | --- |
| B1 | Inconsistency | HIGH | spec.md FR-023; data-model.md:49-50 | FR-023 requires a command that cannot be executed to be recorded as failed. `data-model.md` defines `failed` as "every command that **exited** non-zero" and `exit` as "0 only when every command **exited** 0". A missing executable never exits, so neither field has a defined value for it and the implementer must invent one. | Redefine `failed` as "every command that did not complete successfully, including one that could not be executed", and `exit` as "0 only when every command ran and exited 0". |
| B2 | Ambiguity | MEDIUM | spec.md Terminology; 26 sites across 8 files | U1 was recorded as resolved. A Terminology table was added naming four forbidden synonyms — and the body text still uses them 26 times outside tables: "verification command" ×14, "configured commands" ×9, "the check" ×3. A glossary contradicted by its own document is worse than none, because it makes the drift look settled. | Either normalize the 26 sites or delete the table. Half-applied is the one state to avoid. |
| B3 | Coverage | MEDIUM | spec.md FR-023; contracts/cli-verify.md; tasks.md T027 | FR-023 was added without a rendered case in the CLI contract, which documents seven outcomes and not this one. T027 instructs walking "every output case in `contracts/cli-verify.md`", so the new requirement is outside the manual check meant to catch exactly this. | Add a missing-executable block to `contracts/cli-verify.md` showing the message and exit 1. |
| B4 | Inconsistency | LOW | checklists/analysis-report.md, Pass 1 remediation | The remediation record states "22 FR → 24". The actual count is 23: FR-023 was added and FR-015 was promoted out of Deferred, not created. | Corrected here; see Metrics. |
| B5 | Coverage | LOW | quickstart.md | "What sends it back to `▶`" lists six staleness triggers and no failure or inconclusive row. Defensible — a failing run never reaches green — but a reader scanning that table will not find the most common case. | Optional row, or retitle to name it as staleness only. |

### Pass 1 findings, re-checked

| Pass 1 ID | Status | Evidence |
| --- | --- | --- |
| C1 missing executable | Resolved | FR-023 in spec.md; T012, T013 in tasks.md — but see B1 and B3 |
| F1 parallel markers | Resolved | mechanical re-check: zero within-phase `[P]` file collisions |
| I1 stale failed render | Resolved | `design.md` render names the commands; Superseded block present |
| C2 SC-006 surface | Resolved | SC-006 names `wfctl status`; T022 asserts it |
| C3 passing record, open boxes | Resolved | T023 |
| I2 `"failed": null` | Resolved | `design.md` now `[]`, supersession recorded |
| U1 terminology | **Incompletely resolved** | see B2 |
| X1 FR-015 deferred vs scheduled | Resolved | Deferred section removed; FR-015 is MUST; T044 stands |
| C4 record with no tasks | Resolved | folded into T021 |
| U2 stray `hashlib` | Resolved | zero occurrences in plan.md |
| X2 unmapped T045 | Resolved | T045 states what it stands in for |
| D1 FR-002 / FR-019 | Accepted, no change | different surfaces; merging loses one |

### Coverage

All 31 requirements (23 FR, 8 SC) carry at least one task. Five FRs and three
SCs are covered by implicit keyword mapping rather than an ID reference:
FR-001–004 and FR-006 map to T003–T007, T020, T029; SC-003, SC-004, SC-007 map
to T021, T030. FR-006 remains the central requirement with no ID reference in
any task — a traceability weakness, not a coverage gap.

### Constitution Alignment

`.specify/memory/constitution.md` does not exist. plan.md substitutes gates from
`AGENTS.md` and records the substitution, which the plan template requires. No
constitution findings are possible and none are asserted. The six substituted
repository gates were re-checked against the remediated artifacts and all hold.

### Unmapped Tasks

T001, T002, T009, T028, T035, T040, T046 are setup and merge gates, expected to
map to nothing. Every other task maps to at least one requirement.

### Verification Gaps

None mechanical. 46 of 46 tasks carry `verify with`, `verify by`, or `merge
gate`. Every story has an `Independent Test` and a `Verification` block. FR-020
and FR-021 remain manually verified, correctly, per `AGENTS.md`.

### Metrics

- Total requirements: 31 (23 FR, 8 SC) — pass 1 had 30 (22 FR, 8 SC)
- Total tasks: 46 — pass 1 had 42
- Coverage: 31 of 31 have at least one task (100%)
- Ambiguity count: 1 (B2)
- Duplication count: 1 (D1, benign, accepted)
- Critical issues: 0
- Findings carried forward unresolved: 1 (U1, now B2)

### Remediation Applied — 2026-08-25

Approved by the user after the pass-2 report. All five findings resolved.

| ID | Resolution |
| --- | --- |
| B1 | `data-model.md` redefined both fields: `exit` is "0 only when every command **ran and** exited 0"; `failed` is "every command that did not complete successfully — exited non-zero, or could not be executed at all (FR-023)" |
| B2 | Glossary corrected first — it had no canonical name for the CLI verb, which is *why* one phrase named two things. Added `wfctl verify` and `command` as canonical, then normalized 26 sites across 6 files. Measured clean with word-boundary matching |
| B3 | `contracts/cli-verify.md` gained a missing-executable case, so T027's manual walk now covers FR-023 |
| B4 | Corrected: 22 FR → 23, not 24. FR-015 was promoted, not created |
| B5 | `quickstart.md` gained a second table — what keeps a run from going green, as distinct from what makes a green verdict stale |

**Two corrections to the pass-2 report itself**, found while applying it:

1. **The drift count was overstated.** "the check" was matched as a substring and
   caught *checker*, *checkout*, and *checkbox*. Of the 26 sites, 3 were false
   positives. The real count was 23.
2. **The glossary over-constrained one term.** It banned "configured command"
   (singular), which is unambiguous and often the precise word. Banning it would
   have churned 8 sites for no gain in clarity. The row now permits it; only
   "verification command" — the genuinely ambiguous one — stays banned.

**Re-validated after normalization:**

```
verification command           clean
configured commands (plural)   clean
the check (standalone)         clean

tasks: 46 | sequential: True
missing verification path: none
FR: 23  SC: 8
NEEDS CLARIFICATION: 0
```

---

# Appendix — earlier passes

## Pass 1 — 2026-08-24

**Date**: 2026-08-24
**Artifacts**: spec.md, plan.md, tasks.md, plus design.md, research.md,
data-model.md, contracts/, quickstart.md
**Mode**: read-only. No artifact was modified by this analysis.

**No CRITICAL findings.** Three HIGH, five MEDIUM, four LOW.

## Findings

| ID | Category | Severity | Location(s) | Summary | Recommendation |
| --- | --- | --- | --- | --- | --- |
| C1 | Coverage | HIGH | spec.md Edge Cases; tasks.md Phase 3 | The edge case "a configured command is not installed" has no task. `subprocess.run` raises `FileNotFoundError` for a missing binary, so a typo in `wfctl.json` produces a traceback rather than the failed verification the spec requires. | Add a task under US1 handling the exception as a failed command, with a test asserting exit 1 and a message naming the command. |
| F1 | Inconsistency | HIGH | tasks.md, 16 `[P]` markers | Nine `[P]` tasks all write `tests/test_verify.py` and seven all write `tests/test_pipeline_commands.py`. The format rule defines `[P]` as "different files, no dependencies", and tasks.md's own Parallel opportunities section says these are sequential within each file. An executor trusting the markers collides. | Drop `[P]` from same-file tasks, keeping it only across the two test files, or split the test files per story. |
| I1 | Inconsistency | HIGH | spec.md Behavior; spec.md SC-006; data-model.md | Three artifacts disagree on what a failed status line shows. The rendered example is `failed — exit 1 at a1b2c3d, 2026-08-22`, which names neither command. SC-006 requires the user learn which command failed from status alone. data-model.md says name `record.failed`. | Settle on one. The data-model reading satisfies SC-006; the spec's rendered example does not, and it is the one an implementer will copy. |
| C2 | Coverage | MEDIUM | spec.md SC-006; tasks.md T017 | SC-006 is asserted only against `wfctl verify`'s output. No task asserts `wfctl status` names the failing command. Depends on I1's resolution. | Extend T019 or add a task asserting the status annotation carries the command, not just the condition. |
| C3 | Coverage | MEDIUM | spec.md Edge Cases; tasks.md | "Verification passes while tasks are incomplete" has no task. T019 covers the sentinel-alone case, which is a different condition. | Add an assertion that a passing record with open checkboxes stays `▶`. |
| I2 | Inconsistency | MEDIUM | design.md Design; data-model.md; contracts/verify-record.md | design.md's record example shows `"failed": null` — a single failing command. FR-013 arrived later and requires every command to run, so the field is a list everywhere downstream. Both documents sit in the feature directory; a reader who opens design.md alone gets the wrong shape. | Leave design.md as the historical record it is, but note the supersession in it, or accept that plan.md onward is authoritative. |
| U1 | Ambiguity | MEDIUM | spec.md, plan.md, contracts/ | One concept carries four names: "definition of done", "verification command", "configured commands", "the check". Flagged Outstanding at clarify and still unresolved. | Pick one canonical term before implementation; "definition of done" for the config, "verification run" for the act, is the split most artifacts already lean toward. |
| X1 | Inconsistency | MEDIUM | spec.md FR-015 (Deferred); tasks.md T040 | FR-015 is labeled Deferred and scoped out of the MVP, but T040 schedules it in Phase 6. | Either promote FR-015 out of Deferred, or cut T040. The current pair says both things. |
| C4 | Coverage | LOW | spec.md Edge Cases | "A record exists but no tasks are defined" has no task. Low impact — the `○` branch precedes every verification branch. | Optional assertion; the branch order already prevents it. |
| U2 | Underspecification | LOW | plan.md Technical Context | Lists `hashlib` among stdlib dependencies. research.md decision 3 rejected hashing the working tree, and nothing else in the design hashes. | Remove `hashlib`. |
| D1 | Duplication | LOW | spec.md FR-002, FR-019 | Both govern the no-config case — FR-002 for status, FR-019 for the command. Overlapping but not duplicate. | Keep both; no action. |
| X2 | Coverage | LOW | tasks.md T041 | Adopting `wfctl.json` in this repository maps to no FR or SC. Justified as the only end-to-end exercise, but untraceable. | Note in the task that it validates SC-001 through SC-008 in situ, or accept it as unmapped dogfooding. |

## Coverage Summary

| Requirement | Has Task? | Task IDs | Verification? | Notes |
| --- | --- | --- | --- | --- |
| FR-001 read optional config | yes | T003, T004 | yes | implicit mapping, no ID reference |
| FR-002 absent = unchanged | yes | T004, T032, T034 | yes | implicit |
| FR-003 command runs and records | yes | T010, T012, T016 | yes | implicit |
| FR-004 record fields | yes | T005, T006, T007 | yes | implicit |
| FR-005 verdict not caller-asserted | yes | T019 | yes | |
| FR-006 completion conditions | yes | T018, T025 | yes | implicit; the central requirement, no ID reference |
| FR-007 name the failing condition | yes | T017 | partial | see C2 |
| FR-008 route to verification | yes | T020, T021 | yes | |
| FR-009 status runs nothing | yes | T022 | yes | |
| FR-010 argv, never shell | yes | T011 | yes | |
| FR-011 stays tracked | yes | T035 | yes | |
| FR-012 malformed is an error | yes | T017 | yes | |
| FR-013 run all, report all | yes | T010, T011 | yes | |
| FR-014 correct the README | yes | T039 | yes | manual check |
| FR-015 doctor reports bad config | yes | T040 | yes | see X1 — spec defers it |
| FR-016 inconclusive on drift | yes | T028, T029 | yes | |
| FR-017 write only on completion | yes | T012, T013 | yes | |
| FR-018 no resume | yes | T012 | yes | |
| FR-019 no config exits 0 | yes | T033, T034 | yes | |
| FR-020 skill runs verification | yes | T037 | manual | per AGENTS.md, skills are not verified by the suite |
| FR-021 skill does not claim done | yes | T038 | manual | same |
| FR-022 event per run | yes | T014, T015 | yes | |
| SC-001 unconfigured unchanged | yes | T032 | yes | |
| SC-002 zero commands executed | yes | T022 | yes | |
| SC-003 failing DoD never complete | yes | T019 | yes | implicit |
| SC-004 any change stops green | yes | T026 | yes | implicit |
| SC-005 fresh checkout unverified | yes | T030 | yes | |
| SC-006 user learns which command | partial | T017 | partial | see I1, C2 |
| SC-007 clean tree required | yes | T026 | yes | implicit |
| SC-008 history reconstructable | yes | T015 | yes | |

## Constitution Alignment

`.specify/memory/constitution.md` does not exist. plan.md substituted gates from
`AGENTS.md`, this project's documented conventions file, and recorded the
substitution in Complexity Tracking — which is what the plan template requires
when no constitution is present. No constitution findings are possible, and none
are asserted.

The six substituted repository gates were checked against the artifacts:

- Skills edited at source, not in `.agents/` — T037, T038 name
  `wfctl/agents/skills/…`. Satisfied.
- No lint-rule expansion — no task touches `pyproject.toml`. Satisfied.
- New functions annotated — T009, T031 run mypy as gates. Satisfied.
- No version bump — no task touches `version`. Satisfied.
- One PR closes one issue — deferred to `/speckit.decompose`.

## Unmapped Tasks

T001, T002, T009, T024, T031, T036, T042 are setup and merge gates, expected to
map to nothing. T041 is unmapped dogfooding — see X2. Every other task maps to at
least one requirement.

## Verification Gaps

Every user story carries an `Independent Test` and a `Verification` block. Every
implementation task carries a verification path — checked mechanically: 42 of 42
tasks contain `verify with`, `verify by`, or `merge gate`.

Two requirements (FR-020, FR-021) are verified manually rather than
automatically. This is correct per `AGENTS.md`: "A change to anything under
`wfctl/agents/` is not verified by the test suite alone." It is recorded here so
the manual step is not skipped.

## Metrics

- Total requirements: 30 (22 FR, 8 SC)
- Total tasks: 42
- Coverage: 30 of 30 have at least one task (100%); 1 partially covered (SC-006)
- Ambiguity count: 1 (U1, terminology). Zero unquantified vague adjectives; zero
  placeholders.
- Duplication count: 1 (D1, benign)
- Critical issues: 0

---

## Remediation Applied — 2026-08-24

Approved by the user after the read-only pass. Every HIGH and MEDIUM finding is
resolved; the LOW findings are resolved or accepted with a reason.

**One finding was misfiled and is corrected here.** I1 was located at "spec.md
Behavior". `spec.md` contains no rendered status block — the stale render is
`design.md:37`. That makes I1 the same class as I2: an upstream document holding
a shape its downstream artifacts have moved past, not a live contradiction inside
the specification.

| ID | Severity | Resolution |
| --- | --- | --- |
| C1 | HIGH | FR-023 added to spec.md; T012 handles `FileNotFoundError` as a failed command, T013 asserts exit 1 and a named command rather than a traceback |
| F1 | HIGH | All 16 misplaced `[P]` markers removed. Phases 2–4 now carry none, and Parallel opportunities states the real structure: two lanes by test file, sequential within each. Remaining `[P]` markers verified free of within-phase file collisions |
| I1 | HIGH | `design.md:37`'s failed render now names the failing commands, matching SC-006 and data-model.md. A Superseded block at the top of design.md names both places it no longer governs |
| C2 | MEDIUM | SC-006 reworded to say `wfctl status`, not "the status output" — the ambiguity that let a verify-only test satisfy it. T022 renders the commands in the annotation and asserts it |
| C3 | MEDIUM | T023 asserts a passing record with open checkboxes stays `▶` |
| I2 | MEDIUM | `design.md`'s `"failed": null` corrected to `[]`, with the supersession recorded rather than silently rewritten |
| U1 | MEDIUM | Terminology table added to spec.md fixing four names to one each; tasks.md carries a pointer to it |
| X1 | MEDIUM | FR-015 promoted out of Deferred to MUST. T044 already scheduled it, and a silently ignored broken configuration is this feature's own failure mode |
| C4 | LOW | Folded into T021 — a record present with no `tasks.md` still reports `○` |
| U2 | LOW | `hashlib` removed from plan.md's dependencies; nothing hashes |
| X2 | LOW | T045 now states it stands in for SC-001 through SC-008 in situ, being the only end-to-end exercise |
| D1 | LOW | Accepted. FR-002 and FR-019 govern different surfaces — status and the command — and merging them would lose one |

**Task count**: 42 → 46. Four added (T012, T013, T022, T023), all in US1.
Renumbered so IDs stay sequential in execution order; the coverage table above
uses pre-remediation IDs and is superseded by tasks.md.

**Re-validated after the rewrite:**

```
tasks: 46
bad format: none
ids sequential: True
missing verification path: none
within-phase [P] collisions: none
stray '[ ]': none
```

**Requirements**: 22 FR → 24 (FR-023 added, FR-015 promoted). Success criteria
unchanged at 8.
