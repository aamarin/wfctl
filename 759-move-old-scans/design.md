# Move the old review scans into their spec folders

Contexts: evidence-and-derivation, architecture-records

## Problem Statement

Every clarify, plan review, and analyze scan sits in its feature's spec folder,
next to the spec, plan, and tasks it reviewed. The code repository keeps only
evaluation and spike scans under `<arch-root>/scans/`, so a reader can tell from
that folder which convention is current.

Since #598, new review scans go to the spec folder. The 114 committed before
that are still in wfctl's `docs/architecture/scans/`, and pfms has its own set
in a code repository whose specs live in a separate `pfms-specs` repository.

## Recommended Direction

A new command, `wfctl store scans`, moves the old review scans in whatever
repository it runs in. It sits beside `wfctl store specs` and `wfctl store
reviews`, and it stores each folder through the same spec store code `store
specs` uses. That's why it works for pfms's separate spec repository without
wfctl knowing about it. A one-time script would have had to be run in pfms from
this repository, or copied there.

For each review scan under `<arch-root>/scans/`, the command does four things,
in this order:

1. It finds the spec folder. It reads the folder from the scan's `Detail`
   lines, and falls back to the issue number in the file name when no `Detail`
   line names a folder. With the fallback, it moves the scan only when exactly
   one folder matches. `docs/architecture/design/759-scan-names-its-folder.md`
   records why.
2. It writes the scan to `<folder>/scans/<step>.md`, creating the folder when
   the `Detail` line names one the spec store doesn't have.
3. It stores each folder it wrote to, using the spec store code.
4. Only after a folder is stored, it deletes that folder's scans from the code
   repository's working tree. The branch commits the deletion.

Evaluation and spike scans, such as `424-evaluation.md` and `426-spike.md`, are
never touched.

The command is temporary. Once pfms has run it after a release, a later release
removes it, since a repository set up after #598 has no old scans to move.

### Output

The command prints a table grouped by spec folder, built with rich, then a
summary line, then one block for each scan that needs a choice.

```
Scans moved to origin/specs-trunk

  Spec folder                      clarify  plan review  analyze  Stored
 ─────────────────────────────────────────────────────────────────────────
  109-record-leads-with-drawing       ✓          –          ✓       a1b2c3d
  412-clean-code-skill                ✓          –          ✓       ✗ unreachable
  649-design-checks-by-context        ✓          ⚠          ✓       a1b2c3d
  …

✓ 111 moved · ✗ 2 kept, not stored · ⚠ 1 needs a choice

⚠ 656-plan-review.md → 649-design-checks-by-context/scans/plan-review.md already exists
    add it to the end:  wfctl store scans --append 656-plan-review.md
    replace it:         wfctl store scans --overwrite 656-plan-review.md
```

Each state, and what it prints:

1. Nothing left to move: `✓ no review scans in docs/architecture/scans/`, exit 0.
2. Every scan moved and stored: the table and the summary, exit 0.
3. A folder's store fails: its row shows the store's own reason, such as
   `✗ unreachable`, and its scans stay in the code repository. Exit 1.
4. The destination file already exists: the scan is not written, and the
   command prints the two commands that settle it. Exit 1.
5. No folder can be found for a scan: the scan stays and is listed with the
   reason, either no folder for that issue or more than one. Exit 1.
6. The spec root isn't a spec store, such as a repository whose specs sit
   inside the code repository: `✗ nothing moved: the spec root <path> is inside
   the code repository`, exit 1. Moving the scans there would leave them
   uncommitted and backed up nowhere.

A rerun picks up whatever is left, since a moved scan is gone from the code
repository and a kept one is still there.

### When the destination already exists

The command never picks for the user. A scan whose destination exists stays
put until the user names it with one of two flags, each taking a file name and
repeatable:

1. `--append <file>` adds the old scan's dated sections to the end of the
   existing file, without its title line. A scan file is already one dated
   section per review, and the step reader reads the whole file, so the
   appended sections count.
2. `--overwrite <file>` replaces the existing file.

In wfctl the one case is `656-plan-review.md`, a re-review of #649's plan,
which goes in with `--append` after #649's own plan review.

## Boundaries and Ownership

No boundary moves. `scans-live-in-spec-folder` already gives review scans to
the spec folder and reads them there. This branch amends that record's
Consequences, which had kept the old scans in the code repository.

1. The command decides which folder a scan goes to, from the scan's own text.
   The agent shouldn't decide that per scan, since 114 hand decisions are where
   a scan lands in the wrong folder unnoticed.
2. The spec store code decides whether a folder is stored, by asking git, as
   `spec-storage-read-from-git` requires. The command deletes a scan from the
   code repository only after that answer is yes, so a failed store never
   leaves the scan in neither place.
3. The user decides each conflict. The command can't tell whether two scans for
   one file are a re-review or a mistake.

## Software design decisions

- docs/architecture/design/759-scan-names-its-folder.md — an old scan moves to the spec folder its `Detail` line names, and falls back to the issue number

## Key Assumptions to Validate

- [ ] `store()` in `wfctl/_spec_store.py` stores a folder other than the
  current branch's. Checked by reading it: it takes the folder's path and uses
  the branch only in the commit subject. A test confirms it.
- [ ] Storing 46 folders one at a time is fast enough. Each store fetches and
  pushes, so expect a minute or two. If it's much slower, commit every folder
  first and push once.
- [ ] pfms's scans use the same file names and `Detail` lines. This can't be
  checked from this worktree. If it's wrong, the command reports those scans and
  moves nothing for them.
- [ ] An appended plan review still reads as done in `wfctl status`. Checked in
  `scan_reason`, which reads the whole file. A test confirms it.

## MVP Scope

In scope:

1. The `wfctl store scans` command, with `--append` and `--overwrite`.
2. Running it in wfctl, which moves all 114 review scans, creates
   `650-bob-pr-review-guard`, and appends #656's review to #649's.
3. The amendment to `scans-live-in-spec-folder`.
4. Deployment notes in the PR saying to run the command in pfms after the
   release.

## Not Doing (and Why)

- **Moving evaluation and spike scans.** They are a spike's deliverable, read
  by the PR reviewer, and two records link to `571-evaluation.md`.
- **Taking `scans/` off `_paths.non_record_subtrees`.** The evaluation and spike
  scans still live there.
- **A third conflict option that keeps both files side by side.** The step
  reader would never read the second file, so it would be kept and ignored.
- **Running the command in pfms from here.** The worktree guard refuses work in
  another checkout, and the user runs it there after a release.
- **Rewriting the old scans' `Detail` paths.** They record where the detail was
  written at the time, and some point at another machine.

## Open Questions

None. The user settled the last two on 2026-11-13: scans with no unique folder
by issue number are handled in this PR, #650's folder is created, and conflicts
take `--append` or `--overwrite` with no default.
