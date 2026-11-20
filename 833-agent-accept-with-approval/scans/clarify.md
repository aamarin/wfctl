# Clarify scan — 833-agent-accept-with-approval

## Session 2026-11-20

- Verdict: satisfied
- Scanned: spec.md
- Asked: 3 · Answered: 3 · Outstanding: 0 · Deferred: 3
- Detail: /Users/andremarin/Development/wfctl-specs/833-agent-accept-with-approval/spec.md § Clarifications

### Coverage

| Category | Status |
| --- | --- |
| Functional Scope & Behavior | Resolved |
| Domain & Data Model | Clear |
| Interaction & UX Flow | Resolved |
| Non-Functional Quality Attributes | Resolved |
| Integration & External Dependencies | Deferred |
| Edge Cases & Failure Handling | Deferred |
| Constraints & Tradeoffs | Clear |
| Terminology & Consistency | Clear |
| Completion Signals | Clear |
| Misc / Placeholders | Deferred |

### Findings

- **Functional Scope & Behavior** — the spec dropped the typed confirmation without a terminal, and said nothing about a run at a terminal.
  Q: When the user runs review sign-off or approve-imports in their own terminal, does it still ask for the typed head sha or digest? → A: Yes, keep it at a terminal.
  Basis: the user chose the recommended option in this session.
  Decided against **Drop it everywhere**: a run in the user's own terminal has no host prompt before it, so the typed sha is its only confirmation.
- **Interaction & UX Flow** — the spec's `Log` line for a missing `--agreed` claimed a prompt even when the user typed the command at a terminal.
  Q: When the user accepts a record in their own terminal with no `--agreed`, what does the `Log` line say? → A: `--agreed` stays required at a terminal.
  Basis: the user chose this over the recommendation in this session.
  Decided against **"run at the terminal"**: the user preferred keeping today's terminal behavior unchanged over adding a second fixed line.
  Decided against **Same prompt line for both**: it claims a prompt that never happened when the user typed the command.
- **Non-Functional Quality Attributes** — the spec's security check said "its environment names Claude Code" without saying which signal.
  Q: How does a command tell it's running inside Claude Code before it skips the terminal check? → A: The variable Claude Code itself sets in its shell.
  Basis: the user chose the recommended option in this session. The user's profile sets `WFCTL_AGENT=claude` in every shell, so that variable would pass in a plain terminal or another host.
  Decided against **WFCTL_AGENT**: it's true in any shell where the profile sets it.

### Outstanding

None.

### Deferred

- **Integration & External Dependencies** — which variable Claude Code sets, and whether Bob Shell's payload carries `tool_name`. Both are facts to read from each host, so the plan confirms them.
- **Edge Cases & Failure Handling** — whether the dry run moves to a spelling the host's rule doesn't match. The design doc leaves this to the plan.
- **Misc / Placeholders** — Codex support waits on a session in Codex, outside this feature, as the spec's Assumptions say.
