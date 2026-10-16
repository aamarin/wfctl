# Feature Specification: release automation

**Feature Branch**: `571-release-automation`  
**Created**: 2026-10-14  
**Status**: Draft  
**Input**: User description: none typed. `design.md` in this folder is the description.

## Clarifications

### Session 2026-10-14

- Q: Should the check read a note's content, or only its file name? → A: It
  fails a note that is empty or still holds towncrier's placeholder text, "Add
  your info here", and names the file.
- Q: How does the release script decide a merged pull request came with a note?
  → A: By whether the merge commit itself added a file under `changes/`, read
  from git, not by matching the issue number in the branch name.
- Q: Which pull request template loses the "Type of Change" checkboxes? → A:
  This repository's own `.github/pull_request_template.md` only. The template
  wfctl ships under `wfctl/agents/configs/github/` keeps them.
- Q: Should `main` require the release note check to pass before a pull
  request merges? → A: No. The check fails CI where Andre sees it, as tests and
  lint do today, and the release script lists any merge that got through. A
  follow-up issue, #599, tracks requiring it once someone other than Andre can
  merge. Revised on 2026-10-15, below.

### Session 2026-10-15

- Q: What does the tag job do when the release commit's body is empty? → A: It
  fails before it tags anything, so no tag and no release are published. It
  never falls back to the notes GitHub generates.
- Q: Should `main` require the checks before a pull request merges, now that a
  release with no notes can't be published? → A: Yes. This replaces the
  2026-10-14 answer. `main` is protected with no bypass, Andre included, so a
  release reaches `main` through its own pull request like any other change.
  #599 is folded into this feature.

## User Scenarios & Testing _(mandatory)_

Three people meet this feature. An agent finishing a change has to commit a
release note before the change counts as done. Andre, cutting a release, runs one
script that proposes the version, drafts the release notes from those notes, and
opens a release pull request for him to merge. Someone reading the GitHub
release sees the text Andre confirmed, rather than a list GitHub generated from
pull request titles.

### User Story 1 - A change isn't done until it commits its release note (Priority: P1)

An agent finishes a change and runs `wfctl verify`. If the branch hasn't
committed a release note for its issue, verification fails and says which file
to add. The same check runs in CI, so a pull request opened without running
`wfctl verify` is refused too.

A release note is a short file under `changes/`, named for the issue and one of
four categories, such as `changes/571.change.md`. Its text says what an existing
user of wfctl will notice once the change ships. The four categories are a
behaviour change (`change`), an addition (`addition`), a fix (`fix`), and
nothing to notice (`none`).

**Why this priority**: Every later story reads these files. Without the check,
notes go missing the same way the "Breaking change" checkbox did, which was
ticked on 1 of 5 pull requests that needed it.

**Independent Test**: On a branch with no note, `wfctl verify` records a
failure and `wfctl status` shows the definition of done as unmet. Adding
`changes/<issue>.change.md` and running it again records a pass.

**Acceptance Scenarios**:

1. **Given** branch `571-release-automation` adds no file under `changes/`,
   **When** the agent runs `wfctl verify`, **Then** verification fails with a
   message naming `changes/571.<category>.md` and the four categories.
2. **Given** the branch adds `changes/571.change.md`, **When** the agent runs
   `wfctl verify`, **Then** the release note check passes.
3. **Given** the branch adds `changes/571.feature.md`, **When** the agent runs
   `wfctl verify`, **Then** verification fails and names `feature` as a
   category that doesn't exist.
4. **Given** branch `580-child` is stacked on `571-release-automation` and its
   only note is `changes/571.change.md`, **When** the check runs, **Then** it
   fails and asks for `changes/580.<category>.md`.
5. **Given** a branch whose name starts with no issue adds
   `changes/+bump-ruff.fix.md`, **When** the check runs, **Then** it passes.
6. **Given** the current branch is `main`, **When** the check runs, **Then** it
   passes.
7. **Given** a pull request whose branch has no note, **When** CI runs on it,
   **Then** the CI run fails on the release note check.
8. **Given** the branch adds `changes/571.change.md` holding only "Add your
   info here", which is what `towncrier create` writes without `--content`,
   **When** the check runs, **Then** it fails and names the file as unwritten.
   An empty or whitespace-only note fails the same way.
9. **Given** branch `release/v0.24.0` deletes every note and sets the version
   to 0.24.0, **When** the check runs, **Then** it passes. The same branch with
   the version set to 0.23.1 fails, naming both versions.

---

### User Story 2 - Andre cuts a release with one script (Priority: P2)

Andre runs the release script on an up-to-date `main`. It proposes a version,
lists any merged change that has no release note, and shows a draft of the
release notes grouped by category with behaviour changes first. Andre confirms
or changes the version, then edits the draft. The script commits one release
commit on a new branch, `release/v<version>`, pushes that branch, and opens a
pull request for it. The commit bumps the version, updates `uv.lock`, deletes
the release note files, and carries the edited draft as its body. Andre merges
the pull request once its checks pass.

**Why this priority**: This removes the reading of every merged pull request,
which took a subagent for 0.23.0, and the dropped `uv.lock` that 0.18.0, 0.20.0,
and 0.21.0 each shipped with.

**Independent Test**: On a scratch copy of `main` holding a few release notes,
with a scratch remote and the pull request step stubbed, run the script, accept
the proposal, and check the branch it pushes: the new version in
`pyproject.toml`, a matching `uv.lock`, no files left under `changes/`, and a
commit body equal to the confirmed draft. Check that it asked for the pull
request with `--fill` on a branch holding only that commit, which is what makes
GitHub's description equal the commit body.

**Acceptance Scenarios**:

1. **Given** the notes include one `change` and one `fix`, **When** Andre runs
   the script, **Then** it proposes the next minor version and says why, such
   as "minor: 1 behaviour change".
2. **Given** the notes include only `fix` and `none`, **When** Andre runs the
   script, **Then** it proposes the next patch version.
3. **Given** the notes include `none` notes, **When** the draft is shown,
   **Then** no section and no line for them appears.
4. **Given** a branch merged since the last tag added no note, **When** Andre
   runs the script, **Then** the script names that pull request under "Merged
   with no release note" before the draft.
5. **Given** branch `bump-ruff`, whose name starts with no issue, merged with
   `changes/+bump-ruff.fix.md`, **When** Andre runs the script, **Then** that
   pull request is not listed under "Merged with no release note", and its note
   appears in the draft.
6. **Given** Andre confirms a different version than the one proposed, **When**
   the commit is made, **Then** it and its branch use the version Andre typed.
7. **Given** every note since the last tag is `none`, or there are none, and
   every merge since the last tag added a note, **When** Andre runs the script,
   **Then** it says there is nothing to release and prepares no commit.
8. **Given** there are no notes, and merges since the last tag that added none,
   **When** Andre runs the script, **Then** it lists those merges, proposes a
   patch, and opens the draft for Andre to write them in. It never reports
   nothing to release over merges it couldn't read.
9. **Given** Andre stops at either prompt, **When** the script exits, **Then**
   the working tree and its branches are exactly as they were before the script
   ran, and nothing was pushed.
10. **Given** a release pull request for 0.24.0 is still open, **When** Andre
    runs the script and confirms 0.24.0, **Then** it refuses because
    `release/v0.24.0` already exists, names that branch, and changes nothing.

---

### User Story 3 - The GitHub release carries the confirmed release notes (Priority: P3)

When the release pull request merges and test, wheel, and lint pass on `main`,
the tag job tags the merge and publishes a GitHub release whose text is the
release commit's body. The list GitHub generates from pull request titles is no
longer used, not even as a fallback.

**Why this priority**: Today the release notes are written twice, once in the
commit body and once by GitHub, and the published copy is the one nobody wrote.

**Independent Test**: After the first release that runs through this feature,
the GitHub release page shows the same text as the release commit's body.

**Acceptance Scenarios**:

1. **Given** a release pull request with an edited body merges into `main`,
   **When** test, wheel, and lint pass, **Then** the tag job publishes a release
   whose notes equal the release commit's body.
2. **Given** any of test, wheel, or lint fails on `main` after the merge,
   **When** the tag job is evaluated, **Then** nothing is tagged or published,
   as today.
3. **Given** the tag exists but the release is missing, **When** the tag job
   runs again, **Then** it creates the release from the release commit's body.
4. **Given** the version on `main` changed and the commit that changed it has an
   empty body, or isn't the release commit for that version, **When** the tag
   job runs, **Then** it fails before tagging, says which, and nothing is
   tagged or published.

---

### User Story 4 - The repository's own docs describe the new process (Priority: P4)

AGENTS.md's Releasing section describes running the release script, merging the
release pull request, and writing a release note on every change. The comment
above the tag job describes what the job now publishes. The pull request
template no longer asks for a change type that the release note's category
already records.

**Why this priority**: An agent reads AGENTS.md before working on wfctl, and the
old text tells it to bump the version by hand.

**Independent Test**: Read the three places and confirm none of them describes
the old process.

**Acceptance Scenarios**:

1. **Given** the feature has merged, **When** an agent reads AGENTS.md's
   Releasing section, **Then** it learns to write a release note on every change
   and to cut a release with the script.
2. **Given** the feature has merged, **When** someone opens a pull request on
   this repository, **Then** the template does not ask for the type of change.
3. **Given** the feature has merged, **When** a project runs `wfctl
   install-config github`, **Then** the template it receives still carries the
   "Type of Change" checkboxes, unchanged.

---

### User Story 5 - `main` refuses a change whose checks failed (Priority: P5)

Once this feature merges, Andre turns on protection for `main` with the command
AGENTS.md gives. From then on every change reaches `main` through a pull request
whose test, wheel, lint, and release note checks passed. Nobody can push to
`main` directly or merge past a red check, Andre included, and a pull request
can only merge as a merge commit.

**Why this priority**: Without it, a merge with no release note and a release
with no notes are each caught only after they land. Protection moves both
refusals to before the merge. It comes last because it is a setting applied
after the rest has merged, and the release note check has to exist before
`main` can require it.

**Independent Test**: Read `main`'s protection back from GitHub and confirm the
required checks, that administrators are included, and that the repository
allows merge commits only.

**Acceptance Scenarios**:

1. **Given** protection is on, **When** a pull request's release note check
   fails, **Then** GitHub refuses to merge it, for Andre too.
2. **Given** protection is on, **When** anyone pushes a commit straight to
   `main`, **Then** GitHub refuses the push.
3. **Given** protection is on, **When** Andre merges a pull request, **Then**
   only a merge commit is offered.

---

### Edge Cases

- A pull request that closes two issues commits one note per issue. When both
  notes carry the same sentence, the draft shows one line linking both issues.
- A second pull request for an issue that already has a merged note commits its
  own, such as `changes/571.change.2.md`, and the draft lists both.
- The release pull request deletes every note. Its check passes because a
  branch named `release/v<version>` whose `pyproject.toml` carries that version
  needs no note. A release branch whose name and version disagree fails.
- Two stacked branches for the same issue pass on the parent's note. This case
  is left to review rather than the check.
- A worktree with no local `main` and no `origin/main` to compare against. The
  check fails and says it couldn't find the branch to compare against, rather
  than passing.
- A note file under `changes/` whose name doesn't match the
  `<issue>.<category>.md` or `+<name>.<category>.md` form at all, such as
  `changes/notes.md`. The check fails and names the file.
- A note created with `uv run towncrier create` and never edited. It holds
  "Add your info here", and the check fails it rather than letting the
  placeholder reach the release draft.
- A direct push to `main`. Once protection is on, GitHub refuses it. Before
  then, the release script doesn't list it, since it lists merged pull requests
  only.
- Another change merges while the release pull request is open. The tag lands
  on the release's merge, so that change's code ships in this release while its
  note waits under `changes/` for the next one. Merging the release pull request
  soon after it opens keeps this rare, and closing it and running the script
  again drafts the late change's note too.
- A pull request that closes two issues adds two notes in one merge. The script
  counts the merge as having a note, because it reads the files the merge added
  rather than the issue in the branch name.

## Requirements _(mandatory)_

### Functional Requirements

- **FR-001**: The repository MUST have a release note check that fails a branch
  whose diff against `main` adds no note named for the issue at the front of the
  branch's name.
- **FR-002**: For a branch whose name starts with no issue, the check MUST fail
  unless the branch adds at least one note.
- **FR-003**: The check MUST fail a note whose category isn't one of `change`,
  `addition`, `fix`, or `none`, and a file under `changes/` whose name has
  neither note form. It MUST name the file in its message.
- **FR-003a**: The check MUST fail a note added by the branch whose content is
  empty, whitespace only, or towncrier's placeholder text "Add your info here",
  and MUST name the file in its message.
- **FR-004**: The check MUST pass on `main`, and on a branch named
  `release/v<X.Y.Z>` whose `pyproject.toml` version is `X.Y.Z`. It MUST fail a
  release branch whose name and version disagree.
- **FR-005**: The check MUST read the list of categories from the same
  configuration the release notes are built from, so the two lists can't
  disagree.
- **FR-006**: The check MUST be listed under `verify` in this repository's
  `wfctl.json`, and MUST run in CI on every pull request.
- **FR-007**: The failure message MUST name the file to add and the four
  categories, and give one command that creates a note.
- **FR-008**: The release script MUST propose a minor version when any note is a
  `change` or an `addition`, and a patch version otherwise, and MUST say which
  notes led to the proposal.
- **FR-009**: The release script MUST list the pull requests merged since the
  last tag whose merge commit added no file under `changes/`, before it shows
  the draft. It MUST decide this from the files the merge added, not from the
  issue number in the branch name.
- **FR-010**: The draft MUST group notes under behaviour changes, then
  additions, then fixes, and MUST leave out `none` notes.
- **FR-011**: Andre MUST be able to edit the draft and change the version
  before anything is committed.
- **FR-012**: The release commit MUST bump the version in `pyproject.toml`,
  update `uv.lock` to match, delete every file under `changes/`, and carry the
  confirmed draft as its body.
- **FR-013**: After both prompts are answered, the release script MUST commit
  on a new `release/v<version>` branch, push that branch, and open a pull
  request for it into `main` whose description is the confirmed draft. It MUST
  NOT push `main` and MUST NOT merge. Andre merges the pull request.
- **FR-014**: When no note other than `none` exists since the last tag, and
  every merge since then added a note, the release script MUST say there is
  nothing to release and change nothing. A merge with no note MUST NOT be read
  as `none`, so its presence always leads to a draft.
- **FR-015**: When Andre stops before confirming, the release script MUST leave
  the working tree unchanged.
- **FR-016**: The tag job MUST publish the release commit's body as the GitHub
  release notes, and MUST keep its existing gate on test, wheel, and lint. It
  MUST fail before tagging when it can't find the release commit for the
  version, or when that commit's body is empty, and MUST NOT publish GitHub's
  generated notes in any case.
- **FR-017**: The tool that drafts the release notes MUST be a pinned dev
  dependency, so nothing that installs wfctl gets it.
- **FR-018**: AGENTS.md's Releasing section, the comment above the tag job, and
  this repository's own pull request template MUST describe the new process.
  The template wfctl ships to other projects MUST NOT change, so the two copies
  differ from this feature on.
- **FR-019**: This branch MUST commit its own release note.
- **FR-020**: AGENTS.md MUST give the command that protects `main`, and Andre
  MUST apply it once this feature has merged. The protection MUST require a
  pull request, MUST require the test, wheel, lint, and release note checks to
  pass, MUST apply to administrators with no bypass, and the repository MUST
  allow merge commits only.

## Key Entities _(include if feature involves data)_

- **Release note**: one file under `changes/`, named
  `<issue>.<category>.md`, `<issue>.<category>.<n>.md` for a second note on one
  issue, or `+<name>.<category>.md` for work with no issue. It holds a few
  sentences for an existing user of wfctl.
- **Category**: one of `change`, `addition`, `fix`, or `none`. It decides the
  section a note appears in and whether a release is a minor or a patch.
- **Release commit**: the one commit on a `release/v<version>` branch. It bumps
  the version, updates `uv.lock`, deletes the notes, and carries the release
  notes as its body, with the subject `chore(release): cut <version>`.
- **Release pull request**: the pull request the release script opens for that
  branch, with the release notes as its description. Merging it is what
  releases.

## Success Criteria _(mandatory)_

### Measurable Outcomes

- **SC-001**: Every pull request merged after `main` is protected carries a
  release note, because GitHub refuses the merge otherwise. The release
  script's "Merged with no release note" list stays empty from the second
  release on, which is what measures it.
- **SC-002**: Cutting a release takes one script run and one merge, and needs
  no reading of merged pull requests beyond those the script lists as having
  no note.
- **SC-003**: No release after this feature ships a `uv.lock` that disagrees
  with `pyproject.toml`.
- **SC-004**: The text on the GitHub release matches the release commit's body
  for every release after this feature.
- **SC-005**: Nothing changes for a project that installs wfctl. Its installed
  files and wfctl's runtime dependencies are the same before and after.

## Validation Strategy _(mandatory)_

- `uv run pytest -q`, `uv run ruff check wfctl/ tests/`, and `uv run mypy
  wfctl/` all pass, with tests for the check covering acceptance scenarios 1 - 6,
  8 and 9 of User Story 1, and tests for the release script covering scenarios 1 - 10 of
  User Story 2 against a scratch repository.
- `uv run wfctl check config` passes after `wfctl.json` gains the check.
- `uv run wfctl verify` passes on this branch once its own note is committed,
  and fails when the note is removed.
- A dry run of the release script on a copy of `main` shows the draft and leaves
  the tree unchanged.
- The CI change is read in review, and confirmed on the first release after
  merge, since the tag job only runs on `main`.
- `main`'s protection is read back from GitHub after Andre applies it, and the
  first release after that goes through its own pull request.

## Assumptions

- Pre-specify design context loaded from `design.md` in this folder.
- `main` had no branch protection and no ruleset, checked on 2026-10-14. This
  feature protects it with no bypass for anyone. A bypass that let the release
  commit go straight to `main` would be granted to Andre, and GitHub grants a
  bypass per person rather than per kind of push, so it would also cover every
  red merge. Sending the release through its own pull request removes the need
  for a bypass, at the cost of one merge per release.
- The repository allows merge commits only. Stacked pull requests already rely
  on merge commits, and the release script finds merged pull requests by their
  merge commits, so a squash or rebase merge would be invisible to it.
- This repository's pull request template loses its "Type of Change"
  checkboxes, since the release note's category records the same thing more
  precisely and two fields asking one question will disagree. The template
  wfctl ships keeps them, because projects that install it have no release
  notes to replace them.
- No `CHANGELOG.md` is added. The release commit's body is the one copy Andre
  edits and the tag job publishes.
- Changes merged before this feature have no note. The first release after it
  lists them as having no note, and Andre reads those by hand.
