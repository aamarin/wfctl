---
name: plan-walkthrough
description: Walk the plan owner through their own plan or change, one question at a time, to find out privately whether they can explain it. Use when the person runs /plan-walkthrough, or asks to be walked through, quizzed on, or challenged about a plan or a finished change they are about to put their name on. The answers stay on the person's machine; the feature directory gets only a short marker. Never runs while auto-approve is on.
---

# Plan Walkthrough

Act as a senior engineer walking the plan owner through their own work. The job
is to find out whether they hold the mental model behind it, not whether the
artifacts look plausible or the tests pass.

The goal is not many questions. It is the few consequential assumptions, weak
reasons, unowned failure modes, and gaps between intent and implementation that
the person cannot yet explain.

This check tests the person. Whether the plan itself holds together is a
different check, the plan review. Do not turn this interview into that one.

## Load these references

- Read `references/interrogation-lenses.md` to choose what to ask.
- Read `references/question-quality.md` before the first question.
- Read `references/artifact-contract.md` before writing anything.
- Read `references/examples.md` when a concrete pattern would help.
- Read `references/source-map.md` only when provenance matters.

## 1. Refuse while auto-approve is on

Run this before anything else:

```bash
wfctl status --json
```

Read the top-level `auto_approve` key. If it is `true`, print exactly this,
write nothing, and stop:

```
Plan walkthrough needs a person at the prompt, and auto-approve is on.
Run `wfctl start --no-auto-approve`, then `/plan-walkthrough` again.
An unattended run skips this pass only when its declaration in
wfctl.json carries "needs_person": true.
```

Refuse whoever started the skill. You cannot tell a person who typed the
command from an autonomous agent that ran it, and a wrong guess means you
answer your own questions, which produces invalid evidence. A pass declared
with `needs_person` is skipped by wfctl before an autonomous agent ever reaches
this skill, so reaching this line with auto-approve on means either a person
typed the command or the declaration lacks the flag. The last line of the
refusal covers the second case.

## 2. Choose the mode

There are two modes:

- **Plan walkthrough** (`plan`): the plan exists and tasks have not become the
  committed path. Ask about the plan.
- **Change walkthrough** (`change`): code exists. Ask whether the code does what
  the plan intended, and whether the person understands what it now does.

Resolve the mode in this order, and say which one you picked before the first
question:

1. The argument, when the person typed `/plan-walkthrough plan` or
   `/plan-walkthrough change`.
2. The current pass in the `wfctl status --json` payload from step 1: the
   sub-step with `"is_current": true` whose `command` is `/plan-walkthrough`.
   Change mode when it sits under `implement`, plan mode under any other step.
3. Plan mode.

## 3. Find the two destinations

```bash
wfctl feature-paths    # read FEATURE_DIR from the output
wfctl state-dir        # the branch's state directory
```

Read both values out of the output and use the literal paths. The answers go
under the state directory and the marker goes in `FEATURE_DIR`, as
`references/artifact-contract.md` describes. Nothing else is written.

In plan mode, if `FEATURE_DIR/plan.md` does not exist, say there is no plan to
walk through and stop, without writing an answers file or a marker.

## 4. Establish the evidence base

Read what already defines the work: the spec, the plan, the architecture records
(`wfctl arch context` for the accepted ones), the design notes, the tasks, and in
change mode the diff against the branch's base and the tests.

Extract the consequential decisions already present. Do not ask the person to
restate what the artifacts answer clearly.

For each important claim, tell apart:

- **verified**: supported by repository evidence, an accepted decision, a test,
  a schema, an interface, or another concrete source;
- **asserted**: stated but not yet supported;
- **assumed**: required for the approach to work but not established;
- **unknown**: explicitly unresolved.

## 5. Build a private question queue

Rank candidate questions by the combination of:

- behavioral or business impact;
- uncertainty;
- effects across a boundary;
- failure or recovery risk;
- state or ownership implications;
- cost of changing the decision later.

Do not show a score or a confidence number. The ranking only decides what to ask
next.

## 6. Ask one material question

Ask exactly one primary question per turn. Tie it to a concrete decision, claim,
interface, state transition, or changed behavior. Prefer a question that needs an
operational explanation over one that can be answered with vocabulary.

Weak:

> Have you considered retries?

Better:

> The plan retries this write after a timeout. What makes replay safe, and where
> is that property enforced?

Stop after the question. Wait for the person's answer before continuing.

## 7. Push vague answers toward ownership

Judge each answer as one of:

- **grounded**: explains the mechanism and points to evidence;
- **partial**: addresses the question but leaves a material gap;
- **asserted**: says "should", "normally", "probably", or names a pattern without
  showing why it applies;
- **contradicted**: conflicts with the evidence base;
- **unknown**: admits the answer is not established.

For a partial or asserted answer, ask one focused follow-up. Push at most twice
on the same issue, then record it as a gap.

Never write an answer for the person, and never answer a question yourself. The
point is to find out whether the reasoning is theirs.

## 8. Require failure reasoning

For any material dependency, state transition, persistence boundary,
asynchronous action, or external call, ask the person to walk through at least
one path that is not the happy one. Useful probes:

- What happens if this times out after the remote side succeeded?
- What state exists after partial success?
- What makes a retry safe or unsafe?
- What notices and repairs stale state?
- What would you inspect first if this failed in production?
- Which invariant prevents the bad state rather than detecting it later?

Do not accept "we have tests" in place of the behavior the tests are meant to
prove.

## 9. Record each challenge in the answers file

Follow `references/artifact-contract.md`. For every material challenge, record
the claim, the question, why it matters, the person's answer, the evidence, the
disposition, and what it means for the work. Use only these dispositions:
`SETTLED`, `REVISION_REQUIRED`, `DEFERRED`, `UNRESOLVED`.

Write the answers file as you go, not only at the end, so a walkthrough the
person stops partway keeps what was answered. If they stop, mark the file
`Status: incomplete` and write no marker.

## 10. Finish with an outcome, not a score

When the interview reaches its outcome, tell the person:

- what they explained well;
- what needs revising, stated as a gap in the plan or the code, never as a gap in
  the person;
- what is deferred, and what reopens it;
- what is still unresolved.

Do not say the plan is "90% ready" or "high confidence". Say what is established
and what is open.

Then write the marker, and print the outcome counts and the answers file's path
so the person knows where their private record is. In change mode, if
`git status` shows uncommitted changes, add one line saying the marker names the
last commit and does not cover the uncommitted changes.

A gap belongs in the plan only if the person puts it there. They may add it
themselves, worded as a gap in the plan, such as "the plan does not say what
step 3 does to `plan.md`". This skill never edits the plan.

## Where the check sits in a workflow

wfctl places this check nowhere by default. A repository that wants it after
`plan` or after `implement` declares it in `wfctl.json`; the "Declaring your own
passes" section of wfctl's `docs/reference.md` shows how. Nothing here holds
`tasks`, sends the plan back, or blocks a merge. The result is the person's own.

## Rules for the interview

- Challenge the strongest reasonable reading of the work, not a strawman.
- Skip a question that reliable evidence already answers.
- Prefer a concrete scenario over a generic checklist.
- Ask for mechanisms and ownership, not buzzwords.
- Keep intent apart from literal implementation details.
- Keep evidence apart from assertion, the model's and the person's alike.
- Treat accepted architecture records and repository invariants as settled.
  Ask the person to explain them, not to reopen them.
- Never edit the plan, the code, or the architecture records during the
  walkthrough.
- Do not turn the interview into trivia about syntax or framework APIs unless
  that knowledge is material to the decision.
- Do not ask every lens every time. Ask only what can change a decision, expose
  a hidden assumption, or show a gap in the mental model.
