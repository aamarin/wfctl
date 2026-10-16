# Plan Review Report

Review state: completed
Review type: re-review

## Reviewed inputs

| Artifact | Content identity | Role |
| --- | --- | --- |
| plan.md | 9bf20cbebc542c98a5b97b3794a890e60fc954b4 | technical strategy |
| spec.md | 47b26330ea926fcf2134a58c56957bfa58227e51 | requirements |
| .specify/memory/constitution.md | absent | constitution |
| design.md | 1065767e733aafd03ad89a1c8c73d62f2c58e5e7 | design-record index |
| docs/architecture/change-carries-release-note.md | 419e739406b88b4464317bdbb59b6ab354d9e8dd | design record |
| docs/architecture/design/571-towncrier-builds-release-notes.md | ffc38879d9fa993f87ea60048dc03f5a26ec8f66 | design record |
| research.md | 4ca95fc46e15a7a21f264d8c7d8b0993ee39d873 | planning evidence |
| data-model.md | 68161af43203fc8eacd503de8546da62b1d1b0c5 | planning evidence |
| quickstart.md | 51babb8a75481b09b637476183c6b2a5d529a8b7 | planning evidence |
| contracts/check-release-note.md | cf1f4159814175f43f2c836b3cf4b9bc720a4121 | planning evidence |
| contracts/release-script.md | a51784706881e1fae355a98da35be57d19ed0039 | planning evidence |
| contracts/tag-job.md | 7eb6a965e935d3c18cd2d63864fcf4142567da52 | planning evidence |
| checklists/requirements.md | 37a6a5ce0798ad3e653a03b8fa785d1ce5f4ead5 | requirements-quality checklist |
| tests/test_install_config.py | 0281ffaa4b3ef803a73f1524c9a0271b26aac47d | existing code |
| tests/test_shape.py | 03b350995d6ec85773b0ae5cac37290b571011dd | existing code |
| tests/conftest.py | ab0a68e5a72288cdf034f54a415fbbc547c8d725 | existing code |
| .github/workflows/ci.yml | 51235f6139dda5761a8e3926b459e68b8ac4e205 | existing code |
| .github/pull_request_template.md | 3ee00e4a2b3a566b3a13b0de2e3f7c36e87851da | existing code |
| pyproject.toml | cf085a4ca57e179aa23e278d3ef3b7546a170e17 | existing code |
| wfctl.json | cd10684006bd8b3c52967743cd4e6e5a63a1a00e | existing code |
| wfctl/_verify.py | de7930cbba4cc9d9056a21009d5d0c2f70b8f270 | existing code |
| plan-review.plan.md | ddc76c17967f250d0d4c177a2b0a2625cf9b89d1 | base of this re-review |

## Review scope

- Re-review: the earlier report exists, and the plan copy's identity equals its
  `plan.md` row.
- Changed in `plan.md` since the earlier report: `§Changes from the spec`
  (seven merged pull requests, and the higher-version condition on a release
  branch), `§Implementation order` step 8 (four read-back commands), and
  `§Risks` (two new entries: a merge between the script and the release merge,
  and pull requests open when the ruleset is applied). Reviewed together with
  `§Ownership`, `§Constraints`, and `spec.md §FR-004`, `§FR-020`, and User
  Story 1 scenario 9, which the changed text refers to.
- Inputs that changed since the earlier report, each re-read in full with the
  whole plan reviewed against it: `spec.md`, `design.md`, `research.md`,
  `quickstart.md`, `contracts/check-release-note.md`,
  `contracts/release-script.md`, `contracts/tag-job.md`, and both design
  records. The invoking command named all of these as changed.
- Also changed by identity: `pyproject.toml`. It picked up the commits merged
  from `main` after the earlier review. `[project].version` is still 0.23.0 and
  the `dev` extra still has no towncrier, so no claim in the plan moves.
- Unchanged by identity: `data-model.md`, the checklist, and every other
  existing-code row. `data-model.md` was read again for this review.
- Lenses: requirements and traceability, architecture and boundaries,
  adversarial implementation and verification.
- Conditional lenses: security and reliability applied. The feature protects
  `main` with no bypass for anyone, the tag job publishes a public release and a
  tag every machine upgrades to, and the release script's failure path restores
  tracked files.
- Constitution: the repository has none at `.specify/memory/constitution.md`.
  The plan's gates come from the accepted records and AGENTS.md.
- Claims checked by running them, in a scratch repository: the rollback's
  `git restore --staged --worktree --source=HEAD -- pyproject.toml uv.lock
  changes/` once with a tracked note under `changes/` and once with none.
  Checked against the repository: `git log --merges --format=%s
  v0.23.0..origin/main` lists seven `Merge pull request` subjects, which matches
  the plan's count.
- Reviewers: the four lenses above, run in sequence by one agent with no part in
  writing the artifacts.

## Summary

BLOCKER: 0
MAJOR: 0
MINOR: 2

No BLOCKER findings identified in this review. Six findings the earlier report
left open are now fixed: PR-012, PR-014, PR-015, PR-016, PR-017, and PR-018.

The ruleset read-back now shows the bypass list through two further commands,
`design.md` agrees with the spec on the first release and on the settled
template question, the release commit stages the version bump and the lock file,
the test the plan describes asserts `--fill` and a one-commit branch, and the
script's closing lines say how to change the release text. The release branch
rule in the check, the contract, the research, the records, and the spec now
agree: the version must match the name and be higher than `main`'s. The ruleset's
`allowed_merge_methods` and the release commit message file carry through the
plan, the tag job contract, and the data model.

Two MINOR findings stand:

1. PR-019: the rollback's `git restore` names `changes/` even when step 4 was
   skipped, and git then restores nothing at all.
2. PR-020: `design.md` and `data-model.md` still describe the release branch rule
   without the higher-version condition, and the release script contract's
   example counts nine merges where the plan counts seven.

## Findings

### PR-001: An existing test holds the two pull request templates byte-identical, and the spec requires them to differ

- Priority: BLOCKER
- Category: Architecture / Decision Conflict
- Status: fixed
- Evidence:
  - `plan.md §Project Structure`: the drift test stays and compares
    `.github/pull_request_template.md` with the "Type of Change" section taken
    out of both copies, and a second test asserts the shipped copy still
    carries that section.
  - `plan.md §Implementation order` step 8 names the drift test and the
    `tests/test_shape.py` comment too.
- Finding: The plan says how the test changes and what it still guards.
- Why it matters: The definition of done stays reachable without dropping the
  guard against template drift.
- Suggested response: Fixed by `plan.md §Project Structure`.
- Corroborated by: architecture and boundaries

### PR-002: The tag job falls back to GitHub's generated notes, which the spec and the level 2 record both exclude

- Priority: MAJOR
- Category: Architecture / Decision Conflict
- Status: fixed
- Evidence:
  - `contracts/tag-job.md`: "There is no `--generate-notes` anywhere in the
    job", and an empty body fails before anything is tagged.
  - `research.md §8` and `spec.md §FR-016` agree.
- Finding: The fallback is gone from every artifact.
- Why it matters: The record and the plan agree about the boundary.
- Suggested response: Fixed by the 2026-10-15 revisions.
- Corroborated by: architecture and boundaries, requirements and traceability

### PR-003: The failure message for a branch with no issue gives no command that creates a note

- Priority: MINOR
- Category: Requirement / Plan Mismatch
- Status: fixed
- Evidence:
  - `contracts/check-release-note.md §Messages`: the "no release note on this
    branch" block ends with a `for example: uv run towncrier create
    +<what-changed>.fix.md --content "…"` line.
- Finding: Both "missing note" messages meet FR-007.
- Why it matters: Tests written from the contract pin a message that meets the
  requirement.
- Suggested response: Fixed by the contract.
- Corroborated by: requirements and traceability

### PR-004: The draft for User Story 2 scenario 8 is never empty, and the commit step may find no notes to remove

- Priority: MINOR
- Category: Risk / Failure Mode
- Status: fixed
- Evidence:
  - `research.md §5`: the script drops a line that reads exactly `No
    significant changes.`
  - `contracts/release-script.md §After both prompts` step 4: the removal is
    skipped when `changes/` holds no file.
- Finding: Both halves are specified and tested.
- Why it matters: towncrier's placeholder line can't reach a release page.
- Suggested response: Fixed by the research, the contract, and the plan. PR-019
  is a consequence of that skip.
- Corroborated by: adversarial implementation and verification

### PR-005: The towncrier title line the script drops depends on how towncrier is invoked, and the plan doesn't name the invocation

- Priority: MINOR
- Category: Dependency / Feasibility
- Status: fixed
- Evidence:
  - `research.md §5`: names `--config <repo>/pyproject.toml --dir <temporary
    copy>` and drops the first line starting with `# ` whatever follows it.
- Finding: The invocation is named, and the title match doesn't depend on it.
- Why it matters: The title can't leak into the release body.
- Suggested response: Fixed by `research.md §5`.
- Corroborated by: adversarial implementation and verification

### PR-006: The check reads `GITHUB_HEAD_REF` first, and the test suite runs in CI with it set

- Priority: MINOR
- Category: Verification Gap
- Status: fixed
- Evidence:
  - `research.md §3` and `§10`, and `plan.md §Implementation order` step 2: an
    empty `GITHUB_HEAD_REF` counts as unset, and an autouse fixture clears both
    variables.
- Finding: Every part of the original finding is answered.
- Why it matters: The check's tests give the same result locally and in CI.
- Suggested response: Fixed by the research and the plan.
- Corroborated by: adversarial implementation and verification

### PR-007: The tag job finds the release commit by a text pattern the same job's comment warns against

- Priority: MINOR
- Category: Risk / Failure Mode
- Status: fixed
- Evidence:
  - `contracts/tag-job.md` and `research.md §8`: the job finds the commit by
    its subject and confirms the version at that commit with `tomllib`.
- Finding: The `-G '^version = '` lookup is gone, and a wrong commit fails the
  job instead of publishing.
- Why it matters: The silent wrong-release path is closed.
- Suggested response: Fixed.
- Corroborated by: security and reliability

### PR-008: A squash or rebase merge is invisible to the "Merged with no release note" list

- Priority: MINOR
- Category: Assumption Challenge
- Status: fixed
- Evidence:
  - `spec.md §Assumptions`, `§FR-020`, and `research.md §7` and `§11`: the
    repository allows merge commits only once this feature merges. The ruleset
    now carries `allowed_merge_methods: ["merge"]` in the committed file, so the
    refusal is in the ruleset and not only in a repository setting.
- Finding: The assumption is stated and enforced by a rule a review can read.
- Why it matters: A squash merge can't go unlisted once the ruleset is applied.
- Suggested response: Fixed by FR-020.
- Corroborated by: requirements and traceability

### PR-009: The release script's stop and retry paths after the version prompt are undefined

- Priority: MINOR
- Category: Missing Information
- Status: fixed
- Evidence:
  - `contracts/release-script.md §Prompts` and `§Preconditions`: an editor that
    exits non-zero aborts, and a re-run after an unmerged release reaches the
    branch-exists refusal.
- Finding: The stop paths before the branch exists are defined, and the spec
  and the contract agree on the order.
- Why it matters: A plausible retry before the commit has a defined result.
- Suggested response: Fixed.
- Corroborated by: requirements and traceability

### PR-010: The tag job's lookup finds the release pull request's merge commit, so every release fails before it is tagged

- Priority: BLOCKER
- Category: Requirement / Plan Mismatch
- Status: fixed
- Evidence:
  - `contracts/tag-job.md` and `research.md §8`: the lookup is `git log -1
    --no-merges --format=%H --fixed-strings --grep "chore(release): cut $v"
    HEAD`, and the contract says why `--no-merges` is load-bearing.
  - Reproduced in the earlier review in a scratch repository: the lookup
    returns the release commit, not the merge, and `%b` returns the draft.
  - Unchanged by this round of edits: the lookup line in both artifacts is the
    same.
- Finding: The happy path of User Story 3 reaches the tag.
- Why it matters: Each release no longer lands its version bump on `main`
  without a tag.
- Suggested response: Fixed. A residual case is under Assumptions challenged.
- Corroborated by: adversarial implementation and verification, security and
  reliability

### PR-011: The release script's failure paths after it creates the branch leave the tree changed, and the retry command may point at a deleted draft

- Priority: MINOR
- Category: Risk / Failure Mode
- Status: fixed
- Evidence:
  - `contracts/release-script.md §After both prompts`: the rollback restores
    before it switches back to `main`, and step 7 is `gh pr create --base main
    --head release/v<version> --fill`, which needs no draft file.
  - gh v2.91.0 source, read in the earlier review: with one commit over the
    base, `--fill` takes the title from its subject and the body from its body.
- Finding: The rollback restores the tree, and the retry command is complete.
  The restore's pathspec has its own gap, PR-019.
- Why it matters: A failure partway through no longer leaves the bump on `main`.
- Suggested response: Fixed.
- Corroborated by: adversarial implementation and verification

### PR-012: The read-back command can't show the bypass list, and the contract says it can

- Priority: MINOR
- Category: Verification Gap
- Status: fixed
- Evidence:
  - `contracts/tag-job.md §Contract: .github/rulesets/main.json`: the read-back
    is now four commands. The second finds the ruleset id with `--jq '.[] |
    select(.name == "main") | .id'` and the third prints `rulesets/<id> --jq
    '.bypass_actors'`.
  - The contract's prose now says the second and third show the bypass list is
    `[]`, and that neither the plain `rulesets` listing nor
    `rules/branches/main` returns it. The earlier sentence implying the first
    command showed it is gone.
  - `quickstart.md §Protecting main` lists the same four, and `plan.md
    §Implementation order` step 8 says "the four that read the protection back,
    as `contracts/tag-job.md` lists them".
- Finding: The bypass list is readable, and the plan, quickstart, and contract
  agree on which commands read it.
- Why it matters: A ruleset applied with a bypass entry no longer passes the
  documented read-back.
- Suggested response: Fixed.
- Corroborated by: adversarial implementation and verification

### PR-013: Prose the change makes false is not in the plan's file list

- Priority: MINOR
- Category: Requirement / Plan Mismatch
- Status: fixed
- Evidence:
  - `design.md §Behaviour` matches the contracts for the version prompt, the
    category headings, and `towncrier create` with `--content`.
  - `plan.md §Project Structure` and `§Implementation order` step 8 list the
    comment above `_TEMPLATE` in `tests/test_shape.py`.
- Finding: Every string the earlier finding cited matches, and the test comment
  is in the plan.
- Why it matters: Whoever copies strings into AGENTS.md copies working ones.
- Suggested response: Fixed. PR-020 is a newer case of the same kind.
- Corroborated by: requirements and traceability

### PR-014: Two sentences in `design.md` still describe behaviour the spec has since changed

- Priority: MINOR
- Category: Requirement / Plan Mismatch
- Status: fixed
- Evidence:
  - `design.md §Behaviour` now reads "When `changes/` holds only `none` notes,
    or nothing, and every merge since the last tag added a note, the script says
    so and stops", followed by "A merge with no note keeps it going instead,
    with an empty draft for Andre to write". That is `spec.md §FR-014` and
    `contracts/release-script.md §Nothing to release`.
  - `design.md §Open Questions` now carries the template question as settled on
    2026-10-14, beside the 2026-10-15 pull request answer.
- Finding: Both sentences agree with the spec.
- Why it matters: Whoever writes AGENTS.md's Releasing section from `design.md`
  describes the first release correctly.
- Suggested response: Fixed.
- Corroborated by: requirements and traceability

### PR-015: The rollback's `git reset --hard` discards any tracked edit made after the preconditions passed

- Priority: MINOR
- Category: Risk / Failure Mode
- Status: fixed
- Evidence:
  - `contracts/release-script.md §After both prompts`: the rollback is now `git
    restore --staged --worktree --source=HEAD -- pyproject.toml uv.lock
    changes/`, and the contract says it names its paths rather than running
    `git reset --hard` because the editor session sits between the clean-tree
    check and the commit.
  - Run in a scratch repository with a tracked note: the restore exits 0 and
    `git status --porcelain` is empty.
- Finding: The rollback restores only the paths the script wrote, so an edit to
  another tracked file survives. The pathspec has a gap of its own, PR-019.
- Why it matters: A hand edit made while the editor is open is no longer lost.
- Suggested response: Fixed.
- Corroborated by: security and reliability

### PR-016: The contract's commit step doesn't stage the version bump or the lock file

- Priority: MINOR
- Category: Missing Information
- Status: fixed
- Evidence:
  - `contracts/release-script.md §After both prompts` step 5: "`git add
    pyproject.toml uv.lock`, then `git commit --cleanup=verbatim -F
    <message>`", and "The note deletions are already staged by step 4."
  - `spec.md §FR-012` and `data-model.md §Release commit` list the same parts.
- Finding: Followed as written, the commit holds the bump, the lock file, and
  the deletions.
- Why it matters: The release commit now carries what the tag job's `tomllib`
  check reads.
- Suggested response: Fixed.
- Corroborated by: adversarial implementation and verification

### PR-017: The test the plan describes can't observe the pull request's description

- Priority: MINOR
- Category: Verification Gap
- Status: fixed
- Evidence:
  - `spec.md §User Story 2` Independent Test now says to check that the script
    asked for the pull request with `--fill` on a branch holding only the
    release commit.
  - `research.md §10`: "the tests assert `--fill` and a branch holding one
    commit whose body is the draft", and names gh 2.91.0's source as the reason
    that is enough.
- Finding: The test that can be written is the one the spec and the research
  now name, and the gh assumption is stated.
- Why it matters: A second commit on the release branch is now something a test
  would notice.
- Suggested response: Fixed.
- Corroborated by: adversarial implementation and verification

### PR-018: Nothing says how Andre changes the wording once the release pull request is open

- Priority: MINOR
- Category: Boundary / Ownership Concern
- Status: fixed
- Evidence:
  - `contracts/release-script.md §The release text lives in the commit`: the
    description is a copy made once by `--fill`, the tag job publishes the
    commit's body, a change after the pull request opens is an amend and a
    force-push of `release/v<version>`, and the script's closing lines say so.
  - `data-model.md §Release pull request` still says the description is the
    commit's body, which agrees.
- Finding: The way to change the wording is stated, and the script prints it at
  the moment it is needed. `plan.md §Implementation order` step 8 does not name
  it for AGENTS.md, but the closing line covers the case the finding was about.
- Why it matters: The natural mistake, editing the description on GitHub, is
  warned against where Andre sees it.
- Suggested response: Fixed.
- Corroborated by: architecture and boundaries

### PR-019: The rollback's `git restore` fails outright when `changes/` holds no tracked file, and then restores nothing

- Priority: MINOR
- Category: Risk / Failure Mode
- Status: open
- Evidence:
  - `contracts/release-script.md §After both prompts` step 4: "The step is
    skipped when `changes/` holds no file." The rollback below it always names
    `changes/` in its pathspec.
  - Reproduced in a scratch repository: with no tracked file under `changes/`,
    `git restore --staged --worktree --source=HEAD -- pyproject.toml uv.lock
    changes/` prints `error: pathspec 'changes/' did not match any file(s) known
    to git`, exits 1, and leaves ` M pyproject.toml` and ` M uv.lock` in place.
    With a tracked note it exits 0 and the tree is clean.
- Finding: git checks every pathspec before it restores any, so one that matches
  nothing fails the whole command. In the case step 4 describes as skipped, a
  failure in steps 2, 3, or 5 leaves the version bump and the lock change in the
  tree, and the switch to `main` then carries them onto `main`.
- Why it matters: This is the state PR-011 closed, reopened for a narrower case.
  It needs a release where `changes/` holds no tracked file, which means every
  merge since the tag came with no note. After the first release that can't
  happen once `main` is protected, so it is MINOR.
- Suggested response: Name `changes/` in the restore only when step 4 ran, or
  restore with `git restore --staged --worktree --source=HEAD -- pyproject.toml
  uv.lock` and then `git checkout HEAD -- changes/` guarded by the same
  condition. Say so in the contract, and add a test that fails step 3 with
  `changes/` empty.
- Corroborated by: security and reliability

### PR-020: `design.md` and `data-model.md` still describe the release branch rule without the higher-version condition, and an example count disagrees with the plan

- Priority: MINOR
- Category: Requirement / Plan Mismatch
- Status: open
- Evidence:
  - `design.md §Behaviour`: the check "also passes a `release/v<version>` branch
    whose `pyproject.toml` carries that version". `spec.md §FR-004`,
    `contracts/check-release-note.md`, and both records say the version must
    also be higher than `main`'s.
  - `data-model.md §Release pull request`, checks row: "`release-note` passes
    because the branch's name matches its version". The same condition is
    missing there, and the case it was added for is a branch named for the
    current version.
  - `contracts/release-script.md §Nothing to release` example: "9 merges with
    no release note", while `plan.md §Changes from the spec` counts seven
    merged pull requests on 2026-10-16, which `git log --merges
    v0.23.0..origin/main` confirms. The example's list also ends in "..." after
    seven numbers.
- Finding: Two summaries lag the 2026-10-16 revision, and one illustrative
  number disagrees with the plan.
- Why it matters: Whoever writes AGENTS.md's Releasing section from `design.md`
  or the data model would say a branch named for its version needs no note,
  which is the hole the revision closed. The contracts and the spec agree, so an
  implementer is not misled.
- Suggested response: Add "and higher than `main`'s" to both sentences, and make
  the example's count and list agree with the plan or mark it as illustrative.
- Corroborated by: requirements and traceability

## Requirement-to-plan trace

| Requirement / criterion | Plan location | Review note |
| --- | --- | --- |
| FR-001 | research.md §3, contracts/check-release-note.md | covered |
| FR-002 | contracts/check-release-note.md §Messages | covered |
| FR-003 | data-model.md §Release note, contracts/check-release-note.md | covered |
| FR-003a | contracts/check-release-note.md §Messages | covered |
| FR-004 | research.md §3, contracts/check-release-note.md, plan.md §Changes from the spec | covered; PR-020 in design.md and data-model.md only |
| FR-005 | research.md §4, contracts/check-release-note.md §Category list | covered |
| FR-006 | research.md §2, contracts/tag-job.md §release-note job | covered |
| FR-007 | contracts/check-release-note.md §Messages | covered |
| FR-008 | data-model.md §Version proposal | covered |
| FR-009 | research.md §7, data-model.md §Merge | covered |
| FR-010 | research.md §4 and §5, data-model.md §Category | covered |
| FR-011 | contracts/release-script.md §Prompts | covered |
| FR-012 | contracts/release-script.md §After both prompts step 5 | covered |
| FR-013 | research.md §11, contracts/release-script.md §After both prompts | covered |
| FR-014 | contracts/release-script.md §Nothing to release | covered |
| FR-015 | contracts/release-script.md §Abort | covered |
| FR-016 | research.md §8, contracts/tag-job.md | covered |
| FR-017 | research.md §9 | covered |
| FR-018 | plan.md §Project Structure, §Implementation order step 8 | covered |
| FR-019 | plan.md §Project Structure (`changes/571.none.md`) | covered |
| FR-020 | research.md §11, contracts/tag-job.md §ruleset, quickstart.md, plan.md step 8 | covered |
| SC-001 | research.md §7, §11 | covered; see Assumptions challenged |
| SC-002 | quickstart.md §Cutting a release | covered |
| SC-003 | contracts/release-script.md step 3; `lint` is a required check | covered |
| SC-004 | contracts/tag-job.md | covered |
| SC-005 | plan.md §Constraints, §Structure Decision | covered |
| US1 scenarios 1 - 6, 8, 9 | plan.md §Implementation order step 2 | covered |
| US1 scenario 7 | plan.md §Risks | read in review, per spec §Validation Strategy |
| US2 scenarios 1 - 10 | plan.md §Implementation order step 5 | covered; PR-019 |
| US3 scenarios 1 - 4 | contracts/tag-job.md, plan.md §Risks | covered; confirmed on the first release, per spec |
| US4 scenarios 1 - 3 | plan.md §Project Structure, §Implementation order step 8 | covered |
| US5 scenarios 1 - 3 | contracts/tag-job.md §ruleset, quickstart.md | covered |

## Assumptions challenged

- The lookup's newest match is the release commit. With `--no-merges` that
  holds for the merge that releases. It fails on a later run when the release
  is still missing and a newer non-merge commit mentions `chore(release): cut
  $v` in its message. The failure is loud, needs the release to have failed
  once already, and is fixed by publishing by hand, so it is listed here rather
  than filed. Carried from the earlier review.
- A branch named `release/vX.Y.Z` that raises the version needs no note, so a
  change that is not a release could skip the note by bumping the version. The
  tag job would then find no release commit for that version and fail before
  tagging, so the cost is one hand-published release. The higher-version rule
  narrows what the earlier rule allowed, and one maintainer makes this unlikely.
- `gh pr create --fill` takes the description from a single commit's body.
  Verified from gh v2.91.0's source in the earlier review, and now named as the
  assumption in `research.md §10`. The contract states no minimum gh version.
- The ruleset's required check names match what GitHub reports, and
  `allowed_merge_methods` is accepted in a `pull_request` rule. The second was
  read from GitHub's REST documentation per `research.md §11` and not applied.
  The read-back commands are what confirm both.
- Pull requests open when the ruleset is applied need a new push before they
  can merge. Now stated in `plan.md §Risks` and the ruleset contract, so no
  longer an open gap.
- `spec.md §SC-001` says every pull request merged after protection carries a
  note "because GitHub refuses the merge otherwise". The ruleset covers `main`
  only, so a stacked child can still merge red into its parent's branch. Carried
  from the earlier review.
- The new risk entry on a merge between the script and the release merge matches
  the spec's edge case and the ruleset's lack of an up-to-date requirement.

## Reviewer disagreement

- None identified.

## Strengths worth preserving

- `contracts/tag-job.md` says in its own text why `--no-merges` is
  load-bearing, so a later edit that drops it has to delete the reason first.
- `contracts/release-script.md` says why the restore comes before the switch,
  why it names its paths, and why steps 6 and 7 leave the branch in place.
- The ruleset contract says where "merge commits only" is held in two places and
  what each one does, so a reader knows which one refuses and which one hides a
  button.
- `research.md §3` and the check's record text give the reason a release branch
  needs a higher version, not only the rule.
- `contracts/tag-job.md` runs every check before it creates the tag, so a
  failure leaves no half-published release.

## Source freshness

This review describes only the content identities listed under
`## Reviewed inputs`. When `spec.md`, `plan.md`, a binding design record, or a
material planning artifact changes, this report no longer describes the current
plan, and a new review is needed before it counts as current evidence.
