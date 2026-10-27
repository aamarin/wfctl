# Data model: The design checks match records to the contexts a branch changes

Every value here is read from a file at check time. Nothing is stored by wfctl between runs.

## Name list

The set of names records and branches can use. The user writes it on the domain page, in the header lines before the first `## ` heading:

```
# wfctl domain model

State: accepted
Contexts: evidence-and-derivation, architecture-records, design-method, install-and-drift, session-continuity, attention
Outside parties: workmux, trackers, spec-kit, agent-host, consumer-repo, upstream-projects
```

- Source: every `*.md` directly under `<arch-root>/domain/` whose `State` value is `accepted`.
- Value: the union of each page's `Contexts` and `Outside parties` entries, as a `frozenset[str]`.
- Absent: `None` when no accepted page has a `Contexts` key. Both checks then behave as they do today.
- Rules: entries are split on commas and trimmed, and empty entries are dropped. Names are compared exactly.

## `Contexts` line

The contexts one branch changes. The agent writes it in the header of `design.md`, under the title:

```
# The design checks match records to the contexts a branch changes

Contexts: evidence-and-derivation, architecture-records, design-method
```

- Value: `tuple[str, ...]` in the order written, duplicates removed.
- Absent: `None` when `design.md` has no `Contexts` key in its header. An empty value is `()`. With a name list, both pause brainstorm with `design.md lists no contexts`.

## `governs` field

The contexts a record applies to, in its frontmatter:

```
---
status: proposed
governs: session-continuity, install-and-drift
---
```

- Value: `Record.governs: tuple[str, ...]`, default `()`.
- Read for: level-2 records directly under the arch root, and level-3 records under `design/`.
- Validated by: `wfctl doctor`, for level-2 records only, since `load_records` reads one level.

## Per-context "no"

A design exception saying one context needs no record at one level. It extends #635's layout with one subfolder per context:

```
<spec-folder>/exceptions/
├── boundary.md                                   # #635: branch-wide, level 2
├── brainstorm.ui-design.md                       # #635: a repo-declared pass
└── session-continuity/
    ├── boundary.md                               # level 2, this context
    └── brainstorm.software-design.md             # level 3, this context
```

- `exceptions/<context>/boundary.md`: body `# No new boundary for <context>\n\n<reason>\n`.
- `exceptions/<context>/brainstorm.software-design.md`: body `# brainstorm.software-design does not apply to <context>\n\n<reason>\n`.
- Written by `wfctl arch none --context` and `wfctl step none brainstorm.software-design --context`. A second run overwrites, as #635's files do.
- Read by `_design_exceptions.boundary(spec_dir, context=…)` and `passes(spec_dir, context=…)`. Without a context, `passes` reads one level and never sees a subfolder.

## Check outcome

For each listed context, in order, the first match wins:

| State on disk | Outcome |
| --- | --- |
| The spec folder has `spec.md` | Done (existing exception) |
| `design_record_checks` is `"off"` (from #648) | Done, turned off |
| No name list, or no `design.md` yet | Today's general check, with #635's and #648's exits |
| A gap below, and git can't answer (from #648) | Paused with #648's git-unanswered reason |
| No `Contexts` line, or an empty one | Paused: `design.md lists no contexts` |
| A listed name not on the list | Paused: `<name> is not a context on the domain page` |
| A listed context with no governing record on this branch and no "no" | Paused: `no <noun> governs <context>` |
| Every listed context answered | Done, with a display listing each "no" if there are any |
