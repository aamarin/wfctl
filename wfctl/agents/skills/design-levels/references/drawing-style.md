# Drawing style

This file is the one set of rules for drawing an SVG that a record, a design
record, or an architecture view links. `design-levels`, `architecture-decisions`,
`software-design-decisions`, and `model-the-domain` all link here, and none of
them keeps a copy. A fix to a rule goes in this file only.

A drawing is an SVG because GitHub renders it exactly as it was drawn. Mermaid
lets GitHub's layout engine place the boxes, so labels overlap and the edge the
reader needs to find gets lost. While a design gate is being answered in a
terminal, the sketch stays ASCII, since a terminal can't show an SVG. The SVG
is drawn when the answer lands in a document read on GitHub.

## Where the file goes

1. Save the SVG in the `drawings/` folder under the arch root, named
   `<slug>-<kind>.svg`. A record called `record-drawing-can-be-svg` with a
   `data-flow` drawing saves it as
   `drawings/record-drawing-can-be-svg-data-flow.svg`. `wfctl arch-root` prints
   the arch root.
2. Link it from the record with an inline markdown image, under `## Boundary`,
   or under `### <kind>` when the record declares several kinds:

   ```markdown
   ![wfctl reads a record's SVG, but a file in drawings/ never counts as a record](drawings/record-drawing-can-be-svg-data-flow.svg)
   ```

   Use this inline form, with a relative path and no leading `/`. wfctl doesn't
   read a reference-style image (`![alt][ref]`) yet, so a record linked that way
   is told it has no drawing (#777).
3. Don't write the `<svg>` element into the markdown. GitHub strips it, and the
   record shows nothing.

A level-3 design record or an architecture view saves its SVG in the same
folder, named after the file that links it. The link is relative to that file,
so it climbs out of the document's own folder first:

| Document | SVG | Link |
| --- | --- | --- |
| `design/<slug>.md` | `drawings/<slug>.svg` | `../drawings/<slug>.svg` |
| `views/system-context.md` | `drawings/system-context.svg` | `../drawings/system-context.svg` |
| `views/container.md` | `drawings/container.svg` | `../drawings/container.svg` |
| `views/components/<context>.md` | `drawings/<context>-component.svg` | `../../drawings/<context>-component.svg` |

No check reads a design record's or a view's drawing yet, so looking at it is
the only check it gets.

One `drawings/` folder and the `<slug>-<kind>.svg` name are temporary. #761
decides how records, views, and drawings are grouped, and moves each drawing
with the document that links it. Until then, wfctl checks that the SVG is in
`drawings/` but not what it's called, so the name is a convention.

Domain documents keep their mermaid drawings until #761 gives them a folder.

## What the drawing shows

1. **Boxes on a grid.** Every box sits at coordinates you choose, aligned in
   rows and columns, such as boxes 50 tall with their tops at `y="70"` and
   `y="230"`. Write absolute `x` and `y` values on every element. Don't put a
   `transform` on a label or on a group holding labels, because wfctl measures
   each label at its written `x` and would warn about the wrong position.
2. **A short label on every arrow.** Two to five words saying what crosses,
   such as "reads labels" or "file missing". An arrow with no label leaves the
   reader to guess what crosses it. Put the label beside the arrow's longest
   straight run. An arrow that bends is a `<path>` with absolute coordinates,
   such as `d="M85,70 V40 H660 V68"`.
3. **The refused edge in red.** The edge the owning side refuses carries
   `class="refused-edge"`, and its label carries `class="refused-label"`. The
   edge has no arrowhead. It stops at the refusing side's border with a red ✗.
   The label is the refused claim itself, such as "answers the boundary
   question", running from the side that would make it to the side that refuses
   it. Don't draw the claim as a box inside the side that makes it, since a box
   reads as one more step that side takes. This edge is usually the reason the
   record exists, so it should be the first thing the reader finds.
   An architecture view uses a different red class for a dependency that
   exists but points the wrong way, such as a stable module importing a
   volatile one. That arrow carries `class="wrong-way"` and keeps its
   arrowhead, since the code has the dependency and the reader needs its
   direction. Use the skeleton's red marker, `marker-end="url(#arrow-red)"`,
   and give its label `class="refused-label"`.
4. **The failing step of a sequence.** In a `sequence` drawing, the arrow for
   the step that fails, a `<line>` or `<path>`, carries `class="failing-step"`,
   and its label carries the red label class. wfctl refuses to accept a
   `sequence` record with no element carrying that class. Put it on the arrow
   rather than the label, since the skeleton's rule sets `fill: none` and would
   hide a label's text.
5. **A one-line caption** along the bottom, saying the decision in plain words.
   Use the same sentence as the image's alt text.
6. **Solid and dotted edges.** A solid arrow is a call the sender waits on. A
   dotted arrow (`stroke-dasharray`) is a value or a file read later.
7. **Sides as groups.** When the drawing has sides, such as the agent and
   wfctl, draw each side as a large rectangle with `class="group"` behind its
   boxes, with its name in the top-left corner in the `name` class. The
   skeleton's `.group` rule draws a dashed outline with no fill.
8. **A label that wraps** stays one `<text>` element, with each line in a
   `<tspan>` carrying its own `x` and `dy="1.3em"`. wfctl reads the whole
   element as one label, and measures each line on its own for the edge warning.
   Two separate `<text>` elements are two labels.
9. **Words from the record.** Every label, the caption included, shares at
   least one word with the record's prose outside `## Boundary`. `wfctl doctor`
   warns about a label on a proposed record that appears nowhere else in it,
   since that usually means the drawing and the text describe different things.
   A label with no words, such as a lone ✗ or ●, is skipped.

## Colors and the background

The drawing fills its own background with GitHub's page color, `#ffffff` in
light mode and `#0d1117` in dark mode, and switches with a
`prefers-color-scheme` media query. It blends into the page when the device and
GitHub use the same theme. If they differ, it shows as a card in the device's
theme, and its labels stay readable.

Put every color in the `<style>` block as a class rule, and set the class on the
element itself. A label carries its own class, such as
`<text class="label">`, rather than inheriting one from a group. Don't put a
`style` attribute on a label. wfctl reads a label's size and anchor from its own
attribute and class first, so an inline style or a size set only on a group can
make the edge warning miss a label that overflows, or flag one that fits (#776).

## A skeleton to start from

```svg
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 760 330" width="760" height="330" font-family="-apple-system, BlinkMacSystemFont, 'Segoe UI', Helvetica, Arial, sans-serif" font-size="13">
  <style>
    .bg { fill: #ffffff; }
    .box { fill: #f6f8fa; stroke: #57606a; stroke-width: 1.5; }
    .name { fill: #1f2328; font-weight: 600; font-size: 14px; }
    .label { fill: #1f2328; }
    .caption { fill: #59636e; font-size: 13px; }
    .edge { stroke: #57606a; stroke-width: 1.5; fill: none; }
    .later { stroke-dasharray: 5 4; }
    .head { fill: #57606a; }
    .head-red { fill: #cf222e; }
    .refused-edge { stroke: #cf222e; stroke-width: 2; fill: none; }
    .refused-label { fill: #cf222e; font-weight: 600; }
    .failing-step, .wrong-way { stroke: #cf222e; stroke-width: 2; fill: none; }
    .group { fill: none; stroke: #8c959f; stroke-width: 1; stroke-dasharray: 3 3; }
    @media (prefers-color-scheme: dark) {
      .bg { fill: #0d1117; }
      .box { fill: #161b22; stroke: #8b949e; }
      .group { stroke: #6e7681; }
      .name, .label { fill: #e6edf3; }
      .caption { fill: #9198a1; }
      .edge { stroke: #8b949e; }
      .head { fill: #8b949e; }
      .refused-edge, .failing-step, .wrong-way { stroke: #ff7b72; }
      .refused-label, .head-red { fill: #ff7b72; }
    }
  </style>
  <defs>
    <marker id="arrow" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="8" markerHeight="8" orient="auto-start-reverse">
      <path d="M0,0 L10,5 L0,10 z" class="head"/>
    </marker>
    <marker id="arrow-red" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="8" markerHeight="8" orient="auto-start-reverse">
      <path d="M0,0 L10,5 L0,10 z" class="head-red"/>
    </marker>
  </defs>
  <rect x="0" y="0" width="760" height="330" rx="8" class="bg"/>

  <rect x="20" y="70" width="130" height="50" rx="6" class="box"/>
  <text x="85" y="100" text-anchor="middle" class="name">record author</text>

  <line x1="150" y1="95" x2="298" y2="95" class="edge" marker-end="url(#arrow)"/>
  <text x="224" y="86" text-anchor="middle" class="label">writes the SVG</text>

  <text x="20" y="310" class="caption">The decision in one plain sentence.</text>
</svg>
```

`docs/architecture/drawings/record-drawing-can-be-svg-data-flow.svg` in the
wfctl repository is a complete drawing in this style, with a refused edge.

## Look at it before committing

No tool lays out a hand-drawn SVG, so a label can run past the edge or across a
line with no error. Render the file in both light and dark mode and look at
each PNG before committing. Headless Chrome renders the whole drawing and takes
the mode as a flag, `preferredColorScheme=1` for light and `0` for dark. Set
`--window-size` to the drawing's `width` and `height`:

```bash
"/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" --headless=new \
  --hide-scrollbars --window-size=760,330 --blink-settings=preferredColorScheme=1 \
  --screenshot=<scratchpad>/light.png "file://$(wfctl arch-root | head -n 1)/drawings/<slug>-<kind>.svg"
```

`wfctl arch-root` prints the absolute path of the folder holding `drawings/`,
so the command works from anywhere in the repository. `head -n 1` keeps only
that path, since the command adds a warning line when the folder is outside
the repository.

That's the macOS path. On Linux, the binary is usually `google-chrome` or
`chromium`. macOS's `qlmanage -t` is quicker, but it renders only in the
system's mode and crops a drawing wider than about 760, so use it only for a
drawing that size or smaller.

While a record is proposed, `wfctl doctor` estimates each label's width from
its character count and warns about one that runs past the drawing's edge. It
can't tell when a label crosses a line, so looking is the only check for that.

## Changing an accepted record's drawing

Accepting a record is how the user signs off on its drawing. `wfctl arch accept`
writes each SVG's fingerprint on the record's `accepted` Log line, and `wfctl
doctor` warns when an accepted record's SVG no longer matches it.

1. **A layout fix** changes only how the drawing looks, such as moving a box,
   shortening a label, or fixing a color. It's allowed, and the commit message
   says why the layout changed. The user then looks at the new drawing and runs
   `wfctl arch accept` on the record, which appends a `redrawn` Log line with
   the new fingerprint and leaves the status alone. An agent shouldn't run it,
   since it can't see a visual problem, and the worktree guard refuses it
   without `--dry-run`.
2. **A change to what the drawing shows**, such as a new box, a different
   arrow, or a refused edge that moved, changes the decision. It needs a new
   record that supersedes this one.
