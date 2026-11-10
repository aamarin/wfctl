# Research: architecture views

Each entry is a choice the plan makes that the spec leaves open. The spec and the two proposed records settle everything else.

## R-001: Where the list of required views lives

- **Decision**: A new module, `wfctl/arch/_views.py`, in the architecture-records context. It's re-exported lazily from `wfctl/arch/__init__.py`, the same way every other name in that package is.
- **Rationale**: `wfctl arch context` is the only command that reads the list, and it already gets the records and the domain page's names from this package. The architecture-records context already reads the domain page, so finding the context names for component views adds no new arrow to the Context Map.
- **Alternatives considered**: The design-method context. We didn't choose it because design method ships skills and templates as package data, not code that another context calls. A constant there would need a new import arrow from architecture-records to design-method, and adding an arrow waits on `wfctl arch approve-imports`.

## R-002: Which names get a component view

- **Decision**: Only the names on the domain page's `Contexts` line. A new function, `_contexts.contexts(arch)`, returns them from accepted domain pages. It returns `None` when no accepted page has a `Contexts` line. Otherwise it returns a tuple in the order the line lists the names, with repeats dropped. With more than one accepted domain page, the pages are read in file-name order and their names joined in that order. Contract rule 1 prints component views in this order, so an unordered set, like the `frozenset` that `names` returns, would change the output from run to run.
- **Rationale**: `names(arch)` joins the `Contexts` line and the `Outside parties` line, because a record can govern either. An outside party, such as GitHub, isn't part of the system, so it gets no component view.
- **Alternatives considered**: Reusing `names(arch)`. We didn't choose it because wfctl's own repository would then require component views for GitHub, git, and the agent.

## R-003: How the branch's contexts filter the views

- **Decision**: The views use the same three inputs as `_arch.select`: the domain page's contexts, the branch's `Contexts` line from `listed(spec_dir)`, and the views on disk. A branch that lists only names on the `Contexts` line sees component views for those names. A branch that lists none, or lists a name that isn't there, sees every component view.
- **Rationale**: This matches the records filter for every branch that lists only contexts, so a session start doesn't show the records for one set of contexts and the views for another. Showing every view when the list can't be trusted is the same fallback `select` uses, for the same reason: leaving out a view that applies is worse than showing one that doesn't.
- **Where the two filters differ**: A branch that lists an outside party, such as `github`, gets the records that govern it, since `select` accepts names from the `Outside parties` line. The same branch sees every component view, because an outside party has no component view to narrow to. We accept the difference, since narrowing the views to none would hide every component view from a branch that changes how wfctl talks to GitHub.
- **Alternatives considered**: Adding views to `Selection`. We didn't choose it because `Selection` holds records, and every caller of `records_for_branch` would carry views it never reads.

## R-004: How the `diagram` field reads a list

- **Decision**: `Record.diagram` stays the verbatim string, as it is today. A new property, `Record.kinds`, returns a tuple. It strips one pair of surrounding brackets and splits on commas with `split_names`. An empty value or `[]` gives `()`.
- **Rationale**: wfctl reads frontmatter with a line scan and has no YAML parser, on purpose. YAML's inline list form, `[a, b]`, is the only list syntax the spec needs. Keeping `diagram` verbatim means every existing reader of it, such as the doctor finding that quotes the value, keeps working.
- **Alternatives considered**: A block list (`- a` on separate lines). We didn't choose it because the line scan reads one line per key, and an indented line is a nested value it skips on purpose.

## R-005: How a drawing is found for each kind

- **Decision**: A new function, `_drawings(record)`, returns a map from kind to drawing text. It reads each `### <kind>` heading under `## Boundary` whose text is one of the four kinds, ignoring case. The kind's subsection ends at the next `###` or `##` heading of any text, and the first fenced block inside it is the drawing. In a multi-kind record, a fence above the first `###` heading belongs to no kind. `data-model.md §Drawing per kind` lists every case. For a record declaring one kind, the existing `_drawing(record)` still counts: a drawing directly under `## Boundary` passes, and so does one under `### <kind>`.
- **Rationale**: `_section_bounds` already ends `## Boundary` at the next `## ` heading, and a `### ` line doesn't match `## `, so the subsections stay inside the bounds it returns. A `###` heading whose text isn't a kind, such as `### Key`, is ignored, since an author may add other subheadings.
- **Alternatives considered**: Treating every `###` heading as a kind. We didn't choose it because a record that adds `### Key` under its drawing would then be refused for declaring an unknown kind. Ending a subsection only at the next kind heading was also rejected. A `### data-flow` heading with no fence would then reach past `### Key` into the next subsection, and could pick up a fence that belongs to another kind, which is the swap `the-author-declares-the-diagram-kind.md §Considered` says the headings exist to catch.

## R-006: Where each new rule is checked

- **Decision**: Acceptance refuses each problem in FR-012 through `accept_blockers`. `validate` reports the same problems as warnings on proposed records, which is how `wfctl doctor` shows them (FR-015). A kind that isn't one of the four stays an error on every status, as VR-006 is today, now checked for each kind in the list.
- **Rationale**: This is the split the sequence failure-step rule already uses. Acceptance is where the rule binds, and the doctor warning arrives while the record is still being written, so the refusal isn't the first anyone hears of it.
- **Alternatives considered**: Doctor errors for proposed records. We didn't choose it because doctor exits 1 on an error, and a record mid-draft would fail every `doctor` run until it's finished.

## R-007: Where the view templates ship

- **Decision**: Under `wfctl/agents/skills/architecture-design/views/`, one file per view: `system-context.md`, `container.md`, and `component.md`. The `architecture-design` skill names them in its Inputs section, beside the current-state view.
- **Rationale**: `architecture-design` is the skill that reads the current structure before drawing a boundary, and it already points at the current-state view. The file names match the paths a repository's views use, so the test in FR-004 compares the two lists by name.
- **Alternatives considered**: `design-levels`. We didn't choose it because that skill routes between levels and doesn't hold templates.

## R-008: What drawing format the views use

- **Decision**: Mermaid, like the records. The stability rule draws a stable part above a labeled line by putting it in an upper subgraph, and draws a wrong-way arrow in red with `linkStyle`.
- **Rationale**: Records stay on mermaid here because wfctl's checks only read mermaid. Using the same format for views keeps one drawing style per repository until #740 decides on SVG for both.
- **Alternatives considered**: Hand-drawn SVG. We didn't choose it because #740 owns that decision, and a view format chosen here would have to be undone if #740 decides differently.

## R-009: Where the views print in `wfctl arch context`

- **Decision**: In a `Views` block at the end of the output, after every line about records. Each path prints through `_paths.arch_location`, the function the records footer already uses: relative to the repository root when the architecture root is inside it, and absolute when it isn't. Each missing view prints as `missing: <path>`.
- **Rationale**: The records come first because they bind the work. The views describe the system, so they come after. A path relative to the repository root is what the agent opens, and an architecture root outside the working tree has no relative path worth printing, which is why `arch_location` already prints it absolute.
- **Alternatives considered**: Printing the views before the records. We didn't choose it because the header line counts records, and the records should stay directly under it.

## R-010: How wfctl finds a stale view

- **Decision**: Each view lists the code it draws on a `covers` frontmatter line, such as `covers: [wfctl/]`. For each present view, wfctl finds the view's last commit with `git log -1 --format=%H -- <view>`, then counts the commits since then that touch a covered path with `git rev-list --count <commit>..HEAD -- <paths>`. A count above 0 marks the view stale. Committing an update to the view resets the count, and the PR diff showing that update is where the user reviews it again.
- **Rationale**: This finds drift in any language, since it reads git history rather than the code, and it costs two `git` calls per present view. It doesn't say what changed in the drawing, which is #743's job, but it tells the user and the agent when to look, and nothing did before.
- **Alternatives considered**: Comparing file modification times. We didn't choose it because a checkout or a restore gives every file the same timestamp, so every view would read current. Deriving `covers` from the view's kind, such as `wfctl/<context>/` for a component view, was also rejected. Most contexts haven't moved into their package yet (#671), and a repository that isn't laid out by context would get a wrong default without noticing.
- **When `git` fails**: If either call exits non-zero, the view is unchecked with the reason `not in this repository's history`. An architecture root outside the working tree always takes this path, since its files aren't in the code's history. We didn't choose to read a failed call as "no commit yet", because the view would then print as current forever when wfctl never checked it.
- **Known limit**: A commit that edits the view without redrawing it, such as a typo fix, clears the mark. We accept this because the edit shows up in the PR diff, where the user reads it.

## R-011: How the user checks an arrow

- **Decision**: The container and component view templates ask for a label on each arrow naming the import or call that creates it, such as `A -->|"imports _records"| B`. wfctl doesn't check the labels in this branch.
- **Rationale**: Without a label, the user has nothing but the agent's coloring to tell a wrong-way arrow from a sound one. A label gives the user one line of code to look up for any arrow, without trusting the agent.
- **Alternatives considered**: Checking here that every arrow has a label. We didn't choose it because checking what a view draws is #743's scope, and that issue now names the wrong-way arrow check too. A label check alone would pass a view whose labels are wrong.

## R-012: The record template's section order

- **Decision**: The template opens with the title, then `## Decision`, then `## Boundary`, and the supporting sections follow: `## Context`, `## Direct baseline`, `## Owns truth`, `## Considered`, `## Consequences`, and `## Log`. The two records this branch proposes are reordered to match. Accepted records aren't touched.
- **Rationale**: The reader sees what was decided and its picture before any paragraph of text. The text after the drawing explains what the drawing can't show. wfctl finds every section by its heading, through `_section_bounds` and the `## decision` scan in `decision_text`, so no reader of records depends on the order.
- **Alternatives considered**: Reordering every accepted record too. We didn't choose it because an accepted record isn't edited, and a mixed order across records is harmless to every check.

## R-013: The layout of the new refusals

- **Decision**: Each refusal this change adds prints as its own block: a `✗ <slug> <problem>.` line, then an indented `Fix:` line, which is the layout `design.md` agreed. The existing blockers keep their `cannot be accepted yet` block, and a record with both prints that block first.
- **Rationale**: The user agreed this layout in `design.md`, and the record shows it. Keeping the old blockers as they are keeps SC-004 true, since no existing record's output changes.
- **Alternatives considered**: Folding the new problems into the existing block as `problem: fix` lines. We didn't choose it because the spec and the record both show the other layout, and the existing block names the record only once, in its header.
