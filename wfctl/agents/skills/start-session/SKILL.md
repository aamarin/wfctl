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

9. Ask: "What are we working on today?" — defaulting to the top item from the last
   session's Next Session TODO if there was one.
