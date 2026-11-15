# Feature Specification: SVG drawings

**Feature Branch**: `740-svg-drawings`
**Created**: 2026-11-13
**Status**: Draft
**Input**: `design.md` in this folder, written by the brainstorm step for #740.

## Clarifications

### Session 2026-11-14

- Q: When one heading carries both an SVG image and a mermaid block, which one is the drawing? → A: Neither. A heading's drawing is an SVG or a mermaid block, never both, so acceptance refuses a heading that has both, and `wfctl doctor` warns about it while the record is proposed.
- Q: Where do the SVGs for architecture records, level-3 design records, and views go? → A: All three go in one `drawings/` folder under the architecture root, each named after the document that links it. Grouping architecture documents and their drawings by context is #761, which moves each drawing along with its document once that layout is decided. Checking a design record's drawing is part of #761 too, since design records first need to name their contexts.
- Q: Does wfctl enforce an SVG's file name, or only that it sits in `drawings/`? → A: Only the folder. The name `<slug>-<kind>.svg` is a convention the skills teach. A wrong name breaks nothing, since the record links whichever file it names, and a name check would have to change again when #761 regroups the drawings.
- Q: Where does the edge warning read a label's font size? → A: From both the attributes and the CSS. The label's own `font-size` attribute or class rule comes first, then the nearest ancestor's, so a class on the label beats a size set on the root `<svg>`. If nothing sets one, wfctl uses 16, the SVG default. Selectors more complex than a single class aren't read.

### Session 2026-11-14 (plan walkthrough)

- Q: Can an accepted record's SVG change? → A: Only its layout, such as moving a box or shortening a label, and the commit message says why. A change to what the drawing shows supersedes the record. The plan, the record's Consequences, and `drawing-style.md` all state this rule.
- Q: Who signs off on how a drawing looks, and how? → A: The user, by accepting the record. An agent can't catch a visual problem and could claim it looked, so the sign-off has to be a person's act. We didn't add a separate `approve-drawing` command because every record already needs a drawing to be accepted, so acceptance is already the moment the user looks at it.
- Q: How does a drawing edited after acceptance reach the user again? → A: `wfctl arch accept` records each linked SVG's fingerprint in the Log line it writes. `wfctl doctor` warns when an accepted record's SVG no longer matches. The user looks at it and runs `wfctl arch accept` on the accepted record, which appends a `redrawn` Log line with the new fingerprint and leaves the status alone.
- Q: What stops an agent from running `wfctl arch accept`? → A: The same two checks that stop it from running `wfctl review sign-off`. The worktree guard refuses the command from an agent, and the command itself refuses to write unless it runs at an interactive terminal. `--dry-run` stays open to agents, since the brainstorm skill and the design gate's fix line both run it and it writes nothing.

## User Scenarios & Testing _(mandatory)_

A record's drawing is the picture under its `## Boundary` heading that shows what the decision decided. Today every drawing is a mermaid block, which GitHub lays out on its own, so labels overlap and the refused edge is hard to find. With this change, the author can draw it as a hand-made SVG file instead, and wfctl checks the SVG the same way it checks mermaid.

### User Story 1 - A record whose drawing is an SVG can be accepted (Priority: P1)

The author draws the record's picture as an SVG file in the `drawings/` folder under the architecture root and links it from the record as a markdown image. When the user accepts the record, wfctl counts the linked SVG as the drawing, and the record is accepted with no mermaid block.

**Why this priority**: This is the issue's goal. Today a record with only an SVG is refused with "no drawing", so the author has to keep a mermaid copy of every picture just to pass.

**Independent Test**: Write a throwaway record with `diagram: data-flow` whose only drawing is a linked SVG, and run `wfctl arch accept --dry-run` on it. It reports nothing blocking. Delete the SVG file and run it again. It refuses and names the missing path.

**Acceptance Scenarios**:

1. **Given** a record declaring one kind, with a markdown image under `## Boundary` that links `drawings/<slug>-<kind>.svg`, and that file exists, **When** acceptance is checked, **Then** the record has its drawing and nothing about the drawing blocks it.
2. **Given** a record declaring `[data-flow, sequence]`, with a `### data-flow` and a `### sequence` heading under `## Boundary`, each linking its own SVG, **When** acceptance is checked, **Then** each kind has its drawing.
3. **Given** a record whose image links an SVG that doesn't exist, **When** acceptance is checked, **Then** it's refused, and the refusal names the path it looked for.
4. **Given** a record whose drawing is a mermaid block, **When** acceptance is checked, **Then** the result is the same as before this change.
5. **Given** a branch whose only change under the architecture root is an SVG in `drawings/`, **When** the design gate asks whether the branch answered the boundary question, **Then** the SVG doesn't count as a record.

---

### User Story 2 - wfctl checks what an SVG drawing shows (Priority: P1)

While the author drafts a record, `wfctl doctor` warns when a label in the SVG appears nowhere else in the record. At acceptance, wfctl refuses a sequence drawing that shows no step failing. Both checks read the SVG the way they read mermaid today.

**Why this priority**: Without these checks, switching to SVG means a drawing nobody verifies. The label check is what keeps the picture and the prose saying the same thing, and the failing-step rule is the reason a sequence drawing exists.

**Independent Test**: Write a proposed record with a sequence SVG that has a label missing from the prose and no element with the `failing-step` class. `wfctl doctor` warns about both, and `wfctl arch accept --dry-run` refuses for the failing step. Add the class to one arrow and the word to the prose, and both go away.

**Acceptance Scenarios**:

1. **Given** a proposed record whose SVG has a `<text>` label with words that appear nowhere else in the record, **When** `wfctl doctor` runs, **Then** it warns about that label by its text, as it does for a mermaid label.
2. **Given** a record declaring `sequence` whose SVG has no element with the `failing-step` class, **When** acceptance is checked, **Then** it's refused because the sequence shows no step that fails, and `wfctl doctor` warns about the same thing while the record is proposed.
3. **Given** the same record with `class="failing-step"` on one element, **When** acceptance is checked, **Then** the failing-step rule passes.
4. **Given** a record declaring `data-flow` whose SVG has an element with the `refused-edge` class, **When** any check runs, **Then** the class changes nothing, since no check reads it.

---

### User Story 3 - doctor warns about a label running off the drawing (Priority: P2)

Nothing lays out a hand-drawn SVG, so a label can run past the drawing's edge and be cut off when GitHub shows it. While a record is proposed, `wfctl doctor` warns about each label whose estimated width puts it past the drawing's edge.

**Why this priority**: The user caught exactly this on the first SVG drawn for #740, where a label showed as "file missi". The warning finds the common case before the user has to. It matters less than the first two stories, since the user's own review before acceptance still catches it.

**Independent Test**: Write a proposed record with an SVG 400 units wide and a 40-character label starting at x=380. `wfctl doctor` warns about that label. Move it to x=20, and the warning goes away.

**Acceptance Scenarios**:

1. **Given** a proposed record whose SVG has a label that, by its character count and font size, runs past the drawing's right or left edge, **When** `wfctl doctor` runs, **Then** it warns, naming the record and the label's text.
2. **Given** an accepted record with the same SVG, **When** `wfctl doctor` runs, **Then** it doesn't warn, since an accepted record's body is frozen.
3. **Given** an SVG with no `viewBox` and no `width`, **When** `wfctl doctor` runs, **Then** it doesn't warn, since there's no edge to measure against.

---

### User Story 4 - The skills teach SVG in one style (Priority: P2)

An agent drawing a record's picture follows the skills and produces an SVG in the style the user likes: boxes on a grid, a short label on every arrow, the refused edge in red, a one-line caption, and a background in the page's color that switches with the device's dark mode. The rules are written once, and each skill that teaches drawing links to them.

**Why this priority**: The checks only verify what an SVG shows, not how it reads. The style is what makes an SVG better than mermaid in the first place. It depends on Story 1, since a skill can't teach SVG as the default while acceptance refuses it.

**Independent Test**: After `uv run wfctl install-skills`, have an agent draw one record's SVG from the `architecture-decisions` skill, render it, and check it against each rule in the style file.

**Acceptance Scenarios**:

1. **Given** the installed skills, **When** an agent reads `design-levels`, `architecture-decisions`, `software-design-decisions`, or `model-the-domain` for how to draw, **Then** each one links to the same style file, and none of them states the rules a second time.
2. **Given** an agent that only runs a design conversation and draws nothing, **When** it reads `design-levels`, **Then** the style rules aren't in what it reads, only the one sentence that links to them.
3. **Given** the record template and the view templates, **When** an agent fills one, **Then** the template asks for an SVG drawing by default, and says a mermaid block still passes.

---

### User Story 5 - This feature's own record drops its mermaid copy (Priority: P3)

`record-drawing-can-be-svg.md` carries its SVG and a mermaid copy of the same drawing, because acceptance couldn't read SVG when it was written. Once the checks read SVG, the mermaid copy and the line under it that mentions it are removed, and the record is still acceptable.

**Why this priority**: It's the first real record to rely on SVG alone, so it shows the feature works on a record nobody wrote as a test. It's last because it can only happen once the other stories are done.

**Independent Test**: Remove the mermaid block and the sentence about it, then run `wfctl arch accept --dry-run -- record-drawing-can-be-svg`. Nothing about the drawing blocks it.

**Acceptance Scenarios**:

1. **Given** `record-drawing-can-be-svg.md` with its mermaid block and the "crossed in the mermaid copy" wording removed, **When** acceptance is checked, **Then** nothing about the drawing blocks it, and `wfctl doctor` reports no drawing finding for it.

---

### User Story 6 - Accepting a record is the user's sign-off on its drawing (Priority: P2)

The user accepts a record from their own terminal, after looking at its drawing. wfctl records a fingerprint of each SVG the record links. If a later branch edits the SVG, `wfctl doctor` warns that the drawing changed since the user accepted it. The user looks at it again and runs `wfctl arch accept` on the record, which records the new fingerprint. An agent can't run the real accept, only `--dry-run`.

**Why this priority**: Moving the drawing out of the record's body means an edit to it no longer shows up as a change to the record. Without the fingerprint, an accepted drawing can change and nobody looks at it again. Without the agent block, an agent could accept a record whose drawing nobody looked at.

**Independent Test**: In a scratch repo, accept a record with an SVG drawing from a real terminal, and check its Log line carries the fingerprint. Edit the SVG, and `wfctl doctor` warns. Run `wfctl arch accept` on the accepted record, and the warning goes away. Run the same accept through the agent's shell, and the guard refuses it.

**Acceptance Scenarios**:

1. **Given** a proposed record whose drawing is an SVG, **When** the user accepts it, **Then** the `accepted` Log line ends with the SVG's link and fingerprint, such as `drawing drawings/x-data-flow.svg sha256:3f9a0c1b2d4e`.
2. **Given** an accepted record whose SVG's fingerprint no longer matches its Log, **When** `wfctl doctor` runs, **Then** it warns, naming the record and the SVG, and says to look at the drawing and run `wfctl arch accept` on the record.
3. **Given** that accepted record, **When** the user runs `wfctl arch accept <slug> --agreed "<where>"`, **Then** wfctl appends a `redrawn` Log line with the new fingerprint, leaves `status: accepted` unchanged, and the doctor warning goes away.
4. **Given** an accepted record whose SVG matches its Log, **When** the user runs `wfctl arch accept` on it, **Then** it's refused as already accepted, as today.
5. **Given** an agent's shell, **When** it runs `wfctl arch accept <slug> --agreed "<where>"`, **Then** the worktree guard refuses it, and the message says a person runs it in their own terminal.
6. **Given** an agent's shell, **When** it runs `wfctl arch accept --dry-run -- <slug>`, **Then** the guard lets it through.
7. **Given** stdin or stdout isn't a terminal, **When** `wfctl arch accept` runs without `--dry-run`, **Then** it refuses before writing anything.
8. **Given** a branch that carries "no boundary moved" and whose only record change is a `redrawn` Log line, **When** the PR is opened, **Then** the record gate allows it, and the design gate still reads the boundary answer as "no boundary moved".

---

### Edge Cases

- A heading with both an SVG image and a mermaid block, such as `record-drawing-can-be-svg.md` today, is refused at acceptance, and the refusal says to keep one. `wfctl doctor` warns about it while the record is proposed.
- A record whose image links an SVG outside `drawings/`, such as one beside the record, is refused, and the refusal says to move the file into `drawings/`. Without this, an author could store an SVG where the design gate counts it as a record.
- An image link to a URL, or to a file that isn't an SVG, isn't a drawing. A record with only that under `## Boundary` is refused with "no drawing", as today.
- An SVG that isn't valid XML is refused at acceptance, naming the path and saying the file can't be read. `wfctl doctor` reports the same thing as a warning while the record is proposed.
- An SVG with no `<text>` elements has no labels, so the label check compares nothing, the same as an ASCII sketch in a fence today.
- A label split across `<tspan>` elements inside one `<text>` reads as one label.
- An element whose class list includes `failing-step` among other classes, such as `class="arrow failing-step"`, counts as the failing step.
- A `failing-step` class in a drawing for a kind other than `sequence` changes nothing.
- A label anchored at its middle or its end (`text-anchor`) is measured from where it's anchored, so a centered label near the edge is judged by both halves.
- A record with several kinds gets the edge and label checks on each kind's SVG.
- An SVG that declares external entities isn't fetched from anywhere, since the parser doesn't load external resources.
- A view or a level-3 design record links an SVG from `drawings/`, the same as a record. Neither has a drawing check, so nothing reads it. Checking a design record's drawing is part of #761.
- An SVG checked out with CRLF line endings gets the same fingerprint as the LF copy it was accepted from, because wfctl replaces CRLF with LF before hashing.
- An accepted record with an SVG but no fingerprint in its Log gets no fingerprint warning. No such record exists today, and every one accepted after this change carries one.
- A record with several kinds gets one fingerprint per SVG on its Log line, and doctor warns about each SVG that changed.
- A commit message that mentions `wfctl arch accept` is refused by the guard's text check, the same way one that mentions `wfctl review sign-off` is today. Writing the message to a file and committing with `git commit -F` avoids it.
- A command the guard's text check doesn't recognize, such as one run through an alias, still reaches the terminal check inside `wfctl arch accept`, which refuses it in the agent's shell.

## Requirements _(mandatory)_

### Functional Requirements

- **FR-001**: A record's drawing MUST be either a fenced block or a markdown image that links an SVG file, under `## Boundary`, or under `### <kind>` when the record declares several kinds. Acceptance MUST refuse a heading that carries both, saying to keep one, and `wfctl doctor` MUST warn about it while the record is proposed.
- **FR-002**: An SVG drawing MUST be stored in the `drawings/` folder under the architecture root. Its name SHOULD be `<slug>-<kind>.svg`, and no check enforces the name. The image link MUST be relative to the record. Acceptance MUST refuse a link to an SVG outside `drawings/`, saying to move it there. A view's or a level-3 design record's SVG goes in the same folder, named after the file that links it.
- **FR-003**: Acceptance MUST refuse a link to an SVG that doesn't exist, naming the path. It MUST refuse an SVG that isn't valid XML, naming the path and saying the file can't be read.
- **FR-004**: wfctl MUST read an SVG's labels from the text of its `<text>` elements, including any `<tspan>` inside them, one label per `<text>`.
- **FR-005**: The label check in `wfctl doctor` MUST compare SVG labels against the rest of the record the same way it compares mermaid labels, with `## Boundary` left out.
- **FR-006**: A sequence SVG MUST count as showing a failing step when at least one element's class list includes `failing-step`. Acceptance MUST refuse a sequence SVG with none, and `wfctl doctor` MUST warn about it while the record is proposed. Both messages MUST name the class when the drawing is an SVG, and keep today's wording when it's a fence.
- **FR-007**: Checks MUST NOT read the `refused-edge` class.
- **FR-008**: `wfctl doctor` MUST warn about a proposed record whose SVG has a label past the drawing's left or right edge. The edge is the `viewBox` width, or the `width` attribute when there's no `viewBox`. A label's width MUST be estimated from its character count and font size, and measured from its `text-anchor`. The font size MUST come from the `<text>` itself first, by its `font-size` attribute or a single-class rule in the SVG's `<style>` block matching its class. Failing that, it comes from the nearest ancestor that sets one the same way, the root `<svg>` included, and otherwise defaults to 16. Plan research R-005 gives the exact order. An SVG with neither a `viewBox` nor a `width` MUST produce no edge warning.
- **FR-009**: Every check that reads a drawing MUST read a single summary, built by one reader per format, holding the labels, whether a failing step is shown, and the labels past the edge. A fenced block and an SVG MUST produce the same kind of summary. This is `docs/architecture/design/740-one-drawing-reader.md`.
- **FR-010**: `drawings/` MUST be one of the folders under the architecture root that hold no records, so no reader of records, including the design gate, treats an SVG as a record.
- **FR-011**: Every record that passes or fails acceptance today MUST get the same result after this change, and `wfctl doctor` MUST report the same findings for it. Two kinds of fix text change wording:
  1. The `no drawing` line's fix names an SVG image as well as a fenced block. The line is part of `accept_problems`, so the new wording shows under `wfctl arch accept` and in the design gate's reason, as `tests/pipeline_payload_snapshot.json` shows. `wfctl doctor` doesn't print it.
  2. Each `_DRAWING_FIX` entry, printed when a declared kind has no drawing, names an SVG in `drawings/` first and the mermaid form second. The `sequence` entry names the `failing-step` class for an SVG. These entries print only under `wfctl arch accept`.

  The two exact-output tests in `tests/test_arch_diagram_kinds.py` that pin the old `sequence` fix are updated to the new text, and no other assertion changes. We reworded the per-kind fixes because a fix that names only mermaid sends the author back to the format the skills no longer teach.
- **FR-012**: The drawing style MUST be written once, in `wfctl/agents/skills/design-levels/references/drawing-style.md`. It covers boxes on a grid, a short label on every arrow, the refused edge in red through the `refused-edge` class, a one-line caption, the background in GitHub's page color (`#ffffff` light, `#0d1117` dark) with a `prefers-color-scheme` media query, the `failing-step` and `refused-edge` classes, and rendering the drawing to look at it before committing. It MUST also say that an accepted record's SVG may change only in layout, with a commit message saying why, and that a change to what it shows supersedes the record. This is `docs/architecture/design/740-drawing-style-one-file.md`.
- **FR-013**: `design-levels` MUST link to the style file with one sentence in its "Rendering the gate's answer" section. `architecture-decisions`, `software-design-decisions`, and `model-the-domain` MUST link to the same file and keep only the drawing guidance specific to them.
- **FR-014**: A test MUST fail when any of the four links to the style file points at a file that doesn't exist.
- **FR-015**: The record template, the level-3 design record template, and the view templates MUST ask for an SVG drawing by default, and say a mermaid block still passes.
- **FR-016**: `record-drawing-can-be-svg.md` MUST lose its mermaid block and the wording that refers to it, and remain acceptable.
- **FR-017**: `docs/reference.md` MUST document that a drawing can be a linked SVG in `drawings/`, and the `failing-step` class.
- **FR-018**: The branch MUST commit the release note `changes/740.addition.md`.
- **FR-019**: The style file, and the code that adds `drawings/` to the folders holding no records, MUST each say that the one `drawings/` folder and the file-name convention are temporary, and point to #761 as the issue that replaces them.
- **FR-020**: When `wfctl arch accept` accepts a record whose drawing is an SVG, the `accepted` Log line MUST end with ` · drawing <link> sha256:<12 hex>` for each SVG the record links, in heading order. The fingerprint is the first 12 hex digits of the SHA-256 of the file's bytes, with CRLF replaced by LF. A record drawn with a fence gets today's Log line, unchanged.
- **FR-021**: `wfctl doctor` MUST warn about an accepted record whose drawing has a problem, such as a missing, moved, or unreadable SVG. It MUST also warn about each SVG whose fingerprint no longer matches the last `accepted` or `redrawn` Log line that names it. The warning names the SVG and says to look at it and run `wfctl arch accept` on the record. Superseded and retired records get neither warning, since their drawings no longer bind anything.
- **FR-022**: `wfctl arch accept` on an accepted record MUST append a `redrawn` Log line carrying the current fingerprints when at least one SVG no longer matches, or has no fingerprint on the Log, and MUST leave the status unchanged. It takes `--agreed` the same way. Before writing, it MUST run every acceptance check a proposed record gets, the failing-step rule included, and refuse on any of them, so a layout edit that drops `failing-step` can't be signed off. When every SVG matches, or the record has no SVG, it MUST refuse as it does today for an accepted record.
- **FR-023**: The worktree guard MUST refuse `wfctl arch accept` from an agent unless the command carries `--dry-run` as a whole shell word, with a message saying a person runs it in their own terminal. It reads each command separated by `;`, `&`, `|`, or a newline on its own, so a `--dry-run` in one command doesn't let another through, and `--dry-run` inside a quoted citation doesn't count.
- **FR-024**: `wfctl arch accept` without `--dry-run` MUST refuse unless stdin and stdout are both terminals, before it writes anything, the same check `wfctl review sign-off` and `wfctl arch approve-imports` make.
- **FR-025**: The SVG reader MUST refuse a DOCTYPE in the decoded text, not only in the raw bytes, so a UTF-16 or UTF-32 file can't hide one. An SVG that isn't UTF-8 MUST be refused with the `can't be read` problem, since GitHub and the style file both assume UTF-8.
- **FR-026**: A record whose only change on the branch is added `redrawn` Log lines MUST NOT count as a record the branch changed. This holds for the record gate that refuses a PR, the design gate that reads whether the boundary question was answered, with or without a domain-page name list, the `Boundary` line a session records, and the `record:` lines that say what a branch decided. The record MUST be accepted, and the added lines MUST sit in its `## Log`. Any other edit counts, committed or not, and a new or untracked record is never a redraw. Without it, a branch that only fixes a drawing's layout would have its PR refused for touching a record while it truthfully says no boundary moved, and deleting that answer would let a picture plus a Log line answer the boundary question.

## Key Entities _(include if feature involves data)_

- **Drawing**: The picture under a record's `## Boundary`, or under one `### <kind>` heading. It's a fenced block or a linked SVG.
- **SVG drawing**: A file in `drawings/` under the architecture root, named `<slug>-<kind>.svg` by convention. Its `<text>` elements are its labels, and an element with the `failing-step` class marks a sequence's failing step.
- **Drawing summary**: What wfctl reads from one drawing, whatever its format: the labels, whether it shows a failing step, and the labels past its edge.
- **Drawing style file**: The one file stating how an SVG drawing should look, linked from the four skills that teach drawing.
- **Drawing fingerprint**: The first 12 hex digits of an SVG's SHA-256, written on the `accepted` or `redrawn` Log line beside the SVG's link. It records which version of the drawing the user looked at.

## Success Criteria _(mandatory)_

### Measurable Outcomes

- **SC-001**: A record whose only drawing is a linked SVG passes `wfctl arch accept --dry-run` with no drawing blocker.
- **SC-002**: All 47 records that carry a mermaid drawing today get the same acceptance result and the same `wfctl doctor` findings after the change.
- **SC-003**: `record-drawing-can-be-svg.md` passes `wfctl arch accept --dry-run` with its mermaid block removed.
- **SC-004**: A sequence SVG without the `failing-step` class is refused at acceptance, and adding the class to one element clears the refusal with no other edit.
- **SC-005**: The "file missi" overflow from the first #740 drawing produces an edge warning when recreated, and the corrected drawing produces none.
- **SC-006**: The drawing style rules appear in exactly one file under `wfctl/agents/skills/`, and the four skills that teach drawing each link to it.
- **SC-007**: Editing an accepted record's SVG produces a doctor warning, and running `wfctl arch accept` on that record from a terminal clears it with one `redrawn` Log line.
- **SC-008**: `wfctl arch accept <slug> --agreed "<where>"` run through the agent's shell is refused by the guard, and `wfctl arch accept --dry-run -- <slug>` isn't.

## Validation Strategy _(mandatory)_

- `uv run pytest -q`, `uv run ruff check wfctl/ tests/`, `uv run mypy`, and `python3 .github/scripts/check_imports.py` all pass.
- A failing test first for an SVG in `drawings/` being counted as a record by the design gate, then the fix.
- Tests for each acceptance refusal this change adds (missing file, outside `drawings/`, invalid XML, a DOCTYPE in a UTF-16 file, sequence SVG with no `failing-step`), and for the doctor warnings (label missing from prose, label past the edge, no edge to measure, an accepted record's broken SVG, an accepted record's changed SVG).
- Tests for the fingerprint: the `accepted` Log line carries it, CRLF and LF copies match, a `redrawn` line clears the warning, and a matching record still refuses a second accept.
- Tests for the guard: `wfctl arch accept` with `--agreed` is refused, `--dry-run` isn't, and `--dry-run` in one command doesn't let a second command through. A test that accept refuses without a terminal.
- Each drawing check is tested once with an SVG summary and once with a mermaid summary.
- A one-off comparison in the scratchpad, not committed, showing every record on disk gets the same acceptance result and doctor findings before and after the change, apart from the reworded fix text (plan research R-010).
- A test that each of the four links to the style file resolves.
- `uv run wfctl install-skills`, then have an agent draw one record's SVG from the `architecture-decisions` skill, render it with `qlmanage`, and check it against the style file.
- `uv run wfctl arch accept --dry-run -- record-drawing-can-be-svg` after removing its mermaid block.
- `uv run wfctl doctor` and `uv run wfctl check config` report nothing new.

## Assumptions

- Pre-specify design context loaded from `design.md` in this folder.
- `record-drawing-can-be-svg.md` and both level-3 records are proposed. This spec follows them as written, and changes if the user rejects any of them.
- Every SVG goes in the one `drawings/` folder until #761 decides how architecture documents are grouped by context. A per-kind folder under `design/` would let a branch pass the brainstorm's software-design step with only a picture, since any change under `design/` satisfies that step.
- GitHub's mobile app honors the media query inside an SVG shown as an image. The desktop site does, and the user rated the risk low, so no fallback is planned. The user checks both modes in the mobile app before the PR merges, as `quickstart.md` lists.
