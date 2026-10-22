---
status: proposed
---

# A wfctl command checks the boundary answer, and a repository lists it in `verify`

## Context

`every-change-answers-boundary-question` decides that `wfctl verify` fails a
branch that hasn't answered the boundary question. This record decides where the
code that checks it lives.

The design step already has this check. It counts a branch as having answered
when the branch touches any file under the architecture root, except in the
`design/` folder and the folders that record no decision, such as `scans/`. That
list of folders has grown before. `implementation/` was added after `scans/`,
and every place that read the root had to be found and updated (#370).

## Verified

- `wfctl/_evidence.py:811`, `_architecture_answered`, calls
  `touched_on_this_branch` with `exclude=[*non_record_subtrees(arch), arch /
  DESIGN_DIR]`.
- The same function returns early when `spec.md` exists, so a branch that
  reached `specify` always passes it. The new check can't reuse it as it is.
- `.github/scripts/check_release_note.py` is this repository's release-note
  check. `wfctl.json` lists it in `verify`, and CI runs it with the system
  `python3` as its own `release-note` job.
- `check_release_note.py:27` matches a release branch with
  `^release/v(\d+)\.(\d+)\.(\d+)$`, and it skips `main`.
- `wfctl/_paths.py:531`, `touched_on_this_branch`, checks uncommitted files
  first and then `trunk...HEAD`. Its docstring says this is for "a record
  written moments ago and not yet committed". The new command has to count
  committed files only, since an uncommitted declaration never reaches a
  reviewer.

## Assumed

- CI can run a `wfctl` command. The `release-note` job doesn't set up the
  project, so a job that runs the command needs `uv sync` first.

## Direct baseline

A script beside the release-note check, `.github/scripts/check_boundary_answer.py`,
listed in `verify` and run as its own CI job. It runs `git diff` against `main`
over the architecture root and leaves out its own copy of the folders that don't
count.

## Decision

wfctl gets a command that answers whether the branch has answered the boundary
question. It shares the design step's list of folders that don't count, and
differs from the design step in two ways: it has no early return on `spec.md`,
and it counts committed files only. A repository turns it on by listing the command in `verify`. A
repository states its own exemptions, such as release branches, in that entry or
in `wfctl.json`, because wfctl doesn't know how a project names them.

## Diagram

```
                 baseline                                 decision

stable   ┌───────────────────────────┐          ┌───────────────────────────┐
         │ wfctl: folders that       │          │ wfctl: folders that       │
         │ don't count (one list)    │          │ don't count (one list)    │
         └─────────────▲─────────────┘          └──────▲────────────▲───────┘
                       │ reads                         │ reads      │ reads
         ┌─────────────┴─────────────┐          ┌──────┴──────┐ ┌───┴──────────────┐
         │ design step's check       │          │ design step │ │ boundary command │ (new)
         └───────────────────────────┘          └─────────────┘ └───▲──────────────┘
════ wfctl / this repository ══════════════════════════════════════╪══════════════════
         ┌───────────────────────────┐                             │ runs
volatile │ check_boundary_answer.py  │                    ┌────────┴─────────┐
         │ (its own copy of the list)│                    │ wfctl.json verify│
         └─────────────▲─────────────┘                    └──────────────────┘
                       │ runs
         ┌─────────────┴─────────────┐
         │ wfctl.json verify         │
         └───────────────────────────┘
```

The two graphs differ by where the list of folders lives. In the baseline there
are two lists, one in wfctl and one in the script. In the decision there is one,
and both checks read it. The change this is built to absorb is a new folder
under the architecture root that records no decision. In the baseline, it edits
wfctl and the script, and a missed edit makes `verify` and the design step
disagree about the same branch. In the decision, it edits the one list.

## Considered

- **The direct baseline above.** It follows the release-note check exactly, which
  is the precedent this repository accepted. We didn't choose it because the
  release-note check owns its whole rule, while this script would copy a rule
  wfctl already owns. A copy can go out of date the next time a folder is
  added, the same way #370 found.
- **A fact in `wfctl status` that every repository gets automatically.** Every
  repository would be checked with no setup. We didn't choose it because a
  repository whose design practice we don't control would start failing
  branches it never agreed to check. Listing the command in `verify` is the
  same opt-in as every other check in that list.
- **Reuse `_architecture_answered` as it is.** It is the shortest path. We
  didn't choose it because it returns early when `spec.md` exists, so it can't
  tell a full-pipeline branch that answered from one that didn't.

## Consequences

Projects that use wfctl get the check by adding one line to `verify`, without
copying this repository's script.

The CI job for the check needs the project set up, which the `release-note` job
skips. Making the job required also means editing `.github/rulesets/main.json`,
which Andre applies by hand.

## Verification

- A test runs the command on a branch with no answer and on a branch with a
  committed `arch none`, and checks that it fails the first and passes the second.
- A test adds a folder name to the list of folders that don't count, and checks
  that the design step and the new command both stop counting it.
- A test runs it on a release branch with the exemption set, and on `main`.

## Log

- 2026-10-22  proposed  — #628: the boundary answer needs a check outside the
  design step, and the design step's reader is the one to share
