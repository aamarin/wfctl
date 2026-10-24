# Feature Specification: Every change runs the design passes and records whether it needs a spec

**Feature Branch**: `628-design-passes-every-change`
**Created**: 2026-10-22
**Status**: Draft
**Input**: User description: "From the brainstorm output at design.md (issue #628: run the design passes and a refactor pass on every change, not only Spec Kit ones)"

## Clarifications

### Session 2026-10-22

- Q: Which changes run `design-passes`? → A: Only changes a handoff doesn't send to Spec Kit. A branch routed to Spec Kit from the start skips the skill, and its PR answers "Yes" in the "Needs a spec?" section. The pipeline already runs the passes: brainstorm runs levels 2 and 3, and `/speckit.implement` runs test tasks first and `clean-code` after the last task (#479).
- Q: What's the `wfctl.json` key for required PR sections called? → A: `change_sections`. It pairs with `change_check` beside it, and "change" is wfctl's word for a PR, a merge request, or a patchset.

## User Scenarios & Testing _(mandatory)_

### User Story 1 - A change that bypasses Spec Kit still runs the design passes (Priority: P1)

The design passes are the level-2 and level-3 questions from `design-levels`,
plus a test-first step and a refactor step. Currently, they run only inside
the Spec Kit pipeline. `AGENTS.md`, `design-levels`, `architecture-design`,
and `worktree-handoff` all say that a bug fix or a copy edit can go straight
to implementation, and the agent decides which changes qualify. As a result,
most of this repo's changes never run the passes. Over the last 90 days, more
than half of about 530 commits were `fix:`, `docs:`, or `chore:` changes.

After this change, a new skill, `design-passes`, runs before any code is
written on every change that a handoff doesn't send to Spec Kit. A handoff
that sends a change to Spec Kit skips `design-passes`, since the session that
wrote it has already read the issue and made the spec call. `design-passes`
first asks whether the change needs a full spec. If yes, the change goes
through the Spec Kit pipeline. If no, it runs four passes in this order:

1. Level 2 reads the accepted records (`wfctl arch context`) and the domain
   model in `docs/architecture/domain/`. Then it checks whether the change
   redraws or edits a boundary. A change inside an existing boundary writes
   nothing. A change that redraws or edits one may need an architecture
   record, written with `architecture-design`. A change to what a modeled term
   means goes to `model-the-domain` first.
2. Level 3 writes a design record with `software-design-decisions` for any
   structural choice that had more than one credible option.
3. The agent commits a failing test, then writes the code.
4. A behavior-preserving refactor runs `clean-code`, plus
   `python-pattern-selection` when a pattern name comes up. Each refactor is
   its own commit.

The skill has no design method of its own. Each pass hands off to the skill
that already does that work.

Every place that sends a small change straight to implementation points to
`design-passes` instead:

1. The route line `worktree-handoff` writes into every handoff.
2. The "not for" lines in `design-levels` and `architecture-design`. They say a
   change skips Spec Kit, not the passes.
3. The paragraph in `AGENTS.md` that allows skipping the pipeline.

The agent has to reach the skill through these lines, because a skill found
only by its description doesn't fire in an unattended run (#290).

**Why this priority**: This is the feature. In the handoffs for #603 and #604,
running these passes by hand caught a premise that didn't hold before any code
was written.

**Independent Test**: Install the skills, then give an agent only a handoff
for a one-line fix with the new route line. The agent runs `design-passes`
before writing any code, and the branch ends with a failing-test commit before
the fix commit.

**Acceptance Scenarios**:

1. **Given** a handoff written by `worktree-handoff` for a bug fix, **When** an
   agent reads its route line, **Then** the line tells it to run
   `.agents/skills/design-passes` before writing any code, and says that
   skill decides whether the change needs a spec.
2. **Given** a change the agent answers "needs a spec: yes" for, **When**
   `design-passes` runs, **Then** it sends the change to the Spec Kit pipeline
   and runs none of the four passes itself.
3. **Given** a change inside an existing boundary, **When** level 2 runs,
   **Then** it writes no file.
4. **Given** a change that redefines a term in the domain model, **When**
   level 2 runs, **Then** the skill sends it to `model-the-domain` before
   `architecture-design`.
5. **Given** the shipped `design-levels`, `architecture-design`,
   `worktree-handoff`, and `AGENTS.md`, **When** a reader reads the section in
   each that lets a change skip Spec Kit, **Then** that section names
   `.agents/skills/design-passes`, and no shipped file says "straight to
   implementation" in any case.
6. **Given** a bug fix that `design-passes` sends to `architecture-design`
   because it moves a boundary, **When** the agent reads that skill's "not
   for" line, **Then** the line doesn't send the fix back out. The line
   excludes a change that moves no boundary, not a change of a given kind.
   The same holds for `architecture-decisions`, where `architecture-design`
   hands the boundary next.
7. **Given** a bug fix that `design-passes` answered "needs a spec: yes" for,
   **When** brainstorm reads the `design-levels` "not for" line, **Then** the
   line keeps the change in brainstorm rather than sending it back to
   `design-passes`.

---

### User Story 2 - A PR with no spec answer can't pass `check-body` (Priority: P1)

The spec answer is the change's yes or no on whether it needs a full spec,
with a one-sentence reason. A reviewer can only check or challenge that
decision if it's written down where they read. Currently, it isn't written
anywhere.

After this change, this repo's PR template has a "Needs a spec?" section. A
repo lists the sections every PR has to answer under `change_sections` in
`wfctl.json`, next to
`change_check`. `wfctl check-body` reports a finding when a listed section is:

1. Missing from the body.
2. Empty, or holding nothing but the template's HTML comments.
3. Holding only "N/A".
4. Holding only "Yes" or "No", with no reason after it.

wfctl has no built-in section names. A repo that lists none sees no change,
and `check-body` prints the same thing it prints today. `opening-a-change`
already runs `check-body` in Step 5, before `gh pr create`, so that skill
needs no new step.

A bare yes or no fails because it leaves no record of why the decision was
made. The reason is also what lets a reviewer catch an answer that contradicts
the diff. The check confirms that a reason is there, not that it's a good one.
The reviewer judges the reason.

Nothing checks that the question was asked before any code. An agent that
skipped it can still answer "No" when the PR opens. The review panel reduces
that risk, but doesn't close it. The panel runs before the PR description is
written, so no reviewer sees the answer. Instead, each reviewer reads only the
diff and reports any design decision the diff makes that no record or spec on
the change covers, such as new stored state, a new setting the code reads, a
new command, or a moved boundary. The author writes the answer after reading
those findings, and still decides what to do with each one. In an attended run,
the person sees the findings in the panel's table before the PR opens. In an
unattended run nobody reads the table, so a finding the author dismisses stays
in the reviewer's report and goes no further.

**Why this priority**: This is the only check in the feature, and it catches
a change that skipped every earlier step. It sits beside User Story 1 because
without it a missing answer reaches the reviewer unnoticed.

**Independent Test**: In a repo that lists "Needs a spec?" in `wfctl.json`,
run `check-body` on five bodies: one answered, one with "N/A", one with only
the HTML comment, one with the heading deleted, and one holding only "No.".
The first passes and the other four each print one finding.

**Acceptance Scenarios**:

1. **Given** a listed section holding only "N/A", **When** `check-body` runs,
   **Then** it prints `⚠ "Needs a spec?" holds N/A. The template's comment
   under that heading says what to write.` and exits 1.
2. **Given** a body with the listed heading deleted, **When** `check-body`
   runs, **Then** it prints `⚠ "Needs a spec?" is missing. This repository asks
   every pull request to answer it.` and exits 1.
3. **Given** a listed section holding only its HTML comment, **When**
   `check-body` runs, **Then** it reports the section as empty.
4. **Given** a listed section holding only "No.", **When** `check-body` runs,
   **Then** it prints `⚠ "Needs a spec?" answers yes or no with no reason. The
   template's comment under that heading says what to write.` and exits 1.
5. **Given** a section answered "No. The fix changes one check inside the
   worktree guard and adds no state.", **When** `check-body` runs, **Then** it
   reports nothing about that section.
6. **Given** a repo whose `wfctl.json` lists no required sections, **When**
   `check-body` runs on any body, **Then** its output is the same as before
   this change.
7. **Given** a `wfctl.json` that lists a section the repo's PR template doesn't
   have, **When** `wfctl check config` runs, **Then** it reports a finding
   naming that section.
8. **Given** a fix whose diff has the worktree guard read a new config file,
   and no record or spec covering it, **When** the review panel runs, **Then**
   at least one reviewer reports the new setting as a finding.

---

### User Story 3 - Both routes start level 2 by reading the records and the domain model (Priority: P3)

Currently, level 2 in `design-levels` chooses a method without first reading
what the repo already decided. A small fix can then redraw a line the domain
model already settled, and nobody notices.

After this change, level 2 of `design-levels` starts the same way it does in
`design-passes`: it reads the accepted records with `wfctl arch context` and
the domain model in `docs/architecture/domain/` before choosing a method. A
change to what a modeled term means goes to `model-the-domain` before
`architecture-design`.

**Why this priority**: The Spec Kit route skips this step today too, so it's a
gap in both routes rather than in the new one. It's the smallest change here.

**Independent Test**: Read the installed `design-levels` skill. Level 2's
first step names `wfctl arch context` and `docs/architecture/domain/`, and
uses the same wording as `design-passes`.

**Acceptance Scenarios**:

1. **Given** the shipped `design-levels` and `design-passes`, **When** a reader
   compares their level-2 opening steps, **Then** both read the accepted
   records and the domain model before choosing a method.

---

### Edge Cases

- A PR body renames the "Needs a spec?" heading. `check-body` reports it as
  missing, so the check fails rather than passes.
- A section holds "n/a" or "N/A." in another case or with punctuation.
  `check-body` treats it as N/A.
- A section holds "no", "YES", or "No!" in another case or with punctuation.
  `check-body` treats it as a bare answer. A short reason such as "No, small
  change." passes, and the reviewer judges it.
- A release PR from `.github/scripts/release.py` never runs `check-body`, so
  it needs no exemption.
- A session restarts after the spec question but before the PR. The answer
  may be lost, and the PR section still requires it.
- A handoff sends a change to Spec Kit from the start. The branch skips
  `design-passes`, and its PR still
  answers "Yes" in the "Needs a spec?" section.
- A docs-only change still answers the question. This repo's skills are
  Markdown files that control what an agent can do, and the answer takes one
  sentence.
- A repo lists required sections but ships no PR template. `wfctl check
  config` reports a finding, since no listed section can be found in it.

## Requirements _(mandatory)_

### Functional Requirements

- **FR-001**: wfctl MUST ship a `design-passes` skill under
  `wfctl/agents/skills/` that asks the spec question first and then runs the
  four passes in the order given in User Story 1.
- **FR-002**: `design-passes` MUST hand each pass to the existing skill for it
  (`architecture-design`, `model-the-domain`, `software-design-decisions`,
  `clean-code`, `python-pattern-selection`) and define no design method of its
  own.
- **FR-003**: `design-passes` MUST send a change answered "yes" to the Spec
  Kit pipeline and run none of the four passes on it.
- **FR-004**: The route line in `worktree-handoff`, the "not for" lines in
  `design-levels` and `architecture-design`, and the pipeline-skip paragraph
  in `AGENTS.md` MUST each point to `design-passes`. The "not for" lines in
  `design-levels`, `architecture-design`, `model-the-domain`, and
  `architecture-decisions` MUST exclude a change by whether it moves a
  boundary or changes a modeled term, not by its kind, so a bug fix that
  `design-passes` sends to any of them isn't sent back. The `design-levels`
  line MUST keep a change that `design-passes` answered "yes" for.
- **FR-005**: `design-passes` MUST ask the spec question before any code is
  written, and MUST record the answer only in the PR's "Needs a spec?"
  section. It writes no commit trailer and no file for it.
- **FR-006**: `wfctl.json` MUST accept a `change_sections` key, next to
  `change_check`, that lists the PR sections every PR has to answer.
- **FR-007**: `wfctl check-body` MUST report a finding for each listed section
  that is missing, empty apart from HTML comments, holding only N/A, or
  holding only yes or no with no reason, using
  the messages in User Story 2.
- **FR-008**: `wfctl check-body` MUST NOT change its output in a repo that
  lists no required sections.
- **FR-009**: `wfctl check config` MUST report a finding for a listed section
  the repo's PR template doesn't have, and for a value that isn't a list of
  section names.
- **FR-010**: This repo's PR template MUST have a "Needs a spec?" section, and
  this repo's `wfctl.json` MUST list it.
- **FR-011**: Level 2 of `design-levels` MUST start by reading the accepted
  records and the domain model, the same as `design-passes`.
- **FR-012**: This change MUST NOT make `wfctl verify` require an `arch none`
  file on a branch, and `design-passes` MUST tell the agent not to run
  `wfctl arch none` on its route. The Spec Kit design step still requires a
  record or a declaration.
- **FR-013**: The change MUST NOT edit `opening-a-change`, which #622 is
  redesigning.
- **FR-014**: `fanning-out-code-review` MUST tell every reviewer it dispatches
  to report any new stored state, setting the code reads, command or flag, or
  boundary that the diff adds and that no record or spec on the change covers.

## Key Entities

- **Spec answer**: a change's yes or no on whether it needs a full spec, with
  a one-sentence reason. It's written in one place, the PR's "Needs a spec?"
  section, whichever route the change took.
- **Required PR sections**: the `change_sections` list in a repo's `wfctl.json` of section
  headings every PR body has to answer. It's empty unless a repo sets it.

## Success Criteria _(mandatory)_

### Measurable Outcomes

- **SC-001**: An agent given only a handoff with the new route line, for a
  one-line fix on a throwaway branch, runs `design-passes` and answers the
  spec question before it edits any code.
- **SC-002**: `check-body` reports a finding on all four bad states (missing,
  empty, N/A, a bare yes or no) and on none of the answered bodies in the test
  set.
- **SC-003**: In a repo that lists no required sections, `check-body` output
  is byte-identical to its output before this change on the same bodies.
- **SC-004**: Zero lines in the shipped skills and `AGENTS.md` send a change
  straight to implementation without naming `design-passes`.
- **SC-005**: Given the N/A message, an agent replaces "N/A" with a yes or no
  and a reason, not a bare "No.", on the first retry.

## Validation Strategy _(mandatory)_

- `uv run pytest -q`, `uv run ruff check wfctl/ tests/`, and
  `uv run mypy wfctl/` all pass.
- Tests run `check-body` on a listed section holding "N/A", one holding only
  its HTML comment, one with the heading deleted, one holding only "No.", and
  one answered, and check that the first four each report a finding and the
  last reports none.
- A test runs `check-body` in a repo with no required sections and checks the
  output is unchanged.
- A test runs `wfctl check config` with a listed section missing from the
  template, and checks it reports a finding.
- The suite's skill cross-reference tests cover `design-passes` and fail when a
  route section stops pointing to it.
- An agent handed a body holding N/A under "Needs a spec?" and the N/A finding
  rewrites the section once, and the retry holds a yes or no and a reason
  (SC-005).
- `uv run wfctl check config` passes on this repo after its `wfctl.json` lists
  the new section.
- The review panel, run on a throwaway fix that has the worktree guard read a
  new config file, reports the new setting as a finding (quickstart §5).
- `uv run wfctl install-skills --agent claude`, then run `design-passes` on a
  throwaway branch with a one-line fix and check that it answers the spec
  question before editing any code (SC-001).
- `uv run wfctl doctor` reports the installed tree current.

## Assumptions

- Pre-specify design context loaded from
  `/Users/andremarin/Development/wfctl-specs/628-design-passes-every-change/design.md`,
  along with its four proposed records.
- Where the spec line falls is Andre's decision, and this feature doesn't make
  it. Until he does, each spec answer gives its own reason and the reviewer
  judges it. `design-passes` carries his criterion once he settles it.
- #382's short track currently requires a committed `arch none` file. This
  feature stops requiring that file on small fixes, so #382 needs another
  look. #635 covers where per-branch answers such as `arch none` belong, and
  this feature doesn't decide it.
- Per-task `clean-code` inside `/speckit.implement` is #479 and out of scope.
- Nothing checks the level-3 answer, the test-first commit, or the refactor
  commits. Each would check a file only the agent vouches for.
