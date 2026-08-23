# Feature Specification: Judgment rules section for conversation-response-shape

**Feature Branch**: `73-judgment-rules-section`
**Created**: 2026-08-23
**Status**: Draft
**Input**: User description: GitHub issue #73 body ("conversation-response-shape has
no home for rules the output cannot verify"), used as the feature description in
place of typed text — see Assumptions.

## User Scenarios & Testing _(mandatory)_

### User Story 1 - Judgment rules get a documented home (Priority: P1)

As an agent following `conversation-response-shape`, when constructing a response,
the three judgment rules — enumerate real states, the drawing leads, sections repeat
one shape — are documented in a section explicitly separate from the checkable "Show,
to simplify the description" rules, so applying one isn't confused with a rule that
can be verified by inspecting the rendered output.

**Why this priority**: This is the issue's core ask. Without a section, these three
rules have no home and don't get applied consistently.

**Independent Test**: Read the skill file. Confirm a section exists whose rules are
explicitly framed as requiring re-derivation (not inspection), and that "enumerate
real states" and "sections repeat one shape" appear there.

**Acceptance Scenarios**:

1. **Given** the skill file, **When** a reader looks for "enumerate real states,"
   **Then** they find it filed under a section that states compliance requires
   judgment, not inspection.
2. **Given** an enumeration where two rows produce identical output, **When** an
   agent evaluates it against "enumerate real states," **Then** it collapses to one
   state or reduces to a column instead of two rows.
3. **Given** two named sections in the skill, **When** a reader compares their
   structure, **Then** each holds the same slots in the same order.

---

### User Story 2 - Structured subjects get a leading drawing (Priority: P2)

As an agent describing something with real structure (a pipeline, a control plane, a
routing decision, a layered architecture), the response opens with the drawing and
the prose covers only what the drawing can't say, rather than building toward a
diagram after paragraphs of setup.

**Why this priority**: Named directly in the issue as one of the three rules, and it
changes response order today — rule 3's existing architecture guidance still favors
tables over a leading diagram for structured content.

**Independent Test**: Read the rewritten rule text and rule 3's amended
architecture row; confirm the wording requires a leading diagram before prose for
structured subjects. (Validated by text review, not a live agent prompt — see
Validation Strategy.)

**Acceptance Scenarios**:

1. **Given** a request to explain a pipeline, **When** the agent responds, **Then**
   the drawing renders before the explanatory prose.
2. **Given** a request about something with no real structure, **When** the agent
   responds, **Then** no drawing is forced.

---

### User Story 3 - The section title stops undercutting the rules (Priority: P3)

As a reader of "Show, to simplify the description," the title reflects that the
drawing *is* the description and prose annotates it — not that the drawing is a
follow-on illustration to prose that comes first.

**Why this priority**: Editorial fix with lower blast radius than the two above, but
required for User Story 2 to actually land — the current title is part of why rule
3's architecture row still reads "tables over prose."

**Independent Test**: Read the title. It should not describe the drawing as
something that "simplifies" prose written first.

**Acceptance Scenarios**:

1. **Given** the retitled section, **When** a reader skims the skill's section
   names, **Then** the title communicates "drawing first," not "drawing
   illustrates."

---

### Edge Cases

- What happens when a subject is only partly structured (some steps sequential, some
  flat facts)? The judgment call is whether the structured part dominates; no forced
  drawing for incidental structure.
- Do these judgment rules apply to other response-shaping skills (e.g.,
  `i-have-adhd`)? Out of scope — this issue only touches
  `conversation-response-shape` (see Assumptions).

## Clarifications

### Session 2026-08-23

- Q: Ship in the shared base skill bundle, or personal config only? → A: Ship in
  base bundle — same footing as the #72 checkable rules.
- Q: Where does the judgment-rules section live? → A: Inside
  `conversation-response-shape`, alongside the checkable rules from #72.
- Q: Does "the drawing leads" sit with the checkable set or the judgment set? → A:
  Judgment set — the unchecked half (was a drawing warranted) dominates.
- Q: Does FR-007's domain-agnostic requirement cover the wfctl-specific example
  already shipped in the #72 checkable section (`wfctl end` / `implement 3/8`), or
  only new examples in the judgment section? → A: New examples only. Fixing the
  existing example is out of scope for #73 — flag as a follow-up.
- Q: Is validation a doc-only diff against the FRs, or does it require a live
  behavioral test (prompting the agent and observing drawing-first output)? → A:
  Doc-only diff — this is a skill-text edit, not a runtime feature; matches how #72
  shipped.

## Requirements _(mandatory)_

### Functional Requirements

- **FR-001**: The skill MUST document a section distinct from the checkable "Show,
  to simplify the description" rules, containing rules whose compliance requires
  re-deriving the judgment behind them rather than inspecting the rendered output.
- **FR-002**: The judgment section MUST include "enumerate real states": a property
  that varies across every row is a column, not a row; two states that produce
  identical output collapse to one state.
- **FR-003**: The judgment section MUST include "sections repeat one shape": within
  a set of named sections, each section holds the same slots in the same order.
- **FR-004**: The skill MUST place "the drawing leads" rule in the judgment section
  (resolved — see Clarifications).
- **FR-005**: Rule 3's architecture row ("Structured and complete; tables over
  prose") MUST be amended to require a leading diagram followed by named sections,
  with tables reserved for genuinely tabular content.
- **FR-006**: The "Show, to simplify the description" section title MUST be
  replaced with one that states the drawing is the description, not an illustration
  following prose.
- **FR-007**: Every new example written for the judgment-rules section MUST be
  domain-agnostic (not a wfctl-specific CLI string), since the skill installs into
  every downstream repo via `wfctl install-skills`. The existing wfctl-specific
  example already shipped in the #72 checkable section (`wfctl end` /
  `implement 3/8`) is out of scope for this issue — flag as a follow-up, don't fold
  into this diff.
- **FR-008**: The judgment section MUST live inside `conversation-response-shape`
  (resolved — see Clarifications), not a new skill.
- **FR-009**: This change MUST ship in the shared base skill bundle, not only in a
  personal config (resolved — see Clarifications).

## Key Entities

- **Checkable rule**: a rule whose compliance is decidable by inspecting the
  produced output (e.g., is there a table).
- **Judgment rule**: a rule whose compliance requires re-deriving the thing it
  governs (e.g., was this the right cut).
- **Named section**: a titled group of rules within a skill file that readers
  navigate by name; every section in a set repeats the same slot order.

## Success Criteria _(mandatory)_

### Measurable Outcomes

- **SC-001**: A reader unfamiliar with issue #73 can, from the skill file alone,
  correctly sort a new candidate rule into "checkable" or "judgment" without
  consulting the issue.
- **SC-002**: Zero wfctl-specific (implementation-tool) strings appear as examples
  in the new judgment-rules section. (The pre-existing wfctl example in the #72
  checkable section is a separate follow-up, not part of this feature's scope.)
- **SC-003**: Rule 3's architecture row no longer recommends tables ahead of a
  leading diagram for structured content.

## Validation Strategy _(mandatory)_

- Doc-only change — validation is a read-through diff of the rewritten section
  against every Functional Requirement above. No live agent prompt/behavioral test
  is required.
- `grep` the new judgment-rules section (not the pre-existing #72 checkable
  section) for CLI-looking strings to confirm FR-007.
- Confirm the checklist at `checklists/requirements.md` passes before `/speckit.plan`.

## Assumptions

- No `specs/73-judgment-rules-section/design.md` brainstorming artifact exists; the
  user chose to proceed using GitHub issue #73's body directly as the feature
  description rather than running `/speckit.brainstorm` first.
- The issue's drafted rule text (for "enumerate real states," "the drawing leads,"
  and "sections repeat one shape") is treated as settled content, not open for
  rewording in this spec — the issue states explicitly that wording is already
  drafted and only placement/scope questions remain open.
- The retitled section name for "Show, to simplify the description" is left to
  `/speckit.plan` or implementation to choose concrete wording; this spec only
  requires the new title to satisfy FR-006's framing.
- The existing wfctl-specific example in the #72 checkable section (`wfctl end` /
  `implement 3/8`) stays as-is; fixing it is a follow-up outside this issue's
  scope, not tracked further here.
