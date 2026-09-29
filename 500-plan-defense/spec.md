# Feature Specification: plan-walkthrough

**Feature Branch**: `500-plan-defense`  
**Created**: 2026-09-27  
**Status**: Draft  
**Input**: User description: "plan-defense: an adversarial ownership pass after plan and after implement" (issue #500), as reshaped by `design.md` and renamed the plan walkthrough

## Clarifications

### Session 2026-09-27

- Q: What should `/plan-walkthrough` do when a person types it while auto-approve is on? → A: Always refuse. It asks nothing, writes nothing, and says to run `wfctl start --no-auto-approve` first, since the skill cannot tell a command a person typed from one orchestrate issued.
- Q: Where is the `wfctl.json` snippet that declares the pass documented? → A: In `docs/reference.md`, in a new section on declaring a repository's own steps that covers `needs_person` and uses plan-walkthrough as its example. The skill's `SKILL.md` points to that section in one line and does not repeat the snippet.

## User Scenarios & Testing _(mandatory)_

### User Story 1 - A person walks through their plan in private (Priority: P1)

A person who is about to put their name on a plan runs `/plan-walkthrough`. The
agent reads the spec, the plan, and the architecture records, then asks one
material question at a time about what was written. The person answers each
one in their own words. When the interview ends, the answers and the gaps they
exposed are saved on the person's machine, and the feature directory gets a
marker that says which plan was walked through and when. Nobody else sees the
answers unless the person chooses to share them.

**Why this priority**: This is the whole purpose of the feature. A person finds
out whether they can explain their own work before a reviewer does, and they
answer honestly because the result is private.

**Independent Test**: Run `/plan-walkthrough` in plan mode on a branch that has a
`plan.md`, answer the questions, and confirm that the answers file exists in
the state directory, the marker exists in the feature directory, and the marker
holds no answers.

**Acceptance Scenarios**:

1. **Given** a branch with a `plan.md` and a person at the prompt, **When** the
   person runs `/plan-walkthrough` in plan mode, **Then** the agent asks exactly one
   primary question per turn and waits for the answer before asking the next.
2. **Given** an interview that has reached its outcome, **When** the skill
   records the result, **Then** the answers are written to a new file under the
   branch's state directory and the feature directory holds a
   `plan-walkthrough.md` marker with the mode, the content hash of `plan.md`, and
   the date.
3. **Given** a finished run, **When** anyone reads the marker, **Then** it holds
   no challenge, no answer, no disposition, and no count.
4. **Given** a repository that declares the pass with `plan-walkthrough.md` as its
   evidence, **When** the marker exists, **Then** `wfctl status` reports the
   pass as done.
5. **Given** a question that the architecture records, the `Considered`
   sections, or the checked and assumed split already decided, **When** the
   agent asks about it, **Then** the question asks the person to explain that
   decision and does not reopen it.

---

### User Story 2 - An unattended run skips the check and says so (Priority: P1)

A repository has declared the pass with `needs_person`, and an unattended run
under `auto_approve` reaches the step it sits under. Nobody is present to
answer, and an agent answering its own questions would prove nothing about the
person. wfctl reads the pass as skipped, with the reason that it needs a person
and auto-approve is on, and the run moves on. Nothing is written to the
repository or the feature directory.

**Why this priority**: Without it, every unattended run on a repository that
declares the pass either stalls on the pass or reports a check nobody ran as
done. Both are worse than not shipping the pass.

**Independent Test**: With the pass declared with `needs_person` and
`auto_approve` on, run `wfctl status --json` and confirm that the pass reads
`skipped` with the reason, that the next command names the step after the pass,
and that `git status` shows no new file.

**Acceptance Scenarios**:

1. **Given** a pass declared with `needs_person`, `auto_approve` on, and no
   marker, **When** wfctl reads the pipeline, **Then** the pass reads `skipped`
   with the reason "needs a person; auto-approve is on", and the sub-step
   payload carries `needs_person: true`.
2. **Given** the same state, **When** orchestrate reads the pipeline, **Then**
   the next command names the step after the pass, `/plan-walkthrough` is not
   invoked, and the run is not reported as stalled.
3. **Given** the unattended run has finished, **When** anyone looks at the
   branch, **Then** no claim file, marker, or answers file was written for the
   pass.

---

### User Story 3 - A person comes back to a branch an unattended run passed (Priority: P2)

An unattended run passed the check by. Later a person turns auto-approve off
and picks the branch up. The pass reads as outstanding again with no cleanup,
and the person can run `/plan-walkthrough` as usual. A person who runs the check
while auto-approve is still on is refused and told to turn it off first, since
the skill cannot tell a person at the prompt from an unattended run.

**Why this priority**: This is what makes the skip honest. A skip that stayed
after the person came back would hide a check nobody ran. It matters only once
Story 2 exists.

**Independent Test**: After Story 2's test, run `wfctl start --no-auto-approve`
and confirm the pass reads `in_progress`, the outstanding pass; then run `/plan-walkthrough` attended and
confirm the pass reads `done`.

**Acceptance Scenarios**:

1. **Given** a pass skipped under Story 2, **When** auto-approve is turned off,
   **Then** the pass reads `in_progress`, the outstanding pass, and no file had to be deleted.
2. **Given** auto-approve on and a person who runs `/plan-walkthrough` anyway,
   **When** the skill starts, **Then** it asks nothing, writes nothing, and
   says to run `wfctl start --no-auto-approve` first.
3. **Given** a marker an attended run wrote, **When** auto-approve is turned on
   again, **Then** the pass reads `done`, not `skipped`.
4. **Given** a claim a person wrote with `wfctl step none` on the pass, **When**
   wfctl reads the pipeline in either mode, **Then** the claim wins, as it does
   for every pass today.

---

### User Story 4 - A person walks through a finished change (Priority: P2)

Once code exists, the person runs `/plan-walkthrough` in change mode. The
agent reads the diff and the plan that was walked through, and asks whether the code does
what the plan intended and whether the person understands what it now does.
The answers are saved privately in the same way as Story 1, and the marker is
`change-walkthrough.md`, naming the commit that was walked through.

**Why this priority**: It is the second of the two modes the skill already has,
and it reuses everything Story 1 builds. A repository can get value from plan
mode alone.

**Independent Test**: On a branch with commits, run `/plan-walkthrough` in
change mode and confirm that the answers file is written with the
change mode in its name and the marker names the commit.

**Acceptance Scenarios**:

1. **Given** a branch with commits, **When** the person runs change
   mode, **Then** the questions are about the diff against the plan that was walked through
   and the spec.
2. **Given** a finished run, **When** the skill records it, **Then** the
   feature directory holds `change-walkthrough.md` with the mode, the
   commit, and the date.
3. **Given** uncommitted changes in the tree, **When** the marker is written,
   **Then** the skill tells the person that the marker names the last commit
   and does not cover the uncommitted changes.

---

### User Story 5 - A repository places the pass where it wants it (Priority: P3)

A maintainer wants the check in their workflow, for example after `plan` or
after `implement`. They copy the snippet from the reference docs into `wfctl.json`,
run `wfctl check config`, and the pass appears under the step they chose. wfctl
places the check nowhere by default.

**Why this priority**: Placement already exists in `wfctl.json` `steps`, and
the only new part is `needs_person`, which Story 2 builds. This story is
documentation plus a check that the documented snippet works.

**Independent Test**: Paste the reference-docs snippet into a scratch repository's
`wfctl.json`, run `wfctl check config`, and confirm that it reports no finding
and that `wfctl status` lists the pass under the chosen step.

**Acceptance Scenarios**:

1. **Given** a repository with no declaration, **When** `wfctl status` runs,
   **Then** no plan-walkthrough pass appears anywhere in the pipeline.
2. **Given** the reference-docs snippet pasted into `wfctl.json`, **When** the
   maintainer runs `wfctl check config`, **Then** it reports no finding.
3. **Given** a declaration with `needs_person` that is not a boolean, or with
   `needs_person` on a `manual` pass, **When** the maintainer runs
   `wfctl check config`, **Then** it reports a finding naming the pass.

---

### Edge Cases

- A repository declares the pass without `needs_person`. An unattended run
  then invokes `/plan-walkthrough`; the skill asks nothing, writes nothing, and says
  the declaration needs `needs_person`. The pass stays outstanding and the run
  stops as stalled, which is loud, and the finding names the fix.
- `/plan-walkthrough` is run in a repository that declares no pass at all. It works
  the same way for a person: the answers go to the state directory and the
  marker to the feature directory, and no pipeline reads the marker.
- A repository wraps the skill in a command of its own. `needs_person` still
  works, since wfctl reads the field and never the command's name.
- Plan mode runs on a branch with no `plan.md`. The skill says there is no plan
  to walk through and stops, without writing an answers file or a marker.
- The person stops partway through the interview. The answers given so far
  stay in the answers file, marked as incomplete, and no marker is written, so
  the pass does not read done.
- The plan changes after it was walked through. The marker still exists and the pass
  still reads done; the marker names the hash of the plan it was run against,
  so a person can see the difference, and no check compares them.
- A person decides a gap belongs in the plan. They may add it to the plan
  themselves, worded as a gap in the plan, such as "the plan does not say what
  step 3 does to `plan.md`", and never as a gap in the person. The skill does
  not edit the plan on its own.

## Requirements _(mandatory)_

### Functional Requirements

- **FR-001**: wfctl MUST ship the plan-walkthrough skill as its own skill, with its
  references, installed by `wfctl install-skills` like every other shipped
  skill.
- **FR-002**: wfctl MUST ship a `/plan-walkthrough` command that runs the skill.
- **FR-003**: wfctl MUST NOT place the pass in any pipeline step by default; a
  repository places it by declaring it in `wfctl.json` `steps`.
- **FR-004**: The skill MUST support two modes: plan walkthrough, run against a
  plan before tasks exist, and change walkthrough, run against a
  diff once code exists.
- **FR-005**: The interview MUST ask exactly one primary question per turn,
  follow up at most twice on a vague answer, and then record the question as a
  gap.
- **FR-006**: The agent MUST NOT answer its own questions or write an answer on
  the person's behalf.
- **FR-007**: The skill MUST write the answers, dispositions, and gaps to a new
  file in the branch's state directory on every run, named by mode and date and
  time, and MUST NOT write them anywhere under the feature directory.
- **FR-008**: The skill MUST write a marker to the feature directory only when
  an attended interview reaches its outcome. The marker MUST hold the mode, what
  was walked through (the content hash of `plan.md` in plan mode, the commit in
  change mode), and the date, and nothing else.
- **FR-009**: The marker MUST be named `plan-walkthrough.md` in plan mode and
  `change-walkthrough.md` in change mode, so a declared pass can use
  either name as its evidence.
- **FR-010**: A declared pass in `wfctl.json` MUST accept an optional boolean
  `needs_person`. While `auto_approve` is on and the pass's evidence is absent,
  wfctl MUST read a pass carrying `needs_person: true` as `skipped` with the
  reason "needs a person; auto-approve is on", and MUST write nothing to do so.
- **FR-011**: The checks MUST apply in this order: a claim wins; evidence that
  exists reads `done`; `needs_person` with `auto_approve` on reads `skipped`;
  otherwise the pass's reader decides.
- **FR-012**: The sub-step payload MUST carry `needs_person` beside `manual`, so
  a consumer can tell this skip from a claimed one and an inherited one.
- **FR-013**: `wfctl check config` MUST report a finding for `needs_person`
  that is not a boolean, and for `needs_person` on a `manual` pass.
- **FR-014**: When `/plan-walkthrough` starts while `auto_approve` is on, whether a
  person typed it or orchestrate invoked it, the skill MUST ask nothing, write
  nothing, and say to run `wfctl start --no-auto-approve` first. It MUST also
  say that an unattended run skips the pass only when its declaration carries
  `needs_person`.
- **FR-015**: The lenses for rationale, assumptions, boundaries, and evidence
  MUST ask the person to explain what the architecture records, the `Considered`
  sections, the checked and assumed split, and verification already decided,
  and MUST NOT reopen those decisions. The comprehension lens MUST lead.
- **FR-016**: The skill MUST NOT edit the plan, the code, or the architecture
  records during the interview.
- **FR-017**: The skill MUST NOT ship a per-vendor manifest inside its
  directory.
- **FR-018**: `docs/reference.md` MUST carry a section on declaring a
  repository's own steps in `wfctl.json`, including `needs_person`, with the
  snippet that declares the plan-walkthrough pass as its example. That snippet MUST
  pass `wfctl check config`. The skill's `SKILL.md` MUST point to that section
  and MUST NOT repeat the snippet.
- **FR-019**: The `vendor-upstream-skills` record MUST say that plan-walkthrough is
  wfctl's own skill and vendors no upstream text.
- **FR-020**: This repository's `wfctl.json` MUST declare plan mode under
  `plan`, with `plan-walkthrough.md` as its evidence and `needs_person: true`.
  Change mode is not declared here; its marker would read done on code
  that changed after the walkthrough, and #505 adds it once that is visible.

### Key Entities

- **Answers file**: One per run, in the branch's state directory. It holds each
  challenge, the person's answer, its disposition (`SETTLED`,
  `REVISION_REQUIRED`, `DEFERRED`, or `UNRESOLVED`), and the gaps. It is never
  committed by wfctl, and a run cut short keeps what was answered and says so.
- **Marker**: One per mode, in the feature directory. It holds the mode, what
  was walked through, and the date. It is the evidence a declared pass reads, and it
  holds nothing about how the person did.
- **Declared pass**: A repository's own entry in `wfctl.json` `steps` that runs
  `/plan-walkthrough` under a step the repository chose, with one of the two marker
  names as its evidence and `needs_person: true`. The flag is the repository's
  statement that the pass cannot run without a person, and wfctl combines it
  with the approval mode it already stores to decide the skip.

## Success Criteria _(mandatory)_

### Measurable Outcomes

- **SC-001**: After any number of runs in either mode, 0 answers, dispositions,
  or gaps appear in any file under the feature directory or in any committed
  file.
- **SC-002**: Every agent turn in an attended interview carries exactly 1
  primary question.
- **SC-003**: An unattended run passes a pass declared with `needs_person`
  with 0 invocations of `/plan-walkthrough` and 0 files written, and the pipeline
  reports it as skipped with its reason, never as done and never as stalled.
- **SC-004**: When a person comes back after an unattended skip, the pass reads
  outstanding with 0 files deleted or edited by hand.
- **SC-005**: A maintainer places the pass under any step by pasting 1 snippet
  from the reference docs, with no other change to their repository.

## Validation Strategy _(mandatory)_

- `uv run pytest -q`, `uv run ruff check wfctl/ tests/`, and `uv run mypy
  wfctl/` are green, including the existing tests that check shipped skills
  and command wrappers are present and cross-reference correctly.
- `uv run wfctl install-skills --agent claude` installs the skill and the
  command, and `uv run wfctl doctor` reports no drift.
- New unit tests cover `needs_person`: parsing and both `check config`
  findings; the pass reading `skipped` with `auto_approve` on and `in_progress` with
  it off; a marker that exists reading `done` in both modes; a claim winning in
  both modes; and `needs_person` in the sub-step payload.
- The architecture-record tests pass over the new and amended records.
- The reference-docs snippet, pasted into a `wfctl.json`, passes
  `uv run wfctl check config`, and `wfctl status` lists the pass under the
  chosen step.
- Stories 1, 3, and 4 are run by hand on a scratch branch, since skill
  behavior is not covered by the test suite and this manual run is the
  evidence for it.

## Assumptions

- Pre-specify design context loaded from `design.md` in this feature
  directory.
- The skill's content comes from the candidate at `docs/plan-defense/` in the
  main checkout; its interview method, dispositions, and lenses are kept, and
  only the artifact contract, the lens pruning, and the unattended behavior
  change.
- Answers last as long as the state directory does. wfctl never deletes them,
  and keeping them somewhere durable and private is out of scope.
- The pass reader stays "the marker exists". A plan changed after its walkthrough
  still reads done, and a general check for stale evidence is separate work.
- `auto_approve` on is read as "no person is expected at the prompt". A person
  who is present with it on still sees the pass skipped, and turns auto-approve
  off to run the check.
- Reviewing whether the plan itself holds together, an agent answering from
  evidence, and any gate or revision loop belong to #501 and are not part of
  this feature.
