---
status: proposed
governs: design-method
---

# The code-review rubric carries the cross-layer checks

## Context

A three-reviewer code panel passed a 22-commit PFMS branch that GitHub Copilot then found three bugs in. All three had the same shape: one layer of the app accepted a value the next layer refused. The form allowed an interest rate above 100 while the server capped it at 100. A plan goal's monthly amount passed validation and then overflowed a 32-bit column, two commits after the branch had fixed the same overflow for the paycheck.

The reviewers had the right files open. What the rubric lacks is an instruction to follow each input through the layers it passes, and to check every other place a fix should also apply. The question this record settles is where those two instructions go.

`fanning-out-code-review` gives every reviewer in a group the same rubric and varies the model, not the method ("The axes are not the split"). A group names one skill, and which reviewers a group runs is decided by wfctl's review code, which #725 is changing beside this branch.

## Verified

- `wfctl/agents/skills/code-review/SKILL.md`, Step 4, lists six passes. Correctness asks for "boundary" edge cases and Security asks that input be "validated at the boundary", but no pass asks the reviewer to compare one layer's limit against the next.
- `wfctl/agents/skills/fanning-out-code-review/SKILL.md`, § *The axes are not the split*, says the rubric stays the same across reviewers and only the model varies.
- The skill's history (`git log -- wfctl/agents/skills/code-review/SKILL.md`) shows it edited in place since it was vendored in #47, so it isn't a derived skill an upstream pull would revert.
- An experiment on 2026-11-06 ran six reviewers over PFMS `7cde6095..996f5e5c` with the same brief. The three reviewers given today's rubric reported neither the rate cap nor the overflow. The reviewer given the trace procedure reported both, and so did the reviewer given the sibling-path procedure. Neither of those two was given a map of the project's layers; each found the other layers by following names and calls through the repository.

## Assumed

- That the two procedures still find these bugs when they sit beside six other passes rather than replacing them. In the experiment each procedure ran alone. Falsified by one reviewer, given the changed rubric, missing the rate cap or the overflow on the same PFMS range.
- That a reviewer can find the other layers by name and call path in any project with a form, a server, and a database. Falsified by a project whose layers share no names, where reviewers report "unknown" for most layers.

## Direct baseline

Add two passes to Step 4 of `code-review/SKILL.md`, after the six that exist. The first lists each input the change touches and follows it through every layer that checks or stores it, writing down each layer's limit and reporting any value one layer accepts and the next refuses. The second takes each fix or rule the branch's commits add and checks every other place that writes, reads, or renders the same value or sink. Step 5 asks for a short trail of both after the findings. No new skill, no new group, and no change to wfctl's review code.

## Decision

The baseline. Every reviewer in the code group runs the two new passes, because every reviewer already reads the rubric they're added to.

A value one layer accepts and the next refuses is at least a WARNING, whatever error the user sees, because the user can never save it. In the experiment the trace reviewer rated the rate cap a NIT since the server's message was clear, and the other reviewers rated it a WARNING.

The rubric stays general. An input is any value from outside the program, such as a form field, a request body, a CLI flag, a config or data file, or an environment variable, so the passes apply to a CLI as much as to a web app. A rule only one repository has stays out of the rubric, examples included.

## Diagram

The panel and the rubric are the same in both graphs. The divider is the split already in force between the skills the design method ships and the review code in Evidence and derivation that decides which reviewers each group runs.

```
              baseline (chosen)                 strongest alternative:
                                                a different method per reviewer

stable   ┌──────────────────────────┐     ┌─────────┐ ┌─────────┐ ┌─────────┐
         │ code-review rubric       │     │ rubric  │ │ trace   │ │ sibling │
         │  6 passes + 2 (new)      │     │         │ │ (new)   │ │ (new)   │
         └──────────────────────────┘     └─────────┘ └─────────┘ └─────────┘
              ▲       ▲       ▲                ▲           ▲           ▲
              │ reads │ reads │ reads          │ reads     │ reads     │ reads
              │       │       │                │           │           │
         ┌────┴┐  ┌───┴─┐  ┌──┴──┐          ┌──┴──┐     ┌──┴──┐     ┌──┴──┐
         │ c1  │  │ c2  │  │ c3  │          │ c1  │     │ c2  │     │ c3  │
         └─────┘  └─────┘  └─────┘          └─────┘     └─────┘     └─────┘
              ▲       ▲       ▲                ▲           ▲           ▲
══════════════╪═══════╪═══════╪════════════════╪═══════════╪═══════════╪═══════
   wfctl's review code decides which reviewers a group runs  (in force)
              │ starts│       │                │ starts    │ (new: one │
         ┌────┴───────┴───────┴┐          ┌────┴───────────┴─skill per─┴┐
volatile │ review group: code  │          │ review group: code          │
         │ one skill           │          │ a skill per reviewer (new)  │
         └─────────────────────┘          └─────────────────────────────┘
```

The two graphs differ by two new skill files and one new field on a review group. The change both are built to absorb is a third reading method arriving later. In the baseline that is one more pass in one file. In the alternative it is a new skill, a new reviewer slot, and an edit to the group's configuration, which crosses the divider every time.

## Considered

- **A different method per reviewer** (the right-hand graph). The inspection literature favors it: Porter, Votta, and Basili (1995) and Laitenberger (2001) found reviewers with distinct perspectives catch more than reviewers with one checklist, though Sabaliauskaite (2003) found no difference. We didn't choose it because a group can name only one skill, so it needs changes to wfctl's review code, which this branch must leave to #725. It also reverses a rule `fanning-out-code-review` states on purpose. It's worth its own issue, and this experiment can't settle it, since each procedure ran alone rather than one per reviewer on a shared panel.
- **A cross-layer review group** (option 2 in #724). It gives the check its own reviewers and its own record, but it adds a full panel round to every change, including changes with no inputs at all.
- **A project-written instruction in a per-project review file** (option 1 in #724). It's the lightest change, but every project would have to know to write it, and any app with a form, a server, and a database has these three layers. It stays the right home for limits only one project has.
- **Replacing the rubric per project** (option 3 in #724). Nothing here needs it once the checks ship by default, so whether a project can replace the rubric stays the open question #595 left.

## Consequences

Every code reviewer finds layer mismatches and missed sibling fixes without any project setup, and the panel's size and rounds are unchanged.

Each review gets longer. A branch that touches many inputs produces a long trail, and every reviewer on the panel writes the same one. That duplication is the cost of keeping one rubric.

The failure mode is a reviewer that skims the two passes the way the six existing ones can be skimmed, reporting "consistent" for a layer it never opened. The trail makes that visible, since each input has to name its limit at every layer, and an "unknown" has to say why.

## Verification

- One reviewer given the changed rubric and the saved brief, run over PFMS `7cde6095..996f5e5c`, reports the rate-cap mismatch and the plan goal overflow, each at WARNING or above.
- The same reviewer's report carries the input trail and the list of fixes with the places checked.
- A review of a change with no user inputs, such as a docs-only change, says so in one line rather than producing an empty trail.

## Log

- 2026-11-06  proposed  — written at #724's level-3 gate, after the experiment and after Andre chose passes in the shared rubric over a method per reviewer.
