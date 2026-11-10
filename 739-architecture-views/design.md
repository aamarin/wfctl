# A standard set of architecture views

Contexts: architecture-records, design-method

## Problem Statement

Every repository that uses wfctl describes its architecture in a standardized way, allowing users to quickly see the system's pieces and boundaries and to spot bad architectural decisions.

## Recommended Direction

A view is a single picture of the system that answers a specific question, with a brief summary above it. wfctl uses the C4 model levels to decide which views each repository needs. Every repository includes a system context view, showing who and what the system interacts with, and a container view, showing the parts that run or store data separately. If the domain page lists contexts, there is also one component view for each context. Module layers and deployment views are optional.

We picked C4 instead of arc42 or the 4+1 view model. arc42 is a full documentation template, but its sections on decisions, constraints, and the glossary repeat what wfctl's records and domain page already cover. The 4+1 views don't build on each other, and in a small repository, most end up empty. The development view in 4+1 matches what `views/current-state.md` already provides, so that file remains as wfctl's optional module layers view.

The agent creates each view from the code, and the user reviews it. The user understands how the system should work, not its internal structure, so the views are made for the user to read.

To help the user spot a bad boundary, the container and component view templates follow the layout rule from Iglberger's *C++ Software Design*, which wfctl's level-3 design records already use. Parts that rarely change go above a labeled line, and parts that change often go below it. Arrows point toward the stable side, so an arrow from a stable part down to a volatile one is drawn in red as a problem. The agent draws the dependencies the code has, not the ones the design intends, since any difference between them is the finding.

When a session starts, `wfctl arch context` prints the paths of the two required views and the component views for the contexts listed in the branch. It also adds a line for each missing required view. It prints paths instead of summaries, since summaries are meant for the user reading the file. Each view lists the code it covers, and wfctl marks a view stale when that code has commits newer than the view. Missing or stale views never block a step or a PR.

Each arrow in a container or component view names the import or call that creates it, so the user can check any arrow against the code without relying on the agent's coloring. Checking the arrows themselves is #743.

The record template now opens with the decision, followed by its drawings. The text after them supports the drawings with what they can't show.

The same branch permits an architecture record to declare more than one diagram kind (#738). The `diagram` field can take a single kind or a list, like `diagram: [data-flow, sequence]`. Each kind gets its own `### <kind>` heading under `## Boundary`, with its drawing below. If a record has only one kind, its drawing goes directly under `## Boundary`. wfctl rejects a record that declares a kind without a drawing or repeats the same kind. Each rejection lists the record, the problem, and the fix:

```
✗ review-record-in-git-notes declares a sequence diagram but doesn't draw one.
  Fix: under '## Boundary', add a '### sequence' heading with a mermaid
  sequenceDiagram, including the step that fails (an alt block or a -x message).
```

The domain page template keeps the Bounded Contexts table and the Context Map. Evidence, scenarios, glossary, invariants, and open questions are now short lists instead of wide tables.

## Boundaries and Ownership

1. wfctl decides which views each repository needs. Repositories should not choose their own list, since the goal is for every repository to describe itself in the same way. This is explained in `docs/architecture/required-views-are-wfctls.md`.
2. The agent creates each view based on what it shows. wfctl only reads Python and cannot figure out a repository's running parts, and the user does not know the system's internals.
3. The user decides if a view shows a sound design. The check wfctl ships can tell if a view exists and if its covered code has changed since, not if its boundaries are correct, and the agent should not judge its own drawing. A wrong-way arrow the agent misses isn't visible to the user until #743 adds that check. A repository can still test a view against its own code, as wfctl's `tests/test_architecture_view.py` already does for the module layers view.
4. The record's author states which diagram kinds a record needs, and wfctl checks that each declared kind has a drawing under its heading. This updates `docs/architecture/the-author-declares-the-diagram-kind.md`, which is still a proposal, not a replacement. The #738 issue text says a new record replaces it, but the PR explains why it does not.

## Key Assumptions to Validate

- [ ] The new view templates are enough for an agent to draw a view with no other guidance. Test it by filling each template for a made-up capability.
- [ ] A record that declares `[data-flow, sequence]` passes when both drawings are present, and the refusal names the missing kind when one is deleted. Test it with a throwaway record.
- [ ] A branch that only edits a view isn't reported as deciding a record. Test it by writing a failing test first, then adding `views/` to the folders that aren't records.

## MVP Scope

In scope:

1. The two records above.
2. Templates for the system context, container, and component views, and the trimmed domain page template.
3. The required views as a constant in wfctl's code, checked against the templates by a test.
4. `wfctl arch context` printing the view paths and a line per missing required view.
5. `diagram` as a list, one heading per kind, the duplicate refusal, and the refusal wording above.
6. Adding `views/` to the folders under the architecture root that aren't records.
7. wfctl's own system context and container views, as the worked example the templates point to.
8. Release notes `changes/738.addition.md` and `changes/739.change.md`.

## Not Doing (and Why)

1. Checking a view against the code or the domain page. The issue doesn't ask for it. It's its own feature, tracked in #743, which starts from wfctl's existing test of its module layers view.
2. Drawing wfctl's seven component views. That's seven drawings, and they're easier once each context has moved into its own package (#671). This is tracked in #744.
3. Applying the new template to wfctl's domain page. #737 is rewriting that page now, so the change waits until both branches merge. This is tracked in #745, which also redraws the Context Map by the same stability rule, since no view shows the contexts side by side.
4. SVG drawings in records and views. That's #740. Records stay on mermaid here, since wfctl's checks only read mermaid.
5. Editing the README or `docs/reference.md`, which #735 owns, except the passage of `docs/reference.md` that documents the `diagram` field.

## Open Questions

- Whether `views/components/<context>.md` is the right layout, nobody has challenged it yet.

## Software design decisions

No level-3 record. Neither context makes a structural choice in code that weighed an alternative, and both answers are recorded with `wfctl step none brainstorm.software-design`.
