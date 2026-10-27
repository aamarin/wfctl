---
status: proposed
diagram: data-flow
---

# The spec folder and PR body hold design exceptions

## Context

The architecture folder describes the system: the accepted records, the domain
model, and who owns what. Two commands also write design exceptions into it. A
design exception is a branch's statement, with a reason, that a design step
doesn't apply to it:

1. `wfctl arch none --reason "…"` writes `declarations/<branch>.md`, saying the
   branch drew no new boundary.
2. `wfctl step none <step>.<pass> --reason "…"` writes
   `step-claims/<branch>/<step>.<pass>.md`, saying a pass the repo declared
   doesn't apply to the branch.

On 2026-10-25 the folder held 15 declarations and 5 step claims, all from
branches that had already merged. Each one describes a single change, not the
system. As a result, the folder gains a file for every branch that claims an
exception, and a reader looking for the system's architecture has to skip past
them.

Design exceptions went into the architecture folder so the reviewer would see
them (`an-absent-artifact-is-claimed-not-inferred.md`). The folder is committed,
so a file written there is part of the change under review. That record rejected
the spec folder for the same reason. The spec folder is gitignored, and in this
repo it sits outside the working tree, so nothing written there reaches a
reviewer.

Two things have changed since then:

1. A repo can list headings every PR body has to answer under `change_sections`
   in `wfctl.json`. `wfctl check-body` fails a body that leaves one empty,
   writes N/A, or answers yes or no with no reason.
2. The fast path already answers "Needs a spec?" this way, with no file at all
   (`every-change-answers-spec-question.md`).

The brainstorm gate is the one reader that can't wait for a PR. It runs before
any PR exists, and it stays blocked until the boundary question is answered.

## Direct baseline

Keep design exceptions in the architecture folder. The gate and the pipeline
read them there, and the reviewer reads them in the diff.

This keeps every guarantee in place and adds no new structure. It also keeps
adding a file to the architecture folder for every branch that claims an
exception.

## Decision

The spec folder holds each branch's design exceptions, for the boundary and for
each pass. The gate and the pipeline read them there.

The PR body carries the same design exceptions to the reviewer, under a "Moves a
boundary?" section. Every PR answers it yes or no with a reason, the same way it
answers "Needs a spec?", and lists any pass exceptions under it. The repo makes
the section required by listing it under `change_sections`. wfctl doesn't name
the heading itself.

## Owns truth

The person on the branch still decides whether a boundary moved or a pass
applies, and writes the reason. This record changes only where the design
exception is kept and where each reader finds it.

The pipeline reads its copy from the spec folder. It can't read the PR body,
because the gate runs before any PR exists. The spec folder already holds the
other files the pipeline reads about one branch, such as `design.md` and
`plan.md`, and it is stored on `specs-trunk` with them.

The reviewer reads their copy in the PR body. They can't read the spec folder,
because it is gitignored and, in this repo, outside the working tree. The PR
body also keeps the design exception after the branch is deleted.

The architecture folder holds neither copy. A design exception describes one
branch, not the system, and the folder should change only when the architecture
does (`knowledge-placement.md`).

## Boundary

```mermaid
flowchart LR
  subgraph person["Person or agent on the branch"]
    none["arch none / step none"]
    body["writes the PR body"]
  end
  subgraph spec["Spec folder (gitignored)"]
    file["design exception file"]
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
  gate -- "no design exception file yet" --> blocked
  body --> section
  section -.-> check
  none -- "a design exception for one branch" --x records
```

A solid edge is a write or a result. A dotted edge is a file or a PR body read
later. The crossed edge is the write this record removes.

## Considered

- Keep design exceptions in the architecture folder. This is the direct
  baseline. We didn't choose it because it is the problem this record fixes.
- A `Boundary: none` trailer on a commit, which the gate reads from `git log`.
  This adds no file and keeps the design exception in history. We didn't choose
  it because each design exception would cost an empty commit, a rebase or
  squash can drop the trailer, and `628-early-answer-in-commit-trailer.md`
  already rejected a trailer for the early spec answer.
- A committed folder outside the architecture folder, such as `.wfctl/exceptions/`.
  This keeps the reviewer's copy in the diff. We didn't choose it because the
  repo still gains a file for every branch that claims an exception, just in a
  different folder, and a new file for every one-line fix was already ruled out
  for the spec answer.
- The gate stops requiring an explicit "no" and checks only that `design.md`
  exists. We didn't choose it because the pipeline would no longer make the
  agent answer the boundary question before specify.
- wfctl requires "Moves a boundary?" whenever a branch has a design exception,
  whatever `change_sections` lists. We didn't choose it because it would be the
  first heading wfctl names itself, and a repo whose template lacks the heading
  would fail every PR until it added one (`wfctl/_sections.py` explains why
  wfctl holds no section name).

## Consequences

The reviewer is less certain to see a design exception. Previously, the gate
enforced it, since a design exception outside the change under review didn't
count. Currently, `check-body` enforces it. It reports any design exception
whose reason isn't in the PR body, in every repo, and it finds the reason
anywhere in the body, so wfctl still names no heading. `check-body` skips one
case, a boundary exception a sub-issue inherits from its epic. Once the
sub-issue changes a level-2 record, the inherited exception no longer applies,
since the record states the boundary decision for that sub-issue. The opening-a-change
skill runs `check-body`; CI and the worktree guard don't. That's acceptable
while wfctl has one user, and it should be revisited before it has a second.

The answer is now written once, early, and the branch can change after that.
The gate reads the boundary exception before it asks git about records, so an
agent that writes "no new boundary" and adds a record later passes the gate
with a wrong answer. So the worktree guard refuses to open or merge the PR when
a branch touches a level-2 record and its own spec folder still says no
boundary moved. An exception a sub-issue inherits from its epic's folder isn't
a contradiction, since the record answers the question for that sub-issue and
the epic's answer stays true for the others.

The guard also refuses to open or merge the PR while a record the branch
touches isn't accepted. Previously, an unattended run could merge a boundary
nobody approved. In an attended session, the agent stops when it writes a
record on a branch with a boundary exception, so the user can reject the record
before anything is built on it. In an unattended run, the agent makes the call,
writes the alternatives it rejected, and the user accepts or rejects the record
before the PR opens.

The gate ignores `declarations/` and `step-claims/`. Otherwise a declaration
or step claim written by an older wfctl would count as a record and satisfy the
gate. The architecture folder would start filling up again, and nothing would
flag it.

This change deletes the existing 15 declarations. Git history and each merged
PR keep their reasons. The 5 step claims move into `exceptions/` in their
branches' spec folders instead, since they record why each plan walkthrough was
skipped.

#382's short track reads the same design exception file in the spec folder.
That issue's plan asks for a committed `arch none` file, so it needs the new
location.

## Log

- 2026-10-25  proposed    — #635's level-2 pass; the architecture folder should
  change only when the architecture does
- 2026-10-26  revised     — the 5 step claims move to their spec folders rather
  than being deleted, so the reasons for skipped walkthroughs are kept
- 2026-10-26  revised     — plan walkthrough: `check-body` compares the two
  copies, and the worktree guard holds a PR whose record contradicts the
  branch's own answer or isn't accepted
- 2026-10-26  revised     — analyze: `check-body` skips a boundary exception
  inherited from an epic once the sub-issue changes a level-2 record
