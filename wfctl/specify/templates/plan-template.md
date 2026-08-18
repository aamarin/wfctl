# Implementation Plan: [FEATURE]

**Branch**: `[###-feature-name]` | **Date**: [DATE] | **Spec**: [link]
**Input**: Feature specification from `/specs/[###-feature-name]/spec.md`

**Note**: This template is filled in by the `/speckit.plan` command. See `.specify/templates/commands/plan.md` for the execution workflow.

## Summary

[Extract from feature spec: primary requirement + technical approach from research]

## Technical Context

<!--
  ACTION REQUIRED: Replace the content in this section with the technical details
  for the project. The structure here is presented in advisory capacity to guide
  the iteration process.
-->

**Language/Version**: [language and version, or NEEDS CLARIFICATION]  
**Primary Dependencies**: [frameworks and libraries this feature relies on; add
feature-specific ones only when required, or NEEDS CLARIFICATION]  
**Storage**: [database, file store, or N/A]  
**Testing**: [test runner plus the integration, contract, schema, or UI
validation commands this feature needs]  
**Target Platform**: [where this runs, or NEEDS CLARIFICATION]  
**Project Type**: [single project, web application, CLI, library, or NEEDS CLARIFICATION]  
**Performance Goals**: [feature-specific measurable target or NEEDS CLARIFICATION]  
**Constraints**: [project-specific constraints for this feature] and
minimal-complexity bias  
**Scale/Scope**: [feature-specific users, domains, workflows, or NEEDS CLARIFICATION]

## Constitution Check

_GATE: Must pass before Phase 0 research. Re-check after Phase 1 design._

<!--
  ACTION REQUIRED: Add this project's gates below, derived from
  `.specify/memory/constitution.md` if it exists. If the repo has no
  constitution, substitute gates from its own documented conventions and record
  the substitution in Complexity Tracking — a gate with no source is decorative,
  and one borrowed from another project is false. Delete this comment once the
  gates are in place.

  The two gates below are project-independent. Keep them.
-->

- [ ] Validation plan exists: the project's type or build check plus the
      specific automated tests and checks needed for the changed surface are
      named.
- [ ] Complexity is justified: any added abstraction, infrastructure, or
      dependency has a measured or explicit reason the simpler path is
      insufficient.
- [ ] Ownership is stated: for every piece of state or derived value this
      feature introduces, the plan names which side computes it and why the
      other side cannot.

## Project Structure

### Documentation (this feature)

```text
specs/[###-feature]/
├── plan.md              # This file (/speckit.plan command output)
├── research.md          # Phase 0 output (/speckit.plan command)
├── data-model.md        # Phase 1 output (/speckit.plan command)
├── quickstart.md        # Phase 1 output (/speckit.plan command)
├── contracts/           # Phase 1 output (/speckit.plan command)
└── tasks.md             # Phase 2 output (/speckit.tasks command - NOT created by /speckit.plan)
```

### Source Code (repository root)

<!--
  ACTION REQUIRED: Replace the placeholder tree below with the concrete layout
  for this feature. Delete unused options and expand the chosen structure with
  real paths (e.g., apps/admin, packages/something). The delivered plan must
  not include Option labels.
-->

```text
# [REMOVE IF UNUSED] Option 1: Single project (DEFAULT)
src/
├── models/
├── services/
├── cli/
└── lib/

tests/
├── contract/
├── integration/
└── unit/

# [REMOVE IF UNUSED] Option 2: Web application (when "frontend" + "backend" detected)
backend/
├── src/
│   ├── models/
│   ├── services/
│   └── api/
└── tests/

frontend/
├── src/
│   ├── components/
│   ├── pages/
│   └── services/
└── tests/

# [REMOVE IF UNUSED] Option 3: Mobile + API (when "iOS/Android" detected)
api/
└── [same as backend above]

ios/ or android/
└── [platform-specific structure: feature modules, UI flows, platform tests]
```

**Structure Decision**: [Document the selected structure and reference the real
directories captured above]

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

| Violation                  | Why Needed         | Simpler Alternative Rejected Because |
| -------------------------- | ------------------ | ------------------------------------ |
| [e.g., 4th project]        | [current need]     | [why 3 projects insufficient]        |
| [e.g., Repository pattern] | [specific problem] | [why direct DB access insufficient]  |
