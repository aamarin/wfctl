---
status: proposed
---

# A change with no software design records a claim

## Context

Brainstorm gains a third pass, `software-design`, between `architecture` and
`design-doc`. It holds the pipeline until the branch answers the level-3
question, which is whether the change makes a structural choice worth
recording. The pass needs two answers:

1. Yes. The branch commits a record under `docs/architecture/design/`, and the
   pass reads `done`.
2. No. The change makes no structural choice, so no record is coming, and the
   pass still has to let the branch move on.

The first answer is a file the pass can look for. The second answer leaves
nothing on disk, and `an-absent-artifact-is-claimed-not-inferred.md` already
says how wfctl handles that case: a person states the absence, and wfctl doesn't
infer it. Its main example is `python-pattern-selection`, a built-in skill that
writes a file only when it has something to say. Level 3 has the same shape.

What's left open is how the person states it. The level-2 pass already has its
own verb for this, `wfctl arch none`, so the obvious move is a matching verb for
level 3.

## Verified

- The `_builtin_only` function in `_declared.py` returns
  `{name: list(step.sub_steps) for name, step in _STEPS.items() if step.sub_steps}`,
  so the built-in passes are part of the payload every repository starts from,
  with no `wfctl.json`.
- The test
  `test_the_built_in_plan_review_can_be_claimed_away_and_a_person_still_starts_tasks`
  in `tests/test_step_none.py` claims `plan.plan-review`, a built-in pass, with
  no `wfctl.json`. This means `wfctl step none` already works on a pass wfctl
  ships, not only on passes a repository declares.
- The `_load_step` function in `_declared.py` builds `builtin` from
  `_STEPS[step].sub_steps`, and drops a declared pass with the same name. A
  repository can't declare its own `software-design` pass and collide with this
  one.
- `_design_exceptions.py` sets `_FOLDER = "exceptions"`. Since #635, every
  `wfctl step none` claim is written to `exceptions/<step>.<pass>.md` in the
  branch's spec folder, and `wfctl step none` is still the command that writes
  it.
- The `_architecture_answered` function in `_evidence.py` calls
  `touched_on_this_branch(repo_root, arch, exclude=[*non_record_subtrees(arch), arch / DESIGN_DIR])`
  and then `blocks(verdict, "repo-declared")`. The level-3 reader,
  `brainstorm_software_design`, asks the same question of `arch / DESIGN_DIR`
  alone.
- The `brainstorm_architecture` function in `_evidence.py` returns its own
  `remedy`, and `_infer_steps` in `_pipeline.py` uses an outstanding pass's
  remedy before falling back to `_design_remedy`. A new pass can print its own
  two options without changing `_design_remedy`.

## Assumed

- One answer per branch is enough. A branch that makes two structural choices
  writes two records and still reads `done`, and a branch with none writes one
  claim. A case that needs "yes for one part, no for another" breaks this.

## Direct baseline

The "no" answer is `wfctl step none brainstorm.software-design --reason "…"`.
It writes one claim to `exceptions/` in the branch's spec folder, which wfctl
reads before any pass's reader runs. The new reader, `brainstorm_software_design`,
sits in `_evidence.py` beside `brainstorm_architecture`. It reads `done` when
the branch touched `design/`, and otherwise reads `in_progress` with its own
remedy naming both answers. No new command, file kind, or folder is added.

## Decision

The baseline wins. The level-3 "no" is a step claim, made with `wfctl step
none`, and wfctl reads it the same way it reads every other claim. A claimed
pass is hidden from `wfctl status` like any other, and `--all` shows it as
`claimed: <reason>`. A branch with `spec.md` isn't held, which is the same
escape `_architecture_answered` uses.

## Diagram

```
              baseline (chosen)                    strongest alternative

stable     ┌──────────────────────┐          ┌──────────────────────┐
           │ software-design pass │          │ software-design pass │
           └───▲──────────────▲───┘          └───▲──────────────▲───┘
               │ reads        │ reads            │ reads        │ reads
               │ claims first │ design/          │ (new)        │ design/
═══ wfctl works out state from files (session-state-is-re-derived) ═══════════
               │              │                  │              │
volatile ┌─────┴──────┐ ┌─────┴─────┐  ┌─────────┴────────┐ ┌───┴───────┐
         │ spec folder│ │ design/   │  │ declarations/    │ │ design/   │
         │ exceptions/│ │ record    │  │ <branch>-design  │ │ record    │
         └─────▲──────┘ └───────────┘  │ (new)            │ └───────────┘
               │ writes                └─────────▲────────┘
         ┌─────┴──────────┐                      │ writes
         │ wfctl step none│            ┌─────────┴────────┐
         └────────────────┘            │ wfctl design none│
                                       │ (new)            │
                                       └──────────────────┘
```

The two graphs have the same pass and the same `design/` record. They differ in
how the "no" reaches the pass. The alternative adds a command, a file kind, and
a read path, which is three new parts, and the baseline adds none. Neither graph
draws a new boundary, since both sit on the line `session-state-is-re-derived`
already draws.

The change this was built to absorb is #635 moving where claims live. #635
moved them to the spec folder, and no arrow here changed, because the claim
moved with every other claim. In the alternative, the new declaration would
have had to be moved or special-cased by hand.

## Considered

- **A new verb, `wfctl design none`, mirroring `wfctl arch none`.** The previous
  handoff recommended this because it read `wfctl step none` as only for passes
  a repository declares. That reading is wrong (see Verified). We didn't choose
  this because it adds a command and a file kind to say what a claim already
  says, and #635 would have had to move it by hand.
- **Treat a missing record as "no".** It needs no command at all. We didn't
  choose this because a branch that never asked the question and a branch that
  answered "no" then look the same, which is the case
  `an-absent-artifact-is-claimed-not-inferred.md` rules out.
- **A "none" line in `design.md`.** The answer sits beside the rest of the
  design. We didn't choose this because `design.md` is gitignored and resolves
  outside the working tree, so a reviewer reading the PR never sees it. Since
  #635 the claim sits outside the working tree too. The difference is that
  `wfctl check-body` reports a claim whose reason the PR body doesn't carry,
  and nothing checks a line in `design.md`.

## Consequences

A "no" shows up in the PR body as the claim's reason, the same as a skipped
plan review, and `wfctl check-body` reports a body that leaves it out
(`design-exceptions-live-with-specs.md`). The level-3 answer and the level-2
answer now use different commands, `wfctl step none` and `wfctl arch none`. That's a cost to anyone who
learns one and expects the other. The remedy text names both answers in full to
cover it.

The skills have to say this too. `design-levels` gives the `step none` answer at
level 3, `speckit-brainstorm` names the claim where it says a branch has no
record, and `software-design-decisions` points to the claim where it says a
choice with no alternative earns no record.

## Verification

- On a branch with `design.md` and an architecture answer, `wfctl status` holds
  brainstorm on `software-design` and prints both answers under `next:`.
- Committing a file under `design/` turns the pass `done`.
- `wfctl step none brainstorm.software-design --reason "…"` hides the pass, and
  `wfctl status --all` shows it as `claimed: <reason>`.
- A branch with `spec.md` isn't held by the pass.

## Log

- 2026-10-25  proposed  — #648 level 3: how a branch says it makes no
  structural choice
- 2026-10-27  revised   — #635 moved claims from `step-claims/` to the spec
  folder's `exceptions/`, so the reviewer reads the reason in the PR body
