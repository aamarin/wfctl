# Clarify scans — #200

## Session 2026-09-13

- Verdict: satisfied
- Scanned: spec.md
- Asked: 4 · Answered: 4 · Outstanding: 0 · Deferred: 2
- Detail: /Users/andremarin/Development/wfctl-specs/200-is-a-session-open-now/spec.md § Clarifications

### Coverage

| Category | Status |
| --- | --- |
| Functional Scope & Behavior | Resolved |
| Domain & Data Model | Resolved |
| Interaction & UX Flow | Clear |
| Non-Functional Quality Attributes | Resolved |
| Integration & External Dependencies | Resolved |
| Edge Cases & Failure Handling | Deferred |
| Constraints & Tradeoffs | Clear |
| Terminology & Consistency | Clear |
| Completion Signals | Deferred |
| Misc / Placeholders | Clear |

### Findings

- **Functional Scope & Behavior** — the spec described a wfctl surface and never
  said whether anything was obliged to call it, so a conforming implementation
  could ship the surface and leave #200 open in every repository.
  Q: Does this feature include the caller-side wiring that presents the identity,
  or only wfctl's own surface? → A: Both — the surface and the session-opening
  workflow that presents to it. Recorded as FR-013.
  Basis: derived, nobody present. `wfctl/agents/skills/start-session/` is package
  data wfctl ships, so the caller in wfctl's own pipeline is a wfctl artifact;
  `no-hardcoded-agent` already shows the shape for taking such a value from the
  environment without naming a host in a committed hook.
  Decided against **wfctl's surface only, wiring left to each project**: the
  defect stays open everywhere until some other change closes it, and no such
  change is planned or tracked.
  Decided against **wfctl presenting the identity itself from its own process**:
  that is wfctl deriving the identity, which the accepted record
  `session-identity-comes-from-the-caller` forbids in its own first sentence.

- **Non-Functional Quality Attributes** — nothing in the spec said whether a
  takeover was observable. A branch could change hands with the displaced
  conversation's only signal being a refusal that does not mention it.
  Q: Is a takeover visible, or does the branch quietly change hands? → A: Recorded
  on the branch's event record and reported by status. Recorded as FR-014 and
  SC-007.
  Basis: derived, nobody present. `wfctl/cli.py:164` states this CLI's posture for
  exactly this class of fact — one line per resolved state, never silence — and
  SC-005 already required a reader to distinguish a fresh branch from a held one
  without opening a file.
  Decided against **silent**: leaves the displaced conversation unable to
  distinguish a takeover from a branch it never held.
  Decided against **recorded but not surfaced**: reaching it would mean reading
  the event record directly, which FR-011 forbids callers from doing.

- **Domain & Data Model** — FR-012 was written into the spec by derivation and
  had no row in `design.md`'s ledger, so the lifecycle of a branch recorded
  before identities existed rested on one unattributed sentence.
  Q: What happens on a branch whose session was recorded before identities
  existed, when an identified session arrives? → A: Takeover — the identified
  session takes the branch. FR-012 stands as written.
  Basis: derived, nobody present. `design.md` decision 1 (an absent identity
  leaves a repository no worse off) and decision 2 (a new identity takes the
  branch over) both point here; the ledger simply never applied them to the
  upgrade case.
  Decided against **refuse until the branch is ended**: refuses every branch in
  flight at the moment the feature ships, which is a regression timed to release.
  Decided against **pass, since no identity is recorded**: such a branch would
  never become guarded, because nothing would ever record an identity on it.

- **Integration & External Dependencies** — six skills already gate on the
  existing "has a session ever run here" answer, and the spec did not say whether
  that answer keeps its meaning.
  Q: Does the existing answer change meaning, or does a second answer carry the
  new question? → A: It keeps its meaning; a second, distinct answer carries the
  new question. Recorded in FR-003 and SC-006.
  Basis: derived, nobody present. `design.md` state A — the branch has never had
  a session — is documented "True today, unchanged", and a repurposed field
  cannot answer it. `pipeline-state-is-one-payload` permits both facts in the one
  payload, so nothing forces a choice between them.
  Decided against **repurposing the existing answer**: state A and state C then
  render identically, which is #200's defect with the two states swapped.
  Decided against **removing it**: it is the only answer state A has.

### Deferred

- **Edge Cases & Failure Handling** — two conversations presenting different
  identities on one branch at the same moment. The record is append-only and the
  last write wins, so the behaviour is defined; whether it is the behaviour
  anyone wants is a question about the write path, which `/speckit.plan` owns.
- **Completion Signals** — SC-002 measures "zero behavioural differences across
  every gate this feature touches" against a gate surface nobody has enumerated.
  The enumeration is a plan artifact; asking for it here would have produced a
  list the spec has no place to put.
