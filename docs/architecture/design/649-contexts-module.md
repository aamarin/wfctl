---
status: proposed
---

# One module reads and matches context names

## Context

Under `domain-page-names-contexts.md`, the design checks link records to the
bounded contexts a branch changes. The user lists the context names on the
domain page, a branch lists the contexts it changes in `design.md`, and a
record lists the contexts it governs. wfctl pauses brainstorm until every
context the branch lists has a record that governs it or a "no". Level 3
decides the exact format of the name list, how wfctl reads it when there is
more than one page under `domain/`, and where the parser and matcher are
located.

Two checks need the matcher. The architecture pass in `_evidence.py` checks
level-2 records. #648 adds a software design pass that checks level-3 records
under `design/`. Both run the same match against a different set of records,
so they need the same three inputs: the name list, the branch's `Contexts`
line, and each record's `governs` field.

This code would go into `_evidence.py` (1,708 lines) and `_arch.py` (983
lines), which are already the largest modules in wfctl after `cli.py`. The
domain page lists their long explanatory comments as a sign they need
restructuring (E13, E14). #544 would give each context its own package. When
that's done, the branch's list comes from the files it changes instead of the
`Contexts` line, and only that one input changes.

No architecture record constrains how wfctl's own modules are split, so this is
a level-3 choice.

## Verified

- `_frontmatter` at `_arch.py:124` scans `key: value` lines into a
  `dict[str, str]`. `parse_record` at `_arch.py:146` builds a `Record` from
  `status`, `supersedes`, and `diagram`, and `Record` has no `governs` field.
- `load_records` at `_arch.py:180` reads `root.glob("*.md")`, one level only,
  so `doctor`'s record check at `cli.py:7518`
  (`_arch.validate(_arch.load_records(root))`) never reads a record under
  `design/`.
- At `cli.py:8213`, `wfctl doctor` runs `_check_arch_records`.
- `_architecture_answered` at `_evidence.py:811` returns early once `spec.md`
  exists. Otherwise, it passes when `touched_on_this_branch` finds any changed
  path under the arch root, excluding `design/` and `non_record_subtrees`. It
  doesn't check what the record is about.
- `brainstorm_architecture` at `_evidence.py:1244` calls
  `_architecture_answered` directly, without the `design.md` guard.
- `records_on_this_branch` at `_paths.py:587` returns the slugs of the records
  this branch adds or modifies, including uncommitted work.
- Line 3 of `docs/architecture/domain/wfctl.md` is `State: accepted`.
  `model-the-domain/domain-model-template.md` offers
  `exploratory | proposed | reflects accepted records`, so `accepted` isn't
  one of them. `domain/vision.md` has `State: exploratory`.
- Nothing in `wfctl/` reads `docs/architecture/domain/` today.

## Assumed

- #635 merges with its `_design_exceptions` module and its `exceptions/` folder
  in the spec folder, as described in `design/design-exceptions-module.md` on
  that branch. If #635 changes that layout, the per-context folders below move
  with it. The matcher doesn't change, since it only asks `_design_exceptions`
  for a reason.
- #648 merges with its software design pass as a separate reader beside
  `brainstorm_architecture`. If #648 combines the two passes into one reader,
  that reader makes one call to the matcher instead of two.
- A name that appears on two domain pages refers to the same context, so
  `names` combines them into one. If two capabilities use one name for
  different contexts, a record for one would count for both, and `names` would
  need to report the duplicate instead.

## Direct baseline

Add the code where each piece is used, with no new module:

1. `_arch.py` reads the name list from the domain page, next to
   `_frontmatter`, since both scan header lines. `parse_record` reads
   `governs` into a new `Record.governs` field, and `validate` reports a name
   that isn't on the list.
2. `_evidence.py` reads the `Contexts` line from `design.md` in a private
   helper. `brainstorm_architecture` matches each listed context against the
   `governs` field of this branch's level-2 records and the per-context "no"
   answers, and returns the first context with neither.
3. #648's software design pass in `_evidence.py` calls the same private helper
   and repeats the match against this branch's level-3 records.

The decision below moves this repeated match into one module.

## Decision

A new module, `wfctl/_contexts.py`, reads the context names and matches them.
It holds six plain functions:

1. `names(arch)` returns the combined name list from every page under
   `domain/` whose `State` line is `accepted`, or `None` when no page has a
   list. `None` means the repo has no name list, and both checks fall back to
   the general check, as they do today.
2. `malformed(arch)` returns each entry on a domain page that isn't a valid
   name, so `doctor` can report it. A valid name is lowercase letters and
   digits joined by single hyphens, so `session continuity` and `../x` are
   both malformed. `names` leaves these entries off the list, since each name
   becomes a folder under `exceptions/`, and a name like `../x` would point
   outside it.
3. `listed(spec_dir)` returns the names on the `Contexts` line in
   `design.md`, or `None` when `design.md` has no such line.
4. `unanswered(listed, records, spec_dir)` returns the first listed context
   that no record in `records` governs and that has no "no", or `None` when
   every context has an answer.
5. `pause(names, spec_dir, records, level)` returns why brainstorm pauses
   and how to fix it, or `None`. It first checks for a missing or empty
   `Contexts` line, then for a name that isn't on the list, and then calls
   `unanswered`.
6. `answers(listed, records, spec_dir, level)` returns one line per context
   answered with a "no". Each pass calls it for its done row in
   `wfctl status`.

`level` is a `Level`, a `NamedTuple` with two constants, `ARCHITECTURE` and
`SOFTWARE_DESIGN`. Each holds the record noun, the pass name, and the command for a "no". The two
levels differ only in these three strings, so a constant is enough, and
neither check has to format its own messages.

`_evidence.py` gets one function, `context_gap(repo_root, arch, spec_dir,
level)`. It gathers this branch's records for either level and calls `pause`.
For level 2, it reads the records under the arch root, excluding `design/`.
For level 3, it reads the records under `design/`. A mapping in `_evidence`,
keyed by `level`, picks the folder. `context_gap` stays in `_evidence`
because it asks git which records the branch changed, and `_contexts` doesn't
call git.

The architecture pass, #648's software design pass, and the session summary's
Boundary line all call `context_gap`. The Boundary line is the first thing a
restarted session reads. Under #635, the line counts only a branch-wide "no"
or a changed record, so it could disagree with `wfctl status`. For example, a
branch that answered every context with a per-context "no" would read
"unanswered" while `wfctl status` shows the architecture pass done. The next
session would redo finished work. Calling one function from all three places
keeps them in agreement.

The domain page holds the name list in two header lines, next to the `State` line:

```
State: accepted
Contexts: evidence-and-derivation, architecture-records, design-method, install-and-drift, session-continuity, attention
Outside parties: workmux, trackers, spec-kit, agent-host, consumer-repo, upstream-projects
```

Each line is a comma-separated list. `names` reads them with the same
`key: value` line scan `_arch` already uses for frontmatter, so header lines
and frontmatter follow one rule. The two lines stay separate because the
domain page treats contexts and outside parties as different kinds of things.
`names` still returns both as one list, since a record can govern either.

`repository` isn't a built-in name. Since wfctl doesn't create its own names
(`domain-page-names-contexts.md`), a repo that wants records to govern the
whole repository adds `repository` to its `Contexts` line.

`_arch.py` gets the `governs` field, the `validate` finding, and a
`split_names` function. `split_names` splits a comma-separated list, trims
each entry, and drops empty ones. The domain page's header lines, the
`Contexts` line, and the `governs` field are all lists of the same names, so
they share one split rule. `split_names` is in `_arch` because `parse_record`
needs it to read `governs`. `_contexts` imports `_arch` for `split_names` and
its `key: value` line scan, so the reverse import would create a cycle. For the same reason,
`validate` takes the name list as an argument instead of reading it. The
`doctor` check calls `_contexts.names` and passes the list in.

Each per-context "no" is a file in its context's folder, inside #635's
`exceptions/` folder: `exceptions/<context>/boundary.md` for level 2,
and `exceptions/<context>/<step>.<pass>.md` for level 3. `write`, `boundary`,
and `passes` in `_design_exceptions` take a `context` argument, and the
matcher passes it to `boundary` and `passes`.

## Diagram

The boundary in force is `session-state-is-re-derived`: wfctl works out state
from files on disk at read time. The passes and the module are code that
rarely changes, while the files they read change on every branch.

```
                baseline                                    decision

stable  ┌──────────────┐ ┌──────────────┐        ┌──────────────┐ ┌──────────────┐
        │ architecture │ │ software     │        │ architecture │ │ software     │
        │ pass         │ │ design pass  │        │ pass         │ │ design pass  │
        └─┬────┬────┬──┘ └─┬────┬────┬──┘        └──────┬───────┘ └──────┬───────┘
       reads reads reads reads reads reads            calls            calls
          │    │    │      │    │    │                  └───────┬────────┘
          │    │    │      │    │    │                  ┌───────▼────────┐
          │    │    │      │    │    │                  │ context_gap,   │
          │    │    │      │    │    │                  │ _contexts      │
          │    │    │      │    │    │                  │ (both new)     │
          │    │    │      │    │    │                  └─┬─────┬──────┬─┘
          │    │    │      │    │    │                  reads reads  reads
══════════╪════╪════╪══════╪════╪════╪═ session-state-is-re-derived ═╪═════════
          ▼    ▼    ▼      ▼    ▼    ▼                    ▼     ▼      ▼
       ┌────────┐ ┌──────────┐ ┌─────────┐          ┌────────┐ ┌──────────┐ ┌─────────┐
       │ domain │ │design.md │ │ records,│          │ domain │ │design.md │ │ records,│
       │ page   │ │Contexts  │ │ "no"s   │          │ page   │ │Contexts  │ │ "no"s   │
       └────────┘ └──────────┘ └─────────┘          └────────┘ └──────────┘ └─────────┘
```

Both graphs have the same two passes and the same three kinds of file. In the
baseline, each pass reads the files and matches them itself, so six arrows
cross the divider. In the decision, each pass makes one call to
`context_gap`, which gathers the records and passes them to `_contexts`. Only
those two read the files, so three arrows cross the divider. The decision adds
one module and two functions outside it, `context_gap` and `split_names`, and
no boundary. The session summary's Boundary
line also calls `context_gap`. The drawing leaves it out because it has no
counterpart in the baseline.

The decision is built to absorb #544 changing where the branch's list comes
from. In the baseline, that changes the `Contexts` line read in both passes. In
the decision, it changes only the body of `listed`, and the two `calls` arrows
stay the same.

## Considered

- Use the direct baseline. It's the smallest diff, and it works. We didn't
  choose it because two passes would each read the `Contexts` line and run
  the same match, and #544 would have to change both. It would also add a parser and a matcher to `_evidence.py`
  and `_arch.py`, the two modules the domain page already lists as too large.
- Read the names from the domain page's Bounded Contexts table instead of
  header lines. The table is already there, so the user writes nothing
  twice. We didn't choose this because the table's Context column holds
  display names such as "Install and drift", and the outside parties are a
  numbered list rather than a table. Renaming a display name would rename the
  context, and wfctl would need a markdown table parser to read it.
- Name per-context "no" files `boundary.<context>.md` in #635's flat
  `exceptions/` folder. This adds no folders. We didn't choose this because
  #635's `passes` reads `*.*.md`, so it would read
  `boundary.install-and-drift.md` as a pass named
  `boundary.install-and-drift`.
- Define a context source interface, with the `Contexts` line as one
  implementation and changed packages as the second after #544. We didn't
  choose this because there's one source today, and #544 replaces it rather
  than adding a second. A plain function whose body changes is enough.

## Consequences

The two passes and the Boundary line share one matching rule. `_contexts`
reads the name list and the `Contexts` line. `_arch.split_names` splits both
of them, and every `governs` field, with the same rule. When #544 changes
where the branch's list comes from, only `listed` changes.

`domain-model-template.md` in `model-the-domain` gets the `Contexts` and
`Outside parties` lines. It also gets `accepted` as a `State` value, since
`wfctl.md` already uses it and `names` reads only accepted pages. The skill
writes both lines as part of its output.

Because `load_records` reads one level, `doctor` reports a `governs` name
that isn't on the list only in level-2 records. A misspelled name in a level-3
record's `governs` field appears when brainstorm pauses on the context that
record was meant to cover.

The `_design_exceptions` functions from #635 take a `context` argument, which
changes #635's plan. Neither branch has code yet, so the change is a plan
edit there or a follow-up here once #635 merges.

## Verification

- A test gives the domain page both header lines and a branch whose
  `design.md` lists one context. With a level-2 record that governs a
  different context, brainstorm pauses and names the listed context. A record
  that governs the listed context, or a "no" from
  `wfctl arch none --context <name>`, lets brainstorm pass.
- A test with no header lines on any domain page checks that brainstorm
  behaves as it does today.
- A test with an unknown name on the `Contexts` line checks that brainstorm
  pauses and names the unknown context.
- A test runs `wfctl doctor` on a level-2 record whose `governs` field holds a name
  that isn't on the list, and checks for the finding.
- A test checks that the Boundary line reads "answered" for a branch that
  changed no record and answered every listed context with a "no", and
  "unanswered" for a branch whose only record governs a different context.
- `grep -n "Contexts:" wfctl/_evidence.py wfctl/_arch.py` finds nothing, so
  only `_contexts` reads the line.

## Log

- 2026-10-26  proposed  — #649 level 3: where the context names are read and
  matched, and the format of the name list
- 2026-10-26  amended  — #652: the Decision now covers what the #649 tasks
  add. `split_names` is in `_arch` to avoid an import cycle. `context_gap` in
  `_evidence` gathers the records for both levels, and the Boundary line calls
  it too. `_contexts` now has `malformed`, `pause`, `answers`, and the `Level`
  type with its two constants. Andre chose the shared `context_gap` function in the plan
  walkthrough.
