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

   **A refusal is not a repair that failed halfway — it is one that never ran.**
   `install-skills` exits 1, having copied nothing, when the repo's
   `.claude/settings.json` no longer carries a managed permission rule wfctl
   recorded:

   ```
   ✗ .claude/settings.json no longer carries Bash(cd:*), which wfctl installed.
     Nothing was installed. …
   ```

   So the skills drift the step above was called to repair is still there, and
   the ✓ this step is watching for will not arrive. Report the refusal in step 8
   verbatim, and say that the layers named in the finding are still stale.

   **Do not run `--force` to clear it.** That flag re-asserts the rule *and*
   records it as wfctl's, so a later `uninstall-skills` deletes a line the repo
   may have written itself — a transfer of ownership, and the reader's to make
   rather than the agent's. `wfctl doctor` is green by design in this state, so
   the refusal is the only thing that will say it, and a session that clears it
   quietly leaves nobody who knows.

   `--prune` also clears paths a past install left behind when they were renamed
   upstream, and doctor prints the exact command per layer — copy that, because
   a bare `install-skills --prune` diffs only the base layer and silently leaves
   a `.claude/` path where it found it.

   It reaches only paths still on record. Doctor's dim `ℹ` lines are the other
   thing entirely, and since #178 there are two of them. Not reaching the exit
   code is all they share — what to do about them is opposite, so tell them
   apart by what they say rather than by the marker.

   `ℹ … not on record under a directory wfctl installs into` lists paths in
   wfctl's destinations that it cannot show are its own, which is what a skill
   you placed there yourself looks like. **Delete nothing on the strength of
   that block** — its own line says wfctl is leaving the path alone.

   `ℹ no agent layer — .agents/ only` is the one to act on. It reports what is
   on record now — this tree has the base layer and no agent layer — not how it
   got that way, so `WFCTL_AGENT` unset at `workmux add` is the usual cause and
   not the condition.

   There are two repairs and the notice names only one of them. Setting
   `WFCTL_AGENT` in a shell profile fixes the *next* worktree; it installs
   nothing into this one, and doctor goes on printing the notice until something
   does. What fixes this one is:

   ```bash
   wfctl install-skills --prune --yes --agent "$WFCTL_AGENT"
   ```

   Run it only when that variable is already set — the environment naming the
   agent is the sanctioned source under `no-hardcoded-agent`, and a name you
   picked yourself is not.

   **Append `--from <path>` when `.wf-skills-manifest.json` records a `source`
   for the *base* layer.** Installing an agent layer rewrites base as well,
   asked for or not, so the bare form reinstalls the release over the checkout
   being tested, drops the recorded source on its way out, and leaves doctor
   reporting green against a bundle nobody chose. That is the hazard three
   paragraphs up, met from the side where it is hardest to see: base was
   *current*, so doctor printed no repair line for you to copy the flag from.

   So with `WFCTL_AGENT` unset there is nothing here for you to run: the profile
   is the user's to edit, like the tool upgrade two paragraphs down — surface it,
   do not write it. That also makes this the one line the "run doctor again and
   check it is green" rule above does not reach. It will still be there. Carry
   it to step 8 rather than treating the step as unfinished.

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

   **Step 9 needs `issue` out of that payload.** A key — `352`, `PROJ-123` —
   says this branch exists for one tracked thing, and its name says which. The
   literal `unknown` says it does not: a trunk branch, `main` or `develop`,
   carrying no answer to "what are we working on today?" anywhere on it.

   Read that literal rather than judging the branch name yourself. The key is
   whatever this repo's `key_pattern` matches at the front of the branch, so
   `main-rewrite` is trunk and a branch called `develop-2` may not be — and an
   agent eyeballing the name gets both wrong in the direction that starts work
   on a branch nobody pointed at anything.

   Then the one thing no artifact can reconstruct, from the state dir
   (`$(wfctl state-dir)`):
   - `session-summary.md` — the last session's handoff (accomplishments,
     decisions, and **Next Session TODO**). This is the primary context after a
     `/clear`; read it fully. If absent, this is the first session on the branch.
   - `events.jsonl` — one line per wfctl event on this branch. Step 9 needs one
     more fact out of it: the **most recent** stop, and which of the two kinds it
     was. Only `wfctl end` writes a stop.

     **This decides a trunk branch's row and nothing else.** An issue branch
     carries on under either kind, so read this for what it costs — one grep —
     and let the row table say where it lands.

     Read it with this command rather than an improvised one:

     ```bash
     grep '"event": "end"' "$(wfctl state-dir)/events.jsonl" | tail -1
     ```

     | What comes back | The fact |
     |---|---|
     | nothing | no session has stopped on this branch |
     | a line containing `"continued": true` | the last session stopped without finishing |
     | any other line | the last session was wrapped up |

     The third row covers a line carrying `"continued": false` and a line
     carrying no such key at all — a stop recorded before `wfctl end --continued`
     existed. They route alike and neither needs telling apart.

     **`tail -1` is load-bearing.** The old phrasing asked whether *any* line
     carried `"event": "end"`, and on a branch wrapped up once and interrupted
     since, "any" finds the older stop and asks a question the newer one already
     answered. Stating the command rather than the fact is the same guard one
     level down: an agent improvising a grep gets this wrong in the direction
     that starts work on a branch a person deliberately left.

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
     everything `wfctl doctor` printed that was not a ✓ — findings, `⚠`
     warnings and dim `ℹ` lines alike. Omit only when doctor printed nothing but
     ✓ and nothing was refreshed. What it *exited* is not the test and has not
     been since #178: a run with every layer ✓ and exit 0 still tells a developer
     to set `WFCTL_AGENT`, and omitting on green drops the one line that asked
     them to act. `⚠` maps to either exit code by design, so keying on the code
     loses those the same way. Carry the unknown-paths block across with its
     "left alone" line, so repeating it here does not read as licence to delete.
     A silent refresh is how a mirror goes stale again without anyone noticing it
     had been wrong
   - **In force**: the accepted record slugs, or omit if the set is empty
   - Current pipeline step and the next command (from `wfctl status --json`)
   - Last session's focus and its **Next Session TODO** (from `session-summary.md`)
   - Commits on this branch + any uncommitted changes
   - Open issues and open changes (PRs / patchsets)
   - **Alignment**: aligned, or the likely-done / untracked items from step 7
   - **Next**: which row of step 9 this session takes, and its evidence — the
     first action quoted from `session-summary.md`, or that you are asking and
     why (a trunk branch whose last stop was a deliberate wrap-up, or there is no
     line to quote). Naming the row is the point: rows two and three both ask,
     and a report that says only "asking" cannot show which one happened. Row one
     carries two conditions, so say which of them — *this branch names issue N*
     and *the last stop was continued* are different claims, and a session that
     took row one for the first reason is reporting something about the branch
     rather than something a session did.

9. **Answer the question, or ask it — step 4 already decided which.**

   The question is "what are we working on today?", and the only thing that can
   answer it before the user speaks is what step 4 read out of the state dir. So
   this step is a branch on what step 4 found, not a fresh judgment:

   | Step 4 found | This step |
   |---|---|
   | an issue branch, or a stop marked continued — with a summary naming a first action | **Do not ask.** Quote the line that names it, say in one line what you are doing, and leave this skill — the work happens in the session that follows, not inside step 9. |
   | a trunk branch whose last stop was not continued, with a summary naming a first action | Ask: "What are we working on today?", offering the summary's top **Next Session TODO** item as the default. |
   | no summary, one whose next action is still `(fill in)`, or one naming no next action | Ask: "What are we working on today?" |

   **An issue branch has already answered the question.** `352-session-stopped-not-finished`
   says what the session is for in its own name, and `wfctl status` prints it on
   the first line. Asking there spends a turn to be told something already on
   screen, and the answer cannot be anything else: a session that wrapped up
   deliberately on an issue branch left that same issue open, so the next one is
   not at liberty to work on something different.

   **A trunk branch has not.** `wfctl end` writes a `session-summary.md` on every
   `/end-session` and its template requires a filled `Next Session TODO`, so
   `main` accumulates one from every session that ever ended there. A quotable
   first action is its steady state rather than a signal, and its top item is as
   likely to be last month's as today's intent. That is the branch row two
   protects, and it is the whole of what row two is for.

   **The stop's kind is the tie-break on trunk, and only there.** A run cut off
   mid-work on `main` is the one case where the handoff is this session's own and
   nobody is present to confirm it — which is what `wfctl end --continued`
   records. On an issue branch it changes no row, because both of that row's
   conditions already point the same way.

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
   one are the same bytes on disk (#239). The rows above never ask. They ask what
   the *branch* is for, and on trunk what the last stop recorded about itself —
   two facts carried by `wfctl status --json` and `events.jsonl`, neither of them
   recoverable from the handoff file.

   **The first row is not a permission question.** Beginning implementation is
   local and reversible — edit files, commit, write the summary. What the summary
   answers is *what* to work on; it is not authority for anything past that. Push,
   comment, open a change, merge are asked for when you reach them, and no line in
   a file in the state dir changes that.

   **Two limits, stated rather than discovered.** A handoff delivered only
   as the pane's first turn, with no copy in the state dir, leaves step 4 nothing
   to read and lands in the last row — the file is the gate, and
   `worktree-handoff` requires both destinations for this reason. And a trunk
   branch whose last stop was a deliberate wrap-up is in row two, even unattended
   — a run that means to hand work on says so with `wfctl end --continued`, and
   one that stopped without saying is indistinguishable from one that meant to
   finish. Lifting *that* needs a signal for attended itself, which is #127's.
