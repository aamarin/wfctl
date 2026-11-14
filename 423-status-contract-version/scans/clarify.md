# Clarify scans — #423

## Session 2026-09-20

- Verdict: satisfied
- Scanned: spec.md
- Asked: 5 · Answered: 5 · Outstanding: 0 · Deferred: 0
- Detail: /Users/andremarin/Development/wfctl-specs/423-status-contract-version/spec.md § Clarifications

### Coverage

| Category | Status |
| --- | --- |
| Functional Scope & Behavior | Clear |
| Domain & Data Model | Resolved |
| Interaction & UX Flow | Clear |
| Non-Functional Quality Attributes | Clear |
| Integration & External Dependencies | Resolved |
| Edge Cases & Failure Handling | Resolved |
| Constraints & Tradeoffs | Resolved |
| Terminology & Consistency | Clear |
| Completion Signals | Clear |
| Misc / Placeholders | Clear |

### Findings

- **Integration & External Dependencies** — the spec required a version and a
  shipped shape file without saying which of them the emitted version comes from,
  so the behaviour when a package ships without the file was undefined.
  Q: Where does the emitted version come from — the shipped file, or code?
  → A: Code. The file records it too and a check proves they agree; a package
  built without the file is caught by the packaging check before release.
  Basis: the reviewer, who objected that reading the file at runtime makes a
  consumer's process pay for a packaging fault it cannot cause, detect early or
  work around. The objection stands against the spec's own Validation Strategy,
  which already requires building the package and confirming the file is inside
  it — so the loud failure was already happening in CI and reading at runtime
  added no detection, only a victim.
  Decided against **read the version from the shipped file**: it moves an
  already-caught fault onto the consumer.
  Decided against **constant in code, with the command warning when the file is
  absent**: the warning reaches the consumer, who can do nothing about it, and
  the machine-readable path is the one place a warning is least welcome.

- **Domain & Data Model** — the check compares emitted paths against recorded
  ones in both directions, and three parts of the payload are empty in an
  ordinary worktree: the attention answer, the stall, and a step's nested passes.
  Their inner paths are recorded and never emitted, so the comparison fails on a
  clean tree.
  Q: How are paths a single run cannot exercise covered?
  → A: Several fixture states, each placing the payload in one named condition;
  the comparison runs against the union of what they emit.
  Basis: the reviewer accepted the recommendation. It keeps the promise grounded
  in bytes the command actually produced, which is the property the whole file
  rests on.
  Decided against **marking those paths optional in the file**: the optional ones
  would be precisely the new fields this feature adds, so the check would be
  weakest exactly where it is newest.
  Decided against **one maximal fixture populating every branch at once**: it
  works only while every optional branch can hold simultaneously, and a future
  pair of mutually exclusive states breaks it with no warning.
  Decided against **deriving the shape from the builder's type declarations**:
  the declarations are what a reviewer already reads; the point of the file is to
  record what was emitted, and a derivation from types cannot disagree with them.

- **Constraints & Tradeoffs** — the spec said a failing check names the bump the
  change owes, and never said who applies it or whether a command exists.
  Q: Is the recorded file hand-maintained or regenerated, and does the version
  move on its own?
  → A: A command regenerates the paths and applies the bump the comparison
  computes, with a way to hold the version for a break the author chooses not to
  publish yet.
  Basis: the reviewer pressed on why a hand edit mattered, and it does not. The
  argument for it was that typing the version is where an author decides whether
  they meant to break a consumer; editing one line to turn a red test green is a
  reflex, and friction that small fails exactly when someone is in a hurry. What
  actually catches an unintended rename is the rename sitting in the diff under
  review, which happens under every option. `a-rule-is-expressed-as-a-check` puts
  a rule whose violation is visible in an artifact on the check's side rather
  than the ritual's.
  Decided against **hand-maintained, with the failing check naming the paths**:
  the number it protects is the one thing that drifts, which is the defect the
  file exists to remove.
  Decided against **a command that rewrites paths and refuses to touch the
  version**: the same ritual with fewer keystrokes.
  Decided against **no command, the check printing a file to paste**: pasting is
  a hand edit performed less carefully.

- **Domain & Data Model** — the spec required each path's type to be recorded and
  did not say in whose vocabulary.
  Q: What does a recorded type say?
  → A: JSON type names with nullability spelled out — `object | null`, `string`.
  Basis: the reviewer accepted the recommendation. The attention answer and the
  stall are each an object or nothing, and whether a consumer must handle nothing
  is the single branch its code turns on.
  Decided against **JSON type names without nullability**: it erases the one
  distinction the two new fields turn on.
  Decided against **Python type names**: readable only to a reader who knows the
  language wfctl happens to be written in, which is the reach the file was chosen
  over a constant to gain.
  Decided against **full JSON Schema**: it answers a question nobody asked — the
  check compares paths and types, and a schema's remaining power would be
  unexercised and unmaintained.

- **Functional Scope & Behavior** — FR-017 placed the nested list of declared
  passes inside the versioned surface, and the design named it the bet most worth
  a reviewer's disagreement.
  Q: Is that list's inner shape versioned, or free to change?
  → A: Versioned. FR-017 stands, now confirmed rather than assumed.
  Basis: the reviewer, asked directly. A consumer cannot see the difference
  between a field and an implementation detail, so anything readable and unmarked
  is something it will read, and a rename there is the silent break the version
  exists to stop.
  Decided against **recording the list as an array and stopping**: it leaves the
  break unversioned in the one part of the payload most likely to be restructured.
  Decided against **versioning it but marking it provisional pending #426**: a
  provisional marking is a promise a consumer cannot act on, and #433 is already
  held for the question #426 would settle.

The scan also reached a gap it did not close, recorded in the spec's Edge Cases
and Assumptions rather than resolved: part of this contract is carried in values
rather than in keys. Reordering the rank, adding a fourth kind of attention, or
changing what a detail means each leave every key and every type identical, so no
check here fires and the version does not move. The design named the rank alone;
this scan widened it to the class, and the level-3 record should be widened to
match. Closing it needs a different mechanism than a map of key paths to types,
which is why it is named rather than absorbed.
