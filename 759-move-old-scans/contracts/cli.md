# Contract: `wfctl store scans`

## Synopsis

```
wfctl store scans [--append <file>]... [--overwrite <file>]...
```

The command moves the review scans committed under `<arch-root>/scans/` into
their spec folders, stores each folder it changed, and deletes the moved scans
from the code repository's working tree. It never commits in the code
repository.

## Flags

| Flag | Takes | Repeatable | Effect |
| --- | --- | --- | --- |
| `--append` | a scan's file name, such as `656-plan-review.md` | yes | when that scan's destination exists, add the scan's sections to its end, without the scan's title line |
| `--overwrite` | a scan's file name | yes | when that scan's destination exists, replace it |

Naming one file with both flags is a usage error, exit 2, before anything is
read. A flag naming a file that has no conflict, or isn't a review scan, prints
one line saying it had nothing to apply to, and the run carries on.

## Output

Lines that name a path print without wrapping or markup, as `store specs`
prints them, so a user can copy the path or the command.

**Nothing to move** (exit 0):

```
✓ no review scans in docs/architecture/scans/
```

The path is the repository's own arch root, relative to the repository root
when it sits inside it.

**Spec root isn't a store with a branch** (exit 1, nothing read or written):

```
✗ nothing moved: the spec root /path/to/specs is inside the code repository — not committed, not backed up
```

The text after the path is the store's own `not_applicable` or `detached`
wording for that layout.

**Otherwise**, a rich table, a summary line, then one block per scan needing
attention:

```
Scans moved to origin/specs-trunk

  Spec folder                      clarify  plan review  analyze  Stored
 ─────────────────────────────────────────────────────────────────────────
  109-record-leads-with-drawing       ✓          –          ✓       a1b2c3d
  412-clean-code-skill                ✓          –          ✓       a1b2c3d
  649-design-checks-by-context        ✓         ✓ ⚠         ✓       a1b2c3d
  650-bob-pr-review-guard (new)       –          ✓          ✓       ✗ not pushed
  711-…                               –          –          ✓       – not tried

✓ 109 moved · ✗ 3 kept, not stored · ⚠ 1 needs a choice

⚠ 656-plan-review.md → 649-design-checks-by-context/scans/plan-review.md already exists
    add it to the end:  wfctl store scans --append 656-plan-review.md
    replace it:         wfctl store scans --overwrite 656-plan-review.md

✗ 121-clarify.md: no spec folder starts with 121-

✗ 650-bob-pr-review-guard: <the store's own report_lines for not_pushed, with `wfctl store scans` in place of `wfctl store specs`>
```

Cell values:

| Column | Value | Meaning |
| --- | --- | --- |
| step | `✓` | written, appended, overwritten, or already there, and stored |
| step | `✗` | ready, but the folder's store failed |
| step | `⚠` | conflict, kept |
| step | `–` | no scan for this step |
| Stored | short SHA | the commit the store made or found |
| Stored | `committed, not pushed` | the store has no upstream |
| Stored | `✗ <label>` | the store failed; the label per outcome is in research R8, such as `✗ not pushed` |
| Stored | `– not tried` | an earlier folder's failure stopped storing (research R8) |

When two scans share a step's destination, the cell shows one mark per scan
in the order they were written, such as `✓ ⚠` for #649's written plan review
and #656's conflict. The block under the table names the scan behind each `⚠`.

The first failed store stops storing for the rest of the run (FR-014), so a
run has at most one. Under the blocks for scans, the store's own
`report_lines` for it print once, with `wfctl store scans` in place of `wfctl
store specs` (research R8).

The title names the store's upstream, such as `origin/specs-trunk`, or its
branch when it has no upstream.

## Exit codes

| Code | When |
| --- | --- |
| 0 | every review scan moved and was stored, or none were left |
| 1 | the spec root isn't a store with a branch, a scan couldn't be placed, a conflict is unsettled, or a folder's store failed |
| 2 | usage error, such as one file named with both flags |

## What it never does

- Commit, stage, or push in the code repository.
- Touch a file under `<arch-root>/scans/` whose name isn't a review scan name.
- Write over an existing destination without `--append` or `--overwrite`.
- Delete a scan whose folder wasn't stored, or a scan left as a conflict in a
  folder that was.
