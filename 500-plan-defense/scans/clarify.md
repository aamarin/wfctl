# Clarify scans — #500

## Session 2026-09-27

- Verdict: satisfied
- Scanned: spec.md
- Asked: 2 · Answered: 2 · Outstanding: 0 · Deferred: 1
- Detail: /Users/andremarin/Development/wfctl-specs/500-plan-defense/spec.md § Clarifications

### Coverage

| Category | Status |
| --- | --- |
| Functional Scope & Behavior | Clear |
| Domain & Data Model | Clear |
| Interaction & UX Flow | Resolved |
| Non-Functional Quality Attributes | Clear |
| Integration & External Dependencies | Deferred |
| Edge Cases & Failure Handling | Clear |
| Constraints & Tradeoffs | Clear |
| Terminology & Consistency | Resolved |
| Completion Signals | Clear |
| Misc / Placeholders | Clear |

### Findings

- **Interaction & UX Flow** — the spec said two things about a person who runs
  `/plan-defense` while auto-approve is on. FR-014 refused only when orchestrate
  invoked the skill, and Story 3 and an Assumptions bullet said a person who
  typed it would get credit.
  Q: What should `/plan-defense` do when a person types it while auto-approve is
  on?
  → A: Always refuse. The skill asks nothing, writes nothing, and says to run
  `wfctl start --no-auto-approve` first. FR-014, Story 3, and the Assumptions
  bullet now say the same.
  Basis: Andre chose the recommendation. The skill has no reliable way to tell a
  command a person typed from one orchestrate issued, and a wrong guess means the
  agent answers its own questions, which is the one outcome the check exists to
  prevent. A marker an attended run wrote still reads done after auto-approve is
  turned on again, so no finished defense is lost.
  Decided against **run if the person typed it**: it needs a signal for who
  issued the command, and the skill has none.
  Decided against **always run**: unattended, the agent asks and answers its own
  questions, and the pass reads done on a check nobody ran.

- **Terminology & Consistency** — FR-018 put the `wfctl.json` snippet that
  declares the pass in the README, and the README never mentions `wfctl.json`.
  This repository documents its `wfctl.json` keys in `docs/reference.md`
  (`change_check` has its own section there) and in `AGENTS.md`, and no shipped
  skill carries its own declaration snippet. The `steps` key has no section in
  `docs/reference.md` yet.
  Q: Where is the `wfctl.json` snippet that declares the pass documented?
  → A: In `docs/reference.md`, in a new section on declaring a repository's own
  steps that covers `needs_person` and uses plan-defense as its example. The
  skill's `SKILL.md` points to that section in one line.
  Basis: Andre first accepted `SKILL.md`, then asked whether that was what the
  repository does for similar keys. A search showed it is not, and he approved
  `docs/reference.md` instead. The answer matched none of the offered options.
  Decided against **the skill's `SKILL.md`**: no shipped skill documents a
  `wfctl.json` key, and a maintainer looking for configuration reads the
  reference, not a skill.
  Decided against **a new README section**: the README documents no
  `wfctl.json` key, and one section for this pass alone would be the only one.
  Decided against **both**: two copies of one snippet drift apart, and only one
  of them is checked by FR-018.

### Deferred

- **Integration & External Dependencies** — whether the skill needs an entry in
  `_MIRRORED_SKILLS`. The mirror test named in that set's comment decides it
  during implementation, and the answer changes no requirement here.
