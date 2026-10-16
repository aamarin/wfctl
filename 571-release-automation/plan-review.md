# Plan Review Report

Review state: completed
Review type: re-review

## Reviewed inputs

| Artifact | Content identity | Role |
| --- | --- | --- |
| plan.md | ddc76c17967f250d0d4c177a2b0a2625cf9b89d1 | technical strategy |
| spec.md | 738eb0621931bebe3ae55df908a0b4e9e6782162 | requirements |
| .specify/memory/constitution.md | absent | constitution |
| design.md | 68832bf405fbe2471adc03f621b75bd21ba491d8 | design-record index |
| docs/architecture/change-carries-release-note.md | a6639f9c4e0ef6d32a025627a0588bf233360759 | design record |
| docs/architecture/design/571-towncrier-builds-release-notes.md | 95807a531a9fda579d0bd27199c98ce60de20737 | design record |
| research.md | ee5294ee8b5898783b682e945e1b77e1d3a31965 | planning evidence |
| data-model.md | 68161af43203fc8eacd503de8546da62b1d1b0c5 | planning evidence |
| quickstart.md | c13b1013394ce9e040230843627a574fda2d6506 | planning evidence |
| contracts/check-release-note.md | e926253856385be12d60099c7c310d17c1170fa7 | planning evidence |
| contracts/release-script.md | 823581eea53f1dc86afbcb5bb047305ad62d0ad9 | planning evidence |
| contracts/tag-job.md | aa263d8ca77aaac38b4038671556d92f0c4fc6f5 | planning evidence |
| checklists/requirements.md | 37a6a5ce0798ad3e653a03b8fa785d1ce5f4ead5 | requirements-quality checklist |
| tests/test_install_config.py | 0281ffaa4b3ef803a73f1524c9a0271b26aac47d | existing code |
| tests/test_shape.py | 03b350995d6ec85773b0ae5cac37290b571011dd | existing code |
| tests/conftest.py | ab0a68e5a72288cdf034f54a415fbbc547c8d725 | existing code |
| .github/workflows/ci.yml | 51235f6139dda5761a8e3926b459e68b8ac4e205 | existing code |
| .github/pull_request_template.md | 3ee00e4a2b3a566b3a13b0de2e3f7c36e87851da | existing code |
| pyproject.toml | 0529147d3b9406b2c56277e4570a6556440d949f | existing code |
| wfctl.json | cd10684006bd8b3c52967743cd4e6e5a63a1a00e | existing code |
| wfctl/_verify.py | de7930cbba4cc9d9056a21009d5d0c2f70b8f270 | existing code |
| plan-review.plan.md | 2b629c7d579c5b7a62ea4cdbbfd69f15f47fd914 | base of this re-review |

## Review scope

- Re-review: the earlier report exists, and the plan copy's identity equals its
  `plan.md` row.
- Changed in `plan.md` since the earlier report: `§Project Structure` adds
  `tests/test_shape.py`, and `§Implementation order` step 8 names the
  `_TEMPLATE` comment and "the two that read the protection back". Reviewed
  together with `§Risks`, which names the read-back as the test of the ruleset,
  and `§Ownership`, whose release-text row the new `--fill` step touches.
- Inputs that changed since the earlier report, each re-read in full with the
  whole plan reviewed against it: `design.md`, `research.md`, `quickstart.md`,
  `contracts/release-script.md`, and `contracts/tag-job.md`. These were also
  named as changed by the invoking command, together with `plan.md`.
- Unchanged since the earlier report, compared by identity: `spec.md`, both
  design records, `data-model.md`, `contracts/check-release-note.md`, the
  checklist, and every existing-code row. `spec.md`, `data-model.md`, and
  `contracts/check-release-note.md` were read again for this review, and so were
  the tag job in `ci.yml` and the `_TEMPLATE` comment in `tests/test_shape.py`.
  The checklist, the two design records, `tests/conftest.py`,
  `wfctl/_verify.py`, and the other existing-code rows were compared by
  identity only.
- Lenses: requirements and traceability, architecture and boundaries,
  adversarial implementation and verification.
- Conditional lenses: security and reliability applied. The feature protects
  `main` with no bypass for anyone, the tag job publishes a public release and a
  tag that every machine upgrades to, and the release script's failure path now
  runs `git reset --hard`.
- Constitution: the repository has none at `.specify/memory/constitution.md`.
  The plan's gates come from the accepted records and AGENTS.md.
- Claims checked by running them, in a scratch repository: the tag job's lookup
  with `--no-merges` against a merge commit shaped like GitHub's, the release
  script's rollback after steps 1 to 4, the same rollback with a tracked file
  edited after the preconditions passed, and the contract's steps 2 to 5 typed
  as written. `gh pr create --fill` was checked by reading `initDefaultTitleBody`
  and `Client.Commits` in the source of gh v2.91.0, the version installed here.
  A read-only `gh api repos/astral-sh/ruff/rules/branches/main` showed what the
  new read-back command returns.
- Reviewers: the four lenses above, run in sequence by one agent with no part in
  writing the artifacts.

## Summary

BLOCKER: 0
MAJOR: 0
MINOR: 6

No BLOCKER findings identified in this review. PR-010, PR-011, and PR-013 are
fixed, so every finding the earlier report left open is now fixed except
PR-012, which is narrowed.

The tag job's lookup now skips merge commits, and the scratch run finds the
release commit, passes the subject and version checks, and reads the body. The
release script's rollback now resets before it switches, and the scratch run
leaves `main` clean. The retry command for the pull request no longer needs the
draft file, and gh's source confirms that `--fill` takes the description from a
single commit's body.

The six MINOR findings are bounded and force no architectural choice:

1. PR-012: the new read-back still can't show the bypass list.
2. PR-014: two sentences in `design.md` that the spec now contradicts.
3. PR-015: the rollback's `git reset --hard` discards any tracked edit made
   while the editor was open, which the contract says can't happen.
4. PR-016: the contract's commit step doesn't stage the version bump and the
   lock file.
5. PR-017: the test the plan describes can't observe the pull request's
   description.
6. PR-018: nothing says how Andre changes the wording once the pull request is
   open, and an edit to its description on GitHub never reaches the release.

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
  - `plan.md §Implementation order` step 8 names the drift test and now the
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
- Suggested response: Fixed by the research, the contract, and the plan.
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
    repository allows merge commits only once this feature merges.
- Finding: The assumption is stated and enforced by a setting.
- Why it matters: A squash merge can't go unlisted once the setting is applied.
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
  - `contracts/tag-job.md`: the lookup is now `git log -1 --no-merges
    --format=%H --fixed-strings --grep "chore(release): cut $v" HEAD`, and a
    paragraph says why `--no-merges` is load-bearing. `research.md §8` says the
    same.
  - Reproduced in a scratch repository: a release branch with one commit,
    merged with the subject `Merge pull request #600 from
    aamarin/release/v0.24.0` and the body `chore(release): cut 0.24.0`. The
    lookup returns the release commit, the subject check passes, `tomllib`
    reads `0.24.0` at that commit, and `%b` returns the draft.
  - `.github/workflows/ci.yml`: the tag job checks out with `fetch-depth: 0`,
    so the release commit is in the history the lookup walks.
- Finding: The happy path of User Story 3 now reaches the tag.
- Why it matters: Each release no longer lands its version bump on `main`
  without a tag.
- Suggested response: Fixed by the contract and the research. A residual case
  is under Assumptions challenged.
- Corroborated by: adversarial implementation and verification, security and
  reliability

### PR-011: The release script's failure paths after it creates the branch leave the tree changed, and the retry command may point at a deleted draft

- Priority: MINOR
- Category: Risk / Failure Mode
- Status: fixed
- Evidence:
  - `contracts/release-script.md §After both prompts`: when a step from 1 to 5
    fails, the script runs `git reset --hard` on the release branch, then
    switches back to `main` and deletes the branch.
  - Reproduced in a scratch repository: after the version bump, a changed lock
    file, and a staged note deletion, the reset, switch, and `git branch -D`
    leave `git status --porcelain` empty and `main` as the only branch.
  - Step 7 is now `gh pr create --base main --head release/v<version>
    --fill`, and the retry prints that same command, which needs no draft file.
  - gh v2.91.0, `pkg/cmd/pr/create/create.go` `initDefaultTitleBody`: when
    `Commits(BaseTrackingBranch, head)` returns one commit, the title is its
    subject and the body is its body. `git/client.go` `Commits` runs `git log
    --pretty=format:%H%x00%s%x00%b%x00 --cherry <origin/main>...<head>`, so
    the body arrives whole, and `--cherry` keeps only the head side's commits
    even if `origin/main` moves before a retry.
- Finding: The rollback restores the tree, and the retry command is complete.
- Why it matters: A failure partway through no longer leaves the bump on `main`.
- Suggested response: Fixed. The reset's own reach is PR-015.
- Corroborated by: adversarial implementation and verification

### PR-012: The read-back command can't show the bypass list, and the contract says it can

- Priority: MINOR
- Category: Verification Gap
- Status: open
- Evidence:
  - `spec.md §User Story 5` Independent Test: confirm the required checks,
    that administrators are included, and that the repository allows merge
    commits only.
  - `contracts/tag-job.md` and `quickstart.md §Protecting main`: the read-back
    is now `gh api repos/{owner}/{repo}/rules/branches/main` and a `--jq` of
    the three merge settings. The contract adds: "The plain `rulesets` listing
    isn't enough, since it names each ruleset without its rules or bypass
    actors."
  - `gh api repos/astral-sh/ruff/rules/branches/main` returns each rule's
    `type`, `parameters`, `ruleset_source`, and `ruleset_id`. It carries no
    `bypass_actors` field, and it lists only rules in force, so it doesn't say
    whether a ruleset is active or in evaluate mode either.
- Finding: The required checks and the merge setting are now readable, which
  answers two thirds of the earlier finding. The third, that nobody can
  bypass, is still invisible to both commands. The contract's sentence implies
  the replacement shows the bypass actors, and it doesn't.
- Why it matters: A ruleset applied with a bypass entry, for example after a
  later `PUT` from an edited file, passes the documented read-back. That is
  the one setting FR-020 exists to keep out.
- Suggested response: Add `gh api repos/{owner}/{repo}/rulesets/<id> --jq
  '{enforcement, bypass_actors}'`, taking the id from the `ruleset_id` the first
  command prints, and correct the contract's sentence.
- Corroborated by: adversarial implementation and verification

### PR-013: Prose the change makes false is not in the plan's file list

- Priority: MINOR
- Category: Requirement / Plan Mismatch
- Status: fixed
- Evidence:
  - `design.md §Behaviour` now says the check passes a `release/v<version>`
    branch whose version matches, asks for the version before the draft, shows
    `##` category headings with no title, and gives `towncrier create` with
    `--content`.
  - `plan.md §Project Structure` and `§Implementation order` step 8 now list
    the comment above `_TEMPLATE` in `tests/test_shape.py`, which reads "the
    two are held byte-identical by `test_install_config`".
- Finding: Every string the earlier finding cited now matches the contracts,
  and the test comment is in the plan.
- Why it matters: Whoever copies strings into AGENTS.md copies working ones.
- Suggested response: Fixed. Two other sentences in `design.md` are PR-014.
- Corroborated by: requirements and traceability

### PR-014: Two sentences in `design.md` still describe behaviour the spec has since changed

- Priority: MINOR
- Category: Requirement / Plan Mismatch
- Status: open
- Evidence:
  - `design.md §Behaviour`: "When `changes/` holds only `none` notes, or
    nothing, the script says so and stops". `spec.md §FR-014` and User Story 2
    scenario 8 say that with no notes and a merge that added none, the script
    lists the merges, proposes a patch, and opens the draft.
    `contracts/release-script.md §Nothing to release` agrees with the spec.
  - `design.md §Open Questions`: "Whether the PR template's 'Type of Change'
    checkboxes are removed or kept beside the note's category. This has to be
    settled". `spec.md §Clarifications` 2026-10-14 settled it, and `§FR-018`
    and the plan carry the answer.
- Finding: Both sentences predate the spec's answers. The first is the case the
  first release after this feature will hit, since every merge since v0.23.0
  predates the check.
- Why it matters: The contract and the spec agree, so an implementer is not
  misled. A reader who takes `design.md` as the summary, such as whoever writes
  AGENTS.md's Releasing section, would describe the first release wrongly.
- Suggested response: Add "and every merge since the last tag added a note" to
  the first sentence, and move the open question under the settled one.
- Corroborated by: requirements and traceability

### PR-015: The rollback's `git reset --hard` discards any tracked edit made after the preconditions passed

- Priority: MINOR
- Category: Risk / Failure Mode
- Status: open
- Evidence:
  - `contracts/release-script.md §After both prompts`: "The preconditions
    required a clean tree, so the reset discards only what the script itself
    wrote."
  - `contracts/release-script.md §Preconditions` and `§Prompts`: the clean-tree
    check runs at the start, and the version prompt and the editor session come
    after it. The editor works on a temporary file outside the repository, and
    the contract doesn't check the tree again before step 1.
  - Reproduced in a scratch repository: a line appended to the tracked
    `uv.lock` after the clean check, followed by the step 1 to 4 rollback,
    leaves `uv.lock` as it was committed, and the appended line is gone.
- Finding: The sentence holds only if nothing writes to a tracked file between
  the clean check and a failure in steps 1 to 5. That window includes an
  editor session of any length, in the checkout Andre releases from.
- Why it matters: A hand edit in that window is lost with no message, and git
  has no record of it to restore. It needs a coincidence to happen, which is
  why this is MINOR.
- Suggested response: Check the tree is clean again just before step 1, or
  restore only the paths the script writes, with `git restore --staged
  --worktree pyproject.toml uv.lock changes/`. Then the sentence can stay as
  written.
- Corroborated by: security and reliability

### PR-016: The contract's commit step doesn't stage the version bump or the lock file

- Priority: MINOR
- Category: Missing Information
- Status: open
- Evidence:
  - `contracts/release-script.md §After both prompts`: step 2 sets the version
    line, step 3 runs `uv lock`, step 4 runs `git rm`, and step 5 runs `git
    commit --cleanup=verbatim -F <draft>`. No step runs `git add` and step 5
    has no `-a`.
  - Reproduced in a scratch repository: those four steps as written make a
    commit holding only the note deletions, and leave ` M pyproject.toml` and
    ` M uv.lock` in the tree.
  - `spec.md §FR-012` and `data-model.md §Release commit`: the commit carries
    the new version and the relocked `uv.lock`.
- Finding: An implementer who follows the contract literally makes a release
  commit without the bump.
- Why it matters: The test the spec describes for User Story 2 checks the
  pushed branch's `pyproject.toml` and `uv.lock`, so it would catch this, and
  the tag job's `tomllib` check would refuse the commit. It is bounded, and the
  fix is one line in the contract.
- Suggested response: Add `git add pyproject.toml uv.lock` to step 4 or 5.
- Corroborated by: adversarial implementation and verification

### PR-017: The test the plan describes can't observe the pull request's description

- Priority: MINOR
- Category: Verification Gap
- Status: open
- Evidence:
  - `spec.md §User Story 2` Independent Test: "Check that the pull request it
    asked for carries the same draft as its description." `spec.md §FR-013`:
    the pull request's description is the confirmed draft.
  - `research.md §10`: tests replace `gh pr create` with a stub that records
    its arguments.
  - `contracts/release-script.md` step 7: the arguments are now `--base main
    --head release/v<version> --fill`, so the draft is not among them.
- Finding: Under the new step, the description comes from gh, not from the
  script. A stub that records arguments sees `--fill` and nothing else, so the
  check the spec names can't be written as described. What makes the
  description equal the draft is gh's one-commit rule, which this review
  confirmed from gh's source but which no test in the plan exercises.
- Why it matters: A second commit on the release branch, for example a
  fix-up, would make gh title the pull request after the branch and list
  commit subjects as the description, and no test would notice.
- Suggested response: State in `plan.md §Implementation order` step 5 what the
  test asserts in place of the description: that the pushed branch holds
  exactly one commit over `origin/main`, whose body equals the draft, and that
  the stub received `--fill`. Name gh's one-commit behaviour as the assumption
  that makes this enough.
- Corroborated by: adversarial implementation and verification

### PR-018: Nothing says how Andre changes the wording once the release pull request is open

- Priority: MINOR
- Category: Boundary / Ownership Concern
- Status: open
- Evidence:
  - `contracts/release-script.md §Prompts`: "The draft is not the last gate:
    the pull request it becomes is read again before Andre merges it."
  - `plan.md §Ownership`: what the GitHub release says is the release commit's
    body, read by the tag job. `data-model.md §Release pull request`: the
    description is a copy of that body.
  - `spec.md §User Story 3` scenario 1: "a release pull request with an edited
    body merges", and the release equals the release commit's body.
  - `design.md §Not Doing` leaves out a `CHANGELOG.md` because "a second copy
    edited separately would drift from it".
- Finding: The pull request's description is a second copy of the release
  text, and GitHub lets Andre edit it directly. An edit there never reaches the
  release, since the tag job reads the commit. The plan names reading the pull
  request as a gate, and says nothing about how a wording change found there
  is made, which is to amend the release commit and force-push the release
  branch. Neither the plan nor step 8's AGENTS.md text names that.
- Why it matters: The likely mistake is the natural one, editing the
  description on GitHub, and it publishes the old wording with no error. It is
  fixable afterwards by editing the GitHub release, which is why this is MINOR.
- Suggested response: Have step 8's AGENTS.md text say that the commit body is
  the release text, and that a wording change after the pull request opens is
  an amend and a force-push of `release/v<version>`. Nothing protects that
  branch, so the push is allowed.
- Corroborated by: architecture and boundaries

## Requirement-to-plan trace

| Requirement / criterion | Plan location | Review note |
| --- | --- | --- |
| FR-001 | research.md §3, contracts/check-release-note.md | covered |
| FR-002 | contracts/check-release-note.md §Messages | covered |
| FR-003 | data-model.md §Release note, contracts/check-release-note.md | covered |
| FR-003a | contracts/check-release-note.md §Messages | covered |
| FR-004 | research.md §3, contracts/check-release-note.md | covered |
| FR-005 | research.md §4, contracts/check-release-note.md §Category list | covered |
| FR-006 | research.md §2, contracts/tag-job.md §release-note job | covered |
| FR-007 | contracts/check-release-note.md §Messages | covered |
| FR-008 | data-model.md §Version proposal | covered |
| FR-009 | research.md §7, data-model.md §Merge | covered |
| FR-010 | research.md §4 and §5, data-model.md §Category | covered |
| FR-011 | contracts/release-script.md §Prompts | covered |
| FR-012 | contracts/release-script.md §After both prompts | covered; PR-016 |
| FR-013 | research.md §11, contracts/release-script.md §After both prompts | covered; PR-017, PR-018 |
| FR-014 | contracts/release-script.md §Nothing to release | covered; PR-014 in design.md only |
| FR-015 | contracts/release-script.md §Abort | covered |
| FR-016 | research.md §8, contracts/tag-job.md | covered |
| FR-017 | research.md §9 | covered |
| FR-018 | plan.md §Project Structure, §Implementation order step 8 | covered |
| FR-019 | plan.md §Project Structure (`changes/571.none.md`) | covered |
| FR-020 | research.md §11, contracts/tag-job.md §ruleset, quickstart.md | covered; PR-012 |
| SC-001 | research.md §7, §11 | covered; see Assumptions challenged |
| SC-002 | quickstart.md §Cutting a release | covered |
| SC-003 | contracts/release-script.md step 3; `lint` is a required check | covered |
| SC-004 | contracts/tag-job.md | covered; PR-018 |
| SC-005 | plan.md §Constraints, §Structure Decision | covered |
| US1 scenarios 1 - 6, 8, 9 | plan.md §Implementation order step 2 | covered |
| US1 scenario 7 | plan.md §Risks | read in review, per spec §Validation Strategy |
| US2 scenarios 1 - 10 | plan.md §Implementation order step 5 | covered; PR-015, PR-016, PR-017 |
| US3 scenarios 1 - 4 | contracts/tag-job.md, plan.md §Risks | covered; confirmed on the first release, per spec |
| US4 scenarios 1 - 3 | plan.md §Project Structure, §Implementation order step 8 | covered |
| US5 scenarios 1 - 3 | contracts/tag-job.md §ruleset, quickstart.md | covered; PR-012 |

## Assumptions challenged

- The lookup's newest match is the release commit. With `--no-merges` that
  holds for the merge that releases. It fails on a later run when the release
  is still missing and a newer non-merge commit mentions `chore(release): cut
  $v` in its message, for example a fix that refers to the release. The scratch
  repository showed the lookup returning such a commit, and the subject check
  then failing the job. The failure is loud, needs the release to have failed
  once already, and is fixed by publishing by hand, so it is listed here rather
  than filed. Picking the newest commit whose subject equals the expected one,
  from `git log --no-merges --format='%H%x00%s'`, would close it.
- `gh pr create --fill` takes the description from a single commit's body.
  Verified from gh v2.91.0's source, as PR-011 records. The contract doesn't
  state a minimum gh version, and the behaviour has been in gh for several
  years.
- Step 1 can fail only for a reason other than an existing branch, since the
  version prompt already refused one. The rollback then has no branch to
  delete, and an implementer has to delete only a branch the script created.
  The contract doesn't say so, and a careful implementation does it anyway.
- The ruleset's required check names match what GitHub reports. Carried from
  the earlier review, which read them from the head of #596.
- The ruleset JSON is a valid request body, and an empty `bypass_actors`
  includes repository administrators. Carried from the earlier review. Not
  applied, and PR-012 is why the read-back can't confirm the second half.
- Pull requests open when the ruleset is applied need a new push before they
  can merge, since their runs predate the `release-note` job. Carried from the
  earlier review. The plan doesn't mention it, and it is small with one
  maintainer.
- `spec.md §SC-001` says every pull request merged after protection carries a
  note "because GitHub refuses the merge otherwise". The ruleset covers `main`
  only, so a stacked child can still merge red into its parent's branch. Carried
  from the earlier review.

## Reviewer disagreement

- None identified.

## Strengths worth preserving

- `contracts/tag-job.md` says in its own text why `--no-merges` is
  load-bearing, so a later edit that drops it has to delete the reason first.
- `contracts/release-script.md §After both prompts` says why the reset comes
  before the switch, and why steps 6 and 7 leave the branch in place.
- Step 7's `--fill` removes the last dependency on the temporary draft file
  after the commit exists, so every printed retry command is complete.
- `research.md §11` sends the release through its own pull request rather than
  granting a bypass, and records why.
- `contracts/tag-job.md` runs every check before it creates the tag, so a
  failure leaves no half-published release.

## Source freshness

This review describes only the content identities listed under
`## Reviewed inputs`. When `spec.md`, `plan.md`, a binding design record, or a
material planning artifact changes, this report no longer describes the current
plan, and a new review is needed before it counts as current evidence.
