# Clarification scan — #325

## Session 2026-09-10

- Verdict: satisfied
- Scanned: spec.md
- Asked: 3 · Answered: 3 · Outstanding: 0 · Deferred: 0
- Detail: `<spec-root>/325-flip-clarify-and-analyze/spec.md` § Clarifications

### Coverage

| Category | Status |
| --- | --- |
| Functional Scope & Behavior | Clear |
| Domain & Data Model | Clear |
| Interaction & UX Flow | Clear |
| Non-Functional Quality Attributes | Clear |
| Integration & External Dependencies | Clear |
| Edge Cases & Failure Handling | Resolved |
| Constraints & Tradeoffs | Resolved |
| Terminology & Consistency | Clear |
| Completion Signals | Resolved |
| Misc / Placeholders | Clear |

### Findings

- **Edge Cases & Failure Handling** — the spec's own acceptance scenario 2 says a
  spec with clarification markers still standing reports `auto: true` after the
  flip, which means an unattended run re-enters `/speckit.clarify` on a spec the
  previous pass failed to resolve. The spec said nothing about whether anything
  bounds that.
  Q: Should anything bound the re-entry? →
  A: Free-form, and it stood on its own rather than taking an offered option: the
  behaviour had never been exercised, so the answer was to test it rather than
  decide it. Tested during this session — with markers standing, both `specify`
  and `clarify` read `in_progress` and the pipeline selects `clarify`,
  deliberately, because routing back to `/speckit.specify` would rewrite
  `spec.md` from the template and destroy the Clarifications section. Re-entry
  rescans the current spec, so a surviving marker becomes a candidate question
  again. It does not guarantee resolution, and `speckit-orchestrate` carries no
  iteration cap, no repeated-step check and no bound of any kind. Recorded as: no
  guard here, and the unbounded case is orchestrate's gap, filed separately.
  Decided against **no guard, because re-entry is the mechanism**: the right
  conclusion, reached without evidence. It was offered as the recommendation and
  the answer declined to take it on those terms — the claim that re-entry cleans
  up was untested, and the session tested it before recording anything.
  Decided against **stopping on a second consecutive pass**: it needs state
  saying that clarify already ran and markers survived, which is a new fact the
  pipeline does not carry. `session-state-is-re-derived` puts that on the wrong
  side — it cannot be derived from artifacts, so it would have to be written and
  read back.
  Decided against **attaching a blocking reason to the marker branch**: it
  reports `auto: false` for exactly the state `clarify` exists to handle, which
  removes the flip's effect for the case it most matters in. It also widens what
  `reason` means — every other reason names something re-entering the step cannot
  fix, and a standing marker is the opposite.

- **Constraints & Tradeoffs** — SC-004 claimed the change touches one production
  file and one test file, while the spec's own Validation Strategy requires both a
  table assertion and per-state assertions of the reported flag. Those have
  different natural homes, so the criterion contradicted the strategy two sections
  below it.
  Q: One test file or two? →
  A: Two. SC-004 relaxed to name the module holding the table's test and the
  module holding the tests of the function that reads it.
  Decided against **one file, everything beside the table test**: it keeps SC-004
  literally true by moving `next_step_content` assertions away from the other
  tests of `next_step_content`. The criterion was the thing that was wrong; a
  file count is not worth relocating tests for.
  Decided against **a new module for the change's tests**: it groups by change
  rather than by subject, so `next_step_content` coverage would sit in three
  places and the next reader would have to find all of them. Test modules here
  are named for what they test, not for the issue that added them.

- **Completion Signals** — FR-008 required the test pinning every step's flag to
  be "updated", without saying whether that means edited in place, supplemented,
  or replaced. The three differ in what a future flip trips over.
  Q: How should that test change? →
  A: Edited in place, docstring extended to name #325 alongside #309, and renamed
  shorter — `test_the_table_pins_every_steps_unattended_flag`, replacing
  `test_no_step_changed_the_flag_that_says_it_may_run_unattended`. The rename was
  not offered as an option and came with the answer; it is referenced nowhere but
  its own definition.
  Decided against **keeping it and adding a second test for the two steps**: it
  leaves two places asserting the same table, which a future flip has to update
  both of — and the failure this test exists to catch is precisely a flip that
  updated one thing and not another.
  Decided against **a parametrized test per step**: eight cases replace one dict,
  and the dict is what lets a reader see the whole table at once. FR-008 now says
  so explicitly rather than leaving it to be re-derived.

### Deferred

None. Every category above was read; the seven marked Clear were read and found
to need no question.
