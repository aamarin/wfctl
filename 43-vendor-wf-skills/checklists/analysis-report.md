# Specification Analysis Report: Vendor wf-skills

**Feature**: `43-vendor-wf-skills` · **Date**: 2026-08-16
**Artifacts**: [spec.md](../spec.md), [plan.md](../plan.md), [tasks.md](../tasks.md)
**Supporting**: research.md, data-model.md, contracts/cli.md, quickstart.md
**Constitution**: none (`.specify/memory/constitution.md` absent — gates substituted in plan.md and recorded in its Complexity Tracking)

---

## Findings

| ID | Category | Severity | Location(s) | Summary | Recommendation |
| --- | --- | --- | --- | --- | --- |
| E1 | Coverage Gap | HIGH | spec.md:176 (FR-010), spec.md:249, tasks.md:T008 | FR-010 requires the fingerprint be identical for identical content **across operating systems**, and the spec's own Validation Strategy names "a cross-platform and cross-version fingerprint-stability check". T008 only asserts two trees hash *equal to each other* within a single run — it would pass even if macOS and Linux produced different digests. CI is `ubuntu-latest` only (ci.yml:19, :75); the author's machine is darwin. | Add a task asserting a **hardcoded expected digest** for a fixture tree. Runs on both matrix Pythons and would fail on any platform-dependent drift. One `assert content_hash(fixture) == "…"` covers both halves of FR-010. |
| E2 | Coverage Gap | MEDIUM | spec.md:192 (FR-017), tasks.md | FR-017 (`install-config` records no state, no staleness check) has **zero tasks**. It holds today by not being touched, but T025 edits that command's body, and nothing fails if a manifest write is added by accident. | Add one assertion to `test_install_config.py`: after `install-config workmux`, `.wf-skills-manifest.json` is absent or unchanged. Cheap, and it is the only guard on IC-2. |
| E3 | Coverage Gap | MEDIUM | spec.md:196 (FR-019), spec.md:247-248, tasks.md:T009-T010 | FR-019 and the Validation Strategy call for modifying "one file in **each** sourceable directory". T009 covers a generic edit, T010 covers `trackers/`. `skills/`, `commands/`, `configs/`, `specify/scripts/`, `specify/templates/` are not individually exercised, so a hash that accidentally skipped a subtree would still pass. | Parametrize T009 over the six sourceable directories rather than adding five tasks. |
| E4 | Coverage Gap | MEDIUM | spec.md:221 (SC-003), tasks.md | SC-003 ("under 2 seconds, down from roughly 15") has no task. It follows from deleting the clone, but nothing measures it and nothing would catch a re-introduced network call that is merely slow rather than absent. | Either accept it as a consequence of T021/T025 and say so in the spec, or fold a duration assertion into the T040 wheel job. Recommend the former — T019 already forbids the string that would cause it. |
| F1 | Inconsistency | MEDIUM | spec.md:42-99 vs tasks.md:188-197 | spec.md presents four independently-deliverable stories. The real dependency chain is US1 → US2 → US3, because each consumes the manifest shape the previous one writes. tasks.md discloses this in its "Deviation" section; spec.md and plan.md do not. | Leave tasks.md as the authority (it is what `/speckit.decompose` reads), but note the chain in plan.md so a reader who stops at the plan is not misled about merge order. |
| C1 | Underspecification | MEDIUM | plan.md (Structure), tasks.md:T003 | `wfctl = ["agents/**/*", "specify/**/*"]` is asserted but not derived — setuptools glob semantics for `**/*` at zero depth are not stated anywhere in the artifacts. | No action needed on the spec: T004 validates it empirically before anything depends on it, and a zero-file result is called out as a hard stop. Recorded so the reviewer knows the glob is verified, not assumed. |
| B1 | Ambiguity | LOW | spec.md:220 (SC-002) | "byte-identical … in 100% of attempts" has no task that compares two machines. T040 diffs the installed tree against the source tree on one runner, which is a proxy, not the stated measurement. | Accept the proxy, or reword SC-002 to what is actually checked: installed content matches the bundled source. |
| A1 | Duplication | LOW | spec.md:156-159 (FR-001/FR-002) | FR-001 and FR-002 are the same requirement applied to two commands, and map to overlapping tasks (T019 covers both). | Keep. The split is load-bearing — the two commands had separate clones and are edited by different tasks (T021, T025). |
| D1 | Inconsistency | LOW | spec.md:253-254 | The Assumptions block cites `specs/43-vendor-wf-skills/design.md`; the file actually lives at `/Users/andremarin/Development/wfctl-specs/43-vendor-wf-skills/design.md` (spec root is outside the repo). | Cosmetic. Fix on the next edit to spec.md. |
| G1 | Format | LOW | tasks.md:T013-T015, T017 | Four tasks carry no `verify with` phrase. All four are test-file edits or a deletion (their verification is the suite itself, asserted by the T026 checkpoint). | No change. Noting it so the omission reads as deliberate rather than missed. |

**No CRITICAL findings.** No constitution to violate; no missing core artifact; every user story has both an `Independent Test` and a `Verification` block.

---

## Coverage Summary

| Requirement | Has Task? | Task IDs | Verification? | Notes |
| --- | --- | --- | --- | --- |
| FR-001 no external source (skills) | ✅ | T019, T020, T021 | automated + quickstart §3 | |
| FR-002 no external source (config) | ✅ | T019, T025 | automated | |
| FR-003 no `aamarin/wf-skills` reference | ✅ | T019 | automated | excludes the vendored tree, correctly |
| FR-004 removed options error | ✅ | T018 | automated | zero product code (research §6) |
| FR-005 package carries everything | ✅ | T001, T003, T004, T040 | automated | |
| FR-006 destinations unchanged | ✅ | T020 | automated | `test_layer_destinations_are_disjoint` |
| FR-007 record version + fingerprint | ✅ | T023 | automated | |
| FR-008 fingerprint covers unlayered files | ✅ | T010 | automated | the tracker-JSON case |
| FR-009 changes on edit and rename | ✅ | T009 | automated | |
| FR-010 identical across OS + versions | ✅ | T008 | automated | was ⚠️ **E1** — resolved, see Remediation |
| FR-011 doctor reports locally | ✅ | T031 | automated | |
| FR-012 both versions + distinct equal msg | ✅ | T028, T029 | automated | |
| FR-013 names the remedy | ✅ | T028 | automated | T029 does not restate it; contract D covers both lines |
| FR-014 network check degrades | ✅ | T030 | automated | |
| FR-015 pre-change record warns | ✅ | T034 | automated | |
| FR-016 drops fetch details, keeps items | ✅ | T023, T035, T036, T037 | automated | M1 is the highest-risk invariant, covered by T036 |
| FR-017 install-config stays stateless | ✅ | T025 | automated | was ❌ **E2** — resolved, see Remediation |
| FR-018 checks verify the built package | ✅ | T040, T041 | automated | |
| FR-019 fingerprint coverage per file | ✅ | T009, T010 | automated | was ⚠️ **E3** — resolved, T010 parametrized over all six |
| SC-001 offline install | ✅ | T026, T040 | manual + automated | |
| SC-002 installed content matches the package | ✅ | T040 | automated | was ⚠️ **B1** — criterion reworded to what is checkable |
| SC-003 zero network round-trips | ✅ | T019, T021, T025 | automated | was ❌ **E4** — criterion reworded; wall-clock is a consequence |
| SC-004 stale repo found in one command | ✅ | T027, T031 | automated | |
| SC-005 doctor accurate offline | ✅ | T030 | automated | |
| SC-006 zero commands contact upstream | ✅ | T019 | automated | |
| SC-007 migration in one command | ✅ | T035, T036 | automated | |
| SC-008 broken packaging fails checks | ✅ | T044 | manual, once | acceptable — it is a destructive experiment, not a standing check |

## Constitution Alignment Issues

None applicable. The repo has no constitution. plan.md substitutes six gates from
`pyproject.toml`'s documented rationale and the checks CI runs, and records the
substitution in Complexity Tracking — which is what the plan template requires
rather than leaving the section decorative. All six are marked passing, and the
tasks that satisfy each are traceable: lint scope (no new ruff rules in any task),
typing (T007 annotates the new module), no network in the suite (T017, T042), no
user-reachable override (T011 monkeypatches; no task adds an env var).

## Unmapped Tasks

Six tasks map to no FR/SC. All are legitimate:

- **T005** — validates a research.md finding (`files()` resolution on the floor version) rather than a requirement
- **T032, T038** — regression guards on existing behaviour the change could disturb
- **T042, T043** — CI cleanup following from T017
- **T046, T047** — documentation of internals

## Verification Gaps

None blocking. Every user story declares an `Independent Test` and a `Verification`
block with named automated checks, manual flows and evidence. Every phase ends in a
checkpoint task naming its commands. The only implementation tasks without an
inline `verify with` are the four in **G1**, all test-file edits.

## Metrics

| Metric | Value |
| --- | --- |
| Total Requirements (FR + SC) | 27 |
| Total Tasks | 50 |
| Coverage (≥1 task) | 25/27 = **93%** |
| Full coverage (task + adequate verification) | 22/27 = **81%** |
| Ambiguity Count | 1 |
| Duplication Count | 1 (deliberate) |
| Inconsistency Count | 2 |
| **CRITICAL Issues** | **0** |
| HIGH Issues | 1 |
| MEDIUM Issues | 4 |
| LOW Issues | 4 |

---

## Next Actions

No CRITICAL issues — `/speckit.decompose` is not blocked.

## Remediation applied (2026-08-16)

All five recommended items were applied. **No task IDs were renumbered** — each fix
strengthened an existing task rather than inserting one, so every cross-reference in
`tasks.md` (T004, T011, T012, T017, T026, T040 …) still resolves.

| Finding | Resolution | Where |
| --- | --- | --- |
| **E1** HIGH | T008 now also asserts a **hardcoded expected digest** for a fixture tree, with the reason stated inline: equality-within-one-run passes even if macOS and Linux disagree, and CI is ubuntu-only while development is on darwin. Running on both matrix Pythons covers the cross-version half. | tasks.md T008 |
| **E2** MEDIUM | T025 now requires a new assertion in `test_install_config.py` that `install-config workmux` leaves the manifest absent or byte-unchanged — folded into the task that edits that function's body, which is what put FR-017 at risk. | tasks.md T025 |
| **E3** MEDIUM | T010 rewritten as `test_content_hash_covers_every_sourceable_directory`, **parametrized over all six** (`agents/skills`, `agents/commands`, `agents/trackers`, `agents/configs`, `specify/scripts`, `specify/templates`). Covers FR-008 and FR-019 in one test. | tasks.md T010 |
| **E4 / B1** MEDIUM / LOW | Reworded rather than measured. SC-002 now states what is actually checkable — installed content matches the built package — and says why comparing two machines is not an automated check. SC-003 now targets **zero network round-trips**, naming wall-clock as a consequence and SC-006 as the check that protects it. | spec.md SC-002, SC-003 |
| **F1** MEDIUM | The US1 → US2 → US3 chain is now stated in plan.md's Summary, including what breaks if US2 merges first (`doctor` compares a field nothing writes) and that US4 is genuinely parallel. | plan.md |
| **D1** LOW | Assumption no longer cites a `specs/` path that does not exist; it names `design.md` alongside the spec and points at `wfctl feature-paths`. | spec.md Assumptions |

**Not changed**: A1 (the FR-001/FR-002 split is load-bearing — separate clones,
separate tasks) and G1 (four test-edit tasks without an inline `verify with`; the
T026 checkpoint is their verification).

### Post-remediation metrics

| Metric | Before | After |
| --- | --- | --- |
| Coverage (≥1 task) | 25/27 (93%) | **27/27 (100%)** |
| Full coverage (task + adequate verification) | 22/27 (81%) | **27/27 (100%)** |
| HIGH issues | 1 | **0** |
| MEDIUM issues | 4 | **0** |
| LOW issues | 4 | 2 (both accepted as deliberate) |

FR-010, FR-017, FR-019, SC-002 and SC-003 move from partial/absent to covered. Task
count is unchanged at 50.
