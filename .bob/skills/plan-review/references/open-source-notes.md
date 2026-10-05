# Where this method came from

This skill is a clean-room synthesis of patterns observed in several open-source
spec-driven development (SDD) projects, and of the governance model of the
workflow it was first written for. It vendors none of their implementation code.

## GitHub Spec Kit: kept and extended

Repository: `github/spec-kit`

Spec Kit already splits its later stages usefully:

- planning produces the technical strategy
- a checklist can test the quality of the requirements
- tasks break the planning artifacts down into implementation work
- analyze runs a read-only consistency and coverage review after tasks exist

Adopted: review responsibilities stay separated by lifecycle stage, rather than
one large reviewer replacing the existing analysis.

This skill fills the earlier gap in that split. It reviews the specification,
the plan, and the durable design context before tasks exist.

Licence observed during design: MIT.

## Foundry: the strongest current plan-review reference

Repositories:

- `foundry-works/foundry-mcp`
- `foundry-works/claude-foundry`

Foundry is the active successor the archived `tylerburleigh/claude-sdd-toolkit`
names. It has current plan-review prompts and workflows, support for review by
several models, structured review artifacts, iterative review, and an explicit
human approval stage in its workflow.

Adopted:

- structured, categorized review output
- independent reviewer perspectives, when they are available
- review early, before anything downstream is formalized or implemented
- review artifacts stored apart from the plan
- feedback and approval treated as distinct concepts

Adapted rather than copied:

- Foundry's plan representation and lifecycle are not the artifacts this skill
  reviews.
- A workflow should not take on a Model Context Protocol (MCP) server or another
  runtime dependency only to obtain the review method.
- This skill does not self-edit the plan or self-iterate until the findings
  disappear, because review is kept apart from mutation, and evidence apart from
  certification.
- This skill does not use model-generated time estimates as governance
  evidence.

`foundry-mcp` licence observed during design: MIT.

## claude-sdd-toolkit: a historical source, not a vendoring target

Repository: `tylerburleigh/claude-sdd-toolkit`

The repository holds the original `sdd-plan-review` skill and a Python
implementation with parallel reviewers run through AI command-line tools,
synthesis, Markdown and JSON reporting, and full, quick, security, and
feasibility review modes.

It is no longer maintained, and its README sends users to Foundry. It is
provenance, not a dependency.

Adopted:

- a reviewer that only advises
- categorized findings
- specialized review modes, as an option
- a synthesis that keeps which reviewer said what

Not vendored:

- the upstream is inactive
- its toolchain assumptions are tied to that toolkit
- it couples a runtime dependency to a workflow a skill can express

## sdd-superpowers: verification discipline

Repository: `hllj/sdd-superpowers`

Its `sdd-review` skill separates a check of the specification's completeness
before planning from a check of the implementation's alignment with the
specification afterwards, and it asks for verification evidence before anyone
claims completion.

Adopted: a checked box or a reviewer's assertion is not proof, and a finding
cites evidence someone else can observe.

Not vendored, because its review stages do not match the seam between planning
and task breakdown that this skill reviews.

Licence observed during design: MIT.

## specfact-cli: an evidence and governance reference

Repository: `nold-ai/specfact-cli`

Useful pattern: durable planning and validation evidence, the identity of each
source, and independent proof boundaries.

Adopted: a review is bound to the exact inputs it examined, and evidence is kept
distinct from authority.

Not vendored, because the workflow around this skill already owns its
control-plane semantics and needed only the review method.

Licence observed during design: Apache-2.0.

## Deliberate departures from the research this method was built from

### The review sits before tasks

The strategy is reviewed after the plan exists and before it is broken into
tasks. The cross-artifact consistency and coverage analysis stays after tasks,
where it already runs.

### Agreement between reviewers is not a blocking threshold

"Two reviewers said it" does not make a claim true, and one reviewer can find
an objective contradiction. The report keeps who said what, and the evidence
decides a finding's impact.

### EARS syntax is not required

The Easy Approach to Requirements Syntax (EARS) is useful for diagnosing
ambiguity in a trigger, a state, or a response. Requiring every existing
requirement to be rewritten into EARS would turn a review skill into a
requirements migration.

### The reviewer does not certify progression

The reviewer says what it found. It does not edit the plan, clear its own
BLOCKER findings, or declare the work approved. An agent may produce evidence,
and it does not certify that evidence itself.
