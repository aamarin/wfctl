# Research: Design exceptions move to the spec folder

Each entry was checked against the code on `635-arch-folder-per-branch-notes`
at 8e147f7.

## R1. Where the commands find the spec folder when it doesn't exist yet

**Decision**: A new `_paths.feature_dir(branch, repo_root)` returns
`resolve_spec_dir(branch, repo_root)` when that finds a folder, and
`spec_root(repo_root) / branch` otherwise. `feature_paths_cmd` already computes
exactly this inline at `cli.py:1871`, so it moves into the helper, and
`arch none`, `step none`, and `feature-paths` all call it.

**Rationale**: `resolve_spec_dir` returns `None` until the folder exists, so a
command that runs before `design.md` has nowhere to write. `feature-paths` is
what `/speckit.brainstorm` uses to name the folder it creates. If the exception
commands computed the path differently, an exception written before brainstorm
would land in a folder brainstorm then ignores.

**Alternatives considered**:

- `spec_root / Path(branch).name`, as the old writers used for the arch root.
  We didn't choose it because a branch containing `/` would then put the exception
  in a different folder from the one `feature-paths` creates and
  `resolve_spec_dir` finds. `Path(branch).name` guarded a write into a
  committed tree against a `..` segment. Git rejects `..` in a branch name, so
  only `WFCTL_BRANCH` can carry one, and `feature-paths` already accepts that
  risk for the same folder.
- Refuse when no spec folder exists. We didn't choose it because `arch none`
  is often the first thing a branch writes, before `design.md`, and the spec
  requires the command to create the folder (FR-003).

## R2. The exception file's format

**Decision**: `_design_exceptions.write(spec_dir, name, reason)` writes
`# <title>\n\n<reason>\n`. The title is "No new boundary" for `boundary` and
"`<step>.<pass>` does not apply" for a pass. The readers keep everything after
the first blank line, which is what `_step_claims` does today.

**Rationale**: The header gives a person opening the file a one-line answer.
The branch name the old headers carried is dropped, since the spec folder is
already named for the branch. The parser is unchanged, so `_design_exceptions` holds the
writer and the parser side by side (`design-exceptions-module.md`).

**Alternatives considered**: Frontmatter with a `reason:` field. We didn't
choose it because nothing reads a field other than the reason, and a reason
with a colon or a newline would need quoting that the plain body avoids.

## R3. How the brainstorm gate counts the boundary exception

**Decision**: `_architecture_answered` keeps its `spec.md` escape, then returns
`None` (answered) when `_design_exceptions.boundary(spec_dir)` is not `None`, and only
then asks git whether a record was touched.

**Rationale**: The exception check reads one file and needs no git call. Checking
it first also means an exception answers the question when git can't, which is the
case `touched_on_this_branch` returns `None` for. Today that case blocks as
`inconclusive`, and a branch with a boundary exception has given an answer that
doesn't depend on git.

**Alternatives considered**: Check git first and the exception second. The result
is the same except when git can't answer, where it would hold a branch that
already answered.

This is the second case where the gate's result changes on purpose, beside the
old declaration in story 4. SC-003 names both, and a gate test pins each one
(R8 item 9).

## R4. How `declarations/` stops counting

**Decision**: A `DECLARATIONS_DIR = "declarations"` constant joins
`non_record_subtrees` in `_paths.py`. `STEP_CLAIMS_DIR` is removed from the
list and from the code.

**Rationale**: Today the gate counts a declaration only because it's a file
under the arch root that no exclusion covers. Adding the folder to
`non_record_subtrees` stops the gate counting it, and also stops the two other
readers of that list (`records_on_this_branch` in `cli.py:764` and the
"architecture accepted" fact in `_evidence.py:1085`) from reading a stale
declaration as arch-root activity. FR-007 requires this.

`STEP_CLAIMS_DIR` would only guard against a step claim written by wfctl 0.23.0,
the release on PATH today. Once this change ships and the tool is upgraded,
nothing writes there. The gap is the time between merge and upgrade, when an
old step claim could release the gate. We accept that while wfctl has one user,
and the release note says to upgrade before writing an exception.

Removing the exclusion has one side effect on this branch only. This branch
deletes the 5 files under `step-claims/`, and once that folder isn't excluded,
the deletion counts as arch-root activity. So `records_on_this_branch`
(`cli.py:763`) prints a `record: plan.plan-walkthrough` line in an unattended
`wfctl status` here, though no record was decided. We accept it, since no
other branch deletes those files and the line goes away once this branch
merges.

**Alternatives considered**: Keep `STEP_CLAIMS_DIR` in the list. We didn't
choose it because it keeps the old folder name in the code to cover a version
only one user runs, for the few days until they upgrade.

## R5. What happens to the not-in-the-diff check

**Decision**: `arch none` drops its `touched_on_this_branch` check and
`step none` drops its unlink-and-refuse block. Both end with
"Put the reason in the PR body." `_refuse_unseen` stays, since
`step sign-off` still calls it.

**Rationale**: The spec folder is never part of the diff, so the check would
fire on every run. The reviewer's copy now comes from the PR section, which
`check-body` checks (`design-exceptions-live-with-specs.md`).

## R6. The session summary's Boundary line

**Decision**: `_observe` takes `spec_dir` from its caller, `end_cmd`, which
already resolves it at `cli.py:1273`. It reads "answered" when
`spec_dir` is set and `_design_exceptions.boundary(spec_dir)` is not `None`, and
otherwise maps `touched_on_this_branch` as it does today (FR-014).

**Rationale**: The summary and the pipeline then use the same two inputs. The
summary doesn't apply the gate's `spec.md` escape, because the Boundary line
records whether the question was answered, not whether the gate is still up.

**Alternatives considered**: Call `_architecture_answered` directly. We didn't
choose it because that function returns `None` for "answered" and for "past
the gate", and the Boundary line would then read "answered" on every branch
past specify, whether or not anyone answered.

## R7. The pipeline's pass-claim reader

**Decision**: `_step_claims(repo_root, branch)` is deleted. `_pipeline.py:393`
calls `_design_exceptions.passes(spec_dir)` when `spec_dir` is set and uses `{}`
otherwise.

**Rationale**: `step none` now creates the spec folder, so a pass exception with no
spec folder can't exist. The no-spec-folder arm keeps its shape, passing an
empty mapping.

## R8. Which tests change

**Decision**:

1. New `tests/test_design_exceptions.py` for the module's four functions.
2. `tests/test_step_none.py`: the two not-in-the-diff tests
   (`test_a_claim_no_reviewer_can_see_is_not_left_on_disk`,
   `test_a_refused_claim_does_not_settle_the_pass`) are replaced by one test
   that an exception lands in the spec folder with an out-of-tree arch root. The
   path assertions move to the spec folder.
3. `tests/test_pipeline_commands.py`: the `arch none` tests at lines 364 - 400
   and 512 - 553 assert on `declarations/` and on the old refusal. They move
   to the spec folder and the new success line.
4. `tests/test_arch_records.py:476` asserts a declaration stays out of the
   record set. It stays, since an old declaration on disk still mustn't read as
   a record.
5. `tests/test_design_gate_drawing.py` runs `arch none` and asserts on the
   gate. Those tests keep passing unchanged, which checks SC-003 for every
   case except the two item 9 pins.
6. `wfctl/_contract.py`'s `nested` fixture writes its exception through
   `_design_exceptions.write`.
7. `tests/test_skill_cross_references.py:204`'s docstring names
   `declarations/<branch>.md`, and is updated.
8. `tests/test_warnings_after_gate.py:271` writes a step claim under the arch
   root by hand and calls `_infer_steps`. It writes the exception through
   `_design_exceptions.write` instead, so no test builds an exception path
   itself (FR-009). The docstrings at `tests/test_pipeline_state_names.py:318 -
   324` and `tests/test_declared.py:90 - 91` describe `_step_claims` and
   `step-claims/<branch>/`, and are rewritten for `exceptions/`. So is the
   docstring at `tests/test_pipeline_commands.py:341`, which explains its test
   by `step-claims/`.

   `tests/test_paths.py` imports `STEP_CLAIMS_DIR` at line 12, so the whole
   module stops collecting once the constant goes.
   `test_non_record_subtrees_names_step_claims` at line 1005 asserts the
   constant is in `non_record_subtrees`. It's replaced by a test asserting
   `DECLARATIONS_DIR` is in the list, which keeps the same reason: a fourth
   reader of the arch root inherits the exclusion from one place.
9. Two new gate tests, one per deliberate change in SC-003:
   1. A branch with `design.md`, a boundary exception, and git unable to answer
      reads answered. Today the same branch with a declaration reads
      `inconclusive` and holds.
   2. A branch with `design.md` and only an old declaration under
      `declarations/` reads unanswered (story 4, scenario 2).
10. One CLI test per acceptance scenario the existing tests don't reach:
    1. Scenario 1.2, in `tests/test_pipeline_commands.py`: `arch none` on a
       branch with no spec folder creates the folder and the exception, and
       brainstorm is still the current step. The test also pins that
       brainstorm's state changes from `pending` to `in_progress`, because
       once the folder exists, brainstorm reads its own state as `done` and
       rolls up to `in_progress` behind the `design-doc` pass.
    2. Scenario 1.3, in `tests/test_pipeline_commands.py`: a second `arch none`
       replaces the first reason.
    3. Scenario 2.2, in `tests/test_step_none.py`: `step none` on two passes
       and `arch none` once, then `wfctl status --json` reports exactly the two
       passes as claimed and never `boundary`. This is also the verification
       `design-exceptions-module.md` names.
11. Two tests for epic sub-issues (R11), in `tests/test_design_exceptions.py`
    or beside the `resolve_spec_dir` tests in `tests/test_paths.py`:
    1. A sub-issue branch with no folder of its own, listed in the epic's
       `delivery.md`, reads the epic's boundary exception and pass exceptions.
    2. The same sub-issue with its own spec folder reads no exceptions.

## R9. Which skill and doc text changes

**Decision**: The lines below name the old location or the gate's old reading,
from `grep -rn "declarations\|step-claims\|arch none\|step none"`:

1. `wfctl/agents/skills/design-levels/SKILL.md:204`, which says the command
   writes `declarations/<branch>.md` and that the gate reads it.
2. `wfctl/agents/skills/model-the-domain/SKILL.md:203`, "it writes one
   declaration".
3. `wfctl/agents/skills/writing-a-scan-file/SKILL.md:40`, which names
   `<root>/declarations/` as named for the issue key.
4. `wfctl/agents/skills/opening-a-change/SKILL.md` Step 4, which gains one
   bullet telling the agent to copy the branch's design exceptions from the
   spec folder into the PR body. It names no section, because the skill says
   it "does not carry a section list of its own, and must never grow one". The
   PR template's comment under "Moves a boundary?" says what goes there, the
   same way the "Needs a spec?" comment does (FR-013).
5. `AGENTS.md:174` and `AGENTS.md:287 - 291`.
6. `README.md:107`, checked and left alone if it names no path.
7. `wfctl/cli.py:7507` and `_declared.py:139`, comments that name the old
   folders.
8. The docstrings of `arch_none_cmd` (`cli.py:2013 - 2025`) and
   `step_none_cmd` (`cli.py:2124 - 2130`). Typer prints them as `--help`, and
   both say the file lands in the change under review for a reviewer to read.
   They're rewritten to say the exception goes in the spec folder and the
   reason goes in the PR body.
9. `wfctl/agents/skills/architecture-design/SKILL.md:69 - 71`, "The command is
   how the absence becomes an artifact a reviewer opens". The reviewer now
   reads the PR body, not the file, so the line changes.
10. `docs/architecture/an-absent-artifact-is-claimed-not-inferred.md`. Its
    Decision paragraph was updated on this branch, but three passages still
    say the claim is committed to the branch and reaches the reviewer:
    §Decision ("writes a committed sentence into the change under review"),
    §Owns truth ("a sentence committed to the branch", "that it reached the
    reviewer"), and §Considered ("`specs/` is gitignored ... so the claim
    reaches no reviewer"). All three are rewritten to match
    `design-exceptions-live-with-specs.md`. Both records are `proposed`.

`speckit-brainstorm`, `design-passes`, and `commands/speckit.brainstorm.md`
name the command and not the path, so they stay unless the text says where the
file goes. None of these skills is Spec Kit-derived.

Items 1, 4, and 8, plus the PR template comment (`contracts/cli.md`), are the
text that names the exceptions folder. SC-004's "one edit in one module" covers
wfctl's code. A later move of the folder also updates these texts.

## R10. What happens to the existing step claims

**Decision**: The 5 files under `step-claims/` move by hand, once, into
`exceptions/` in each branch's spec folder, rewritten in the new format. No
migration code ships.

**Rationale**: All 5 are plan walkthrough sign-offs for branches that merged,
so nothing reads them. They're kept because they record who decided to skip
each walkthrough and why. Every target spec folder exists in the local spec
root:

1. `359-push-specs-to-trunk`, `40-save-uncommitted-on-remove`, and
   `571-release-automation` are already stored on `specs-trunk`.
2. `264-sentinel-goes-stale` and `293-mirror-below-recorded-dir` aren't stored
   yet, so storing them adds those two folders to `specs-trunk`.

The old header names the branch (`# plan.plan-walkthrough does not apply — 571-release-automation`).
The new format drops it, since the folder already names the branch, so each
file is rewritten through `_design_exceptions.write` rather than copied.

`wfctl store specs` stores only the current branch's spec folder. So each of
the 5 is stored by running `WFCTL_BRANCH=<branch> wfctl store specs` once per
branch. For 264 and 293, that pushes their whole spec folders to `specs-trunk`
for the first time. Each run pushes, so the user is asked before the first
one.

**Alternatives considered**: Delete them, as the first plan did. We didn't
choose it because it loses the reasons for 5 skipped walkthroughs, and moving
them costs one step. Migration code that moves them on first run was rejected
too, since there are 5 files in one repo.

## R11. Exceptions on an epic's sub-issues

**Decision**: An epic's sub-issues share the epic's spec folder, so they share
its exceptions too. A sub-issue that adds an architecture record keeps sharing
the folder, and the record answers the boundary question for that sub-issue,
whatever the epic's answer says (R13). A sub-issue that needs different pass
exceptions, or a plan of its own, gets its own spec folder, named after its
branch. wfctl checks for that folder first, so the sub-issue stops sharing and
starts with no exceptions. No code changes for the sharing itself.

**Rationale**: `resolve_spec_dir` looks for a folder named after the branch
first. When it finds none, it falls back to the one feature whose `delivery.md`
lists the branch's issue (`_paths.py:854-867`). So a sub-issue with no folder of
its own reads and writes the epic's `exceptions/`.

For example, epic #700 is split into #701 and #702, and only
`700-review-records/` exists:

1. `exceptions/boundary.md`: no new boundary, since the epic reuses the
   existing review store.
2. `exceptions/plan.plan-walkthrough.md`: the maintainer skipped the
   walkthrough for #700.

Branches `701-record-format` and `702-record-reader` both see the boundary
answered and the walkthrough skipped. That's correct for both. The epic's
brainstorm answered the boundary question once for the whole feature, and the
walkthrough covered the plan both sub-issues are cut from.

If #702 needs a new boundary, it writes the record on its own branch and keeps
the epic's folder. The record is committed on `702-record-reader`, so it's
already separate from #701 and from the epic, and the guard holds #702's PR
until a person accepts the record (R14). #701 still reads the epic's "no new
boundary", which is still true for #701.

If #702 needs its own plan or different pass exceptions, the user creates
`702-record-reader/`. wfctl finds that folder first, so #702 stops sharing and
starts with no exceptions, while #701 keeps using the epic's folder.

The cost is that an exception written from one sub-issue applies to its
siblings too. For example, if #701 skips a pass, #702 reads that pass as
skipped. That's acceptable because a sub-issue whose answers differ from its
siblings is the case that gets its own folder. Nothing warns about this when
the exception is written, and we didn't add a warning, since every sub-issue
shares the folder on purpose and a warning would fire on every write from one.

A sub-issue's own spec folder replaces the epic's for every artifact, not only
the exceptions. #702 with its own folder no longer reads the epic's `spec.md`,
`plan.md`, or `tasks.md`, so its pipeline starts again at brainstorm. That's
the existing behavior of `resolve_spec_dir` and this change doesn't alter it.
It's the right cost for a sub-issue that needs its own plan, since that
sub-issue needs its own design too.

**Alternatives considered**:

- A folder per branch under the epic's folder, such as
  `700-review-records/exceptions/701-record-format/`. We didn't choose it
  because every sub-issue would have to answer the boundary question again,
  even though the epic's brainstorm already answered it for all of them.
- The same subfolder, written only by a sub-issue whose answer differs from the
  epic's, with wfctl reading the sub-issue's answer first. The plan walkthrough
  on 2026-10-26 raised this for a sub-issue that adds a record. We didn't
  choose it because the record already answers the question for that
  sub-issue, and git already keeps the record apart from its siblings. The
  subfolder would hold a second copy of an answer git already has.
- Updating the epic's shared answer when one sub-issue adds a record. We didn't
  choose it because the answer would then be wrong for every other sub-issue.

## R12. The PR body carries every exception's reason

**Decision**: `check-body` gains a fourth source, `_exception_findings(body)`.
It resolves the branch's spec folder and reads every exception in it through
`_design_exceptions.boundary` and `_design_exceptions.passes`. For each
exception whose reason doesn't appear in the PR body, it prints one finding.
The comparison collapses runs of whitespace in both texts first, so a reason
rewrapped across lines still matches.

One boundary exception is skipped. When the spec folder is an epic's folder
the sub-issue inherited (R11), and the branch touches a level-2 record, the
epic's "no new boundary" reason isn't compared. "Inherited" uses the same test
as R13: the folder isn't named after the branch. The records are the ones
`_evidence._branch_records` returns, since `check-body` runs in the working
tree and can import `_evidence`. Without the skip, a sub-issue whose PR body
answers yes and names its record would have to quote the epic's "no" to pass.
The epic's answer stays true for the other sub-issues, so their bodies still
carry it.

**Rationale**: The gate reads the spec folder's copy and the reviewer reads the
PR body's copy. Before this, nothing compared them. `opening-a-change` copies
the reasons into the body (FR-013), so the check fails only when the agent
skipped the copy, or when one copy changed after the other was written.

The check needs no section name. It looks for the reason anywhere in the body,
so wfctl still names no heading (FR-011). As a result, the check also runs in a
repo that doesn't list "Moves a boundary?". That repo still gets the reviewer's
copy, since `opening-a-change` copies the reasons whatever `change_sections`
lists. Previously, the level-2 record accepted that such a repo loses the
reviewer's copy, and this closes that gap.

When the two copies disagree, `opening-a-change` tells the agent to work out
which one is wrong from the code, the plan, and the domain model. In an
attended session it recommends which copy to fix, and the user decides. In an
unattended run it fixes the wrong copy and carries on. The fix is clerical,
since the design question was already answered once.

**Alternatives considered**:

- Read the "Moves a boundary?" section and compare it with the spec folder. We
  didn't choose it because wfctl would have to name the heading, which
  `_sections.py` rules out.
- Run the comparison in the worktree guard. We didn't choose it because the
  guard sees the `gh pr create` command, not always a body file, and a mismatch
  between two copies of the same answer isn't worth refusing a PR over.

## R13. A record contradicts the branch's own "no new boundary"

**Decision**: The worktree guard refuses `gh pr create` and `gh pr merge` when
two things are both true:

1. The branch's own spec folder holds a boundary exception. "Own" means the
   folder is named after the branch, so an exception inherited from an epic
   (R11) doesn't count.
2. The branch touches a level-2 architecture record, using the same set of
   records the gate and the "architecture accepted" fact read.

The refusal names the record and prints the command that deletes the
exception. The record then answers the boundary question.

**Rationale**: The gate reads the boundary exception before it asks git about
records (R3). So an agent that writes "no new boundary" early and adds a record
later passes the gate with a wrong answer, and the agreement check in R12 can't
catch it if both copies say the same wrong thing.

The answer can go wrong at any point after brainstorm, including during
implementation. A plan review would see only a plan that adds a boundary, not a
record added while the code is written. So the check runs when the PR opens,
which is the last point before a reviewer reads the answer.

An inherited exception isn't a contradiction. The epic's answer stays true for
the other sub-issues, and the sub-issue's record answers the question for that
sub-issue.

The guard reads the records at the commit the command acts on, through git,
not from the working tree. `gh pr merge` from the `main` checkout judges a
branch that isn't checked out, so the working tree there holds the wrong
records. Like the review check, any error refuses the command.

**Alternatives considered**:

- Report the contradiction in `check-body` only. We didn't choose it because
  nothing but the author runs `check-body`, and an unattended run that skips it
  would open the PR with the wrong answer.
- Have the gate stop reading the exception once a record exists. The gate does
  that already in effect, since either one answers it. It doesn't fix the
  wrong answer the reviewer reads.

## R14. An unaccepted record holds the PR

**Decision**: The worktree guard refuses `gh pr create` and `gh pr merge` while
any level-2 record the branch touches has a status outside
`accepted`, `superseded`, `rejected`, and `retired`. That's the same rule as
the "architecture accepted" fact in `_evidence.py`, and the guard reads the
records at the commit the command acts on, as in R13.

**Rationale**: Previously, a record the branch added showed as an unmet fact in
`wfctl status`, and nothing else. An unattended run could open and merge a PR
whose boundary nobody approved.

An unattended run intends the agent to make the design call. So the agent
writes the record, with its rejected alternatives and trade-offs in
`Considered`, and keeps working. The person reads the trade-offs and accepts or
rejects the record before the PR opens. The `architecture-decisions` checklist
requires `Considered` to carry at least one real alternative with the reason it
lost, so the person has more than the agent's choice to go on. `wfctl arch
accept` doesn't check that section, so the checklist is the only thing that
asks for it.

The rule is scoped to the branch, like the fact. A proposed record already on
`main` holds a PR only when the branch edits it. An edit counts because it can
change a decision as much as a new record can, and the design gate's
`added_only` rule exists for a different reason: it keeps newer drawing rules
from holding a branch that touches an old record.

The cost is that every branch that adds or edits a proposed record waits for a
person before its PR opens, this one included. This PR waits on two proposed
records: its own `design-exceptions-live-with-specs.md`, and
`an-absent-artifact-is-claimed-not-inferred.md` from #339, which this branch
edits. Its level-3 record under `design/` doesn't hold the PR, since the guard
reads only level-2 records.

A record held as proposed on purpose, until it is validated end to end, holds
any branch that edits it until it is accepted. So an edit to one of those
records belongs on the branch that validates it, unless that branch is already
closed. #339 is closed, so the edit stays on this branch. Moving it to a
follow-up branch would leave `main` describing a folder this branch removes,
and the follow-up would wait on the same record.

**Alternatives considered**: Hold only the merge, not the PR. We didn't choose
it because the person then reviews the record after the agent has asked for a
review of the code built on it, which leaves little room to reject it.

## R15. An attended session pauses when a record is written

**Decision**: `architecture-decisions` gains one step. When the agent writes a
record on a branch that has a boundary exception, own or inherited, it reads
`auto_approve` from `wfctl status --json`. When `auto_approve` is false, the
agent stops after writing the record as `proposed`, tells the user, and waits
for them to accept or reject it before building anything on it. When it's
true, the agent finishes the record's `Considered` section and carries on, and
R14 holds the PR.

**Rationale**: A review that happens only when the PR opens comes after the
code is built on the choice. Rejecting the record then means redoing the work,
so the person is pushed toward accepting it. Pausing when the record is
written lets the person reject it before anything depends on it.

The pause is skill text, not a check. Nothing enforces it, but R14 catches an
agent that skips it, since the PR can't open until the record is accepted.

`architecture-decisions` is wfctl's own skill, not Spec Kit-derived, so the
edit isn't reverted by an upstream pull.

**Alternatives considered**: A hook that refuses writes under the arch root on
a branch with a boundary exception. We didn't choose it because it would also
refuse the record the person asked for, and R14 already enforces the part that
matters.
