# Clarify scans — #188

## Session 2026-09-11

- Verdict: satisfied
- Scanned: spec.md
- Asked: 3 · Answered: 3 · Outstanding: 0 · Deferred: 0
- Detail: <FEATURE_DIR>/spec.md § Clarifications

### Coverage

| Category | Status |
| --- | --- |
| Functional Scope & Behavior | Resolved |
| Domain & Data Model | Clear |
| Interaction & UX Flow | Clear |
| Non-Functional Quality Attributes | Resolved |
| Integration & External Dependencies | Resolved |
| Edge Cases & Failure Handling | Clear |
| Constraints & Tradeoffs | Clear |
| Terminology & Consistency | Clear |
| Completion Signals | Clear |
| Misc / Placeholders | Clear |

### Findings

- **Functional Scope & Behavior** — FR-005 said the cycle is "handoff, then
  reset, then session start" without establishing that the handoff earns its
  place. `design.md` carried it as an open question, so the spec was asserting
  something its own upstream document had not settled.
  Q: Does the cycle run `/end-session` before the reset, or only reset and
  resume? → A: It runs `/end-session` first. `session-state-is-re-derived`
  reserves the session file for "the handoff prose a human or agent wrote
  deliberately", and nothing else writes it; `start-session`'s step 9 then
  routes on whether `session-summary.md` names a first action, so a returning
  session with no summary lands in that table's last row and asks a human what
  to work on.
  Decided against **B, reset and resume only**: it is cheaper and it is the one
  option that provably stalls the unattended run — the returning session has no
  quotable first action, which is precisely the state `start-session` is written
  to stop on.
  Decided against **C, run the handoff only when the window holds prose the
  artifacts do not**: sound in principle and it is the self-report
  `wfctl-owns-the-recycle-verdict` rejects one level up. The agent judging what
  of its own context is worth keeping is the judgment the cycle exists to stop
  depending on.

- **Non-Functional Quality Attributes** — FR-012 fixed the threshold as a single
  value in source without saying what it measures against, and a token count and
  a percentage are different requirements.
  Q: What is the threshold measured against? → A: An absolute token count held in
  wfctl's source. Read directly from this session's transcript, the usage object
  carries `input_tokens`, `cache_read_input_tokens`, `cache_creation_input_tokens`
  and `output_tokens` and no context-window total, so a percentage is not
  computable from what wfctl is handed.
  Decided against **B, a fraction of a window size wfctl derives**: it would need
  a model-to-window-size table inside wfctl, which drifts with every model release
  and would make a pipeline step wrong in a way no test on this repo could catch.
  Decided against **C, a fraction of a window size the transcript reports**:
  falsified by reading the transcript — the field is not there. This was the
  option that looked best before it was checked, which is why it was checked.

- **Integration & External Dependencies** — FR-005 and FR-006 branch on whether
  the pane is registered, and nothing said who answers that question. It matters
  because one of the two candidates is forbidden from asking.
  Q: How does the run know whether its pane can be sent to? → A: The orchestrating
  skill asks, not wfctl. `wfctl-names-the-reset-it-cannot-perform` holds that
  wfctl declines the multiplexer dependency by construction, and `_workmux.py`
  states in its own docstring that it "never calls `subprocess`".
  Decided against **A, wfctl reports it on the payload**: it would put a
  multiplexer query inside `build_report`, which every view of pipeline state
  calls — so the cost lands on `wfctl status` in repos that will never recycle
  anything, and the dependency lands in the module written to exclude it.
  Decided against **C, attempt the send and fall back on failure**: the failure is
  not observable. A send to this pane during the design pass exited 0 and printed
  nothing, so an exit code distinguishes neither a delivered prompt from a
  dropped one nor either from a missing pane.

### Correction, same session

The Functional Scope answer above is right that the handoff must be written and
wrong about what writes it. `wfctl end` also appends `{"event": "end"}`, and
`start-session`'s step 9 routes a branch carrying one into its second row, which
asks a human what to work on — so the cycle as answered would leave every
unattended run stopped on a question at the moment its window was freshly empty.
The skill states the property directly: "a branch that has ended a session once
is in row two from then on, even unattended".

The answer stands; its mechanism does not. `spec.md` FR-005a now carries the
constraint, and the choice between a distinct recycle event and a fourth row in
step 9's table belongs to `/speckit.plan`.

Found by reading, before the acceptance test was driven. Recorded here rather
than silently amending the finding above, because a scan that corrected itself
and one that got it right first time should not read the same.
