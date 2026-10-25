---
status: proposed
diagram: data-flow
---

# A branch's "doesn't apply" answers live in its spec folder and its PR body

## Context

The architecture folder describes the system: the accepted records, the domain
model, and who owns what. Two commands also write a branch's "doesn't apply"
answers into it:

1. `wfctl arch none --reason "…"` writes `declarations/<branch>.md`, saying the
   branch drew no new boundary.
2. `wfctl step none <step>.<pass> --reason "…"` writes
   `step-claims/<branch>/<step>.<pass>.md`, saying a pass the repo declared
   doesn't apply to the branch.

On 2026-10-25 the folder held 15 declarations and 5 step claims, all from
branches that had already merged. Each one describes a single change, not the
system. As a result, the folder gains a file for every branch that answers "no",
and a reader looking for the system's architecture has to skip past them.

These answers went into the architecture folder so the reviewer would see them
(`an-absent-artifact-is-claimed-not-inferred.md`). The folder is committed, so a
file written there is part of the change under review. That record rejected the
spec folder for the same reason. The spec folder is gitignored, and in this repo
it sits outside the working tree, so nothing written there reaches a reviewer.

Two things have changed since then:

1. A repo can list headings every PR body has to answer under `change_sections`
   in `wfctl.json`. `wfctl check-body` fails a body that leaves one empty,
   writes N/A, or answers yes or no with no reason.
2. The fast path already answers "Needs a spec?" this way, with no file at all
   (`every-change-answers-spec-question.md`).

The brainstorm gate is the one reader that can't wait for a PR. It runs before
any PR exists, and it stays blocked until the boundary question is answered.

## Direct baseline

Keep both kinds of answer where they are. The gate and the pipeline read them
from the architecture folder, and the reviewer reads them in the diff.

This keeps every guarantee in place and adds no new structure. It also keeps
adding a file to the architecture folder for every branch that answers "no".

## Decision

A branch's "doesn't apply" answers, for the boundary and for each pass, live in
that branch's spec folder. The gate and the pipeline read them there.

The reviewer reads them in the PR body, under a "Moves a boundary?" section.
Every PR answers it yes or no with a reason, the same way it answers "Needs a
spec?", and lists any pass answers under it. The repo makes the section required
by listing it under `change_sections`. wfctl doesn't name the heading itself.

## Owns truth

The person on the branch still decides whether a boundary moved or a pass
applies, and writes that answer as a sentence. This record changes only where
the sentence is kept and where each reader finds it.

The spec folder holds the copy the pipeline reads. The PR body can't serve the
gate, because the gate runs before any PR exists. The spec folder already holds
the other files the pipeline reads about one branch, such as `design.md` and
`plan.md`, and it is stored on `specs-trunk` with them.

The PR body holds the copy the reviewer reads. The spec folder can't serve the
reviewer, because it is gitignored and, in this repo, outside the working tree.
The PR body also keeps the answer after the branch is deleted.

The architecture folder holds neither copy. An answer about one branch isn't a
fact about the system, and the folder should change only when the architecture
does (`knowledge-placement.md`).

## Boundary

```mermaid
flowchart LR
  subgraph person["Person or agent on the branch"]
    none["arch none / step none"]
    body["writes the PR body"]
  end
  subgraph spec["Spec folder (gitignored)"]
    file["answer file"]
  end
  subgraph wfctl["wfctl"]
    gate["brainstorm gate and pipeline"]
    blocked["gate stays blocked"]
    check["check-body"]
  end
  subgraph pr["PR"]
    section["Moves a boundary? section"]
  end
  subgraph arch["Architecture folder"]
    records["records"]
  end
  none --> file
  file -.-> gate
  gate -- "no answer file yet" --> blocked
  body --> section
  section -.-> check
  none -- "an answer about one branch" --x records
```

A solid edge is a write or a result. A dotted edge is a file or a PR body read
later. The crossed edge is the write this record removes.

## Considered

- Keep the answers in the architecture folder. This is the direct baseline.
  We didn't choose it because it is the problem this record fixes.
- A `Boundary: none` trailer on a commit, which the gate reads from `git log`.
  This adds no file and keeps the answer in history. We didn't choose it
  because each answer would cost an empty commit, a rebase or squash can drop
  the trailer, and `628-early-answer-in-commit-trailer.md` already rejected a
  trailer for the early spec answer.
- A committed folder outside the architecture folder, such as `.wfctl/claims/`.
  This keeps the reviewer's copy in the diff. We didn't choose it because the
  repo still gains a file for every branch that answers "no", just in a
  different folder, and a new file for every one-line fix was already ruled out
  for the spec answer.
- The gate stops requiring an explicit "no" and checks only that `design.md`
  exists. We didn't choose it because the pipeline would no longer make the
  agent answer the boundary question before specify.
- wfctl requires "Moves a boundary?" whenever a branch has an answer file,
  whatever `change_sections` lists. We didn't choose it because it would be the
  first heading wfctl names itself, and a repo whose template lacks the heading
  would fail every PR until it added one (`wfctl/_sections.py` explains why
  wfctl holds no section name).

## Consequences

The reviewer is less certain to see a "no". Previously, the gate enforced it,
since an answer outside the change under review didn't count. Currently,
`check-body` enforces it, and only in a repo that lists "Moves a boundary?". The
opening-a-change skill runs `check-body`; CI and the worktree guard don't. A repo
that doesn't list the heading loses the reviewer's copy. That's acceptable while
wfctl has one user, and it should be revisited before it has a second.

`declarations/` joins the subtrees the gate ignores. Otherwise a declaration
written by an older wfctl would count as a record and satisfy the gate. The
architecture folder would start filling up again, and nothing would flag it.

The existing 15 declarations and 5 step claims are deleted. Git history and
each merged PR keep their sentences.

#382's short track reads the same answer file in the spec folder. That issue's
plan asks for a committed `arch none` file, so it needs the new location.

## Log

- 2026-10-25  proposed    — #635's level-2 pass; the architecture folder should
  change only when the architecture does
