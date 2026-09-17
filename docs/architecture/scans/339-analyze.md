# Analyze scan — #339 declare pipeline step

## Session 2026-09-17

- Verdict: satisfied
- Scanned: spec.md, plan.md, tasks.md — all three present and read
- Findings: 9 · Critical: 0 · Acted on: 4 · Accepted: 5
- Detail: /Users/andremarin/Development/wfctl-specs/339-declare-pipeline-step/checklists/analysis-report.md

There is no `.specify/memory/constitution.md` in this repo. Pass D ran against
the substitution `plan.md` § Constitution Check records: `AGENTS.md` and the
records `wfctl arch context` prints. Every one of D's findings is against a
`proposed` record, which is why none of them is CRITICAL — the twelve accepted
records are honoured.

### Coverage

| Pass | Status |
| --- | --- |
| A · Duplication | Clear |
| B · Ambiguity | Clear (no placeholder, no unmeasured adjective) |
| C · Underspecification | Resolved (1 MEDIUM, tasks fixed) |
| D · Constitution alignment | Outstanding (3 HIGH) |
| E · Coverage gaps | Resolved (1 HIGH, 2 MEDIUM; tasks added) |
| F · Inconsistency | Outstanding (1 HIGH, 1 MEDIUM) |
| G · Design-record contradiction | Clear (design.md records none) |
| Requirement-to-task coverage | 100% |

Pass G reached its answer rather than being deferred: `design.md` carries a
`## Software design decisions` section, and that section lists no entries. It
explains in prose why — every structural choice here was about who owns a piece
of truth, so each landed in a level-2 record instead. The two records its prose
names are level-2 and were read under pass D, where D1, D2 and D3 are.

### Findings

- **D · Constitution alignment (record), HIGH** — `an-absent-artifact-is-claimed-not-inferred`'s
  Decision and Consequences are reversed in three places: the claim's location
  (declarations directory vs `step-claims/<branch>/<step>.<name>.md`), whether
  `step none` generalises `wfctl arch none` or sits beside it, and whether a pass
  has three reachable states or the four FR-005 requires.
  → Accepted: out of scope — every fix is to a file outside the three artifacts,
    and the record is `proposed`, which only a human moves
    (`a-human-accepts-a-decision`). Filed as #408.

- **D · Constitution alignment (record), HIGH** — `a-step-carries-sub-steps-one-level-deep`'s
  Consequences says `doctor` gains the finding for a declared pass whose command
  is not installed. `spec.md` Q2 put it in `wfctl check config` and said
  explicitly "not in the drift report"; `plan.md` says `doctor` is not touched.
  → Accepted: same reason. Filed as #408.

- **D · Constitution alignment (record), HIGH** — `brainstorm-is-one-step-with-addressable-levels`'s
  Decision says `_STEPS` "gains no second axis" and that `design-levels` owns
  which gates run inside `brainstorm`. T004 adds `sub_steps` to `Step` and T034
  puts `architecture` — level 2 — into `_STEPS["brainstorm"]` with a continuation
  of its own. `plan.md`'s Constitution Check does not list this record at all.
  → Accepted: same reason. Filed as #408.

- **F · Inconsistency, HIGH** — a claim that cannot reach a reviewer has two
  opposite specifications. `data-model.md`: "Refused, and the pipeline does not
  advance". `contracts/cli.md`: `⚠ Wrote <path>, but it is not part of the change
  under review …`, exit 1. Because T047 reads claims off disk, the written claim
  makes the pass `skipped` and the pipeline advances — FR-014 and US3 acceptance
  5 inverted. `arch none` escapes this only because its gate reads git rather
  than the file.
  → Accepted: out of scope — choosing between the two readings is a decision the
    artifacts have not made, and it lands in `data-model.md` and
    `contracts/cli.md`, outside the three. Filed as #409 with both candidates and
    what each costs.

- **F · Inconsistency, MEDIUM** — two vocabularies for one thing. The records and
  the code say *sub-step* (`SubStep`, `sub_steps`, both record titles); the spec,
  plan, tasks and every user-facing string say *pass*. The record keeps them as
  distinct terms — "how you do a sub-step, not a sub-step" — and `spec.md`
  collapses that. `wfctl-counts-the-passes` already uses "pass" for one iteration
  of the orchestrate loop, a third sense in the same arch root.
  → Accepted: out of scope — picking the word is a decision, and the fix reaches
    the records. Filed as #408.

- **E · Coverage gap, HIGH** — FR-021b had zero tasks. `auto_approve` is a notice
  today and never reaches `next_step_content`, whose own comment states the two
  are deliberately separate axes, so a granted run would halt at every declared
  pass — and FR-021 makes `review_required` the default for exactly those.
  → Fixed: T012a applies the grant to a pass's continuation in `_pipeline`;
    T022a tests that a granted run does not stop. Decided against filing it: a
    requirement with zero tasks is the coverage gap this step sits before
    `implement` to catch, and `spec.md` already decided the behaviour — adding the
    task decides nothing.

- **C · Underspecification, MEDIUM** — `data-model.md`'s state table gives `done`
  when the predicate is satisfied and `skipped` when a claim exists, with no
  precedence stated. Read top-down it gives `done`, the opposite of `spec.md`'s
  edge case 7: "a pass is declared away, and a later commit produces its artifact
  anyway: the claim stands". Nothing tested it.
  → Fixed: T047 amended to read the claim ahead of the pass's own predicate, and
    T043a added. Decided against changing `data-model.md`'s table: it is outside
    the three artifacts, and `tasks.md` is where the ordering becomes code.

- **E · Coverage gap, MEDIUM** — `quickstart.md` names "a bare name is not
  resolved against the current step" as a test to add and calls it the failure the
  references note argues is silent. T038 covers only the rows of `contracts/cli.md`
  § `wfctl step none`, and that case is not one of them.
  → Fixed: T038a, written as the sharp case — a bare name carried by a pass under
    the current step is still refused when a second pass elsewhere carries it.

- **E · Coverage gap, MEDIUM** — FR-008 exists so a pass whose evidence is a
  heading inside another step's artifact can report correctly, and edge case 5
  requires it. Both built-in passes read whole files and `evidence` builds a
  file-exists predicate, so nothing in the delivered set exercises the capability
  — a regression to a path-only pass would fail no test. This is the exact
  amendment commit d6a9f21 made to the record, left unguarded.
  → Fixed: T017a. Decided against adding a third built-in pass to carry it: that
    would be a design decision, and a test over the predicate type is what guards
    the capability.

### Filing

- **The #339-adjacent architecture records disagree with the spec and plan they
  produced** — D1, D2, D3 and F2. Filed as #408.
- **A claim that cannot reach a reviewer still advances the pipeline** — F1.
  Filed as #409.

### Deferred

- Nothing. Every pass reached an answer, and every finding was fixed or filed.
