# Source map

This skill is an original synthesis of two books. It reproduces no sample
program, example or diagram from either.

- Eric Evans, *Domain-Driven Design: Tackling Complexity in the Heart of
  Software* (Addison-Wesley / Pearson, 2003).
- Vaughn Vernon, *Domain-Driven Design Distilled* (Addison-Wesley / Pearson,
  2016).

Naming the books is a citation, not a derivation, and it owes no row in
`NOTICES.md`. `vendor-upstream-skills` says so for this skill by name.

**The chapters are the key here and nowhere else.** Every other file is named
for what an agent is doing at that moment. This one is for a maintainer checking
whether a chapter was covered or left out on purpose.

## Evans

| Chapter | Where | Adaptation |
| --- | --- | --- |
| 1 Crunching Knowledge | `process.md` §2 | The crunching cycle, kept as ten steps. |
| 2 Communication and the Use of Language | `SKILL.md` step 4, `visual-language.md` | Ubiquitous Language kept. Diagrams: "selective and simplified" is wfctl's own rule already, so the per-round visual mandate the draft carried was dropped. |
| 3 Binding Model and Implementation | `ddd-heuristics.md` *Knowledge and language*, `process.md` §5 | Model-Driven Design and Hands-On Modelers stated as principles, not as pattern names. |
| 4 Isolating the Domain | `ddd-heuristics.md` rules | One line. Drawing the layer boundary is `architecture-design`'s. |
| 5 A Model Expressed in Software | `ddd-heuristics.md` *Tactical building blocks* | Entity, Value Object, Service, Module, associations. |
| 6 The Life Cycle of a Domain Object | `ddd-heuristics.md`, `process.md` §4 | Aggregate, Factory, Repository. |
| 7 Using the Language: An Extended Example | not reproduced | A worked example, not a technique. |
| 8 Breakthrough | `process.md` §2 | Press on an awkward spot rather than smoothing it. |
| 9 Making Implicit Concepts Explicit | `process.md` §2, `ddd-heuristics.md` | Specification as a building block; implicit constraints and processes named. |
| 10 Supple Design | `.agents/skills/clean-code` | Out of scope here — how code expresses a settled model is levels 3 and 4. |
| 11 Applying Analysis Patterns | not carried | A known model is one of the evidence sources in `SKILL.md` step 2; no catalog. |
| 12 Relating Design Patterns to the Model | not carried | `python-pattern-selection` and `software-design-decisions` own pattern choice. |
| 13 Refactoring Toward Deeper Insight | `SKILL.md` step 8, `evidence.md` *What reopens a model* | |
| 14 Maintaining Model Integrity | `process.md` §3, `ddd-heuristics.md`, `visual-language.md` | Bounded Context, Context Map, the seven relationships Evans names; Continuous Integration as keeping one context coherent. |
| 15 Distillation | `process.md` §6 | Core Domain, generic subdomain, domain vision statement. Segregated and Abstract Core are whole-codebase moves and are left out. |
| 16 Large-Scale Structure | not carried | Whole-system organization, above one feature's round. |
| 17 Bringing the Strategy Together | `SKILL.md` | The skill's own ordering plays this role. |

## Vernon

| Chapter | Where | Adaptation |
| --- | --- | --- |
| 1 DDD for Me | `SKILL.md` *Select the depth* | |
| 2 Bounded Contexts and Ubiquitous Language | `process.md` §2–3 | |
| 3 Subdomains | `process.md` §3, `ddd-heuristics.md` | Problem space against solution space. |
| 4 Context Mapping | `ddd-heuristics.md` | Partnership and Big Ball of Mud added to Evans' seven. Transport named abstractly (synchronous, asynchronous, batch, manual) rather than as RPC, REST or messaging. |
| 5 Aggregates | `process.md` §4 | The four rules of thumb. |
| 6 Domain Events | `ddd-heuristics.md` | Past-tense facts. Event Sourcing is a persistence technique and is left out. |
| 7 Acceleration and Management Tools | `ddd-heuristics.md` *Cautions* | Event-first discovery kept. Estimation, timeboxing and SWOT are process and are left out. |

## Departures from the draft

The draft this skill was adapted from carried four things wfctl already owns,
and each was dropped rather than kept beside the owner:

- eight pass/fail promotion gates — `design-levels` owns every gate, and #100
  decides a gate's shape;
- `not applicable - <reason>` as prose — `wfctl arch none`;
- a visual on every round — `the-drawing-is-required-at-acceptance`;
- paired human and agent views with a stable ID scheme — #86's
  dual-representation principle.
