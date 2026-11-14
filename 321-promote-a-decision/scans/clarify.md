# Clarify scans — #321

## Session 2026-09-09

- Verdict: satisfied
- Scanned: spec.md
- Asked: 4 · Answered: 4 · Outstanding: 0 · Deferred: 2
- Detail: /Users/andremarin/Development/wfctl-specs/321-promote-a-decision/spec.md § Clarifications

### Coverage

| Category | Status |
| --- | --- |
| Functional Scope & Behavior | Clear |
| Domain & Data Model | Clear |
| Interaction & UX Flow | Clear |
| Non-Functional Quality Attributes | Resolved |
| Integration & External Dependencies | Clear |
| Edge Cases & Failure Handling | Resolved |
| Constraints & Tradeoffs | Clear |
| Terminology & Consistency | Resolved |
| Completion Signals | Clear |
| Misc / Placeholders | Clear |

### Findings

- **Non-Functional Quality Attributes** — the history line is dated `YYYY-MM-DD`
  with no zone, and nothing said which clock.
  Q: local date or UTC? → A: UTC. Decided against the local date, which is what
  the person running the command believes the date to be and is friendlier for a
  single maintainer: it makes the field depend on where that maintainer was
  sitting, and every other timestamp wfctl writes is UTC (`_session.py:38`,
  `_verify.py:174`, `_io.py:40`, `_archive.py:104`). Cost named in the spec — a
  maintainer west of UTC accepting late in the evening records tomorrow's date.

- **Non-Functional Quality Attributes** — observability: whether the transition
  also lands in the session event log.
  Q: should `events.jsonl` gain a line? → A: no. Decided against logging it: the
  event log is per-branch, uncommitted, and dies with the worktree, while the
  record outlives it (FR-010), so a second durable answer to "when was this
  accepted" could disagree with the first. The observable artifact is the
  committed history line.

- **Terminology & Consistency** — the issue says "promote", the status value is
  `accepted`, and the first spec draft used both for one transition.
  Q: which is canonical? → A: `accept` is the verb, `accepted` the status.
  Decided against "promote", which reads better in the issue's own framing: the
  status value is fixed in `_arch.STATUSES` and a command whose name does not
  match the value it writes makes a reader hold two words for one transition.
  "Promotion" survives in prose about the backlog awaiting one.

- **Edge Cases & Failure Handling** — FR-005 reads a status and then writes, and
  the pair is not atomic.
  Q: what happens if two runs interleave? → A: two history lines; accepted and
  recorded as NFR-002. Decided against a lock file: the actor is a person at a
  local CLI on a record they have just agreed to, and a lock adds durable state to
  a repository whose records carry none. The write itself stays all-or-nothing.

### Deferred

- **Domain & Data Model** — whether the citation should be a structured field
  (issue key, review URL) rather than free text. Belongs to a later change: the
  two existing hand-written acceptances cite an issue and a shipped release
  respectively, so the shape is not yet knowable from two samples, and a
  structure guessed now would refuse the second one.
- **Interaction & UX Flow** — whether `wfctl arch context` should list the
  withheld slugs rather than only counting them. Answered for this feature by
  putting the listing in the acceptance command's own refusal path (FR-007), so
  it appears where someone is acting on it. Whether the contract surface should
  also carry it is a change to a command every session runs, and belongs to
  whoever owns that output.
