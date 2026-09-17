# Feature Specification: record leads with drawing

**Feature Branch**: `109-record-leads-with-drawing`
**Created**: 2026-09-16
**Status**: Draft
**Input**: Issue #109 — "Human views are visual-first — the record leads with a drawing", a sub-issue of the #86 Architecture Knowledge Lifecycle epic.

## Clarifications

### Session 2026-09-16

- Q: What is the drawing's section called? → A: `## Boundary`, unchanged.
- Q: What counts as a drawing? → A: any non-empty fenced block under
  `## Boundary`; its content is never classified.
- Q: Where does the label-disagreement report surface? → A: with the existing
  record findings, which `doctor` prints.
- Q: Does this bind records in repositories that install wfctl? → A: yes, by the
  same rule — it turns on a record's status, not on which repository holds it.

## User Scenarios & Testing _(mandatory)_

### User Story 1 - A record cannot be accepted without its drawing (Priority: P1)

Someone has written an architecture decision and is ready to make it binding.
Today they run the accept command and it succeeds whether or not the record
shows anything. After this change, a record that carries no drawing is refused,
and the refusal says what is missing and what to add.

**Why this priority**: This is the whole of what the issue asks for that a
machine can hold. Everything else in the feature is either a way of making this
refusal possible or a way of making it more useful. Shipped alone, it changes
the corpus permanently: from here on, a binding decision shows its shape.

**Independent Test**: Take any proposed record with no drawing, run the accept
command, read the refusal, add a drawing, run it again, watch it succeed. No
other part of the feature has to exist.

**Acceptance Scenarios**:

1. **Given** a proposed record with no drawing section, **When** someone accepts
   it, **Then** the command refuses, names the record, says a drawing is
   required, and changes nothing on disk.
2. **Given** a proposed record carrying a drawing and a declared kind, **When**
   someone accepts it, **Then** the record becomes accepted exactly as it does
   today.
3. **Given** a record already accepted before this feature shipped, carrying no
   drawing, **When** anything reads or projects it, **Then** nothing reports it
   as incomplete and its file is not modified.
4. **Given** a listing of records that could be accepted, **When** it is
   produced, **Then** a record that would be refused for a missing drawing does
   not appear in it.

---

### User Story 2 - The record says which kind of drawing it carries (Priority: P2)

A decision about who owns a value wants a different picture from a decision
about a thing moving through states. The author knows which; nothing in the
record says so. After this change, the record declares it, in one place, in a
form both a reader and a check can find.

**Why this priority**: Without it the refusal in Story 1 can only ask for "a
drawing" and cannot say what kind, and the traceability in Story 3 has no name
for what a drawing is of. It is second rather than first because a required
drawing with no declared kind is already most of the value.

**Independent Test**: Write a record declaring each of the three kinds in turn,
and confirm each is read back and reported correctly. Testable without the
accept gate existing.

**Acceptance Scenarios**:

1. **Given** a record declaring one of the three kinds, **When** it is read,
   **Then** the declared kind is available to every reader of that record.
2. **Given** a record declaring no kind, **When** it is read, **Then** the kind
   reads as undeclared, never as a default.
3. **Given** a record declaring a word that is not one of the three kinds,
   **When** it is read, **Then** that is reported as a finding rather than
   silently accepted.
4. **Given** a record carrying a drawing but declaring no kind, **When** someone
   accepts it, **Then** the command refuses and names the three permitted kinds.
5. **Given** an author who has not written a record before, **When** they read
   the guidance the project ships, **Then** they can name which kind their
   decision needs without asking anyone.

---

### User Story 3 - A drawing that says something the prose does not is surfaced (Priority: P3)

The drawing and the words are two views of one decision. When they drift, a
reader gets two architectures and no signal. After this change, a label that
appears in the drawing and nowhere else in the record is reported.

**Why this priority**: It is the issue's traceability item, scoped to what is
checkable inside the record. It ships last because it is the part most likely to
be noisy, and because the first two stories are worth having whether or not this
one survives contact with the corpus.

**Independent Test**: Run the check over the records that already carry
drawings, and read every finding it produces. The test of this story is whether
a reader agrees with the findings, which is why it is a warning rather than a
refusal.

**Acceptance Scenarios**:

1. **Given** a record whose drawing uses only labels its prose also uses,
   **When** the check runs, **Then** it reports nothing.
2. **Given** a record whose drawing carries a label appearing nowhere else,
   **When** the check runs, **Then** it reports that label and names the record.
3. **Given** a record that would be reported by this check, **When** someone
   accepts it, **Then** the report is shown and the acceptance still succeeds.

### Edge Cases

- A record whose decision genuinely has no shape to draw: the author still
  declares a kind and draws the smallest true picture, or the record is a
  candidate for not being a record at all. There is no exemption, because an
  exemption is indistinguishable from an omission.
- A drawing that fails to render where the reviewer reads it: nothing in this
  feature can detect that, and the specification says so rather than implying
  coverage it does not have.
- A record accepted before this feature existed that someone later supersedes:
  the superseding record is new, so it carries a drawing; the superseded one is
  never edited beyond its status and log.
- A label that is a common English word appearing in the prose by coincidence:
  the check passes, and this is a known limit rather than a defect. Agreement of
  spelling is what is being checked.
- Two records drawing the same concept under different labels: out of range.
  Nothing here compares one record against another.
- A repository that installed the skills before this shipped and has proposed
  records with no drawing: those records are refused at acceptance, exactly as
  this repository's own are. Nothing distinguishes them, and nothing needs to.

## Key Entities

- **Record**: one architecture decision as a file. Gains a declared diagram kind
  and a required drawing. Already carries a status, an optional pointer to the
  record it replaces, and its full text.
- **Diagram kind**: one of three named shapes — a flow of data between sides, a
  component boundary, or a lifecycle of states. Chosen by the author from what
  the decision is about.
- **Drawing**: the picture a record leads with, in the form that renders where
  the record is read. It lives under the record's `## Boundary` heading, which is
  the canonical name for the section throughout — "sketch" and "diagram" name the
  same thing in other documents and are not used here. Any non-empty fenced block
  under that heading is a drawing; nothing inspects what is inside it.
- **Acceptance**: the transition that makes a record binding. The only point at
  which this feature's requirements are enforced.

## Requirements _(mandatory)_

### Functional Requirements

- **FR-001**: A record MUST be able to declare which of three diagram kinds it
  carries, in a single place readable without parsing its prose.
- **FR-002**: The system MUST treat an undeclared kind as undeclared, and MUST
  NOT substitute a default.
- **FR-003**: The system MUST reject a declared kind that is not one of the
  three permitted values, and MUST report it rather than ignoring it.
- **FR-004**: The system MUST refuse to accept a record that carries no drawing,
  and the refusal MUST name the record and say what to add.
- **FR-005**: The system MUST refuse to accept a record that carries a drawing
  but declares no kind.
- **FR-006**: The system MUST NOT check, modify, or report on a record that is
  already accepted.
- **FR-007**: A listing of records eligible for acceptance MUST exclude any
  record that acceptance would refuse, so that no listed record fails its own
  suggested command.
- **FR-008**: The system MUST report, without refusing, a drawing label **none
  of whose content words** appears in any other section of the same record. The
  report MUST appear alongside the record findings the project already produces,
  not among the refusals, so that a warning stays a warning.
  The unit is the content word and not the whole label because the whole-label
  rule was measured and reports every label in the corpus; research `R-004`
  carries the three mechanisms and their counts.
- **FR-009**: The record template the project ships MUST carry the drawing as a
  required section rather than an optional one, under its existing heading. The
  heading MUST NOT be renamed: two records already accepted carry drawings under
  it, and their bodies can no longer be edited.
- **FR-010**: The set of permitted diagram kinds MUST be held against the
  shipped template by a check that fails when the two diverge.
- **FR-011**: The projection read by agents MUST be unchanged by this feature —
  no drawing, in any form, reaches it.
- **FR-012**: The guidance the author reads MUST say which kind suits which sort
  of decision, so that the declaration in FR-001 is a choice rather than a guess.
- **FR-013**: The requirements above MUST hold in any repository that installs
  the project's skills, by the same rule and with no per-repository opt-in. What
  decides whether a record is checked is its status, never which repository holds
  it.

## Success Criteria _(mandatory)_

### Measurable Outcomes

- **SC-001**: Every record accepted after this ships carries a drawing. Counted
  over the corpus, the number of exceptions is zero.
- **SC-002**: The five records accepted before this ships are byte-identical
  afterwards.
- **SC-003**: A reader can name the kind of drawing a record carries without
  reading any of its prose, for every record accepted after this ships.
- **SC-004**: Run over every record carrying a `## Boundary` block — four at the
  time of writing, not the 22 that carry a fenced block somewhere — the label
  report produces no more than two findings that a reader judges wrong. More
  than that means the check is miscalibrated and does not ship. The 22 draw under
  `## Context` and `## Decision`, which are not drawings under the Drawing entity
  above; research `R-006` measured the split.
- **SC-005**: The refusal a person meets when a drawing is missing tells them
  what to do without their opening the skill: a reader shown only the refusal
  can produce a conforming record.
- **SC-006**: No existing behaviour changes for anyone who is not accepting a
  record. Every other command produces the same output it did before.

## Validation Strategy _(mandatory)_

The project's definition of done, unchanged:

```bash
uv run pytest -q
uv run ruff check wfctl/ tests/
uv run mypy wfctl/
uv run wfctl doctor
```

Specific to this feature:

- A test that the permitted diagram kinds match the shipped record template,
  following the pattern already used for the spec and plan section lists.
- Tests for each acceptance scenario above, including the refusals — the
  refusals are the feature, so a test suite that only covers the success path
  has not tested it.
- A test that an accepted record is never read by the new checks, written
  against a record with no drawing so it fails if the scope ever widens.
- A run of the label report over this repository's own records, with every
  finding read by a person. This is a judgment, not an assertion, and SC-004 is
  the threshold it is judged against.
- Because this changes files under the skills tree, the suite passing is not
  sufficient: the skills must be installed and a record written through the
  updated template, end to end.
- Rendering where the reviewer reads it is checked by opening a record on the
  hosting site by hand. No automated check covers it and none is proposed.

## Assumptions

- Pre-specify design context loaded from `design.md` in this feature's spec
  directory. The three decisions it records — who declares the kind, when the
  requirement binds, and how traceability is checked — are treated as settled
  here and are not re-argued.
- Three kinds are enough. Taken from the issue's own wording. `design.md`
  proposed validating it against the 22 existing drawings; research `R-006` is
  why that test cannot run — those drawings are not under `## Boundary`, and the
  four that are classify cleanly at a sample size that is evidence of nothing. The
  assumption stays open. If two of the three turn out to be indistinguishable in
  practice, that is a change to FR-001's cardinality and not to anything else
  here.
- The label report belongs with the existing record findings rather than with the
  refusals. `design.md` left this open and the clarification session above closed
  it: the findings path already carries a warning level that does not hold the
  exit code, and already points a reader at the records directory. This is no
  longer an assumption.
- Records are authored by agents as often as by people, and frequently with
  nobody watching. Every requirement above is written to hold in that case,
  which is why none of them relies on a checklist being read.
- The proposed records that carry no drawing — eleven when this was written,
  twenty-four now, because the corpus grew — are held deliberately and are not
  part of this feature's scope. They gain drawings when someone accepts them.

## Dependencies

- The acceptance transition must exist and be the point at which a record
  becomes binding. It does.
- The record template shipped by the project is the one authors copy. Changing
  it reaches authors only after the skills are installed, which is a step this
  feature's validation depends on rather than assumes.
