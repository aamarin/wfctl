# Clarify scans — #364

## Session 2026-09-13

- Verdict: satisfied
- Scanned: spec.md
- Asked: 4 · Answered: 4 · Outstanding: 0 · Deferred: 0
- Detail: /Users/andremarin/Development/wfctl-specs/364-two-permission-systems/spec.md § Clarifications

Nobody was present to answer: the run was asked for unattended. Every question
below took the recommendation the step computed, together with the reasoning that
produced it. No question reached a pause the repository could not settle, which is
why there is no `### Outstanding` block.

### Coverage

| Category | Status |
| --- | --- |
| Functional Scope & Behavior | Resolved |
| Domain & Data Model | Resolved |
| Interaction & UX Flow | Clear |
| Non-Functional Quality Attributes | Resolved |
| Integration & External Dependencies | Clear |
| Edge Cases & Failure Handling | Resolved |
| Constraints & Tradeoffs | Clear |
| Terminology & Consistency | Clear |
| Completion Signals | Clear |
| Misc / Placeholders | Clear |

### Findings

- **Functional Scope & Behavior** — FR-010 held "the step that owns the reported
  action" without saying how a step comes to own one. Every test of the hold and
  every implementation of it turns on the answer.
  Q: Which step does a standing block hold? → A: The step that was current when
  the report was made; the report names no step of its own.
  Basis: `design.md` § Behavior places the hold on "whichever step the event
  names", and the verb it renders — `wfctl blocked <action> --reason "…"` — carries
  no step argument. The current step is the only thing the command has to name.
  Decided against **a fixed action-to-step mapping held by wfctl**: the action is
  free text by an explicit decision in the same design ("an enum for `action`" is
  in Not Doing), so a mapping would have to be extended for every spelling an
  agent invents, and would silently hold nothing for one it had not seen.
  Decided against **the agent naming the step as an argument**: it adds a
  parameter the design's rendered surface does not have, and lets a blocked agent
  hold a step it is not standing on — a wider self-report than the level-2
  exception carves out.

- **Edge Cases & Failure Handling** — the spec said a person clears a hold and
  never said what happens when the blocked action later succeeds. A step held
  after its work demonstrably finished is the feature's most visible way to be
  wrong.
  Q: Does a later recorded success for the same action release the hold, or only
  an explicit clear? → A: Yes — the most recent event for an action stands,
  whether it is a block, a clearing, or a recorded success.
  Basis: `design.md` § Checked and assumed records having opened
  `_tracker.py:350-358` to confirm that a successful `wfctl issue
  comment|create|label` writes its event under the *verb's* spelling, and lists as
  a key assumption to validate "the action spelling an agent reports matches the
  one a later success records. Test with `gh issue comment` blocked, then `wfctl
  issue comment`." That assumption has no purpose unless a later success is what
  releases the block.
  Decided against **only an explicit clear releases**: it leaves a step held after
  the work finished through wfctl itself, and makes the checked fact and the
  assumption above both pointless.
  Decided against **only a success wfctl itself performed releases it**: `wfctl
  notify` exists precisely to record outward actions wfctl does not perform — a
  push, most of all — so excluding those holds a step after the person did the
  work and said so.

- **Domain & Data Model** — the spec named a block report as an entity without
  saying what it belongs to, which decides whether a block on one branch can hold
  a step on another.
  Q: What is a block scoped to? → A: The branch's own session state, alongside
  every other event.
  Basis: `design.md` renders the trunk-branch case — the report is recorded where
  there is no feature and no step to hold — so the store cannot be the feature
  directory. `session-state-is-re-derived` (accepted) puts what re-derivation
  cannot reach in the branch's state dir, and that is where every other wfctl
  event already lives.
  Decided against **the feature directory**: it has no home for the trunk-branch
  report the design explicitly keeps, and it is gitignored or outside the tree in
  most repos, so the trace would not survive where the design wants it.
  Decided against **repo-global**: a block recorded on one branch would hold a
  step on another, which is a hold nobody working on that branch can explain.

- **Non-Functional Quality Attributes** — FR-013 said a *person* clears a block
  and did not say whether that is enforced. It is the security posture of the one
  command in the feature that asserts a success.
  Q: Is clearing enforced as a person's action rather than the agent's? → A: No —
  ungated, the row closing an issue already occupies. The asymmetry is carried by
  the shape of the report command, which has no spelling that reports a success.
  Basis: `design.md` § Boundaries and Ownership — "`--clear` asserts a success, so
  it is a person's command, not the agent's — the row `wfctl issue close` already
  occupies" — and `AGENTS.md` § Safety, where `close` is ungated and never will
  be, because gating it would refuse the human who is the only actor allowed to
  run it.
  Decided against **gating it behind the notify grant**: it contradicts the reason
  the report itself is ungated (a host-blocked run may hold no grant), and it
  would refuse the person on exactly the branches where the block was recorded.
  Decided against **a new authority label of its own**: authority machinery for
  one command, resolved once per session by `wfctl start`, which is the wrong
  cadence for an act a person takes in the middle of one.
