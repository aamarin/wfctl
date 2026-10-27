# Implementation Plan: A required CI check fails a PR while a review group has unreviewed commits

**Branch**: `627-ci-review-check` | **Date**: 2026-10-25 | **Spec**: `spec.md` in this feature directory
**Input**: Feature specification from `spec.md` in this feature directory

## Summary

When a review run completes, or a person signs off, wfctl adds a line to a git
note on that commit and pushes `refs/notes/wfctl-review` to `origin`. A new
`review` job on GitHub reads those notes, works out which commits on the PR no
review covers, and fails while any group has one. The `main` ruleset requires
the job. GitHub runs `main`'s copy of the job and `main`'s wfctl, so a PR can't
weaken its own check by accident.

CI requires every review group `main`'s `wfctl.json` lists, plus any group
the PR's own `wfctl.json` adds (R13). A group the PR removes still needs its
review on that PR. The guard and the sign-off require the same list, so a PR
that passes locally passes in CI, as long as the local `origin/main` is
current (R13). `wfctl review start` can also run a group
that's only in the uncommitted `wfctl.json`, which lets a user try a new group
before it's required.

CI measures against the branch the PR targets, which GitHub reports in the
event, and ignores any `trunk` key in the PR's `wfctl.json` (R14). That way a
PR can't skip review by naming its own branch as trunk, and a stacked PR is
measured against its parent's branch.

The local check and CI count with one function. `unreviewed` stops reading the
state directory and takes each group's last reviewed commit and the signed-off
commits as arguments. A state directory reader builds them for the guard and
`wfctl review sign-off`, and a notes reader builds them for CI.

After any notes push, wfctl reruns the PR's failed `review` job, since pushing
a notes ref doesn't start a CI run. If that rerun fails, wfctl warns and the
user reruns the check by hand (R8). `wfctl store reviews` resends notes that
didn't reach GitHub, joining them with the remote notes when the push is
rejected. The worktree guard refuses an agent's hand-written notes and pushes
of any notes ref.

Design records read before this plan (via `reading-design-records`):

```
Design records: 3 listed in design.md
  docs/architecture/design/627-unreviewed-takes-coverage.md
  docs/architecture/design/627-review-note-line-per-event.md
  docs/architecture/design/627-guard-blocks-note-writes.md
```

The accepted level-2 record `review-record-in-git-notes` is the boundary this
plan implements, and `review-covers-unreviewed-commits` sets the range rules
both sides share. The #642 records `642-commit-range-takes-judged-branch` and
`642-origin-head-trusted-on-full-fetch` shape how CI finds the trunk.

## Technical Context

**Language/Version**: Python 3.11+ (CI runs 3.11 and 3.13)
**Primary Dependencies**: `typer` and `rich` for the CLI; no new dependency.
`git` and `gh` run as subprocesses. The guard path keeps importing neither
`typer` nor `rich`.
**Storage**: git notes under `refs/notes/wfctl-review`, one plain line per
event. The state directory records under `<state dir>/reviews/` stay as they
are. See `data-model.md`.
**Testing**: `uv run pytest -q`, `uv run ruff check wfctl/ tests/`, and
`uv run mypy`. Scratch repositories with a bare `origin` cover the push, the
rejected push, and the two readers. `gh` is stubbed for the rerun. The job
itself is checked on a throwaway PR after merge (quickstart.md).
**Target Platform**: the `wfctl` CLI on macOS and Linux, and an
`ubuntu-latest` GitHub Actions runner for the job.
**Project Type**: CLI, plus one GitHub Actions workflow in this repository.
**Performance Goals**: the CI job finishes in under a minute on this
repository. Counting reuses `commit_range`, which costs a few git calls per
group plus up to three per merge in the range.
**Constraints**: the job never runs code from the PR's checkout (FR-017a).
wfctl makes no outward write beyond the notes push and the job rerun, and
records the push as an outward action. Minimal-complexity bias.
**Scale/Scope**: one repository with one user today. Two default groups plus
any custom ones, and PRs of tens of commits.

## Constitution Check

_GATE: Must pass before Phase 0 research. Re-check after Phase 1 design._

The repository has no `.specify/memory/constitution.md`. The gates below come
from `AGENTS.md` and from the accepted records `wfctl arch context` prints,
and Complexity Tracking records the substitution.

- [x] Validation plan exists: the three `uv run` commands, the new tests named
      under Project Structure, `uv run wfctl verify`, and the post-merge
      throwaway PR in `quickstart.md`.
- [x] Complexity is justified: one new module for notes, and a second
      workflow file because the job needs a different trigger from `ci.yml`.
      Research R4 and R5 give the reasons.
- [x] Ownership is stated:
      1. The local machine writes the notes, because only it knows a run
         completed or a person signed off.
      2. CI computes the unreviewed commits, because only GitHub sees the PR's
         actual head, including an "Update branch" merge no local machine
         made.
      3. The local machine reruns the job, because only it knows when the
         notes arrived.
- [x] `review-record-in-git-notes`: notes under `refs/notes/wfctl-review`,
      pushed to `origin`, and the guard keeps reading the state directory.
      The record's Consequences said the CI job runs the PR's own wfctl and
      reads the PR's groups. R4 and R13 reverse both, so the record carries a
      2026-10-25 `revised` Log entry and Consequences that say GitHub runs
      `main`'s job and wfctl, and that CI requires `main`'s groups plus the
      PR's additions.
- [x] `review-covers-unreviewed-commits`: CI reuses `commit_range`, so its
      range starts where the last reviewed commit or the merge base says.
- [x] `a-rule-is-expressed-as-a-check`: the review rule now has a check
      GitHub enforces, beyond the guard's text match.
- [x] `wfctl-runs-the-verification`: unchanged. The job reports a verdict
      from git data, and the agent certifies nothing.
- [x] `change-carries-release-note`: `changes/627.addition.md`.
- [x] Outward actions are recorded: each notes push is recorded with
      `record_outward_action`, as `store specs` records its push.

Re-checked after Phase 1: the trigger decision (R4), the group list (R13),
and the base branch (R14) changed what `review-record-in-git-notes` said
about CI, and the record was revised to match. Every other gate is unchanged.

## Project Structure

### Documentation (this feature)

```text
<FEATURE_DIR>/
├── plan.md              # This file
├── research.md          # Phase 0
├── data-model.md        # Phase 1
├── quickstart.md        # Phase 1
├── contracts/
│   ├── cli.md           # check reviews, store reviews, and the changed commands
│   ├── review-note.md   # the note format
│   └── review-job.md    # the workflow job and its trust rules
└── tasks.md             # Phase 2 (/speckit.tasks)
```

### Source Code (repository root)

```text
wfctl/
├── _review.py           # unreviewed() takes coverage and trunk;
│                        # coverage_from_state() added; trunk_refs takes --base
├── _review_config.py    # parse a wfctl.json's text; the FR-015 group list
├── _review_notes.py     # new: record a line, read coverage, send, rerun
├── _review_gate.py      # notes-write and notes-push refusals in read();
│                        # _judge takes groups from the FR-015 list
├── _hook.py             # substring test adds "notes" and "--mirror"
└── cli.py               # check reviews, store reviews; review check and
                         # sign-off record and send notes; review start,
                         # check, groups, sign-off, and relay use the
                         # FR-010 and FR-010a lists

.github/
├── workflows/review.yml # new: the review job, on pull_request_target
├── workflows/ci.yml     # top-level permissions: contents: read
├── rulesets/main.json   # review added to required checks
└── scripts/release.py   # prints the sign-off command after opening the PR

tests/
├── test_review.py           # unreviewed with passed-in coverage; state reader;
│                            # trunk_refs with --base
├── test_review_config.py    # group list: trunk plus head additions, join by name
├── test_review_notes.py     # new: note lines, notes reader, send and merge,
│                            # rerun with gh stubbed, readers agree (with a
│                            # removed group)
├── test_review_gate.py      # notes refusals and what stays allowed; a removed
│                            # group is required, an uncommitted one isn't
├── test_review_cli.py       # check reviews output and --base, store reviews,
│                            # warnings; review start and groups with a removed
│                            # group; relay's ambiguous letter
├── test_review_workflow.py  # new: the job runs only main's code
├── test_ruleset.py          # reads job names from review.yml as well as ci.yml
└── test_release_script.py   # the printed sign-off command

AGENTS.md                    # required checks, store reviews, notes guard,
                             # release sign-off, recovering from a broken
                             # review key on main (R13)
docs/reference.md            # check reviews and store reviews
changes/627.addition.md
```

**Structure Decision**: notes handling goes in a new `_review_notes.py` beside
`_review.py`. `_review.py` keeps the range rules and the state directory, and
gains nothing that touches a remote. The CI command sits under the existing
`check` group as `wfctl check reviews`, next to `check specs`, and the resend
sits under `store` as `wfctl store reviews`, next to `store specs` (R2).

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
| --- | --- | --- |
| No constitution; gates taken from `AGENTS.md` and the accepted records | The repository keeps its rules there | Gates borrowed from another project would be false |
| A second workflow file, `review.yml` | The job runs on `pull_request_target` so GitHub uses `main`'s copy (R4) | Adding that trigger to `ci.yml` would run every job in it on the new event, or need an `if` on each one |
