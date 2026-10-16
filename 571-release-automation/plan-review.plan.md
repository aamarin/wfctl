# Implementation Plan: release automation

**Branch**: `571-release-automation` | **Date**: 2026-10-15 | **Spec**: `spec.md`
**Input**: Feature specification from `spec.md` in this folder

## Summary

Every change commits a release note under `changes/`, named for its issue and
category, and a check in this repository's `verify` list and in CI refuses a
branch without one. A release script proposes the version from the notes, lists
merges that came with no note, drafts the release notes with towncrier, and
opens a release pull request for Andre to merge. The tag job publishes the
release commit's body as the GitHub release, and fails before tagging when that
body is empty. A ruleset protects `main` with no bypass, so every change, a
release included, merges only once its checks pass.

Two standalone Python scripts under `.github/scripts/` carry the work, with
towncrier as a pinned dev dependency and the ruleset as a committed JSON file
Andre applies after merge. Nothing under `wfctl/` changes, so nothing changes
for a project that installs wfctl.

## Technical Context

**Language/Version**: Python 3.11 or later, the repository's floor. The check
uses the standard library only, `tomllib` included.
**Primary Dependencies**: towncrier 26.9, pinned `>=26.9,<27` in the `dev`
extra. git and the `gh` CLI in CI, as the tag job already uses.
**Storage**: files under `changes/` and git history. No other state.
**Testing**: pytest, with scratch git repositories under `tmp_path`.
`uv run wfctl check config` for `wfctl.json`, and `uv run wfctl verify` on this
branch.
**Target Platform**: macOS for Andre's release runs and local `verify`, and
GitHub's `ubuntu-latest` runners for CI.
**Project Type**: repository tooling for a CLI project. Two scripts, one
configuration table, two CI jobs, and one ruleset.
**Performance Goals**: the check finishes within the time `git diff` takes on
the branch, well under a second. No target for the release script, which
waits on Andre.
**Constraints**: nothing reaches a project that installs wfctl (SC-005).
Nothing in `wfctl/agents/` changes, the shipped pull request template included.
The release script never pushes `main`, never merges, and leaves the tree and
its branches unchanged until both prompts are answered. Minimal complexity: no
new wfctl subcommand, and no configuration beyond the towncrier table and the
ruleset file.
**Scale/Scope**: one maintainer cutting a release every week or two, covering
up to about twenty merges.

## Constitution Check

_GATE: Must pass before Phase 0 research. Re-check after Phase 1 design._

The repository has no `.specify/memory/constitution.md`. The gates below come
from the accepted records `wfctl arch context` prints and from AGENTS.md, and
Complexity Tracking records the substitution.

- [x] Validation plan exists: the three commands in AGENTS.md's Definition of
      done, `uv run wfctl check config` for `wfctl.json`, `uv run wfctl verify`
      with and without this branch's note, and tests for every acceptance
      scenario of User Stories 1 and 2. User Story 3 is read in review and
      confirmed on the first release, since the tag job runs only on `main`.
- [x] Complexity is justified: towncrier is the one new dependency, and the
      level 3 record weighed it against writing the collector ourselves. It is
      a dev dependency only.
- [x] Ownership is stated: the author owns the note's text and category, the
      check owns whether the note was committed, the release script proposes
      the version, and Andre confirms it. Each is stated under Ownership below.
- [x] `a-rule-is-expressed-as-a-check`: a missing note is visible in the
      branch's diff, so the rule ships as a check, not as AGENTS.md prose.
- [x] `wfctl-runs-the-verification`: the check is a `verify` command, so wfctl
      records the verdict and the agent doesn't vouch for its own note.
- [x] `layer-model`: no file under `wfctl/agents/` or `wfctl/specify/` changes,
      and nothing is written into a dotted directory by hand.
- [x] `knowledge-placement`: how to write a note and cut a release is guidance
      for the worker, so it goes in AGENTS.md. The rule itself lives in the
      check and in `change-carries-release-note`.
- [x] AGENTS.md's Releasing rules: the version bump and `uv lock` stay in one
      commit, now made by the script, and this branch doesn't bump the version.

Re-checked after Phase 1: all gates still hold. The FR-014 refinement below adds
a case to the release script and no new component.

## Ownership

| Value | Computed by | Why the other side can't |
| --- | --- | --- |
| what a user will notice, and its category | the change's author, in the note | a commit type can't say it, and the person cutting the release can only reconstruct it later |
| whether the branch committed a note | the check, from `git diff` | an agent saying it wrote one is the agent vouching for its own work |
| which merges came with no note | the release script, from each merge's own diff | the branch name doesn't say which notes a branch added |
| the proposed version | the release script, from the notes' categories | nobody else has read every note at once |
| the confirmed version and the final wording | Andre | a release is a judgment about the whole set |
| what the GitHub release says | the release commit's body, read by the tag job | GitHub's generated list comes from titles nobody wrote for users |
| whether a change may reach `main` | the ruleset, from the required checks | a bypass would be granted to the one person who merges, and would let every red merge through |

## Design records

Read before Phase 0, from `design.md`'s `## Software design decisions`:

- `docs/architecture/change-carries-release-note.md` (proposed, level 2)
- `docs/architecture/design/571-towncrier-builds-release-notes.md` (proposed,
  level 3)

This plan follows both. It differs from the level 3 record's wording in one
place: the record says the script removes the `none` notes before the build,
and this plan builds from a temporary copy without them, so nothing in the
tree changes before Andre confirms (research 4). The outcome the record names
is the same. The release pull request, the ruleset, and the tag job's refusal
of an empty body follow the level 2 record as revised on 2026-10-15
(research 8 and 11).

## Changes from the spec

- FR-014 now requires every merge since the last tag to have added a note
  before the script reports nothing to release, and User Story 2 gained
  scenario 8. Every merge since v0.23.0 predates the check, so the first
  release after this feature would otherwise report nothing to release over
  nine merges. `design.md` already says a merge with no note is never read as
  `none`, and the spec now agrees.
- After the first plan review, clarify's 2026-10-15 session reversed the answer
  on branch protection. `main` is protected with no bypass, so the release goes
  through its own pull request (FR-013, FR-020, User Stories 2 and 5), and #599
  is folded in. The check passes a release branch whose version matches its
  name (FR-004, User Story 1 scenario 9). The tag job fails before tagging on an
  empty release body and never publishes GitHub's generated notes (FR-016, User
  Story 3 scenario 4). The level 2 record was revised the same day.
- User Story 2 now names the version prompt before the draft, which is the
  order the release script's contract always had.

## Project Structure

### Documentation (this feature)

```text
wfctl-specs/571-release-automation/
├── design.md
├── spec.md
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   ├── check-release-note.md
│   ├── release-script.md
│   └── tag-job.md
└── tasks.md             # /speckit.tasks, not this step
```

### Source Code (repository root)

```text
.github/
├── scripts/
│   ├── check_release_note.py      # new: the check
│   └── release.py                 # new: the release script
├── rulesets/main.json             # new: main's protection, applied by Andre after merge
├── workflows/ci.yml               # release-note job added, tag job publishes the body
└── pull_request_template.md       # "Type of Change" removed, this repo only
changes/
└── 571.none.md                    # this branch's own note
pyproject.toml                     # towncrier in the dev extra, [tool.towncrier]
uv.lock                            # relocked for towncrier
wfctl.json                         # check added to verify
AGENTS.md                          # Releasing rewritten, release notes in Conventions
tests/
├── test_install_config.py         # drift test skips "Type of Change" in the template
├── test_shape.py                  # the _TEMPLATE comment stops saying byte-identical
├── test_release_note_check.py     # new
└── test_release_script.py         # new
```

`tests/test_install_config.py::test_shipped_github_config_matches_this_repos_own_copy`
holds every file of the shipped `github` config byte-identical to this
repository's copy, and FR-018 makes the two pull request templates differ. The
test stays, because the drift it was written for, the repository's copy edited
and the shipped one left behind, can still happen in every other line. For
`.github/pull_request_template.md` only, it compares the two with the "Type of
Change" section removed from each, from its `##` heading to the next one. A
second test asserts the shipped copy still carries that section, which is User
Story 4 scenario 3.

**Structure Decision**: repository tooling only. The scripts sit beside the two
existing CI scripts in `.github/scripts/`, and tests sit in `tests/`, which
already holds every test this repository runs. Nothing is added under `wfctl/`.

This branch's own note is `none`. What changes is how wfctl is released, and
nothing an installed wfctl does is different. The release page carrying written
notes is visible to anyone reading releases, so if that reads as an addition to
whoever reviews this, the file is renamed `571.addition.md` before merge.

## Implementation order

1. towncrier in the `dev` extra, the `[tool.towncrier]` table with its four
   types, and `uv lock`. Everything after it reads that table.
2. The check, its tests covering User Story 1 scenarios 1 to 6, 8 and 9, and
   its `verify` entry. The tests clear `GITHUB_HEAD_REF` and `GITHUB_REF_NAME`
   in an autouse fixture, and one test sets them. Then `uv run wfctl check
   config`.
3. This branch's note, and `uv run wfctl verify` with and without it.
4. The `release-note` CI job.
5. The release script and its tests covering User Story 2 scenarios 1 to 10,
   with scenario 8 carried through to the commit, then a dry run against a
   scratch clone of `main`.
6. The tag job's checks and release text, and its comment.
7. `.github/rulesets/main.json`.
8. AGENTS.md, this repository's pull request template, the drift test, and the
   comment above `_TEMPLATE` in `tests/test_shape.py`, which says the two
   templates are byte-identical. The shipped template is left as it is. AGENTS.md's Releasing section gives the
   two commands that protect `main` and the two that read the protection back.

Steps 2 and 5 are independent once step 1 lands.

After merge, Andre applies the ruleset and the merge setting, which is User
Story 5. It has to wait for merge, because a required `release-note` check that
no pull request reports yet would block every merge, this one included.

## Risks

- The tag job change can only run on `main`. The first release after merge is
  its test. A failure there leaves no tag and no release, so it is visible and
  publishes nothing wrong, and the fix is to publish that one release by hand.
- `actions/checkout` on a pull request checks out a detached merge commit. The
  check reads `GITHUB_HEAD_REF` for that reason. On this branch's own pull
  request, the evidence it works is that the pass line names `#571` rather than
  "this branch", since a lookup that fell through to the detached `HEAD` would
  read as a branch with no issue and still pass on `571.none.md`.
- The ruleset's check names must match the job names GitHub reports. A name
  that never reports blocks every merge into `main`. Reading the ruleset back
  and merging the next pull request is the test, and removing the ruleset is
  the way back.
- towncrier's file name format is assumed stable within the pin. A change
  shows up as a failing test at the next `uv lock --upgrade`, not in a release.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
| --- | --- | --- |
| Gates come from the accepted records and AGENTS.md rather than a constitution | the repository has no `.specify/memory/constitution.md` | an empty gate list would pass anything, and gates from another project would be false here |
