# Clarification scan — #352

## Session 2026-09-11

- Verdict: unsatisfied
- Scanned: spec.md
- Asked: 3 · Answered: 3 · Outstanding: 0 · Deferred: 2
- Detail: `<spec-root>/352-session-stopped-not-finished/spec.md` § Clarifications
- Mode: auto-approve. The three answers below were chosen by the run, not by a
  human. Each is recorded with the options it beat so a reviewer can take any of
  them back on the pull request, which is where the approval moved to.

### Coverage

| Category | Status |
| --- | --- |
| Functional Scope & Behavior | Resolved |
| Domain & Data Model | Deferred |
| Interaction & UX Flow | Deferred |
| Non-Functional Quality Attributes | Clear |
| Integration & External Dependencies | Clear |
| Edge Cases & Failure Handling | Resolved |
| Constraints & Tradeoffs | Clear |
| Terminology & Consistency | Resolved |
| Completion Signals | Clear |
| Misc / Placeholders | Clear |

### Findings

- **Terminology & Consistency** — the branch handoff settles that the mark is
  `continued` rather than `recycle`, and separately says the event's spelling on
  disk is unsettled. The spec as first written used a third word, *unfinished*,
  throughout. Three words for one thing, and nothing said which of them the
  feature is named after.
  Q: What is the canonical name for a stop that did not finish — *continued*,
  *unfinished*, or *interrupted*? →
  A: **continued**. It names what happens next rather than judging the work. The
  spec was normalized onto it and FR-014 now says no other word names the same
  thing. The answer fixes the vocabulary, not the literal value stored on disk,
  which stays with the deferred architecture gate below.
  Decided against **unfinished**: it states a verdict about the work, and `end`
  deliberately stopped making one — #70 removed `**Status**: complete` from the
  handoff header precisely because nothing observed it. The tool can see that a
  session stopped; it cannot see that the work was incomplete, and a mark named
  for the thing it cannot see would re-import the claim that was removed.
  Decided against **interrupted**: it names a cause that lives outside the
  tool's view. A person who stops deliberately mid-run was not interrupted, and
  the same mark has to serve them — the handoff's own argument for why this is
  not a Claude-specific recycle.

- **Functional Scope & Behavior** — the issue says `wfctl status` "should be
  able to say a run has been interrupted N times", and the spec's User Story 3
  asks only that a branch's history report every stop. Those are different
  scopes and the spec did not say which one it was buying.
  Q: Does this feature also surface the continued stop in the pipeline status
  view, or is the branch history the only place it is reported? →
  A: **Branch history only.** FR-015 now states the status view is unchanged,
  and the contract test asserts its output is byte-identical on a branch
  carrying a continued stop. "Should be able to" is a capability the record
  creates; shipping the view is a separate decision.
  Decided against **the status view reports it, always**: it adds a second
  reader of a record whose shape the architecture gate has not yet chosen, and
  `pipeline-state-is-one-payload` makes any status row an addition to the single
  payload every view transforms — a wider change than the two deliverables the
  issue names, taken before the gate that decides what is being read.
  Decided against **the status view reports it only when the count is above
  zero**: the same cost as reporting always, plus a conditional row — which
  makes a branch with no continued stops indistinguishable from a wfctl too old
  to know about them. That is the confusion `start`'s own "one line per resolved
  state, never silence" rule exists to prevent, and this repo already lives with
  it between its two installed copies.

- **Edge Cases & Failure Handling** — FR-006 makes the next session ask whenever
  it cannot quote a first action, whatever the mark says. So a continued stop
  recorded over a handoff that names none produces exactly the stall the feature
  exists to remove, and the spec said nothing about whether anyone is told.
  Q: When a stop is recorded as continued but the handoff beside it names no
  usable first action, is anything said at the moment of the stop? →
  A: **Yes — the stop reports it**, and still records the stop. FR-013 and User
  Story 2's fifth acceptance scenario carry it. The stop is the last moment the
  operator is present, and the thing that would otherwise fail silently is the
  feature's whole purpose.
  Decided against **saying nothing**: it defers the only signal to a session
  that may run unattended hours later, where by construction nobody reads it.
  Decided against **refusing the stop until the handoff names a first action**:
  it blocks the automated case at the one moment it cannot answer, turning a
  stop that would have degraded to "the next session asks" into one that does
  not happen at all. `end` refuses on session state today and never on the
  content of the handoff, and this would be the first.

### Deferred

- **Domain & Data Model** — how the record distinguishes a continued stop from a
  finished one: a separate kind of stop, or a field on the existing kind. Both
  satisfy every requirement in the spec, and the choice changes what every
  existing reader of the record must interpret. The branch handoff routes it to
  a level-2 gate explicitly and says to run the gate rather than pick in the
  spec. Deciding it here would settle it in a document whose readers cannot see
  the argument.
- **Interaction & UX Flow** — the surface an operator uses to declare it: a flag
  on the existing end command, or a command of its own. Invisible to every
  acceptance scenario in the spec, and it follows the record's shape rather than
  leading it.

The verdict is `unsatisfied` because the first of those is high-impact and open.
That is the designed path rather than a gap — but a scan that called it
`satisfied` would tell a reviewer nothing is owed before `/speckit.plan`, and a
level-2 gate is.
