---
name: start-session
description: Use when starting a development session in a git worktree - initializes wfctl session state, loads handoff artifacts from the last session, and reports open work before any code is touched.
allowed-tools: Read Bash(wfctl start*) Bash(wfctl status*) Bash(wfctl arch context*) Bash(wfctl state-dir*) Bash(wfctl doctor*) Bash(wfctl install-skills*) Bash(wfctl issue list*) Bash(wfctl issue view*) Bash(wfctl change list*) Bash(git status*) Bash(git log*) Bash(git symbolic-ref*)
compatibility: 'Requires wfctl to be installed'
---

# Start Session

You are starting a development session in the current git worktree. If the last
session ended with `/end-session` and `/clear`, the artifacts below are your only
memory of it — load them before doing anything else.

## Workflow

1. **Set the output style:** read `.agents/skills/i-have-adhd/SKILL.md` and
   `.agents/skills/conversation-response-shape/SKILL.md` (or
   `../i-have-adhd/SKILL.md` and `../conversation-response-shape/SKILL.md`
   relative to this file) and apply both to every response for the rest of the
   session, starting with the report in step 8. `i-have-adhd` sets the length
   and the next action; `conversation-response-shape` sets what comes first and
   how deep it goes. Skip either silently if it isn't installed. The user turns
   both off with "stop adhd mode" or "normal mode".

   If step 2 then refreshes the skills, read both files again afterwards. This
   step runs first so the report in step 8 is already shaped, but that puts it
   ahead of the refresh — so on precisely the run where a skill was missing or
   stale, this step read the old copy or skipped it. A second read costs nothing
   and is the only thing that closes that window. Skills installed mid-session
   may not enter the agent's own index until it restarts; say so in step 8 if a
   refresh added one, rather than assuming it is loadable by name.

2. **Initialize and check freshness:**
   ```bash
   wfctl start     # init session context, infer the current pipeline step
   wfctl doctor    # is the wfctl tool / installed skills up to date?
   ```
   `wfctl doctor` reports green ✓ current · cyan ⬆ upgrade available.

   **If it reports any layer's skills behind or drifted, bring them level now.**
   Doctor names the layer on each finding and prints the command that repairs
   *that* layer. **Run what it printed, once per reported layer, with `--prune
   --yes` appended.** Those two flags are this step's, not doctor's: doctor
   prints the repair for the drift and no policy on top of it, and the policy
   here is that the refresh runs unattended. So the two most common lines are:

   ```bash
   wfctl install-skills --prune --yes                   # a `base` finding
   wfctl install-skills --prune --yes --agent claude    # a `claude` finding
   ```

   **The printed command is the part that governs; those two are only its
   common shapes.** A layer installed from a source someone named is repaired by
   a line carrying `--from <that source>`, and running the bare form instead does
   not fail — it succeeds, reinstalls the release over the branch being tested,
   and reports the layer green. That is a repair destroying the thing it was
   called to check, and nothing downstream would say so.

   Copy the printed path as printed. It is quoted when it needs to be, and a
   path carrying a space or a bracket is one this step has already got wrong.

   Then run `wfctl doctor` again and check it is green before moving on. Without
   the second run the report says "refreshed" over a tree that is still drifted:
   a layer is rewritten only when it is asked for by name, so a run that omits
   `--agent` leaves that layer exactly as stale as it found it.

   `--prune` also clears paths a past install left behind when they were renamed
   upstream, and doctor prints the exact command per layer — copy that, because
   a bare `install-skills --prune` diffs only the base layer and silently leaves
   a `.claude/` path where it found it.

   It reaches only paths still on record. Doctor's dim `ℹ` block is the other
   thing entirely: paths in wfctl's destinations that it cannot show are its
   own, which is what a skill you placed there yourself looks like. **Delete
   nothing on the strength of that block** — it does not affect the exit code,
   and its own line says wfctl is leaving the path alone.

   `--yes` is what keeps this non-interactive, and it is not free: it skips the
   prompt that would otherwise list pre-existing files being overwritten — files
   *not* on wfctl's record, so possibly someone's own. They are backed up and the
   run says where, so this is recoverable, not silent. If that is not a trade you
   want made unattended, drop `--yes` and answer the prompt.

   Run `doctor` and `install-skills` through the **same** wfctl. They compare the
   installed tree against the bundle carried by whichever one you invoked, so two
   different wfctls disagree permanently — whichever installed last is the one
   that reports clean. In most repos there is only one and this costs you nothing
   to honour. In a repo that develops wfctl itself there are two; that project's
   own AGENTS.md says which to use, and it governs.

   The **tool** being behind is a different call and stays the user's: `uv tool
   install --upgrade …` changes what is installed on the machine, not what this
   repo holds. Surface it as a one-line heads-up. Not a blocker.

3. **Load the architectural contract:**
   ```bash
   wfctl arch context   # the decisions this repo is built under
   ```
   These bind the work you are about to do; they are not background reading. A
   record is in force because someone accepted it, and the projection shows only
   those — proposed, superseded, rejected and retired records are counted but
   never listed, because a superseded decision read as live is the confusion the
   status field exists to prevent.

   An empty set is normal: a repo has no records until it writes its first one.
   Carry the set into the report as slugs, one line each — the full text is a
   `wfctl arch context` away and does not need repeating.

4. **Read the position, then the handoff:**
   ```bash
   wfctl status --json   # issue, branch, per-step state, the next command
   ```
   Every value there is computed from artifacts at the moment you ask, so it is
   true whatever happened since the last session — including work done with no
   wfctl command in between. `state` is one of `done`, `in_progress`, `pending`,
   `skipped`; read it rather than the glyphs `wfctl status` draws, which spend
   one symbol on "ran" and another on "passed by" and cannot be told apart once
   printed.

   Then the one thing no artifact can reconstruct, from the state dir
   (`$(wfctl state-dir)`):
   - `session-summary.md` — the last session's handoff (accomplishments,
     decisions, and **Next Session TODO**). This is the primary context after a
     `/clear`; read it fully. If absent, this is the first session on the branch.
   - `events.jsonl` — one line per wfctl event on this branch. Step 9 needs one
     fact out of it: whether any line carries `"event": "end"`. Only `wfctl end`
     writes that, so it is the mark that a session has finished here before —
     which is what separates a branch someone handed work to from one someone is
     coming back to.

5. **Surface work done on this branch** so you can see where things stand:
   ```bash
   BASE=$(git symbolic-ref --short refs/remotes/origin/HEAD 2>/dev/null || true)
   git log --format="%h %s" ${BASE:+${BASE}..HEAD} ${BASE:--20}
   git status --short
   ```

6. Check open work via the configured backends:
   ```bash
   wfctl issue list     # open issues (scoped to you if the tracker sets {me})
   wfctl change list     # open PRs / patchsets (your changes under review)
   ```
   Each runs the active backend's list command (GitHub, Jira, Gerrit, or a custom
   one). If a backend isn't configured — or doesn't implement the verb — it prints
   a notice and no-ops, so skip whatever comes back empty.

7. **Check alignment** — does the branch's work match what's tracked? Correlate
   the commits (step 5) with the open issues/changes (step 6). It's a heads-up
   read, not an audit or a gate:
   - **Aligned** — a commit references an issue/change (`#N`, `Closes #N`, or a
     tracker key like `PROJ-123`). Nothing to flag.
   - **Likely done** — an open issue whose work the commits appear to complete.
     Flag it to close (`wfctl issue view <id>` to confirm), don't close it yourself.
   - **Untracked** — committed work (especially new feature files) that matches no
     open issue. Surface it so the user decides: open an issue, fold it into an
     existing one, or leave it (infra / one-off).

   Only surface the non-aligned items. If everything lines up, say so in one line
   and move on.

8. Report status to the user:
   - **Freshness**: skills you refreshed in step 2 and what changed, plus
     everything `wfctl doctor` still reports — it checks more than skills and
     still exits 1 on any of them. Omit only when doctor is green and nothing was
     refreshed; a silent refresh is how a mirror goes stale again without anyone
     noticing it had been wrong
   - **In force**: the accepted record slugs, or omit if the set is empty
   - Current pipeline step and the next command (from `wfctl status --json`)
   - Last session's focus and its **Next Session TODO** (from `session-summary.md`)
   - Commits on this branch + any uncommitted changes
   - Open issues and open changes (PRs / patchsets)
   - **Alignment**: aligned, or the likely-done / untracked items from step 7
   - **Next**: the first action, quoted from `session-summary.md` — or, when
     there is no line to quote, that you are asking instead

9. **Answer the question, or ask it — step 4 already decided which.**

   The question is "what are we working on today?", and the only thing that can
   answer it before the user speaks is what step 4 read out of the state dir. So
   this step is a branch on what step 4 found, not a fresh judgment:

   | Step 4 found | This step |
   |---|---|
   | a summary naming a first action, and **no** `end` event | **Do not ask.** Quote the line that names it, say in one line what you are doing, and leave this skill — the work happens in the session that follows, not inside step 9. |
   | a summary, and an `end` event — a session has finished here before | Ask: "What are we working on today?", offering the summary's top **Next Session TODO** item as the default. |
   | no summary, one whose next action is still `(fill in)`, or one naming no next action | Ask: "What are we working on today?" |

   **The `end` event is what keeps an attended session safe.** `wfctl end` writes
   a `session-summary.md` on every `/end-session` and its template requires a
   filled `Next Session TODO`, so on any branch that has run a session before —
   `main` most of all — a quotable first action is the *steady state*, not a
   signal. Row one without this column hands every returning session an
   instruction it never asked for, which trades this step's defect for a worse
   one. The event is the narrow question actually worth asking: has anyone
   worked here yet?

   **The gate on the summary is the quote.** If you cannot copy a literal
   sentence out of `session-summary.md` saying what to do first, you are in the
   last row. An inference about what the branch is probably for is not an answer,
   and acting on one is how the last row's protection is lost. Quoting is also
   what makes the branch visible from outside — step 8 reports which row this
   session took, so a wrong turn is a mismatch someone can point at rather than a
   matter of tone.

   **Do not try to tell a handoff from a previous session's summary by reading
   the file.** Provenance is not recoverable from its content or its timestamps:
   `worktree-handoff` copies a handoff in around the moment the pane comes up, so
   which of the two landed first is a race, and a kept file and a freshly written
   one are the same bytes on disk (#239). The rows above never ask. They ask
   whether anyone has finished a session here, which `events.jsonl` records
   directly.

   **The first row is not a permission question.** Beginning implementation is
   local and reversible — edit files, commit, write the summary. What the summary
   answers is *what* to work on; it is not authority for anything past that. Push,
   comment, open a change, merge are asked for when you reach them, and no line in
   a file in the state dir changes that.

   **Two limits, stated rather than discovered.** A handoff delivered only
   as the pane's first turn, with no copy in the state dir, leaves step 4 nothing
   to read and lands in the last row — the file is the gate, and
   `worktree-handoff` requires both destinations for this reason. And a branch
   that has ended a session once is in row two from then on, even unattended;
   lifting that needs a signal for *attended* itself, which is #127's.
