# Feature Specification: architecture views

**Feature Branch**: `739-architecture-views`
**Created**: 2026-11-09
**Status**: Draft
**Input**: `design.md` in this folder, written by the brainstorm step for #739 and #738.

## Clarifications

### Session 2026-11-09

- Q: When a repository has no architecture folder at all, does session start still name its two required views as missing? → A: Yes. Every repository needs the two required views, and the reminder is how a new repository finds out.
- Q: When several component views are missing, does session start name them in one line or print one line each? → A: One line each, naming the file to create. The length is intentional. It keeps #744 visible in wfctl's own repository, and each line goes away once its view is drawn.
- Q: On a branch that lists its contexts, does session start name every missing component view, or only those for the listed contexts? → A: Only the listed contexts, the same filter `wfctl arch context` applies to records. Once each context is its own package (#671), wfctl can derive the list from the files a change edits, and the filter keeps working unchanged.
- Q: Once a view exists, how does anyone find out it no longer matches the code? → A: wfctl tells them. Each view lists the code it covers, and session start marks a view stale when that code has commits newer than the view. Checking what a view draws against the code stays in #743.
- Q: The user judges a view, but a wrong-way arrow shows up red only if the agent colors it. What does the user check an arrow against? → A: Each arrow in a container or component view names the import or call that creates it, so the user can check any arrow against the code. The record says what the user's review can't catch, and #743 adds the check for a wrong-way arrow drawn in the normal color.
- Q: Where does a record's decision go? → A: At the top. A record opens with its decision, then its drawings, and the rest of the text supports the drawings with what they can't show.

## User Scenarios & Testing _(mandatory)_

A view is one picture of the system that answers one question, with a short plain summary above it. The agent draws views from the code, and the user reads them to see the system's pieces and boundaries well enough to spot a bad architectural decision.

### User Story 1 - Every repository has the same required views (Priority: P1)

The user opens any repository that uses wfctl and finds the same views in the same place: a system context view showing who and what the system talks to, and a container view showing the parts that run or store data separately. A repository whose domain page lists contexts also has one component view per context. The design method ships a template for each view, so the agent knows what to draw without being told.

**Why this priority**: This is the issue's goal. Without a standard set, each repository works out its own pictures and the user can't find the system's outline at a glance.

**Independent Test**: Fill each view template for a made-up capability and check that the result answers the template's question with no other guidance.

**Acceptance Scenarios**:

1. **Given** a repository using wfctl, **When** the agent follows the system context template, **Then** the view opens with a plain summary and draws the system, its users, and the outside systems it talks to.
2. **Given** a repository whose domain page lists three contexts, **When** the agent asks which views are required, **Then** the answer is the system context view, the container view, and three component views, one per context.
3. **Given** wfctl's own repository after this change, **When** the user opens the architecture folder, **Then** it holds a system context view and a container view of wfctl, and `views/current-state.md` stays as the optional module layers view.

---

### User Story 2 - Session start points the agent at the views (Priority: P1)

When a session starts, the agent sees where the views are, and which required ones are missing, in the same output that lists the architecture records.

**Why this priority**: A view the agent never opens can't stop it from drawing a bad boundary. Printing the paths at session start puts them in front of the agent at the moment it reads the rest of the architecture.

**Independent Test**: Run session start in a repository with some views present and some missing, and check the output names each present path and each missing view.

**Acceptance Scenarios**:

1. **Given** a repository with both required views present, **When** session start runs, **Then** it prints the path of each one.
2. **Given** a branch whose design document lists two contexts, **When** session start runs, **Then** it also prints the path of the component view for each of those two contexts.
3. **Given** a repository with no container view, **When** session start runs, **Then** it prints a line naming the missing container view, and the session continues.
4. **Given** any missing view, **When** the agent runs any pipeline step or opens a PR, **Then** nothing is refused because of it.
5. **Given** a container view that covers `wfctl/`, **When** a commit changes `wfctl/` after the view's last commit, **Then** session start marks the container view stale and says how many commits it's behind. Committing an update to the view clears the mark.

---

### User Story 3 - A record can carry more than one kind of diagram (Priority: P2)

An architecture record's author can declare more than one diagram kind, such as a data flow and a sequence, and draw each one under its own heading. wfctl checks that every declared kind has its drawing.

**Why this priority**: Some decisions need two pictures, such as who owns a value and what happens when a step fails partway. It's a separate issue (#738) carried on this branch, and the views work doesn't depend on it.

**Independent Test**: Write a throwaway record declaring `[data-flow, sequence]` with both drawings and check it passes. Delete one drawing and check the refusal names the missing kind and the fix.

**Acceptance Scenarios**:

1. **Given** a record declaring one kind with its drawing directly under `## Boundary`, **When** acceptance is checked, **Then** it passes exactly as it does today.
2. **Given** a record declaring `[data-flow, sequence]` with a `### data-flow` and a `### sequence` heading under `## Boundary`, each with its drawing, **When** acceptance is checked, **Then** it passes.
3. **Given** the same record with the sequence drawing removed, **When** acceptance is checked, **Then** it's refused with a message that names the record, says the sequence drawing is missing, and says to add a `### sequence` heading with a sequence diagram including the step that fails.
4. **Given** a record declaring `[state, state]`, **When** acceptance is checked, **Then** it's refused with a message naming the repeated kind.

---

### User Story 4 - The domain page template is easier to read (Priority: P3)

The user reads a domain page written from the template and finds short lists where wide tables used to be.

**Why this priority**: wfctl's own domain page showed the long, wide tables are hard to read. It matters less than the views because the template only shapes pages written after this change.

**Independent Test**: Fill the new template for a made-up capability and check that only the Bounded Contexts list is a table.

**Acceptance Scenarios**:

1. **Given** the new domain model template, **When** the agent fills it, **Then** the Bounded Contexts table and the Context Map remain, and evidence, scenarios, the glossary, invariants, and open questions are short lists.

---

### Edge Cases

- A repository with no domain page, or a domain page with no `Contexts` line, needs only the two required views, and session start names no component views.
- A branch whose design document lists no contexts prints the paths of every component view that exists and names every one that's missing, the same way `wfctl arch context` prints every record when no contexts are listed.
- When several component views are missing, session start prints one line for each, naming the file to create. wfctl's own repository prints seven of these lines every session until #744 is done, and that reminder is intentional.
- A repository with no architecture folder at all still gets the two missing-view lines, since every repository needs the two required views.
- A branch that only edits a view isn't reported as deciding a record, and doesn't count as touching the boundary question.
- A record with `diagram: []` reads as not declared, the same as a record with no `diagram` field.
- A record whose list names a kind wfctl doesn't know is refused, and the message names that kind and lists the four known kinds.
- A record whose `## Boundary` has a `### <kind>` heading for a kind it doesn't declare is refused, because the declaration and the drawings disagree.
- A view with no `covers` line is marked unchecked, since wfctl can't tell whether it's stale.
- A view whose `covers` line names a path that doesn't exist is marked unchecked, and the line names the path.
- A view that isn't committed yet is new, so it isn't stale. Uncommitted changes to the covered code don't count either, since wfctl compares commits only.
- If the architecture root is outside the working tree, wfctl can't read the views' git history, so each present view is marked unchecked rather than current.
- A stale or unchecked view never refuses anything, the same as a missing one.
- A record declaring `sequence` in a list still needs the failing step in its sequence drawing, the same rule that applies to a one-kind sequence record today.

## Requirements _(mandatory)_

### Functional Requirements

- **FR-001**: wfctl MUST define the required views as a system context view and a container view in every repository, and one component view per context on the domain page's `Contexts` line.
- **FR-002**: Views MUST be located under `views/` in the architecture root, with component views at `views/components/<context>.md`, named exactly as the context is spelled on the `Contexts` line.
- **FR-003**: The design method MUST ship a template for the system context, container, and component views. Each template opens with a plain summary, states the one question the view answers, and asks for one drawing.
- **FR-003a**: The container and component view templates MUST state the layout rule from Iglberger's *C++ Software Design* in their own words, not by citation alone. Parts that rarely change go above a labeled line, and parts that change often go below it. Arrows point toward the stable side, and an arrow from a stable part to a volatile one is drawn in red. The agent draws the dependencies the code has, not the ones the design intends.
- **FR-003b**: The container and component view templates MUST ask that each arrow carry a label naming the import or call in the code that creates it.
- **FR-003c**: Each view template MUST carry a `covers` frontmatter line listing the paths, relative to the repository root, whose code the view draws. It uses the same bracket form as a record's `diagram` list.
- **FR-004**: A test in wfctl's suite MUST compare wfctl's list of required views with the view templates it ships, and fail when they disagree.
- **FR-005**: `wfctl arch context` MUST print the paths of the required views that exist, limited to the component views for the contexts the branch lists when it lists any.
- **FR-006**: `wfctl arch context` MUST name each missing required view on its own line, as the path where the view belongs. When the branch lists contexts, it names only the missing component views for those contexts.
- **FR-006a**: For each required view that exists, `wfctl arch context` MUST mark the view stale when any path on its `covers` line has a commit newer than the view's own last commit, and say how many. It MUST mark the view unchecked, with the reason, when the view has no `covers` line, the line names a path that doesn't exist, or wfctl can't read the view's git history.
- **FR-007**: A missing view MUST NOT refuse any command, block any pipeline step, or block a PR.
- **FR-008**: `views/` MUST be one of the folders under the architecture root that aren't records, so no reader of records treats a view as a record.
- **FR-009**: A record's `diagram` field MUST accept one kind or a list of kinds.
- **FR-010**: For a record declaring one kind, acceptance MUST behave as it does today, with the drawing directly under `## Boundary`. A drawing under a `### <kind>` heading for that kind MUST also pass.
- **FR-011**: For a record declaring more than one kind, acceptance MUST require a `### <kind>` heading under `## Boundary` for each declared kind, with a drawing under it.
- **FR-012**: Acceptance MUST refuse a list that repeats a kind, names an unknown kind, or leaves a declared kind without its drawing, and MUST refuse a `### <kind>` heading for a kind the record doesn't declare.
- **FR-013**: Every refusal this change adds MUST name the record, the problem, and the fix, in the shape agreed in `design.md`: a `✗ <slug> <problem>.` line, then an indented `Fix:` line.
- **FR-014**: The rule that a sequence drawing shows the step that fails MUST apply to the sequence drawing in a multi-kind record.
- **FR-015**: `wfctl doctor` MUST warn about a proposed record with any of the problems in FR-012, the same way it warns about a sequence drawing with no failing step today. An unknown kind is the exception: it stays an error on every status, as it is today, now checked for each kind in the list.
- **FR-016**: The domain model template MUST keep the Bounded Contexts table and the Context Map drawing, and MUST use short lists for evidence, scenarios, the glossary, subdomains, the Context Map's relationships, invariants, Aggregates, implementation feedback, and open questions.
- **FR-017**: The architecture-decisions skill and the record template MUST describe how to declare and draw more than one kind.
- **FR-017a**: The record template MUST open with the decision, then the drawings, in this order: the title, `## Decision`, `## Boundary`, `## Context`, `## Direct baseline`, `## Owns truth`, `## Considered`, `## Consequences`, and `## Log`. The two records this branch proposes follow it. Accepted records keep their order, since wfctl finds each section by name.
- **FR-018**: wfctl's repository MUST carry a system context view and a container view of wfctl, drawn with the new templates.
- **FR-019**: `docs/reference.md` MUST document the `diagram` field's list form. No other part of that file or the README changes, since #735 owns them.
- **FR-020**: The branch MUST commit the release notes `changes/738.addition.md` and `changes/739.change.md`.

## Key Entities _(include if feature involves data)_

- **View**: One markdown file under `views/` in the architecture root. It holds a `covers` line, a plain summary, the question it answers, and one drawing. It describes the system and binds nothing.
- **Required view**: A view wfctl expects in every repository, or in every repository whose domain page lists contexts.
- **Diagram declaration**: A record's `diagram` field, holding one kind or a list of the four kinds `data-flow`, `component`, `state`, and `sequence`.

## Success Criteria _(mandatory)_

### Measurable Outcomes

- **SC-001**: An agent can fill each of the three view templates for a made-up capability with no guidance beyond the template, and each result answers the template's question in one drawing.
- **SC-002**: Session start in wfctl's own repository shows the paths of its two required views. On a branch that lists no contexts, it names each of the seven missing component views on its own line. On this branch, it names only the two for architecture-records and design-method.
- **SC-003**: A record declaring two kinds with both drawings passes acceptance, and removing either drawing produces a refusal that names the missing kind and the fix, with no other reading needed.
- **SC-004**: Every one of the existing records on disk that declares one kind passes or fails acceptance exactly as it did before this change.
- **SC-005**: A domain page filled from the new template has exactly one table, the Bounded Contexts list.
- **SC-006**: In a test repository, a commit to a path a view covers makes session start mark that view stale, and a commit to the view clears the mark, with no other step.

## Validation Strategy _(mandatory)_

- `uv run pytest -q`, `uv run ruff check wfctl/ tests/`, `uv run mypy`, and `python3 .github/scripts/check_imports.py` all pass.
- A failing test first for `views/` being treated as a record, then the fix.
- Tests for the required-views list against the shipped templates, for `wfctl arch context`'s view lines (present, missing, stale, unchecked, filtered by contexts), and for each refusal in FR-012 with its message.
- A test that every record on disk gets the same acceptance result before and after the change.
- `uv run wfctl install-skills`, then fill each new template for a made-up capability, and write a throwaway `diagram: [data-flow, sequence]` record, confirm it passes, delete one drawing, and confirm the refusal names the missing kind.
- `uv run wfctl doctor` and `uv run wfctl check config` report nothing new.

## Assumptions

- Pre-specify design context loaded from `design.md` in this folder.
- Both records, `required-views-are-wfctls.md` and the amended `the-author-declares-the-diagram-kind.md`, are proposed. This spec follows them as written, and changes if the user rejects either one.
