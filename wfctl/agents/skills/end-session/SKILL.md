---
name: end-session
description: Use when finishing a development session - writes a session-summary handoff artifact, reconciles the issue tracker, and surfaces uncommitted work before the context is lost.
compatibility: 'Requires wfctl to be installed'
---

# End Session

You are ending the current development session. Produce a handoff good enough
that a fresh session (after `/clear`) can resume from the artifacts alone.

**Run every step below — do not stop at `wfctl end`.** Step 3 only writes an
*empty scaffold*; the session isn't ended until the summary is filled with real
data (step 4). Steps 1–5 and 8 are mandatory; steps 6–7 must be *offered* to the
user, who decides whether to commit and update the tracker. A scaffold left
unfilled is a failed handoff.

## Workflow

1. **Capture the end timestamp** (used in the summary header; also the window for
   the git scan below):
   ```bash
   date -u +"%Y-%m-%dT%H:%M:%SZ"
   ```

2. **Scan this branch's work** to ground the summary in facts, not memory.
   `origin/HEAD` names the default branch when a remote is set; otherwise fall
   back to recent history so this never errors:
   ```bash
   BASE=$(git symbolic-ref --short refs/remotes/origin/HEAD 2>/dev/null || true)  # e.g. origin/main
   git log --format="%h %s" ${BASE:+${BASE}..HEAD} ${BASE:--20}   # branch commits, or last 20
   git diff --stat                                               # uncommitted changes in the tree
   git log -p ${BASE:+${BASE}..HEAD} ${BASE:--20} | grep -nE '^\+.*(TODO|FIXME)'  # TODOs added
   ```
   Read the commit subjects for what shipped, `--stat` for files touched, and note
   any new TODO/FIXME as follow-up candidates. The branch's own issue is already
   known — it's the branch key (`wfctl status` shows it), no scanning needed. If a
   commit subject says it *also* resolved another issue (your tracker's convention,
   e.g. GitHub `Closes #123` or Jira `Fixes PROJ-45`), note those as secondary
   issues to reconcile in step 7.

3. **Close the session and write the summary scaffold:**
   ```bash
   wfctl end
   ```
   This writes `session-summary.md` in the state dir (`$(wfctl state-dir)`) and
   prints what it observed:

   ```
   ✓ Session closed — implement 3/8 done, boundary answered, tree dirty.
     Summary: /Users/…/state/wfctl/<branch>/session-summary.md
   ```

   Three readings, no verdict. The scaffold it writes already carries them as
   `**Step**`, `**Boundary**` and `**Tree**` — leave those lines alone. They are
   what `wfctl` could see; the prose below them is what only you know.

   **It writes only when the file is absent.** A summary already there survives
   untouched, and `end` says so:

   ```
   ✓ Session closed — brainstorm, boundary unanswered, tree clean.
     Summary: /Users/…/state/wfctl/<branch>/session-summary.md
     ⚠ kept — this session wrote nothing; last modified 2026-09-05T22:14:03Z.
   ```

   On that line the file is **not** a scaffold, and `end` cannot tell you which
   of the two it is:

   - **A handoff**, written *for* this branch by `worktree-handoff` before any
     session ran on it. Its own first line says so. It uses its own shape, so
     the `**Step**` / `**Boundary**` / `**Tree**` lines are simply not in it.
   - **The last session's summary**, carrying those three lines filled with
     readings that are now hours or days old.

   Both are normal — a fresh worktree gets the first the moment it is created,
   and a long-lived branch like `main` gets the second on every session after
   its first. Read the file before step 4 either way, and take the `**Step**` /
   `**Boundary**` / `**Tree**` values from the `Session closed` line above
   rather than from the file, which is the one place the two cases need the same
   thing of you.

4. **Fill in `$(wfctl state-dir)/session-summary.md`** using the scan from step 2.
   Keep it concrete — this is the next session's starting context:

   ```markdown
   # Session Summary: {YYYY-MM-DD, today} — {branch}

   **End time:** {timestamp from step 1}
   **Step**: {from the `Session closed` line — already in the file if `end` wrote it}
   **Boundary**: {from the `Session closed` line — already in the file if `end` wrote it}
   **Tree**: {from the `Session closed` line — already in the file if `end` wrote it}
   **Focus:** {one line — what this session was about}

   ## What We Accomplished
   - {from commit subjects: what shipped}

   ## Decisions Made
   - {decision} — {why} (even small ones; future-you won't remember)

   ## Files Changed
   - `path` — {what changed} (from git diff --stat)

   ## Next Session TODO
   - [ ] {highest-priority next step}
   - [ ] {new TODO/FIXME found in step 2, if worth tracking}

   ## Blockers / Open Questions
   - {anything blocking, or "None"}
   ```

   **CRITICAL:** Fill every field with the actual data from step 2's scan — never
   leave `(fill in)` or template placeholders. No commits this session → "No
   commits." No blockers → "None."

   Do not add a status line. There used to be one — `in progress | complete |
   blocked` — and nothing could observe which of the three was true, so it was
   guessed and the next session read the guess as fact. Where the work stands is
   the `**Step**` line above, which was read rather than decided. Say what is
   unfinished in **Next Session TODO**, where it is a statement of intent and
   reads as one.

5. **Read what this run may do before doing any of it.**

   ```bash
   wfctl status --json     # read `notify` and `notify_source`
   ```

   `notify` is `false` unless a person granted this feature branch the authority
   to tell people outside the repo. Steps 6 and 7 below both take actions in that
   class — a comment, a label, a new issue, a push — and none of them can be
   taken back once someone has been notified.

   **`false` means do not take them.** Not "ask twice", not "take them and say
   so afterwards": print the line `wfctl status` prints, say which of the actions
   below you are therefore skipping, and carry on with the rest of the session
   close. Committing and writing the summary are unaffected — those reach nobody
   and are undone by the person who made them.

   Treat any other answer — the key absent, the command failing, an older wfctl —
   as `false`. The mode is the thing that removes a human from an outward-facing
   decision, so an inconclusive read has to leave one in.

   `notify_source` says *why*, and the report in step 8 carries it. Five values
   mean refused and they are not the same event: nobody granted it, someone
   turned it off, the stored answer was damaged, the tracker could not be
   reached, or this is the trunk branch. The middle two are failures rather than
   anyone's decision, and reporting them as a person withholding authority is the
   thing this distinction exists to prevent.

   **An attended session still asks.** The grant answers whether the authority
   *exists*, never whether to use it here — steps 6 and 7 ask their questions
   exactly as written. What the grant changes is what an unattended run does when
   nobody answers: refuse, rather than proceed.

   **Record what wfctl cannot see.** `wfctl issue` logs its own writes, so a
   comment or a label needs nothing from you. A push does — no wfctl verb
   performs one, and it is in the same class:

   ```bash
   wfctl notify push                                    # after it succeeded
   wfctl notify push --declined --reason "<why not>"    # allowed, and you didn't
   ```

   The second is not bookkeeping. An action you skipped and one you were refused
   leave an identical repo, and only one of them says the grant should be wider.

6. **Ask before committing.** If step 2 showed uncommitted changes, ask the user:
   "Commit these with a message referencing the active issue?" On yes, commit with
   a clear message (include your tracker's close keyword if it has one, e.g. GitHub
   `Closes #N`). On no, leave them as-is and note it in the report.

7. **Ask before touching the tracker.** Ask the user: "Update the issue tracker —
   close it (work complete), add a progress comment (partial), or skip?" Act on
   their choice with `wfctl issue` (skip silently if no tracker is configured or a
   verb is unsupported — `wfctl issue` no-ops in both cases). The branch's issue
   key is already known — `wfctl status` prints it. Verbs are backend-agnostic
   (GitHub, Jira, or a custom tracker):

   ```bash
   ISSUE=<branch issue key from `wfctl status`>

   # View first, then close only if still open. Idempotent: handles trackers that
   # already auto-closed the issue on merge, and those that don't — no tracker-
   # specific assumption needed.
   wfctl issue view "$ISSUE"
   wfctl issue close "$ISSUE" --comment "Completed this session."   # only if still open

   # If work is only partially done, leave it open with a progress note:
   wfctl issue comment "$ISSUE" --body "Partial progress: <what remains>"
   wfctl issue label "$ISSUE" --action add --label in-progress

   # Reconcile any secondary issues noted in step 2 the same way, and file new work:
   wfctl issue create --title "<title>" --body "<context>"
   ```

8. **Report:** session closed, summary written, whether the work was committed and
   the tracker updated (per the user's choices in 6–7), next steps, any blockers.
   **Say what the grant allowed and what it refused**, naming the source — a run
   that skipped the tracker because nobody granted it looks identical, in a
   report that omits this, to a run that had nothing to tell anyone.
   If ending because context is filling, remind the user they can `/clear` and
   `/start-session` to resume from the summary.

   **Also report uncommitted specs when they live in a different working tree.**
   With a spec root outside the working repo, the spec dir is somewhere the user
   never opens, so uncommitted work there is invisible:

   Run `wfctl feature-paths` and read `FEATURE_DIR` from its output — the plain
   command, not `eval "$(…)"`, which the command's pre-approval would not match,
   costing an approval prompt every session. Substituting that real path:

   ```bash
   git -C <FEATURE_DIR> rev-parse --show-toplevel   # → SPEC_ROOT, or fails
   git rev-parse --show-toplevel                    # → THIS_ROOT
   ```

   Call those two outputs `SPEC_ROOT` and `THIS_ROOT` and substitute them below
   the same way you substitute `FEATURE_DIR`.

   Say nothing at all when the first command fails — the spec dir is in a plain
   directory, or this branch has no spec dir, and it fails identically for both —
   or when `SPEC_ROOT` equals `THIS_ROOT`, since step 6 already covered that
   case. Otherwise count the lines of
   `git -C <SPEC_ROOT> status --short -- <FEATURE_DIR>` and, if non-zero, add one
   line to the report naming `SPEC_ROOT` and the count. An absolute pathspec is
   correct here: it scopes the count to this branch's spec dir and excludes any
   sibling branch's.

   Compare the two `rev-parse` outputs, never `$FEATURE_DIR` against a toplevel
   directly — `rev-parse` resolves symlinks (on macOS `/var` → `/private/var`),
   so a direct comparison misfires. `status --short` rather than `git diff`,
   because a new spec dir is untracked and `diff` reports nothing on the most
   common case.

   **Report only.** Do not stage, commit, push, or delete anything in the spec
   root, and do not offer to. Someone who wants their specs committed will commit
   them; what they cannot do is notice that a directory they never open has
   uncommitted work in it.

   Any *working tree* other than this one qualifies, including a sibling worktree
   on an orphan branch — it shares an object store but has its own toplevel.

**Before reporting done:** confirm `session-summary.md` has real content (no
`(fill in)` placeholders) and that steps 6–7 were offered to the user. If the
summary is still a scaffold, you haven't finished — go back to step 4.
