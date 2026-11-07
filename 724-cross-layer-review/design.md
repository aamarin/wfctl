# Reviewers check that each layer accepts the same input

Contexts: design-method

## Problem Statement

How might every code reviewer find a value that one layer of an app accepts and the next layer refuses, and a fix that one path got and its sibling paths didn't, without each project having to ask for it?

## Recommended Direction

The `code-review` rubric gets two new passes after the six it has today, and every reviewer in the code group runs them, because every reviewer already reads that rubric. Nothing about the panel changes: the same groups, the same three code reviewers, and the same rounds.

The first pass is the input trace. The reviewer lists each user input the change adds or changes, follows it from the form through client validation, the request, server validation, any conversion, and storage, and writes down each layer's limit. A finding is a value one layer accepts and the next refuses, reported with a counterexample value and the file and line on both sides. For example, a signup form lets a username be 40 characters, but the server schema caps it at 32, so a name the user can type always fails to save.

The second pass is the sibling-path check. The reviewer takes each rule or fix the branch's commits add and searches for every other place that writes the same value or sink, including unchanged code, and checks whether each one enforces the rule. For example, one commit escapes HTML in the comment form's preview, so the reviewer looks for every other place that renders the same comment text.

The report gets a short trail after the findings: each input with its limit at each layer, and each rule with the places checked. A layer the reviewer couldn't inspect is written as "unknown" with the reason. A change with no user inputs says so in one line.

A value one layer accepts and the next refuses is at least a WARNING, whatever error the user sees, because the user can never save it.

## Boundaries and Ownership

wfctl owns the rubric, as it does today, and this change moves no ownership. The level-2 answer for `design-method` is recorded with `wfctl arch none`:

> wfctl already owns the code-review rubric, and this change adds two passes to it. No ownership moves: which reviewers a group runs stays in wfctl's review code, and project-specific limits wait for the per-project review file in #625.

The checklist stays general. A rule only one repository has belongs to that repository, and wfctl's checklist carries neither the rule nor an example of it.

## Software design decisions

- docs/architecture/design/724-cross-layer-checks-in-rubric.md — the code-review rubric carries the cross-layer checks as two passes every code reviewer runs, rather than a group of their own or a different method per reviewer

## Key Assumptions to Validate

- [ ] The two procedures still find the bugs when they sit beside six other passes. In the experiment each ran alone. Test: one reviewer with the changed rubric and the saved brief, over PFMS `7cde6095..996f5e5c`, reports the rate-cap mismatch and the plan goal overflow at WARNING or above.
- [ ] A reviewer finds the other layers by following names and calls, with no project map. The experiment's trace and sibling reviewers did. The same run above confirms it again.
- [ ] The trail stays readable on a large branch. Test: the PFMS run's trail fits under the findings without crowding them out. If it doesn't, consistent inputs collapse to one line each.

## MVP Scope

In:

1. Two new passes in Step 4 of `wfctl/agents/skills/code-review/SKILL.md`, with the neutral examples above.
2. Step 5 asks for the trail and states the WARNING floor.
3. The pass count updates wherever it's stated: the skill's own description, `wfctl/agents/commands/code-review.md`, `requesting-code-review` ("six-pass rubric"), and `fanning-out-code-review` where it counts the passes.
4. A release note, `changes/724.change.md`, since every code review now asks more of the reviewer.
5. The verification run over PFMS described above.

Out: everything in the list below.

## Not Doing (and Why)

- A different method per reviewer — the inspection literature favors it, but a group names one skill, so it needs changes to wfctl's review code that #725 is making beside this branch. It's worth its own issue.
- A cross-layer review group — it adds a full panel round to every change, including changes with no inputs.
- Project-specific limits in the rubric — they belong in the per-project review file from #625.
- Letting a project replace the rubric — nothing here needs it once the checks ship by default, so it stays the open question #595 left.
- Changes to `_review*.py` — out of this branch's scope, per #725.

## Open Questions

None. The PFMS name-length bug the trace reviewer found (`VARCHAR(191)` against a 255-character schema limit) belongs to PFMS and goes to the user to file there.
