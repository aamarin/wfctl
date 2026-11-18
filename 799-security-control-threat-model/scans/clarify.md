# Clarify scan

## Session 2026-11-18

- Verdict: satisfied
- Scanned: spec.md
- Asked: 3 · Answered: 3 · Outstanding: 0 · Deferred: 0
- Detail: /Users/andremarin/Development/wfctl-specs/799-security-control-threat-model/spec.md § Clarifications

### Coverage

| Category | Status |
| --- | --- |
| Functional Scope & Behavior | Resolved |
| Domain & Data Model | Clear |
| Interaction & UX Flow | Resolved |
| Non-Functional Quality Attributes | Clear |
| Integration & External Dependencies | Clear |
| Edge Cases & Failure Handling | Resolved |
| Constraints & Tradeoffs | Clear |
| Terminology & Consistency | Clear |
| Completion Signals | Clear |
| Misc / Placeholders | Clear |

### Findings

- **Functional Scope & Behavior**: the trigger said "adds, removes, or narrows", which left a stricter control unclear.
  Q: Does a change that makes a control stricter need a threat model too? → A: Yes, any change to what a control refuses or lets through, so "adds, removes, loosens, or tightens".
  Basis: derived unattended from the repository. #769 made the accept check stricter, and #792 is the ordinary commands that change then refused. The record's "Must let through" list exists for that direction.
  Decided against **A (only add, remove, or narrow, as the issue words it)**: it leaves out the tightening that produced #792.
  Decided against **C (any change to a control's files)**: a rename or refactor changes nothing a threat model would say, and would send every guard edit through the pipeline.
- **Edge Cases & Failure Handling**: the spec didn't say what a reviewer does with a form in none of the record's lists.
  Q: What does the reviewer do with a form in none of the lists? → A: Judge it by "Defends against": a finding if that agent could reach it, a note otherwise, and either way ask for it to be added to a list.
  Basis: derived unattended. The "Defends against" part names the agent the control stops, so it settles the form without a bar written for the run.
  Decided against **A (always a finding that asks for the record to be extended)**: it treats every unlisted form as a regression, which is the #792 loop again.
  Decided against **C (not a finding)**: an agent the control defends against could reach the form, and a gap like that should block the change.
- **Interaction & UX Flow**: the spec didn't say whether the coordinator names the record in the brief.
  Q: Does the coordinator name the threat-model record in the brief? → A: No, the reviewer finds it by its heading.
  Basis: derived unattended from `fanning-out-code-review`, which gives each reviewer only its id and the reports folder, and from the record's rule that the coordinator sets no bar.
  Decided against **B (the coordinator lists the record paths)**: a coordinator that names one record can leave out another, and a reviewer that searches finds both.
