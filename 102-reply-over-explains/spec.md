# Feature Specification: reply over-explains

**Feature Branch**: `102-reply-over-explains`
**Created**: 2026-08-29
**Status**: Draft
**Input**: Issue #102 — "conversation-response-shape lets a reply over-explain what needs no decision"

## Overview

`conversation-response-shape` governs the **order** of a reply (answer first) and
its **depth** (scale to the question). It governs neither **register** — whether a
piece of material is worth saying at all — nor **composition** — what a reply is
made of.

It also never requires a reply to establish *what it is talking about* before it
argues about it, so a reply can be answer-first, jargon-free and forty words long
and still leave the reader asking "what are we talking about again".

The consequence is a reply that satisfies every stated rule and is still
unreadable: five finished records reported, then two hundred words justifying
decisions that were already made, already verified, and required nothing from the
reader. This feature adds the two missing governors and removes the four passages
that contradict them.

## User Scenarios & Testing _(mandatory)_

### User Story 1 - Finished work is reported as finished (Priority: P1)

A reader asks for a batch of work to be completed. The work completes and is
verified. The reply tells them it is done and stops. Judgment calls made along the
way get one line each, or none — because the reader has nothing to decide about
them.

**Why this priority**: This is the defect #102 names, reproduced under controlled
conditions. It is the one change that, shipped alone, fixes the reported failure.

**Independent Test**: Run the skill against a task whose output is completed,
verified work and measure prose words in the reply (code and tables excluded).
The current skill produces ~203; every variant carrying a register rule produced
91–152.

**Acceptance Scenarios**:

1. **Given** a reply reporting five completed and verified records, **When** the
   skill is in force, **Then** the reply states completion and contains no
   volunteered section justifying a decision the reader did not contest.
2. **Given** a judgment call made during that work that the reader might want to
   know about, **When** the reply mentions it, **Then** it gets one line, not a
   paragraph and not a heading.
3. **Given** a reply draft containing a heading of the form "two things worth
   naming" or equivalent, **When** the register rule is applied, **Then** that
   section is cut — the heading is the tell that material was inflated to justify
   its own presence.
4. **Given** a reader who explicitly asks "why did you choose X", **When** the
   register rule is in force, **Then** the reasoning is still given in full — the
   rule governs volunteered material, not requested material.

---

### User Story 2 - A reply has a shape, and the material picks the form (Priority: P2)

A reader receives replies composed the same way every time: an opening matched to
what the reply is doing, then a drawing for each question they have, each with one
line naming what to look at. The form of each drawing follows from what the
material is — a partition draws as two columns, a fan-out as a fan-out — so the
reader never has to ask for a diagram that should have been there.

**Why this priority**: The composition is what makes the register rule
actionable, and the form-selection step is what stops the table rule from winning
by default. Without selection the skill lists forms that are merely available,
which produced tables in 3 of 5 runs including one where the material had no
shape at all, and a 2x2 table on #99 where the material was a fan-out over a
28-item partition.

**Independent Test**: Run the skill against tasks with structural content and
count warranted against unwarranted drawings, and the share of drawings whose
form matches the material. Baselines: the control variant with all form
instructions removed produced zero tables; the variant with them produced tables
in three of five runs, one unwarranted.

**Acceptance Scenarios**:

1. **Given** material that is a set split in two, **When** the reply is composed,
   **Then** it draws two columns with the counts in the headers — not prose, and
   not a table of some other axis.
2. **Given** material that is one source with several destinations, **When** the
   reply is composed, **Then** it draws a fan-out, without the reader asking for
   a diagram.
3. **Given** a reader with three distinct questions, **When** the reply is
   composed, **Then** it may carry three drawings — one drawing per reply is not a
   limit.
4. **Given** a reply that reports a change, **When** it opens, **Then** it opens
   with what changed, why, and what it affects. **Given** a reply that answers a
   question about current state, **Then** it opens with the claim and the numbers
   in it, and does not manufacture a "what changed".
5. **Given** subject matter with no structure worth drawing, **When** the reply is
   composed, **Then** no drawing is forced — a two-cell table around twenty words
   is a failure of this requirement, not a satisfaction of it.
6. **Given** a drawing in a reply, **When** it is rendered, **Then** one line
   beneath it names what to look at, and says nothing the drawing already says.

---

### User Story 3 - The skill reads correctly in a repo that is not wfctl (Priority: P3)

A downstream project installs the skill bundle. Every example in
`conversation-response-shape` is comprehensible without knowing what wfctl is,
what its pipeline steps are, or what its commands print.

**Why this priority**: The skill installs into every repo that runs
`install-skills`. #80 already records the current `wfctl end` example as a defect
for exactly this reason, and the five pull requests that motivated the reply
template are drawn from two of the author's own repos.

**Independent Test**: Read the skill as a newcomer to a project that is not wfctl
and confirm no example depends on wfctl-specific vocabulary to be understood.

**Acceptance Scenarios**:

1. **Given** the "render the literal output" example, **When** the skill ships,
   **Then** it does not use `wfctl end` or any other wfctl command as its
   illustration.
2. **Given** the reply template, **When** it is written into the skill, **Then**
   the shape is stated in domain-agnostic terms even though it was derived from
   this author's pull requests.

---

### User Story 4 - The pull request template agrees with the skill (Priority: P3)

A contributor writing a pull request body and an agent writing a reply are given
the same instruction about when a drawing is warranted.

**Why this priority**: Two homes for one rule is the condition `knowledge-placement`
names as having no owner. Today they disagree: the skill tests warrant by length,
the template tests it by reading time.

**Independent Test**: Compare the drawing guidance in
`.github/pull_request_template.md` against the corresponding passage in the skill
and confirm they state the same test.

**Acceptance Scenarios**:

1. **Given** the template's line "if a diagram takes longer to read than the prose
   it replaced, delete it", **When** this feature ships, **Then** it is replaced by
   the same test the skill states, not a paraphrase of it.

---

### User Story 5 - The reply establishes what it is talking about (Priority: P1)

A reader asks where something should live, or whether to keep it, or which of two
options wins. Before the reply argues about it, the reply says what it *is* — in
one or two lines, with its literal surface if it has one. The reader never has to
ask "wait, what X are we talking about".

**Why this priority**: Co-equal with User Story 1. This failure survives the
register fix — an observed reply passed answer-first, passed plain-language,
carried no volunteered justification, ran forty words, and the reader's next
message was still a request to identify the subject. Compression removed the
symptom and preserved the cause.

**Independent Test**: Run the skill against a task that decides the placement or
fate of a named-but-unexplained thing, and check whether the reader's next
message is a clarifying question about the subject rather than about the answer.

**Acceptance Scenarios**:

1. **Given** a question about where a thing should live, **When** the reply is
   composed, **Then** it states what the thing is and what it does before it
   states where it should go.
2. **Given** a thing with a literal surface — a config block, a command, a field
   — **When** the reply establishes it, **Then** it renders that surface rather
   than describing it.
3. **Given** a reply compressed for brevity, **When** the establishing lines
   compete with the reasoning for space, **Then** the establishing lines are kept
   and the reasoning is cut — never the reverse.
4. **Given** a reply that already established its subject in an immediately
   preceding turn, **When** the next reply continues the same subject, **Then**
   it need not re-establish it — the obligation is per subject, not per reply.

---

### Edge Cases

- **A question that genuinely asks for depth.** The register rule must not
  compress an explicit request for reasoning. "Terseness is the default, not a
  ceiling" is being deleted as a contradicted passage; the guard against
  over-compression must therefore live in rule 3's precedence, which already
  says depth is opt-in and the reader is the one who opts in.
- **A decision the reader does need to make.** Material that requires a decision
  is not volunteered side-notes and is not covered by the register rule. The
  boundary is whether the reader has something to decide, not whether the topic
  is important.
- **Subject matter with no shape.** Forcing a drawing is a defect. The
  composition says one drawing per question the reader actually has — which is
  sometimes none, and is not capped at one.
- **A correct form answering the wrong question.** The #99 failure was not a bad
  table; it was a correct 2x2 answering a smaller question than the one asked.
  Form selection has to be driven by the material the reader needs, not by the
  first structure that presents itself.
- **A short reply that is still unusable.** Brevity is not evidence of success.
  A forty-word reply that assumes its subject fails harder than a long one that
  establishes it, because the establishing lines are the first thing compression
  removes.
- **Rules lost mid-session.** Out of scope here and recorded as such: the skill's
  rules demonstrably decay within a long session, and every piece of evidence
  behind this spec was gathered in fresh contexts. The honest claim for this
  feature is that these rules work *when loaded*. The durable fix is #85.
- **A form the skill never produces.** Boundary sketches appeared in zero of
  fourteen runs because the form is not in this skill. Adding a trigger for it is
  explicitly excluded — see FR-008.

## Requirements _(mandatory)_

### Functional Requirements

- **FR-001**: The skill MUST state a register rule: material that requires no
  decision from the reader is not expanded into a paragraph; finished and verified
  work is reported as finished; judgment calls made along the way get one line each
  or none.
- **FR-002**: The register rule MUST be positioned so its precedence against the
  existing order and depth rules is unambiguous — it governs volunteered material
  attached to completed work, where rule 1 governs justification of the answer
  itself.
- **FR-003**: The skill MUST resolve all four passages that contradict the register
  rule, by deletion or replacement:
  - "Reach for it when the description is getting long…" (length is not the test)
  - "The artifact does not replace the explanation" (the drawing carries the
    argument; the line beneath it is a caption)
  - "Terseness is the default, not a ceiling…"
  - the pull request template's "if a diagram takes longer to read than the prose
    it replaced, delete it"
- **FR-004**: The skill MUST state what a reply is composed of, with an opening
  matched to what the reply is doing — what changed / why / what it affects when
  reporting a change; the claim with its numbers when answering a question about
  current state — followed by the drawings, each with one line naming what to look
  at in it.
- **FR-004a**: The composition MUST allow one drawing per question the reader has,
  and MUST NOT cap a reply at one drawing.
- **FR-005**: The skill MUST state a checkable test for when to draw: the reader
  has to hold a set, a location, a count, or a branch in order to follow the
  sentence. This is the replacement for the deleted length test in FR-003 and MUST
  be checkable against the material, not against the prose.
- **FR-005a**: The skill MUST state which form the material calls for, covering at
  minimum: a set split in two, one source with several destinations, a value and
  its consequence, a sequence with exits, and rows against columns. Two-column is
  the most frequent form, but *before / after* MUST be one filling of it rather
  than the privileged default.
- **FR-006**: Every example in the skill MUST be comprehensible without knowledge
  of wfctl. This closes #80.
- **FR-007**: `.github/pull_request_template.md` MUST point at the skill for when
  a drawing is warranted and which form to use, rather than restating either. The
  skill is the single owner of the test and the form-selection table; every other
  surface states only the obligation and defers the choice.
- **FR-008**: This feature MUST NOT add a per-form trigger for the decision tree
  or the boundary sketch, and MUST record why so the proposal is not re-raised:
  availability is not the constraint. Three untriggered forms appeared on demand
  on #99, so the forms are reachable already; what is missing is the step that
  picks between them, which FR-005a supplies. A per-form trigger would add a rule
  to a set where one rule already wins every contest. Revisit only if the
  selection step ships and those forms still never appear.
- **FR-009**: This feature MUST NOT introduce a new skill, a new frontmatter key,
  or any CLI change. Scope is the skill file and the pull request template.
- **FR-010**: The skill cross-reference tests MUST continue to pass unchanged.
- **FR-011**: The skill MUST require a reply to establish its subject before
  deciding about it. Where a reply determines placement, retention, or a choice
  between options for a named thing, it MUST first state what that thing is and
  what it does, rendering its literal surface where one exists.
- **FR-011a**: The subject rule MUST sit in the precedence list beside "answer
  first" and "frame in plain language", not in the drawing section — it governs
  content and order, not form. It MUST be stated as distinct from both: a reply
  can satisfy either and still fail this one.
- **FR-011b**: The skill MUST name the observable check — a reader's follow-up
  asking what the reply is about, rather than about its answer, means the
  subject was never established.

- **FR-012**: This feature MUST add automated checks for the invariants it
  introduces, so they are enforced rather than merely documented:
  - the draw test and the form-selection table appear in exactly one file under
    `wfctl/agents/` (FR-005a, FR-007) — the check that survives #556 adding two
    more pointers;
  - no example in the skill contains wfctl-specific vocabulary (FR-006), which is
    what closes #80 verifiably rather than by inspection;
  - the existing rule numbers 1-3 keep their headings, since three in-file
    references resolve by number and no test covers them today.
- **FR-012a**: Checks for general skill well-formedness — frontmatter key sets,
  precedence-list contiguity — MUST NOT be added here. #60 is open for exactly
  that and owns it; adding them here would give that concern two homes.

### Out of Scope

- A per-turn mechanism to stop mid-session rule decay — that is #85.
- Deleting "render the literal output, not a description of it". The control run
  says it earns nothing, but removing a working rule on one run of evidence is the
  worse bet.
- Merging `i-have-adhd` into this skill. It is vendored, upstream owns its
  contents, and copying its rules here would give them two homes.
- Verifying skills are well-formed in general — frontmatter, section anatomy,
  description quality. That is #60, which is open and names the problem.
- Optional install layers so a consumer can decline the default — that is #106,
  and it is not a precondition for the default shipping.
- Adding the *lead with a figure* obligation to `speckit-delivery-plan` and
  `finishing-a-development-branch`. That is #556's change. FR-007 governs the
  shape those additions must take — point at the skill, do not restate the
  selection table — but this feature does not make them.
- Any ASCII-rendering tooling. A reply is text either way; the problem is what to
  draw, not how.

## Key Entities

- **Register**: whether a piece of material is worth saying at all. Distinct from
  order (what comes first) and depth (how far to go). The property the skill was
  missing.
- **Reply composition**: the shape a reply takes — an opening matched to its
  genre, then a drawing per question, each captioned. A template, not a rule; it
  replaces "here are forms available to you" with "this is what a reply looks
  like."
- **Form selection**: the step that maps what the material *is* onto which drawing
  to use. Absent from the skill today, which is why the table rule fires by
  default and answers whatever question a table can answer.
- **Reply genre**: whether a reply reports a change or answers a question about
  current state. The two take different openings; only the first has a "what
  changed".
- **Rule ownership**: exactly one surface states the draw test and the
  form-selection table; every other surface that needs the rule points at it. The
  alternative — the same rule written in four places — is what
  `knowledge-placement` calls the condition with no owner.
- **Subject**: the thing a reply is deciding about — what a phrase like "the
  hook" points at. Distinct from the answer and from the vocabulary the answer is
  written in. A reply that never establishes its subject is unusable regardless of
  how short or how well-ordered it is.
- **Volunteered material**: reasoning attached to work the reader did not ask
  about and cannot act on. The target of the register rule. Its tell is a heading
  that announces its own worth.

## Success Criteria _(mandatory)_

### Measurable Outcomes

- **SC-001**: On issue #88 — the one task with a recorded baseline — a reply
  passes every question in `judgment-test.md`. Prose word count is recorded
  alongside (baseline: 203) and is never the verdict, per SC-012.
- **SC-002**: A reply reporting completed work contains zero volunteered sections
  justifying a decision the reader did not contest.
- **SC-003**: Exactly one surface states the draw test and the form-selection
  table. Every other surface referencing the rule points at that one — zero
  restatements, therefore zero possible contradictions.
- **SC-004**: Zero examples in the skill require knowledge of wfctl to understand.
- **SC-005**: A question that explicitly asks for reasoning, a tradeoff, or a
  correction still receives full reasoning — the register change does not reduce
  depth where the reader opted in.
- **SC-006**: A reader can state what a reply is composed of after reading the
  skill once.
- **SC-007**: A reply about material with no structure contains no drawing — the
  unwarranted two-cell table observed under the current rules does not recur.
- **SC-008**: On material that is a fan-out or a partition, the reply draws it
  without the reader asking. The #99 failure — a reader having to type "i need a
  diagram here" — does not recur on the same class of material.
- **SC-009**: Across the four unscored tasks, each drawing's form is recorded
  against the material's actual shape. **No delta against the 3-of-5 baseline is
  claimed** — that baseline counted whether a table *appeared*, not whether it was
  warranted, so the two numbers are not comparable. Whether form selection beats
  the table habit stays an open question (design.md), not a criterion this feature
  asserts it meets.
- **SC-010**: A reply answering a question about current state contains no
  manufactured "what changed" section.
- **SC-011**: Zero reader follow-ups asking to identify the subject of a reply
  ("what X are we talking about", "which file", "wait, what is X") across the
  benchmark tasks.
- **SC-012**: Prose word count is reported alongside SC-011, never alone. A reply
  that scores well on word count and triggers an SC-011 follow-up counts as a
  failure, not a win.
- **SC-013**: Every invariant this feature introduces has an automated check.
  Zero invariants are documented-but-unenforced.

## Validation Strategy _(mandatory)_

- `uv run pytest -q`, `uv run ruff check wfctl/ tests/`, `uv run mypy wfctl/` — all
  green. This is the project's definition of done and what CI runs.
- `tests/test_skill_cross_references.py` passes — it is the test that covers this
  skill's references (FR-010).
- `wfctl install-skills`, then exercise the changed skill. A change under
  `wfctl/agents/skills/` is not verified by the suite alone; the suite checks that
  skills ship and cross-reference, not that they read well.
- `wfctl doctor` — no finding that still stands.
- Behavioral check for FR-001 and SC-001: run the revised skill against the same
  fixed tasks used in the design experiment and compare prose word counts against
  the recorded baseline (variant A, ~203 words).
- Manual read for FR-006 and SC-004: no example in the file depends on wfctl
  vocabulary.

## Assumptions

- Pre-specify design context loaded from
  `<spec root>/102-reply-over-explains/design.md`, which is complete and approved.
  Where this spec and that document differ in wording, the design document is the
  intent.
- Deleting "Terseness is the default, not a ceiling" does not cause
  over-compression elsewhere. This was settled by experiment — the variant that
  deleted it produced the most informative reply in the set, and the variant that
  kept it over-compressed anyway — but no variant was tested against a question
  that genuinely asked for depth. SC-005 exists to catch this if the assumption is
  wrong.
- The reply composition survives contact with a repo that is not the author's. It
  was derived from five merged pull requests across two of the author's own repos.
  FR-006 and SC-004 are the mitigation.
- Two genres — reporting a change, answering a question — are the right cut.
  Those are the two observed. A third may need its own opening; FR-004 should be
  read as extensible rather than closed.
- A selection step fires where a per-form trigger would not. This is the claim the
  whole of FR-005a rests on, and it is inferred from two cases (#90 and #99), not
  run. SC-009 is the check. It is also still rule text, and rule text is what
  decays — see #85.
- Stating the subject rule makes it fire. It is checkable after the fact, from
  the reader's follow-up, which no other rule in this skill is — but nothing has
  tested whether it fires unprompted.
- These rules work when loaded. Every piece of evidence behind this spec was
  gathered in a fresh context, so none of it measures whether the rules survive a
  long session. #85 owns that problem.
- wfctl's defaults are deliberately this author's approach. "It ships to every
  repo" is not a reason to keep a preference out of the base layer; #106 gives a
  consumer an exit rather than gating what ships.
