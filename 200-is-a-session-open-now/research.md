# Research — #200, is a session open now?

Phase 0. The Technical Context carries no `NEEDS CLARIFICATION` marker: every
value in it is read from this repository's own source, `AGENTS.md`, or its
accepted records. What follows is the research that removed the markers, plus
the two questions this feature ships without answering and the reason that is
safe.

## Decision: where the comparison lives

**Decision**: `wfctl/_session.py`, beside `session_started`.

**Rationale**: `session_started` reads `events.jsonl` for the first `start` line;
the new answer reads the same file for the *last* `start` line and compares one
field. Same file, same parse, same failure posture — a malformed line is skipped
rather than raised, because the log is appended to by every command and a
truncated final write must not make a running session look unstarted.

**Alternatives considered**:
- `_stall.py`, beside `opens_a_new_sitting`, which already walks the log for
  `start`/`end`/`resume`. Rejected: that function answers "did the previous
  sitting run anything", which is a different question with a different reason to
  change. Two questions in one function is how a later edit breaks the one nobody
  was looking at.
- A new `_identity.py`. Rejected under minimal-complexity bias: one module for
  two short functions, whose only caller is the module they would be split from.

## Decision: the id is read from `--session-id`, falling back to `WFCTL_SESSION_ID`

**Decision**: an explicit option, with an environment fallback wfctl names.

**Rationale**: `session-identity-comes-from-the-caller` states this shape
directly — wfctl names *its own* variable and never the host's. That is what makes
a wrong guess about the host a mapping to fix rather than a design to redo: the
host's spelling lives in the shipped skill, on one line, where changing it is a
one-line edit rather than a code change.

**Alternatives considered**:
- wfctl reading `CLAUDE_CODE_SESSION_ID` directly. Rejected by the accepted
  record, in its own first sentence: it names a particular host, and wfctl ships
  to repositories that use none.
- Option only, no environment fallback. Rejected: the committed hook shape
  `${WFCTL_AGENT:+--agent "$WFCTL_AGENT"}` that `no-hardcoded-agent` establishes
  needs a variable to key on, and inventing a second mechanism for the second
  value of this kind would leave the two inconsistent.

## Decision: the takeover is an appended `start` event, not a rewritten one

**Decision**: append a `start` line carrying the new id. Never rewrite or clear
an earlier line.

**Rationale**: the log is append-only and every reader of it tolerates lines it
does not understand. A takeover is therefore a new line, the branch's current
holder is the last `start` line carrying an id, and the history of who held the
branch survives — which is what makes FR-014's "reported by status" answerable
without a second file.

**Alternatives considered**:
- A `session.json` beside `mode.json`. Rejected in
  `design/200-session-id-rides-on-the-start-event.md`: it would need clearing on
  `end`, and the process most likely to skip that is the one that crashed, so the
  file goes stale exactly when it matters.
- Rewriting the last `start` line in place. Rejected: it destroys the takeover
  history FR-014 reports, and it makes the log the one file in the state dir that
  is not append-only, which every reader's malformed-line tolerance assumes.

## Decision: two new payload fields, not one repurposed

**Decision**: `session_started` keeps its meaning. The payload gains a second
answer for "is a session open for this caller", and the identity of the holder.

**Rationale**: settled at clarify (Q4). `design.md` state A — the branch has never
had a session — is documented "True today, unchanged", and a repurposed field
cannot answer it. `pipeline-state-is-one-payload` permits both facts in one
payload, so nothing forces a choice.

**Alternatives considered**: repurposing, and removal. Both recorded with their
reasons in `docs/architecture/scans/200-clarify.md`.

## Open: does the host's id stay stable within a long session?

**Status**: unresolved, and shipped unresolved on purpose.

Measured on 2026-09-13 in this worktree, twice and independently: across a
context clear in the same pane, `CLAUDE_CODE_SESSION_ID` changed and
`CLAUDE_CODE_BRIDGE_SESSION_ID` did not. What is **not** measured is whether the
first stays fixed across hours of one conversation. If it rotates mid-session,
every command reads as a takeover and the log fills with sittings nobody opened.

**Why it is safe to ship without the answer**: wfctl stores an opaque value, so
this is a wiring question, not a design question. The variable the shipped skill
presents is one line in one file; a rotation discovered later is corrected there
without touching wfctl's surface, its tests, or its records. The alternative —
holding the feature until a long-session measurement exists — blocks a defect fix
on an observation that takes hours to make and has no bearing on whether the
surface is right.

**How it would be caught**: a takeover is visible (FR-014), so a rotating host
announces itself as repeated takeovers in one sitting rather than as silence.
That visibility is what converts this from a lurking defect into a legible one,
and is a second reason FR-014 is not cosmetic.

## Open: what does the host's nesting marker mean?

**Status**: unresolved, and depended on by nothing.

`CLAUDE_CODE_CHILD_SESSION=1` was observed in a conversation with no parent, and
again on 2026-09-13. `session-identity-comes-from-the-caller` builds a paragraph
on reading that flag as a nesting marker — resolve the innermost host's own
variable rather than the first one found set — and that paragraph has no signal
to key on if the flag is set unconditionally.

**Why it is safe**: no requirement in `spec.md` depends on it. The consequence is
that a sub-agent presenting a different id takes the branch over from the
conversation that spawned it, which is recorded as an edge case rather than
prevented. Preventing it needs a trustworthy nesting signal, which no measurement
has yet produced.

**What it obliges**: the record's paragraph needs revisiting or removing, which
is an amendment to an accepted record and belongs to whoever makes the
measurement — not to this feature, which neither relies on the paragraph nor
contradicts it.
