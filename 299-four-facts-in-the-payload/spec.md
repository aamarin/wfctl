# Feature Specification: four facts in the payload

**Feature Branch**: `299-four-facts-in-the-payload`
**Created**: 2026-09-10
**Status**: Draft
**Input**: Issue #299 — the pipeline collapses four independent facts into one
step state, so a blocked branch cannot say which question is unanswered. Child of
epic #100, scope item 4, and its last open child.

## User Scenarios & Testing _(mandatory)_

### User Story 1 - A reader can tell which question is unanswered (Priority: P1)

A developer returns to a branch whose tasks are all ticked and whose definition
of done is green. They run `wfctl status` and want to know whether anything still
stands between this branch and a merge. Today the answer is a row of glyphs that
says the pipeline is finished, and two of the four questions that decide
readiness are not in the output at all — so the reader supplies the answer from
memory, or misses it.

**Why this priority**: This is the reported defect. Everything else in the
feature exists to make this state distinguishable.

**Independent Test**: Build two branches that are identical except that one's
architecture record is `proposed` and the other's is `accepted`. Run `wfctl
status` on each and compare the console output. Delivers the whole value of the
issue on its own.

**Acceptance Scenarios**:

1. **Given** a branch whose tasks are closed, whose definition of done passed,
   and whose architecture record on this branch is `proposed`, **When** the
   reader runs `wfctl status`, **Then** the output names *architecture accepted*
   as unmet and names the record that is waiting.
2. **Given** the same branch after a human has run `wfctl arch accept` on that
   record, **When** the reader runs `wfctl status`, **Then** the output shows
   *architecture accepted* as met, and differs from the output in scenario 1.
3. **Given** a branch to which nobody has granted outward-facing authority,
   **When** the reader runs `wfctl status`, **Then** the output names
   *outward actions authorized* as unmet.

---

### User Story 2 - A consumer can ask each question precisely (Priority: P2)

An agent or a script reads `wfctl status --json` to decide what to do next. It
needs to branch on which fact is unmet, not parse a sentence out of a step's
annotation.

**Why this priority**: The console answers the human; a machine consumer needs
the same four answers in a form it can key on. Without it, the only machine-
readable route is string matching on prose, which is what the payload exists to
avoid.

**Independent Test**: Run `wfctl status --json` on a branch with one unmet fact
and confirm a `facts` list is present with one entry per fact, each carrying its
own value.

**Acceptance Scenarios**:

1. **Given** any branch, **When** `wfctl status --json` runs, **Then** the
   payload carries a `facts` list of exactly four entries, in a fixed order,
   whatever the state of the branch.
2. **Given** a repository that declares no definition of done, **When** the
   payload is read, **Then** *definition of done verified* reports that the
   question does not arise, and is distinguishable from a definition of done
   that ran and passed.

---

### User Story 3 - A question that does not arise is not reported as a blocker (Priority: P3)

A developer works on a branch that touches no architecture and on a repository
that declares no definition of done. They should not be told to satisfy things
that do not exist on their branch.

**Why this priority**: Without it the feature manufactures two permanent
blockers for every branch that has nothing to accept, which is worse than the
silence it replaces.

**Independent Test**: Run `wfctl status` on a branch that wrote no architecture
record and confirm *architecture accepted* reports that there is no record on
this branch rather than reporting it unmet.

**Acceptance Scenarios**:

1. **Given** a branch that added or modified no file under the architecture root,
   **When** the reader runs `wfctl status`, **Then** *architecture accepted*
   reports that there is no record on this branch, distinct from both met and
   unmet.
2. **Given** the trunk branch, **When** the reader runs `wfctl status`, **Then**
   *outward actions authorized* reports that this is the trunk rather than reporting
   an ungranted authority.

### Edge Cases

- **No feature directory resolves for the branch.** *Artifacts written* reports
  unmet and names the missing spec dir; the other three facts still report, since
  none of them reads the spec dir.
- **Git cannot say whether this is the trunk.** *Integration authorized* reports
  unmet with a detail naming the unavailable evidence. A human grant is promised
  evidence and the accepted rule for promised evidence that is unavailable is to
  block; no new rule is written to reach this.
- **The branch modified an architecture record without adding one.** The record
  counts: the fact reads that branch's record set, and a modified record is on it.
- **More than one record on the branch, mixed statuses.** The fact is met only
  when every record the branch touched is accepted; the detail names the ones
  that are not.
- **A record the branch touched lives under the level-3 `design/` subtree.**
  Level-3 records are never binding, so they are excluded from the fact, the same
  way the existing design gate excludes them.
- **A repository whose definition of done is malformed.** Reported unmet, with
  the existing malformed-config reason, not as a question that does not arise.

## Requirements _(mandatory)_

### Functional Requirements

- **FR-001**: The pipeline payload MUST carry four facts about the branch,
  alongside the per-step list and never inside it: *artifacts written*,
  *definition of done verified*, *architecture accepted*, *outward actions
  authorized*.
- **FR-002**: Each fact MUST be derived from its own owner — the spec dir, the
  repository's declared definition of done and its verification record, the
  status field of the architecture records this branch touched, and the recorded
  human grant respectively.
- **FR-003**: No fact may be derived from another fact, from any step's state, or
  from the current step.
- **FR-004**: Each fact MUST carry one of three values, written `met`, `unmet`
  and `n/a` — the third meaning the question does not arise on this branch. No
  fourth value, and no fact may be omitted from the payload in any state.
- **FR-005**: Each fact MUST carry a detail phrase naming why it holds the value
  it holds, sufficient for a reader to act without consulting another command.
- **FR-006**: `wfctl status` MUST render all four facts in its console output, in
  every state including the state where all four are met.
- **FR-007**: `wfctl status --json` MUST carry the same four facts, in the same
  fixed order, as structured data rather than prose.
- **FR-008**: The pipeline MUST NOT gain a new step state, and no existing step
  state's meaning may change. A step state goes on answering only whether the
  pipeline may advance past that step.
- **FR-009**: *Architecture accepted* MUST read only the records this branch
  added or modified, never the repository's whole projection, and MUST exclude
  the level-3 `design/` subtree.
- **FR-010**: *Architecture accepted* MUST report *does not arise* when the
  branch touched no record, and MUST NOT report it as unmet.
- **FR-011**: *Definition of done verified* MUST report *does not arise* when the
  repository declares no definition of done, distinguishably from a verification
  that ran and passed.
- **FR-012**: *Outward actions authorized* MUST read the recorded human grant
  and MUST report *does not arise* on the trunk, where nothing outside the repo
  is waiting.
- **FR-012a**: No fact may report authority to merge, close or delete. Those are
  covered by no grant and never will be, so a fact answering from the notify
  grant would claim authority no human gave — a wrong answer where the payload
  previously had none. The fourth fact is named for what its grant covers.
- **FR-013**: A fact whose evidence cannot be read MUST report unmet with a
  detail naming the unavailable evidence, and MUST reach that outcome through the
  existing rule for promised evidence rather than a rule written for this
  feature.
- **FR-014**: The rule that decides what unavailable evidence means MUST be left
  unchanged. This feature answers which question the evidence was about, not
  whether the evidence was there.
- **FR-015**: Neither view may compose a fact. Both render what inference already
  decided, per the accepted record that inference produces one payload.

## Key Entities

- **Fact**: One of the four questions that decide whether a branch is ready. Has
  a fixed name, a value of `met` / `unmet` / `n/a`, and a detail phrase. Belongs
  to the branch, not to a step. The four names are `artifacts written`,
  `definition of done`, `architecture accepted` and `outward actions authorized` —
  the wire spelling a consumer keys on, which is shorter than the question each
  one asks.
- **Fact owner**: The source a fact is read from — the spec dir, the verification
  record, an architecture record's status field, or the recorded grant. Each fact
  has exactly one.
- **Pipeline report**: The single inference every view renders. Gains the fact
  list; its step list is unchanged.

## Success Criteria _(mandatory)_

### Measurable Outcomes

- **SC-001**: A reader running `wfctl status` on a branch with one unmet fact can
  name which of the four it is, from that output alone, without running a second
  command.
- **SC-002**: Two branches identical except for one architecture record's status
  produce different `wfctl status` console output.
- **SC-003**: All four facts appear in `wfctl status --json` on every branch,
  including a branch with no feature directory and including the trunk.
- **SC-004**: The number of pipeline step states is unchanged at four, and every
  existing step's state for every existing input is unchanged — demonstrated by
  the pinned payload snapshot needing no edit.
- **SC-005**: A branch that touched no architecture and a repository that
  declares no definition of done report zero unmet facts on those two questions.

## Validation Strategy _(mandatory)_

- The repository's declared definition of done: `uv run pytest -q`, `uv run ruff
  check wfctl/ tests/`, `uv run mypy wfctl/`, then `uv run wfctl doctor`.
- Console assertions pin `NO_COLOR`, as the suite requires everywhere output is
  asserted on.
- A test that builds both situations in User Story 1 — a passing branch with a
  `proposed` record, and the same branch after acceptance — and asserts the
  console output differs. A test asserting only on `--json` does not satisfy this.
- A test per does-not-arise case: no record on the branch, no declared definition
  of done, the trunk.
- The pinned pipeline payload snapshot must require no regeneration. It covers
  the per-step payload, and these facts are not per-step; a diff against it would
  mean a step verdict moved, which this feature does not do.

## Assumptions

- Pre-specify design context loaded from `specs/299-four-facts-in-the-payload/design.md`.
- The two decisions this rests on have shipped and are consumed, not re-decided:
  who accepts a record (#321) and who grants outward-facing authority (#280).
- The issue's `Dependencies` section, which names #86 as a blocker, is stale. The
  `blocked` label was removed and a comment on the issue records why.
- Four extra console lines do not make `wfctl status` too long to scan. Recorded
  as an assumption in the design record rather than as a measured fact.

## Clarifications

### Session 2026-09-10

Run under `auto_approve: true`. Each question was answered from the codebase and
the tracker rather than by a person, and each answer carries the basis it was
decided on. The options each question offered, and why the answer beat them, are
in `docs/architecture/scans/299-clarify.md`.

- **Q: What three values does a fact carry, in the payload a consumer reads?**
  A: `met`, `unmet`, `n/a`.
  Basis: FR-014 forbids touching the rule that decides what unavailable evidence
  means, and that rule's vocabulary — `satisfied` / `unsatisfied` /
  `inconclusive` — already means something else. `inconclusive` means the
  evidence could not be read; `n/a` means the question was never asked. Reusing
  one set of words for both would make the existing rule look applicable to a
  question it does not answer. A boolean with a nullable reason was rejected for
  the reason `notify` is present-and-false rather than absent (FR-004 of #280's
  spec): a consumer reading a missing or false value cannot tell a real answer
  from a wfctl too old to have one.

- **Q: Where in `wfctl status` does the block render, and in which states?**
  A: Between the step table and the `next:` line, in every state, including when
  all four facts are met and including when no feature directory resolves.
  Basis: rendering only when something is unmet makes the block's *absence*
  carry meaning, and an absent block cannot be told from a wfctl that does not
  know the question — the same distinction the previous answer turns on. `next:`
  and its remedy stay last because they are the action; a reader who has reached
  the next command has stopped reading.

- **Q: Are the four facts the same thing as the seven "rungs" `_predicates.py`
  documents?**
  A: No. They are separate vocabularies and the rung commentary is left as it
  is, with one cross-reference added where it names rungs 6 and 7.
  Basis: the rungs grade *what one predicate proves about its step* — rungs 1
  through 5 are all evidence about whether that step's artifacts were written and
  how strongly, which is a single fact here. Only rungs 6 ("a decision has
  authority") and 7 ("integration was approved") line up one-to-one, with facts 3
  and 4. A stated mapping would hold for two rows out of seven and mislead on the
  other five.

**Deferred to the plan**: whether resolving the architecture root and asking git
for this branch's records on every `wfctl status` is fast enough to leave
unconditional. It is recorded as an assumption in
`docs/architecture/design/299-facts-render-as-a-block.md` and needs a measurement,
which belongs to implementation rather than to the spec.
