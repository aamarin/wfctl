# SVG drawings that wfctl checks

Contexts: architecture-records, design-method

## Problem Statement

Records and architecture views carry hand-drawn SVG drawings that read at a glance on GitHub, and wfctl checks an SVG drawing the same way it checks a mermaid one.

## Recommended Direction

Mermaid renders poorly on GitHub. Its layout engine places the nodes itself, labels overlap, and the refused edge or the failing step is hard to find. The hand-drawn SVGs from the #739 brainstorm read better. Currently, `wfctl arch accept` rejects a record whose only drawing is an SVG with "no drawing", since every check reads a mermaid fence.

A record's drawing can now be an SVG file in the `drawings/` folder under the arch root, named `<slug>-<kind>.svg`. The record links it with a markdown image under `## Boundary`, or under `### <kind>` when it declares several kinds. wfctl counts the link as the drawing and reads two things from the file:

1. The labels, from its `<text>` elements. The label check compares them against the record's prose, as it does for mermaid.
2. A sequence's failing step, from an element with the class `failing-step`. A `sequence` record needs at least one.

The edge the owning side refuses carries the class `refused-edge`, and the SVG's own style colors it red. No check reads that class. We didn't use the color as the marker, because the check would compare color values and miss a failing step drawn in a second shade of red or a dark-mode color.

The SVG switches its colors with a `prefers-color-scheme` media query and fills its own background with GitHub's page color, `#ffffff` in light mode and `#0d1117` in dark mode. Without the background, a dark-mode device viewing GitHub's light theme shows dark-mode labels on a white page, and they're nearly invisible. With it, the drawing blends in when the themes match and shows as a readable card when they don't. The colors follow the device setting, not GitHub's theme toggle.

Nothing lays out a hand-drawn SVG, so a label can run past the drawing's edge with no error. `wfctl doctor` warns when a proposed record's SVG has a label past the edge, estimated from its character count. The skills tell the agent to render the drawing and look at it before committing. The user's review before acceptance catches the rest. We didn't make rendering a brainstorm sub-step, because its only evidence would be a PNG, which proves the agent rendered the drawing, not that it looked at it. Rendering also needs a tool such as `qlmanage` on macOS, and wfctl takes no dependencies.

Mermaid fences keep passing every check, so existing records don't change. The skills teach SVG as the default. The style rules are written once, in a new `design-levels/references/drawing-style.md`, and the four skills that carry diagram guidance link to it:

1. Boxes on a grid, so related boxes line up and the reader follows rows and columns.
2. A short label on every arrow, since an unlabeled arrow leaves the reader to guess what crosses.
3. The refused edge in red, through the `refused-edge` class, so the claim the decision rejects stands out.
4. A one-line caption under the drawing saying what it shows.
5. The page-colored background and the media query described above.
6. The `failing-step` and `refused-edge` classes, the only two names a check or the style depends on.
7. Rendering the drawing and looking at it before committing, since nothing else catches a label that crosses a line.

Views have no drawing check today. wfctl only checks whether a view exists and whether the code it covers has changed since. A view can link an SVG with no change to wfctl, and the view templates teach SVG the same way the record template does.

## Boundaries and Ownership

1. wfctl checks whether a record has a drawing, whether the SVG's labels appear in the prose, and whether a sequence shows its failing step. These read only the record and the file, so wfctl can run them at acceptance without asking anyone. This is recorded in `docs/architecture/record-drawing-can-be-svg.md`.
2. The author marks the failing step with the `failing-step` class. wfctl shouldn't infer it from the picture, since it would have to guess from a stroke color or a path's shape. A wrong guess would give the author a refusal they can't argue with.
3. wfctl decides where the SVG is stored. The design gate asks git whether anything under the arch root changed, skipping the folders that hold no records. An SVG beside its record would count as a changed record, so a branch could answer the boundary question with only a picture. That's why `drawings/` joins `views/` and `scans/` on that list.
4. The user decides whether a drawing reads well. wfctl's edge warning catches a label running off the drawing, not one crossing a line or a confusing layout.

## Key Assumptions to Validate

- [ ] GitHub's mobile app honors the `prefers-color-scheme` media query inside an SVG shown as an image. Test it by opening `record-drawing-can-be-svg.md` in the app with the phone in dark mode.
- [ ] A label's width, estimated from its character count and font size, catches the overflows a reader sees. Test it against the drawings the skills teach, including the "file missi" label from the first drawing.
- [ ] Python's bundled expat is safe enough for SVG files committed to the repository. Expat 2.4.1 and later limit entity expansion, and wfctl requires Python 3.11, whose bundled expat is 2.6.3 here.
- [ ] An agent drawing for a record follows the link to `drawing-style.md` and draws in that style. Test it after `uv run wfctl install-skills` by drawing one record's SVG from the `architecture-decisions` skill.

## MVP Scope

In scope:

1. One drawing reader that turns a fence or an SVG link into a summary of labels, whether a failing step is shown, and labels past the edge. The four drawing checks read only the summary.
2. `wfctl arch accept` counting an SVG link as the drawing, and rejecting a link to a missing file, naming the path.
3. The label check and the sequence check reading SVG through the summary.
4. The `wfctl doctor` warning for a label past the edge, on proposed records only.
5. `drawings/` added to the folders under the arch root that hold no records.
6. `design-levels/references/drawing-style.md`, linked from `design-levels`, `architecture-decisions`, `software-design-decisions`, and `model-the-domain`, with a test that each link resolves.
7. The record and view templates teaching SVG as the default.
8. Removing the mermaid copy from `record-drawing-can-be-svg.md`, and the line under it that says "crossed in the mermaid copy", once the checks read SVG.
9. A release note, `changes/740.addition.md`.

## Not Doing (and Why)

1. Redrawing existing mermaid records as SVG. Mermaid keeps passing, so nothing breaks, and redrawing the 47 records that carry a mermaid drawing is separate work.
2. Detecting a label that crosses a line or another label. That needs a layout engine or a renderer, and wfctl takes no dependencies. The agent's look at the rendered drawing and the user's review cover it.
3. A rendering sub-step in brainstorm. A PNG proves the agent rendered the drawing, not that it looked at it.
4. Following GitHub's theme toggle. An SVG shown as an image can only see the device's color setting.
5. Checking a view's drawing. Views have no drawing check today, and adding one is #743's scope.

## Open Questions

- Whether a view's SVG goes in the same `drawings/` folder as a record's, or beside the view under `views/`, which is already excluded from the record readers.

## Software design decisions

- docs/architecture/design/740-one-drawing-reader.md — one reader turns a fence or an SVG into the same drawing summary, and the four checks read only the summary
- docs/architecture/design/740-drawing-style-one-file.md — the drawing style lives in one `design-levels` reference file that the four diagram skills link to
