# Clarify scan: Move the old review scans into their spec folders

## Session 2026-11-13

- Verdict: satisfied
- Scanned: spec.md
- Asked: 2 · Answered: 2 · Outstanding: 0 · Deferred: 0
- Detail: /Users/andremarin/Development/wfctl-specs/759-move-old-scans/spec.md § Clarifications

### Coverage

| Category | Status |
| --- | --- |
| Functional Scope & Behavior | Clear |
| Domain & Data Model | Resolved |
| Interaction & UX Flow | Clear |
| Non-Functional Quality Attributes | Clear |
| Integration & External Dependencies | Clear |
| Edge Cases & Failure Handling | Resolved |
| Constraints & Tradeoffs | Clear |
| Terminology & Consistency | Clear |
| Completion Signals | Clear |
| Misc / Placeholders | Clear |

### Findings

- **Domain & Data Model** — FR-003 said the folder is the path's component "directly under a spec root", but a scan's `Detail` path can come from another machine, whose spec root this command can't know.
  Q: How does the command pick the folder name out of a scan's `Detail` path? → A: The first path segment that starts with an issue key in the repository's tracker format followed by a hyphen, matched the way `extract_issue_key` matches a branch name, refusing `..`.
  Basis: the user accepted the recommendation, after asking for it in plain terms. They asked for spec folders without an issue key to be tracked separately, and that work is #760, which references this issue.
  Decided against **B** (the segment after one named `specs` or ending in `-specs`): it depends on how each repository names its spec storage folder, while the issue-key rule uses the tracker format wfctl already knows.
  Decided against **C** (the `Detail` file's parent folder): it picks the wrong folder when the file sits in a subfolder, such as `checklists/analysis-report.md`.
- **Edge Cases & Failure Handling** — the spec said two scans can target the same file, but not which one is written first in a single run, and the design's single `--append 656-plan-review.md` command depends on that order.
  Q: When two scans in one run target the same file, which goes first? → A: Scans are handled in ascending issue-number order, so `649-plan-review.md` is written first and `656-plan-review.md` then appends to it.
  Basis: the user accepted the recommendation.
  Decided against **B** (file-name order): it sorts names as text, so `1000-clarify.md` comes before `999-clarify.md`, and the order breaks once issue numbers differ in digit count.
  Decided against **C** (treat the second scan as a conflict within one run): it needs a second command after the first scan is stored, which contradicts the single-command run the design describes.
