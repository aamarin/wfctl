---
status: proposed
---

# towncrier drafts the release notes, and a check of ours requires each branch's own note

## Context

`change-carries-release-note` requires every change to commit a release note
file, and has a release script build the release notes from those files. That
leaves two pieces of code to write: a check that refuses a branch with no note,
and a collector that groups the notes by category, puts behaviour changes first,
and renders them as markdown.

towncrier is a release notes tool that pip and pytest use, and it already does
most of the collecting. The first pass of the #571 evaluation missed it. Finding
11 of `scans/571-evaluation.md` installed and ran it, and this record decides how
much of the work it takes over.

## Verified

- towncrier 26.9.0, run in a scratch repository (finding 11): `build` groups the
  notes by category in the order the configuration lists them, and merges two
  notes with the same sentence into one line that links both issues.
  `towncrier create 620.fix.md` writes `620.fix.2.md` when the first name is
  taken.
- The same run: `towncrier check` passes a stacked branch on its parent's note,
  and skips itself when a branch edits the changelog.
- A note named `+trunk-null.change.md` renders as a line with no issue link, and
  a note named for a branch, such as `571-release-automation`, renders as a
  broken issue link.
- A category configured with `showcontent = false` still prints its heading and
  a bare list of issue links. No setting was found that leaves a category out.
- `towncrier build --draft` prints the release notes and writes nothing: "Draft
  only -- nothing has been written."
- `pyproject.toml` pins the dev tools in the `dev` extra, with `ruff>=0.15,<0.16`
  and a comment saying why an unpinned tool turns "someone else's release into a
  red build on an untouched branch".
- `.github/workflows/ci.yml` line 197 publishes the release with
  `gh release create "v$v" --generate-notes`.
- Python 3.11, this repository's floor, ships `tomllib`, so the check script can
  read the category list from `pyproject.toml` with no dependency.

## Assumed

- towncrier's file name format, `<issue>.<category>.md` with `+` for a note
  with no issue, stays the same across the minor versions the pin allows. A
  release that renames either would break notes already on `main`.
- Reordering lines inside a section by hand is enough for the person cutting the
  release, since towncrier sorts each section by issue number. If it isn't, the
  release script would need to sort the draft itself.

## Direct baseline

We write both scripts ourselves. A note is `changes/<branch>.md` with the
category in frontmatter. The check script parses the frontmatter and compares
the category against a list it holds. The collector parses the same
frontmatter, groups the notes using its own copy of the list, orders the
sections, renders the markdown, and deletes the files.

## Decision

towncrier drafts the release notes, and it is pinned in the `dev` extra like
ruff, so nothing that installs wfctl gets it. Its configuration, under
`[tool.towncrier]` in `pyproject.toml`, holds the four categories in the order
the release notes print them, and the format that turns an issue number into a
link. A note is named in towncrier's format, such as `changes/293.change.md`.

The check is ours, not `towncrier check`. It reads the category list from that
same configuration, and fails a branch that adds no note for the issue its name
starts with, or a note whose category isn't in the list.

The release script removes the `none` notes first, since towncrier can't leave a
category out, and then runs `towncrier build --draft --version <version>`. The
draft becomes the release commit's body for the person to edit, which is what
the tag job publishes. The script deletes the remaining notes itself, so the
repository gains no `CHANGELOG.md`.

## Diagram

```
             baseline                                decision

stable    ┌────────────────────────┐           ┌────────────────────────────┐
          │ note files             │           │ note files                 │
          │ changes/<branch>.md,   │           │ changes/<issue>.<cat>.md   │
          │ category in frontmatter│           │ (new name)                 │
          └────────────────────────┘           └────────────────────────────┘
               ▲              ▲                       ▲               ▲
════ change-carries-release-note: the author writes the note ═════════════════
               │ reads        │ reads                 │ reads         │ reads
volatile  ┌────┴─────┐  ┌─────┴───────┐         ┌─────┴────┐   ┌──────┴──────┐
          │ check    │  │ collector   │         │ check    │   │ towncrier   │
          │ (ours),  │  │ (ours),     │         │ (ours)   │   │ (new, a     │
          │ holds the│  │ holds the   │         └─────┬────┘   │ pinned dev  │
          │ category │  │ category    │               │ reads  │ dependency) │
          │ list     │  │ list, order,│               ▼        └──────┬──────┘
          └──────────┘  │ and layout  │         ┌────────────────┐    │ reads
                        └─────────────┘         │[tool.towncrier]│◄───┘
                                                │ categories,    │
                                                │ order, links   │
                                                │ (new)          │
                                                └────────────────┘
```

The change this is built to absorb is adding or renaming a category. In the
baseline it touches two places, the check's list and the collector's, and the
two can disagree without either one failing. In the decision it touches one
table that both readers take the list from. The graphs differ by the collector
being replaced with a pinned dependency and by one configuration table added,
which takes the category list from two copies to one.

## Considered

- We write our own collector, per Direct baseline. It adds no dependency. We
  didn't choose it because it rewrites what towncrier already does and tests,
  such as merging duplicate lines and numbering a second note on one issue, and
  because it keeps the category list in two scripts.
- `towncrier check` instead of a check of ours. It is less code. We didn't
  choose it because it passes a stacked branch on its parent's note, and skips
  itself whenever a branch edits the changelog.
- towncrier writes a `CHANGELOG.md` in the release commit. That is how most
  projects run it, and it would give the repository a readable history. We
  didn't choose it for now, because the release commit's body is already what
  the tag job publishes, and a second copy the person edits separately would
  drift from it. Adding it later means dropping `--draft`.
- Changesets. It is the JavaScript ecosystem's version of the same idea, and it
  needs a Node toolchain in a Python repository. It fits a JavaScript project
  better than this one.

## Consequences

wfctl gains a dev dependency, locked in `uv.lock` like the others. An agent
writes a note directly as a file, or with `uv run towncrier create`, which picks
the `.2` suffix when a note for the issue already exists.

A note's category lives in its file name, so a typo such as `571.feature.md`
is caught by the check rather than by the release.

The `none` notes are committed and then deleted unread at release time. They
exist so the check can tell a skipped note from a change with nothing to say,
and the release notes never show them.

## Verification

The check script has tests for five cases: a branch with no note fails, a branch
with a note for its own issue passes, a stacked branch carrying only its
parent's note fails, a note with an unknown category fails, and `main` passes.

A dry run of the release script against notes copied from 0.23.0's changes
prints a draft with behaviour changes first and no `none` section, and leaves
the working tree unchanged.

## Log

- 2026-10-14  proposed  — #571. Andre chose towncrier after a preview built
  from 0.23.0's changes, and this records which parts it takes over.
