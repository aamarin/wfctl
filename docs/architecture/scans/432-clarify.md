# Clarify scan: #432

## Session 2026-11-02

- Verdict: satisfied
- Scanned: spec.md
- Asked: 4 · Answered: 4 · Outstanding: 0 · Deferred: 0
- Detail: /Users/andremarin/Development/wfctl-specs/432-start-session-loads-issue-context/spec.md § Clarifications

### Coverage

| Category | Status |
| --- | --- |
| Functional Scope & Behavior | Resolved |
| Domain & Data Model | Clear |
| Interaction & UX Flow | Clear |
| Non-Functional Quality Attributes | Clear |
| Integration & External Dependencies | Resolved |
| Edge Cases & Failure Handling | Clear |
| Constraints & Tradeoffs | Clear |
| Terminology & Consistency | Clear |
| Completion Signals | Resolved |
| Misc / Placeholders | Clear |

### Findings

- **Completion Signals**: The accepted record `session-report-built-in-code.md` and the issue's done-when both list a size-limit test on `start-session/SKILL.md`, while `design.md` put it out of scope after the user said the rewrite doesn't need to optimize the file's size.
  Q: Does #432 keep the size-limit test? → A: No. It moves to #693, which asks for a person's approval when any skill grows more than 30% past its last approved size, and whether the skill should be split.
  Basis: The user chose it. They proposed the growth check after seeing that the file grew 66%, from 15.8 KB to 26.2 KB.
  Decided against **Keep the test in scope**: a fixed limit on one file only blocks growth, and the user wanted the growth to prompt a review of whether the skill should be split.
  Decided against **Drop it and edit the issue and record**: this would lose the check entirely, and the user wanted it kept as its own issue.
- **Functional Scope & Behavior**: The issue says the report gives the handoff's path rather than retelling it, but the step 8 decision quotes a line from the handoff, so the agent would open the file anyway.
  Q: How much of the handoff does the report print? → A: All of `session-summary.md`, word for word.
  Basis: The user chose it. An agent on an issue branch reads the rest of the handoff almost every session, so a partial print saves nothing and costs an extra read.
  Decided against **Path only**: the agent would open the file every session before deciding what to do.
  Decided against **The path, `In Flight`, and the Next Session TODO list**: the agent would still open the file for the decisions and reasoning sections, and pay for the TODO list twice.
  Decided against **Only the first TODO item**: it drops the other open items, including the ones waiting on the user.
- **Functional Scope & Behavior**: With the issue list gone, the commit check compares against the branch's own issue, and the spec didn't say whether wfctl or the agent does the comparison.
  Q: Who flags commits that don't mention the branch's issue? → A: wfctl, in the report.
  Basis: The user chose it, matching both accepted records, which move rules about the session report out of skill prose and into wfctl.
  Decided against **The agent does it**: the rule stays in instructions the agent can skip without leaving a trace, which `a-rule-is-expressed-as-a-check.md` describes.
  Decided against **Drop the check**: a commit for another issue on a worktree branch is rare but possible, and the check is cheap in code.
- **Integration & External Dependencies**: The `branch` verb reports a count of unanswered review comments, and a GitHub comment can be replied to, resolved, or both.
  Q: What counts as unanswered? → A: A review thread that isn't resolved, whether or not someone has replied.
  Basis: The user chose it. Resolving a thread is how the repository marks a comment as dealt with, since the convention is to reply and then resolve.
  Decided against **Threads with no reply from the PR author**: a reply can be a question back, which leaves the comment open.
  Decided against **Every review comment as a plain count**: it counts addressed comments too, so the line can't say whether anything is waiting.

### Outstanding

None. Every category above was read, and the four questions asked were all answered.

### Deferred

None.
