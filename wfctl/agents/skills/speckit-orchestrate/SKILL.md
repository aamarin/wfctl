---
name: 'speckit-orchestrate'
description: 'Read pipeline state after a speckit step completes, then auto-advance or surface the next command based on the step auto flag.'
---

## Steps

0. **Session gate** — before anything else, including the spec lookup below.

   Run `wfctl status --json` and read `session_started`. If it is `false`:
   - Display: "No wfctl session for this branch. Run `/start-session` first."
   - Stop.

   Stop the same way if the command exits non-zero or the payload carries no
   `session_started` at all, displaying what it printed. A gate that proceeds
   on a missing answer is not a gate, and the missing answer is the likelier
   failure: outside a git repo `status` exits 1 before it prints a payload.

   Stop means stop: no checks, no analysis, no recommendation offered first. A
   run that reaches a conclusion here leaves it in scrollback and nowhere else.
   `wfctl start` is what opens the event log every later view reads, so without
   it `/end-session` has no run to summarize and the next session on this branch
   reads an empty state dir and reports "first session on this branch" — true of
   the state dir, false of the branch (#117).

   **What this catches is a branch's first session, not every session.**
   `session_started` is true once any `start` event exists in the log and
   nothing ever clears it, so a later conversation that skips `/start-session`
   on a branch that has already had one walks straight through this gate. Do
   not read the check as proof that a session is open now. Closing that gap
   needs a per-session identity the state dir does not carry (#200), and the
   six skills that invoke this one as their *last* step meet the gate after
   their work is done rather than before it (#201).

   Name `/start-session`, not `wfctl start`. Both clear this check; only the
   first also refreshes the skills mirror, loads the architecture contract and
   reads the handoff. And do not run either one yourself to clear your own
   gate: opening a session is `/start-session`'s job, and doing it from inside
   a read hides from the user that the step was skipped.

1. **Sub-issue scoping** — after `wfctl` has resolved the spec dir, not instead
   of it.

   `resolve_spec_dir` does the `delivery.md` key scan itself since #120: exact
   branch dir, then key glob, then the feature whose Issue Grouping Map names
   this branch's issue key. That is the whole list — ancestry was a fourth leg
   until #263 and is not one now (`a-branch-is-claimed-not-inherited`), because
   where a worktree was cut from is the same fact whether the base was chosen or
   mistyped. This step no longer hand-rolls that search.

   **The failure mode to watch is a false positive, not a false negative.** This
   step used to warn that resolution "can report 'no spec dir found' and default
   to `brainstorm`" — loud, obviously wrong, harmless. What actually bit was the
   opposite: the ancestor leg returned a *different* feature's dir, and `wfctl
   status` reported that feature's `46/46 done — open PR` on work that had not
   begun. Quiet, plausible, and it says ship it.

   Which means: **`(no spec dir found)` is now an answer, not a gap to close by
   guessing.** Read `spec_dir` off the payload the gate above already fetched —
   `null` there is the resolver saying no feature claims this branch. Do not go
   looking for one, and do not re-run `status` for it.

   It has one remedy, and it is a command rather than a search: a sub-issue of
   an epic is claimed by that epic's Issue Grouping Map, which
   `/speckit.decompose` writes. Until the epic has decomposed, nothing claims
   the branch and `null` is the correct answer — say that, rather than treating
   it as a lookup that failed.

   A resolved dir whose key is not this branch's is now one thing only: an epic
   whose grouping map names this issue. That is a claim somebody wrote, so its
   task counts are the epic's and the scope below is yours to apply.
   **Compare the two issue keys, never a key against a directory name.** Take
   the leading key off `spec_dir`'s basename and the leading key off the branch,
   and compare those:

   ```
   branch 120-spec-dir-ancestor-is-foreign
   spec_dir  .../wfctl-specs/120-spec-dir-ancestor-is-foreign

     "120-spec-dir-ancestor-is-foreign" vs "120"   → differ   ✗ wrong: every
                                                                own feature
                                                                reads claimed
     "120" vs "120"                                → same     ✓ owned
   ```

   Same key means the branch owns the feature — stop here, the steps below are
   not for it. Different keys mean an epic claimed it, and then:
   - Its `delivery.md` row for this issue key carries the `Tasks` range. That is
     this sub-issue's scope; spec/plan/tasks/decompose are done at the epic
     level.
   - For a GitHub-backed repo, `gh pr list --head {current-branch}` is a cheap
     non-blocking nicety — an open/merged PR means the sub-issue is past
     `implement`; report that instead ("PR #N open, awaiting review" / "PR #N
     merged — story complete"). Skip this check for other trackers; the six
     standard verbs don't include a by-branch change lookup.
   - No PR found (or non-GitHub tracker) → next command is `/speckit.implement`
     scoped to that task range, not `/speckit.brainstorm`.

2. Run `wfctl status` and display the output so the user can see the updated pipeline position.

3. Run `wfctl resume`. It re-infers the step and records the advance — neither
   of which the read below does.

   **If it exits non-zero, display its output and stop.** A read that follows a
   command which failed is a read of a state nobody established.

   You are not compensating for a gate here. A step whose evidence does not
   satisfy it reports that in the payload step 4 reads — the reason lands on the
   step, and `next_command` names what unblocks it rather than what the gate
   would refuse. `resume` and `status` are two renderings of one inference, so
   there is no answer step 3 has that step 4 lacks.

4. Run `wfctl status --json` and read `next_command`, `auto` and `stall` off the
   payload, and the current step's `reason` and `remedy` with them.
   Not `$(wfctl state-dir)/next-step.md`: that file is written once per
   `resume`/`next` and holds whatever was true then, observed 2.5 hours stale
   during #114. `--json` re-derives from the artifacts on disk at the moment
   you ask. Nor step 0's payload: `resume` ran between the two reads, which is
   the whole reason this one is taken again.

5. Branch on the result:

   **`stall` is not `null`** — check this before `auto`, and stop:
   - Display: "Stopped — `{stall.step}` ran {stall.passes} times and changed
     nothing." Then, under it, `unchanged` as a list, and one line saying this
     needs a person because re-entering the step has not moved the work.
   - Stop. Do not emit `EXECUTE_COMMAND`.

   Ahead of the `auto` branch, and that order is the whole of it: a stalled run
   has `auto: true` and a `next_command` naming the step that just failed to make
   progress, so reading `auto` first sends the loop back into it — which is the
   defect (#332), not a state to recover from.

   You are not deciding this. wfctl counts the passes, from the event log
   `wfctl resume` writes one line into per pass; the payload carries the verdict
   and this step renders it (`wfctl-counts-the-passes`). Do not keep your own
   tally of which command you emitted last, and do not treat the absence of
   `stall` as a reason to start one — a conversation cleared or compacted
   mid-run loses a tally like that at exactly the moment the bound is for.

   **A stall is not a blocked step**, and the two are told apart by which field
   carries the answer. A `reason` names something re-entering the step can fix
   once someone supplies it; a stall says re-entering has already been tried and
   changed nothing. Both stop the loop, and only one of them is worth trying
   again after a person looks.

   **Story complete** (`next_command` is `null`):
   - Display: "Story complete — open PR or run `/end-session`."
   - Stop.

   **`auto` is `true`**:
   - Strip the leading `/` from `next_command` (e.g. `/speckit.plan` → `speckit.plan`)
   - Output on its own line: `EXECUTE_COMMAND: {command-without-slash}`

   **`auto` is `false`**:
   - Display: "Next: run `{next_command}` when ready."
   - Where the current step carries a `reason`, display it, and its `remedy`
     below it where there is one. `next_command` names the step to re-enter; the
     reason is what re-entering has to answer, and the remedy is the part no
     command can be. A step that reports blocked and is announced as merely
     "next" sends the loop back in to do the work again rather than to give the
     answer that was missing.
   - Stop.
