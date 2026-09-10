---
disable-model-invocation: true
description: Identify underspecified areas in the current feature spec by asking up to 5 highly targeted clarification questions and encoding answers back into the spec.
handoffs:
  - label: Build Technical Plan
    agent: speckit.plan
    prompt: Create a plan for the spec. I am building with...
allowed-tools: Read Glob Write Edit Bash(.specify/scripts/bash/check-prerequisites.sh*) Bash(wfctl status*) Bash(wfctl arch-root*) Bash(wfctl arch check*) Bash(git add*) Bash(git commit*)
---

## User Input

```text
$ARGUMENTS
```

You **MUST** consider the user input before proceeding (if not empty).

Read `.agents/skills/speckit-clarify/SKILL.md` (or `../skills/speckit-clarify/SKILL.md` relative to this file, if `.agents/skills` isn't present) for the complete clarification workflow.

## Write the scan file

Follow `.agents/skills/writing-a-scan-file/SKILL.md` (or
`../skills/writing-a-scan-file/SKILL.md` relative to this file, if
`.agents/skills` isn't present). It owns the destination, the session rule, the
commit and the check. What it does not own is what *this* step scanned, which is
below.

**File**: `<arch-root>/scans/<issue>-clarify.md`.
**Detail**: `FEATURE_DIR/spec.md` § Clarifications.

**Coverage rows** — the ten taxonomy categories the workflow above scans, in its
order, every one of them present:

```
Functional Scope & Behavior          Edge Cases & Failure Handling
Domain & Data Model                  Constraints & Tradeoffs
Interaction & UX Flow                Terminology & Consistency
Non-Functional Quality Attributes    Completion Signals
Integration & External Dependencies  Misc / Placeholders
```

The map behind them already exists: step 2 above builds it on every run and
discards it unless no question is asked. Writing it down is what this step stops
throwing away.

Its scanning vocabulary is Clear / Partial / Missing and its reporting vocabulary
is Clear / Resolved / Deferred / Outstanding. **The reported one is what goes in
the file** — a reader wants what the scan concluded, not what it saw first.

**Verdict, for this step**: `satisfied` — the scan ran and nothing material is
open. `unsatisfied` — a category is Outstanding, or a high-impact one is
Deferred. `inconclusive` — the scan could not run: no `spec.md`, or one still
carrying its template.

**Section shape**:

```markdown
## Session YYYY-MM-DD

- Verdict: satisfied
- Scanned: spec.md
- Asked: N · Answered: N · Outstanding: N · Deferred: N
- Detail: <FEATURE_DIR>/spec.md § Clarifications

### Coverage

| Category | Status |
| --- | --- |
| Functional Scope & Behavior | Clear |
| … the nine others |

### Findings

- **<category>** — what was ambiguous.
  Q: <the question> → A: <the answer>. Decided against <the alternative>: <why>.

### Deferred

- **<category>** — <what was not asked, and why it belongs to a later step>.
```
