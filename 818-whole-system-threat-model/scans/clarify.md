## Session 2026-11-21

- Verdict: satisfied
- Scanned: spec.md
- Asked: 3 · Answered: 3 · Outstanding: 0 · Deferred: 0
- Detail: /Users/andremarin/Development/wfctl-specs/818-whole-system-threat-model/spec.md § Clarifications

### Coverage

| Category | Status |
| --- | --- |
| Functional Scope & Behavior | Resolved |
| Domain & Data Model | Clear |
| Interaction & UX Flow | Clear |
| Non-Functional Quality Attributes | Clear |
| Integration & External Dependencies | Resolved |
| Edge Cases & Failure Handling | Resolved |
| Constraints & Tradeoffs | Clear |
| Terminology & Consistency | Clear |
| Completion Signals | Clear |
| Misc / Placeholders | Clear |

### Findings

- **Functional Scope & Behavior**: the spec described `/threat-baseline` only with auto-approve on, and left the attended run unspecified.
  Q: What does `/threat-baseline` do when auto-approve is off? → A: It runs upstream's bootstrap and then upstream's interview with the user. The self-walkthrough runs only with auto-approve on.
  Basis: the user accepted the recommendation. Upstream's interview mode is built for an owner who's present, and the design describes the self-walkthrough as the stand-in for when nobody is.
  Decided against **B** (self-walkthrough always): it replaces upstream's interview with a weaker version when the person who can answer is there.
  Decided against **C** (bootstrap only, interview started by hand): an attended run would finish without the four questions being asked, and nothing prompts the user to start the interview later.
- **Integration & External Dependencies**: upstream calls its helper at a hardcoded `.claude/skills/_lib/` path, which resolves only for Claude.
  Q: How does `/threat-baseline` run the helper for an agent other than Claude? → A: The pass works the same for every agent, and `threat-baseline` tells the agent to run the helper from the `_lib` folder beside the skill it loaded.
  Basis: the user's answer after discussion. The user pointed out that the agent is always known at install, so a tree with no agent layer is a setup mistake `doctor` already reports. Each supported agent (Claude, Codex, Bob, Copilot) gets `_lib` copied into its own skills folder, so only upstream's path is wrong. Installing through agent plugin marketplaces instead was split out as #847.
  Decided against **A** (a fallback that builds the file without the helper): the helper is already installed for every agent, so a second way to build the file is redundant.
  Decided against **B** (agent writes the file another way, or records an exception): it assumed a tree with no agent layer was a supported setup, which the user corrected.
  Decided against **C** (skip the pass for repos without the Claude layer): repos on other agents would lose the baseline with no record of it.
- **Edge Cases & Failure Handling**: the spec scoped the pass to records the branch "adds or changes" as an assumption, which left a typo fix on an existing security record ambiguous.
  Q: Which level-2 records make the pass apply? → A: Records the branch adds or edits that carry a `## Threat model` section.
  Basis: the user accepted the recommendation. An edit to a security record usually means its control is changing, so it's a fair point to build a missing baseline.
  Decided against **B** (only records the branch adds): an edit that changes a control would skip the baseline.
  Decided against **C** (any security record in the repo): every branch would pause once the repo has one security record, including branches that never change a control.

Every other category was read and found Clear: the entities, the user flows, the edge cases already listed, the rejected alternatives, and the success criteria each have a testable statement in the spec.
