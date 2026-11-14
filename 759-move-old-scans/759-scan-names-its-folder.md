---
status: proposed
governs: evidence-and-derivation, architecture-records
---

# Old scans move to the spec folder they name

## Context

The `wfctl store scans` command moves the review scans committed under
`<arch-root>/scans/` into each feature's spec folder, as `scans/<step>.md`.
To do that, it has to find the spec folder for each scan.

A scan's file name carries only the issue number and the step, such as
`649-plan-review.md`. A spec folder is named for its branch, such as
`649-design-checks-by-context`. Matching the two by issue number works for most
scans, but fails in three cases:

1. #40 has two spec folders, `40-save-uncommitted-on-remove` and `40-scratch`.
2. `656-plan-review.md` is a re-review of #649's plan, so it belongs in
   `649-design-checks-by-context`, and no folder starts with `656-`.
3. #650's scans were written on another machine. Their folder,
   `650-bob-pr-review-guard`, isn't in this spec store.

Every scan section opens with a `Detail` line, naming the file where the review
wrote its details. That path includes the spec folder.

We decided in `scans-live-in-spec-folder` that review scans are stored in the
spec folder. This record decides only how the command finds an old scan's
folder.

## Verified

- In wfctl, 114 of the 117 files under `docs/architecture/scans/` are review
  scans, from 46 issues. The other three are `424-evaluation.md`,
  `571-evaluation.md`, and `426-spike.md`.
- 110 review scans have a `Detail` line naming a spec folder, such as
  `- Detail: /Users/…/wfctl-specs/412-clean-code-skill/spec.md
  § Clarifications`. Some wrap the path in backticks, or start it with
  `<spec-root>/`, as #299, #307, #325, and #352 do. The other 4 name no
  folder: `121-clarify.md`, `121-analyze.md`, `188-clarify.md`, and
  `711-analyze.md`.
- No scan names more than one folder across its `Detail` lines, and no
  `Detail` path has more than one segment shaped like `<issue>-<slug>`.
- pfms's `dev` branch has 89 review scans with the same file names. Every `Detail` path names
  one folder under `pfms-specs/`, except three scans, `636-analyze.md`,
  `636-clarify.md`, and `645-clarify.md`, whose `Detail` says
  `$FEATURE_DIR/…`. Each of those three has exactly one spec folder starting
  with its issue number.
- For every scan that names a folder, the folder starts with the scan's own
  issue number, except `656-plan-review.md`, which names
  `649-design-checks-by-context`.
- Every named folder exists in the spec store except `650-bob-pr-review-guard`.
  Its `Detail` lines start with `/esw/rch/san5/aamarin/wfctl/specs/`.
- Each of the 4 scans with no folder in its `Detail` line has exactly one
  spec folder starting with its issue number.
- `wfctl/_spec_store.py`'s `store` function takes the path of the spec folder
  to store and uses the branch name only for the commit subject. So it can
  store another branch's folder.
- `wfctl/_evidence.py`'s `scan_reason` function reads the whole scan file for a
  `Verdict` line and a coverage row. So a file with two appended review sections
  still counts as a scan that ran.

## Assumed

- The spec folder named in a scan's `Detail` line is the one the scan reviewed.
  If a scan points at the wrong folder, the command moves it there. Even so, the
  scan's own text is the closest evidence of what it reviewed.

## Direct baseline

Match by issue number alone. For `<n>-<step>.md`, the command
looks for spec folders whose name starts with `<n>-`. If it finds exactly one,
it moves the scan there. Otherwise, it reports the scan. This needs no parsing
of the scan.

In wfctl, this moves 108 of the 114 review scans. It reports #40's three scans
as ambiguous, and `656-plan-review.md` and #650's two scans as having no
folder.

## Decision

The command reads the scan's `Detail` lines first. If they name a spec folder,
the command moves the scan there and creates the folder if it doesn't exist yet.
If no `Detail` line names a folder, the command falls back to the issue number.
It moves the scan only when exactly one folder matches.

In wfctl, this places all 114 review scans. #40's scans go to
`40-save-uncommitted-on-remove`, `656-plan-review.md` goes to
`649-design-checks-by-context`, and the command creates `650-bob-pr-review-guard`
for #650's two scans.

## Diagram

The decision is built to handle a scan whose issue number doesn't match its
folder, such as a re-review filed under a follow-up issue, or a branch renamed
after its scan was written.

```
          baseline                              decision

        ┌──────────────────────┐            ┌──────────────────────┐
        │ spec folders on the  │            │ spec folders on the  │
        │ spec store           │            │ spec store           │
        └──────────────────────┘            └──────────────────────┘
               ▲ matches by                   ▲ named by    ▲ matches by
               │ issue number                 │ Detail      │ issue number
               │                              │ (new)       │ (fallback)
════ code repo / spec store ════════════════════════════════════════════
               │                              │             │
        ┌──────┴───────────────┐            ┌─┴─────────────┴──────┐
        │ <n>-<step>.md        │            │ <n>-<step>.md        │
        │ file name            │            │ Detail line, then    │
        │                      │            │ file name            │
        └──────────────────────┘            └──────────────────────┘
```

The divider is the boundary between the code repository and the spec store,
drawn in `scans-live-in-spec-folder`. The decision adds one arrow, from the
scan's `Detail` line to its folder, and keeps the issue number as the fallback.
When a scan's issue number differs from its folder's, the baseline's only arrow
fails. The decision handles that scan with the new arrow and no code change.

## Considered

- **Issue number alone**, the baseline. We didn't choose this because it leaves
  six of wfctl's scans for the user to move by hand. Those six are the cases the
  command exists to move automatically.
- **A mapping file or a `--folder` flag the user fills in.** We didn't choose
  this because the scans already name their folders. A hand-written mapping
  would duplicate that and could contradict it.
- **Skip a scan whose named folder is missing, instead of creating the folder.**
  We didn't choose this because the folder name comes from the scan, so creating
  the folder doesn't invent a name. Skipping it would leave #650's scans in the
  code repository with no way to move them.

## Consequences

Every review scan in wfctl moves without a manual step. A folder the command
creates holds only scans, with no spec. `wfctl status` never reads that folder,
since no branch uses it as its spec folder.

The command now depends on the `Detail` line's format. If a `Detail` line
names no folder, the command falls back to the issue number. The command takes
the first path segment shaped like `<issue>-<slug>` as the folder, so a path
with such a segment above the spec folder would send the scan to the wrong
folder. For example, an in-repo `specs/` inside a worktree named `656-foo`
gives `…/wt/656-foo/specs/649-bar/plan.md`, and the command would take
`656-foo`. No scan in wfctl or pfms has a path like
that, so the command doesn't check for it.

## Verification

- A test moves a scan whose `Detail` line names a folder different from its
  issue number into the named folder.
- A test falls back to the issue number for a scan with no folder in its
  `Detail` line, and reports a scan whose issue number matches two folders.
- A test creates the folder a scan names when the spec store doesn't have it.
- After the move in wfctl, `649-design-checks-by-context/scans/plan-review.md`
  holds #649's three review sections and #656's, and `wfctl status`, pointed at
  `412-clean-code-skill` and `40-save-uncommitted-on-remove` with
  `WFCTL_SPEC_DIR`, reads their clarify and analyze scans.

## Log

- 2026-11-13  proposed  — #759. The old review scans move to their spec
  folders, and six of them can't be placed by issue number alone.
