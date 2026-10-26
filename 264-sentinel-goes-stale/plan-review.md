# Plan Review Report

Review state: completed
Review type: re-review

## Reviewed inputs

| Artifact | Content identity | Role |
| --- | --- | --- |
| plan.md | 1797be85e18f6a5d6f364b0cd1b049d83b10f30c | technical strategy |
| spec.md | e63d64911c6132e33deeaaeebb8cb4f4bd8ac50c | requirements |
| .specify/memory/constitution.md | absent | constitution |
| design.md | 5c686de27a6212a1692331fb32dcf695f7372772 | design-record index |
| docs/architecture/design/264-the-task-copy-lives-in-the-completion-record.md | 73d6c1664f0986dd82400ff10a2165a1588547b9 | design record |
| docs/architecture/design/264-the-completion-command-is-a-step-verb.md | 6938214375db57bbe96bd0992d114812fcf90749 | design record |
| docs/architecture/new-task-reopens-implement.md | 800f96d21795ee68ef91441bb3373f62b82eea9e | architecture record (level 2) |
| research.md | 37b719254e4b58c5947b6f3c6a0f6ae2255a4e3f | planning evidence |
| data-model.md | aac2aa3e59090497e429651da8469dd2a2b5e76f | planning evidence |
| contracts/cli.md | 0eacf07ff9625faad3e1e42f07d87a8a09a93642 | planning evidence |
| quickstart.md | 1b6384fb8d4f74077512e8853124234990759a6d | planning evidence |
| checklists/requirements.md | 3f61287371e0bafbc032dbdaa791ed2c1e3c3709 | planning evidence |
| checklists/analysis-report.md | 75050b8fa04f75cb0a2d1c38b36f445e255d8f69 | context only, read to locate the edits |
| plan-review.plan.md | 597f94bc5473d1795b088140ad8bc913f6190e7a | base of this re-review |

## Review scope

- Re-review: the earlier report and the plan copy both exist, and the copy's identity equals the earlier report's `plan.md` row.
- Changed in `plan.md`: one paragraph, the second paragraph of §Summary item 2. It now says the claim holds for a feature whose delivery plan has every row keyed or whose repository declares no tracker, says `decompose` is skipped "while the tasks read closed", names the unkeyed-row route, and widens the set of features the case reaches. Nothing else in `plan.md` changed. The paragraph was reviewed together with the first paragraph of item 2, the §Test Plan introduction and its row with no `delivery.md`, the changed-tests row for `tasks-open-but-implemented`, and research R1, which state the same limit.
- Changed inputs beyond `plan.md`: `spec.md`. There is no earlier copy of it to diff against, so it was re-read in full and the whole of `plan.md` was reviewed against it. The visible changes are FR-010, which now carries the condition "for a feature whose `decompose` step reads done or skipped", and the delivery-plan bullet under Edge Cases, which now names keyed rows, the no-tracker case, and the unkeyed-row route. Every other input row of the earlier report still matches its file.
- `checklists/analysis-report.md` is new since the earlier review. It was read only to find which artifacts the analysis pass edited, and nothing in this report rests on its claims. The `tasks.md` edits it describes are outside this review, since tasks are the analysis pass's subject.
- Lenses: requirements and traceability, architecture and boundaries, adversarial implementation and verification.
- Conditional lenses: security and reliability applied, for the earlier report's reason. The feature's subject is a trust boundary, since the agent shouldn't certify its own completion, and the new command overwrites the file that gates the `implement` step. The edits in this round don't touch that boundary, so the lens found nothing new.
- Design records: 2 listed in `design.md`, unchanged. The level-2 record, named in prose there, is unchanged and was checked again at its §Decision, since FR-010 now carries a condition the record does not.
- Accepted architecture records: carried from the earlier report (13 accepted). `wfctl arch context` was not re-run, since no record and no boundary in the plan changed.
- Constitution: `.specify/memory/constitution.md` is still absent.
- Existing code inspected: `wfctl/_evidence.py` (`_tasks_open`, `_task_tally`, `_unkeyed_issues`, and the `plan_review`, `tasks`, `analyze`, `decompose`, and `implement` readers).
- Population check: carried from the earlier report and not re-run. All 22 feature directories in the spec store that hold a completion record also hold a `delivery.md`, and `26-spec-root-prompt-and-durable-skip` has one unkeyed row.
- Reviewers: the four lenses above, run in sequence by one agent in a context separate from the session that edited the plan.

## Summary

BLOCKER: 0
MAJOR: 0
MINOR: 8

No BLOCKER findings identified in this review. PR-009 is fixed: the plan and the spec now state the delivery-plan limit the way the `decompose` reader behaves. FR-010 now carries the same condition, so the requirement half of PR-008 is fixed, and PR-008 stays open only for the level-2 record. One new MINOR finding, PR-011, follows from the same edit. The plan's new sentence can be read as covering a repository with no tracker and no delivery plan, and research R1 still states the older, narrower limit. PR-003 through PR-007 and PR-010 are unchanged and still open.

## Findings

### PR-001: A reopened story with no `delivery.md` is sent to `decompose`, not to `implement`

- Priority: MAJOR
- Category: Requirement / Plan Mismatch
- Status: fixed
- Evidence:
  - `plan.md §Summary` item 2, second paragraph: names the routing with no `delivery.md`, says it is left as it is, and says the Story 1 and Story 4 tests carry a keyed `delivery.md`.
  - `plan.md §Test Plan` introduction: every test that expects `implement` to be current builds its feature with `KEYED_DELIVERY`. A row pins `decompose` as current with no `delivery.md`.
  - `spec.md §Edge Cases` and `spec.md §FR-010`: both now state the limit.
- Finding: Fixed in the earlier round and still fixed. This round's edits keep the routing and the fixtures the same.
- Why it matters: An implementer does not have to choose between the two behaviors.
- Suggested response: Fixed by `plan.md §Summary` and §Test Plan, `research.md §R1`, `spec.md §Edge Cases`, and `quickstart.md §Set up`.
- Corroborated by: requirements and traceability, adversarial implementation and verification

### PR-002: The snapshot row the plan names stops at `analyze`, so no verdict moves in it

- Priority: MINOR
- Category: Verification Gap
- Status: fixed
- Evidence:
  - `plan.md §Test Plan`, changed-tests row for `tasks-open-but-implemented` (unchanged): rebuilt from `_ANALYZED` plus a keyed `delivery.md`, and the new row `tasks-open-implemented-with-copy` is built the same way.
- Finding: Fixed in the earlier round and still fixed. Both rows reach the `implement` reader.
- Why it matters: The snapshot observes the change.
- Suggested response: Fixed by the changed-tests row.
- Corroborated by: adversarial implementation and verification

### PR-003: The fence rule departs from FR-004's wording and leaves nested tilde lines open to reading

- Priority: MINOR
- Category: Requirement / Plan Mismatch
- Status: open
- Evidence:
  - `spec.md §FR-004`: "The fence around the copy is one character longer than the longest fence inside it."
  - `264-the-task-copy-lives-in-the-completion-record.md §Decision`: "inside a fence longer than any fence in that text."
  - `research.md §R4` and `data-model.md §Completion record` (both unchanged): tildes, one longer than "the longest run of tildes that opens a fence line inside the copy", and at least four.
  - `wfctl/_md.py`, `closes_fence`: closes on any line of the same character, at least as long as the opener, with no info string, whatever block that line sits in.
- Finding: The planning artifacts still size the fence against tilde fences only, which differs from what the spec and the record say, and they do not label the difference. The phrase "opens a fence line" can also be read through a walk of the copy, which skips a `~~~~~~` line inside a backtick block. The reader's walk over the record does not track that inner block, so such a line closes the outer fence early and truncates the copy.
- Why it matters: A truncated copy reopens the step, which is the safe direction, but it breaks the round trip FR-004 and SC-005 require. The round-trip test the plan lists uses ```` ``` ````, `~~~`, and `~~~~` fences, and would not catch the nested case.
- Suggested response: Say that every line `_md.opens_fence` matches counts, read line by line rather than through a walk, or name the tilde-only rule as a deliberate departure. Add a `~~~~~~` line inside a backtick block to the round-trip test.
- Corroborated by: deterministic checks, adversarial implementation and verification

### PR-004: The new module and `_evidence.py` import each other

- Priority: MINOR
- Category: Boundary / Ownership Concern
- Status: open
- Evidence:
  - `plan.md §Summary` item 2: `_tasks_open` in `wfctl/_evidence.py` asks `_completion`.
  - `research.md §R3` (unchanged): which lines are tasks is decided on `quoted_out(text)`, which lives in `wfctl/_evidence.py`.
  - `plan.md §Structure Decision` (unchanged): `_completion.py` sits beside `_plan_review.py`, which imports nothing from `wfctl`.
- Finding: `_completion` needs `quoted_out` from `_evidence`, and `_evidence` needs `_completion`, so a top-level import in both directions is a cycle. The plan still does not say how it is broken.
- Why it matters: The implementer finds this on the first import. The choice decides whether `_completion` is a leaf like `_plan_review`, but no behavior depends on it.
- Suggested response: Name the dependency direction in `plan.md §Project Structure`, for example `_evidence` imports `_completion`, which receives the quoted-out text as an argument.
- Corroborated by: architecture and boundaries

### PR-005: Research R2's claim that matching by the first box "can only reopen the step" is not true

- Priority: MINOR
- Category: Assumption Challenge
- Status: open
- Evidence:
  - `research.md §R2` (unchanged): "A line holding two checkboxes counts once for matching, by its first box ... counting once can only reopen the step, never hide work."
  - `wfctl/_evidence.py`, `_task_tally`: counts every `[ ]` and `[x]` on a line.
- Finding: A new line whose first box is ticked and whose second box is incomplete, such as `- [x] T010 Ship A; [ ] follow-up B`, reads as ticked for matching, and the step stays closed. Such a line hides work, which contradicts the stated reason for the rule.
- Why it matters: No task list in the store writes two boxes on one line, so the practical risk is small. The claim is still a stated safety argument that does not hold, and a later change could rely on it.
- Suggested response: Read a line as incomplete when any of its boxes is incomplete, or correct the sentence in R2 so it names the case it does not cover.
- Corroborated by: adversarial implementation and verification

### PR-006: The plan does not say what the agent does when `wfctl step complete implement` refuses

- Priority: MINOR
- Category: Missing Information
- Status: open
- Evidence:
  - `plan.md §Summary` item 4 (unchanged): the command file tells the agent to run the command in place of writing the file at step 9b.
  - `wfctl/agents/skills/speckit-implement/SKILL.md` step 9b: still tells the agent to write the record by hand, and it is not edited.
  - `contracts/cli.md §Refusals`: four refusals, each exiting 1.
  - `spec.md §Edge Cases`, the delivery-plan bullet: a reopened story with no `delivery.md`, or with an unkeyed row, has `decompose` current, so under FR-003a the command refuses and names `decompose`.
- Finding: The command file's new text has no instruction for a refusal. The agent then holds two instructions: the wrapper's command, which failed, and the derived skill's step 9b, which writes the file by hand. Refusals at the end of an `implement` run are reachable, and the widened edge case adds the unkeyed-row route to them.
- Why it matters: A record written by hand has no copy, which the spec reads in the safe direction. Two agents can still act differently: one stops and reports, and the other falls back to step 9b and so bypasses the FR-003a guard.
- Suggested response: Add one sentence to the planned command-file change saying what the agent does on a refusal, for example stop and report the message, and say that writing the file by hand is not a fallback.
- Corroborated by: adversarial implementation and verification

### PR-007: The write path doesn't say it is atomic or that it reads `tasks.md` once

- Priority: MINOR
- Category: Risk / Failure Mode
- Status: open
- Evidence:
  - `264-the-task-copy-lives-in-the-completion-record.md §Consequences`: "One file is written in one step, so a record can never lose its copy."
  - `research.md §R6` (unchanged): the command calls `build_report`, which reads `tasks.md` through `build_evidence`.
  - `contracts/cli.md §Success`: the counts printed are the tally of the copy just written.
  - `wfctl/_io.py` provides `write_atomic`, which `step none` and `_verify` already use.
- Finding: The plan does not say the record is written with `write_atomic`, and it does not say that the position check, the copy, and the printed tally come from one read of `tasks.md`.
- Why it matters: A truncated record reads as one with no copy, or with an unclosed fence, so the step fails toward reopening. The level-3 record's guarantee depends on the write being atomic, and `_tasks_open`'s own docstring treats two reads of one file as a defect.
- Suggested response: State that the record is written with `write_atomic`, and that the command reads `tasks.md` once and uses that text for the copy and the tally.
- Corroborated by: security and reliability

### PR-008: The level-2 record still gives `/speckit.implement` with no exception

- Priority: MINOR
- Category: Requirement / Plan Mismatch
- Status: open
- Evidence:
  - `spec.md §FR-010` (changed): "When the `implement` step reads open under FR-005 or FR-007, for a feature whose `decompose` step reads done or skipped, the next command MUST be `/speckit.implement`."
  - `docs/architecture/new-task-reopens-implement.md §Decision` (unchanged): when wfctl finds new work, "it reopens the `implement` step and gives `/speckit.implement` as the next step".
  - `plan.md §Test Plan`, the row with no `delivery.md`: "`decompose` is current and the next command is `/speckit.decompose`."
- Finding: The requirement half of this finding is fixed. FR-010 now carries the condition the edge case and the Test Plan row rely on, and it matches the `decompose` reader, which reads `pending` with no delivery plan and `in_progress` with an unkeyed row whenever the tasks are open. The level-2 record still states the routing with no exception, so it now disagrees with FR-010 rather than agreeing with the old wording.
- Why it matters: The behavior is settled in the spec and the plan, so no implementer has to guess. The record is still proposed, and it is the text that will be read as the decision once it is accepted.
- Suggested response: Add one sentence to the level-2 record's §Decision or §Consequences naming the limit FR-010 now states.
- Corroborated by: requirements and traceability, architecture and boundaries

### PR-009: The recorded limit is narrower than what the `decompose` reader does

- Priority: MINOR
- Category: Assumption Challenge
- Status: fixed
- Evidence:
  - `plan.md §Summary` item 2, second paragraph: "skipped only while the tasks read closed" and "A delivery plan with an unkeyed row under a configured tracker does the same."
  - `spec.md §Edge Cases`, the delivery-plan bullet: the same two statements, and "`implement` becomes current once a delivery plan exists and either every row in it is keyed or the repository declares no tracker."
  - `wfctl/_evidence.py`, `decompose`: with no `delivery.md`, `skipped` when `ev.tasks_text and not ev.tasks_open`, `pending` otherwise. With a delivery plan and a configured tracker, an unkeyed row returns `in_progress` while `ev.tasks_open` is true.
- Finding: All three inexact statements are corrected in the plan and the spec. "While every task is ticked" became "while the tasks read closed", the unkeyed-row route is named, and the condition under which `implement` becomes current now names keyed rows or no tracker. Each statement matches the reader. Two residual issues in how the limit is stated elsewhere are filed as PR-011.
- Why it matters: A reader who sees `decompose` current on a feature with an unkeyed delivery plan now finds that case in the plan and the spec.
- Suggested response: Fixed by `plan.md §Summary` item 2 and `spec.md §Edge Cases`.
- Corroborated by: adversarial implementation and verification

### PR-010: The quickstart runs the installed wfctl, not the working tree

- Priority: MINOR
- Category: Verification Gap
- Status: open
- Evidence:
  - `quickstart.md` (unchanged): "Work in a scratch repository", then every command is `uv run wfctl ...`, and step 3 says "from the working tree".
  - Tool check in the earlier report: `uv run` outside a project falls back to the `wfctl` on `PATH`, which is the tool install and has no `step complete`.
  - `quickstart.md §Set up` step 1: points at the `spec_tree` fixture, whose `_default_body` writes `x` for a plan review, which does not clear `plan`.
- Finding: Run as written from the scratch repository, step 3 fails as an unknown command, and `status` and `next` report the old verdict. The set-up pointer also leads a reader to a plan review that holds the pipeline at `plan`.
- Why it matters: The spec's Validation Strategy requires both arms by hand, and the quickstart is the script for them. A reader following it sees the fix fail in both arms for reasons unrelated to the change.
- Suggested response: Name the invocation, for example `uv run --project <worktree> wfctl ...` run from the scratch repository, and point the set-up step at `REVIEWED` and `_ANALYZED` in the snapshot test.
- Corroborated by: adversarial implementation and verification

### PR-011: The delivery-plan limit is stated three ways across the plan, the spec, and research R1

- Priority: MINOR
- Category: Requirement / Plan Mismatch
- Status: open
- Evidence:
  - `plan.md §Summary` item 2, second paragraph: "That holds for a feature whose delivery plan has every row keyed, or whose repository declares no tracker."
  - `spec.md §Edge Cases`, the delivery-plan bullet: "a delivery plan whose rows are all keyed, or a delivery plan in a repository that declares no tracker."
  - `research.md §R1` (unchanged): "That claim holds for a feature with a delivery plan."
  - `wfctl/_evidence.py`, `decompose`: with no `delivery.md`, it reads `pending` whenever the tasks are open, whatever the tracker.
- Finding: The plan's new sentence reads as two separate conditions, and the second, "whose repository declares no tracker", needs no delivery plan. Read that way, a repository with no tracker and no `delivery.md` sends a reopened story straight to `implement`, which the next sentence of the same paragraph and the `decompose` reader both contradict. The spec says it exactly, since it attaches the no-tracker case to a delivery plan. Research R1 still carries the narrower claim PR-009 named, "a feature with a delivery plan", which the plan and the spec no longer make.
- Why it matters: The tests are safe, since every fixture that expects `implement` carries `KEYED_DELIVERY`. The risk is the one PR-009 named. A reader of the plan or of R1 who sees `decompose` current in a repository with no tracker, or on a feature with an unkeyed delivery plan, may conclude the fix failed.
- Suggested response: In `plan.md §Summary` item 2, say "a feature whose delivery plan has every row keyed, or has a delivery plan in a repository that declares no tracker", the spec's wording. Bring the first sentence of the second paragraph of `research.md §R1` to the same wording.
- Corroborated by: deterministic checks, requirements and traceability

## Requirement-to-plan trace

| Requirement / criterion | Plan location | Review note |
| --- | --- | --- |
| FR-001 | plan.md §Summary item 3; contracts/cli.md §Success; Test Plan row "writes the record with a copy" | covered; PR-007 |
| FR-002 | contracts/cli.md §Refusals; Test Plan row `step complete plan` | covered |
| FR-003 | contracts/cli.md §Refusals; Test Plan row "no `tasks.md`" | covered |
| FR-003a | research.md §R6; Test Plan rows "while `analyze` is current" and "every box ticked" | covered; PR-006 |
| FR-004 | research.md §R4, §R5; Test Plan round-trip row | covered; PR-003 |
| FR-005 | plan.md §Summary item 2; data-model.md §New work | covered; PR-005 |
| FR-006 | research.md §R2, §R3; data-model.md §Task | covered; PR-005 |
| FR-007 | data-model.md table; Test Plan rows for a record with no copy | covered |
| FR-008 | data-model.md table; Test Plan row for a task list with no task | covered; PR-006 |
| FR-009 | research.md §R3; Test Plan row "task inside a code example" | covered |
| FR-010 | research.md §R1; Test Plan row with a definition of done; Test Plan row with no `delivery.md` | covered, including the new condition on `decompose`; PR-008, PR-011 |
| FR-011 | plan.md §Summary item 4; Test Plan row in `test_skill_cross_references.py` | covered; PR-006 |
| FR-012 | plan.md §Technical Context, Constraints | covered by construction, inspected rather than tested |
| FR-013 | Test Plan row "No definition of done, copy with T001 ticked", with a keyed `delivery.md` by the Test Plan introduction | covered |
| SC-001 | Test Plan rows for both configurations; quickstart.md | covered in the suite; PR-010 for the quickstart |
| SC-002 | Test Plan row for FR-013 | covered |
| SC-003 | Test Plan row for the three ordinary edits | covered |
| SC-004 | Test Plan rows for the three record shapes and `decompose` | covered |
| SC-005 | Test Plan round-trip row | covered; PR-003 |
| Edge case: delivery plan | plan.md §Summary item 2; research.md §R1; Test Plan row with no `delivery.md` | covered for no `delivery.md`; the unkeyed-row route is stated and left as it is, with no test, as the spec says; PR-011 |

## Assumptions challenged

- `implement` becomes current once a delivery plan exists and every row is keyed or no tracker is declared (spec Edge Cases). That is one sufficient condition, not the whole set. A delivery plan with no Issue Grouping Map, or a map with no rows, makes `_unkeyed_issues` return `None`, and `decompose` reads `done`. That route also reaches `implement`, so it never puts `decompose` in front of a reopened story, and it is noted here rather than filed.
- FR-010's condition names `decompose` reading done or skipped. With no delivery plan, `decompose` reads `skipped` only while the tasks read closed, and FR-010 applies only while they read open. So the reader never produces the `skipped` arm together with FR-010's trigger. The arm does no harm, and it covers a `skipped` that comes from elsewhere.
- The rebuilt snapshot row's "verdict moves from finished to `implement` in progress" (plan §Test Plan, unchanged). Carried from the earlier report. The committed JSON never held the finished verdict for that row, since today it stops at `analyze`, so a fixture rebuild and a reader change in one commit show a different move.
- The completion record takes the agent out of judging its own work (`plan.md §Constitution Check`, Ownership). Carried from the earlier report. The agent still decides when to run the command, and the spec accepts this under its tamper edge case.
- `build_report` writes nothing (research R6). Carried from the earlier report, and not re-verified line by line.

## Reviewer disagreement

- None identified.

## Strengths worth preserving

- The limit is pinned by a test rather than left as prose, and FR-010 now names it, so a later change to the `decompose` reader that sends a reopened story straight to `implement` fails that row and has to update the requirement on purpose.
- The plan's corrected paragraph states the unkeyed-row route and widens the set of features it reaches to include one in this store, rather than keeping the earlier claim that only new features and other repositories meet it.
- The Test Plan introduction names one fixture, `KEYED_DELIVERY`, for every test that expects `implement` to be current, so the Story 1 and Story 4 tests can't pass or fail on whether an individual fixture happened to write a delivery plan.
- Research R6 checks pipeline position through `build_report`, the one inference every view renders, rather than `_infer_steps`, so a host-block hold and a pass hold are counted.

## Source freshness

This review describes only the content identities listed under `## Reviewed inputs`. When `spec.md`, `plan.md`, a binding design record, or a material planning artifact changes, this report no longer describes the current plan, and a new review is needed before it counts as current evidence.
