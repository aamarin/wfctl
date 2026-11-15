# Clarify scan: 740-svg-drawings

## Session 2026-11-14

- Verdict: satisfied
- Scanned: spec.md
- Asked: 4 · Answered: 4 · Outstanding: 0 · Deferred: 1
- Detail: /Users/andremarin/Development/wfctl-specs/740-svg-drawings/spec.md § Clarifications

### Coverage

| Category | Status |
| --- | --- |
| Functional Scope & Behavior | Clear |
| Domain & Data Model | Resolved |
| Interaction & UX Flow | Clear |
| Non-Functional Quality Attributes | Clear |
| Integration & External Dependencies | Deferred |
| Edge Cases & Failure Handling | Resolved |
| Constraints & Tradeoffs | Resolved |
| Terminology & Consistency | Clear |
| Completion Signals | Clear |
| Misc / Placeholders | Clear |

### Findings

- **Edge Cases & Failure Handling**: the spec didn't say which drawing counts when one heading carries both an SVG image and a mermaid block.
  Q: When one heading carries both, which one is the drawing? → A: Neither. A heading's drawing is an SVG or a mermaid block, never both. Acceptance refuses a heading with both, and `wfctl doctor` warns while the record is proposed.
  Basis: the user chose it ("Should be really svg or mermaid I think").
  Decided against **The first one wins**: the record would pass while carrying a second drawing nobody checks, and the two could disagree.
  Decided against **The SVG wins**: same problem as first-wins, with the mermaid copy left in the record unchecked.
- **Domain & Data Model**: the spec left open where a view's SVG goes, and said nothing about a level-3 design record's SVG.
  Q: Do architecture records, design records, and views all put their SVGs in one `drawings/` folder, named after the document that links each one? → A: Yes, for now. The user pointed out that architecture documents aren't grouped by context, which is filed as #761. #761 moves each drawing along with its document once the layout is decided, and also covers checking a design record's drawing, since design records first need to name their contexts.
  Basis: the user chose it and asked for #761 to be filed and linked from #740.
  Decided against **The view's SVG sits beside the view under `views/`**: two folders mean two rules to teach, and `drawings/` already does the job.
  Decided against **A per-kind folder such as `design/drawings/`**: any change under `design/` satisfies the brainstorm's software-design step, so a branch could pass that step with only a picture.
  Decided against **Folders per context in this change**: the layout needs its own design, so it moved to #761 rather than holding #740.
- **Constraints & Tradeoffs**: FR-002 required the name `<slug>-<kind>.svg` without saying whether anything enforces it.
  Q: Does wfctl enforce the file name, or only the folder? → A: Only the folder. The name is a convention the skills teach.
  Basis: the user chose it.
  Decided against **Enforce the exact name**: a wrong name breaks nothing, since the record links whichever file it names, and the check would change again when #761 regroups the drawings.
- **Edge Cases & Failure Handling**: the edge warning needs each label's font size, and the spec didn't say where wfctl reads it.
  Q: Where does wfctl read a label's font size? → A: From both the attributes and the CSS. A `font-size` attribute on the `<text>` or its nearest group comes first, then a single-class rule in the SVG's `<style>` block, then the SVG default of 16.
  Basis: the user answered "Well both" to the recommended attributes-only option, read as attributes and CSS.
  Decided against **Attributes only, default 16**: a drawing that sizes its text in CSS would get no warning or a wrong one, and the style guide teaches classes.

### Deferred

- **Integration & External Dependencies**: nobody has tested whether GitHub's mobile app honors the `prefers-color-scheme` media query inside an SVG shown as an image. That's a check on a real device, not a spec question, and the spec's Assumptions already says it's untested.
