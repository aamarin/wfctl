# Plan Review Report

Review state: completed
Review type: re-review

## Reviewed inputs

| Artifact | Content identity | Role |
| --- | --- | --- |
| plan.md | 8db05c97b69f943604fccbde690846ba11d431af | technical strategy |
| spec.md | 5661b758047ee362034de67e76acb008576e25b1 | requirements |
| .specify/memory/constitution.md | absent | constitution |
| design.md | 53265dda3df5dfb6fe8e04a9938d1eeb0f391a40 | design-record index |
| docs/architecture/design/818-threat-baseline-layers-over-upstream.md | b3f40c18672eb328391539bb29d5a762b527970c | design record |
| docs/architecture/security-record-needs-baseline.md | 9358cdb91f85c7b92dd1e955e3c6825bdfafbf03 | level-2 record the plan names |
| docs/architecture/promised-evidence-blocks-on-silence.md | 706e289280ece13c1ae6d1ede7f9fd57074b01d8 | record the plan cites (R6) |
| research.md | 6e5d79cdb7eff74a0f9734e389fe8aebf4d56b64 | planning evidence |
| data-model.md | a3ccca58c2db9154f8faef992928f41545e25bf4 | planning evidence |
| contracts/threat-baseline-pass.md | 79dc0cb2a5c06224791a5487a6436dcc8b251820 | contract |
| quickstart.md | b012175ecfdfc6c9fadf563c75b6db75ae6867c8 | verification route |
| plan-review.plan.md | fe4fd15c29e548914c8e960d8688e9d8053f24ef | base of this re-review |

## Review scope

- Re-review: the earlier report exists, and the plan copy's identity equals
  its `plan.md` row (`fe4fd15c`)
- Changed in `plan.md` since the earlier report: §Summary items 1 to 4,
  §Technical Context (Performance Goals, Scale/Scope), §Constitution Check
  (validation and ownership lines), §Source Code (the `_evidence.py`, wrapper,
  `NOTICES.md`, `threat-baseline`, `design-levels` and test lines; the
  `status-payload.json` line removed), and §Order of work steps 1, 3 and 4.
  Reviewed together with the research, data-model and contract sections they
  point into
- Inputs that changed since the earlier report, each re-read in full with the
  whole plan reviewed against it: `spec.md` (FR-007a, FR-007b, FR-015
  extended, FR-015a, two edge cases), `research.md` (R1, R4, R5, R6, R8, R10),
  `data-model.md` (inputs and pass-state tables),
  `contracts/threat-baseline-pass.md` (remedy, git-failure row, payload note).
  `design.md`, both level-2 records, the level-3 record and `quickstart.md`
  match their earlier identities
- Lenses: requirements and traceability, architecture and boundaries,
  adversarial implementation and verification, plus verification, risk,
  dependency and scope from the rubric
- Conditional lenses: security and reliability applied. The pass is a check
  that stands between the agent and its own report that a baseline exists, the
  feature vendors executable third-party code with a pre-granted tool call, and
  the new skill commits a security-sensitive document
- Design records: 1 listed in design.md
  `docs/architecture/design/818-threat-baseline-layers-over-upstream.md`
- Constitution: absent at `.specify/memory/constitution.md`; the review went on
  without it
- Existing code inspected, to check the revision's claims:
  `wfctl/_paths.py` (`touched_on_this_branch` at 626, `trunk_branch`,
  `non_record_subtrees`, `records_on_this_branch`), `wfctl/_evidence.py`
  (`GIT_UNANSWERED_REASON`/`GIT_UNANSWERED_HELP` at 174-181,
  `DRAWINGS_UNCHECKED` at 198, `branch_records` at 1309,
  `fact_architecture_accepted` at 1358, `_architecture_answered`,
  `brainstorm_architecture`, `_judge_drawings`, `brainstorm_software_design`,
  `brainstorm`), `wfctl/_pipeline.py` (`_STEPS`, `_pass_states` at 521,
  `collect_warnings` at 974), `wfctl/contracts/status-payload.json`,
  `wfctl/agents/skills/NOTICES.md`, the `allowed-tools` lines of every shipped
  skill and command, and the tests `test_skill_attribution.py`,
  `test_declared.py`, `pipeline_payload_snapshot.json`,
  `test_pipeline_needs_person.py`, `test_threat_model_skills.py`
- Ran `git ls-tree --name-only HEAD -- <path>` for a missing path (exit 0,
  empty output), a present path (exit 0, name printed), in a repository with no
  commits (exit 128, `Not a valid object name HEAD`), and outside a repository
  (exit 128). R5's exit-code claims hold
- Upstream (`anthropics/defending-code-reference-harness@d3bea6b5`) was not
  fetched. Claims about upstream stay under Assumptions challenged
- Reviewers: the lenses above, run in sequence by one agent

## Summary

BLOCKER: 0
MAJOR: 0
MINOR: 6

No BLOCKER findings identified in this review. All six earlier MAJOR findings
are fixed, and so are two earlier MINOR findings: 8 fixed since the earlier
review. The reader now asks `touched_on_this_branch` first and reads `HEAD`
with `git ls-tree`, and both claims check out against the code and a run. The
skill's commit, its auto-approve source, the exception's ownership and the
`design-levels` ordering are each written into the spec and research.

Six MINOR findings stay open. Four were open before. PR-008 stays open because
the revision followed the earlier report's evidence, which was wrong about
`pipeline_payload_snapshot.json`, and the test that does pin the pass list is
still missing. Two are new. PR-013 is a narrow silent skip when the repository
has no trunk, and PR-014 is the new skill requirements, which no test pins.

## Findings

### PR-001: `git cat-file -e` exits 128 for an absent file, not 1

- Priority: MAJOR
- Category: Dependency / Feasibility
- Status: fixed
- Evidence:
  - `research.md §R5`: now `git ls-tree --name-only HEAD -- THREAT_MODEL.md`,
    run with `subprocess.run` in the reader; empty output is absent, a non-zero
    exit is git failing; a new `BASELINE_UNANSWERED_REASON`
  - Run here: a missing path exits 0 with no output, a present path prints the
    name, a repository with no commits and a non-repository both exit 128
  - `research.md §R6` row 8 now places the `spec.md` fold after the
    git-failure rows, as `brainstorm_software_design` does
- Finding: The earlier read mapped absence to git failure. The new read keeps
  the two apart, the reader runs its own subprocess as `_paths.py` does, and
  the git-failure state has its own reason and its own place in the order.
- Why it matters: FR-010's reason and FR-012a's warning now hold on the
  common state.
- Suggested response: Fixed by `research.md §R5` and `§R6`.
- Corroborated by: adversarial implementation, dependency and feasibility

### PR-002: The record listing reads git failure as "no record", so the pass skips silently

- Priority: MAJOR
- Category: Risk / Failure Mode
- Status: fixed
- Evidence:
  - `plan.md §Summary` item 1 and `research.md §R4`: the reader asks
    `touched_on_this_branch(repo_root, arch, exclude=non_record_subtrees(arch))`
    first and calls `branch_records` only on `True`
  - `wfctl/_evidence.py:1358`, `fact_architecture_accepted`: the same order,
    with `is_in_tree` ahead of it, which `research.md §R6` row 2 mirrors
  - `research.md §R6` row 3 and `data-model.md §Pass states`: `None` reads
    `in_progress` with `GIT_UNANSWERED_REASON` and `GIT_UNANSWERED_HELP`;
    row 4 shows `DRAWINGS_UNCHECKED` with no trunk
  - `plan.md §Source Code`: the state tests cover the git-failure and no-trunk
    rows
- Finding: The silent skip on git failure, and on no trunk with nothing
  uncommitted, is closed. A narrower case remains with no trunk and some
  uncommitted record, filed as PR-013.
- Why it matters: The check no longer lets a branch through on a failed read
  in the cases the earlier finding named.
- Suggested response: Fixed by `research.md §R4` and `§R6` rows 2 to 4.
- Corroborated by: security and reliability, adversarial implementation

### PR-003: The remedy tells an unattended agent how to exempt itself

- Priority: MAJOR
- Category: Boundary / Ownership Concern
- Status: fixed
- Evidence:
  - `spec.md §FR-007b`: the skill and wrapper tell the agent not to run
    `wfctl step none brainstorm.threat-baseline`, and no shipped skill grants it
  - `spec.md` edge case on auto-approve: the agent doesn't run `step none` on
    this pass
  - `contracts/threat-baseline-pass.md §wfctl status, paused`: the remedy
    says "This is the user's decision, not the agent's"
  - `research.md §R1` "The exception stays the user's"; `plan.md §Constitution
    Check` ownership line
  - Checked: the only shipped `step none` grants are
    `wfctl step none brainstorm.software-design *` in `speckit-brainstorm` and
    its command, and no skill grants `Bash(wfctl *)` or `wfctl step none *`
- Finding: The remedy, the skill and the wrapper now all mark the claim as the
  user's, and no grant covers it.
- Why it matters: The ownership rule in `security-record-needs-baseline.md` is
  now carried by the artifacts the agent reads, not only by the record.
- Suggested response: Fixed by FR-007b, R1 and the contract.
- Corroborated by: security and reliability, architecture and boundaries

### PR-004: Nothing says who commits `THREAT_MODEL.md`, with what grant, or how the skill reads auto-approve

- Priority: MAJOR
- Category: Missing Information
- Status: fixed
- Evidence:
  - `spec.md §FR-007a`: the skill ends by committing `THREAT_MODEL.md` and
    only that file
  - `research.md §R1` "How it ends": `git add THREAT_MODEL.md` and
    `git commit -m "<subject>" -- THREAT_MODEL.md`, with the grant
    `Bash(wfctl status*) Bash(git add THREAT_MODEL.md) Bash(git commit*)`
  - `research.md §R1` "Where the flag comes from": the top-level
    `auto_approve` key of `wfctl status --json`, which
    `wfctl/contracts/status-payload.json:9` and `wfctl/cli.py:857` carry
  - `data-model.md §Files the feature writes`: committed by the skill's last
    step
- Finding: The commit, its grant, its pathspec and the flag source are all
  named.
- Why it matters: Story 1 and Story 2 now connect, and the rerun loop the
  earlier finding described can't start from a missing commit.
- Suggested response: Fixed by FR-007a and `research.md §R1`.
- Corroborated by: adversarial implementation, requirements and traceability

### PR-005: The level-2 record has `design-levels` send the agent to `/threat-baseline` first; the spec and plan don't

- Priority: MAJOR
- Category: Architecture / Decision Conflict
- Status: fixed
- Evidence:
  - `spec.md §FR-015`: `design-levels` tells the agent to run
    `/threat-baseline` before writing the section when no baseline is
    committed, as the primary route, with the pass as the backstop
  - `spec.md §FR-015a` and `research.md §R1` "The per-control section
    afterwards": a section written before the forced baseline is re-read and
    updated
  - `plan.md §Summary` item 2, `§Source Code` (`design-levels/SKILL.md #
    security part names threat-baseline and runs it first`), `§Order of work`
    step 4
- Finding: The spec and plan now carry the record's instruction, and say what
  happens to a section written before a baseline the check forced.
- Why it matters: The ordering `security-record-needs-baseline.md` decided now
  holds in the spec.
- Suggested response: Fixed by FR-015, FR-015a and the plan's structure and
  order of work.
- Corroborated by: architecture and boundaries, requirements and traceability

### PR-006: The attribution test hard-codes MIT as every notice's licence

- Priority: MAJOR
- Category: Verification Gap
- Status: fixed
- Evidence:
  - `research.md §R8` "To fix in the test": four changes, `_ROW` accepting
    `_`, a licence per section read from the notice, an Apache-2.0 twin of
    `test_each_notice_carries_the_permission_text_it_claims_to` against
    `LICENSE-Apache-2.0`, and a `_lib/` claim pattern beside
    `_reference_claims`
  - `tests/test_skill_attribution.py`: `_ROW` at 63, `_sections` at 280-292,
    `_licence_the_notices_carry` at 367-378, `_reference_claims` at 188-199
    and the permission-text test at 480 all match R8's description
  - `plan.md §Source Code` and `§Order of work` step 1 name the four changes
- Finding: The plan now lists every change the test needs, keeps the
  line-to-notice agreement check, and adds the missing claim check for the
  helper's path. One small gap: R8.4 names only `NOTICES.md`'s opening, and
  line 59 ("Every upstream licence above is the MIT licence") needs the same
  change. An implementer will meet it while adding the section.
- Why it matters: Order-of-work step 1 no longer hits an unpredicted red suite.
- Suggested response: Fixed by `research.md §R8`.
- Corroborated by: verification, dependency and feasibility

### PR-007: FR-012a's warning appears only where `design.md` exists

- Priority: MINOR
- Category: Requirement / Plan Mismatch
- Status: fixed
- Evidence:
  - `research.md §R6` "Limit on row 8" and `data-model.md §Pass states` closing
    paragraph state the limit, citing `wfctl/_evidence.py:1762-1767` and the
    architecture pass's docstring
- Finding: The exception is now recorded beside the row it limits.
- Why it matters: A reader of the plan no longer expects a warning on a branch
  with no `design.md`.
- Suggested response: Fixed by `research.md §R6`.
- Corroborated by: single reviewer

### PR-008: The file list misses the tests that pin the brainstorm pass order

- Priority: MINOR
- Category: Verification Gap
- Status: open
- Evidence:
  - `plan.md §Source Code` now lists `test_declared.py` (25, 399, 406, which
    match) and `pipeline_payload_snapshot.json # brainstorm passes gain
    threat-baseline`; `§Technical Context` Scale/Scope and
    `contracts/threat-baseline-pass.md §wfctl status --json` repeat the
    snapshot claim
  - `tests/pipeline_payload_snapshot.json` holds step rows only (`annotation`,
    `name`, `reason`, `remedy`, `state`) and names no pass. The earlier report's
    evidence that it "carries the brainstorm passes" was wrong, and the revision
    followed it
  - `tests/test_pipeline_needs_person.py:210-214` asserts the whole
    `needs_person` map over every pass as a dict equality, including
    `"architecture": False, "software-design": False, "design-doc": False`, so
    a new built-in pass turns it red
- Finding: The plan names one test file that won't change and still misses one
  that will.
- Why it matters: It's mechanical, but the plan, the contract and the scope
  line all state a change that doesn't exist, and step 3's test fixes are one
  short.
- Suggested response: Replace the snapshot line with
  `test_pipeline_needs_person.py:211` in the plan, the Scale/Scope line and the
  contract's payload note.
- Corroborated by: single reviewer

### PR-009: The relative helper path misses upstream's grant on Claude too

- Priority: MINOR
- Category: Risk / Failure Mode
- Status: open
- Evidence:
  - `research.md §R2` unchanged: `python3 <folder this skill was loaded
    from>/../_lib/checkpoint.py`; Known cost scoped to "other agents"
  - `spec.md §SC-003`: the Claude layer runs the helper "on the first try"
- Finding: Loaded from `.claude/skills/threat-baseline/`, the instruction
  yields `.claude/skills/threat-baseline/../_lib/checkpoint.py`, which is not
  the string upstream's `allowed-tools` pre-grants, so Claude prompts too and
  an unattended bootstrap stalls. The revision didn't touch this.
- Why it matters: R2's known cost and SC-003 both understate what Claude will
  do.
- Suggested response: Tell the agent to use the normalized path, which is
  upstream's own path on Claude.
- Corroborated by: single reviewer

### PR-010: Two requirements are checked by hand only

- Priority: MINOR
- Category: Verification Gap
- Status: open
- Evidence:
  - `spec.md §FR-015` (now longer, with the run-first instruction) and User
    Story 3 AC2; `spec.md` User Story 2 AC1
  - `plan.md §Source Code`: no test for the `design-levels` lines beside
    `tests/test_threat_model_skills.py`, and no diff against `d3bea6b5` named
    as a verification step
- Finding: The `design-levels` lines, which now carry the primary route the
  record depends on, and the unedited-upstream claim still have no check that
  fails when a later edit drops them.
- Why it matters: FR-015's instruction is now the primary route, so losing it
  silently matters more than it did.
- Suggested response: Add a text test for the `design-levels` lines beside
  `test_threat_model_skills.py`, and name the diff against `d3bea6b5` as a
  verification step.
- Corroborated by: single reviewer

### PR-011: Committing the baseline publishes the attack-surface map

- Priority: MINOR
- Category: Assumption Challenge
- Status: open
- Evidence:
  - `spec.md §FR-007a` and `§FR-010`: the skill commits the baseline at the
    root, and the pass requires that
  - No change in the spec, research or the level-2 record mentions disclosure
    or a public repository
- Finding: Every adopting repository is still pushed to commit its threats and
  open gaps, and FR-007a now has the agent do it unattended. Nothing tells the
  user that a public repository may not want this.
- Why it matters: It's a security-relevant default the records never weighed.
- Suggested response: Add a line to the level-2 record or the
  `threat-baseline` skill on what to do when the repository is public.
- Corroborated by: security and reliability

### PR-012: The pass and the security reviewer find the section differently

- Priority: MINOR
- Category: Architecture / Decision Conflict
- Status: fixed
- Evidence:
  - `research.md §R4`: `^## Threat model` outside fenced code, the pattern
    `reviewing-security` greps for (`tests/test_threat_model_skills.py:71`,
    checked), with the one difference, fenced matches, stated and its cost named
  - `plan.md §Source Code`: the state tests include a fenced heading that
    doesn't count
- Finding: The two readers now share one rule, and the remaining difference is
  stated and tested.
- Why it matters: Settled.
- Suggested response: Fixed by `research.md §R4`.
- Corroborated by: single reviewer

### PR-013: With no trunk, a committed security record beside an uncommitted record skips silently

- Priority: MINOR
- Category: Risk / Failure Mode
- Status: open
- Evidence:
  - `wfctl/_paths.py:663-667`, `touched_on_this_branch`: returns `True` as soon
    as `git status` shows anything under the arch root, before it looks for a
    trunk
  - `wfctl/_paths.py`, `records_on_this_branch` (used by `branch_records`):
    with no trunk it lists only what `git status` reports
  - `research.md §R6` row 4 and `data-model.md §Pass states`: that empty
    listing reads `skipped` with `DRAWINGS_UNCHECKED` as a display line
  - `wfctl/_pipeline.py:974`, `collect_warnings`: a display string on a skipped
    pass is not a reason, so nothing warns and nothing holds
  - `wfctl/_evidence.py:1598-1662`, `_judge_drawings`: the pattern R6 copies
    finishes there only because `accept` refuses the drawing later; nothing
    later catches a missing baseline
  - `research.md §R6` rationale cites `promised-evidence-blocks-on-silence`
    for the other git-failure rows
- Finding: In a repository where `trunk_branch` finds nothing, a branch that
  committed its security record and has a second level-2 record still
  uncommitted reads `skipped`. The architecture pass is answered by the
  uncommitted record, so the cascade reaches this reader. The pass then
  can't see the committed record, and says so only on a skipped row.
- Why it matters: It's rare, because `trunk_branch` falls back to local
  `main`, `master` or `dev`. But it's the let-through the plan's own rows 3 and
  7 exist to prevent, and copying `_judge_drawings` brings over its display
  line without the later check that made the display line safe there.
- Suggested response: With no trunk, read row 4 as `in_progress` with
  `GIT_UNANSWERED_REASON` and `GIT_UNANSWERED_HELP` (the repository can fix it
  by naming its trunk), or state the case as an accepted limit beside R6 row
  4.
- Corroborated by: security and reliability, adversarial implementation

### PR-014: The new skill requirements have no check

- Priority: MINOR
- Category: Verification Gap
- Status: open
- Evidence:
  - `spec.md §FR-007a`, `§FR-007b`, `§FR-015a`: new MUSTs on the
    `threat-baseline` skill and wrapper
  - `spec.md §FR-007b`: "no shipped skill's `allowed-tools` grants that
    command", a property of every shipped frontmatter
  - `plan.md §Source Code` tests list: no test names these, and
    `tests/test_threat_model_skills.py` is the repository's pattern for pinning
    skill text
- Finding: The commit step, the do-not-run instruction and the re-read step are
  checked only by the one run in Order of work step 6. The `allowed-tools`
  half of FR-007b is mechanical, and nothing stops a later skill from granting
  `wfctl step none *`.
- Why it matters: FR-007b is what keeps the exception with the user, since
  `step none` has no check of its own. A broad grant added later would remove
  it with every test green.
- Suggested response: Add a test that no shipped `allowed-tools` grants a
  command matching `wfctl step none brainstorm.threat-baseline`, and text pins
  for the skill's commit, do-not-run and re-read lines.
- Corroborated by: verification, security and reliability

## Requirement-to-plan trace

| Requirement / criterion | Plan location | Review note |
| --- | --- | --- |
| FR-001 | plan.md §Project Structure; research R8 | covered; helper claim check added (PR-006 fixed) |
| FR-002 | research R2, R7 | covered |
| FR-003 | research R9 | covered |
| FR-004 | research R8 | covered |
| FR-005 | research R1 | covered |
| FR-005a | research R2 | covered; Claude grant mismatch (PR-009) |
| FR-006, FR-007 | spec-defined; plan.md §Project Structure | covered by reference to spec |
| FR-007a | research R1 "How it ends"; plan.md §Source Code | covered; no check (PR-014) |
| FR-007b | research R1; contract; plan.md §Constitution Check | covered; no check (PR-014) |
| FR-008 | research R4; plan.md §Project Structure | covered |
| FR-009 | research R4, R6 rows 3-4 | covered; no-trunk residual (PR-013) |
| FR-010 | research R5, R6 row 6 | covered |
| FR-011 | research R5 | covered |
| FR-012 | research R6 note; `_pass_states` verified | covered |
| FR-012a | research R6 row 8 and limit | covered |
| FR-013 | plan.md §Technical Context | covered |
| FR-014 | `_AUTOMATIC`, `needs_person` off; verified | covered |
| FR-015 | plan.md §Project Structure, §Order of work step 4 | covered; checked by hand (PR-010) |
| FR-015a | research R1 | covered; no check (PR-014) |
| FR-016 | research R10.3 | covered |
| FR-017 | research R10.2 | covered |
| FR-018 | research R10.1 | covered |
| FR-019 | plan.md §Order of work step 6 | covered |
| SC-001 | pass tests | covered; PR-013 residual |
| SC-002 | R6 row 4 | covered |
| SC-003 | quickstart step 1 | PR-009 |
| SC-004 | quickstart step 4 | manual only (PR-010) |
| SC-005 | Order of work step 6 | covered |

## Assumptions challenged

- Upstream's `SKILL.md` offers a `bootstrap-then-interview` mode (research R1).
  Not checked against upstream in this review.
- Upstream's `SKILL.md` frontmatter carries no key beyond `argument-hint` that
  `ALLOWED_KEYS` lacks, and each mode file's frontmatter, if any, parses as
  YAML. Not checked against upstream.
- Upstream's copyright line reads "2026 Anthropic PBC" (research R8). Not
  checked against upstream.
- `git commit -m … -- THREAT_MODEL.md` after `git add` commits only that path.
  That is git's default `--only` behavior for a pathspec. A rerun with an
  unchanged file makes `git commit` exit non-zero with "nothing to commit",
  which the skill should read as already committed. Not stated.
- `_lib` passes through install and doctor with no `SKILL.md`. Checked in part
  in the earlier review, and unchanged.

## Reviewer disagreement

- None identified.

## Strengths worth preserving

- The reader's order now matches `fact_architecture_accepted` step for step:
  arch root in the tree, then `touched_on_this_branch`, then `branch_records`.
  Each row of R6 names the existing function it copies.
- R5 records why `cat-file` was dropped, so a later reader doesn't swap it
  back.
- FR-007b names the missing check on `step none` as the reason the grant
  matters, which makes the ownership rule auditable instead of implied.

## Source freshness

This review describes only the content identities listed under
`## Reviewed inputs`. When `spec.md`, `plan.md`, a binding design record, or a
material planning artifact changes, this report no longer describes the current
plan, and a new review is needed before it counts as current evidence.
