# The design checks match records to the contexts a branch changes

Contexts: evidence-and-derivation, architecture-records, design-method

## Problem Statement

How might we make the design checks pass only when a branch's records cover the parts of wfctl the branch changes?

The domain page splits wfctl into six bounded contexts. For example, "install and drift" covers how wfctl installs its skills into a project and reports when they fall out of date, while "session continuity" carries work from one agent session to the next. Currently, brainstorm's architecture check passes once a branch adds or edits any architecture record, and the software design check from #648 passes once a branch adds any record under `design/`. Neither check looks at which context the record is about. As a result, a branch that changes the restart hook (session continuity) passes both checks with a record about how `install-skills` backs up files (install and drift), and the restart change has no design answer.

## Recommended Direction

The design checks read the context names from the domain page and match each record to the contexts the branch changes. Three things carry the names:

1. The domain page lists the short names in two header lines, `Contexts` and `Outside parties`. The user writes them, and wfctl reads them from every page under `domain/` whose `State` is `accepted`.
2. A branch lists the contexts it changes in one `Contexts` line in `design.md`, as this file does on line 3.
3. A record lists the contexts it governs in a `governs` field.

Brainstorm pauses until every context on the branch's `Contexts` line has a record that governs it, or a "no" for that context with a reason. The agent gives that "no" with `wfctl arch none --context <name> --reason "…"` at level 2, and `wfctl step none --context` at level 3. Once the domain page has a name list, a `design.md` with no `Contexts` line pauses brainstorm too, because otherwise an agent could skip the check by leaving the line out. A repo whose domain page has no name list keeps today's general check and nothing else.

One new module, `wfctl/_contexts.py`, reads the names and runs the match. Both design checks call it, so the matching rule is written once, and #544 later changes only where the branch's list comes from.

## Behavior (level 1)

A repo's domain page carries the two header lines, and branch `700-restart-handoff` changes the restart hook. Its `design.md` says:

```
Contexts: session-continuity
```

The agent adds a level-2 record whose frontmatter says `governs: install-and-drift`. Each reachable state, with what `wfctl status` shows:

```
record governs a different context than the branch lists
  ▶ no architecture record governs session-continuity
  Brainstorm pauses, and the line names the context that has no answer.

record governs session-continuity
  ✓ architecture
  Brainstorm passes.

no record for session-continuity, and `arch none --context session-continuity` with a reason
  ✓ architecture
  Brainstorm passes. A bare `arch none` with no --context doesn't count for a listed context.

the Contexts line names something that isn't on the domain page, such as session-continuty
  ▶ session-continuty is not a context on the domain page
  Brainstorm pauses on the misspelled name, since no record could ever govern it.

design.md has no Contexts line
  ▶ design.md lists no contexts
  Brainstorm pauses until the agent adds the line.

no domain page carries a name list
  ▶ no architecture record for this change   (until any record or arch none)
  Unchanged from today.
```

`wfctl doctor` adds one finding: a level-2 record whose `governs` field names something that isn't on the list.

## Architecture (level 2)

The user chooses which contexts the repository has and what they're called, on the domain page. wfctl checks whether every context a branch changes has a record or a "no", since an agent answering that would be grading its own work. The agent still decides which contexts a branch changes and which contexts a new record governs, because today's modules overlap contexts and wfctl can't tell from a changed file which context it belongs to.

## Software design decisions

The level-2 decision is `docs/architecture/domain-page-names-contexts.md`, which the Architecture section above summarizes.

- docs/architecture/design/649-contexts-module.md — one `_contexts` module of plain functions reads the name list and the `Contexts` line, and matches them against records and per-context "no" answers

## Structure (level 3)

`_contexts.py` holds three functions:

1. `names(arch)` returns the combined list from every accepted domain page, or `None` when no page has one.
2. `listed(spec_dir)` returns the names on the `Contexts` line in `design.md`, or `None` when there's no such line.
3. `unanswered(listed, records, spec_dir)` returns the first listed context with no record and no "no", or `None`.

Each check gathers its own records and calls `unanswered`. The architecture pass passes this branch's level-2 records, and #648's software design pass passes its level-3 records. `_arch.py` gets only the `governs` field on `Record` and the `validate` finding, and `validate` takes the name list as an argument, since `_contexts` imports `_arch` and the reverse import would create a cycle.

Each per-context "no" is a file in #635's `exceptions/` folder, one subfolder per context: `exceptions/<context>/boundary.md` for level 2 and `exceptions/<context>/<step>.<pass>.md` for level 3. A flat `boundary.<context>.md` doesn't work, because #635's `passes` reads every `*.*.md` file as a pass.

## Key Assumptions to Validate

- [ ] #635 merges with `_design_exceptions` and the `exceptions/` folder as its level-3 record describes. If it changes the layout, the per-context folders move with it. Test: rebase onto `main` after #635 merges and read `_design_exceptions.py`.
- [ ] #648 merges with its software design pass as a separate reader beside `brainstorm_architecture`. If the two become one reader, it makes one call to `unanswered` instead of two. Test: read `_evidence.py` after #648 merges.
- [ ] A name on two domain pages is the same context. If two pages use one name for different contexts, `names` has to report the duplicate instead of combining them. Test: this repo has one page with a list, so the test comes when a second page adds one.

## MVP Scope

In:

1. `wfctl/_contexts.py` with `names`, `listed`, and `unanswered`.
2. `Record.governs`, read from the `governs` frontmatter field, and the `validate` finding for an unknown name, with `doctor` passing in `_contexts.names`.
3. The architecture pass and #648's software design pass calling `unanswered`, and the pause line naming the context.
4. A `--context` option on `wfctl arch none` and `wfctl step none`, and a `context` argument on `_design_exceptions.write`, `boundary`, and `passes`.
5. The two header lines on `docs/architecture/domain/wfctl.md`.
6. Skill text:
   1. `model-the-domain`'s template gets `accepted` as a `State` value and the two header lines.
   2. `design-levels` and `speckit-brainstorm` have the agent write the `Contexts` line in `design.md`.
   3. The `architecture-decisions` and `software-design-decisions` templates get a `governs` field.
   4. `opening-a-change` copies the `Contexts` line into the "Moves a boundary?" section of the PR body, and the PR template gets the line.
7. Tests for each state in Behavior, and the `doctor` finding.
8. A release note, `changes/649.change.md`, as `change`, since a branch that passes the checks today can pause after this ships.

## Not Doing (and Why)

- `wfctl arch context` printing only the records for the branch's contexts (domain page recommendation item 2). It reads the same `governs` field, but it changes what a session shows rather than what passes brainstorm, and it needs `governs` on the accepted records first.
- Adding `governs` to the 18 accepted records. The checks read only this branch's records, so the existing ones don't need it yet. The `arch context` filtering above is what needs it.
- The stricter level-3 bar, "a second module has to follow the choice" (recommendation item 3). It changes when a level-3 record is required, not how one is matched, and it gets its own issue.
- Working out a branch's contexts from the files it changes. Today's modules overlap contexts, so a path-to-context map would be a module list under another name. #544 makes this possible by giving each context its own package.
- Keeping the name list in `wfctl.json`. The names are found and accepted on the domain page, and a second copy would drift from it without anyone noticing.
- A built-in `repository` name. wfctl ships no names of its own, so a repo that wants repo-wide records adds `repository` to its `Contexts` line.

## Open Questions

- None blocking. Implementation waits on #648 and #635 merging, and both are at the plan stage with no code yet.
