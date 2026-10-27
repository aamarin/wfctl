---
status: proposed
---

# One module reads and writes design exceptions

## Context

`design-exceptions-live-with-specs.md` moves a branch's design exceptions out of
the architecture folder and into its spec folder. A design exception is a
branch's statement, with a reason, that a design step doesn't apply to it. That
record settles where they live. This one settles how the code that handles them
is organized once they move.

Today that code is spread across four places in three modules:

1. `wfctl arch none` in `cli.py` builds the boundary exception's path and writes its
   header and reason.
2. `wfctl step none` in `cli.py` builds each pass exception's path and writes its
   header and reason the same way.
3. The brainstorm gate in `_evidence.py` decides whether the boundary was
   answered.
4. `_step_claims` in `_pipeline.py` lists the pass exceptions and parses each reason
   back out of the file.

The file format is written in one module and parsed in another. `_step_claims`
strips the header that `step none` writes, and its comment says so. As a result,
changing the format means finding both sides. Moving the files means changing all
four places, since each one builds its own path.

No architecture record constrains how wfctl's own modules are split, so this is
a level-3 choice.

## Verified

- `cli.py` `arch_none_cmd` writes `root / "declarations" / f"{Path(branch).name}.md"`
  with `write_atomic`, and its comment says "Overwritten, not appended: one change
  makes one claim".
- `cli.py` `step_none_cmd` writes `arch_root(repo_root) / STEP_CLAIMS_DIR /
  branch_name / f"{qualified_name}.md"`, where `qualified_name` is
  `f"{step}.{name}"`, with the body `f"# {qualified_name} does not apply —
  {branch_name}\n\n{reason}\n"`.
- `_pipeline.py` `_step_claims` globs `directory.glob("*.md")` and keeps
  everything after the first blank line. Its comment says the header is
  "`wfctl step none`'s own formatting, stripped here rather than duplicated as a
  second parser".
- `_pipeline.py` calls `_step_claims(repo_root, resolve_branch(repo_root))`
  before its `spec_dir is None` arm, so pass exceptions are read whether or not a
  spec folder exists.
- `_evidence.py` `_architecture_answered(spec_dir, repo_root)` already takes the
  spec folder, so it can check a file there without a new argument.
- `_paths.py` `resolve_spec_dir` returns a folder only when `exact.is_dir()`, so
  a branch has no spec folder until something creates it.
- `_spec_store.py` `_store` runs `git("add", "-A", "--", name)`, which stages
  subfolders, so an `exceptions/` folder reaches `specs-trunk` with `design.md`.
- `wfctl/` has no `_design_exceptions.py` today.

## Assumed

- A spec folder that holds only `exceptions/` still reads brainstorm as the current
  step. `arch none` can run before `design.md` exists, and it now creates the
  spec folder. If any reader treats an existing spec folder as evidence that
  brainstorm finished, the pipeline would skip ahead. A test that runs `arch
  none` on a branch with no spec folder and then reads `wfctl status` settles
  it.
- #648 adds a third kind of exception, "no design decision", to the same folder. If
  it needs a different format, such as more fields than a reason, a shared
  format would have to grow a second shape.

## Direct baseline

Change the paths in place and add nothing. Each command builds its new path under
the spec folder and keeps writing its own header. The gate checks for the
boundary file by path. `_step_claims` takes the spec folder instead of the
branch, and keeps parsing the header `step none` writes. A shared constant for
the folder name goes in `_paths.py` beside the others.

## Decision

A new module, `wfctl/_design_exceptions.py`, owns the exceptions folder. It holds five plain
functions, and both commands, both readers, and the worktree guard call them
instead of building paths or parsing files themselves:

1. `folder(spec_dir)` returns `<spec_dir>/exceptions`.
2. `path(spec_dir, name)` returns the file for one exception, such as
   `<spec_dir>/exceptions/boundary.md`.
3. `write(spec_dir, name, reason)` creates the folder if needed and writes one
   exception with `write_atomic`.
4. `boundary(spec_dir)` returns the boundary exception's reason, or `None`.
5. `passes(spec_dir)` returns each pass exception as `<step>.<pass>` mapped to its
   reason.

The worktree guard calls `path` because its refusal prints the command that
removes the boundary exception. Without `path`, the guard would build that file
name itself.

The module keeps the format and its parser side by side, so the header the
commands write and the header the readers strip are defined once.

The folder holds one file per exception:

1. `exceptions/boundary.md` holds the boundary exception. A second `arch none`
   overwrites it, as it does today.
2. `exceptions/<step>.<pass>.md` holds each pass exception. A second exception on a
   different pass adds a file, as it does today (FR-015 of #339).

`boundary.md` can't collide with a pass file, because a pass file name always
contains a dot before `.md`. That's also how `passes` tells them apart: it reads
`*.*.md`, so the boundary exception never shows up as a pass named `boundary`.

The folder is named `exceptions/` after the term the docs use, design
exception, so the docs and the files use the same word. The module is
`_design_exceptions.py` rather than `_exceptions.py`, because in Python a module
named `exceptions` reads as error handling. The pipeline payload's `claimed`
field keeps its name, since renaming it would change the JSON other tools read.

## Diagram

No boundary in force crosses this code, so neither graph has a divider. The
arrows show what each piece of code has to know about the files.

```
                baseline                                decision

  ┌──────────┐            ┌──────────┐       ┌──────────┐      ┌──────────┐
  │ arch none│            │ step none│       │ arch none│      │ step none│
  └──┬───┬───┘            └──┬───┬───┘       └────┬─────┘      └────┬─────┘
   path format             path format          calls             calls
     │   │                   │   │                └──────┬──────────┘
     ▼   ▼                   ▼   ▼                ┌──────▼───────┐
  boundary file          pass files               │  new module  │
     ▲                       ▲   ▲                │ path, format │
   path                    path parse             └──────▲───────┘
     │                       │   │                ┌──────┴──────────┐
  ┌──┴───────┐            ┌──┴───┴───┐          calls             calls
  │   gate   │            │ pipeline │       ┌────┴─────┐      ┌────┴─────┐
  └──────────┘            └──────────┘       │   gate   │      │ pipeline │
                                             └──────────┘      └──────────┘
```

The change this is built to absorb is moving the files or changing their format.
In the baseline, a move touches four `path` arrows and a format change touches
three `format` and `parse` arrows. In the decision, either change touches
`_design_exceptions` alone, and the four `calls` arrows stay as they are. The decision adds
one module and no boundary.

## Considered

- The direct baseline. It's the smallest diff, and it works. We didn't choose it
  because the format would stay split between `cli.py` and `_pipeline.py`, and
  #648 is about to add a third writer and a third reader to the same folder. In
  the baseline that's two more places that each build their own path.
- A `Claim` class, or a storage interface with the file system as its only
  backend. We didn't choose it because there's one place exceptions are stored and
  no second backend planned. Plain functions give the same single home for the
  format without a type every caller has to construct.
- Putting the functions in `_paths.py`. That module resolves paths and already
  holds the subtree constants. We didn't choose it because writing and parsing
  exception files isn't path resolution, and `_paths.py` would gain a file format to
  maintain.
- One file holding every exception, with a section per pass. This keeps the spec
  folder to a single new file. We didn't choose it because each write would have
  to read the file, find its own section, and write the rest back. A bug there
  loses the other exceptions, which is the failure FR-015 split the files to
  prevent.

## Consequences

The commands and the readers share one definition of where exceptions live and what
they look like. A later move or format change is one edit in `_design_exceptions.py`.

`_step_claims` in `_pipeline.py` becomes a call to `_design_exceptions.passes`, and it now
takes the spec folder instead of the branch name. With no spec folder there are
no exceptions, which matches the case where nothing has been written yet.

#648's "no design decision" exception becomes one more name in the folder and one
more reader function, rather than a fifth place that builds its own path.

## Verification

- A test runs `step none` on two passes and `arch none` once, then checks that
  the pipeline reports exactly the two passes as claimed and the gate reports the
  boundary answered.
- A test runs `arch none` on a branch with no spec folder and checks that
  brainstorm is still the current step.
- `grep -rn '"exceptions"\|boundary\.md' wfctl/cli.py wfctl/_pipeline.py wfctl/_evidence.py`
  finds no path built or file parsed outside calls into `_design_exceptions`.

## Log

- 2026-10-25  proposed  — #635's level-3 pass; settles how the code handling
  design exceptions is organized once they move to the spec folder
- 2026-10-25  revised   — the folder is `exceptions/` and the module
  `_design_exceptions.py`, so the files use the same word as the docs
- 2026-10-26  revised   — analyze: a fifth function, `path`, so the worktree
  guard's refusal prints the boundary exception's file without building it
