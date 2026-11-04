# Plan review scan for #711

## Review 2026-11-04T00:52Z

- Verdict: unsatisfied
- Reviewed: plan.md f4788c839aa20270a92ce5a1d8b54b37a97750b9, spec.md 2c34cb4b9087a2e5d2039fb77d55ed4193d05b37, .specify/memory/constitution.md absent, design.md dde55371b7c3e381ab3168bc1b985f1b6d494c3d, docs/architecture/review-commands-from-trunk.md 1cdb799b8112426f7a42f55ca50124580960ff76, research.md 0bc34274db64362a7242f1084c31561ed45323bc, data-model.md cd84c395766b011b43082e64a7ed696f7e7be434, contracts/review-start-output.md b2ff8e36d80006ddbf581b44f4925db467fa26d8, quickstart.md 93ed542c8c48c1009c3aaa1e658f8f2b11995941
- Review type: full (no earlier report)
- Open: BLOCKER 1 · MAJOR 2 · MINOR 3 · Fixed since the earlier review: 0
- Detail: /Users/andremarin/Development/wfctl-specs/711-review-commands-from-trunk/plan-review.md

### Coverage

| Check | Status |
| --- | --- |
| Deterministic checks | Outstanding (PR-001, PR-002, PR-004) |
| Requirements and traceability | Outstanding (PR-001, PR-004) |
| Architecture and boundaries | Outstanding (PR-006) |
| Adversarial implementation and verification | Outstanding (PR-001, PR-002, PR-003, PR-005) |
| Security and reliability | Outstanding (PR-001) |

### Findings

- **PR-001, BLOCKER, open.** `spec.md` User Story 3, FR-004, and SC-003 plan a
  warning and a fallback for a trunk whose commands can't be used. Stands
  because `review start` reads the required groups through `required_at`
  first, which validates the trunk's `review.commands` and refuses a broken
  file, so the fallback can never run.
- **PR-002, MAJOR, open.** User Story 2 scenario 2 says the trunk's command
  still runs when the branch drops it. Stands because that's only reachable
  through a group the trunk lists and the branch removed, and the plan names
  no test setup for it.
- **PR-003, MAJOR, open.** The manual `review start` in the quickstart starts a
  real run on this branch. Stands because that run uses up one of the
  branch's three security rounds.
- **PR-004, MINOR, open.** `load_commands` "mirrors `load_rounds`". Stands
  because a branch with no `review.commands` would get None and no difference
  warning, against SC-002.
- **PR-005, MINOR, open.** After the fallback, every reviewer reads "no command
  in wfctl.json on origin/main", which is false for a trunk whose command is
  invalid. Stands because the plan doesn't say what the reason reads.
- **PR-006, MINOR, open.** The `fanning-out-code-review` skill and `AGENTS.md`
  describe `review.commands` as the repository's own copy. Stands because the
  plan doesn't update either.

## Review 2026-11-04T01:10Z

- Verdict: satisfied
- Reviewed: plan.md f0e372133f608fddc607420b3ae8ff489278da32, spec.md c9cbdd331fd7ca70f8f018ec0acea96274c011d1, .specify/memory/constitution.md absent, design.md 4c337fa6c3f2c8f22d4cc298157b5b6b1ff248a4, docs/architecture/review-commands-from-trunk.md 48c163fd01a4b78106429ff061c8d6d45133ce2f, research.md ebfe85e6616dcfdf7956b3c514c1f0067b8dc863, data-model.md 16a64bea06a4d2a174ce73938ff7b675c5f7cfc2, contracts/review-start-output.md ecce38f47a2081ace1c88f65ee89d23fd76af3b8, quickstart.md e0ac71744732637de876926543234e29b8e730cb, plan-review.plan.md f4788c839aa20270a92ce5a1d8b54b37a97750b9 (base)
- Review type: re-review (the plan copy matches the earlier review's plan; every changed input re-read in full)
- Open: BLOCKER 0 · MAJOR 1 · MINOR 3 · Fixed since the earlier review: 6
- Detail: /Users/andremarin/Development/wfctl-specs/711-review-commands-from-trunk/plan-review.md

### Coverage

| Check | Status |
| --- | --- |
| Deterministic checks | Clear |
| Requirements and traceability | Outstanding (PR-009, PR-010; PR-001 and PR-004 fixed) |
| Architecture and boundaries | Outstanding (PR-008; PR-006 fixed) |
| Adversarial implementation and verification | Outstanding (PR-007, PR-009; PR-002, PR-003, PR-005 fixed) |
| Security and reliability | Outstanding (PR-007) |

### Findings

- **PR-001, BLOCKER, fixed.** Fixed by spec User Story 3, FR-004, SC-003,
  research R4, and the design record, which keep today's refusal of a broken
  trunk file.
- **PR-002, MAJOR, fixed.** Fixed by spec User Story 2 scenario 2 and plan
  Tests item 3, which name a custom group only the trunk lists.
- **PR-003, MAJOR, fixed.** Fixed by the quickstart, which sets
  `WFCTL_STATE_DIR` to a scratch folder for the manual run.
- **PR-004, MINOR, fixed.** Fixed by plan `load_commands`, which returns `{}`
  for a missing file or key.
- **PR-005, MINOR, fixed.** Fixed by removing the fallback and naming the
  reason text when no ref is given.
- **PR-006, MINOR, fixed.** Fixed by the plan's docs section.
- **PR-007, MAJOR, open.** The difference warning prints every model key
  either side sets, and `_commands` checks only the values. Stands because a
  branch key holding a newline would print a line that reads as a roster
  entry.
- **PR-008, MINOR, open.** The skill and `AGENTS.md` say `✗ unavailable` means
  a program missing from `PATH`. Stands because a model with no command on the
  trunk is now a second cause, and the plan omits `install-skills` for the
  skill edit.
- **PR-009, MINOR, open.** No CLI test for an invalid trunk `review.commands`
  or a trunk naming Claude. Stands because the existing refusal test covers
  only invalid JSON.
- **PR-010, MINOR, open.** `plan.md` Project Structure and `design.md` Scope
  name fewer files than the plan changes. Stands because both lists predate
  the docs section.
