# Data model: architecture views

Nothing here is stored by wfctl. Every value is read from files in the repository each time a command runs.

## Required view

One view wfctl expects a repository to have.

- `name`: `system-context`, `container`, or a context name from the domain page's `Contexts` line.
- `path`: where the view belongs, relative to the architecture root.
  - `views/system-context.md`
  - `views/container.md`
  - `views/components/<context>.md`, spelled exactly as on the `Contexts` line.
- `present`: whether a file exists at `path`.
- `covers`: the paths from the view's `covers` frontmatter line, read with the same bracket parsing as a record's `diagram` list. Empty when the line is missing.
- `freshness`, for a present view:
  - `current`: no commit to any covered path since the view's last commit, or the view has no commit yet.
  - `stale (n)`: `n` commits to the covered paths since the view's last commit.
  - `unchecked (no covers line)`: the view has no `covers` line, or it's empty.
  - `unchecked (missing path)`: a covered path doesn't exist in the working tree. The line names the first one.
  - `unchecked (no history)`: a `git` call for the view fails, such as when the architecture root is outside the working tree, the directory isn't a git repository, or `git` isn't installed. wfctl never reads a failed call as "no commit yet".

  If more than one `unchecked` reason applies, wfctl prints only the first one in this order: `no history`, then `no covers line`, then `missing path`. The history reason comes first because it applies to every view under the same root, the same way it does for a root outside the working tree. For example, a view with no `covers` line in a directory that isn't a git repository prints `not in this repository's history`.

Rules:

1. The system context view and the container view are required in every repository, including one with no architecture folder.
2. A component view is required for each name on the `Contexts` line of an accepted domain page. A repository with no such line requires none.
3. `views/current-state.md` and any other file under `views/` is optional, and wfctl never reports it.
4. Freshness reads commits only. An uncommitted edit to the view or to the covered code doesn't change it.
5. Freshness never changes the exit code, including when a `git` call fails.

Example, for wfctl's own repository after this change:

```
views/system-context.md                        present
views/container.md                             present
views/components/architecture-records.md       missing
views/components/design-method.md              missing
... five more component views                  missing
```

## View listing

What `wfctl arch context` prints about the views for one branch.

- `present`: the required views that exist, after the branch filter.
- `missing`: the required views that don't, after the branch filter.

The branch filter applies to component views only:

| What the branch's `design.md` lists | Component views shown |
| --- | --- |
| Names that are all on the `Contexts` line | Those names only |
| No `Contexts` line, or an empty one | Every one |
| A name that isn't on the `Contexts` line, including a name from `Outside parties` | Every one |
| No spec folder | Every one |

The system context and container views are always shown, present or missing.

## Diagram declaration

A record's `diagram` frontmatter field.

- `diagram`: the verbatim value, as today.
- `kinds`: the declared kinds, read from `diagram`.
  - `diagram: sequence` gives `("sequence",)`.
  - `diagram: [data-flow, sequence]` gives `("data-flow", "sequence")`.
  - `diagram: []`, an empty value, or no field gives `()`, which reads as not declared.

## Drawing per kind

The drawings under a record's `## Boundary`, keyed by kind.

- A `### <kind>` heading whose text is one of `data-flow`, `component`, `state`, or `sequence` starts that kind's subsection. The match ignores case and surrounding spaces, the same way `_section_bounds` matches `## Boundary`.
- The subsection ends at the next `###` or `##` heading, whatever its text, or at the end of `## Boundary`. The first fenced block inside the subsection is the drawing. A kind heading with no fence before the next heading has no drawing, even when a later subsection has one.
- Any other `###` heading, such as `### Key`, isn't a kind and is never refused, but it still ends the subsection above it.
- A record declaring one kind may instead put its drawing directly under `## Boundary`.
- In a record declaring more than one kind, a fence directly under `## Boundary`, before the first `###` heading, belongs to no kind. It doesn't count as any kind's drawing.

Acceptance rules, each a refusal (FR-012):

1. A kind repeated in the list.
2. A kind that isn't one of the four.
3. A declared kind with no drawing. With more than one kind, that means no `### <kind>` heading with a fenced block under it.
4. A `### <kind>` heading for a kind the record doesn't declare.
5. A `sequence` drawing with no step that fails, the rule that applies today.

A record declaring more than one kind with no drawing at all gets rule 3 once per declared kind, and not the existing `no drawing` blocker.

`wfctl doctor` reports rules 1, 3, 4, and 5 as warnings on proposed records. Rule 2 stays an error on every status, as it is today.
