# Feature Specification: declare pipeline step

**Feature Branch**: `339-declare-pipeline-step`
**Created**: 2026-09-16
**Status**: Draft
**Input**: User description: "" (empty command; design context loaded from `design.md`)

## Clarifications

### Session 2026-09-16

- Q: Must a pass's name be unique across the whole pipeline, or only within the step it is declared under? → A: Only within its step — two steps may each declare a pass called `scan`. The name is written bare in the position view, where the row's indentation under its step already qualifies it, and qualified as `<step>.<name>` wherever it is typed as an argument or written into a path. A bare name given as an argument resolves only where exactly one declared pass carries it, and is otherwise refused with the qualified candidates named. It is never resolved against the step that happens to be current: the current step is inferred from artifacts rather than set by the author, so a bare name would change meaning as unrelated work lands, with nothing on screen to say it had.

- Q: Where is a declared pass whose command is not installed reported, and does it fail? → A: In a check over the repository's own configuration — the shape `tracker-check` already has — exiting non-zero on a finding. Not in the drift report, whose remit is state wfctl installed rather than configuration a repository wrote for itself. A pass may declare that no command runs it, and such a pass is not reported, so a stage a person performs by hand is expressible rather than tolerated as a dead declaration.
- Q: FR-011 forbids a pass from recording whether it belongs to the repository or the tool, while FR-021 requires repository-declared passes to default to waiting for review. How is the default decided? → A: By which list the pass was read from, applied as that list is read. Nothing on the pass records its origin, so a pass moved from the bundle into configuration changes where the list came from and nothing else, and a repository that overrides the default produces a pass indistinguishable from a tool-shipped one. A run granted autonomy with `--auto-approve` walks past a pass that requires review, the same as it walks past the design gates.
- Q: A step carries passes from two lists — the tool's own and the repository's. In what order do they run? → A: Written order within each list, with the tool's passes first, and a repository may override that for one of its passes by naming the sibling it goes before or after. The default therefore needs no configuration, and interleaving is available to a repository that needs its pass earlier rather than being ruled out. FR-002's prohibition on a declaration stating a position is about position in the step sequence, not order among one step's passes; it was narrowed to say so.
- Q: FR-004 caps nesting at one level. A repository that nests a pass below another pass — is it refused, or is the deeper pass ignored? → A: Refused, by the check in FR-022, which already reports a declared pass whose command is not installed. Ignoring it leaves the repository believing in a stage that never appears, which is the failure this feature exists to remove; a declaration wfctl silently discards is indistinguishable from one it never read. The cap itself is a cost decision rather than a limit of the design — a second level makes every view recursive and every consumer depth-aware, to express a nesting nobody has asked for — so it is reopenable by whoever finds they need it, and refusing is what makes the attempt visible when someone does.

## User Scenarios & Testing _(mandatory)_

### User Story 1 - A repository's own stage becomes a row the pipeline routes to (Priority: P1)

A team has a stage of their own that sits inside one of the eight steps — a UI
design pass that belongs between brainstorming and writing the spec. Today they
write that down in a skill nobody's tooling reads, and a feature that walked
straight past it looks exactly like one that ran it. They declare the pass in
their repository's own configuration, keyed by the step it belongs inside, and
from then on the pass is a row on screen, the step is not finished until the
pass is, and the tool names the command that runs it.

**Why this priority**: This is the whole of what the issue asks for. Without it
the other stories have nothing to hang from, and a repository's process stays
prose.

**Independent Test**: Declare one pass in a scratch repository's configuration,
run the status view, and confirm the pass appears indented under its step, that
the step reports unfinished while the pass is outstanding, and that the tool
hands out the declared command as what to run next.

**Acceptance Scenarios**:

1. **Given** a repository that declares one pass under a built-in step, **When**
   the author reads the pipeline position, **Then** the pass appears as its own
   row indented under that step, in the order it was written.
2. **Given** that pass has not run, **When** the author asks what to do next,
   **Then** the answer names the command the repository declared, not the
   built-in step's own command.
3. **Given** that pass has produced its artifact, **When** the author reads the
   position again, **Then** the pass reports finished and the step moves on.
4. **Given** a repository that declares no passes, **When** the author reads the
   position, **Then** the view is exactly what it is today.

---

### User Story 2 - wfctl's own passes report separately (Priority: P2)

Brainstorming is not one thing: it runs the design levels, escalates ownership
questions, and ends by writing the design document. Today all of that collapses
into a single state with one sentence hung off it, so an author is told the step
is unfinished and which single thing is missing, but not how many passes the
step has or which command produces the one that is outstanding. Those passes
become rows of the same kind the previous story introduced, shipped with the
tool rather than configured.

**Why this priority**: It is the evidence that the mechanism is the right one. A
mechanism that cannot express the tool's own passes would have been built for
one consumer and never tested against a second.

**Independent Test**: On a branch part-way through brainstorming, read the
position and confirm each pass reports its own state, and that the outstanding
one names the command that produces it.

**Acceptance Scenarios**:

1. **Given** a branch where the architecture pass has left its artifact and the
   design document has not been written, **When** the author reads the position,
   **Then** the architecture pass reports finished and the design document pass
   reports outstanding, each on its own row.
2. **Given** that same branch, **When** the author asks what to do next, **Then**
   the answer names the command that writes the outstanding artifact.
3. **Given** a pass shipped with the tool, **When** the author reads its row,
   **Then** nothing on it distinguishes it from a pass a repository declared.

---

### User Story 3 - A pass that does not apply is declared away, and the claim reaches a reviewer (Priority: P3)

A backend-only change reaches a UI design pass that has nothing to design. The
author says so in a sentence, that sentence lands in the change under review
where a reviewer can disagree with it, and the pipeline moves on. The settled-away
row then drops out of the ordinary view so the common case stays short, and a
single flag brings every row back.

**Why this priority**: Without it the first two stories install a gate with no
exit, and the pass that does not apply blocks the pipeline permanently. It is
last only because the first two must exist for there to be anything to declare
away.

**Independent Test**: Declare a pass inapplicable with a reason, confirm the
claim is part of the change under review, confirm the pipeline advances, and
confirm the row is hidden by default and shown with the flag.

**Acceptance Scenarios**:

1. **Given** an outstanding pass, **When** the author declares it inapplicable
   with a reason, **Then** the reason is written to a file that is part of the
   change under review and the pipeline advances past the pass.
2. **Given** a declared-away pass, **When** the author reads the position,
   **Then** the row is hidden.
3. **Given** a declared-away pass, **When** the author reads the position asking
   for everything, **Then** the row is shown carrying the reason that was
   written.
4. **Given** an empty or placeholder reason, **When** the author tries to declare
   a pass away, **Then** the attempt is refused and nothing is written.
5. **Given** a claim that cannot reach a reviewer because the destination is
   outside the working tree or ignored, **When** the author declares a pass away,
   **Then** they are told the claim will not be seen and the pipeline does not
   advance.
6. **Given** two passes on one branch declared inapplicable, **When** the author
   reads both claims, **Then** both survive — neither has overwritten the other.

### Edge Cases

- A pass is declared under a name that is not one of the built-in steps: the
  declaration names no anchor, and the author is told which names are available
  rather than having the pass silently ignored.
- A pass is declared away while it is the one holding the pipeline: the row stays
  visible until it is settled, so a step never reports itself unfinished with the
  reason off screen.
- A repository declares several passes under one step: all of them appear, in the
  order written, and none of them declares a position of its own.
- Two steps each declare a pass under the same name: both are accepted, both are
  addressable as `<step>.<name>`, and the bare name is refused with both
  candidates named rather than resolving to either.
- A pass whose artifact is produced by a step other than its own — the pass whose
  evidence is a heading inside another step's file — reports finished from that
  heading, not from a file of its own.
- The same pass is declared away twice on one branch: the second claim replaces
  the first, because that is the author changing their mind about one pass rather
  than making a second claim.
- A pass is declared away, and a later commit produces its artifact anyway: the
  claim stands, because whether a pass applies is a person's judgment and no
  artifact overturns it.
- A repository declares a pass whose command is not installed in that repository:
  the configuration check names the pass and the missing command and exits
  non-zero, unless the pass declared that a person performs it.
- A repository nests a pass below another pass: the configuration check names the
  declaration and exits non-zero, rather than loading the outer pass and dropping
  the inner one, so the author learns the cap exists at the point they hit it.

## Requirements _(mandatory)_

### Functional Requirements

- **FR-001**: A repository MUST be able to declare one or more passes belonging
  inside a built-in pipeline step, without any change to the tool's own source.
- **FR-002**: A declaration MUST be keyed by the name of the step the pass
  belongs inside, so that no declaration states a position in the step sequence
  and reordering the step table breaks nothing. Order among the passes of one
  step is a separate question, governed by FR-003.
- **FR-002a**: A pass's name MUST be unique among the passes declared under one
  step. The same name under two different steps MUST be accepted, so that a
  repository adding a pass is never refused on account of a pass under a step it
  did not name.
- **FR-002b**: A pass MUST be addressed as `<step>.<name>` wherever the name is
  typed as an argument or written into a path, and MUST be presented bare in the
  position view, where the row's indentation under its step already carries the
  qualification.
- **FR-002c**: A bare name given as an argument MUST resolve only where exactly
  one declared pass carries it, and MUST otherwise be refused with the qualified
  candidates named. It MUST NOT resolve against the step that is current, which
  is inferred from artifacts rather than set by the author and therefore moves as
  unrelated work lands.
- **FR-003**: Where a step has several passes, the system MUST present and run
  them in the order they were written, with the tool's own passes before a
  repository's. A repository MUST be able to override that for one of its passes
  by naming the sibling it goes before or after, so the default holds without
  configuration and a repository that needs its pass earlier can say so.
- **FR-003a**: A pass naming a sibling that does not exist under its step, and a
  set of passes whose stated order cannot be satisfied, MUST both be reported by
  the check in FR-022 rather than resolved to some arbitrary order.
- **FR-004**: The system MUST nest passes exactly one level below a step. A
  declaration that nests a pass below another pass MUST be reported by the check
  in FR-022, and MUST NOT be dropped silently.
- **FR-005**: The pipeline position MUST report each pass with a state of its own
  drawn from the same set a step uses, rather than collapsing a step's passes
  into one state.
- **FR-006**: A step MUST report unfinished while any of its passes is
  outstanding.
- **FR-007**: Where an outstanding pass is what holds the pipeline, the system
  MUST name that pass's command as what to run next, or — where the pass declares
  that no command runs it — name the pass and say that a person performs it.
- **FR-008**: A pass MUST determine whether it has run by evaluating an evidence reader,
  not by testing for a file at a fixed path — so that a pass whose evidence is a
  section inside another step's artifact can report correctly.
- **FR-009**: A repository MUST be able to express the common case — this pass
  has run when this file exists — without writing a reader itself.
- **FR-010**: The tool's own brainstorming passes MUST be expressed as passes of
  the same kind, carried with the tool rather than configured.
- **FR-011**: Nothing on a pass MUST mark it as belonging to a repository rather
  than to the tool, so that moving one into configuration later changes where the
  list comes from and not what a pass is.
- **FR-012**: A person MUST be able to declare that a pass does not apply to the
  change under review, supplying a reason in their own words.
- **FR-013**: The system MUST refuse a claim whose reason is empty or is a
  placeholder, and MUST write nothing when it refuses.
- **FR-014**: A claim MUST be written where it forms part of the change
  under review, and the system MUST tell the author and decline to advance when
  it cannot be.
- **FR-015**: Each claim MUST be stored so that claiming a second pass
  inapplicable does not destroy the first, while claiming the same pass
  twice replaces it.
- **FR-016**: A claim about a pass MUST NOT satisfy the check that asks
  whether this change put the architectural boundary question — a pass's claimed
  absence is not an answer to that question.
- **FR-017**: The system MUST treat "the pass ran and produced nothing" and "the
  pass does not apply" as one state, with no third outcome distinguishing them.
- **FR-018**: The default position view MUST hide passes that were settled away,
  and MUST show every other pass including any that is holding the pipeline.
- **FR-019**: The system MUST offer a way to show every row including the ones
  hidden by default, and a shown settled-away row MUST carry the reason that was
  written.
- **FR-020**: The machine-readable position MUST always carry the full tree,
  unaffected by what the human-readable view hides.
- **FR-021**: A pass read from a repository's configuration MUST default to
  requiring review before the pipeline continues past it, and a pass carried with
  the tool MUST default to continuing, because the tool cannot vouch for a
  command it does not ship.
- **FR-021a**: That default MUST be applied as the list is read, so that nothing
  on a pass records which list it came from and FR-011 holds. A repository MUST
  be able to override the default for any one pass, and an overridden pass MUST
  be indistinguishable from a tool-shipped pass with the same setting.
- **FR-021b**: A feature granted autonomy MUST run past a pass that requires
  review without stopping, exactly as it does past the design gates, so that
  autonomy stays one switch rather than one per kind of gate.
- **FR-022**: A check over the repository's own configuration MUST report every
  declaration it cannot honour — a pass whose command is not installed in that
  repository, an unsatisfiable order (FR-003a), a nesting deeper than one level
  (FR-004) — and MUST exit non-zero when it finds one, so that a dead declaration
  fails a run somebody wired up rather than waiting to be walked into. No such
  declaration is dropped silently: one wfctl discards without saying so is
  indistinguishable to its author from one it never read. This is not the drift
  report's work: that reports state wfctl installed and has since been changed,
  and a repository's own configuration is neither.
- **FR-022a**: A pass MUST be able to declare that no command runs it, and the
  check in FR-022 MUST NOT report such a pass, so that a stage a person performs
  by hand is expressible rather than tolerated as a broken declaration.

## Key Entities

- **Pass**: a stage of work belonging inside one pipeline step. Carries a name
  unique among that step's passes, either a command that runs it or a statement
  that a person performs it, an evidence reader that says
  whether it has run, and whether the pipeline may continue past it without
  review. Addressed as `<step>.<name>` wherever the name is typed or written to a
  path. Holds no position of its own and no mark of who declared it.
- **Claimed absence**: one person's statement that one pass does not apply to one
  change, carrying the reason in their words. Lives in the change under review so
  a reviewer can disagree with it; nothing reads it back.

## Success Criteria _(mandatory)_

### Measurable Outcomes

- **SC-001**: A repository can add a stage of its own to the pipeline and have it
  routed to, with zero changes to the tool's source and one edit to one
  configuration file.
- **SC-002**: For a step with several passes, an author reading the position can
  name which pass is outstanding and which command produces it, without opening
  any file.
- **SC-003**: A reviewer can tell, from the change under review alone, whether a
  pass was skipped as a judgment someone made or omitted with nobody noticing —
  a distinction that is invisible today.
- **SC-004**: A feature with any number of settled-away passes shows no more rows
  in the default view than a feature with none, so the ordinary case does not get
  longer as declarations accumulate.
- **SC-005**: A branch that declares two passes inapplicable retains both
  statements; neither is lost.
- **SC-006**: A change that declares a pass inapplicable and never puts the
  architectural boundary question is still held by the check that asks it.

## Assumptions

- Pre-specify design context loaded from `design.md` in this feature's directory.
- The eight built-in step names are taken as they are. Whether they are the right
  names is tracked separately and is not decided here.
- A pass earns a row only if it leaves an artifact somebody can point at. A
  practice that hands its result to another pass and writes nothing itself stays
  what it is — how you do a pass, not a pass.
- Replacing or overriding a built-in step is out of scope, as is any general
  mechanism for review or change-opening stages.
- A repository-declared pass defaults to requiring review, on the grounds that
  the tool cannot vouch for a command it does not ship. A repository that wants
  its pass to run unattended says so in its own configuration.
- Ordering of the tool's own brainstorming passes follows the order the design
  levels are worked in. The behavior level earns no row because its output lands
  as sections inside the design document, which is written last.

## Validation Strategy _(mandatory)_

The project's declared verification, unchanged:

```
uv run --frozen --extra dev pytest -q
uv run --frozen --extra dev ruff check wfctl/ tests/
uv run --frozen --extra dev mypy wfctl/
```

Beyond the suite, these have to be exercised for real, because each is a case the
suite can pass while the behavior is wrong:

- Declare a pass in a scratch repository's configuration and walk a branch
  through it end to end, confirming the position view, the next command, and the
  advance after the artifact appears. A test that constructs the payload directly
  has not tested that a repository can reach it.
- Read the tool's own brainstorming passes on a branch part-way through, and
  confirm each reports separately. The existing assertions read a named step's
  state out of a mapping and will keep passing whether or not the passes appear.
- Declare two passes inapplicable on one branch and confirm both claims survive,
  then confirm the change under review carries both.
- On a branch that has declared a pass inapplicable and drawn no boundary,
  confirm the boundary check still holds the work. This is the one where a wrong
  answer looks like success.
- Confirm the machine-readable position carries rows the default human view hid.
