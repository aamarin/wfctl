# Clarify scan for #739

## Session 2026-11-09

- Verdict: satisfied
- Scanned: spec.md
- Asked: 3 · Answered: 3 · Outstanding: 0 · Deferred: 0
- Detail: /Users/andremarin/Development/wfctl-specs/739-architecture-views/spec.md § Clarifications

### Coverage

| Category | Status |
| --- | --- |
| Functional Scope & Behavior | Resolved |
| Domain & Data Model | Clear |
| Interaction & UX Flow | Resolved |
| Non-Functional Quality Attributes | Clear |
| Integration & External Dependencies | Clear |
| Edge Cases & Failure Handling | Resolved |
| Constraints & Tradeoffs | Clear |
| Terminology & Consistency | Clear |
| Completion Signals | Clear |
| Misc / Placeholders | Clear |

### Findings

- **Edge Cases & Failure Handling**: the spec didn't say what session start prints in a repository with no architecture folder.
  Q: When a repository has no architecture folder at all, does session start still name its two required views as missing? → A: Yes. Every repository needs the two required views, and the reminder is how a new repository finds out.
  Basis: the user chose the recommended option.
  Decided against **B, stay quiet until the repository has an architecture folder**: a new repository would never learn it needs the views.

- **Interaction & UX Flow**: the spec grouped missing component views into one line, as a default nobody had confirmed.
  Q: When several component views are missing, does session start name them in one line or print one line each? → A: One line each, naming the file to create.
  Basis: the user said the length is intentional. In wfctl's own repository the lines keep #744 visible, and each one goes away once its view is drawn.
  Decided against **A, one line naming every missing view**: it hides the reminder the lines exist to give, and the agent has to work out each path itself.

- **Functional Scope & Behavior**: the spec filtered the views that exist by the branch's contexts, but didn't say whether missing views are filtered too.
  Q: On a branch that lists its contexts, does session start name every missing component view, or only those for the listed contexts? → A: Only the listed contexts, the same filter `wfctl arch context` applies to records.
  Basis: the user tied it to the move of each context into its own package (#671). Once that's done, wfctl can derive a branch's contexts from the files it edits, and the same filter keeps working unchanged.
  Decided against **B, every missing view on every branch**: it shows the agent views for parts of the system the branch doesn't change, while the records beside them are already filtered.

- **Functional Scope & Behavior**: while answering the questions above, the user asked whether anything besides the author can judge whether a view's boundaries are sound. The spec only checked that a view exists. FR-003a now makes the container and component view templates state the layout rule from Iglberger's *C++ Software Design*, which wfctl's level-3 design records already use. Stable parts go above a labeled line, arrows point toward the stable side, and an arrow pointing the wrong way is drawn in red.
  Decided against **leaving the templates without a layout rule**: the user reviews the views to spot bad boundaries but doesn't know the system's internals, so the drawing has to make a bad boundary visible.
  Decided against **having wfctl check a view against the code here**: the issue doesn't ask for it, and it stays in #743. The Context Map, the one picture of how the contexts depend on each other, gets the same layout in #745.

The other six categories were read and found Clear. The two proposed records settle who owns the list of required views and who declares diagram kinds. The edge cases list covers a missing domain page, a branch with no contexts, a branch that only edits a view, and a heading for an undeclared kind, which FR-012 refuses.
