# Plan Review Report

Review state: completed
Review type: re-review

## Reviewed inputs

| Artifact | Content identity | Role |
| --- | --- | --- |
| plan.md | c35ab84d872a98701795267d0a00a1f91e5770a5 | technical strategy |
| spec.md | d01e78918246d887167bbd0a9b88586f100a6527 | requirements |
| .specify/memory/constitution.md | absent | constitution |
| design.md | 9794ff4227fc3be5e233071d203061432d050a19 | design-record index (no level-3 record listed) |
| research.md | 3227bc91fbd9b78d541598312ec7d3a23be26541 | planning evidence |
| data-model.md | 5a7f740a30d66172dd90aa5b0878c8107724c584 | planning evidence |
| contracts/cli.md | 6f8f915fe65be22ff509cf47bd65699e5e6fe59d | CLI contract |
| quickstart.md | 0fa327cc5522471467e79e2a7bc9aaa73f600bb3 | manual verification |
| checklists/requirements.md | d5925f3b1a84965cb1d73f8b712f6b1b75092da0 | requirements-quality checklist |
| docs/architecture/required-views-are-wfctls.md | 4b39a7b1988bba304dc97b460a90a060cf093afb | level-2 record, proposed and amended on this branch |
| docs/architecture/the-author-declares-the-diagram-kind.md | 0c32077ce31aca87ee00f777f0bc85728e5f413d | level-2 record, proposed, amended and reordered on this branch |
| docs/architecture/a-rule-is-expressed-as-a-check.md | 81e9a7d67301935f73a6e3b97c9b06284310879f | accepted record cited by the plan's gates |
| docs/architecture/branch-contexts-select-records.md | 06dd5c4d9c75c78add625ea1a7ec738b5b37c17c | accepted record the view filter follows |
| docs/architecture/domain/wfctl.md | 406e93843e422bdd70292396c90c315de0e09ed9 | domain page whose `Contexts` line drives component views |
| plan-review.plan.md | 32de5374d2cdc6288e6c5462adfcf13fd9872d5d | base of this re-review |

## Review scope

- Re-review: the plan copy's identity equals the earlier report's `plan.md` row.
- Changed in `plan.md`: the `vendor-upstream-skills` gate under `§Constitution Check`, the Structure Decision under `§Project Structure`, and the out-of-tree line in `§Validation Strategy` (`test_arch_views.py`). Reviewed together with `§Notes for tasks` items 5, 7 and 9, which those lines depend on.
- Changed inputs besides `plan.md`, each re-read in full with the whole of `plan.md` reviewed against it: `spec.md`, `research.md`, `data-model.md`, `contracts/cli.md`, and `quickstart.md`. Unchanged: `design.md`, `checklists/requirements.md`, the two proposed records, the two accepted records, and the domain page.
- New material reviewed in full: the third `unchecked` reason (`spec.md §FR-006a` and its edge case, `research.md §R-010` "When `git` fails", `data-model.md §Required view` freshness and rule 5, contract rules 6 and 7 and the new example line), and the quickstart's `covers`, arrow-label, and stale-mark checks.
- Lenses: deterministic checks; requirements and traceability; architecture and boundaries (with dependency and scope); adversarial implementation and verification (with risk and failure).
- Conditional lenses: security and reliability did not apply. The feature reads local markdown files and git history, prints paths, and adds acceptance refusals. The `git log` and `git rev-list` calls are read-only and take the `covers` paths after `--`. Nothing crosses a trust boundary, touches secrets, destroys data, or migrates state.
- Design records: none listed in `design.md §Software design decisions`. The two level-2 records the spec follows were read because the plan relies on them, and grepped for any statement about stale or unchecked views that the new text could contradict.
- Constitution: absent. The plan substitutes gates from `AGENTS.md` and accepted records, and says so under Complexity Tracking.
- Existing code inspected: `wfctl/_paths.py`, for how it runs `git` (every call passes `cwd=repo_root`). Git behavior checked directly in this worktree: `git log -1 --format=%H -- <absolute path outside the repository>` exits 128 with "is outside repository", and the same call on a gitignored path inside the tree exits 0 with empty output.
- Reviewers: the lenses above, run in sequence by one agent.

## Summary

BLOCKER: 0
MAJOR: 0
MINOR: 1

No BLOCKER findings identified in this review. The three findings the earlier report left open are fixed: the failed `git` call now has a named result in every file that describes freshness, the quickstart anticipates the stale mark and checks the two new template lines, and the plan counts four edited skills. One new MINOR finding: the docs list three `unchecked` reasons but never say which one wins when two apply, and the plan's out-of-tree test is worded as if the history reason always wins.

## Findings

### PR-001: The refusal shape in the contract is not the shape the spec requires

- Priority: MAJOR
- Category: Requirement / Plan Mismatch
- Status: fixed
- Evidence:
  - `spec.md §FR-013`: spells the shape, a `✗ <slug> <problem>.` line, then an indented `Fix:` line
  - `contracts/cli.md §wfctl arch accept`: prints each new refusal in that shape, and keeps the existing `cannot be accepted yet` block for the old blockers
  - `research.md §R-013`: states the split and why the old block stays (SC-004)
- Finding: The spec, contract, and research describe one layout for new refusals, and say how it sits beside the old block. Unchanged by this round's edits.
- Why it matters: Tests written from the contract satisfy FR-013 as worded.
- Suggested response: Fixed by `spec.md §FR-013`, `contracts/cli.md §wfctl arch accept`, and `research.md §R-013`.
- Corroborated by: deterministic checks, requirements and traceability

### PR-002: Two proposed records describe a different implementation than the plan

- Priority: MINOR
- Category: Architecture / Decision Conflict
- Status: fixed
- Evidence:
  - `the-author-declares-the-diagram-kind.md §Consequences`: says `Record` gains `kinds` and `Record.diagram` keeps the value as written, which is `research.md §R-004`
  - `required-views-are-wfctls.md §Consequences`: says a test checks the list against the view templates, which is `spec.md §FR-004` and `research.md §R-007`
- Finding: Both sentences match the plan. Neither record changed since the earlier review.
- Why it matters: The records put to the user describe the code that will ship.
- Suggested response: Fixed by the two amended `§Consequences` sections.
- Corroborated by: architecture and boundaries

### PR-003: Where a `### <kind>` drawing ends is undefined

- Priority: MAJOR
- Category: Missing Information
- Status: fixed
- Evidence:
  - `research.md §R-005` and `data-model.md §Drawing per kind`: the subsection ends at the next `###` or `##` heading of any text; `### Key` still ends the subsection above it; case is ignored; a fence above the first `###` heading in a multi-kind record belongs to no kind
  - `plan.md §Validation Strategy`, `test_arch_diagram_kinds.py`: tests each of those cases
- Finding: Every case is defined and has a test.
- Why it matters: Two implementers write the same scanner.
- Suggested response: Fixed by `research.md §R-005`, `data-model.md §Drawing per kind`, and the tests.
- Corroborated by: adversarial implementation and verification

### PR-004: The view filter diverges from the records filter it claims to match

- Priority: MINOR
- Category: Assumption Challenge
- Status: fixed
- Evidence:
  - `research.md §R-003`: "Where the two filters differ" names the outside-party case and why it's accepted
  - `research.md §R-002`: `contexts(arch)` returns an ordered, de-duplicated tuple, or `None`
  - `data-model.md §View listing`: the filter table names `Outside parties` explicitly
- Finding: The stated rationale matches the behavior, and the ordering contract rule 1 depends on is specified.
- Why it matters: Output order is stable.
- Suggested response: Fixed by `research.md §R-002` and `§R-003`.
- Corroborated by: adversarial implementation and verification

### PR-005: The SC-004 snapshot test pins records that will keep changing

- Priority: MINOR
- Category: Verification Gap
- Status: fixed
- Evidence:
  - `plan.md §Notes for tasks` item 2: fixture copies of every one-kind record at the branch's base, compared instead of the live folder
  - `plan.md §Validation Strategy`: "Every fixture copy of a one-kind record gives the acceptance result saved beside it (SC-004)"
- Finding: The test no longer binds future records, and SC-004 stays observable.
- Why it matters: The evidence for SC-004 survives later records branches.
- Suggested response: Fixed by `plan.md §Notes for tasks` item 2.
- Corroborated by: adversarial implementation and verification

### PR-006: The start-session skill still says the last lines are about records

- Priority: MINOR
- Category: Requirement / Plan Mismatch
- Status: fixed
- Evidence:
  - `plan.md §Project Structure`: lists `start-session/SKILL.md`, step 2
  - `plan.md §Notes for tasks` item 9: one sentence saying a missing, stale, or unchecked view is a reminder and never a refusal
- Finding: The skill the agent reads at session start is in scope, with the sentence it needs.
- Why it matters: User Story 2 reaches the agent through that skill.
- Suggested response: Fixed by `plan.md §Notes for tasks` item 9.
- Corroborated by: requirements and traceability

### PR-007: Doctor treats an unknown kind as an error, not the warning FR-015 asks for

- Priority: MINOR
- Category: Requirement / Plan Mismatch
- Status: fixed
- Evidence:
  - `spec.md §FR-015`: an unknown kind is the exception, an error on every status
  - `data-model.md §Drawing per kind` and `contracts/cli.md §wfctl doctor`: rules 1, 3, 4 and 5 warn, rule 2 stays an error
- Finding: The spec and the plan agree.
- Why it matters: A test written from FR-015 expects the behavior the plan builds.
- Suggested response: Fixed by `spec.md §FR-015`.
- Corroborated by: deterministic checks

### PR-008: View paths for an arch root outside the working tree are unspecified

- Priority: MINOR
- Category: Missing Information
- Status: fixed
- Evidence:
  - `research.md §R-009` and contract rule 4: view paths print through `_paths.arch_location`, relative in-tree and absolute outside
  - `contracts/cli.md §wfctl arch context`: the new example line prints an absolute path
  - `plan.md §Validation Strategy`: tests the absolute path
- Finding: The printed path is defined and tested.
- Why it matters: An out-of-tree arch root gets a usable path.
- Suggested response: Fixed by `research.md §R-009` and contract rule 4.
- Corroborated by: adversarial implementation and verification

### PR-009: The quickstart's accept rehearsal uses the risky flag order

- Priority: MINOR
- Category: Risk / Failure Mode
- Status: fixed
- Evidence:
  - `quickstart.md §3`: `uv run wfctl arch accept --dry-run -- <slug>`
- Finding: The rehearsal uses the form wfctl itself prints.
- Why it matters: A dropped flag no longer turns the rehearsal into a real acceptance.
- Suggested response: Fixed by `quickstart.md §3`.
- Corroborated by: adversarial implementation and verification

### PR-010: SC-005's one table needs more tables converted than the plan names

- Priority: MINOR
- Category: Requirement / Plan Mismatch
- Status: fixed
- Evidence:
  - `spec.md §FR-016` and `plan.md §Notes for tasks` item 3: name every template table other than Bounded Contexts for conversion
- Finding: A page filled from the converted template meets SC-005.
- Why it matters: SC-005 is reachable as planned.
- Suggested response: Fixed by `spec.md §FR-016` and `plan.md §Notes for tasks` item 3.
- Corroborated by: deterministic checks, requirements and traceability

### PR-011: The layout rule's exemption reasons from tooling, which the cited record says not to

- Priority: MINOR
- Category: Architecture / Decision Conflict
- Status: fixed
- Evidence:
  - `plan.md §Constitution Check`, `a-rule-is-expressed-as-a-check` gate: a broken layout rule or arrow label "is visible in the view, so each one is a check, and #743 builds it"
- Finding: The gate applies the record's own test and names the deferral as a known gap.
- Why it matters: The precedent the next plan copies reasons the way the record does.
- Suggested response: Fixed by the reworded gate.
- Corroborated by: architecture and boundaries

### PR-012: The stale check has no defined result when its `git` call fails

- Priority: MAJOR
- Category: Missing Information
- Status: fixed
- Evidence:
  - `spec.md §FR-006a`: marks a view unchecked when "wfctl can't read the view's git history", and the new edge case says an out-of-tree root's present views are unchecked "rather than current"
  - `research.md §R-010` "When `git` fails": either call exiting non-zero gives `not in this repository's history`, and says why reading it as "no commit yet" was turned down
  - `data-model.md §Required view`: a third freshness value, `unchecked (no history)`, and rule 5, freshness never changes the exit code
  - `contracts/cli.md §wfctl arch context` rules 6 and 7 and the new example line: "no commit yet" only when `git log` exits 0 with empty output; a non-zero exit prints `unchecked: <path> (not in this repository's history)` and exit stays 0
  - `plan.md §Validation Strategy`: the out-of-tree test now expects that line, not current, and checks the exit code
  - Checked here: `git log -1 --format=%H -- <absolute path outside the repository>`, run with `cwd` at the repository root as `_paths.py` runs every `git` call, exits 128. So rule 6's "exit 0 with empty output" can't fire for an out-of-tree root, and rule 7 does.
- Finding: Every file that describes freshness now names the failed-call result, and they agree in substance. `data-model.md` calls it `no history` where the contract prints `not in this repository's history`; the data model's labels are names rather than printed strings (its `missing path` label doesn't match its printed text either), and `plan.md §Notes for tasks` item 5 makes the contract's text the one tests compare.
- Why it matters: A view wfctl couldn't check no longer reads as current.
- Suggested response: Fixed by `research.md §R-010`, `data-model.md §Required view`, contract rules 6 and 7, `spec.md §FR-006a`, and the plan's test line.
- Corroborated by: adversarial implementation and verification, deterministic checks

### PR-013: The quickstart expects plain paths where the stale mark will often show

- Priority: MINOR
- Category: Verification Gap
- Status: fixed
- Evidence:
  - `quickstart.md §2`: says the container view prints `stale:` with the commit count if a commit to `wfctl/` landed after it was drawn, that this is the mark working, and how to see it clear
  - `quickstart.md §1` items 4 and 5: check the `covers` line (FR-003c) and the arrow-label request (FR-003b)
- Finding: The manual check anticipates the mark and covers both new template requirements.
- Why it matters: Whoever runs the quickstart can tell the mark from a defect.
- Suggested response: Fixed by `quickstart.md §1` and `§2`.
- Corroborated by: requirements and traceability

### PR-014: The plan's gate and structure text still count three edited skills

- Priority: MINOR
- Category: Requirement / Plan Mismatch
- Status: fixed
- Evidence:
  - `plan.md §Constitution Check`, `vendor-upstream-skills` gate: now lists `architecture-design`, `architecture-decisions`, `model-the-domain`, and `start-session`
  - `plan.md §Project Structure` Structure Decision: "guidance lands in four of wfctl's own skills"
- Finding: Both sentences match the tree, which edits four skills.
- Why it matters: The gate a reviewer reads lists every skill the plan edits.
- Suggested response: Fixed by the two edited sentences.
- Corroborated by: deterministic checks

### PR-015: Which `unchecked` reason prints when two apply is unspecified

- Priority: MINOR
- Category: Missing Information
- Status: open
- Evidence:
  - `data-model.md §Required view` `freshness`: three `unchecked` values, `no covers line`, `missing path`, and `no history`, with no order between them
  - `contracts/cli.md §wfctl arch context` rules 6 and 7: say when the history reason prints, not whether the covers checks run first
  - `research.md §R-010`: "An architecture root outside the working tree always takes this path"
  - `plan.md §Validation Strategy`: "each present view there prints as unchecked with `not in this repository's history`"
  - `plan.md §Notes for tasks` item 5: tests compare the contract's text exactly
- Finding: A view under an out-of-tree root can also have no `covers` line or name a missing path. The two covers checks need no `git` call, so an implementer will likely run them first, and that view then prints `(no covers line)`. That contradicts R-010's "always" and the plan's "each present view there". An implementer who runs `git` first prints the history reason instead. Both are `unchecked`, so no view reads as current either way, but the exact string a test pins differs.
- Why it matters: Two implementers can write different strings for the same view, and the plan's test sentence picks one without the data model saying so. Nothing behaves unsafely.
- Suggested response: State the order in `data-model.md §Required view`, for example covers line, then missing path, then history, and narrow R-010 and the plan's test line to an out-of-tree view whose `covers` line is valid. Or say the history check runs first.
- Corroborated by: adversarial implementation and verification

## Requirement-to-plan trace

| Requirement / criterion | Plan location | Review note |
| --- | --- | --- |
| FR-001 | plan.md §Project Structure `_views.py`; research.md §R-001, §R-002 | covered |
| FR-002 | data-model.md §Required view | covered |
| FR-003 | plan.md §Project Structure `architecture-design/views/`; research.md §R-007 | covered |
| FR-003a | plan.md §Project Structure; research.md §R-008; quickstart.md §1 | covered |
| FR-003b | research.md §R-011; plan.md §Validation Strategy; quickstart.md §1 item 5 | covered |
| FR-003c | data-model.md §Required view; plan.md §Validation Strategy; quickstart.md §1 item 4 | covered |
| FR-004 | plan.md §Validation Strategy `test_arch_views.py` | covered |
| FR-005 | contracts/cli.md §wfctl arch context; research.md §R-003, §R-009 | covered |
| FR-006 | contracts/cli.md §wfctl arch context | covered |
| FR-006a | research.md §R-010; data-model.md §Required view; contracts/cli.md rules 5 to 7; plan.md §Notes for tasks item 7, §Validation Strategy | covered; PR-015 |
| FR-007 | contracts/cli.md §No refusals from views, rule 3; data-model.md rule 5 | covered |
| FR-008 | plan.md §Notes for tasks item 1 | covered |
| FR-009 | research.md §R-004 | covered |
| FR-010 | research.md §R-005 | covered |
| FR-011 | research.md §R-005; data-model.md §Drawing per kind | covered |
| FR-012 | data-model.md §Drawing per kind; contracts/cli.md | covered |
| FR-013 | contracts/cli.md §wfctl arch accept; research.md §R-013 | covered |
| FR-014 | plan.md §Validation Strategy | covered |
| FR-015 | research.md §R-006; contracts/cli.md §wfctl doctor | covered |
| FR-016 | plan.md §Notes for tasks item 3 | covered |
| FR-017 | plan.md §Project Structure | covered |
| FR-017a | research.md §R-012; plan.md §Notes for tasks item 8; plan.md §Validation Strategy | covered |
| FR-018 | plan.md §Notes for tasks item 6 | covered |
| FR-019 | plan.md §Project Structure | covered |
| FR-020 | plan.md §Constitution Check | covered |
| SC-001 | quickstart.md §1 | covered |
| SC-002 | contracts/cli.md | covered |
| SC-003 | plan.md §Validation Strategy; quickstart.md §3 | covered |
| SC-004 | plan.md §Notes for tasks item 2 | covered |
| SC-005 | plan.md §Notes for tasks item 3 | covered |
| SC-006 | plan.md §Notes for tasks item 7; §Validation Strategy; quickstart.md §2 | covered |

## Assumptions challenged

- Rule 7 assumes `git` runs against the code's repository. No artifact says which directory the calls run in. The `covers` paths are relative to the repository root (FR-003c), and every `git` call in `_paths.py` passes `cwd=repo_root`, so the convention settles it. A call run from the view's own directory, with the arch root in another git repository, would succeed there and count against that repository's `HEAD`.
- An architecture root inside the working tree but gitignored, or a view a person never commits, makes `git log` exit 0 with empty output (checked here on a gitignored path). Rule 6 then prints a plain path indefinitely. The spec accepts this for a view "being drawn now", and wfctl's own root, `docs/architecture`, is committed, so it doesn't change the plan.
- A repository with no commit yet makes `git log` exit 128, so a view there prints as unchecked rather than as a plain path. The "no commit yet" test in `plan.md §Validation Strategy` needs an initial commit in its `tmp_path` repository to reach rule 6. Notes item 7 already builds commits before the view's, so this holds as planned.
- Rule 7 says "exits non-zero", and `data-model.md` names `git` not being installed. A missing `git` raises rather than exits, and a timeout, if the implementation sets one as `_paths.py` does, raises too. `data-model.md` says "a `git` call fails", which covers both, and rule 5 keeps the exit code at 0, so an implementer reads both as the history reason.
- R-010's range counts commits reachable from `HEAD` and not from the view's last commit. That is ancestry, not time, which is what FR-006a's "newer" has to mean on a branch.
- In a shallow clone, `git log -1 -- <view>` can return the shallow boundary commit, and the count reads 0. `arch context` runs at local session start, where clones are full.
- wfctl's own container view covers `wfctl/`, so nearly every code commit marks it stale until the view is touched again. The spec, the record, and now `quickstart.md §2` accept this.
- `start-session` isn't named in `vendor-upstream-skills.md`, so editing it is allowed.

## Reviewer disagreement

- None identified.

## Strengths worth preserving

- `research.md §R-010` names why a failed call isn't read as "no commit yet": the view would print as current forever when wfctl never checked it.
- `contracts/cli.md` rule 6 defines "no commit yet" by both the exit code and the output, so rule 7's failure path can't be mistaken for it.
- `plan.md §Notes for tasks` item 7 builds stale-view tests on a real git repository, because a mocked `git` would pass whatever range the code builds.
- `research.md §R-005` explains why a subsection ends at any `###` heading by naming the swap the record says the headings exist to catch.
- `research.md §R-013` keeps the old blockers in their existing block, so SC-004 holds by construction.

## Source freshness

This review describes only the content identities listed under
`## Reviewed inputs`. When `spec.md`, `plan.md`, a binding design record, or a
material planning artifact changes, this report no longer describes the current
plan, and a new review is needed before it counts as current evidence.
