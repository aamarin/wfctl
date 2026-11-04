---
status: proposed
governs: architecture-records, evidence-and-derivation, session-continuity
---

# One function selects the records both session readers print

## Context

Two places tell a session which records bind it. The `wfctl arch context`
command prints the records, and the session report's `Records` line counts them
(`branch-contexts-select-records.md`). If the two count differently, the agent
reads one number in the report and a different set of records under it, and
can't tell which one is wrong.

The session report sits in Session continuity, and the selection rule belongs to
Architecture records. The Context Map draws no arrow from Architecture records to
Session continuity, so the session report can't import `_contexts` without a new
line in the import baseline (`contexts-are-packages.md`). It can import
Evidence and derivation, since the map draws an arrow from there to Session
continuity, and Evidence and derivation can import Architecture records.

## Verified

- `wfctl/_session_report.py:198` counts the accepted records itself, with
  `len(_arch.in_force(_arch.load_records(arch_root(repo_root))))`.
- `wfctl/cli.py:2029` loads the same records separately, in `arch_context_cmd`.
- `.github/scripts/check_imports.baseline` places `_session_report.py` in
  `session`, `_contexts.py` in `arch`, and `_evidence.py` in `evidence`, and it
  already lists `_session_report.py -> _arch.py` as a violation.
- The Context Map on `docs/architecture/domain/wfctl.md` draws `AR --> EV` and
  `EV --> SC`, and no arrow from `AR` to `SC`.
- `_contexts.listed(spec_dir)` reads the `Contexts` line of `design.md`, and
  `_contexts.names(arch)` reads the domain page's name list. Neither calls git.
- `_paths.resolve_spec_dir(branch, repo_root)` finds the branch's spec folder,
  and returns `None` when there is none.

## Assumed

- The import check accepts `_session_report.py` importing `_evidence.py` with no
  new baseline line. Running `.github/scripts/check_imports.py` on the branch
  would falsify this.

## Direct baseline

Each reader works out the selection on its own. `arch_context_cmd` reads the
name list and the `Contexts` line and filters the records in `cli.py`. The
session report's reader repeats those three reads and the filter to get its
count. No new function is needed, but the rule exists in two copies.

## Decision

`_contexts.select(names, listed, accepted)` holds the rule. It takes the name
list, the branch's listed contexts, and the accepted records, and reads no
files. It returns the records that apply, the count left out, and the reason it
printed every record, if it did.

`_evidence.records_for_branch(repo_root, branch)` resolves the arch root and the
spec folder, reads the name list and the `Contexts` line through `_contexts`,
loads the accepted records, and calls `select`. The session
report's reader and `arch_context_cmd` both call it, so both readers get the
same selection from one call.

## Diagram

```
               baseline                                 decision

stable   ┌──────────────┐  ┌──────────────┐    ┌──────────────┐  ┌──────────────┐
         │ arch context │  │ session      │    │ arch context │  │ session      │
         │ (cli.py)     │  │ report       │    │ (cli.py)     │  │ report       │
         └─┬────┬────┬──┘  └─┬────┬────┬──┘    └──────┬───────┘  └──────┬───────┘
         reads reads reads reads reads reads         calls            calls
           │    │    │       │    │    │              └───────┬─────────┘
           │    │    │       │    │    │          ┌───────────▼──────────┐
           │    │    │       │    │    │          │ records_for_branch   │
           │    │    │       │    │    │          │ and select (new)     │
           │    │    │       │    │    │          └──┬───────┬───────┬───┘
           │    │    │       │    │    │           reads   reads   reads
═══════════╪════╪════╪═══════╪════╪════╪═ session-state-is-re-derived ═╪════
           ▼    ▼    ▼       ▼    ▼    ▼             ▼       ▼       ▼
        ┌──────┐ ┌─────────┐ ┌─────────┐        ┌──────┐ ┌─────────┐ ┌─────────┐
        │domain│ │design.md│ │records  │        │domain│ │design.md│ │records  │
        │page  │ │Contexts │ │governs  │        │page  │ │Contexts │ │governs  │
        └──────┘ └─────────┘ └─────────┘        └──────┘ └─────────┘ └─────────┘
```

Both graphs have the same two readers and the same three kinds of file. In the
baseline, each reader reads the files and applies the rule itself, so six arrows
cross the divider. In the decision, each reader makes one call, and only
`records_for_branch` and `select` read the files, so three arrows cross it. The
decision adds two functions and no boundary.

The decision is built to absorb a change to the rule, such as a third way for a
record to apply. In the baseline, that change touches both readers. In the
decision, it touches only `select`, and the two `calls` arrows stay the same.

## Considered

- Keep the rule in two copies, as described in the direct baseline. We didn't
  choose this because the two copies can drift, and the agent then gets a count
  that doesn't match the records printed.
- Have the session report import `_contexts` directly. This works and saves one
  function, but it adds a line to the import baseline that a person has to
  approve, for an import the Context Map doesn't draw. Going through
  `_evidence` follows two arrows the map already has.
- Have `cli.py` compute the selection and pass it to the session report's
  reader. `cli.py` may import any context, so this needs no new import. We
  didn't choose it because the session report is built in two places in
  `status`, and the selection would then be wired in twice, in code that #711
  is changing at the same time.
- Put the rule in `_arch`, beside `in_force`. We didn't choose this because the
  rule reads the name list and the `Contexts` line, which `_contexts` reads, and
  `_contexts` imports `_arch`, so `_arch` can't import it back.

## Consequences

`_evidence` gains a function that only gathers paths and records for
`_contexts`, the same shape `context_gap` already has. When #671 moves the
modules into their packages, `records_for_branch` moves with `_evidence`, and
neither reader changes.

## Verification

- A test builds a spec folder whose `Contexts` line names one context, and checks
  that `arch context` prints the records `select` returns and that the session
  report's count matches.
- `.github/scripts/check_imports.py` passes with no new baseline line.

## Log

- 2026-11-03  proposed  — #700 level 3, choosing where the selection rule lives
