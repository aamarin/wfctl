# Clarify scan: #544

## Session 2026-11-02

- Verdict: satisfied
- Scanned: spec.md
- Asked: 4 · Answered: 4 · Outstanding: 0 · Deferred: 2
- Detail: /Users/andremarin/Development/wfctl-specs/544-package-per-context/spec.md § Clarifications

### Coverage

| Category | Status |
| --- | --- |
| Functional Scope & Behavior | Resolved |
| Domain & Data Model | Resolved |
| Interaction & UX Flow | Clear |
| Non-Functional Quality Attributes | Clear |
| Integration & External Dependencies | Deferred |
| Edge Cases & Failure Handling | Resolved |
| Constraints & Tradeoffs | Resolved |
| Terminology & Consistency | Resolved |
| Completion Signals | Clear |
| Misc / Placeholders | Deferred |

### Findings

- **Domain & Data Model**: The record lets any context import the shared core
  and the tracker package, but neither had a name the check could read.
  Q: How does the check know which modules are the shared core and the tracker
  package? → A: Both become subpackages, `wfctl/core/` and `wfctl/tracker/`. The
  domain page lists them under the Bounded Contexts table as a Shared Kernel and
  an Anticorruption Layer, and the check reads both names from there.
  Basis: the user chose it in chat, after asking for the Python convention for a
  shared directory.
  Decided against **hardcoding `core` and `tracker` in the check**: the check
  takes every other package name from the domain page, and a second source for
  two of them is a list a reader has to find.
  Decided against **no name until the packages exist**: the baseline's placement
  lines need a name to place `_paths.py` and `_tracker.py` in.
- **Edge Cases & Failure Handling**: The spec said the baseline only shrinks, but
  nothing checked that. An agent that hit a failure could add a baseline line or
  a map arrow and turn the check green.
  Q: What stops an agent from turning the check green by editing what the check
  reads? → A: The check compares the branch's baseline and Context Map against
  the copies on `main`, and fails on any line or arrow the branch adds until a
  person approves it from their own terminal. The mermaid parser fails on any
  line it can't parse instead of skipping it.
  Basis: the user raised the risk of an agent misreading or working around the
  check, and agreed to this answer. The approval follows `wfctl review sign-off`,
  which the worktree guard already refuses when an agent runs it.
  No options offered — short answer.
- **Functional Scope & Behavior**: The user asked whether the boundary belongs on
  the map alone, with no directory moves.
  Q: Do the contexts still move into packages, or does the boundary live only on
  the Context Map? → A: They move into packages, so a module's context comes from
  its path and the placement lines disappear as each context moves.
  Basis: the user chose the recommendation in chat.
  Decided against **the boundary on the map only**: the placement lines would be
  permanent, every new module would need an approved line, and an agent could
  change a module's context by editing a line instead of moving a file.
- **Constraints & Tradeoffs**: The spec made exactly one plain-named module per
  package public, and research found no Python project or guide that does this.
  Q: What may another context import from a package? → A: Only the package
  itself. Its `__init__.py` re-exports the public names lazily and lists them in
  `__all__`, and every module inside it keeps a leading underscore.
  Basis: the user chose it in chat, after three research passes. SQLAlchemy,
  attrs, httpx, pydantic, and Textual re-export from `__init__.py`, and Textual
  and pydantic do it lazily. Griffe's public-API guide recommends the same
  layout.
  Decided against **any plain-named module is public**: a caller imports a file
  by name, so the context can't split or rename that file without breaking the
  caller, and a new plain-named file widens the surface with nobody deciding to.
  Decided against **exactly one public module**: no project or guide uses it,
  and lazy re-exports keep the guard's start-up as cheap as it would.
- **Terminology & Consistency**: "public module" no longer names anything once
  the package is the public surface. The spec and `contexts-are-packages.md` now
  say "the package" and "public surface", and the record's Log carries the
  amendment.
  Basis: follows from the previous finding.
  No options offered — short answer.

### Deferred

- **Integration & External Dependencies**: whether mypy supports Python 3.15's
  `lazy` imports. Ruff 0.15.22 does, and mypy's issue is still open. The first
  move under #671 picks between `lazy` imports and a module-level `__getattr__`,
  so the answer belongs there, and nothing on this branch depends on it.
- **Misc / Placeholders**: the command a person runs to approve a new baseline
  line or map arrow, and where the approval is stored. FR-015 fixes the rule and
  leaves the mechanism to the plan.
