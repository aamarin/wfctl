# Data model: Design exceptions move to the spec folder

## The exceptions folder

Every exception a branch makes lives in one folder inside its spec folder:

```text
<spec folder>/exceptions/
├── boundary.md                    # at most one: the boundary exception
├── brainstorm.ui-design.md        # one per pass exception, <step>.<pass>.md
└── plan.plan-walkthrough.md
```

`_design_exceptions.folder(spec_dir)` returns this path, and no other code builds it.

## Boundary exception

- **File**: `exceptions/boundary.md`.
- **Written by**: `wfctl arch none --reason "…"`, through
  `_design_exceptions.write(spec_dir, "boundary", reason)`.
- **Body**: `# No new boundary\n\n<reason>\n`.
- **Read by**: `_design_exceptions.boundary(spec_dir)`, which returns the reason or
  `None`. The brainstorm gate (`_evidence._architecture_answered`) and the
  session summary (`cli._observe`) call it.
- **Rules**:
  1. A second `arch none` replaces the reason.
  2. An empty reason or a `<placeholder>` is refused before anything is
     written.

## Pass exception

- **File**: `exceptions/<step>.<pass>.md`.
- **Written by**: `wfctl step none <step>.<pass> --reason "…"`, through
  `_design_exceptions.write(spec_dir, "<step>.<pass>", reason)`.
- **Body**: ``# `<step>.<pass>` does not apply\n\n<reason>\n``.
- **Read by**: `_design_exceptions.passes(spec_dir)`, which returns
  `{"<step>.<pass>": reason}` for every `*.*.md` file. The pipeline calls it.
- **Rules**:
  1. A second exception on the same pass replaces that file only.
  2. An exception on another pass adds a file.
  3. The pass must be declared in `wfctl.json`, or the command refuses.
  4. `boundary.md` has no dot before `.md`, so `passes` never returns it.

## `_design_exceptions` module

```python
BOUNDARY = "boundary"

def folder(spec_dir: Path) -> Path: ...
def path(spec_dir: Path, name: str) -> Path: ...
def write(spec_dir: Path, name: str, reason: str) -> Path: ...
def boundary(spec_dir: Path) -> str | None: ...
def passes(spec_dir: Path) -> dict[str, str]: ...
```

- `path` returns `folder(spec_dir) / f"{name}.md"` without touching the disk.
  `write` writes to it, and `_record_gate` prints it in the `rm` line of its
  refusal.
- `write` creates `spec_dir` and the exceptions folder when missing, writes with
  `write_atomic`, and returns the path it wrote. It doesn't validate the
  reason. The commands do that, since each prints its own refusal.
- `boundary` and `passes` return `None` and `{}` when the folder or file is
  missing. Neither raises on a missing folder.
- The title for each exception is chosen inside `write` from `name`, so the
  header format and the parser that strips it live in one file.

## "Moves a boundary?" PR section

- **Lives in**: the PR body, under `## Moves a boundary?`.
- **Required by**: `wfctl.json`'s `change_sections`, in this repo only.
- **Checked by**: `wfctl check-body`, using the rules it already applies to
  "Needs a spec?": missing, empty, N/A, None, or a bare yes or no is a finding.
- **Content**: yes or no with a reason, then one line per pass exception.
- **Agreement**: `check-body` reports every exception in the spec folder whose
  reason isn't in the body, in any repo, after collapsing whitespace in both
  (research R12). It finds the reason anywhere in the body, so it names no
  heading. It skips an inherited boundary exception when the branch changes a
  level-2 record, since that record answers the boundary question for the
  sub-issue. An inherited exception is one in a spec folder that isn't named
  after the branch (research R12, FR-015).

## The guard's record checks

The worktree guard reads two facts at the commit `gh pr create` or
`gh pr merge` acts on:

1. **Touched records**: the level-2 records the branch changes, from
   `git diff --name-only --diff-filter=d <trunk>...<commit>`, with `<trunk>`
   the value `trunk_branch` returns. A path counts only when its parent is the
   arch root and it ends in `.md`, which is the set `_branch_records` reads
   for the "architecture accepted" fact. Level-3 records, views, scans, and
   deleted files are left out. Each one's status comes from `git show`.
2. **Own boundary exception**: a boundary exception in a spec folder named
   after the branch. An epic's folder that a sub-issue falls back to isn't the
   sub-issue's own.

It refuses when either rule holds:

1. The branch has its own boundary exception and touches any record (R13).
2. A touched record's status isn't `accepted`, `superseded`, `rejected`, or
   `retired` (R14). That set is `_arch.RULED_ON`, moved from `_evidence.py`.

## Removed

- `docs/architecture/declarations/` and its 15 files.
- `docs/architecture/step-claims/`. Its 5 files move to their branches' spec
  folders (research R10).
- `_pipeline._step_claims`.
- `STEP_CLAIMS_DIR` (research R4).

The new `DECLARATIONS_DIR` is in `_paths.py`, listed in `non_record_subtrees`,
so a declaration an older wfctl writes still answers nothing (FR-007).
