# Feature Specification: Check imports against the Context Map

**Feature Branch**: `544-package-per-context`  
**Created**: 2026-11-02  
**Status**: Draft  
**Input**: User description: design.md in this folder, from the brainstorm for #544

## Clarifications

### Session 2026-11-02

- Q: How does the check know which modules are the shared core and the tracker package? → A: Both become subpackages, `wfctl/core/` and `wfctl/tracker/`. The domain page lists them under the Bounded Contexts table by their Context Map pattern, with the shared core as a Shared Kernel and the tracker package as an Anticorruption Layer. The check reads both names from that list.
- Q: What stops an agent from turning the check green by editing what the check reads? → A: The check compares the branch's baseline and Context Map against the copies on `main`. A baseline line or map arrow that the branch adds fails the check until a person approves it. How that approval is recorded is decided in the plan. The parser also fails on any line in the map's mermaid block that it can't parse, instead of skipping it.
- Q: Do the contexts still move into packages, or does the boundary live only on the Context Map? → A: They move into packages, as `contexts-are-packages.md` decides. A module's context comes from its path, so the placement lines in the baseline disappear as each context moves, and an agent can't change a module's context without moving the file.
- Q: What may another context import from a package? → A: Only the package itself, such as `from wfctl.evidence import derive`. Each package's `__init__.py` re-exports its public names lazily and lists them in `__all__`, and every module inside it keeps a leading underscore. This lets a context split or rename its own files without breaking callers, and it keeps the list of what it offers in one file.

## User Scenarios & Testing _(mandatory)_

The domain page draws wfctl's seven bounded contexts and a Context Map of which
context may depend on which. Today nothing checks the code against that map, and
the code already breaks it once. This feature adds a check that fails a change
whose imports break the map, and tells the developer what to do instead. No
module moves in this feature. The moves come later, one context per PR under
#671, and each one leans on this check.

The developer below is whoever changes wfctl's code, a person or an agent. The
maintainer is the person who owns the domain page and decides what the map
draws.

### User Story 1 - An import the map doesn't allow fails the change (Priority: P1)

A developer adds an import from one context into another, and the Context Map
draws no arrow that allows it. `wfctl verify` and CI both fail. The failure
names the file and line, both contexts, and draws the boundary the import
crosses. It also says what to do instead: move the code into the importing
context, or ask the maintainer to add the arrow to the map.

**Why this priority**: This is the check's reason to exist. Without it, a
dependency the map doesn't draw lands without anyone deciding it, as the status
code's import of the session module did.

**Independent Test**: Add an import from an Evidence and derivation module into
a Session continuity module, run the check, and confirm it fails with both
context names and the drawn boundary. Remove the import and confirm it passes.

**Acceptance Scenarios**:

1. **Given** a module in Evidence and derivation, **When** it imports a module
   in Session continuity, **Then** the check fails, because the map draws the
   arrow only the other way.
2. **Given** a module in Session continuity, **When** it imports from the
   `wfctl.evidence` package, **Then** the check passes, because the map draws
   that arrow.
3. **Given** two modules in the same context, **When** one imports the other,
   **Then** the check passes, since imports inside one context aren't checked.

---

### User Story 2 - Other contexts import a context's package, never its modules (Priority: P1)

Each context's package lists what it offers other contexts in its
`__init__.py`, which re-exports those names from the package's underscore
modules and names them in `__all__`. A developer in one context imports a
module inside another context's package, such as `wfctl.evidence._status`,
instead of the package itself. The check fails even when the map allows the
dependency, and tells the developer to import from `wfctl.evidence`, or to
export what they need there.

**Why this priority**: Without this rule, an allowed dependency reaches any
module in the other context. That context then can't split or rename its own
files without breaking a caller it never agreed to have.

**Independent Test**: In a context the map allows, import a module inside
another context's package and confirm the check fails. Import the same name from
the package instead and confirm it passes.

**Acceptance Scenarios**:

1. **Given** the map allows Session continuity to depend on Evidence and
   derivation, **When** a Session continuity module imports
   `wfctl.evidence._status`, **Then** the check fails and names
   `wfctl.evidence` as the place to import from.
2. **Given** any context, **When** a module imports the shared core or the
   tracker package, **Then** the check passes, since those two packages may be
   imported from anywhere.
3. **Given** `cli.py`, **When** it imports from any context's package, **Then**
   the check passes, and **When** it imports a module inside a context's
   package, **Then** the check fails.

---

### User Story 3 - Today's violations are listed, and the list only shrinks (Priority: P2)

The code breaks the rules today, and the flat modules have no package to say
which context they belong to. The check ships with a baseline file that lists
each unmoved module's context and each import that breaks the rules today. The
check passes on the current code with that baseline, fails on any new
violation, and fails on any baseline line that no longer matches anything.

**Why this priority**: Without the baseline, the check either fails on the
current code or passes everything until the first move. Without the shrink
rule, a fixed import can quietly come back.

**Independent Test**: Run the check on the current code and confirm it passes.
Delete one import that the baseline lists and confirm the check fails until
that baseline line is removed.

**Acceptance Scenarios**:

1. **Given** the current code and the shipped baseline, **When** the check runs,
   **Then** it passes.
2. **Given** a baseline line for an import, **When** that import is removed from
   the code, **Then** the check fails and says to delete the line.
3. **Given** a baseline line that places a module in a context, **When** that
   module moves into its package or is deleted, **Then** the check fails until
   the line is removed.
4. **Given** a new module outside every package, **When** the baseline has no
   line for it, **Then** the check fails, so a new flat module can't skip it.
5. **Given** the baseline places the status modules in Evidence and derivation
   and the session module in Session continuity, **When** the check runs,
   **Then** the status code's import of the session module is a listed
   violation, not an allowed import.

---

### User Story 4 - The maintainer changes the map, and the check follows (Priority: P2)

The maintainer adds or removes an arrow on the Context Map, or renames a
context's package in the Bounded Contexts table. The check reads both from the
domain page, so its rules change with no edit to the check.

**Why this priority**: A second copy of the map in the check would drift from
the page that people read and accept.

**Independent Test**: Add an arrow to a copy of the domain page and confirm an
import the check refused before now passes.

**Acceptance Scenarios**:

1. **Given** an import the check refuses for lack of an arrow, **When** the
   maintainer adds that arrow to the map and approves the addition, **Then** the
   check passes.
2. **Given** an arrow from or to an outside party, **When** the check reads the
   map, **Then** it ignores the arrow, since outside parties aren't packages.
3. **Given** a domain page whose map or table the check can't read, **When** the
   check runs, **Then** it fails and names what it couldn't read, and never
   passes by treating the map as empty.

---

### User Story 5 - A bare "record" is kept for decision records (Priority: P3)

A developer exports a name from a context's package other than `arch`, and the
name is a bare `Record`, `record`, `records`, or `load_record`. The check fails
and asks for a qualified name, such as `CompletionRecord` or `load_verdict`.

**Why this priority**: The domain page now reserves a bare "record" for
architecture and design decisions. Holding the public names to it keeps the two
meanings apart while the contexts move, and it's cheap to drop if it turns out
not to be worth it.

**Independent Test**: Export `load_record` from a package other than `arch` and
confirm the check fails. Rename it `load_verdict` and confirm it passes.

**Acceptance Scenarios**:

1. **Given** a context's package other than `arch`, **When** its `__all__`
   lists `Record`, **Then** the check fails.
2. **Given** a context's package other than `arch`, **When** its `__all__`
   lists `CompletionRecord`, **Then** the check passes.
3. **Given** an underscore module anywhere, **When** it defines `record` and
   its package doesn't export it, **Then** the check passes, since only exported
   names are checked.
4. **Given** the `arch` package, **When** its `__all__` lists `Record`,
   **Then** the check passes.

### Edge Cases

- A function-local import counts the same as a top-level one, since about half
  of wfctl's imports between modules are function-local.
- An import written as `from wfctl import _paths` followed by `_paths._name`
  counts as an import of `_paths`.
- A relative import (`from .. import x`) resolves to the same module an absolute
  import would.
- Tests under `tests/` aren't checked, since a white-box test imports internals
  on purpose.
- An indirect dependency, where Session continuity reaches Architecture records
  through the `wfctl.evidence` package, isn't a violation. The map is
  meant to compose that way.
- The shared core and the tracker package import no context. An import from
  either into a context fails.
- A branch that adds a placement line for a new flat module fails until a
  person approves it, since the placement decides which imports the module may
  make.
- A branch that deletes a baseline line or a map arrow passes, since removing
  either one only makes the check stricter.
- A module the baseline places in a context that has no package yet behaves as
  if it were in that package, except that another context may import the
  module directly, as FR-004 says.

## Requirements _(mandatory)_

### Functional Requirements

- **FR-001**: The check MUST read the allowed dependencies from the Context Map
  on the domain page, and treat an arrow `A --> B` between two contexts as
  allowing B to import A.
- **FR-002**: The check MUST read each context's package name from the Bounded
  Contexts table on the domain page. It MUST read the two shared package names,
  `core` and `tracker`, from the list under that table. A baseline placement
  line may place an unmoved module in either shared package.
- **FR-003**: The check MUST fail on an import between two contexts that the map
  doesn't allow, unless the baseline lists it.
- **FR-004**: An import from another context MUST name that context's package,
  such as `from wfctl.evidence import derive`. The check MUST fail on an import
  of any module inside another context's package, unless the baseline lists it.
  A module that hasn't moved into its package yet is exempt from this rule and
  is checked against the map only, since it has no package to import from.
- **FR-005**: The check MUST allow any module to import the shared core and the
  tracker package, and MUST fail on an import from either of them into a
  context.
- **FR-006**: Wiring is the layer above the contexts that routes a command to
  them and holds no logic of its own. Its files are `cli.py`, the full command
  line, and `_entry.py`, the console script, and no other file is wiring. The
  check MUST allow a wiring file to import from any context's package, and MUST
  fail on one importing a module inside a context's package. An unmoved module
  is exempt under FR-004.
- **FR-007**: The check MUST place a module in the context whose package holds
  it, or, for a module in no package, in the context its baseline line names.
- **FR-008**: The check MUST fail on a module in no package that has no
  baseline line, and on a module under a directory that is neither a listed
  package nor package data.
- **FR-009**: The check MUST fail on any baseline line that matches no current
  import or no current module.
- **FR-010**: The check MUST fail, naming what it couldn't read, when the domain
  page's map or table is missing or unreadable. It MUST also fail on any line
  inside the map's mermaid block that it can't parse, rather than skip it.
- **FR-015**: The check MUST compare the branch's baseline and Context Map
  against the copies on `main`. It MUST fail on any baseline line, map arrow,
  shared package, or context-to-package pair the branch adds, and on any
  change to the two files CI runs the check with, its own script, which holds
  the wiring list and the rules, and the CI workflow, until a person approves
  the addition. The person approves it
  by running a command in their own terminal, which the worktree guard refuses
  when an agent runs it, the same way it refuses `wfctl review sign-off`. The
  plan decides the command and how the approval is stored. Deleting a baseline
  line or a map arrow, moving a module, and adding an import the map already
  allows need no approval. The one exception is the branch that ships the
  check. `main` has no copy to compare it with, so the user approves its
  baseline and its two trusted files by merging its PR by hand, from their
  own terminal. CI enforces the comparison, since it runs `main`'s copy of
  both files. The local refusals don't have that strength. They stop an agent
  from taking a shortcut, but not one set on getting around them, such as by
  calling the approval code from its own Python, the same as `wfctl review
  sign-off` today.
- **FR-011**: Each failure MUST name the file and line, the contexts involved,
  why the rule exists, and what to do instead. Failures between two contexts
  MUST draw the boundary as shown in `contracts/failure-output.md`.
- **FR-012**: The check MUST fail when a context's package other than `arch`
  lists a bare `Record`, `record`, `records`, or `load_record` in its
  `__all__`, or binds one at the top level of its `__init__.py` by a
  definition, an assignment, or an import. A name left out of `__all__` can
  still be imported by name, so `__all__` alone doesn't keep it out.
- **FR-013**: `wfctl verify`, CI, and the test suite MUST all run the same
  script for the rules in FR-001 to FR-012. The comparison with `main` in
  FR-015 runs in CI, where a branch can't change which copy of the script
  runs, and in the approval command, since the test suite and `wfctl verify`
  run before a person has approved anything.
- **FR-014**: The shipped baseline MUST make the check pass on the code as it is
  when this feature merges, and MUST list the status code's import of the
  session module as a violation.

## Key Entities _(include if feature involves data)_

- **Context Map**: The arrows on the domain page between contexts and outside
  parties. Only arrows between two contexts matter to the check.
- **Bounded Contexts table**: The table on the domain page that names each
  context and its package.
- **Shared packages**: The list under that table. It names `core`, a Shared
  Kernel that holds the repo, branch, and trunk lookups, and `tracker`, an
  Anticorruption Layer that translates between wfctl and the trackers. Neither
  one is a context. Any module may import either one, and neither imports a
  context.
- **Baseline**: A file of two kinds of lines. A placement line gives an unmoved
  module's context. A violation line gives an import that breaks the rules
  today. Both kinds only shrink.
- **Public surface**: The names a context's package re-exports from its
  `__init__.py` and lists in `__all__`. Other contexts may import only these.
  Every module inside the package keeps a leading underscore.

## Success Criteria _(mandatory)_

### Measurable Outcomes

- **SC-001**: On the code at merge, the check passes with the shipped baseline,
  and every line in the baseline matches a current import or module.
- **SC-002**: Each refused case in the user stories fails with a message that
  names the contexts involved and the action to take, and none of the allowed
  cases fails.
- **SC-003**: The check finishes in under 5 seconds on wfctl's code, so adding
  it to `wfctl verify` doesn't slow the change noticeably.
- **SC-004**: Adding an arrow to the domain page's map changes the check's
  answer with no edit to the check.
- **SC-005**: The status code's import of the session module is on the
  baseline at merge, so the first move that resolves it has a line to delete.

## Validation Strategy _(mandatory)_

- `uv run pytest -q` runs the check over the real code, plus tests over small
  fixture packages and a fixture domain page for every acceptance scenario
  above.
- `uv run ruff check wfctl/ tests/` and `uv run mypy`, which covers
  `.github/scripts/`.
- `uv run wfctl verify` passes with the check added to `wfctl.json`.
- `uv run wfctl check config` passes after the `verify` list changes.

## Assumptions

- Pre-specify design context loaded from design.md in this spec folder.
- The check lives in `.github/scripts/` beside the release note check, so mypy
  and CI already cover it.
- The first move decides how a package's `__init__.py` loads its re-exports
  without loading the whole context. It uses Python 3.15's `lazy` imports if
  mypy supports them by then, and a module-level `__getattr__` like Textual's
  if not. Until the first move, the flat modules are checked against the map
  only, so the baseline lists only the imports the map doesn't allow.
- The existing private-crossings test in `tests/test_architecture_view.py`
  stays as it is. The check doesn't replace it on this branch.
