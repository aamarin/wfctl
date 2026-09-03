# Specification Analysis Report: #85 merge install mode

**Analyzed**: 2026-09-01
**Artifacts**: spec.md, plan.md, tasks.md, research.md, data-model.md, contracts/hook-command.md, quickstart.md
**Constitution**: no `.specify/memory/constitution.md` in this repo — `plan.md`
substituted `wfctl arch context` + `AGENTS.md` as the gate source and recorded
that substitution explicitly (per the template's own instruction). Not
re-litigated here; treated as the alignment baseline below.

## Remediation Applied

E1 and E2 were folded into `tasks.md` (new T008, new T025; every task after
T007 renumbered) on 2026-09-01, per user approval. E3-E7 remain open —
addressable inline during implementation, not blocking `/speckit.decompose`.

## Findings

| ID | Category | Severity | Location(s) | Summary | Recommendation |
| --- | --- | --- | --- | --- | --- |
| E1 | Coverage Gap | HIGH | spec.md:167-169 (FR-015), tasks.md:41 (T004) | FR-015 ("merge mode MUST NOT be offered for agents whose settings schema does not define an equivalent hook mechanism") has an implementing task (T004 scopes the target list to `claude`) but no task asserts the negative case — that `install-skills --agent codex` or `--agent bob` neither writes a settings file nor gains a `merged` manifest record. | Add a task in Foundational or US1: assert no merge attempt for a non-`claude` agent (empty target list → no-op, confirmed by absence of a `merged` key). |
| E2 | Coverage Gap | HIGH | spec.md:199-202 (SC-005), spec.md:235-237 (Validation Strategy) | SC-005 — "the re-anchoring rule reaches the model on every turn of a session" — is the feature's central success criterion, and spec.md's own Validation Strategy names a manual check for it ("run a session … confirm it fires each turn"). `tasks.md`'s Polish phase (T023) runs `quickstart.md`'s six scenarios, none of which is a live multi-turn session — every quickstart step is a single invocation. The manual check spec.md itself calls for was not carried into a task. | Add a manual task in Phase 6: run an actual Claude Code session against a repo with the hook installed, confirm `UserPromptSubmit` fires it more than once, and that stdout matches standalone `wfctl hook user-prompt` output. |
| E3 | Coverage Gap | MEDIUM | spec.md:162-163 (FR-013), tasks.md:74 (T010) | FR-013 ("merged path MUST NOT be gitignored") is stated as an implementation constraint in T010's description but no task verifies it — no test asserts `.gitignore` gains no entry for `.claude/settings.json` after a merge install. | Add an assertion to T006 or a new US1 test: after install, the repo's gitignore mechanism (whatever `_BASE_TARGETS`/`_AGENT_TARGETS` writes) contains no entry for the merged path. |
| E4 | Coverage Gap | MEDIUM | spec.md:164-166 (FR-014), tasks.md:73 (T009) | FR-014 ("merged path MUST NOT be recorded in the manifest's items list") is implemented in T009 but not separately verified — T006's test checks foreign-entry preservation, not manifest shape. | Add an assertion to T006 or T009's paired test: `manifest["claude"]["items"]` excludes `.claude/settings.json`; `manifest["claude"]["merged"]` includes it. |
| E5 | Underspecification | LOW | spec.md:149-150 (FR-008), tasks.md:140-141 (T020, T021) | FR-008 ("uninstall MUST NOT open the file for writing when no wfctl entry is present") is implicit in T020's reuse of `_settings.remove_hooks` (which returns `False` when nothing changed), but neither T020 nor T021's text states the no-write behavior explicitly — unlike T009's install-side wording ("writing only when it reports a change"), which does. Asymmetric task wording for a requirement stated symmetrically in spec.md. | Add "skip the write when nothing changed" to T021's description, matching T009's phrasing, so the requirement is traceable from task text alone. |
| E6 | Underspecification | LOW | spec.md:157-158 (FR-011), tasks.md:67 (T006) | FR-011 ("entry MUST NOT embed skill text directly in settings.json") holds by construction — `HOOK_COMMAND` is a fixed short string — but no test asserts the installed command contains no skill-derived prose (e.g., a digest's text leaking into the command field). | Low priority given the structural guarantee; optionally add one assertion to T006 checking the installed command equals the constant exactly. |
| E7 | Terminology Drift | LOW | spec.md:23-52 vs. spec.md:171-176 (Key Entities) | spec.md itself alternates "wfctl hook entry" (US1 body), "wfctl entry" (acceptance scenarios), and "managed entry" / "Managed hook entry" (Key Entities, Requirements). Same concept, three names, all within one file. | Standardize on "managed entry" — the term Key Entities already canonicalizes — the next time spec.md is touched. Not blocking; no reader has yet been misled since context disambiguates every instance. |

No CRITICAL findings, no duplication, no unresolved placeholders, no ambiguous
adjectives, no task-ordering contradictions, no conflicting requirements
between artifacts.

## Coverage Summary Table

| Requirement Key | Has Task? | Task IDs | Verification? | Notes |
| --- | --- | --- | --- | --- |
| FR-001 | Yes | T009, T010 | Yes | T006 |
| FR-002 | Yes | T008 | Yes | T006 |
| FR-003 | Yes | T002 | Yes | T003 |
| FR-004 | Yes | T009 | Yes | T013, T015 |
| FR-005 | Yes | T009 | Yes | T013 |
| FR-006 | Yes | T020, T021 | Yes | T019 |
| FR-007 | Yes | T002, T020 | Yes | T003, T019 |
| FR-008 | Yes | T020, T021 | Partial | T019 tests it; task text doesn't name the no-write path explicitly (E5) |
| FR-009 | Yes | T016, T017 | Yes | T014 |
| FR-010 | Yes | T008 | Yes | T006 |
| FR-011 | Yes | T004, T009 | Partial | holds by construction; no explicit assertion (E6) |
| FR-012 | Yes | T011 | Yes | T007 |
| FR-013 | Yes | T010 | **No** | E3 |
| FR-014 | Yes | T009 | **No** | E4 |
| FR-015 | Yes | T004 | **No** | E1 |
| SC-001 | Yes | T009, T010 | Yes | T006 |
| SC-002 | Yes | T009 | Yes | T013 |
| SC-003 | Yes | T016, T017 | Yes | T014 |
| SC-004 | Yes | T020, T021 | Yes | T019 |
| SC-005 | Yes | T011 | Partial | mechanism tested (T007, T011); live-session firing check absent (E2) |

**Constitution Alignment Issues**: None. No constitution file exists; the
substitution `plan.md` records (`wfctl arch context` + `AGENTS.md`) is itself
the alignment baseline and both cited records — `install-modes`,
`no-hardcoded-agent`, `vendor-upstream-skills` — are reflected correctly across
spec/plan/data-model (checked during this pass, no conflict found).

**Unmapped Tasks**: None. Every task maps to at least one requirement, story,
or the Foundational/Polish phase it belongs to.

**Verification Gaps**: FR-013, FR-014, FR-015, SC-005 — see E1-E4 above.

## Metrics

- Total Requirements: 20 (15 FR + 5 SC)
- Total Tasks: 24
- Coverage % (requirements with ≥1 task): 100% (20/20)
- Requirements with full verification: 16/20 (80%)
- Ambiguity Count: 0
- Duplication Count: 0
- Critical Issues Count: 0
