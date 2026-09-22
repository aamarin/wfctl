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

## When the input is `restart`

`wfctl hook session-restart` types `/end-session restart` into a pane whose
context window is full, and types `/clear` and `/start-session` once this turn
has recorded its stop. Nobody is at the prompt, and the context is about to be
discarded — so this turn is the handoff, and the only one. Three steps change:

- **Step 3 runs `wfctl end --continued`**, not bare `wfctl end`. A restarted
  session is one the next session carries on without being asked, and
  `/start-session` reads that from the stop this records. A bare `end` says the
  work was wrapped up, which is the opposite.
- **Step 4 is filled in full**, as on any other run, and its accomplishments,
  decisions and **Next Session TODO** are written for a session that will read
  nothing else. Add one line saying this was an automatic session restart and
  that the tree was left as found.
- **Steps 6 and 7 are skipped.** Do not ask about committing or the tracker: the
  question would sit at a prompt nobody reads until `/clear` discards it. Leave
  uncommitted work uncommitted and the tracker untouched, and say so in the
  summary and the step 8 report.

Everything else runs as written, step 5 included.

Only the exact input `restart` does this. Any other input — none, a typo, a
sentence — is a normal end-session, so a mistyped argument cannot become an
unattended close. A person who types `/end-session restart` by hand gets the
same close as the hook; nothing here can tell the two apart, and it does not try.

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

5. **Outward actions are asked for, attempted, and recorded — never skipped for
   want of a setting.** Step 7 below reaches outside the repo: a comment, a
   label, a closed or new issue. wfctl does not decide whether those may run.
   Your host's permission layer does, and it refuses before wfctl ever starts
   (`wfctl-records-outward-actions-and-never-gates-them`). The same holds for a
   push, which this step tells you to record below. Step 6 commits and reaches
   nobody, as does writing the summary.

   **Ask as each step is written.** An attended session gets the question. A run
   where nobody answers takes the action rather than stopping on the question —
   there is no mode to read that says which of the two this is, and reading one
   would be the second permission system this replaced.

   **If the host refuses, report it rather than routing around it.** Reaching
   for `gh` or another client directly defeats the one gate that exists. What
   the refusal needs is a record, so the next session reads the step as
   unfinished rather than done:

   ```bash
   wfctl report-block issue-close --reason "<what your host said>"
   ```

   The name is `issue-<verb>` for a tracker write, which is the name `wfctl issue`
   records when that write succeeds — so a later successful `wfctl issue close`
   lifts the hold with nothing else typed. `push` for a push.

   **Record what wfctl cannot see.** `wfctl issue` logs its own writes, so a
   comment, a label or a close needs nothing from you. A push does — no wfctl verb
   performs one:

   ```bash
   wfctl report-action push       # after it succeeded
   ```

   A push leaves no other trace a restarted session can read: the summary is
   written in step 3, and `/clear` follows the handoff.

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

   # If work is only partially done, leave it open with a progress note. Its
   # state is not yours to set here: `wfctl issue start` and `stop` carry that,
   # and the worktree hooks already run them.
   wfctl issue comment "$ISSUE" --body "Partial progress: <what remains>"

   # Reconcile any secondary issues noted in step 2 the same way, and file new work:
   wfctl issue create --title "<title>" --body "<context>"
   ```

   **If your host refuses one of these commands**, file the block step 5
   describes, under the verb's own name — `issue-close`, `issue-comment`,
   `issue-create`. A person who then takes the action outside wfctl lifts the
   hold with `wfctl report-action issue-close`; a later successful
   `wfctl issue close` lifts it by itself.

8. **Report:** session closed, summary written, whether the work was committed and
   the tracker updated (per the user's choices in 6–7), next steps, any blockers.
   **Name every outward action the host refused**, with the action and what the
   host said — a run that filed a block and a run that had nothing to tell anyone
   leave the same tracker, and only the report says which this was.
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
