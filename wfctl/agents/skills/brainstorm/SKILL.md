---
name: brainstorm
description: Turn rough ideas into fully-formed designs through collaborative dialogue before any implementation. Facilitates structured brainstorming sessions with Socratic questioning, approach evaluation, and design documentation. Use when starting a new feature or major change that needs design thinking before coding.
---

# Brainstorming Skill

**Purpose**: Turn rough ideas into fully-formed designs through collaborative dialogue before any implementation begins.

**Philosophy**: A hard gate that prevents ANY implementation (code writing, scaffolding, etc.) until a design is presented and approved by the user.

**Scope**: This is a pre-speckit workflow. It produces `specs/<branch>/design.md`, which `/speckit.specify` and `/speckit.brainstorm` read as their starting point. Use it when you want a structured dialogue before entering the speckit pipeline. It is a different skill from `brainstorming` — that one is the speckit-integrated variant that calls `idea-refine` and `design-levels`.

---

## Step 1 — Explore project context

Understand the existing codebase, patterns, and constraints before asking questions.

- Use `list_files` to explore relevant directories
- Use `read_file` to review key files mentioned in the idea
- Use `grep` to find existing patterns
- Use `glob` to locate similar implementations

Output: brief summary of relevant context (2–3 sentences max).

---

## Step 2 — Ask clarifying questions (one at a time)

Understand purpose, constraints, and success criteria through Socratic dialogue.

Ask ONE question at a time. Prefer multiple-choice framing over open-ended. Continue until you can answer all of:

- Who will use this?
- What problem does it solve?
- What are the constraints?
- How will we measure success?
- What's explicitly out of scope?

Stop when you can answer all five confidently.

---

## Step 3 — Propose 2–3 approaches

Present options with trade-offs and a recommendation. For each approach:

- **Description**: 1–2 sentence overview
- **Pros**: 3–4 key benefits
- **Cons**: 2–3 key limitations
- **Why recommended** (for your top choice only)

Ask the user to choose before continuing.

---

## Step 4 — Present the design in sections (one at a time)

Break the design into digestible sections and get approval for each before continuing.

Section order (adapt to the feature):
1. **Overview** — high-level description, key components, interactions
2. **Core Functionality** — main features, workflows, data flow
3. **Edge Cases & Error Handling** — failure modes, recovery
4. **Integration Points** (if applicable) — connections to existing code, APIs
5. **Testing Strategy** — verification approach, test scenarios

Present one section, wait for approval, then continue.

---

## Step 5 — Write the design document

Create a permanent record of the approved design. Use `wfctl feature-paths` to get the branch's spec directory:

```bash
eval "$(wfctl feature-paths)"   # binds FEATURE_DIR
```

Write to `$FEATURE_DIR/design.md`. Outside a wfctl repo, use `specs/<branch>/design.md`.

**Document structure**:

```markdown
# [Feature Name] — Design Document

**Created**: [Date]
**Status**: Approved for Implementation

---

## Context
[Why this feature is needed]

## Requirements

### Functional Requirements
- [Requirement 1]

### Non-Functional Requirements
- [Performance, security, etc.]

### Constraints
- [Technical or business constraints]

## Approach

### Chosen Approach: [Name]
[Description]

**Why this approach**:
- [Reason 1]

### Alternatives Considered
**[Alternative 1]**: [Why not chosen]

## Design Details

### [Section 1 Name]
[Content from approved section]

## Implementation Notes

### Integration Points
- [How this connects to existing code]

### Testing Strategy
- [How to verify it works]

### Risks & Mitigations
- [Potential issues and how to handle them]

## Trade-offs
[Document the trade-offs made]

## Success Criteria
- [ ] [Measurable outcome 1]

---

**Next Steps**: `/speckit.specify` reads this file as its starting point.
```

---

## Step 6 — Spec self-review

Check the document against this list and fix issues inline before showing it to the user:

- [ ] No placeholders (TBD, TODO, incomplete sections)
- [ ] No contradictions between sections
- [ ] Scope is focused enough for a single implementation cycle
- [ ] All requirements have a single clear interpretation
- [ ] All requirements are testable
- [ ] All questions from brainstorming are answered
- [ ] Trade-offs documented
- [ ] Risks identified

---

## Step 7 — User review and approval

Present a summary and the path, then ask:

> Please review `$FEATURE_DIR/design.md` and let me know if you approve moving to implementation planning.

Options to offer: Approve / Revise / Reject.

Do not proceed to implementation until the user explicitly approves.

---

## Step 8 — Transition

After explicit user approval, the next step is `/speckit.specify` (reads `design.md`) or `/speckit.plan` if a spec already exists.

Do not write any code. Do not create scaffolding.

---

## Scope management

If the idea spans multiple independent subsystems, stop and decompose before proceeding:

```
## Scope Alert

This appears to involve multiple independent subsystems:
1. [Subsystem 1]
2. [Subsystem 2]

Recommendation: run a separate brainstorming session for each.
Which do you want to start with?
```

---

## Design quality principles

1. **Follow existing patterns** unless there is a compelling reason to diverge
2. **Targeted improvements only** — fix problems in scope, not adjacent ones
3. **Clear interfaces** — components communicate through well-defined boundaries
4. **YAGNI** — remove unnecessary features ruthlessly
