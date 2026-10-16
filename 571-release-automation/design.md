# A release note on every change, and a release cut from them

## Problem Statement

How might we cut a wfctl release from notes written when each change was made,
so that nobody has to read every merged pull request to find out what changed?

## Recommended Direction

Every change commits a short release note file saying what an existing user
will notice, named for its issue and its category, such as
`changes/293.change.md`. A check in this repository's `verify` list refuses a
branch without one, so `wfctl verify`, `wfctl status`, the check before a pull
request opens, and CI all hold the change until the note exists. The agent that
makes the change writes the note, so it costs no person's time.

When Andre cuts a release, a script proposes the version from the notes'
categories, and towncrier drafts the release notes from the files. Andre
confirms the version and edits the draft, and the script opens a release pull
request, which Andre merges once its checks pass. The tag job then publishes the
release commit's body as the GitHub release, in place of the list GitHub
generates.

This is wfctl's own release process. Nothing changes for a project that installs
wfctl, and towncrier is a dev dependency that nobody who installs wfctl gets.

## Behaviour

Three people see something new. The strings below are what each one reads, in
each state.

### An agent finishing a change

A branch with no note fails verification:

```
✗ no release note for #571
  add changes/571.<category>.md, where the category is change, addition, fix, or none
  for example: uv run towncrier create 571.change.md --content "What a user of wfctl will notice."
```

A note whose category doesn't exist fails the same way:

```
✗ changes/571.feature.md names the category "feature", which doesn't exist
  use change, addition, fix, or none
```

A stacked branch whose only note is its parent's gets the first message, naming
its own issue. A branch whose name starts with no issue, such as a dependency
update, gets this one:

```
✗ no release note on this branch
  add changes/+<what-changed>.<category>.md, where the category is change, addition, fix, or none
  for example: uv run towncrier create +<what-changed>.fix.md --content "What a user of wfctl will notice."
```

On `main` the check passes, since there is no branch to compare against. It
also passes a `release/v<version>` branch whose `pyproject.toml` carries that
version, which is what lets the release pull request, which deletes the notes,
pass its own CI.

### Andre cutting a release

The release script prints the proposal and the draft, then waits:

```
Proposed version: 0.24.0 (minor: 2 behaviour changes, 1 addition)
Merged with no release note: #566, #570

## Behaviour changes

- ... (#542)

## Additions

- ... (#509)

## Fixes

- ... (#537)

Confirm the version [0.24.0]:
```

Once the version is confirmed, the draft opens in Andre's editor as the release
commit's body, and the script then opens the release pull request. Lines inside a
section are sorted by issue number, so he moves the most important line to the
top while editing, as he did for 0.23.0. The notes marked `none` never appear.

The "Merged with no release note" line lists pull requests merged before the
check existed. It is a list to read by hand, never treated as `none`. Once every
merged change carries a note, the line is absent.

When `changes/` holds only `none` notes, or nothing, and every merge since the
last tag added a note, the script says so and stops, because there is nothing
for a user to notice. A merge with no note keeps it going, with an empty draft
for Andre to write:

```
Nothing to release: 3 changes merged since v0.23.0, all marked none.
```

### Someone reading the GitHub release

The release page shows the same text Andre confirmed, with each issue number as
a link. A preview built from 0.23.0's changes, with the notes rewritten under
the writing-style rules, read as Andre wanted.

## Boundaries and Ownership

The level 2 answer is a record. The change's author owns what an existing user
will notice. wfctl's verification owns whether the note was committed. The
person cutting the release owns the version and the final wording.

## Software design decisions

- docs/architecture/change-carries-release-note.md — every change commits its own release note, and the definition of done requires it
- docs/architecture/design/571-towncrier-builds-release-notes.md — towncrier drafts the release notes, and a check of ours requires each branch's own note

### Checked

- towncrier 26.9.0 groups notes by category in the configured order, merges
  identical sentences into one line, numbers a second note on one issue, and
  renders a `+` note with no link. Measured in a scratch repository (finding
  11 of `scans/571-evaluation.md`).
- `towncrier build --draft` writes nothing. Measured on 2026-10-14.
- Merge commits on `main` read `Merge pull request #596 from
  aamarin/468-panel-rubric-by-path`, so the release script can list merged
  branches since the last tag, and each branch's issue, from `git log --merges`
  alone. Read from `v0.23.0..origin/main`.
- The tag job publishes with `gh release create "v$v" --generate-notes`
  (`.github/workflows/ci.yml` line 197).
- `pyproject.toml` pins ruff to a minor in the `dev` extra, which is the
  precedent for pinning towncrier.
- `tomllib` ships with Python 3.11, so the check reads the category list from
  `pyproject.toml` with no dependency.

### Assumed

- `wfctl verify` runs from the branch's working tree with `origin/main` or
  `main` available to diff against. A worktree with no fetched `main` would
  need the check to say so rather than pass.
- The release commit can carry the edited draft as its body, and the tag job
  can read that body back with `git log -1 --format=%b`. Not yet tried in CI.
- Agents will write honest notes rather than default to `none`. No evidence
  either way. The review panel is where a category gets compared against the
  diff.

## Key Assumptions to Validate

- [ ] The check runs inside `wfctl verify` and in CI with the same result. Test
  it on this branch before it opens.
- [ ] The tag job publishes the release commit's body unchanged. Test it with
  the first release after this merges.
- [ ] A merged branch is matched to its note by the files under `changes/` its
  merge commit added, not by the issue at the front of its name (clarified
  2026-10-14). Test it on the merges since v0.23.0, which should all come back
  as having no note.

## MVP Scope

1. The check script, added to `verify` in `wfctl.json` and to CI.
2. towncrier in the `dev` extra, with its configuration under
   `[tool.towncrier]`.
3. The release script under `.github/scripts/`: proposes the version, lists the
   merged changes with no note, drafts with towncrier, bumps the version, runs
   `uv lock`, deletes the notes, and opens a release pull request for Andre to
   merge.
4. The tag job publishes the release commit's body, and the comment above it
   describes this process.
5. This branch's own note.
6. AGENTS.md's Releasing section, and the PR template's "Type of Change"
   checkboxes, which ask the same question as the note's category.

## Not Doing (and Why)

- A `CHANGELOG.md` file. The release commit's body is already what the tag job
  publishes, and a second copy edited separately would drift from it. Adding it
  later means dropping `--draft`.
- Deriving the version from commit subjects. None of 0.23.0's five behaviour
  changes was typed as one.
- Reminding anyone that merged work is waiting. The number of notes under
  `changes/` is the natural input, and whether anything should prompt is still
  open.
- Releasing without a person. The version and the wording stay Andre's call.
- Anything wfctl ships to other projects. This is wfctl's own process only.

## Open Questions

- Settled on 2026-10-14: this repository's pull request template drops the
  "Type of Change" checkboxes, and the template wfctl ships keeps them.
- Settled on 2026-10-15: the release script opens a pull request for the
  release commit, and `main` is protected with no bypass, so nothing reaches it
  by a direct push.
