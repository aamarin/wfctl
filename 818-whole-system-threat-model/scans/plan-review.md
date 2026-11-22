# Plan review scan for #818

## Review 2026-11-22T00:39Z

- Verdict: satisfied
- Reviewed: plan.md fe4fd15c29e548914c8e960d8688e9d8053f24ef, spec.md 5c96d2b8c2783c8decce7f936e16bfa71d1412ab, .specify/memory/constitution.md absent, design.md 53265dda3df5dfb6fe8e04a9938d1eeb0f391a40, docs/architecture/design/818-threat-baseline-layers-over-upstream.md b3f40c18672eb328391539bb29d5a762b527970c, docs/architecture/security-record-needs-baseline.md 9358cdb91f85c7b92dd1e955e3c6825bdfafbf03, docs/architecture/promised-evidence-blocks-on-silence.md 706e289280ece13c1ae6d1ede7f9fd57074b01d8, research.md 178d535e9c538f9689fee568af80768916e5ea51, data-model.md 75512f066cb183f4999f9f7b092203b2fba9ab3a, contracts/threat-baseline-pass.md 7c3e3126bd6146bfe4f62f433fec21bec57a97ec, quickstart.md b012175ecfdfc6c9fadf563c75b6db75ae6867c8
- Review type: full (no earlier report)
- Open: BLOCKER 0 · MAJOR 6 · MINOR 6 · Fixed since the earlier review: 0
- Detail: /Users/andremarin/Development/wfctl-specs/818-whole-system-threat-model/plan-review.md

### Coverage

| Check | Status |
| --- | --- |
| Deterministic checks | Outstanding (PR-001, PR-006) |
| Requirements and traceability | Outstanding (PR-004, PR-005, PR-007) |
| Architecture and boundaries | Outstanding (PR-003, PR-005, PR-008, PR-012) |
| Adversarial implementation and verification | Outstanding (PR-001, PR-002, PR-004, PR-006, PR-008, PR-009, PR-010) |
| Security and reliability | Outstanding (PR-002, PR-003, PR-011) |

### Findings

- **PR-001, MAJOR, open.** `git cat-file -e HEAD:<missing>` exits 128, not 1, so research R5 reads every missing baseline as "git couldn't answer" and R6 holds a branch past `spec.md`, against FR-010 and FR-012a. Stands because the plan's absent test is wrong.
- **PR-002, MAJOR, open.** `branch_records` returns `{}` when git can't be asked, the arch root is outside the tree, or there is no trunk, and the reader then reads `skipped` silently. Stands because the plan never calls `touched_on_this_branch` first, as the function's docstring requires.
- **PR-003, MAJOR, open.** The contract's remedy hands the agent `wfctl step none brainstorm.threat-baseline`, which has no check on who runs it. Stands because the record says the user decides and the plan never forbids the agent from taking it.
- **PR-004, MAJOR, open.** The pass reads done only on a commit, and no artifact says who commits `THREAT_MODEL.md`. Stands because an unattended run that writes without committing re-runs the bootstrap until the stall count stops it; where the skill reads auto-approve is also unstated.
- **PR-005, MAJOR, open.** `security-record-needs-baseline §Decision` has `design-levels` send the agent to `/threat-baseline` before the control's threat model. Stands because FR-015 and the plan only name the skill, so the baseline always comes after; part of the fix belongs in spec FR-015.
- **PR-006, MAJOR, open.** `test_skill_attribution.py` `_sections` gives every notice section LICENSE's MIT first line, so the Apache line fails, and a helper row in `_NOTICED_ROWS` goes unchecked since `_reference_claims` only matches `references/`. Stands because the plan counts the change as two edits.
- **PR-007, MINOR, open.** With `spec.md` and no `design.md`, brainstorm reads skipped and its passes inherit it, so FR-012a's warning never appears. Stands because the plan doesn't say so.
- **PR-008, MINOR, open.** `test_declared.py` and `pipeline_payload_snapshot.json` pin the brainstorm pass order and aren't listed; the `status-payload.json` line does nothing. Stands because "three test fixes" undercounts.
- **PR-009, MINOR, open.** The `../_lib/checkpoint.py` path from `.claude/skills/threat-baseline/` doesn't match upstream's `allowed-tools` grant, so Claude prompts too. Stands against SC-003 and R2's scoping of that cost.
- **PR-010, MINOR, open.** FR-015's `design-levels` lines and Story 2 AC1 are checked only by hand. Stands because no text test or diff against `d3bea6b5` is named.
- **PR-011, MINOR, open.** Committing `THREAT_MODEL.md` at the root publishes each adopting repo's threats and gaps. Stands because neither the records nor the plan weigh that.
- **PR-012, MINOR, open.** The plan matches a line equal to `## Threat model` while `reviewing-security` greps `'^## Threat model'`. Stands because they disagree on a suffixed heading, and both match inside a fenced example.

## Review 2026-11-22T02:07Z

- Verdict: satisfied
- Reviewed: plan.md 8db05c97b69f943604fccbde690846ba11d431af, spec.md 5661b758047ee362034de67e76acb008576e25b1, .specify/memory/constitution.md absent, design.md 53265dda3df5dfb6fe8e04a9938d1eeb0f391a40, docs/architecture/design/818-threat-baseline-layers-over-upstream.md b3f40c18672eb328391539bb29d5a762b527970c, docs/architecture/security-record-needs-baseline.md 9358cdb91f85c7b92dd1e955e3c6825bdfafbf03, docs/architecture/promised-evidence-blocks-on-silence.md 706e289280ece13c1ae6d1ede7f9fd57074b01d8, research.md 6e5d79cdb7eff74a0f9734e389fe8aebf4d56b64, data-model.md a3ccca58c2db9154f8faef992928f41545e25bf4, contracts/threat-baseline-pass.md 79dc0cb2a5c06224791a5487a6436dcc8b251820, quickstart.md b012175ecfdfc6c9fadf563c75b6db75ae6867c8, plan-review.plan.md fe4fd15c29e548914c8e960d8688e9d8053f24ef (base)
- Review type: re-review
- Open: BLOCKER 0 · MAJOR 0 · MINOR 6 · Fixed since the earlier review: 8
- Detail: /Users/andremarin/Development/wfctl-specs/818-whole-system-threat-model/plan-review.md

### Coverage

| Check | Status |
| --- | --- |
| Deterministic checks | Outstanding (PR-008) |
| Requirements and traceability | Resolved (PR-004, PR-007 fixed) |
| Architecture and boundaries | Resolved (PR-003, PR-005, PR-012 fixed) |
| Adversarial implementation and verification | Outstanding (PR-010, PR-014; PR-001, PR-006 fixed) |
| Security and reliability | Outstanding (PR-009, PR-011, PR-013; PR-002 fixed) |

### Findings

- **PR-001, MAJOR, fixed.** Fixed by research R5, which reads `HEAD` with `git ls-tree --name-only` and gives a failed read its own `BASELINE_UNANSWERED_REASON`; the four exit-code cases were run and match.
- **PR-002, MAJOR, fixed.** Fixed by research R4 and R6, which ask `touched_on_this_branch` before `branch_records` and hold on `None` with `GIT_UNANSWERED_REASON`.
- **PR-003, MAJOR, fixed.** Fixed by spec FR-007b, research R1, and the contract's remedy, which label `step none` as the user's; no shipped `allowed-tools` grants it.
- **PR-004, MAJOR, fixed.** Fixed by spec FR-007a and research R1: the skill commits `THREAT_MODEL.md` alone, names its grants, and reads `auto_approve` from `wfctl status --json`.
- **PR-005, MAJOR, fixed.** Fixed by spec FR-015, which has `design-levels` run `/threat-baseline` first, and FR-015a, which re-reads an earlier section against the baseline.
- **PR-006, MAJOR, fixed.** Fixed by research R8's four attribution-test changes. `NOTICES.md` line 59's "every upstream licence above is the MIT licence" still needs the edit R8.4 gives the opening.
- **PR-007, MINOR, fixed.** Fixed by research R6 and data-model.md, which state the no-`design.md` limit.
- **PR-012, MINOR, fixed.** Fixed by research R4, which uses the reviewer's `^## Threat model` pattern outside fenced code.
- **PR-008, MINOR, open.** `tests/pipeline_payload_snapshot.json` names no pass, while `tests/test_pipeline_needs_person.py:210-214` compares the whole `needs_person` map and isn't listed. Stands because plan.md, its scope line, and the contract still name the snapshot.
- **PR-009, MINOR, open.** On Claude, `.claude/skills/threat-baseline/../_lib/checkpoint.py` doesn't match upstream's pre-granted path, so Claude prompts too. Stands because research R2 is unchanged, against SC-003.
- **PR-010, MINOR, open.** The `design-levels` lines, now the primary route, and the unedited-upstream claim are checked by hand only. Stands because no text test or diff against `d3bea6b5` is named.
- **PR-011, MINOR, open.** Committing the baseline publishes a public repository's threat map, now unattended under FR-007a. Stands because nothing addresses disclosure.
- **PR-013, MINOR, open.** With no trunk, an uncommitted level-2 record makes `touched_on_this_branch` return `True` while `branch_records` misses a committed security record, so the pass skips with only a display line. Stands because nothing later catches a missing baseline, unlike the drawing check R6 copies.
- **PR-014, MINOR, open.** No test checks FR-007a, FR-007b, or FR-015a. Stands because a broad `allowed-tools` grant added later would break FR-007b with every test green.
