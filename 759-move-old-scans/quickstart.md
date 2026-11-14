# Quickstart: Move the old review scans into their spec folders

## Run it in wfctl

From this worktree, once the command is implemented:

```bash
uv run wfctl store scans --append 656-plan-review.md
```

`656-plan-review.md` re-reviews #649's plan, and scans run in ascending issue
order, so #649's plan review is written first and #656's appends to it in the
same run. Every other scan has no conflict.

Then check the success criteria:

```bash
ls docs/architecture/scans
```

SC-001: this lists exactly `424-evaluation.md`, `426-spike.md`, and
`571-evaluation.md`.

```bash
git -C <spec root> fetch origin specs-trunk
git -C <spec root> ls-tree -r --name-only origin/specs-trunk | grep -c '/scans/'
```

SC-002: the count includes all 114 moved scans, beside the scans written after
#598. `649-design-checks-by-context/scans/plan-review.md` holds #649's review
sections and then #656's.

```bash
WFCTL_SPEC_DIR=<spec root> wfctl status
```

SC-003: run with `WFCTL_BRANCH` set to `412-clean-code-skill`,
`40-save-uncommitted-on-remove`, and `649-design-checks-by-context` in turn.
None of their clarify, plan review, or analyze lines reads `no scan file`.

The branch then commits the deletions under `docs/architecture/scans/`.

## Run it in pfms

After the release that ships the command, the user runs `wfctl store scans`
in pfms. It stores into `pfms-specs` through the same layout check. pfms's `dev`
branch has 89 review scans with the same file names, and every `Detail` path names one
folder under `pfms-specs/`, except three that say `$FEATURE_DIR/…` and fall
back to the issue number. A scan it
can't place stays where it is and is listed, and a rerun picks up the rest.

## Test map

Each acceptance scenario in `spec.md` gets one test in
`tests/test_store_scans.py`.

| Scenario | Test needs |
| --- | --- |
| US1-1 `Detail` names the folder | code repo, spec store with a bare remote |
| US1-2 `Detail` names another issue's folder | placement only, no git |
| US1-3 no `Detail` folder, one match | placement only |
| US1-3 a `Detail` path in backticks gives the folder name without them | placement only |
| US1-4 named folder missing, created | spec store with a bare remote |
| US1-5 evaluation and spike untouched | placement only |
| US1-6 table and summary, exit 0 | CLI runner, `NO_COLOR` |
| US2-1 conflict kept, both commands printed, exit 1 | CLI runner |
| US2-2 `--append` keeps the old content and adds the sections | spec store |
| US2-3 `--overwrite` replaces it | spec store |
| US2-4 appended file reads as a scan in `scan_reason` | file only |
| US3-1 the second of three folders fails to store: the first moves, the third shows `– not tried`, and the remedy lines name `wfctl store scans` | spec store whose remote is moved away after the first store |
| US3-2 two folders match | placement only |
| US3-3 no folder matches | placement only |
| US3-4 spec root inside the code repository | code repo only |
| US3-5 rerun after a failed store writes nothing twice, including a destination holding one scan with a second appended to it | spec store, two runs |
| Edge: `--overwrite` on a destination an earlier scan wrote in the same run is held, and the earlier scan is stored | spec store with a bare remote |
| SC-004 a conflict beside a ready scan in one stored folder: only the ready scan is deleted | code repo, spec store with a bare remote |
| US3-6 nothing left | code repo only |
| Edge: two scans in one run, ascending order | placement and write, no git |
| Edge: unused flag | CLI runner |
