# Analyze scans — #200, is a session open now?

## Session 2026-09-13

- Verdict: satisfied
- Scanned: spec.md, plan.md, tasks.md — all three present and read
- Findings: 6 · Critical: 0 · Acted on: 4 · Accepted: 2
- Detail: `/Users/andremarin/Development/wfctl-specs/200-is-a-session-open-now/checklists/analysis-report.md`

### Coverage

| Pass | Status |
| --- | --- |
| A · Duplication | Clear |
| B · Ambiguity | Clear |
| C · Underspecification | Outstanding (1 MEDIUM) |
| D · Constitution alignment | Clear (no constitution file; the six records `plan.md` substitutes were read) |
| E · Coverage gaps | Resolved (2 MEDIUM, tasks added) |
| F · Inconsistency | Resolved (1 HIGH, 1 MEDIUM) |
| G · Design-record contradiction | Deferred (no records section) |
| Requirement-to-task coverage | 100% |

Pass D is `Clear` rather than `Deferred` because it reached an answer. This
repository ships no `.specify/memory/constitution.md`; `plan.md` substitutes six
accepted architecture records and records the substitution in its Complexity
Tracking table, which is the plan template's own instruction. Each of the six was
compared against the task list and none is reversed.

Pass G is `Deferred` and not `Clear` because it never had an input. See G1.

### Findings

- **F · Inconsistency, HIGH** — T030 instructed the implementing run to move
  `docs/architecture/design/200-session-id-rides-on-the-start-event.md` from
  `proposed` to `accepted` once phases 3–5 were green. `wfctl arch accept`
  requires `--agreed`, *where the human agreed*, and its own help names
  implementation as the one evidence it will not promote on: "a record promoted
  on its own implementation can never disagree with the implementation." The task
  as written asked an unattended run to perform the one transition this
  repository reserves for a person.
  → Fixed: T030 now asks the reader for the citation and runs
  `wfctl arch accept 200-session-id-rides-on-the-start-event --agreed "<where>"`,
  quoting the sentence that rules out the old justification. Decided against
  deleting T030: the record does need promoting once the work lands, and dropping
  the task would lose the only thing that says so.

- **E · Coverage gaps, MEDIUM** — SC-004 ("no sequence of interrupted sessions
  leaves a branch in a state that requires manual cleanup") mapped to no task by
  reference or by keyword. T018 and T022 make it true in effect, which is what
  made it easy to miss: the property holds and nothing asserts it.
  → Fixed: T023a added to Phase 4 — open, abandon without `end`, take over,
  abandon again, take over again, and confirm every gate still answers. Decided
  against folding it into T023, which pins that a takeover never rewrites an
  earlier line: one assertion about the log, the other about recoverability, and
  a combined test would fail without saying which.

- **E · Coverage gaps, MEDIUM** — FR-010 and FR-011 are both MUST NOTs, and each
  was realised by a positive task with nothing asserting the negative. FR-010
  (the identity rides on the event record, not a separate file) had T018;
  FR-011 (skills obtain this answer from wfctl, never by reading the event record
  themselves) had T015. A `session.json` added later, or a skill grepping
  `events.jsonl`, would pass every test the plan named.
  → Fixed: T009a asserts the state dir gains no file; T017a greps
  `wfctl/agents/` for `events.jsonl` and allows only `start-session`'s stop-kind
  read, which asks a different question. Decided against one combined task: they
  land in different phases and different test files.

- **F · Inconsistency, MEDIUM** — `plan.md`'s Project Structure block listed
  three test files under `tests/`; `tasks.md` names nine. A reviewer reading the
  plan for the test surface saw a third of it.
  → Fixed: the plan's block now lists all nine. Decided against changing
  `tasks.md` instead — the tasks are the more recent artifact and the more
  specific, so the plan is the one that had drifted.

- **C · Underspecification, MEDIUM** — FR-014 requires a takeover be "reported by
  status, so that neither the displaced conversation **nor a later reader** has to
  read that record directly to learn the branch changed hands." What
  `contracts/cli.md` gives status is `session_holder`, a current-state field:
  after a takeover a third conversation reads `"other"`, which is exactly what it
  would read had no takeover ever happened. The displaced conversation is served
  — it gets `"other"` plus the second refusal string — and the later reader is
  not.
  → Accepted: out of scope — what `status` prints for a takeover is a surface
  decision `plan.md` and `contracts/cli.md` both left open, and choosing it here
  would decide something those artifacts have not.
  Not filed: outward actions are authorized on this branch, so the gate did not
  stop it; it is held for the reader, who has the report in front of them and may
  rule the later-reader half out of scope instead. Title and body below.

- **G · Design-record contradiction, MEDIUM** — pass G had no input.
  `design.md` carries no `## Software design decisions` section, so
  `reading-design-records` resolves the list as `unknown` and the pass had
  nothing to compare `tasks.md` against. The record exists and is named in prose
  under `## Level 3 — design`, which that skill explicitly does not read: "Prose
  in that section names no records." Four steps resolve `unknown` for this
  feature — plan, tasks, implement and analyze — so the record reached `plan.md`
  by a route nobody designed, which is `spec.md`'s Assumptions naming its path by
  hand.
  → Accepted: out of scope — the fix is in `design.md`, which is not one of the
  three artifacts this step may edit.
  Not filed: held for the reader, as above. Title and body below.

### Filing

- **What status reports about a takeover (C1)** — one finding, from pass C.
  Not filed: this run is attended, and both findings were handed to the reader
  with the report rather than opened as issues. Outward actions *are* authorized
  on this branch, so this is a deferral rather than a refusal.
  Title: `FR-014's "reported by status" is unserved for a later reader`
  Body:
  `#200's FR-014 requires a takeover be reported by status "so that neither the`
  `displaced conversation nor a later reader has to read that record directly to`
  `learn the branch changed hands".`
  ``
  `contracts/cli.md gives status one new field for this, session_holder, and it`
  `is a current-state field: "self" | "other" | "none" | "unknown". After a`
  `takeover a third conversation reads "other" — which is what it would read had`
  `no takeover ever happened. The two cases are indistinguishable from status.`
  ``
  `The displaced conversation is served: it gets "other" plus the second refusal`
  `string, which together say the branch is held by someone else. The later`
  `reader is not, and FR-014 names them both.`
  ``
  `Either status grows a surface that says the branch changed hands — a count, a`
  `last-takeover timestamp, a line in the console render — or FR-014's scope`
  `narrows to the displaced conversation and the "later reader" clause comes out.`
  `Both are decisions for /speckit.plan or for the reader; /speckit.analyze`
  `cannot make either without deciding something the artifacts left open.`

- **`design.md` does not index its own design record (G1)** — one finding, from
  pass G.
  Not filed: as above.
  Title: `#200's design.md has no "Software design decisions" section, so four steps see no records`
  Body:
  `reading-design-records resolves a feature's level-3 records from the list in`
  `design.md's "## Software design decisions" section. #200's design.md has no`
  `such section. It names the record in prose under "## Level 3 — design", which`
  `that skill explicitly does not read: "Prose in that section names no records."`
  ``
  `So the state resolves as unknown, and it resolves that way for all four`
  `consumers — /speckit.plan, /speckit.tasks, /speckit.implement and`
  `/speckit.analyze. Pass G in the #200 analyze scan is Deferred for this reason`
  `and for no other.`
  ``
  `The record is docs/architecture/design/200-session-id-rides-on-the-start-event.md.`
  `It reached plan.md anyway, because spec.md's Assumptions names its path by`
  `hand — a route nobody designed and which the next feature will not have.`
  ``
  `The fix for #200 is three lines in design.md. The wider question is whether`
  `/speckit.brainstorm writes that section reliably, since design-md-indexes-the-records`
  `is the decision this mechanism rests on and this feature's own design.md is a`
  `counter-example to it.`

### Deferred

- **G · Design-record contradiction** — the pass itself, not a finding within it.
  It can run for this feature as soon as `design.md` carries the section; until
  then no run of `/speckit.analyze` on this branch will reach an answer, and
  re-running this step before that changes nothing about this row.
